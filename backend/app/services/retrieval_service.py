
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.neo4j_connection import neo4j_connection
from app.schemas.search import SearchRequest
from app.services.search_service import SearchService
from app.services.query_analysis_service import query_analysis_service


class RetrievalService:
    """
    Hybrid Retrieval:
    - Query Analysis: phân tích câu hỏi và trích xuất keywords.
    - Vector Retrieval: tìm kiếm ngữ nghĩa trên ChromaDB.
    - Graph Retrieval: tìm kiếm thực thể trên Neo4j.
    - Relationship Expansion: mở rộng quan hệ theo intent.
    """

    MAX_VECTOR_TOP_K = 10
    MAX_GRAPH_TOP_K = 10
    MAX_NEIGHBORS = 3

    IDENTITY_KEYS = [
        "name",
        "ten",
        "title",
        "entity",
        "entity_name",
        "canonical_name",
        "event_name",
        "person_name",
        "location_name",
        "aliases",
        "alias",
        "ten_nhan_vat",
        "ten_su_kien",
        "ten_dia_diem",
    ]

    EXCLUDED_KEYS = {
        "embedding",
        "vector",
        "raw_text",
        "raw_content",
        "content",
    }

    PRIORITY_PROPERTIES = [
        "id",
        "entity_id",
        "event_id",
        "person_id",
        "name",
        "ten",
        "title",
        "entity",
        "event_name",
        "person_name",
        "type",
        "entity_type",
        "year",
        "date",
        "start_date",
        "end_date",
        "start_year",
        "end_year",
        "description",
        "aliases",
        "source",
    ]

    GENERIC_TERMS = [
        "quân",
        "đại",
        "phá",
        "trận",
        "vua",
        "năm",
        "nhà",
    ]

    def __init__(self):
        self.search_service = SearchService()
        self.query_analysis_service = query_analysis_service

    # =====================================================
    # 1. VECTOR RETRIEVAL
    # =====================================================

    def retrieve_vectors(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:

        top_k = max(
            1,
            min(top_k, self.MAX_VECTOR_TOP_K),
        )

        request = SearchRequest(
            query=query,
            top_k=top_k,
        )

        response = self.search_service.search(request)

        return [
            item.model_dump()
            for item in response.results
        ]

    # =====================================================
    # 2. DATA NORMALIZATION
    # =====================================================

    def _to_json_safe(self, value: Any) -> Any:
        """Chuyển dữ liệu Neo4j về kiểu có thể JSON hóa."""

        if value is None:
            return None

        if isinstance(value, (str, int, float, bool)):
            return value

        if isinstance(value, list):
            return [
                self._to_json_safe(item)
                for item in value
            ]

        if isinstance(value, dict):
            return {
                str(key): self._to_json_safe(item)
                for key, item in value.items()
            }

        return str(value)

    def _compact_properties(
        self,
        properties: Dict[str, Any],
        max_properties: int = 15,
    ) -> Dict[str, Any]:
        """Giới hạn số lượng và độ dài thuộc tính trả về."""

        if not properties:
            return {}

        ordered_keys = []

        for key in self.PRIORITY_PROPERTIES:
            if key in properties:
                ordered_keys.append(key)

        for key in properties:
            if key not in ordered_keys:
                ordered_keys.append(key)

        result = {}

        for key in ordered_keys:

            if len(result) >= max_properties:
                break

            if key.lower() in self.EXCLUDED_KEYS:
                continue

            value = self._to_json_safe(properties[key])

            if isinstance(value, str) and len(value) > 500:
                value = value[:500] + "..."

            result[key] = value

        return result

    # =====================================================
    # 3. GRAPH RETRIEVAL
    # =====================================================

    def retrieve_graph(
        self,
        keywords: List[str],
        top_k: int = 5,
        max_neighbors: int = 3,
        retrieval_strategy: Optional[Dict[str, bool]] = None,
        intent: str = "general_query",
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm node trên Neo4j.

        Relationship Expansion chỉ được thực hiện
        khi retrieval_strategy cho phép.
        """

        if not keywords:
            return []

        top_k = max(
            1,
            min(top_k, self.MAX_GRAPH_TOP_K),
        )

        if retrieval_strategy is None:
            retrieval_strategy = {
                "relationship_expansion": False
            }

        expand_relationships = retrieval_strategy.get(
            "relationship_expansion",
            False,
        )

        if expand_relationships:
            max_neighbors = max(
                0,
                min(max_neighbors, self.MAX_NEIGHBORS),
            )
        else:
            max_neighbors = 0

        # ---------------------------------------------
        # Phần truy xuất và chấm điểm node
        # ---------------------------------------------

        base_query = """
        MATCH (n)

        WITH n,

            [
                term IN $keywords
                WHERE any(
                    key IN keys(n)
                    WHERE toLower(key) IN $identity_keys
                    AND toLower(toString(n[key])) CONTAINS term
                )
            ] AS identity_matches,

            [
                term IN $keywords
                WHERE any(
                    key IN keys(n)
                    WHERE NOT toLower(key) IN $identity_keys
                    AND toLower(toString(n[key])) CONTAINS term
                )
            ] AS context_matches

        WITH n,

            [
                term IN identity_matches
                WHERE
                    size(split(term, ' ')) > 1
                    OR NOT any(
                        phrase IN identity_matches
                        WHERE size(split(phrase, ' ')) > 1
                        AND term IN split(phrase, ' ')
                    )
            ] AS identity_effective,

            [
                term IN context_matches
                WHERE
                    size(split(term, ' ')) > 1
                    OR NOT any(
                        phrase IN context_matches
                        WHERE size(split(phrase, ' ')) > 1
                        AND term IN split(phrase, ' ')
                    )
            ] AS context_effective

        WITH n,
            identity_effective,
            context_effective,

            reduce(
                score = 0.0,
                term IN identity_effective |
                score +
                CASE
                    WHEN term = 'quân thanh' THEN 12.0
                    WHEN term = 'quân xiêm' THEN 12.0
                    WHEN size(split(term, ' ')) = 4 THEN 10.0
                    WHEN size(split(term, ' ')) = 3 THEN 8.0
                    WHEN size(split(term, ' ')) = 2 THEN 6.0
                    WHEN term IN $generic_terms THEN 0.2
                    ELSE 1.5
                END
            ) AS identity_score,

            reduce(
                score = 0.0,
                term IN context_effective |
                score +
                CASE
                    WHEN term = 'quân thanh' THEN 3.0
                    WHEN term = 'quân xiêm' THEN 3.0
                    WHEN term CONTAINS ' ' THEN 1.5
                    WHEN term IN $generic_terms THEN 0.1
                    ELSE 0.5
                END
            ) AS context_score

        WITH n,
            identity_effective,
            context_effective,
            identity_score + context_score AS relevance_score

        WHERE relevance_score > 0

        ORDER BY relevance_score DESC
        LIMIT $top_k
        """

        # ---------------------------------------------
        # Phần mở rộng quan hệ
        # ---------------------------------------------

        if expand_relationships and max_neighbors > 0:

            relationship_query = """
            OPTIONAL MATCH (n)-[r]-(m)

            WITH n,
                identity_effective,
                context_effective,
                relevance_score,

                collect(
                    DISTINCT CASE
                        WHEN r IS NULL THEN null
                        ELSE {
                            type: type(r),

                            direction:
                                CASE
                                    WHEN startNode(r) = n
                                    THEN 'outgoing'
                                    ELSE 'incoming'
                                END,

                            target: {
                                id: coalesce(
                                    properties(m)['id'],
                                    properties(m)['entity_id'],
                                    elementId(m)
                                ),

                                labels: labels(m),

                                name: coalesce(
                                    properties(m)['name'],
                                    properties(m)['ten'],
                                    properties(m)['title'],
                                    properties(m)['entity'],
                                    properties(m)['event_name'],
                                    properties(m)['person_name']
                                ),

                                properties: properties(m)
                            }
                        }
                    END
                ) AS all_relationships

            RETURN
                elementId(n) AS node_id,
                labels(n) AS labels,
                properties(n) AS properties,
                relevance_score AS score,

                identity_effective AS matched_identity_terms,
                context_effective AS matched_context_terms,

                [
                    rel IN all_relationships
                    WHERE rel IS NOT NULL
                ][0..$max_neighbors] AS relationships

            ORDER BY score DESC
            """

        else:

            # Không thực hiện OPTIONAL MATCH khi không cần
            # mở rộng quan hệ.
            relationship_query = """
            RETURN
                elementId(n) AS node_id,
                labels(n) AS labels,
                properties(n) AS properties,
                relevance_score AS score,

                identity_effective AS matched_identity_terms,
                context_effective AS matched_context_terms,

                [] AS relationships

            ORDER BY score DESC
            """

        cypher_query = base_query + relationship_query

        # ---------------------------------------------
        # Thực thi Neo4j
        # ---------------------------------------------

        driver = neo4j_connection.get_driver()

        with driver.session(
            database=settings.NEO4J_DATABASE
        ) as session:

            records = session.run(
                cypher_query,
                keywords=keywords,
                identity_keys=self.IDENTITY_KEYS,
                generic_terms=self.GENERIC_TERMS,
                top_k=top_k,
                max_neighbors=max_neighbors,
            )

            results = []

            for record in records:

                relationships = []

                for relationship in record["relationships"]:

                    target = relationship["target"]

                    relationships.append({
                        "type": relationship["type"],
                        "direction": relationship["direction"],

                        "target": {
                            "id": target["id"],
                            "labels": target["labels"],
                            "name": target["name"],

                            "properties": self._compact_properties(
                                target["properties"]
                            ),
                        },
                    })

                results.append({
                    "node_id": record["node_id"],
                    "labels": record["labels"],

                    "properties": self._compact_properties(
                        record["properties"]
                    ),

                    "score": round(
                        float(record["score"]),
                        3,
                    ),

                    "matched_terms": (
                        record["matched_identity_terms"]
                        + record["matched_context_terms"]
                    ),

                    "relationships": relationships,
                })

        return results

    # =====================================================
    # 4. MAIN RETRIEVAL
    # =====================================================

    def retrieve(
        self,
        query: str,
        vector_top_k: int = 5,
        graph_top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Điều phối toàn bộ quá trình Hybrid Retrieval.
        """

        # 1. Phân tích câu hỏi
        analysis = self.query_analysis_service.analyze(query)

        normalized_query = analysis["normalized_query"]
        keywords = analysis["keywords"]
        intent = analysis["intent"]
        retrieval_strategy = analysis["retrieval_strategy"]

        # 2. Giới hạn số lượng kết quả
        vector_top_k = max(
            1,
            min(vector_top_k, self.MAX_VECTOR_TOP_K),
        )

        graph_top_k = max(
            1,
            min(graph_top_k, self.MAX_GRAPH_TOP_K),
        )

        # 3. Vector Retrieval
        vector_results = []

        if retrieval_strategy.get("vector_search", True):

            vector_results = self.retrieve_vectors(
                query=normalized_query,
                top_k=vector_top_k,
            )

        # 4. Graph Retrieval
        graph_results = []

        if retrieval_strategy.get("graph_search", True):

            graph_results = self.retrieve_graph(
                keywords=keywords,
                top_k=graph_top_k,
                max_neighbors=self.MAX_NEIGHBORS,
                retrieval_strategy=retrieval_strategy,
                intent=intent,
            )

        # 5. Tổng hợp kết quả
        return {
            "query": query.strip(),

            "analysis": {
                "normalized_query": normalized_query,
                "keywords": keywords,
                "intent": intent,
                "retrieval_strategy": retrieval_strategy,
            },

            "keywords": keywords,

            "retrieval": {
                "vector": {
                    "top_k": vector_top_k,
                    "count": len(vector_results),
                    "results": vector_results,
                },

                "graph": {
                    "top_k": graph_top_k,
                    "count": len(graph_results),
                    "results": graph_results,
                },
            },
        }


# Singleton
retrieval_service = RetrievalService()
