
from typing import Iterator, List

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from app.schemas.chunk import TextChunk
from app.schemas.embedding import EmbeddingItem


class EmbeddingService:
    MODEL_NAME = "intfloat/multilingual-e5-base"
    MAX_SEQUENCE_LENGTH = 512

    # CPU configuration
    BATCH_SIZE = 8
    CPU_THREADS = 6

    def __init__(self):
        self.model = None

    def load_model(self) -> SentenceTransformer:
        if self.model is None:
            torch.set_num_threads(self.CPU_THREADS)

            self.model = SentenceTransformer(
                self.MODEL_NAME,
                device="cpu"
            )

            self.model.max_seq_length = self.MAX_SEQUENCE_LENGTH

        return self.model

    def embed_chunks_in_batches(
        self,
        chunks: List[TextChunk]
    ) -> Iterator[List[EmbeddingItem]]:

        if not chunks:
            raise ValueError("Danh sách chunks không được để trống.")

        model = self.load_model()

        for start in range(0, len(chunks), self.BATCH_SIZE):
            batch = chunks[start:start + self.BATCH_SIZE]

            texts = []

            for chunk in batch:
                content = chunk.content.strip()

                if not content:
                    raise ValueError(
                        f"Chunk {chunk.chunk_id} có nội dung rỗng."
                    )

                texts.append(f"passage: {content}")

            vectors = model.encode(
                texts,
                batch_size=self.BATCH_SIZE,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True
            )

            if vectors.ndim != 2:
                raise ValueError("Embedding không đúng định dạng.")

            if vectors.shape[0] != len(batch):
                raise ValueError("Số lượng embedding không khớp batch.")

            if not np.isfinite(vectors).all():
                raise ValueError("Embedding chứa giá trị không hợp lệ.")

            dimensions = int(vectors.shape[1])

            results = []

            for chunk, vector in zip(batch, vectors):
                results.append(
                    EmbeddingItem(
                        chunk_id=chunk.chunk_id,
                        document_name=chunk.document_name,
                        page_number=chunk.page_number,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        embedding=vector.tolist(),
                        dimensions=dimensions
                    )
                )

            yield results

    def embed_query(self, query: str) -> List[float]:
        if not query or not query.strip():
            raise ValueError("Câu truy vấn không được để trống.")

        model = self.load_model()

        text = f"query: {query.strip()}"

        vector = model.encode(
            [text],
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        if vector.ndim != 2 or vector.shape[0] != 1:
            raise ValueError(
                "Không thể tạo embedding cho câu truy vấn."
            )

        if not np.isfinite(vector).all():
            raise ValueError(
                "Embedding câu truy vấn chứa giá trị không hợp lệ."
            )

        return vector[0].tolist()
