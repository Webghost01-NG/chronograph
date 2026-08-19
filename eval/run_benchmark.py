"""Benchmark evaluation harness for ChronoGraph on LongMemEval and On-Chain Temporal Datasets."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List

from chronograph.engine import ChronoGraphEngine
from chronograph.onchain.onchain_ingest import OnChainIngestor
from chronograph.graph_client import HydraClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_onchain_benchmark(engine: ChronoGraphEngine) -> Dict[str, Any]:
    """Run real on-chain protocol temporal memory questions."""
    questions = [
        {
            "id": "eth_01_temporal",
            "category": "TEMPORAL_REASONING",
            "question": "How did Uniswap's liquidity mechanism evolve from V2 to V3 and V4?",
            "must_contain": ["Concentrated Liquidity", "Hooks", "Singleton"],
            "must_not_contain": [],
            "should_abstain": False,
        },
        {
            "id": "eth_02_exploit",
            "category": "MULTI_SESSION_REASONING",
            "question": "What was the Euler Finance exploit and what happened to the stolen assets?",
            "must_contain": ["197M", "returned", "Euler"],
            "must_not_contain": [],
            "should_abstain": False,
        },
        {
            "id": "eth_03_eip",
            "category": "KNOWLEDGE_UPDATE",
            "question": "What Ethereum upgrade introduced blobspace for L2 rollup gas reduction?",
            "must_contain": ["Dencun", "EIP-4844", "Blob"],
            "must_not_contain": [],
            "should_abstain": False,
        },
        {
            "id": "eth_04_abstain_1",
            "category": "ABSTENTION",
            "question": "What was the genesis allocation percentage for the Solana Foundation?",
            "must_contain": [],
            "must_not_contain": [],
            "should_abstain": True,
        },
        {
            "id": "eth_05_abstain_2",
            "category": "ABSTENTION",
            "question": "What is the staking reward APR for Cardano ADA in 2024?",
            "must_contain": [],
            "must_not_contain": [],
            "should_abstain": True,
        },
    ]

    results = []
    correct_by_cat: Dict[str, int] = {}
    total_by_cat: Dict[str, int] = {}

    for q in questions:
        cat = q["category"]
        total_by_cat[cat] = total_by_cat.get(cat, 0) + 1

        t0 = time.time()
        res = engine.query(q["question"])
        elapsed = (time.time() - t0) * 1000.0

        is_correct = False
        if q["should_abstain"]:
            is_correct = res["should_abstain"] is True
        else:
            if not res["should_abstain"]:
                ans = (res["answer"] + " " + res["evidence_context"]).lower()
                matches = sum(1 for kw in q["must_contain"] if kw.lower() in ans)
                is_correct = matches >= max(1, len(q["must_contain"]) // 2)

        if is_correct:
            correct_by_cat[cat] = correct_by_cat.get(cat, 0) + 1

        results.append({
            "id": q["id"],
            "category": cat,
            "question": q["question"],
            "should_abstain": q["should_abstain"],
            "model_abstained": res["should_abstain"],
            "is_correct": is_correct,
            "latency_ms": round(elapsed, 2),
            "answer_preview": res["answer"][:100],
        })

    cat_accuracy = {
        cat: f"{round(correct_by_cat.get(cat, 0) / total_by_cat[cat] * 100, 1)}%"
        for cat in total_by_cat
    }

    total_correct = sum(correct_by_cat.values())
    total_q = sum(total_by_cat.values())
    overall_acc = f"{round(total_correct / total_q * 100, 1)}%"

    return {
        "dataset": "OnChain_Temporal_Benchmark",
        "total_questions": total_q,
        "total_correct": total_correct,
        "overall_accuracy": overall_acc,
        "category_accuracy": cat_accuracy,
        "question_results": results,
    }


def main():
    logger.info("Initializing ChronoGraph Benchmark Evaluation...")
    client = HydraClient()
    ingestor = OnChainIngestor(client)
    ingestor.ingest_all()

    engine = ChronoGraphEngine()
    report = run_onchain_benchmark(engine)

    output_path = Path("/home/web-ghost/chronograph/results/scores.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info("Benchmark complete! Overall Accuracy: %s", report["overall_accuracy"])
    logger.info("Category breakdown: %s", report["category_accuracy"])
    print("\n" + json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
