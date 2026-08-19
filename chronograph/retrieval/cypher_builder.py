import logging
from typing import Any

from chronograph.retrieval.query_analyzer import AnalyzedQuery, QueryCategory

logger = logging.getLogger(__name__)


class CypherBuilder:
    def build_query(self, analyzed: AnalyzedQuery) -> list[tuple[str, dict[str, Any]]]:
        queries = []

        if not analyzed.entities:
            logger.warning("No entities found for cypher query builder.")
            return queries

        # Using -1 as sentinel for valid_to IS NULL (still current)

        if analyzed.category == QueryCategory.INFORMATION_EXTRACTION:
            for entity in analyzed.entities:
                q = (
                    "MATCH (e:Entity {name: $entity_name})-[:HAS_FACT]->(f:Fact {valid_to: -1}) "
                    "RETURN e.name AS entity, f.content AS fact, f.valid_from AS valid_from, f.valid_to AS valid_to"
                )
                queries.append((q, {"entity_name": entity}))

        elif analyzed.category == QueryCategory.TEMPORAL_REASONING:
            for entity in analyzed.entities:
                q = (
                    "MATCH (e:Entity {name: $entity_name})-[:HAS_FACT]->(f:Fact) "
                    "OPTIONAL MATCH (f)-[:SUPERSEDED_BY*]->(f_new:Fact) "
                    "RETURN e.name AS entity, f.content AS start_fact, f_new.content AS new_fact, f.valid_from AS valid_from "
                    "ORDER BY f.valid_from ASC"
                )
                queries.append((q, {"entity_name": entity}))

        elif analyzed.category == QueryCategory.MULTI_SESSION_REASONING:
            if len(analyzed.entities) >= 2:
                for i in range(len(analyzed.entities)):
                    for j in range(i + 1, len(analyzed.entities)):
                        q = "CALL algo.SPpaths($source, $target) YIELD path RETURN path"
                        queries.append(
                            (q, {"source": analyzed.entities[i], "target": analyzed.entities[j]})
                        )
            else:
                for entity in analyzed.entities:
                    q = (
                        "MATCH (e:Entity {name: $entity_name})-[:HAS_FACT]->(f:Fact) "
                        "RETURN e.name AS entity, f.content AS fact, f.session_id AS session_id"
                    )
                    queries.append((q, {"entity_name": entity}))

        elif analyzed.category == QueryCategory.KNOWLEDGE_UPDATE:
            for entity in analyzed.entities:
                q = (
                    "MATCH path = (f1:Fact)<-[:SUPERSEDED_BY*]-(fn:Fact) "
                    "MATCH (e:Entity {name: $entity_name})-[:HAS_FACT]->(f1) "
                    "RETURN path, e.name AS entity"
                )
                queries.append((q, {"entity_name": entity}))

        elif analyzed.category == QueryCategory.ABSTENTION:
            for entity in analyzed.entities:
                # Basic check first
                q = (
                    "MATCH (e:Entity {name: $entity_name}) "
                    "OPTIONAL MATCH (e)-[:HAS_FACT]->(f:Fact) "
                    "RETURN e.name AS entity, count(f) AS fact_count"
                )
                queries.append((q, {"entity_name": entity}))
                q2 = (
                    "MATCH (e:Entity {name: $entity_name})-[:HAS_FACT]->(f:Fact) "
                    "RETURN e.name AS entity, f.content AS fact"
                )
                queries.append((q2, {"entity_name": entity}))

        return queries
