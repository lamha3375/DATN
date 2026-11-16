
from typing import List, Dict, Any, Set
import math

from app.core.chroma_connection import chroma_connection
from app.schemas.embedding import EmbeddingItem


class VectorStoreService:

    COLLECTION_NAME = "tay_son_history"
    MAX_TOP_K = 20
    EXPECTED_DIMENSIONS = 768

    def __init__(self):
        self.client = chroma_connection.connect()

        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

    # VALIDATION
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
                    f"Embedding của {chunk_id} chứa giá trị không phải số."
                )

            if not math.isfinite(value):
                raise ValueError(
                    f"Embedding của {chunk_id} chứa NaN hoặc Infinity."
                )

    # STORE EMBEDDINGS
    def store_embeddings_batch(
        self,
        embeddings: List[EmbeddingItem]
    ) -> int:

        if not embeddings:
            return 0

        document_names = {
            item.document_name for item in embeddings
        }

        if len(document_names) != 1:
            raise ValueError(
                "Một batch chỉ được chứa chunks của cùng một tài liệu."
            )

        ids = [item.chunk_id for item in embeddings]

        if len(ids) != len(set(ids)):
            raise ValueError(
                "Batch chứa chunk_id bị trùng."
            )

        dimensions = embeddings[0].dimensions

        if dimensions != self.EXPECTED_DIMENSIONS:
            raise ValueError(
                f"Embedding phải có {self.EXPECTED_DIMENSIONS} chiều."
            )

        vectors = []
        documents = []
        metadatas = []

        for item in embeddings:

            self._validate_embedding(
                item.embedding,
                item.chunk_id
            )

            if item.dimensions != dimensions:
                raise ValueError(
                    f"Dimensions của {item.chunk_id} không khớp."
                )

            if len(item.embedding) != item.dimensions:
                raise ValueError(
                    f"Vector {item.chunk_id} không đúng số chiều."
                )

            if not item.content or not item.content.strip():
                raise ValueError(
                    f"Nội dung chunk {item.chunk_id} không được để trống."
                )

            vectors.append([
                float(value) for value in item.embedding
            ])

            documents.append(item.content)

            metadatas.append({
                "document_name": item.document_name,
                "page_number": item.page_number,
                "chunk_index": item.chunk_index
            })

        self.collection.upsert(
            ids=ids,
            embeddings=vectors,
            documents=documents,
            metadatas=metadatas
        )

        return len(ids)

    # COLLECTION INFORMATION
    def get_collection_count(self) -> int:
        return self.collection.count()

    # GET EXISTING IDS
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

    # SEARCH
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:

        if isinstance(top_k, bool) or not isinstance(top_k, int):
            raise ValueError(
                "top_k phải là số nguyên."
            )

        if top_k < 1 or top_k > self.MAX_TOP_K:
            raise ValueError(
                f"top_k phải nằm trong khoảng từ 1 đến {self.MAX_TOP_K}."
            )

        self._validate_embedding(query_embedding)

        if len(query_embedding) != self.EXPECTED_DIMENSIONS:
            raise ValueError(
                f"Query embedding phải có {self.EXPECTED_DIMENSIONS} chiều, "
                f"nhưng nhận được {len(query_embedding)} chiều."
            )

        collection_count = self.collection.count()

        if collection_count == 0:
            return []

        result = self.collection.query(
            query_embeddings=[
                [float(value) for value in query_embedding]
            ],
            n_results=min(top_k, collection_count),
            include=[
                "documents",
                "metadatas",
                "distances"
            ]
        )

        results = []

        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        for chunk_id, content, metadata, distance in zip(
            ids,
            documents,
            metadatas,
            distances
        ):

            metadata = metadata or {}
            distance = float(distance)

            results.append({
                "chunk_id": chunk_id,
                "document_name": metadata.get(
                    "document_name", ""
                ),
                "page_number": metadata.get(
                    "page_number", 0
                ),
                "chunk_index": metadata.get(
                    "chunk_index", 0
                ),
                "content": content or "",
                "distance": distance,
                "similarity": 1.0 - distance
            })

        return results

    # DELETE COLLECTION
    def delete_collection(self) -> None:

        self.client.delete_collection(
            name=self.COLLECTION_NAME
        )

        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
# Lưu ý: EXPECTED_DIMENSIONS = 768 đang cố định theo mô hình multilingual-e5-base mà bạn sử dụng
# Nếu sau này đổi embedding model, cần cập nhật đồng bộ.