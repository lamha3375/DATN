
from typing import Dict, List, Any, Optional

from app.services.graph_service import GraphService


class GraphSearchService:

    MAX_ENTITY_RESULTS = 10
    MAX_RELATIONSHIPS = 30
    MAX_NEIGHBORS = 50

    # Các thuộc tính thường dùng để lưu tên node
    NAME_FIELDS = (
        "name",
        "entity",
        "ten",
        "title"
    )

    def __init__(self, graph_service: GraphService):
        self.graph_service = graph_service

    # =====================================================
    # 1. SEARCH ENTITIES
    # =====================================================

    def search_entities(
        self,
        keywords: List[str],
        limit: int = MAX_ENTITY_RESULTS
    ) -> List[Dict[str, Any]]:

        if not keywords:
            return []

        limit = max(1, min(limit, self.MAX_ENTITY_RESULTS))

        graph = self.graph_service.get_graph(limit=1000)

        candidates = []

        for node in graph["nodes"]:

            properties = node["properties"]

            name = self._get_node_name(properties)

            if not name:
                continue

            score, matched_terms = self._calculate_match_score(
                name,
                properties,
                keywords
            )

            if score <= 0:
                continue

            candidates.append({
                "id": node["id"],
                "name": name,
                "labels": node["labels"],
                "properties": properties,
                "score": score,
                "matched_terms": matched_terms
            })

        candidates.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return candidates[:limit]

    # =====================================================
    # 2. SEARCH RELATIONSHIPS
    # =====================================================

    def search_relationships(
        self,
        node_id: str,
        limit: int = MAX_RELATIONSHIPS
    ) -> Dict[str, Any]:

        graph = self.graph_service.get_node_neighbors(
            node_id=node_id,
            limit=limit
        )

        if graph is None:
            return {
                "center": None,
                "nodes": [],
                "relationships": []
            }

        relationships = []

        for edge in graph["edges"]:

            relationships.append({
                "source": edge["source"],
                "target": edge["target"],
                "type": edge["type"],
                "properties": edge["properties"]
            })

        return {
            "center": graph["center"],
            "nodes": graph["nodes"],
            "relationships": relationships
        }

    # =====================================================
    # 3. EXPAND NEIGHBORS
    # =====================================================

    def expand_neighbors(
        self,
        entity_ids: List[str],
        limit: int = MAX_NEIGHBORS
    ) -> Dict[str, Any]:

        if not entity_ids:
            return {
                "nodes": [],
                "relationships": []
            }

        limit = max(1, min(limit, self.MAX_NEIGHBORS))

        all_nodes = {}
        all_relationships = {}

        for entity_id in entity_ids:

            result = self.search_relationships(
                node_id=entity_id,
                limit=limit
            )

            for node in result["nodes"]:
                all_nodes[node["id"]] = node

            for edge in result["relationships"]:

                key = (
                    edge["source"],
                    edge["target"],
                    edge["type"]
                )

                all_relationships[key] = edge

        return {
            "nodes": list(all_nodes.values()),
            "relationships": list(all_relationships.values())
        }

    # =====================================================
    # 4. MAIN GRAPH SEARCH
    # =====================================================

    def search(
        self,
        keywords: List[str],
        intent: str = "entity_query",
        entity_limit: int = MAX_ENTITY_RESULTS,
        relationship_limit: int = MAX_RELATIONSHIPS
    ) -> Dict[str, Any]:

        entities = self.search_entities(
            keywords=keywords,
            limit=entity_limit
        )

        entity_ids = [
            entity["id"]
            for entity in entities
        ]

        relationships = {
            "nodes": [],
            "relationships": []
        }

        should_expand = intent in {
            "relationship_query",
            "event_query",
            "reasoning_query"
        }

        if should_expand and entity_ids:

            relationships = self.expand_neighbors(
                entity_ids=entity_ids,
                limit=relationship_limit
            )

        # Gộp entity tìm được và entity mở rộng
        all_nodes = {
            node["id"]: node
            for node in relationships["nodes"]
        }

        for entity in entities:

            all_nodes[entity["id"]] = {
                "id": entity["id"],
                "labels": entity["labels"],
                "properties": entity["properties"]
            }

        return {
            "query_entities": entities,
            "related_entities": list(all_nodes.values()),
            "relationships": relationships["relationships"],
            "metadata": {
                "intent": intent,
                "entity_count": len(entities),
                "related_entity_count": len(all_nodes),
                "relationship_count": len(
                    relationships["relationships"]
                )
            }
        }

    # =====================================================
    # 5. NODE NAME
    # =====================================================

    def _get_node_name(
        self,
        properties: Dict[str, Any]
    ) -> Optional[str]:

        for field in self.NAME_FIELDS:

            value = properties.get(field)

            if value is not None:
                return str(value).strip()

        return None

    # =====================================================
    # 6. MATCH SCORING
    # =====================================================

    def _calculate_match_score(
        self,
        name: str,
        properties: Dict[str, Any],
        keywords: List[str]
    ):

        normalized_name = self._normalize(name)

        score = 0
        matched_terms = []

        for keyword in keywords:

            normalized_keyword = self._normalize(keyword)

            if not normalized_keyword:
                continue

            if normalized_keyword == normalized_name:
                score += 10

            elif normalized_keyword in normalized_name:
                score += 5

            else:
                for value in properties.values():

                    if isinstance(value, (str, int, float)):

                        normalized_value = self._normalize(
                            str(value)
                        )

                        if normalized_keyword in normalized_value:
                            score += 1
                            break

            if (
                normalized_keyword in normalized_name
                or normalized_keyword == normalized_name
            ):
                matched_terms.append(keyword)

        return score, list(dict.fromkeys(matched_terms))

    # =====================================================
    # 7. NORMALIZE TEXT
    # =====================================================

    @staticmethod
    def _normalize(text: str) -> str:

        return " ".join(
            str(text).lower().strip().split()
        )
