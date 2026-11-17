
import hashlib
import re
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple, Optional

from transformers import AutoTokenizer

from app.schemas.document import DocumentExtractionResponse
from app.schemas.chunk import TextChunk, ChunkingResponse


class ChunkingService:
    """
    Chia PDF thành các chunks theo tokenizer multilingual-e5-base.

    Mỗi chunk được gắn:
    - document_id: ID liên kết DocumentFile trong Neo4j.
    - document_name: Tên file PDF.
    - content_hash: SHA256 phiên bản nội dung PDF.
    - page_number: Trang PDF.
    - chunk_id: ID duy nhất của chunk.
    """

    MODEL_NAME = "intfloat/multilingual-e5-base"

    MAX_SEQUENCE_LENGTH = 512

    # Chừa chỗ cho prefix passage: và special tokens.
    CHUNK_SIZE = 380
    CHUNK_OVERLAP = 60

    @classmethod
    @lru_cache(maxsize=1)
    def _get_tokenizer(cls):
        return AutoTokenizer.from_pretrained(cls.MODEL_NAME)

    @classmethod
    def _token_ids(
        cls,
        text: str,
        add_special_tokens: bool = False
    ) -> List[int]:

        return cls._get_tokenizer().encode(
            text,
            add_special_tokens=add_special_tokens,
            truncation=False,
        )

    @classmethod
    def _token_count(cls, text: str) -> int:
        return len(
            cls._token_ids(
                f"passage: {text}",
                add_special_tokens=True
            )
        )

    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:

        text = re.sub(r"[ \t]+", " ", text.strip())

        if not text:
            return []

        return [
            part.strip()
            for part in re.split(
                r"(?<=[.!?…])\s+",
                text
            )
            if part.strip()
        ]

    @classmethod
    def _split_oversized_sentence(
        cls,
        sentence: str
    ) -> List[str]:

        words = sentence.split()

        pieces: List[str] = []
        current: List[str] = []

        for word in words:

            candidate = " ".join(current + [word])

            if cls._token_count(candidate) <= cls.CHUNK_SIZE:
                current.append(word)
                continue

            if current:
                pieces.append(" ".join(current))
                current = []

            if cls._token_count(word) <= cls.CHUNK_SIZE:
                current = [word]
                continue

            # Xử lý từ hoặc chuỗi quá dài không có khoảng trắng.
            ids = cls._token_ids(
                word,
                add_special_tokens=False
            )

            budget = max(1, cls.CHUNK_SIZE - 8)

            for offset in range(0, len(ids), budget):

                decoded = cls._get_tokenizer().decode(
                    ids[offset:offset + budget],
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=False,
                ).strip()

                if decoded:
                    pieces.append(decoded)

        if current:
            pieces.append(" ".join(current))

        return pieces

    @classmethod
    def _build_segments(cls, text: str) -> List[str]:

        segments: List[str] = []

        paragraphs = re.split(
            r"\n\s*\n",
            text.strip()
        )

        for paragraph in paragraphs:

            paragraph = paragraph.strip()

            if not paragraph:
                continue

            for sentence in cls._split_into_sentences(paragraph):

                if cls._token_count(sentence) <= cls.CHUNK_SIZE:
                    segments.append(sentence)

                else:
                    segments.extend(
                        cls._split_oversized_sentence(sentence)
                    )

        return segments

    @classmethod
    def _tail_overlap(cls, text: str) -> str:

        ids = cls._token_ids(
            text,
            add_special_tokens=False
        )

        if not ids:
            return ""

        tail = ids[-cls.CHUNK_OVERLAP:]

        return cls._get_tokenizer().decode(
            tail,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        ).strip()

    @classmethod
    def _create_chunks(
        cls,
        text: str
    ) -> List[Tuple[str, int]]:
        """
        Trả về danh sách (nội dung chunk, số token thực tế).
        """

        segments = cls._build_segments(text)

        if not segments:
            return []

        chunks: List[Tuple[str, int]] = []

        current = ""

        for segment in segments:

            candidate = (
                f"{current}\n\n{segment}"
                if current
                else segment
            )

            if cls._token_count(candidate) <= cls.CHUNK_SIZE:
                current = candidate
                continue

            if current:

                count = cls._token_count(current)

                chunks.append(
                    (current.strip(), count)
                )

                overlap = cls._tail_overlap(current)

                candidate = (
                    f"{overlap}\n\n{segment}"
                    if overlap
                    else segment
                )

            else:
                candidate = segment

            # Không để overlap làm vượt giới hạn token.
            if cls._token_count(candidate) > cls.CHUNK_SIZE:
                candidate = segment

            if cls._token_count(candidate) > cls.CHUNK_SIZE:
                raise ValueError(
                    "Không thể chia đoạn văn về giới hạn token an toàn."
                )

            current = candidate

        if current.strip():

            chunks.append(
                (
                    current.strip(),
                    cls._token_count(current.strip())
                )
            )

        # Kiểm tra toàn bộ chunks trước khi embedding.
        for content, token_count in chunks:

            actual = cls._token_count(content)

            if actual > cls.CHUNK_SIZE or token_count != actual:
                raise ValueError(
                    "Chunk vượt giới hạn token cấu hình."
                )

        return chunks

    @staticmethod
    def _make_document_identity(
        filename: str,
        pages
    ) -> Tuple[str, str]:

        filename = Path(filename).name.strip()

        if not filename:
            raise ValueError(
                "Tên tài liệu không được để trống."
            )

        normalized_parts = [
            f"{page.page_number}:{(page.content or '').strip()}"
            for page in pages
        ]

        full_text = "\n".join(normalized_parts)

        content_digest = hashlib.sha256(
            full_text.encode("utf-8")
        ).hexdigest()

        document_id = f"FILE:{filename}"

        return document_id, content_digest

    @classmethod
    def chunk_document(
        cls,
        document: DocumentExtractionResponse,
        document_id: Optional[str] = None,
        content_hash: Optional[str] = None,
    ) -> ChunkingResponse:

        if not document.filename or not document.filename.strip():
            raise ValueError(
                "Tên tài liệu không được để trống."
            )

        if cls.CHUNK_OVERLAP < 0 or cls.CHUNK_OVERLAP >= cls.CHUNK_SIZE:
            raise ValueError(
                "CHUNK_OVERLAP phải >= 0 và nhỏ hơn CHUNK_SIZE."
            )

        filename = Path(document.filename).name

        generated_document_id, generated_content_hash = (
            cls._make_document_identity(
                filename,
                document.pages
            )
        )

        # Ưu tiên định danh và hash được cung cấp từ DocumentService.
        document_id = document_id or generated_document_id
        content_hash = content_hash or generated_content_hash

        if not document_id.strip():
            raise ValueError("document_id không hợp lệ.")

        if not content_hash.strip():
            raise ValueError("content_hash không hợp lệ.")

        chunks: List[TextChunk] = []

        total_characters = 0

        for page in document.pages:

            page_content = (page.content or "").strip()

            if not page_content:
                continue

            page_chunks = cls._create_chunks(page_content)

            for index, (content, token_count) in enumerate(
                page_chunks,
                start=1
            ):

                content = content.strip()

                if not content:
                    continue

                chunk_digest = hashlib.sha256(
                    content.encode("utf-8")
                ).hexdigest()[:12]

                chunk_id = (
                    f"{document_id}_"
                    f"{content_hash[:12]}_"
                    f"P{page.page_number}_"
                    f"C{index}_"
                    f"{chunk_digest}"
                )

                chunks.append(
                    TextChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        document_name=filename,
                        page_number=page.page_number,
                        source_id=None,
                        content_hash=content_hash,
                        content=content,
                        character_count=len(content),
                        token_count=token_count,
                        chunk_index=index,
                    )
                )

                total_characters += len(content)

        return ChunkingResponse(
            document_id=document_id,
            document_name=filename,
            content_hash=content_hash,
            total_pages=document.total_pages,
            total_chunks=len(chunks),
            total_characters=total_characters,
            chunks=chunks,
        )
