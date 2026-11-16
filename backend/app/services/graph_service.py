
from typing import Any, Dict, List, Optional

from app.core.config import settings


class GraphService:

    MAX_GRAPH_LIMIT = 500

    def __init__(self, driver):
        self.driver = driver

    @staticmethod
    def _serialize_node(node) -> Dict[str, Any]:
        """
        Chuyển Neo4j Node thành dictionary.
        """

        properties = dict(node)

        business_id = (
            properties.get("person_id")
            or properties.get("event_id")
            or properties.get("location_id")
            or properties.get("source_id")
            or properties.get("id")
        )

        return {
            "id": node.element_id,
            "business_id": business_id,
            "labels": list(node.labels),
            "properties": properties
        }

    @staticmethod
    def _serialize_relationship(relationship) -> Dict[str, Any]:
        """
        Chuyển Neo4j Relationship thành dictionary.
        """

        properties = dict(relationship)

        return {
            "id": relationship.element_id,
            "business_id": properties.get("edge_id"),
            "source": relationship.start_node.element_id,
            "target": relationship.end_node.element_id,
            "type": relationship.type,
            "properties": properties
        }

    def get_graph(
        self,
        keyword: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:

        keyword = keyword.strip() if keyword else None
        limit = max(1, min(limit, self.MAX_GRAPH_LIMIT))

        query = """
        MATCH (n)-[r]-(m)

        WHERE $keyword IS NULL
           OR any(
               key IN keys(n)
               WHERE n[key] IS NOT NULL
                 AND toLower(toString(n[key]))
                     CONTAINS toLower($keyword)
           )
           OR any(
               key IN keys(m)
               WHERE m[key] IS NOT NULL
                 AND toLower(toString(m[key]))
                     CONTAINS toLower($keyword)
           )

        WITH n, r, m
        ORDER BY elementId(n), elementId(m)
        LIMIT $limit

        RETURN
            collect(DISTINCT n) AS nodes,
            collect(DISTINCT r) AS relationships
        """

        with self.driver.session(
            database=settings.NEO4J_DATABASE
        ) as session:

            result = session.run(
                query,
                keyword=keyword,
                limit=limit
            )

            record = result.single()

            if record is None:
                return self._empty_graph()

            raw_nodes = record["nodes"]
            raw_relationships = record["relationships"]

        nodes = [
            self._serialize_node(node)
            for node in raw_nodes
        ]

        edges = [
            self._serialize_relationship(relationship)
            for relationship in raw_relationships
        ]

        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "nodes": nodes,
            "edges": edges
        }

    def search_entities(
        self,
        keyword: str,
        entity_type: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Tìm kiếm nhân vật, sự kiện và địa điểm.
        """

        keyword = keyword.strip() if keyword else ""

        if not keyword:
            raise ValueError("Từ khóa tìm kiếm không được để trống.")

        allowed_types = {
            "NhanVat",
            "SuKien",
            "DiaDiem"
        }

        if entity_type is not None and entity_type not in allowed_types:
            raise ValueError("Loại thực thể không hợp lệ.")

        limit = max(1, min(limit, 100))

        labels = (
            [entity_type]
            if entity_type
            else list(allowed_types)
        )

        query = """
        MATCH (n)
        WHERE any(label IN labels(n) WHERE label IN $labels)

          AND any(
              key IN keys(n)
              WHERE n[key] IS NOT NULL
                AND toLower(toString(n[key]))
                    CONTAINS toLower($keyword)
          )

        RETURN
            elementId(n) AS node_id,
            labels(n) AS labels,
            properties(n) AS properties

        ORDER BY
            toLower(
                coalesce(
                    n.name,
                    n.event_name,
                    n.location_name,
                    ''
                )
            )

        LIMIT $limit
        """

        with self.driver.session(
            database=settings.NEO4J_DATABASE
        ) as session:

            result = session.run(
                query,
                labels=labels,
                keyword=keyword,
                limit=limit
            )

            entities = []

            for record in result:
                properties = record["properties"]

                business_id = (
                    properties.get("person_id")
                    or properties.get("event_id")
                    or properties.get("location_id")
                    or properties.get("id")
                )

                entities.append({
                    "id": record["node_id"],
                    "business_id": business_id,
                    "entity_type": record["labels"],
                    "name": (
                        properties.get("name")
                        or properties.get("event_name")
                        or properties.get("location_name")
                    ),
                    "properties": properties
                })

        return {
            "keyword": keyword,
            "entity_type": entity_type,
            "total": len(entities),
            "results": entities
        }

    def get_node_neighbors(
        self,
        node_id: str,
        limit: int = 50
    ) -> Optional[Dict[str, Any]]:

        limit = max(1, min(limit, self.MAX_GRAPH_LIMIT))

        query = """
        MATCH (center)
        WHERE elementId(center) = $node_id

        CALL {
            WITH center

            OPTIONAL MATCH (center)-[r]-(neighbor)

            WITH neighbor, collect(r) AS relationships

            ORDER BY elementId(neighbor)
            LIMIT $limit

            RETURN collect({
                node: neighbor,
                relationships: relationships
            }) AS items
        }

        RETURN center, items
        """

        with self.driver.session(
            database=settings.NEO4J_DATABASE
        ) as session:

            result = session.run(
                query,
                node_id=node_id,
                limit=limit
            )

            record = result.single()

            if record is None:
                return None

            center = record["center"]
            items = record["items"]

        nodes = [
            self._serialize_node(center)
        ]

        edges = []

        for item in items:

            neighbor = item["node"]

            if neighbor is None:
                continue

            nodes.append(
                self._serialize_node(neighbor)
            )

            for relationship in item["relationships"]:
                if relationship is not None:
                    edges.append(
                        self._serialize_relationship(relationship)
                    )

        # Loại bỏ node trùng lặp
        unique_nodes = {
            node["id"]: node
            for node in nodes
        }

        # Loại bỏ relationship trùng lặp
        unique_edges = {
            edge["id"]: edge
            for edge in edges
        }

        return {
            "center": center.element_id,
            "center_business_id": (
                self._serialize_node(center)["business_id"]
            ),
            "total_nodes": len(unique_nodes),
            "total_edges": len(unique_edges),
            "nodes": list(unique_nodes.values()),
            "edges": list(unique_edges.values())
        }

    @staticmethod
    def _empty_graph() -> Dict[str, Any]:

        return {
            "total_nodes": 0,
            "total_edges": 0,
            "nodes": [],
            "edges": []
        }
