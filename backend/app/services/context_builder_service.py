
import json
import re
from typing import Any, Dict, List


class ContextBuilderService:
    """
    Xây dựng ngữ cảnh từ kết quả Hybrid Retrieval.

    Bao gồm:
    - Vector Context
    - Graph Context
    - Combined Context
    - Danh sách Source đã được ánh xạ từ DocumentFile
    """

    MAX_VECTOR_RESULTS = 10
    MAX_GRAPH_RESULTS = 10
    MAX_CONTEXT_LENGTH = 20000

    def __init__(self):
        pass

    # =====================================================
    # 1. NORMALIZATION
    # =====================================================

    @staticmethod
    def _normalize_text(text: Any) -> str:

        if text is None:
            return ""

        text = str(text).strip().lower()
        text = re.sub(r"\s+", " ", text)

        return text

    @staticmethod
    def _safe_string(value: Any) -> str:

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
    # 2. SOURCE HELPERS
    # =====================================================

    @staticmethod
    def _get_source_id(source: Dict[str, Any]) -> str:

        source_id = (
            source.get("id")
            or source.get("source_id")
        )

        return str(source_id).strip() if source_id else ""

    @staticmethod
    def _get_source_name(source: Dict[str, Any]) -> str:

        for field in (
            "name",
            "title",
            "file",
            "filename",
            "document_name",
        ):

            value = source.get(field)

            if value:
                return str(value).strip()

        return "Không rõ tên nguồn"

    def _collect_unique_sources(
        self,
        vector_context: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Tổng hợp Source từ các vector chunk.

        Một PDF có thể liên kết nhiều Source.
        Một Source xuất hiện ở nhiều chunk chỉ được trả một lần.
        """

        unique_sources = {}

        for item in vector_context:

            for source in item.get("sources") or []:

                if not isinstance(source, dict):
                    continue

                source_id = self._get_source_id(source)

                if not source_id:
                    continue

                if source_id not in unique_sources:

                    unique_sources[source_id] = {
                        **source,
                        "id": source_id,
                        "name": self._get_source_name(source),
                        "document_names": [],
                        "pages": [],
                    }

                current = unique_sources[source_id]

                document_name = item.get("document_name")
                page_number = item.get("page_number")

                if (
                    document_name
                    and document_name not in current["document_names"]
                ):
                    current["document_names"].append(document_name)

                if (
                    page_number is not None
                    and page_number not in current["pages"]
                ):
                    current["pages"].append(page_number)

        results = list(unique_sources.values())

        for source in results:
            source["pages"].sort()

        return results

    # =====================================================
    # 3. VECTOR CONTEXT
    # =====================================================

    def build_vector_context(
        self,
        vector_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        if not vector_results:
            return []

        sorted_results = sorted(
            vector_results,
            key=lambda item: float(
                item.get("distance", float("inf"))
            ),
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

            sources = item.get("sources") or []

            # Chuẩn hóa source để tránh dữ liệu không phải dict.
            sources = [
                source
                for source in sources
                if isinstance(source, dict)
            ]

            results.append({
                "chunk_id": item.get("chunk_id"),
                "document_id": item.get("document_id"),
                "document_name": item.get("document_name"),
                "source_id": item.get("source_id"),
                "sources": sources,
                "content_hash": item.get("content_hash"),
                "token_count": item.get("token_count"),
                "page_number": item.get("page_number"),
                "chunk_index": item.get("chunk_index"),
                "content": content,
                "distance": item.get("distance"),
                "similarity": item.get("similarity"),
            })

            if len(results) >= self.MAX_VECTOR_RESULTS:
                break

        return results

    # =====================================================
    # 4. GRAPH CONTEXT
    # =====================================================

    def build_graph_context(
        self,
        graph_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

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
    # 5. FORMAT VECTOR CONTEXT
    # =====================================================

    def format_vector_context(
        self,
        vector_context: List[Dict[str, Any]],
    ) -> str:

        sections = []

        for index, item in enumerate(vector_context, start=1):

            document_name = item.get("document_name") or "Không rõ"
            page_number = item.get("page_number")
            chunk_index = item.get("chunk_index")

            source_lines = []

            for source in item.get("sources") or []:

                source_id = self._get_source_id(source)
                source_name = self._get_source_name(source)

                if source_id:
                    source_lines.append(
                        f"- {source_id}: {source_name}"
                    )

            source_text = (
                "\n".join(source_lines)
                if source_lines
                else "Chưa đối chiếu được nguồn thư mục."
            )

            sections.append(
                f"[Tài liệu {index}]\n"
                f"Document ID: {item.get('document_id')}\n"
                f"Tên PDF: {document_name}\n"
                f"Nguồn tham khảo:\n{source_text}\n"
                f"Trang: {page_number}\n"
                f"Chunk: {chunk_index}\n"
                f"Nội dung:\n{item['content']}"
            )

        return "\n\n".join(sections)

    # =====================================================
    # 6. FORMAT GRAPH CONTEXT
    # =====================================================

    def format_graph_context(
        self,
        graph_context: List[Dict[str, Any]],
    ) -> str:

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
    # 7. BUILD COMBINED CONTEXT
    # =====================================================

    def build_combined_context(
        self,
        vector_context: str,
        graph_context: str,
    ) -> str:

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
    # 8. MAIN CONTEXT BUILDER
    # =====================================================

    def build(
        self,
        retrieval_result: Dict[str, Any],
    ) -> Dict[str, Any]:

        if not isinstance(retrieval_result, dict):
            raise TypeError(
                "retrieval_result phải là dictionary."
            )

        query = str(
            retrieval_result.get("query") or ""
        ).strip()

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

        # 1. Vector Context
        vector_context = self.build_vector_context(
            vector_results
        )

        # 2. Graph Context
        graph_context = self.build_graph_context(
            graph_results
        )

        # 3. Tổng hợp Source duy nhất
        sources = self._collect_unique_sources(
            vector_context
        )

        # 4. Format
        formatted_vector = self.format_vector_context(
            vector_context
        )

        formatted_graph = self.format_graph_context(
            graph_context
        )

        # 5. Combined Context
        combined_context = self.build_combined_context(
            formatted_vector,
            formatted_graph,
        )

        return {
            "query": query,

            "context": {
                "vector_context": vector_context,
                "graph_context": graph_context,
                "combined_context": combined_context,
                "sources": sources,
            },

            "sources": sources,

            "metadata": {
                "vector_count": len(vector_context),
                "graph_count": len(graph_context),
                "source_count": len(sources),
                "unique_document_count": len({
                    item.get("document_id")
                    for item in vector_context
                    if item.get("document_id")
                }),
                "combined_context_length": len(combined_context),
            },
        }


# Singleton
context_builder_service = ContextBuilderService()
