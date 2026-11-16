
import re
from pathlib import Path
from typing import List

from app.schemas.document import DocumentExtractionResponse
from app.schemas.chunk import TextChunk, ChunkingResponse


class ChunkingService:

    CHUNK_SIZE = 2000
    CHUNK_OVERLAP = 400

    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        """
        Chia văn bản thành các câu.
        Giữ dấu câu ở cuối câu.
        """

        sentences = re.split(
            r'(?<=[.!?])\s+',
            text.strip()
        )

        return [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

    @staticmethod
    def _split_long_text(text: str) -> List[str]:
        """
        Chia đoạn văn dài theo câu,
        sau đó theo khoảng trắng nếu cần.
        """

        if len(text) <= ChunkingService.CHUNK_SIZE:
            return [text]

        sentences = ChunkingService._split_into_sentences(text)

        if not sentences:
            return [text[i:i + ChunkingService.CHUNK_SIZE]
                    for i in range(0, len(text), ChunkingService.CHUNK_SIZE)]

        segments = []
        current = ""

        for sentence in sentences:

            # Câu dài hơn giới hạn chunk
            if len(sentence) > ChunkingService.CHUNK_SIZE:

                if current:
                    segments.append(current)
                    current = ""

                words = sentence.split()
                word_chunk = ""

                for word in words:

                    candidate = (
                        f"{word_chunk} {word}"
                        if word_chunk else word
                    )

                    if len(candidate) <= ChunkingService.CHUNK_SIZE:
                        word_chunk = candidate

                    else:
                        if word_chunk:
                            segments.append(word_chunk)

                        # Trường hợp một từ quá dài
                        if len(word) > ChunkingService.CHUNK_SIZE:
                            for i in range(
                                0,
                                len(word),
                                ChunkingService.CHUNK_SIZE
                            ):
                                segments.append(
                                    word[i:i + ChunkingService.CHUNK_SIZE]
                                )
                            word_chunk = ""
                        else:
                            word_chunk = word

                if word_chunk:
                    segments.append(word_chunk)

                continue

            candidate = (
                f"{current} {sentence}"
                if current else sentence
            )

            if len(candidate) <= ChunkingService.CHUNK_SIZE:
                current = candidate

            else:
                if current:
                    segments.append(current)

                current = sentence

        if current:
            segments.append(current)

        return segments

    @staticmethod
    def _create_chunks(text: str) -> List[str]:
        """
        Chia văn bản thành chunks có overlap.
        """

        paragraphs = re.split(r'\n\s*\n', text.strip())

        segments = []

        for paragraph in paragraphs:

            paragraph = paragraph.strip()

            if not paragraph:
                continue

            segments.extend(
                ChunkingService._split_long_text(paragraph)
            )

        chunks = []
        current = ""

        for segment in segments:

            candidate = (
                f"{current}\n\n{segment}"
                if current else segment
            )

            if len(candidate) <= ChunkingService.CHUNK_SIZE:
                current = candidate

            else:
                if current:
                    chunks.append(current)

                # Giữ lại phần cuối của chunk trước
                overlap = (
                    current[-ChunkingService.CHUNK_OVERLAP:]
                    if current else ""
                )

                current = (
                    f"{overlap}\n\n{segment}"
                    if overlap else segment
                )

                # Đảm bảo chunk không vượt quá giới hạn
                if len(current) > ChunkingService.CHUNK_SIZE:
                    current = segment

        if current:
            chunks.append(current)

        return chunks

    @staticmethod
    def chunk_document(
        document: DocumentExtractionResponse
    ) -> ChunkingResponse:
        """
        Chia nội dung tài liệu PDF thành các chunks.
        Mỗi chunk giữ lại tên tài liệu và số trang.
        """

        if not document.filename:
            raise ValueError("Tên tài liệu không được để trống.")

        if ChunkingService.CHUNK_OVERLAP >= ChunkingService.CHUNK_SIZE:
            raise ValueError(
                "CHUNK_OVERLAP phải nhỏ hơn CHUNK_SIZE."
            )

        filename = Path(document.filename).name
        document_id = Path(filename).stem

        if not document_id:
            raise ValueError("Tên tài liệu không hợp lệ.")

        chunks = []
        total_characters = 0

        for page in document.pages:

            page_content = page.content or ""

            if not page_content.strip():
                continue

            page_chunks = ChunkingService._create_chunks(
                page_content
            )

            for index, content in enumerate(page_chunks, start=1):

                content = content.strip()

                if not content:
                    continue

                chunk = TextChunk(
                    chunk_id=(
                        f"{document_id}_"
                        f"P{page.page_number}_"
                        f"C{index}"
                    ),
                    document_name=filename,
                    page_number=page.page_number,
                    content=content,
                    character_count=len(content),
                    chunk_index=index
                )

                chunks.append(chunk)
                total_characters += len(content)

        return ChunkingResponse(
            document_name=filename,
            total_pages=document.total_pages,
            total_chunks=len(chunks),
            total_characters=total_characters,
            chunks=chunks
        )
