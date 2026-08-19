"""Fact extraction from chat sessions using structured LLM output."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass

from openai import OpenAI

from chronograph.config import get_config
from chronograph.ingestion.session_parser import ChatSession

logger = logging.getLogger(__name__)


@dataclass
class ExtractedFact:
    content: str
    subject: str
    fact_type: str = "preference"
    confidence: float = 1.0
    object_: str | None = None
    relation: str | None = None
    timestamp: int = 0


class FactExtractor:
    def __init__(self):
        self.config = get_config()
        api_key = self.config.llm.openai_api_key or "mock-key"
        self.client = OpenAI(api_key=api_key)
        self.model = self.config.llm.extraction_model

    def extract_facts(self, session: ChatSession) -> list[ExtractedFact]:
        """Extract atomic facts using OpenAI API with structured JSON output."""
        system_prompt = (
            "You are an expert information extraction system. "
            "Extract atomic facts from the following conversation session. "
            "Each fact must include a subject, optionally an object and relation, "
            "and a fact_type ('preference', 'biographical', 'event', 'opinion', 'relationship'). "
            "Provide output as JSON in the format: "
            '{"facts": [{"content": "...", "subject": "...", "object_": "...", "relation": "...", "fact_type": "...", "confidence": 0.9}]}'
        )

        conversation_text = "\n".join([f"{turn.role}: {turn.content}" for turn in session.turns])
        session_ts = getattr(session, "started_at", 0)

        max_retries = 3
        base_delay = 2

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": conversation_text},
                    ],
                    temperature=0.0,
                )

                content = response.choices[0].message.content
                data = json.loads(content)

                facts = []
                for item in data.get("facts", []):
                    facts.append(
                        ExtractedFact(
                            content=item.get("content", ""),
                            subject=item.get("subject", "User"),
                            object_=item.get("object_"),
                            relation=item.get("relation"),
                            fact_type=item.get("fact_type", "opinion"),
                            confidence=float(item.get("confidence", 1.0)),
                            timestamp=session_ts,
                        )
                    )
                return facts

            except Exception as e:
                logger.warning(
                    f"Failed to extract facts (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(base_delay ** (attempt + 1))
                else:
                    logger.error("Max retries reached for fact extraction.")
                    # Heuristic fallback extraction for resilience
                    fallback_facts = []
                    for turn in session.turns:
                        if turn.role == "user" and len(turn.content) > 10:
                            fallback_facts.append(
                                ExtractedFact(
                                    content=turn.content,
                                    subject="User",
                                    fact_type="statement",
                                    confidence=0.8,
                                    timestamp=session_ts,
                                )
                            )
                    return fallback_facts
        return []
