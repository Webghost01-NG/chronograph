"""Comprehensive test suite for ChronoGraph on HydraDB."""

import pytest

from chronograph.engine import ChronoGraphEngine
from chronograph.graph_client import HydraClient, str_to_int_id
from chronograph.ingestion.entity_resolver import EntityResolver
from chronograph.onchain.onchain_ingest import OnChainIngestor


@pytest.fixture(scope="module")
def hydra_client():
    client = HydraClient()
    assert client.wait_for_ready(timeout=10.0), "HydraDB must be running"
    yield client
    client.close()


@pytest.fixture(scope="module")
def engine(hydra_client):
    eng = ChronoGraphEngine()
    ingestor = OnChainIngestor(hydra_client)
    ingestor.ingest_all()
    yield eng
    eng.close()


def test_str_to_int_id():
    """Verify deterministic 63-bit positive integer IDs."""
    id1 = str_to_int_id("ent_alice")
    id2 = str_to_int_id("ent_alice")
    id3 = str_to_int_id("ent_bob")

    assert id1 == id2
    assert id1 != id3
    assert isinstance(id1, int)
    assert id1 > 0
    assert id1 < (1 << 63)  # Fits in signed int64


def test_entity_resolver():
    """Verify entity resolution and alias normalization."""
    resolver = EntityResolver()
    e1 = resolver.resolve("Uniswap", "Protocol")
    e2 = resolver.resolve("uniswap labs", "Protocol")
    e3 = resolver.resolve("Vitalik Buterin", "Person")

    assert e1.canonical_name == "Uniswap"
    assert e2.canonical_name == "Uniswap"  # Resolves alias
    assert e3.canonical_name == "Vitalik Buterin"


def test_graph_stats(hydra_client):
    """Verify graph contains ingested nodes and relationships."""
    stats = hydra_client.get_graph_stats()
    assert stats["entities"] > 0
    assert stats["facts"] > 0


def test_temporal_chain_traversal(engine):
    """Test temporal reasoning query on Uniswap evolution."""
    res = engine.query("How did Uniswap evolve from V1 to V2 to V3 and V4?")
    assert res["should_abstain"] is False
    assert res["facts_retrieved"] > 0
    assert "Uniswap" in res["evidence_context"] or "V4" in res["evidence_context"]


def test_exploit_forensics(engine):
    """Test multi-session reasoning on Euler Finance exploit & restitution."""
    res = engine.query("What was the Euler Finance exploit and what happened to the stolen assets?")
    assert res["should_abstain"] is False
    assert "Euler" in res["evidence_context"] or "197M" in res["evidence_context"]


def test_provable_abstention_unknown_entity(engine):
    """Test that querying an unknown entity provably abstains."""
    res = engine.query("What is the tokenomics distribution of Solana Foundation in 2021?")
    assert res["should_abstain"] is True
    assert "Graph structural check" in res["abstention_reason"]
    assert "don't have enough information" in res["answer"].lower()


def test_provable_abstention_arbitrary_query(engine):
    """Test that unrelated questions trigger structural abstention."""
    res = engine.query("What is the average transaction fee on Polygon PoS?")
    assert res["should_abstain"] is True
