"""Graph-structural abstention detector for ChronoGraph."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any

from chronograph.graph_client import HydraClient

logger = logging.getLogger(__name__)


@dataclass
class AbstentionResult:
    should_abstain: bool
    reason: str
    coverage: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class AbstentionDetector:
    """Detects whether an agent should abstain based on graph structural coverage."""

    def __init__(self, client: HydraClient, coverage_threshold: int = 1):
        self.client = client
        self.coverage_threshold = coverage_threshold

    def check(self, entity_names: List[str], keywords: List[str] | None = None) -> AbstentionResult:
        if not entity_names:
            return AbstentionResult(
                should_abstain=True,
                reason="No known entities identified in the query.",
                coverage={},
            )

        coverage: Dict[str, Dict[str, Any]] = {}
        has_relevant_fact = False

        # Get all known entity names in graph for fuzzy/partial matching
        all_graph_entities = self.client.run("MATCH (e:Entity) RETURN e.name AS name, e.aliases AS aliases")
        graph_name_map = {row["name"].lower(): row["name"] for row in all_graph_entities}

        matched_canonical_names = set()
        for q_ent in entity_names:
            q_lower = q_ent.lower()
            # Exact match
            if q_lower in graph_name_map:
                matched_canonical_names.add(graph_name_map[q_lower])
            else:
                # Substring match (e.g. "Euler" matching "Euler Finance" or vice versa)
                for g_lower, g_canon in graph_name_map.items():
                    if q_lower in g_lower or g_lower in q_lower:
                        matched_canonical_names.add(g_canon)

        if not matched_canonical_names:
            return AbstentionResult(
                should_abstain=True,
                reason=f"Graph structural check: None of the queried entities ({entity_names}) exist in the memory graph.",
                coverage={name: {"exists": False, "fact_count": 0} for name in entity_names},
            )

        kws = [k.lower() for k in (keywords or []) if len(k) > 2]

        for canon_name in matched_canonical_names:
            facts = self.client.get_entity_facts(canon_name, current_only=False)
            exists = len(facts) > 0

            # Match against keywords if provided
            if kws:
                matching_facts = [
                    f for f in facts if any(k in f.get("content", "").lower() for k in kws)
                ]
                # If keyword filter is too strict, keep all entity facts
                if not matching_facts:
                    matching_facts = facts
            else:
                matching_facts = facts

            fact_count = len(matching_facts)
            coverage[canon_name] = {
                "exists": exists,
                "fact_count": fact_count,
                "facts": [f.get("content", "") for f in matching_facts[:5]],
            }

            if fact_count > 0:
                has_relevant_fact = True

        if not has_relevant_fact:
            return AbstentionResult(
                should_abstain=True,
                reason="Graph structural check: Entities exist but have no connected facts.",
                coverage=coverage,
            )

        return AbstentionResult(
            should_abstain=False,
            reason="Sufficient graph evidence found.",
            coverage=coverage,
        )
