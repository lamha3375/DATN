
from typing import List, Dict, Any, Set
import math

from app.core.chroma_connection import chroma_connection
from app.schemas.embedding import EmbeddingItem


class VectorStoreService:

    COLLECTION_NAME = "tay_son_history"

    MAX_TOP_K = 20
    EXPECTED_DIMENSIONS = 768

    MAX_CHUNKS_PER_DOCUMENT = 2
    CANDIDATE_MULTIPLIER = 5

    def __init__(self):

        self.client = chroma_connection.connect()

        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={
                "hnsw:space": "cosine"
            }
        )

    # ==================================================
    # VALIDATE EMBEDDING
    # ==================================================

    @staticmethod
    def _validate_embedding(
        embedding: List[float],
        chunk_id: str = "query"
    ) -> None:

        if not embedding:
            raise ValueError(
                f"Embedding của {chunk_id} không được để trống."
            )

        for value in embedding:

            if isinstance(value, bool) or not isinstance(
                value, (int, float)
            ):
                raise ValueError(
                    f"Embedding của {chunk_id} chứa giá trị không hợp lệ."
                )

            if not math.isfinite(value):
                raise ValueError(
                    f"Embedding của {chunk_id} chứa NaN hoặc Infinity."
                )

        if len(embedding) != VectorStoreService.EXPECTED_DIMENSIONS:
            raise ValueError(
                f"Embedding phải có {VectorStoreService.EXPECTED_DIMENSIONS} chiều, "
                f"nhận được {len(embedding)} chiều."
            )

    # ==================================================
    # VALIDATE DOCUMENT METADATA
    # ==================================================

    @staticmethod
    def _validate_document_metadata(item: EmbeddingItem) -> None:

        if not item.document_id or not item.document_id.strip():
            raise ValueError(
                f"Chunk {item.chunk_id} thiếu document_id."
            )

        if not item.document_name or not item.document_name.strip():
            raise ValueError(
                f"Chunk {item.chunk_id} thiếu document_name."
            )

        if not item.content_hash or not item.content_hash.strip():
            raise ValueError(
                f"Chunk {item.chunk_id} thiếu content_hash."
            )

        if not isinstance(item.page_number, int) or item.page_number < 1:
            raise ValueError(
                f"Chunk {item.chunk_id} có page_number không hợp lệ."
            )

        if not isinstance(item.chunk_index, int) or item.chunk_index < 1:
            raise ValueError(
                f"Chunk {item.chunk_id} có chunk_index không hợp lệ."
            )

    # ==================================================
    # STORE EMBEDDINGS
    # ==================================================

    def store_embeddings_batch(
        self,
        embeddings: List[EmbeddingItem]
    ) -> int:

        if not embeddings:
            return 0

        document_ids = {
            item.document_id for item in embeddings
        }

        document_names = {
            item.document_name for item in embeddings
        }

        content_hashes = {
            item.content_hash for item in embeddings
        }

        # Một batch chỉ được chứa một tài liệu và một phiên bản.
        if len(document_ids) != 1:
            raise ValueError(
                "Một batch chỉ được chứa chunks của cùng một document_id."
            )

        if len(document_names) != 1:
            raise ValueError(
                "Một batch chỉ được chứa chunks của cùng một tài liệu."
            )

        if len(content_hashes) != 1:
            raise ValueError(
                "Một batch không được trộn nhiều phiên bản content_hash."
            )

        ids = [
            item.chunk_id for item in embeddings
        ]

        if len(ids) != len(set(ids)):
            raise ValueError(
                "Batch chứa chunk_id bị trùng lặp."
            )

        vectors = []
        documents = []
        metadatas = []

        for item in embeddings:

            self._validate_embedding(
                item.embedding,
                item.chunk_id
            )

            self._validate_document_metadata(item)

            if item.dimensions != self.EXPECTED_DIMENSIONS:
                raise ValueError(
                    f"Chunk {item.chunk_id} có số chiều embedding "
                    f"không đúng: {item.dimensions}."
                )

            if len(item.embedding) != item.dimensions:
                raise ValueError(
                    f"Chunk {item.chunk_id} có dimensions không khớp."
                )

            if not item.content or not item.content.strip():
                raise ValueError(
                    f"Chunk {item.chunk_id} có nội dung rỗng."
                )

            vectors.append([
                float(value) for value in item.embedding
            ])

            documents.append(item.content)

            # Metadata dùng để truy xuất tài liệu và vị trí chunk.
            metadata = {
                "document_id": item.document_id,
                "document_name": item.document_name,
                "page_number": item.page_number,
                "chunk_index": item.chunk_index,
                "content_hash": item.content_hash,
            }

            # ChromaDB không chấp nhận metadata None.
            if item.source_id is not None:
                metadata["source_id"] = item.source_id

            metadatas.append(metadata)

        self.collection.upsert(
            ids=ids,
            embeddings=vectors,
            documents=documents,
            metadatas=metadatas
        )

        return len(ids)

    # ==================================================
    # COLLECTION INFORMATION
    # ==================================================

    def get_collection_count(self) -> int:

        return self.collection.count()

    def get_existing_ids(
        self,
        chunk_ids: List[str]
    ) -> Set[str]:

        if not chunk_ids:
            return set()

        result = self.collection.get(
            ids=chunk_ids,
            include=[]
        )

        return set(result.get("ids", []))

    def get_document_chunk_ids(
        self,
        document_id: str
    ) -> Set[str]:

        if not document_id:
            return set()

        result = self.collection.get(
            where={
                "document_id": document_id
            },
            include=[]
        )

        return set(result.get("ids", []))

    def get_document_chunk_count(
        self,
        document_id: str
    ) -> int:
        """
        Đếm số chunks đang được lưu cho một DocumentFile.
        """

        if not document_id:
            return 0

        return len(
            self.get_document_chunk_ids(document_id)
        )

    def get_document_version_hashes(
        self,
        document_id: str
    ) -> Set[str]:
        """
        Lấy các content_hash đang tồn tại của tài liệu.
        Hữu ích khi kiểm tra tài liệu có nhiều phiên bản chunks.
        """

        if not document_id:
            return set()

        result = self.collection.get(
            where={
                "document_id": document_id
            },
            include=["metadatas"]
        )

        hashes = set()

        for metadata in result.get("metadatas") or []:

            if not metadata:
                continue

            content_hash = metadata.get("content_hash")

            if content_hash:
                hashes.add(content_hash)

        return hashes

    # ==================================================
    # DELETE CHUNKS
    # ==================================================

    def delete_ids(
        self,
        ids: List[str]
    ) -> int:

        if not ids:
            return 0

        self.collection.delete(
            ids=ids
        )

        return len(ids)

    def delete_document_chunks(
        self,
        document_id: str
    ) -> int:
        """
        Xóa chunks theo document_id.

        Chỉ gọi khi thực sự muốn xóa toàn bộ chunks của tài liệu.
        Không sử dụng trong luồng cập nhật thông thường.
        """

        if not document_id:
            return 0

        ids = self.get_document_chunk_ids(document_id)

        return self.delete_ids(
            sorted(ids)
        )

    # ==================================================
    # SEARCH HELPERS
    # ==================================================

    @staticmethod
    def _build_search_item(
        chunk_id: str,
        content: str,
        metadata: Dict[str, Any],
        distance: float
    ) -> Dict[str, Any]:

        return {
            "chunk_id": chunk_id,
            "document_id": metadata.get("document_id"),
            "document_name": metadata.get("document_name"),
            "page_number": metadata.get("page_number"),
            "chunk_index": metadata.get("chunk_index"),
            "content_hash": metadata.get("content_hash"),
            "source_id": metadata.get("source_id"),
            "content": content,
            "distance": float(distance),
            "similarity": 1.0 - float(distance)
        }

    # ==================================================
    # VECTOR SEARCH
    # ==================================================

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:

        if not isinstance(top_k, int) or isinstance(top_k, bool):
            raise ValueError(
                "top_k phải là số nguyên."
            )

        if not 1 <= top_k <= self.MAX_TOP_K:
            raise ValueError(
                f"top_k phải nằm trong khoảng 1 đến {self.MAX_TOP_K}."
            )

        self._validate_embedding(query_embedding)

        collection_count = self.collection.count()

        if collection_count == 0:
            return []

        candidate_k = min(
            max(
                top_k * self.CANDIDATE_MULTIPLIER,
                20
            ),
            collection_count
        )

        result = self.collection.query(
            query_embeddings=[
                query_embedding
            ],
            n_results=candidate_k,
            include=[
                "documents",
                "metadatas",
                "distances"
            ]
        )

        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        candidates = []

        for chunk_id, content, metadata, distance in zip(
            ids,
            documents,
            metadatas,
            distances
        ):

            if not content or not metadata:
                continue

            item = self._build_search_item(
                chunk_id=chunk_id,
                content=content,
                metadata=metadata,
                distance=distance
            )

            candidates.append(item)

        # Độ tương đồng cao hơn tương ứng distance thấp hơn.
        candidates.sort(
            key=lambda item: item["distance"]
        )

        selected = []
        document_counts = {}

        # LƯỢT 1: Ưu tiên đa dạng tài liệu.
        for item in candidates:

            document_id = (
                item.get("document_id")
                or item.get("document_name")
                or "unknown"
            )

            current_count = document_counts.get(
                document_id,
                0
            )

            if current_count >= self.MAX_CHUNKS_PER_DOCUMENT:
                continue

            selected.append(item)

            document_counts[document_id] = (
                current_count + 1
            )

            if len(selected) >= top_k:
                return selected

        # ----------------------------------------------
        # LƯỢT 2: Bổ sung nếu chưa đủ top_k.
        # ----------------------------------------------

        selected_ids = {
            item["chunk_id"]
            for item in selected
        }

        for item in candidates:

            if item["chunk_id"] in selected_ids:
                continue

            selected.append(item)

            if len(selected) >= top_k:
                break

        return selected

    # DELETE AND RECREATE COLLECTION
    def delete_collection(self) -> None:

        self.client.delete_collection(
            name=self.COLLECTION_NAME
        )

        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={
                "hnsw:space": "cosine"
            }
        )


# SHARED INSTANCE

vector_store_service = VectorStoreService()
