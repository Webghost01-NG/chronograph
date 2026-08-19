"""Configuration and connection management for ChronoGraph."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class HydraConfig:
    """HydraDB connection settings."""

    bolt_uri: str = field(default_factory=lambda: os.getenv("HYDRA_BOLT_URI", "neo4j://127.0.0.1:7687"))
    http_uri: str = field(default_factory=lambda: os.getenv("HYDRA_HTTP_URI", "http://127.0.0.1:8443"))
    auth_token: str = field(default_factory=lambda: os.getenv("HYDRA_AUTH_TOKEN", "local-development-token-32-bytes"))
    graph_namespace: str = "default"
    graph_id: str = "default"
    cell_id: str = "cell-0"

    @property
    def auth(self) -> tuple[str, str]:
        """Return (username, password) tuple for Neo4j driver. Username is ignored by HydraDB but required."""
        return ("neo4j", self.auth_token)


@dataclass(frozen=True)
class LLMConfig:
    """LLM settings for extraction and synthesis."""

    extraction_model: str = field(default_factory=lambda: os.getenv("EXTRACTION_MODEL", "gpt-4.1-mini"))
    synthesis_model: str = field(default_factory=lambda: os.getenv("SYNTHESIS_MODEL", "gpt-4.1"))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    max_concurrent_extractions: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONCURRENT_EXTRACTIONS", "5"))
    )
    extraction_batch_size: int = field(
        default_factory=lambda: int(os.getenv("EXTRACTION_BATCH_SIZE", "10"))
    )


@dataclass(frozen=True)
class AppConfig:
    """Top-level application configuration."""

    hydra: HydraConfig = field(default_factory=HydraConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    project_root: Path = _PROJECT_ROOT
    data_dir: Path = field(default_factory=lambda: _PROJECT_ROOT / "data")
    results_dir: Path = field(default_factory=lambda: _PROJECT_ROOT / "results")


def get_config() -> AppConfig:
    """Get the application configuration singleton."""
    return AppConfig()
