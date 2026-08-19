"""Ingestion Graph Writer — Writes extracted entities, facts, and temporal relations to HydraDB."""

import hashlib
import logging
from typing import List
from tqdm import tqdm

from chronograph.graph_client import HydraClient, str_to_int_id
from chronograph.ingestion.session_parser import ChatSession
from chronograph.ingestion.fact_extractor import ExtractedFact
from chronograph.ingestion.entity_resolver import EntityResolver
from chronograph.ingestion.temporal_tagger import TemporalRelation

logger = logging.getLogger(__name__)


class GraphWriter:
    """Writes chat sessions, extracted facts, and entity relations to HydraDB."""

    def __init__(self, client: HydraClient):
        self.client = client

    def _generate_fact_id(self, content: str, session_id: str) -> int:
        """Generate a deterministic 63-bit integer fact ID."""
        key = f"{content}:{session_id}"
        return str_to_int_id(key)

    def write_session(
        self, session: ChatSession, facts: List[ExtractedFact], resolver: EntityResolver
    ) -> None:
        """Write session and facts to HydraDB using valid one-hop edge creation patterns."""
        sess_int_id = str_to_int_id(session.session_id)
        started_at = getattr(session, "started_at", 0)
        ended_at = getattr(session, "ended_at", started_at)

        for fact in facts:
            fact_int_id = self._generate_fact_id(fact.content, session.session_id)
            fact_ts = getattr(fact, "timestamp", started_at) or started_at

            # Resolve Subject Entity
            subj_entity = resolver.resolve(fact.subject)
            subj_int_id = str_to_int_id(subj_entity.id)
            alias_str = ", ".join(subj_entity.aliases)

            # 1. Connect Session -> Subject Entity (creates both nodes if missing)
            self.client.run(
                """
                CREATE (s:Session {id: $s_id, index: $idx, started_at: $st, ended_at: $et})-[:MENTIONS]->(e:Entity {id: $e_id, name: $e_name, entity_type: $e_type, aliases: $aliases, last_seen: $ts})
                """,
                s_id=sess_int_id,
                idx=session.index,
                st=started_at,
                et=ended_at,
                e_id=subj_int_id,
                e_name=subj_entity.canonical_name,
                e_type=subj_entity.entity_type,
                aliases=alias_str,
                ts=fact_ts,
            )

            # 2. Connect Subject Entity -> Fact (creates Fact node and SUBJECT_OF edge)
            self.client.run(
                """
                CREATE (e:Entity {id: $e_id, name: $e_name})-[:SUBJECT_OF {role: 'subject'}]->(f:Fact {id: $f_id, content: $content, session_id: $sess_str, timestamp: $ts, valid_from: $ts, valid_to: -1, confidence: $conf})
                """,
                e_id=subj_int_id,
                e_name=subj_entity.canonical_name,
                f_id=fact_int_id,
                content=fact.content,
                sess_str=str(session.session_id),
                ts=fact_ts,
                conf=getattr(fact, "confidence", 1.0),
            )

            # 3. Connect Session -> Fact (CONTAINS)
            self.client.run(
                """
                CREATE (s:Session {id: $s_id})-[:CONTAINS]->(f:Fact {id: $f_id, content: $content})
                """,
                s_id=sess_int_id,
                f_id=fact_int_id,
                content=fact.content,
            )

            # 4. If Fact has an Object Entity, resolve and link Fact -> Object Entity
            if getattr(fact, "object_", None):
                obj_entity = resolver.resolve(fact.object_)
                obj_int_id = str_to_int_id(obj_entity.id)
                obj_alias_str = ", ".join(obj_entity.aliases)

                self.client.run(
                    """
                    CREATE (f:Fact {id: $f_id})-[:OBJECT_OF {role: 'object'}]->(o:Entity {id: $o_id, name: $o_name, entity_type: $o_type, aliases: $aliases, last_seen: $ts})
                    """,
                    f_id=fact_int_id,
                    o_id=obj_int_id,
                    o_name=obj_entity.canonical_name,
                    o_type=obj_entity.entity_type,
                    aliases=obj_alias_str,
                    ts=fact_ts,
                )

    def apply_temporal_relations(self, relations: List[TemporalRelation]) -> None:
        """Apply temporal relations as supersessions (valid_to update + SUPERSEDED_BY edge)."""
        for rel in relations:
            try:
                old_id = str_to_int_id(rel.old_fact_id)
                new_id = str_to_int_id(rel.new_fact_id)
                ts = getattr(rel, "superseded_at", 0) or int(hashlib.md5(str(new_id).encode()).hexdigest()[:8], 16)
                reason = getattr(rel, "reason", "updated")

                self.client.supersede_fact(old_id, new_id, reason=reason, superseded_at=ts)
            except Exception as e:
                logger.error(f"Failed to supersede fact {rel.old_fact_id} with {rel.new_fact_id}: {e}")
