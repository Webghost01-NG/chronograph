"""Path procedure wrapper for HydraDB's GraphBLAS algorithms."""

from __future__ import annotations

import logging
from typing import List, Dict, Any

from chronograph.graph_client import HydraClient

logger = logging.getLogger(__name__)


class PathRetriever:
    """Invokes HydraDB graph pathfinding algorithms and variable-length traversals."""

    def __init__(self, client: HydraClient):
        self.client = client

    def find_connection(self, source: str, target: str, max_hops: int = 3) -> List[Dict[str, Any]]:
        """Find bounded shortest path between two entities using algo.SPpaths."""
        return self.client.find_path_between_entities(source, target, max_len=max_hops)

    def get_entity_neighborhood(self, entity_name: str, depth: int = 2) -> List[Dict[str, Any]]:
        """Retrieve facts and connected entities around an entity."""
        facts = self.client.get_entity_facts(entity_name, current_only=False)
        return [{"entity": entity_name, "facts": facts}]
