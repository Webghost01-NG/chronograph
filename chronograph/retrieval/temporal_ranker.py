import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RankedFact:
    content: str
    score: float
    is_current: bool
    valid_from: int
    valid_to: int
    session_id: str


class TemporalRanker:
    def rank(self, facts: list[dict[str, Any]], prefer_current: bool = True) -> list[RankedFact]:
        ranked = []
        for f_dict in facts:
            # Safely extract values
            content = f_dict.get("content", "")
            valid_from = f_dict.get("valid_from", 0)
            valid_to = f_dict.get("valid_to", -1)
            session_id = f_dict.get("session_id", "unknown")
            confidence = f_dict.get("confidence", 0.5)

            is_current = valid_to == -1

            score = confidence * 10.0

            if prefer_current and is_current:
                score += 50.0

            # more recent gets higher score (assuming valid_from is timestamp)
            # Add a small boost for valid_from
            score += valid_from / 1e12  # arbitrary scaling for timestamp

            ranked.append(
                RankedFact(
                    content=content,
                    score=score,
                    is_current=is_current,
                    valid_from=valid_from,
                    valid_to=valid_to,
                    session_id=session_id,
                )
            )

        ranked.sort(key=lambda x: x.score, reverse=True)
        return ranked

    def get_latest_for_topic(self, facts: list[RankedFact]) -> RankedFact | None:
        if not facts:
            return None
        return max(facts, key=lambda x: x.valid_from)
