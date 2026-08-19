"""Sample LongMemEval dataset generator across 5 evaluation categories."""

import json
from pathlib import Path

SESSIONS = [
    {
        "session_id": "session_01",
        "turns": [
            {"role": "user", "content": "Hi! My name is Jordan Lee and I work as a Senior Distributed Systems Engineer at CloudMatrix in Seattle."},
            {"role": "assistant", "content": "Hello Jordan! It's great to meet you. Working in distributed systems at CloudMatrix must be exciting. How can I help you today?"},
            {"role": "user", "content": "I'm working with my manager Elena Rostova on optimizing our Raft consensus cluster latency."}
        ]
    },
    {
        "session_id": "session_02",
        "turns": [
            {"role": "user", "content": "Hey, remember Elena? She just approved our migration to Rust for the new storage kernel."},
            {"role": "assistant", "content": "That's a big step! Rust is great for systems programming. How are you approaching the architecture?"},
            {"role": "user", "content": "We're using SlateDB for LSM storage and SuiteSparse GraphBLAS for sparse matrix traversals."}
        ]
    },
    {
        "session_id": "session_03",
        "turns": [
            {"role": "user", "content": "Big update: I just moved from Seattle to Zurich last week. Loving Switzerland so far!"},
            {"role": "assistant", "content": "Congratulations on the move to Zurich, Jordan! A new country is a wonderful adventure."},
            {"role": "user", "content": "Also, Elena got promoted to VP of Engineering, so Marco Rossi is my new engineering manager."}
        ]
    },
    {
        "session_id": "session_04",
        "turns": [
            {"role": "user", "content": "Quick question: Marco and I are presenting Project Hydra to our CEO Dr. Aris Thorne next Tuesday."},
            {"role": "assistant", "content": "Best of luck with the presentation to Dr. Thorne! What are the key highlights you'll present?"},
            {"role": "user", "content": "Our benchmark results show 180ms p99 latency across 10 million graph edges."}
        ]
    },
    {
        "session_id": "session_05",
        "turns": [
            {"role": "user", "content": "I decided to adopt a Golden Retriever puppy named Atlas yesterday. He's full of energy!"},
            {"role": "assistant", "content": "Atlas is a wonderful name for a Golden Retriever! Puppies bring so much joy."}
        ]
    }
]

BENCHMARK_QUESTIONS = [
    # 1. Information Extraction
    {
        "id": "q1_info_extraction",
        "category": "INFORMATION_EXTRACTION",
        "question": "What is Jordan Lee's pet name and breed?",
        "expected_answer": "Atlas, a Golden Retriever puppy.",
        "should_abstain": False
    },
    # 2. Multi-Session Reasoning
    {
        "id": "q2_multi_session",
        "category": "MULTI_SESSION_REASONING",
        "question": "What storage kernel and graph library did Elena Rostova approve for Jordan's team at CloudMatrix?",
        "expected_answer": "SlateDB for LSM storage and SuiteSparse GraphBLAS for sparse matrix traversals.",
        "should_abstain": False
    },
    # 3. Temporal Reasoning
    {
        "id": "q3_temporal_reasoning",
        "category": "TEMPORAL_REASONING",
        "question": "Where did Jordan Lee live before moving to Zurich?",
        "expected_answer": "Seattle.",
        "should_abstain": False
    },
    # 4. Knowledge Update
    {
        "id": "q4_knowledge_update",
        "category": "KNOWLEDGE_UPDATE",
        "question": "Who is Jordan Lee's current engineering manager?",
        "expected_answer": "Marco Rossi (Elena Rostova was promoted to VP).",
        "should_abstain": False
    },
    # 5. Abstention (Not in history)
    {
        "id": "q5_abstention_1",
        "category": "ABSTENTION",
        "question": "What university did Jordan Lee graduate from?",
        "expected_answer": "ABSTAIN (Not mentioned in memory).",
        "should_abstain": True
    },
    # 6. Abstention (Unrelated entity)
    {
        "id": "q6_abstention_2",
        "category": "ABSTENTION",
        "question": "What is Samantha's favorite programming language?",
        "expected_answer": "ABSTAIN (Samantha is not in memory).",
        "should_abstain": True
    }
]

def generate_sample_files(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "longmemeval_sessions.json", "w") as f:
        json.dump(SESSIONS, f, indent=2)
    with open(output_dir / "benchmark_questions.json", "w") as f:
        json.dump(BENCHMARK_QUESTIONS, f, indent=2)
    print(f"Generated sample dataset in {output_dir}")

if __name__ == "__main__":
    generate_sample_files(Path("/home/web-ghost/chronograph/data"))
