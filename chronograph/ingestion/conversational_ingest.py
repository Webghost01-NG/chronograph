"""Ingestion pipeline for multi-session conversational agent memory into HydraDB."""

from __future__ import annotations

import logging
from typing import Dict, Any

from chronograph.graph_client import HydraClient, str_to_int_id

logger = logging.getLogger(__name__)

CONVERSATIONAL_FACTS = [
    # ── Session 1 ──
    {
        "id": "fact_jordan_job_1",
        "subject": "Jordan Lee",
        "object": "CloudMatrix",
        "content": "Jordan Lee works as a Senior Distributed Systems Engineer at CloudMatrix in Seattle.",
        "session_id": "session_01",
        "timestamp": 1700000000000,
        "valid_from": 1700000000000,
        "valid_to": 1705000000000,  # Superseded when moved to Zurich
    },
    {
        "id": "fact_jordan_location_seattle",
        "subject": "Jordan Lee",
        "object": "Seattle",
        "content": "Jordan Lee lives in Seattle, Washington.",
        "session_id": "session_01",
        "timestamp": 1700000000000,
        "valid_from": 1700000000000,
        "valid_to": 1705000000000,  # Superseded by move to Zurich
    },
    {
        "id": "fact_jordan_manager_elena",
        "subject": "Jordan Lee",
        "object": "Elena Rostova",
        "content": "Elena Rostova is Jordan Lee's engineering manager at CloudMatrix.",
        "session_id": "session_01",
        "timestamp": 1700000000000,
        "valid_from": 1700000000000,
        "valid_to": 1705000000000,  # Superseded when Elena promoted to VP
    },
    # ── Session 2 ──
    {
        "id": "fact_elena_approved_stack",
        "subject": "Elena Rostova",
        "object": "SlateDB",
        "content": "Elena Rostova approved the migration to Rust using SlateDB for LSM storage and SuiteSparse GraphBLAS for sparse matrix traversals.",
        "session_id": "session_02",
        "timestamp": 1702000000000,
        "valid_from": 1702000000000,
        "valid_to": -1,
    },
    # ── Session 3 (Updates & Supersessions) ──
    {
        "id": "fact_jordan_location_zurich",
        "subject": "Jordan Lee",
        "object": "Zurich",
        "content": "Jordan Lee moved from Seattle to Zurich, Switzerland.",
        "session_id": "session_03",
        "timestamp": 1705000000000,
        "valid_from": 1705000000000,
        "valid_to": -1,
    },
    {
        "id": "fact_jordan_manager_marco",
        "subject": "Jordan Lee",
        "object": "Marco Rossi",
        "content": "Marco Rossi is Jordan Lee's new engineering manager following Elena Rostova's promotion to VP of Engineering.",
        "session_id": "session_03",
        "timestamp": 1705000000000,
        "valid_from": 1705000000000,
        "valid_to": -1,
    },
    # ── Session 4 ──
    {
        "id": "fact_project_hydra_perf",
        "subject": "Marco Rossi",
        "object": "Project Hydra",
        "content": "Marco Rossi and Jordan Lee are presenting Project Hydra to CEO Dr. Aris Thorne with benchmark results showing 180ms p99 latency across 10 million graph edges.",
        "session_id": "session_04",
        "timestamp": 1708000000000,
        "valid_from": 1708000000000,
        "valid_to": -1,
    },
    # ── Session 5 ──
    {
        "id": "fact_jordan_puppy_atlas",
        "subject": "Jordan Lee",
        "object": "Atlas",
        "content": "Jordan Lee adopted a Golden Retriever puppy named Atlas.",
        "session_id": "session_05",
        "timestamp": 1710000000000,
        "valid_from": 1710000000000,
        "valid_to": -1,
    },
]

CONVERSATIONAL_SUPERSEDED_CHAINS = [
    ("fact_jordan_location_seattle", "fact_jordan_location_zurich", "relocation_to_switzerland", 1705000000000),
    ("fact_jordan_manager_elena", "fact_jordan_manager_marco", "manager_promotion_reassignment", 1705000000000),
]


class ConversationalIngestor:
    """Ingests multi-session chat memories with temporal supersessions into HydraDB."""

    def __init__(self, client: HydraClient):
        self.client = client

    def ingest_all(self) -> Dict[str, Any]:
        """Ingest all conversational sessions, entities, and facts into HydraDB."""
        logger.info("Ingesting multi-session conversation dataset into HydraDB...")

        for fact in CONVERSATIONAL_FACTS:
            f_int_id = str_to_int_id(fact["id"])
            subj_name = fact["subject"]
            subj_int_id = str_to_int_id(f"ent_{subj_name.lower().replace(' ', '_')}")
            sess_str = fact["session_id"]
            sess_int_id = str_to_int_id(sess_str)

            # 1. Connect Session -> Subject Entity
            self.client.run(
                """
                CREATE (s:Session {id: $s_id, index: 1, summary: 'Multi-Session Conversation'})-[:MENTIONS]->(e:Entity {id: $e_id, name: $name, entity_type: 'Person', aliases: $name, last_seen: $ts})
                """,
                s_id=sess_int_id,
                e_id=subj_int_id,
                name=subj_name,
                ts=fact["timestamp"],
            )

            # 2. Connect Subject Entity -> Fact
            self.client.run(
                """
                CREATE (e:Entity {id: $e_id, name: $name})-[:SUBJECT_OF {role: 'subject'}]->(f:Fact {id: $f_id, content: $content, session_id: $sess_str, timestamp: $ts, valid_from: $vf, valid_to: $vt, confidence: 1.0})
                """,
                e_id=subj_int_id,
                name=subj_name,
                f_id=f_int_id,
                content=fact["content"],
                sess_str=sess_str,
                ts=fact["timestamp"],
                vf=fact["valid_from"],
                vt=fact["valid_to"],
            )

            # 3. Link Object Entity if present
            if "object" in fact:
                obj_name = fact["object"]
                obj_int_id = str_to_int_id(f"ent_{obj_name.lower().replace(' ', '_')}")
                self.client.run(
                    """
                    CREATE (f:Fact {id: $f_id, content: $content})-[:OBJECT_OF {role: 'object'}]->(o:Entity {id: $o_id, name: $name, entity_type: 'Concept_Or_Entity', aliases: $name, last_seen: $ts})
                    """,
                    f_id=f_int_id,
                    content=fact["content"],
                    o_id=obj_int_id,
                    name=obj_name,
                    ts=fact["timestamp"],
                )

        # 4. Apply Superseded Chains
        for old_id, new_id, reason, ts in CONVERSATIONAL_SUPERSEDED_CHAINS:
            self.client.supersede_fact(old_id, new_id, reason=reason, superseded_at=ts)

        stats = self.client.get_graph_stats()
        logger.info("Conversational memory knowledge graph successfully ingested: %s", stats)
        return stats
