"""CLI Demonstration Runner for ChronoGraph."""

from chronograph.engine import ChronoGraphEngine

def run_demo():
    engine = ChronoGraphEngine()

    queries = [
        "How did Uniswap evolve from V1 to V2 to V3 and V4?",
        "What caused the Euler Finance exploit and was the stolen money recovered?",
        "What was the genesis allocation percentage for the Solana Foundation?"
    ]

    print("=" * 80)
    print("🧠 CHRONOGRAPH LIVE DEMO EXECUTION ON HYDRADB")
    print("=" * 80)

    for idx, q in enumerate(queries, 1):
        res = engine.query(q)
        q_text = res["question"]
        cat = res["category"]
        abstain = res["should_abstain"]
        reason = res.get("abstention_reason")
        latency = res["latency_ms"]
        evidence = res["evidence_context"]
        answer = res["answer"]

        print(f"\n[{idx}] ❓ QUESTION: {q_text}")
        print(f"    🏷️  CATEGORY: {cat}")
        print(f"    🛡️  ABSTAIN TRIGGERED: {abstain}")
        if abstain:
            print(f"    ⚠️  REASON: {reason}")
        print(f"    ⚡ LATENCY: {latency} ms")
        print(f"    📄 EVIDENCE SUBGRAPH:\n{evidence}")
        print(f"    🤖 ANSWER:\n{answer}")
        print("-" * 80)

if __name__ == "__main__":
    run_demo()
