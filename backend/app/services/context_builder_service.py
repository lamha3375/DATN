
import json
import re
from typing import Any, Dict, List


class ContextBuilderService:
    """
    Xây dựng ngữ cảnh từ kết quả Hybrid Retrieval.

    Input:
        Kết quả từ RetrievalService.

    Output:
        Vector Context, Graph Context và Combined Context.
    """

    MAX_VECTOR_RESULTS = 5
    MAX_GRAPH_RESULTS = 5
    MAX_CONTEXT_LENGTH = 12000

    def __init__(self):
        pass

    # =====================================================
    # 1. NORMALIZATION
    # =====================================================

    @staticmethod
    def _normalize_text(text: Any) -> str:
        """Chuẩn hóa văn bản để so sánh và loại bỏ trùng lặp."""

        if text is None:
            return ""

        text = str(text).strip().lower()
        text = re.sub(r"\s+", " ", text)

        return text

    @staticmethod
    def _safe_string(value: Any) -> str:
        """Chuyển dữ liệu thành chuỗi an toàn."""

        if value is None:
            return ""

        if isinstance(value, (dict, list)):
            return json.dumps(
                value,
                ensure_ascii=False,
                default=str,
            )

        return str(value)

    # =====================================================
    # 2. VECTOR CONTEXT
    # =====================================================

    def build_vector_context(
        self,
        vector_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Chuẩn hóa kết quả Vector Retrieval.

        Distance càng thấp thì kết quả càng gần
        với câu truy vấn theo khoảng cách của vector store.
        """

        if not vector_results:
            return []

        sorted_results = sorted(
            vector_results,
            key=lambda item: float(item.get("distance", float("inf"))),
        )

        results = []
        seen_contents = set()

        for item in sorted_results:

            content = str(item.get("content") or "").strip()

            if not content:
                continue

            normalized_content = self._normalize_text(content)

            if normalized_content in seen_contents:
                continue

            seen_contents.add(normalized_content)

            results.append({
                "chunk_id": item.get("chunk_id"),
                "document_name": item.get("document_name"),
                "page_number": item.get("page_number"),
                "chunk_index": item.get("chunk_index"),
                "content": content,
                "distance": item.get("distance"),
            })

            if len(results) >= self.MAX_VECTOR_RESULTS:
                break

        return results

    # =====================================================
    # 3. GRAPH CONTEXT
    # =====================================================

    def build_graph_context(
        self,
        graph_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Chuẩn hóa node và relationship từ Graph Retrieval.
        """

        if not graph_results:
            return []

        sorted_results = sorted(
            graph_results,
            key=lambda item: float(item.get("score", 0)),
            reverse=True,
        )

        results = []
        seen_nodes = set()

        for item in sorted_results:

            node_id = item.get("node_id")

            properties = item.get("properties") or {}
            labels = item.get("labels") or []

            # Tạo khóa nhận diện node
            if node_id is not None:
                node_key = str(node_id)
            else:
                node_key = (
                    str(labels)
                    + self._normalize_text(
                        properties.get("name")
                        or properties.get("ten")
                        or properties.get("title")
                    )
                )

            if node_key in seen_nodes:
                continue

            seen_nodes.add(node_key)

            relationships = []

            for relationship in item.get("relationships") or []:

                target = relationship.get("target") or {}

                relationships.append({
                    "type": relationship.get("type"),
                    "direction": relationship.get("direction"),
                    "target": {
                        "id": target.get("id"),
                        "labels": target.get("labels") or [],
                        "name": target.get("name"),
                        "properties": target.get("properties") or {},
                    },
                })

            results.append({
                "node_id": node_id,
                "labels": labels,
                "properties": properties,
                "score": item.get("score", 0),
                "matched_terms": item.get("matched_terms") or [],
                "relationships": relationships,
            })

            if len(results) >= self.MAX_GRAPH_RESULTS:
                break

        return results

    # =====================================================
    # 4. FORMAT VECTOR CONTEXT
    # =====================================================

    def format_vector_context(
        self,
        vector_context: List[Dict[str, Any]],
    ) -> str:
        """Chuyển Vector Context thành văn bản."""

        sections = []

        for index, item in enumerate(vector_context, start=1):

            document_name = item.get("document_name") or "Không rõ"
            page_number = item.get("page_number")
            chunk_index = item.get("chunk_index")

            sections.append(
                f"[Tài liệu {index}]\n"
                f"Nguồn: {document_name}\n"
                f"Trang: {page_number}\n"
                f"Chunk: {chunk_index}\n"
                f"Nội dung:\n{item['content']}"
            )

        return "\n\n".join(sections)

    # =====================================================
    # 5. FORMAT GRAPH CONTEXT
    # =====================================================

    def format_graph_context(
        self,
        graph_context: List[Dict[str, Any]],
    ) -> str:
        """Chuyển thông tin đồ thị thành văn bản."""

        sections = []

        for index, node in enumerate(graph_context, start=1):

            properties = node.get("properties") or {}

            lines = [
                f"[Thực thể {index}]",
                f"Node ID: {node.get('node_id')}",
                f"Labels: {', '.join(node.get('labels') or [])}",
                f"Score: {node.get('score')}",
            ]

            if node.get("matched_terms"):
                lines.append(
                    "Matched terms: "
                    + ", ".join(node["matched_terms"])
                )

            lines.append("Thuộc tính:")

            for key, value in properties.items():

                lines.append(
                    f"- {key}: {self._safe_string(value)}"
                )

            relationships = node.get("relationships") or []

            if relationships:
                lines.append("Các quan hệ:")

                for relationship in relationships:

                    target = relationship.get("target") or {}

                    direction = relationship.get("direction")
                    relation_type = relationship.get("type")
                    target_name = (
                        target.get("name")
                        or target.get("id")
                        or "Không rõ"
                    )

                    if direction == "outgoing":
                        relation_text = (
                            f"Node hiện tại --{relation_type}--> "
                            f"{target_name}"
                        )
                    else:
                        relation_text = (
                            f"{target_name} --{relation_type}--> "
                            "Node hiện tại"
                        )

                    lines.append(f"- {relation_text}")

                    target_properties = target.get("properties") or {}

                    for key, value in target_properties.items():
                        lines.append(
                            f"  {key}: {self._safe_string(value)}"
                        )

            sections.append("\n".join(lines))

        return "\n\n".join(sections)

    # =====================================================
    # 6. BUILD COMBINED CONTEXT
    # =====================================================

    def build_combined_context(
        self,
        vector_context: str,
        graph_context: str,
    ) -> str:
        """
        Kết hợp hai nguồn thông tin thành một context.

        Giới hạn độ dài để tránh đưa quá nhiều dữ liệu
        vào LLM.
        """

        combined = (
            "=== VECTOR CONTEXT ===\n"
            f"{vector_context or 'Không có dữ liệu vector.'}\n\n"
            "=== GRAPH CONTEXT ===\n"
            f"{graph_context or 'Không có dữ liệu graph.'}"
        )

        if len(combined) > self.MAX_CONTEXT_LENGTH:
            combined = combined[:self.MAX_CONTEXT_LENGTH]

        return combined

    # =====================================================
    # 7. MAIN CONTEXT BUILDER
    # =====================================================

    def build(
        self,
        retrieval_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Điều phối quá trình xây dựng context.
        """

        if not isinstance(retrieval_result, dict):
            raise TypeError(
                "retrieval_result phải là dictionary."
            )

        query = str(retrieval_result.get("query") or "").strip()

        if not query:
            raise ValueError(
                "Không tìm thấy câu truy vấn trong retrieval_result."
            )

        retrieval = retrieval_result.get("retrieval") or {}

        vector_results = (
            retrieval.get("vector", {}).get("results") or []
        )

        graph_results = (
            retrieval.get("graph", {}).get("results") or []
        )

        # 1. Chuẩn hóa Vector Context
        vector_context = self.build_vector_context(
            vector_results[:self.MAX_VECTOR_RESULTS * 2]
        )

        # 2. Chuẩn hóa Graph Context
        graph_context = self.build_graph_context(
            graph_results[:self.MAX_GRAPH_RESULTS * 2]
        )

        # 3. Format hai nguồn dữ liệu
        formatted_vector = self.format_vector_context(
            vector_context
        )

        formatted_graph = self.format_graph_context(
            graph_context
        )

        # 4. Kết hợp context
        combined_context = self.build_combined_context(
            formatted_vector,
            formatted_graph,
        )

        # 5. Trả kết quả
        return {
            "query": query,

            "context": {
                "vector_context": vector_context,
                "graph_context": graph_context,
                "combined_context": combined_context,
            },

            "metadata": {
                "vector_count": len(vector_context),
                "graph_count": len(graph_context),
                "combined_context_length": len(combined_context),
            },
        }


# Singleton
context_builder_service = ContextBuilderService()
