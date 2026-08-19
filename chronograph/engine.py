"""ChronoGraph Unified Engine — Coordinates Ingestion, Graph Storage, Retrieval, and Synthesis."""

from __future__ import annotations

import logging
import time
from typing import Any

from chronograph.config import AppConfig, get_config
from chronograph.graph_client import HydraClient
from chronograph.ingestion.entity_resolver import EntityResolver
from chronograph.ingestion.graph_writer import GraphWriter
from chronograph.ingestion.temporal_tagger import TemporalTagger
from chronograph.retrieval.abstention import AbstentionDetector, AbstentionResult
from chronograph.retrieval.path_retriever import PathRetriever
from chronograph.retrieval.query_analyzer import AnalyzedQuery, QueryAnalyzer
from chronograph.retrieval.subgraph_context import SubgraphContext
from chronograph.retrieval.temporal_ranker import RankedFact, TemporalRanker
from chronograph.synthesis.answer_generator import AnswerGenerator

logger = logging.getLogger(__name__)


class ChronoGraphEngine:
    """End-to-end Graph-Native Agent Memory Engine on HydraDB."""

    def __init__(self, config: AppConfig | None = None):
        self.config = config or get_config()
        self.client = HydraClient(self.config.hydra)
        self.resolver = EntityResolver()
        self.writer = GraphWriter(self.client)
        self.tagger = TemporalTagger()
        self.analyzer = QueryAnalyzer()
        self.path_retriever = PathRetriever(self.client)
        self.ranker = TemporalRanker()
        self.abstention_detector = AbstentionDetector(self.client)
        self.context_formatter = SubgraphContext()
        self.synthesizer = AnswerGenerator()

    def initialize(self) -> bool:
        """Verify HydraDB connection."""
        return self.client.wait_for_ready(timeout=15.0)

    def query(self, question: str) -> dict[str, Any]:
        """Execute a graph-native memory query with temporal resolution and abstention."""
        start_time = time.time()

        # Step 1: Query Analysis & Classification
        analyzed: AnalyzedQuery = self.analyzer.analyze(question)

        # Step 2: Graph-Structural Abstention Check
        abstention: AbstentionResult = self.abstention_detector.check(
            analyzed.entities, analyzed.keywords
        )

        paths: list[dict[str, Any]] = []
        ranked_facts: list[RankedFact] = []
        raw_facts: list[dict[str, Any]] = []

        if not abstention.should_abstain:
            # Step 3: Retrieve Entity Facts for all matched entities in coverage
            matched_entities = list(abstention.coverage.keys()) or analyzed.entities
            for entity in matched_entities:
                prefer_current = not analyzed.temporal_cue
                e_facts = self.client.get_entity_facts(entity, current_only=prefer_current)
                raw_facts.extend(e_facts)

            # Step 4: Multi-Hop Path Retrieval (algo.SPpaths) if multiple entities
            if len(matched_entities) >= 2:
                for i in range(len(matched_entities) - 1):
                    src = matched_entities[i]
                    tgt = matched_entities[i + 1]
                    found_paths = self.path_retriever.find_connection(src, tgt, max_hops=3)
                    paths.extend(found_paths)

            # Step 5: Temporal Ranking
            ranked_facts = self.ranker.rank(raw_facts, prefer_current=not analyzed.temporal_cue)

        # Step 6: Subgraph Context Formatting
        context_str = self.context_formatter.format_for_llm(ranked_facts, paths=paths)

        # Step 7: Answer Synthesis
        answer = self.synthesizer.generate(
            question=question,
            context=context_str,
            should_abstain=abstention.should_abstain,
        )

        latency_ms = (time.time() - start_time) * 1000.0

        return {
            "question": question,
            "answer": answer,
            "category": analyzed.category.value,
            "entities": analyzed.entities,
            "keywords": analyzed.keywords,
            "should_abstain": abstention.should_abstain,
            "abstention_reason": abstention.reason if abstention.should_abstain else None,
            "facts_retrieved": len(ranked_facts),
            "paths_discovered": len(paths),
            "evidence_context": context_str,
            "latency_ms": round(latency_ms, 2),
        }

    def close(self):
        self.client.close()
