"""Temporal ranking and scoring for retrieved graph facts."""

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
        seen_content: set[str] = set()

        for f_dict in facts:
            # Safely extract values, treating None as missing
            content = f_dict.get("content") or ""
            if not content or content in seen_content:
                continue  # Skip empty or duplicate facts
            seen_content.add(content)

            valid_from = f_dict.get("valid_from") or 0
            valid_to = f_dict.get("valid_to")
            session_id = f_dict.get("session_id") or "unknown"
            confidence = f_dict.get("confidence") or 0.5

            # HydraDB returns None for the -1 sentinel; treat None as "still current"
            is_current = valid_to is None or valid_to == -1

            score = float(confidence) * 10.0

            if prefer_current and is_current:
                score += 50.0

            # More recent facts get higher score
            score += float(valid_from) / 1e12

            ranked.append(
                RankedFact(
                    content=content,
                    score=score,
                    is_current=is_current,
                    valid_from=int(valid_from),
                    valid_to=int(valid_to) if valid_to is not None else -1,
                    session_id=str(session_id),
                )
            )

        ranked.sort(key=lambda x: x.score, reverse=True)
        return ranked

    def get_latest_for_topic(self, facts: list[RankedFact]) -> RankedFact | None:
        if not facts:
            return None
        return max(facts, key=lambda x: x.valid_from)
