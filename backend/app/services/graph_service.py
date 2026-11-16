
from typing import Any, Dict, List, Optional
from app.core.config import settings

# =========================================================
# NODE LABELS
# =========================================================

NODE_LABELS = {
    "Person": "Nhân vật",
    "Event": "Sự kiện",
    "Location": "Địa điểm",
    "Faction": "Phe phái",
    "Policy": "Chính sách",
    "Document": "Văn kiện",
    "Unit": "Đơn vị",
    "Tactics": "Chiến thuật",
    "Source": "Nguồn tư liệu",
}


ENTITY_TYPE_MAP = {
    "Nhân vật": "Person",
    "Sự kiện": "Event",
    "Địa điểm": "Location",
    "Phe phái": "Faction",
    "Chính sách": "Policy",
    "Văn kiện": "Document",
    "Đơn vị": "Unit",
    "Chiến thuật": "Tactics",
    "Nguồn tư liệu": "Source",
}


# =========================================================
# RELATIONSHIP LABELS
# =========================================================

RELATIONSHIP_LABELS = {
    "DIEN_RA_TAI": "Diễn ra tại",
    "THAM_GIA_SU_KIEN": "Tham gia sự kiện",
    "CHI_HUY_SU_KIEN": "Chỉ huy sự kiện",
    "TRICH_DAN_TU_NGUON": "Trích dẫn từ nguồn",
    "THUOC_VE_PHE_PHAI": "Thuộc về phe phái",
    "ANH_EM_CUA": "Anh em của",
    "CHA_ME_CUA": "Cha mẹ của",
    "VO_CHONG_CUA": "Vợ chồng của",
    "PHUNG_SU_TRIEU_INH": "Phụng sự triều đình",
    "LIEN_MINH_VOI": "Liên minh với",
    "THAY_HOC_CUA": "Thầy học của",
    "BAN_HANH": "Ban hành",
    "SOAN_THAO": "Soạn thảo",
    "CHU_TRI_THUC_HIEN": "Chủ trì thực hiện",
    "CHI_HUY_ON_VI": "Chỉ huy đơn vị",
    "SANG_TAO_CHIEN_THUAT": "Sáng tạo chiến thuật",
    "AP_DUNG_TRONG": "Áp dụng trong",
    "BAN_HANH_TRONG_SU_KIEN": "Ban hành trong sự kiện",
    "SU_DUNG_TRONG_SU_KIEN": "Sử dụng trong sự kiện",
    "SU_DUNG_TRONG": "Sử dụng trong",
    "TIEN_E_CUA": "Tiền đề của",
    "DAN_EN": "Dẫn đến",
    "CHU_TRI_SU_KIEN": "Chủ trì sự kiện",
}


# =========================================================
# GRAPH SERVICE
# =========================================================

class GraphService:

    MAX_GRAPH_LIMIT = 500
    MAX_SEARCH_LIMIT = 100
    MAX_NEIGHBOR_LIMIT = 100

    ALLOWED_TYPES = {
        "Person",
        "Event",
        "Location",
        "Faction",
        "Policy",
        "Document",
        "Unit",
        "Tactics",
        "Source",
    }

    def __init__(self, driver):
        self.driver = driver

    # =====================================================
    # HELPERS
    # =====================================================

    @staticmethod
    def _empty_graph():
        return {
            "total_nodes": 0,
            "total_edges": 0,
            "nodes": [],
            "edges": [],
        }

    @staticmethod
    def _normalize_keyword(keyword: Optional[str]) -> Optional[str]:
        if keyword is None:
            return None

        keyword = str(keyword).strip()

        return keyword if keyword else None

    @staticmethod
    def _get_business_id(properties: Dict) -> Optional[str]:
        return (
            properties.get("person_id")
            or properties.get("event_id")
            or properties.get("location_id")
            or properties.get("source_id")
            or properties.get("id")
        )

    @staticmethod
    def display_relationship_type(rel_type: str) -> str:
        if not rel_type:
            return "Quan hệ"

        return RELATIONSHIP_LABELS.get(
            rel_type,
            rel_type.replace("_", " ").capitalize()
        )

    # =====================================================
    # SERIALIZE NODE
    # =====================================================

    @staticmethod
    def _serialize_node(node):

        if node is None:
            return None

        properties = dict(node)
        labels = list(node.labels)

        display_labels = [
            NODE_LABELS.get(label, label)
            for label in labels
        ]

        return {
            "id": node.element_id,
            "business_id": GraphService._get_business_id(
                properties
            ),
            "labels": labels,
            "display_labels": display_labels,
            "properties": properties,
        }

    # =====================================================
    # SERIALIZE RELATIONSHIP
    # =====================================================

    @staticmethod
    def _serialize_relationship(relationship):

        if relationship is None:
            return None

        properties = dict(relationship)
        rel_type = relationship.type

        return {
            "id": relationship.element_id,
            "business_id": properties.get("edge_id"),
            "source": relationship.start_node.element_id,
            "target": relationship.end_node.element_id,
            "type": rel_type,
            "display_type": GraphService.display_relationship_type(
                rel_type
            ),
            "properties": properties,
        }

    # =====================================================
    # 1. GET FULL GRAPH
    # =====================================================

    def get_graph(
        self,
        keyword: Optional[str] = None,
        limit: int = 500
    ) -> Dict:

        keyword = self._normalize_keyword(keyword)

        limit = max(
            1,
            min(int(limit), self.MAX_GRAPH_LIMIT)
        )

        labels = sorted(self.ALLOWED_TYPES)

        with self.driver.session(
            database=settings.NEO4J_DATABASE
        ) as session:

            # ---------------------------------------------
            # A. DATABASE DIAGNOSTICS
            # ---------------------------------------------

            try:
                db_record = session.run(
                    """
                    CALL db.info()
                    YIELD name
                    RETURN name
                    """
                ).single()

                database_name = (
                    db_record["name"]
                    if db_record else "UNKNOWN"
                )

                print(
                    "[GRAPH] DATABASE:",
                    database_name
                )

            except Exception as error:
                print(
                    "[GRAPH] DATABASE INFO ERROR:",
                    error
                )

            # ---------------------------------------------
            # B. COUNT NODES BY LABEL
            # ---------------------------------------------

            label_count_query = """
            MATCH (n)
            UNWIND labels(n) AS label
            RETURN label, count(*) AS total
            ORDER BY label
            """

            label_records = list(
                session.run(label_count_query)
            )

            print("[GRAPH] NODE COUNTS BY LABEL:")

            for record in label_records:
                print(
                    f"  {record['label']}: {record['total']}"
                )

            # ---------------------------------------------
            # C. COUNT ALLOWED NODES
            # ---------------------------------------------

            count_nodes_query = """
            MATCH (n)
            WHERE any(
                label IN labels(n)
                WHERE label IN $labels
            )
            RETURN count(n) AS total
            """

            allowed_node_count = session.run(
                count_nodes_query,
                labels=labels
            ).single()["total"]

            print(
                "[GRAPH] TOTAL ALLOWED NODES:",
                allowed_node_count
            )

            # ---------------------------------------------
            # D. COUNT ALL RELATIONSHIPS
            # ---------------------------------------------

            count_edges_query = """
            MATCH ()-[r]->()
            RETURN count(r) AS total
            """

            all_edge_count = session.run(
                count_edges_query
            ).single()["total"]

            print(
                "[GRAPH] TOTAL DATABASE RELATIONSHIPS:",
                all_edge_count
            )

            # ---------------------------------------------
            # E. GET NODES
            # ---------------------------------------------

            node_query = """
            MATCH (n)
            WHERE any(
                label IN labels(n)
                WHERE label IN $labels
            )
            AND (
                $keyword IS NULL
                OR any(
                    key IN keys(n)
                    WHERE n[key] IS NOT NULL
                    AND toLower(toString(n[key]))
                        CONTAINS toLower($keyword)
                )
            )
            RETURN n
            ORDER BY elementId(n)
            LIMIT $limit
            """

            node_records = list(
                session.run(
                    node_query,
                    labels=labels,
                    keyword=keyword,
                    limit=limit
                )
            )

            raw_nodes = [
                record["n"]
                for record in node_records
                if record["n"] is not None
            ]

            node_ids = [
                node.element_id
                for node in raw_nodes
            ]

            print(
                "[GRAPH] FETCHED NODES:",
                len(raw_nodes)
            )

            if not raw_nodes:
                return self._empty_graph()

            # ---------------------------------------------
            # F. GET ALL RELATIONSHIPS BETWEEN THESE NODES
            # ---------------------------------------------

            relationship_query = """
            MATCH (a)-[r]-(b)
            WHERE elementId(a) IN $node_ids
              AND elementId(b) IN $node_ids
            RETURN DISTINCT r
            ORDER BY elementId(r)
            """

            relationship_records = list(
                session.run(
                    relationship_query,
                    node_ids=node_ids
                )
            )

            raw_relationships = [
                record["r"]
                for record in relationship_records
                if record["r"] is not None
            ]

            print(
                "[GRAPH] FETCHED RELATIONSHIPS:",
                len(raw_relationships)
            )

            # ---------------------------------------------
            # G. CHECK RELATIONSHIP TYPES
            # ---------------------------------------------

            type_count_query = """
            MATCH (a)-[r]->(b)
            WHERE elementId(a) IN $node_ids
              AND elementId(b) IN $node_ids
            RETURN type(r) AS relationship_type,
                   count(r) AS total
            ORDER BY relationship_type
            """

            type_records = list(
                session.run(
                    type_count_query,
                    node_ids=node_ids
                )
            )

            print("[GRAPH] RELATIONSHIP COUNTS BY TYPE:")

            for record in type_records:
                print(
                    f"  {record['relationship_type']}: "
                    f"{record['total']}"
                )

        # ---------------------------------------------
        # H. SERIALIZE
        # ---------------------------------------------

        nodes = [
            self._serialize_node(node)
            for node in raw_nodes
        ]

        edges = [
            self._serialize_relationship(rel)
            for rel in raw_relationships
        ]

        result = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "nodes": nodes,
            "edges": edges,
        }

        print(
            "[GRAPH] FINAL RESULT:",
            result["total_nodes"],
            "nodes /",
            result["total_edges"],
            "relationships"
        )

        return result

    # =====================================================
    # 2. SEARCH ENTITIES
    # =====================================================

    def search_entities(
        self,
        keyword: str,
        entity_type: Optional[str] = None,
        limit: int = 20
    ) -> Dict:

        keyword = self._normalize_keyword(keyword)

        limit = max(
            1,
            min(int(limit), self.MAX_SEARCH_LIMIT)
        )

        if not keyword:
            return {
                "keyword": "",
                "entity_type": entity_type,
                "total": 0,
                "results": [],
            }

        if entity_type:

            entity_type = ENTITY_TYPE_MAP.get(
                entity_type,
                entity_type
            )

            if entity_type not in self.ALLOWED_TYPES:
                return {
                    "keyword": keyword,
                    "entity_type": entity_type,
                    "total": 0,
                    "results": [],
                }

            allowed_labels = [entity_type]

        else:
            allowed_labels = sorted(self.ALLOWED_TYPES)

        query = """
        MATCH (n)
        WHERE any(
            label IN labels(n)
            WHERE label IN $labels
        )
        AND any(
            key IN keys(n)
            WHERE n[key] IS NOT NULL
            AND toLower(toString(n[key]))
                CONTAINS toLower($keyword)
        )
        WITH n
        ORDER BY toLower(
            coalesce(
                n.name,
                n.event_name,
                n.location_name,
                n.fullName,
                n.id,
                ''
            )
        )
        RETURN
            elementId(n) AS node_id,
            labels(n) AS labels,
            properties(n) AS properties
        LIMIT $limit
        """

        with self.driver.session(
            database=settings.NEO4J_DATABASE
        ) as session:

            records = list(
                session.run(
                    query,
                    labels=allowed_labels,
                    keyword=keyword,
                    limit=limit
                )
            )

        results = []

        for record in records:

            labels = record["labels"] or []
            properties = dict(record["properties"] or {})

            results.append({
                "node_id": record["node_id"],
                "business_id": self._get_business_id(properties),
                "labels": labels,
                "display_labels": [
                    NODE_LABELS.get(label, label)
                    for label in labels
                ],
                "properties": properties,
            })

        return {
            "keyword": keyword,
            "entity_type": entity_type,
            "total": len(results),
            "results": results,
        }

    # =====================================================
    # 3. GET NODE NEIGHBORS
    # =====================================================

    def get_node_neighbors(
        self,
        node_id: str,
        limit: int = 50
    ) -> Dict:

        if not node_id:
            return self._empty_graph()

        limit = max(
            1,
            min(int(limit), self.MAX_NEIGHBOR_LIMIT)
        )

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

            record = session.run(
                query,
                node_id=node_id,
                limit=limit
            ).single()

        if not record:
            return self._empty_graph()

        center = record["center"]

        if center is None:
            return self._empty_graph()

        center_data = self._serialize_node(center)

        items = record["items"] or []

        nodes = [center_data]
        edges = []

        seen_node_ids = {
            center.element_id
        }

        seen_edge_ids = set()

        for item in items:

            if not item:
                continue

            neighbor = item.get("node")

            if neighbor is None:
                continue

            if neighbor.element_id not in seen_node_ids:

                nodes.append(
                    self._serialize_node(neighbor)
                )

                seen_node_ids.add(
                    neighbor.element_id
                )

            relationships = item.get("relationships") or []

            for relationship in relationships:

                if relationship is None:
                    continue

                relationship_id = relationship.element_id

                if relationship_id in seen_edge_ids:
                    continue

                edges.append(
                    self._serialize_relationship(relationship)
                )

                seen_edge_ids.add(relationship_id)

        center_properties = dict(center)

        return {
            "center": center_data,
            "center_business_id": self._get_business_id(
                center_properties
            ),
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "nodes": nodes,
            "edges": edges,
        }
