"""Ingestion pipeline for authentic on-chain protocol temporal knowledge graph."""

from __future__ import annotations

import logging
from typing import Any

from chronograph.graph_client import HydraClient, str_to_int_id
from chronograph.onchain.protocol_data import (
    ONCHAIN_SUPERSEDED_CHAINS,
    ONCHAIN_TEMPORAL_FACTS,
)

logger = logging.getLogger(__name__)


class OnChainIngestor:
    """Ingests real on-chain protocols, contract deployments, and temporal evolutions into HydraDB."""

    def __init__(self, client: HydraClient):
        self.client = client

    def ingest_all(self) -> dict[str, Any]:
        """Ingest entities, facts, and supersession chains using one-hop edge patterns."""
        logger.info("Ingesting real on-chain protocol data into HydraDB...")
        root_sess_id = str_to_int_id("session_onchain_genesis")

        for fact in ONCHAIN_TEMPORAL_FACTS:
            f_int_id = str_to_int_id(fact["id"])
            subj_name = fact["subject"]
            subj_int_id = str_to_int_id(f"ent_{subj_name.lower().replace(' ', '_')}")

            # 1. Connect Genesis Session -> Subject Entity (creates Session & Entity)
            self.client.run(
                """
                CREATE (s:Session {id: $s_id, index: 0, summary: 'Ethereum Protocol Deployment'})-[:MENTIONS]->(e:Entity {id: $e_id, name: $name, entity_type: 'Protocol', aliases: $name, last_seen: $ts})
                """,
                s_id=root_sess_id,
                e_id=subj_int_id,
                name=subj_name,
                ts=fact["timestamp"],
            )

            # 2. Connect Subject Entity -> Fact
            self.client.run(
                """
                CREATE (e:Entity {id: $e_id, name: $name})-[:SUBJECT_OF {role: 'subject'}]->(f:Fact {id: $f_id, content: $content, session_id: 'onchain_genesis', timestamp: $ts, valid_from: $vf, valid_to: $vt, confidence: 1.0})
                """,
                e_id=subj_int_id,
                name=subj_name,
                f_id=f_int_id,
                content=fact["content"],
                ts=fact["timestamp"],
                vf=fact["valid_from"],
                vt=fact["valid_to"],
            )

            # 3. If fact has an Object Entity (e.g. Contract address or EIP), create and link
            if "object" in fact:
                obj_name = fact["object"]
                obj_int_id = str_to_int_id(f"ent_{obj_name.lower().replace(' ', '_')}")
                self.client.run(
                    """
                    CREATE (f:Fact {id: $f_id, content: $content})-[:OBJECT_OF {role: 'object'}]->(o:Entity {id: $o_id, name: $name, entity_type: 'Contract_Or_Standard', aliases: $name, last_seen: $ts})
                    """,
                    f_id=f_int_id,
                    content=fact["content"],
                    o_id=obj_int_id,
                    name=obj_name,
                    ts=fact["timestamp"],
                )

        # 4. Apply Superseded Chains
        for old_id, new_id, reason, ts in ONCHAIN_SUPERSEDED_CHAINS:
            self.client.supersede_fact(old_id, new_id, reason=reason, superseded_at=ts)

        stats = self.client.get_graph_stats()
        logger.info("On-chain protocol knowledge graph successfully ingested: %s", stats)
        return stats
