import hashlib
from dataclasses import dataclass

from rapidfuzz import fuzz

from chronograph.ingestion.fact_extractor import ExtractedFact


@dataclass
class TemporalRelation:
    old_fact_id: str
    new_fact_id: str
    reason: str


class TemporalTagger:
    def __init__(self):
        self.contradiction_markers = ["actually", "changed", "no longer", "moved to", "switched to"]

    def _generate_fact_id(self, content: str, session_id: str) -> str:
        return hashlib.sha256(f"{content}:{session_id}".encode()).hexdigest()

    def detect_supersessions(
        self, facts_by_entity: dict[str, list[tuple[ExtractedFact, str]]]
    ) -> list[TemporalRelation]:
        """
        Detect temporal relations based on fact contents and markers.
        Takes a dict of entity canonical names to a list of (fact, session_id) tuples ordered by time.
        """
        relations = []

        for entity_name, facts in facts_by_entity.items():
            for i in range(len(facts)):
                for j in range(i + 1, len(facts)):
                    old_fact, old_session = facts[i]
                    new_fact, new_session = facts[j]

                    old_id = self._generate_fact_id(old_fact.content, old_session)
                    new_id = self._generate_fact_id(new_fact.content, new_session)

                    # High similarity could mean topic match but different value
                    similarity = fuzz.partial_ratio(
                        old_fact.content.lower(), new_fact.content.lower()
                    )

                    if similarity > 70 and old_fact.content != new_fact.content:
                        relations.append(
                            TemporalRelation(
                                old_fact_id=old_id, new_fact_id=new_id, reason="temporal_update"
                            )
                        )
                    else:
                        # Check markers
                        for marker in self.contradiction_markers:
                            if marker in new_fact.content.lower():
                                relations.append(
                                    TemporalRelation(
                                        old_fact_id=old_id,
                                        new_fact_id=new_id,
                                        reason="user_correction",
                                    )
                                )
                                break

        return relations
