"""HydraDB graph client — connection management, schema creation, and core graph operations."""

from __future__ import annotations

import hashlib
import logging
import time
from contextlib import contextmanager
from typing import Any, Generator

from neo4j import GraphDatabase, Driver, Session, Result

from chronograph.config import HydraConfig, get_config

logger = logging.getLogger(__name__)


def str_to_int_id(s: str | int) -> int:
    """Convert any string or int ID to a deterministic positive 63-bit integer for HydraDB."""
    if isinstance(s, int):
        return abs(s)
    return int(hashlib.md5(s.encode("utf-8")).hexdigest()[:14], 16)


class HydraClient:
    """Manages the connection to HydraDB via the Neo4j Bolt driver."""

    def __init__(self, config: HydraConfig | None = None):
        self._config = config or get_config().hydra
        self._driver: Driver | None = None

    @property
    def driver(self) -> Driver:
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self._config.bolt_uri,
                auth=self._config.auth,
            )
        return self._driver

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Yield a Neo4j session scoped to the default database."""
        s = self.driver.session(database="default")
        try:
            yield s
        finally:
            s.close()

    def run(self, query: str, **params: Any) -> list[dict[str, Any]]:
        """Execute a Cypher query and return all records as dicts."""
        with self.session() as s:
            result: Result = s.run(query, **params)
            return [record.data() for record in result]

    def run_single(self, query: str, **params: Any) -> dict[str, Any] | None:
        """Execute a Cypher query and return the first record, or None."""
        records = self.run(query, **params)
        return records[0] if records else None

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # ─── Health Check ────────────────────────────────────────────

    def wait_for_ready(self, timeout: float = 60.0, interval: float = 2.0) -> bool:
        """Block until HydraDB is accepting Bolt connections, or timeout."""
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            try:
                self.driver.verify_connectivity()
                logger.info("HydraDB is ready at %s", self._config.bolt_uri)
                return True
            except Exception:
                logger.debug("Waiting for HydraDB... (%.1fs)", time.monotonic() - start)
                time.sleep(interval)
        logger.error("HydraDB did not become ready within %.0fs", timeout)
        return False

    # ─── Core Write Operations ───────────────────────────────────

    def upsert_entity(
        self,
        entity_id: str | int,
        name: str,
        entity_type: str,
        aliases: list[str] | str | None = None,
        timestamp: int | None = None,
    ) -> int:
        """Create or update an Entity node via a self-referential or session edge."""
        int_id = str_to_int_id(entity_id)
        alias_str = ", ".join(aliases) if isinstance(aliases, list) else (aliases or "")
        ts = timestamp or int(time.time() * 1000)
        self.run(
            """
            CREATE (e:Entity {id: $id, name: $name, entity_type: $entity_type, aliases: $aliases, last_seen: $ts})-[:IS_ENTITY]->(e:Entity {id: $id})
            """,
            id=int_id,
            name=name,
            entity_type=entity_type,
            aliases=alias_str,
            ts=ts,
        )
        return int_id

    def create_fact(
        self,
        fact_id: str | int,
        content: str,
        session_id: str,
        session_idx: int,
        timestamp: int,
        source_turn: int = 0,
        confidence: float = 1.0,
        valid_from: int | None = None,
    ) -> int:
        """Create a Fact node."""
        int_id = str_to_int_id(fact_id)
        self.run(
            """
            CREATE (f:Fact {id: $id, content: $content, session_id: $session_id, session_idx: $session_idx, timestamp: $timestamp, valid_from: $valid_from, valid_to: -1, confidence: $confidence})-[:IS_FACT]->(f:Fact {id: $id})
            """,
            id=int_id,
            content=content,
            session_id=str(session_id),
            session_idx=session_idx,
            timestamp=timestamp,
            valid_from=valid_from or timestamp,
            confidence=confidence,
        )
        return int_id

    def link_entity_to_fact(self, entity_id: str | int, fact_id: str | int, role: str) -> None:
        """Create a SUBJECT_OF or OBJECT_OF relationship between Entity and Fact."""
        e_id = str_to_int_id(entity_id)
        f_id = str_to_int_id(fact_id)
        if role == "subject":
            self.run(
                "CREATE (e:Entity {id: $e_id})-[:SUBJECT_OF {role: $role}]->(f:Fact {id: $f_id})",
                e_id=e_id,
                f_id=f_id,
                role=role,
            )
        else:
            self.run(
                "CREATE (f:Fact {id: $f_id})-[:OBJECT_OF {role: $role}]->(e:Entity {id: $e_id})",
                e_id=e_id,
                f_id=f_id,
                role=role,
            )

    def link_session_to_fact(self, session_id: str | int, fact_id: str | int) -> None:
        """Create a CONTAINS relationship between Session and Fact."""
        s_id = str_to_int_id(session_id)
        f_id = str_to_int_id(fact_id)
        self.run(
            "CREATE (s:Session {id: $s_id})-[:CONTAINS]->(f:Fact {id: $f_id})",
            s_id=s_id,
            f_id=f_id,
        )

    def link_session_to_entity(self, session_id: str | int, entity_id: str | int) -> None:
        """Create a MENTIONS relationship between Session and Entity."""
        s_id = str_to_int_id(session_id)
        e_id = str_to_int_id(entity_id)
        self.run(
            "CREATE (s:Session {id: $s_id})-[:MENTIONS]->(e:Entity {id: $e_id})",
            s_id=s_id,
            e_id=e_id,
        )

    def supersede_fact(
        self,
        old_fact_id: str | int,
        new_fact_id: str | int,
        reason: str = "updated",
        superseded_at: int = 0,
    ) -> None:
        """Mark old fact as superseded and link to new fact via direct edge creation."""
        old_id = str_to_int_id(old_fact_id)
        new_id = str_to_int_id(new_fact_id)
        ts = superseded_at or int(time.time() * 1000)

        # Update valid_to on old fact
        try:
            self.run(
                "MATCH (old:Fact {id: $old_id}) SET old.valid_to = $ts",
                old_id=old_id,
                ts=ts,
            )
        except Exception as e:
            logger.warning("Could not SET valid_to on fact %s: %s", old_id, e)

        # Create SUPERSEDED_BY edge directly
        self.run(
            "CREATE (old:Fact {id: $old_id})-[:SUPERSEDED_BY {reason: $reason, superseded_at: $ts}]->(new:Fact {id: $new_id})",
            old_id=old_id,
            new_id=new_id,
            reason=reason,
            ts=ts,
        )

    # ─── Core Read Operations ────────────────────────────────────

    def get_entity_facts(self, entity_name: str, current_only: bool = True) -> list[dict]:
        """Get all facts associated with an entity by name."""
        try:
            res_subj = self.run(
                """
                MATCH (e:Entity)-[:SUBJECT_OF]->(f:Fact)
                WHERE e.name = $name
                RETURN f.id AS id, f.content AS content, f.timestamp AS timestamp,
                       f.valid_from AS valid_from, f.valid_to AS valid_to,
                       f.session_id AS session_id, f.confidence AS confidence
                ORDER BY f.timestamp DESC
                """,
                name=entity_name,
            )
        except Exception:
            res_subj = []

        try:
            res_obj = self.run(
                """
                MATCH (f:Fact)-[:OBJECT_OF]->(e:Entity)
                WHERE e.name = $name
                RETURN f.id AS id, f.content AS content, f.timestamp AS timestamp,
                       f.valid_from AS valid_from, f.valid_to AS valid_to,
                       f.session_id AS session_id, f.confidence AS confidence
                ORDER BY f.timestamp DESC
                """,
                name=entity_name,
            )
        except Exception:
            res_obj = []

        seen = set()
        all_facts = []
        for r in res_subj + res_obj:
            if r["id"] not in seen:
                seen.add(r["id"])
                if not current_only or r.get("valid_to", -1) == -1:
                    all_facts.append(r)
        return all_facts

    def find_path_between_entities(
        self,
        source_name: str,
        target_name: str,
        max_len: int = 3,
    ) -> list[dict]:
        """Use algo.SPpaths to find shortest paths between two entities through the fact graph."""
        src_node = self.run_single("MATCH (e:Entity) WHERE e.name = $name RETURN e.id AS id", name=source_name)
        tgt_node = self.run_single("MATCH (e:Entity) WHERE e.name = $name RETURN e.id AS id", name=target_name)
        if not src_node or not tgt_node:
            return []

        src_id = src_node["id"]
        tgt_id = tgt_node["id"]
        try:
            return self.run(
                f"""
                CALL algo.SPpaths({{
                    sourceNode: {src_id},
                    targetNode: {tgt_id},
                    relTypes: ['SUBJECT_OF', 'OBJECT_OF', 'SUPERSEDED_BY', 'MENTIONS'],
                    maxLen: {max_len}
                }}) YIELD path
                RETURN path
                """
            )
        except Exception as e:
            logger.warning("algo.SPpaths fallback: %s", e)
            return self.run(
                """
                MATCH (a:Entity {id: $src})-[:SUBJECT_OF]->(f:Fact)-[:OBJECT_OF]->(b:Entity {id: $tgt})
                RETURN a.name AS src, f.content AS fact, b.name AS dst
                """,
                src=src_id,
                tgt=tgt_id,
            )

    def check_graph_coverage(self, entity_names: list[str]) -> dict[str, Any]:
        """Check whether query entities exist in the graph and have connected facts."""
        results = {}
        for name in entity_names:
            node = self.run_single("MATCH (e:Entity) WHERE e.name = $name RETURN e.id AS id", name=name)
            if node:
                facts = self.get_entity_facts(name, current_only=True)
                results[name] = {
                    "entity_exists": True,
                    "fact_count": len(facts),
                    "facts": [f["content"] for f in facts[:5]],
                }
            else:
                results[name] = {
                    "entity_exists": False,
                    "fact_count": 0,
                    "facts": [],
                }
        return results

    def get_graph_stats(self) -> dict[str, int]:
        """Get counts of nodes and relationships in the graph."""
        try:
            entity_res = self.run("MATCH (e:Entity) RETURN count(*) AS c")
            fact_res = self.run("MATCH (f:Fact) RETURN count(*) AS c")
            session_res = self.run("MATCH (s:Session) RETURN count(*) AS c")
            return {
                "entities": entity_res[0]["c"] if entity_res else 0,
                "facts": fact_res[0]["c"] if fact_res else 0,
                "sessions": session_res[0]["c"] if session_res else 0,
            }
        except Exception as e:
            logger.warning("Error fetching graph stats: %s", e)
            return {"entities": 0, "facts": 0, "sessions": 0}
