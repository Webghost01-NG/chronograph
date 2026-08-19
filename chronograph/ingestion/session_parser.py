import json
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ChatTurn:
    role: str
    content: str
    turn_index: int


@dataclass
class ChatSession:
    session_id: str
    index: int
    turns: list[ChatTurn]
    started_at: int
    ended_at: int


def parse_longmemeval(data_path: Path) -> list[ChatSession]:
    """Parse LongMemEval chat sessions from JSON."""
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Assuming format: list of sessions, each session is a list of dicts with 'role' and 'content'
    # or similar structure.
    sessions = []

    # Generate synthetic timestamps starting from a recent point
    base_time = int(time.time() * 1000) - (len(data) * 24 * 3600 * 1000)

    for session_idx, session_data in enumerate(data):
        session_start = base_time + (session_idx * 24 * 3600 * 1000)  # 1 day apart

        turns = []
        # Support different potential structures
        messages = (
            session_data if isinstance(session_data, list) else session_data.get("messages", [])
        )

        current_time = session_start
        for turn_idx, msg in enumerate(messages):
            turns.append(
                ChatTurn(
                    role=msg.get("role", "unknown"),
                    content=msg.get("content", ""),
                    turn_index=turn_idx,
                )
            )
            current_time += 5 * 60 * 1000  # 5 minutes apart

        sessions.append(
            ChatSession(
                session_id=f"session_{session_idx}",
                index=session_idx,
                turns=turns,
                started_at=session_start,
                ended_at=current_time,
            )
        )

    return sessions
