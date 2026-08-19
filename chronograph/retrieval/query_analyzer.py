"""Query analysis and intent classification for ChronoGraph."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum

from openai import OpenAI

from chronograph.config import get_config

logger = logging.getLogger(__name__)


class QueryCategory(Enum):
    INFORMATION_EXTRACTION = "INFORMATION_EXTRACTION"
    MULTI_SESSION_REASONING = "MULTI_SESSION_REASONING"
    TEMPORAL_REASONING = "TEMPORAL_REASONING"
    KNOWLEDGE_UPDATE = "KNOWLEDGE_UPDATE"
    ABSTENTION = "ABSTENTION"


@dataclass
class AnalyzedQuery:
    original: str
    category: QueryCategory
    entities: list[str]
    keywords: list[str]
    temporal_cue: bool
    requires_comparison: bool


class QueryAnalyzer:
    def __init__(self):
        self.config = get_config()
        self.llm_config = self.config.llm
        api_key = self.llm_config.openai_api_key or "mock-key"
        self.client = OpenAI(api_key=api_key)

    def _detect_cues(self, question: str, cue_words: list[str]) -> bool:
        q_lower = question.lower()
        return any(cue in q_lower for cue in cue_words)

    def _heuristic_entities_keywords(self, question: str) -> tuple[list[str], list[str]]:
        """Extract capitalized words as entities, other words as keywords."""
        words = re.findall(r"\b\w+\b", question)
        entities = [
            w
            for w in words
            if w[0].isupper()
            and w.lower() not in {"what", "where", "when", "how", "who", "why", "did", "is", "was"}
        ]
        keywords = [
            w.lower()
            for w in words
            if len(w) > 3
            and w.lower()
            not in {"what", "where", "when", "how", "who", "why", "does", "have", "that", "this"}
        ]
        return entities, keywords

    def analyze(self, question: str) -> AnalyzedQuery:
        temporal_cues = [
            "before",
            "after",
            "changed",
            "used to",
            "previously",
            "when did",
            "earlier",
            "originally",
        ]
        comparison_cues = ["compare", "difference", "both", "and", "between", "versus", "vs"]

        has_temporal = self._detect_cues(question, temporal_cues)
        has_comparison = self._detect_cues(question, comparison_cues)

        prompt = (
            f"Analyze the following question and extract entities and keywords. "
            f"Classify it into one of these categories: INFORMATION_EXTRACTION, MULTI_SESSION_REASONING, "
            f"TEMPORAL_REASONING, KNOWLEDGE_UPDATE, ABSTENTION.\n"
            f"Question: {question}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.llm_config.extraction_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that analyzes questions and outputs JSON with keys 'category', 'entities', and 'keywords'.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)
            category_str = result.get("category", "INFORMATION_EXTRACTION").upper()
            try:
                category = QueryCategory[category_str]
            except KeyError:
                category = QueryCategory.INFORMATION_EXTRACTION

            entities = result.get("entities", [])
            keywords = result.get("keywords", [])

        except Exception as e:
            logger.warning(f"Using heuristic query analyzer: {e}")
            if has_temporal:
                category = QueryCategory.TEMPORAL_REASONING
            elif has_comparison:
                category = QueryCategory.MULTI_SESSION_REASONING
            else:
                category = QueryCategory.INFORMATION_EXTRACTION
            entities, keywords = self._heuristic_entities_keywords(question)

        # Fallback if no entities extracted
        if not entities:
            h_entities, _ = self._heuristic_entities_keywords(question)
            entities = h_entities or ["User"]

        return AnalyzedQuery(
            original=question,
            category=category,
            entities=entities,
            keywords=keywords,
            temporal_cue=has_temporal,
            requires_comparison=has_comparison,
        )
