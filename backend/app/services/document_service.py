
# Trích xuất, chuẩn hóa và định danh file PDF

import re
import hashlib
import unicodedata
import logging
import fitz

from pathlib import Path
from typing import Dict, Any

from app.schemas.document import (
    PageContent,
    DocumentExtractionResponse
)


logger = logging.getLogger(__name__)


class DocumentProcessingError(Exception):
    pass


class DocumentService:

    @staticmethod
    def generate_document_id(filename: str) -> str:

        normalized = Path(filename).name.strip()

        if not normalized:
            raise DocumentProcessingError(
                "Không xác định được tên file PDF."
            )

        return f"FILE:{normalized}"

    @staticmethod
    def calculate_content_hash(pdf_bytes: bytes) -> str:

        if not pdf_bytes:
            raise DocumentProcessingError(
                "Không thể tính hash của file rỗng."
            )

        return hashlib.sha256(pdf_bytes).hexdigest()

    @staticmethod
    def get_file_metadata(
        pdf_bytes: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Tạo metadata định danh file dùng chung cho Neo4j và ChromaDB.
        """

        document_id = DocumentService.generate_document_id(
            filename
        )

        content_hash = DocumentService.calculate_content_hash(
            pdf_bytes
        )

        return {
            "document_id": document_id,
            "filename": Path(filename).name,
            "content_hash": content_hash,
            "sync_status": "pending"
        }

    @staticmethod
    def fix_legacy_vietnamese(text: str) -> str:
        """
        Sửa lỗi ánh xạ ký tự tiếng Việt trong PDF sử dụng
        bảng mã/font cũ.
        """

        if not text:
            return ""

        replacements = {
            "ð": "Đ",
            "ñ": "đ",
        }

        return text.translate(
            str.maketrans(replacements)
        )

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Chuẩn hóa và làm sạch văn bản PDF.
        """

        if not text:
            return ""

        text = DocumentService.fix_legacy_vietnamese(text)

        text = unicodedata.normalize("NFC", text)

        text = text.replace("\xa0", " ")
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")
        text = text.replace("\t", " ")

        lines = [
            re.sub(r" {2,}", " ", line).strip()
            for line in text.split("\n")
        ]

        text = "\n".join(lines)

        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    @staticmethod
    def extract_pdf(
        pdf_bytes: bytes,
        filename: str
    ) -> DocumentExtractionResponse:

        if not pdf_bytes:
            raise DocumentProcessingError(
                "File PDF không có dữ liệu."
            )

        document = None

        try:
            document = fitz.open(
                stream=pdf_bytes,
                filetype="pdf"
            )

            if not document.is_pdf:
                raise DocumentProcessingError(
                    "File không phải định dạng PDF hợp lệ."
                )

            if document.needs_pass:
                raise DocumentProcessingError(
                    "PDF được bảo vệ bằng mật khẩu."
                )

            pages = []
            empty_pages = []
            total_characters = 0

            for index, page in enumerate(document):

                raw_text = page.get_text(
                    "text",
                    sort=True
                )

                content = DocumentService.clean_text(
                    raw_text
                )

                character_count = len(content)

                if not content:
                    empty_pages.append(index + 1)

                total_characters += character_count

                pages.append(
                    PageContent(
                        page_number=index + 1,
                        content=content,
                        character_count=character_count
                    )
                )

                logger.info(
                    "PDF %s | Page %s | %s characters",
                    filename,
                    index + 1,
                    character_count
                )

            total_pages = len(document)

            if total_pages == 0:
                raise DocumentProcessingError(
                    "PDF không có trang nào."
                )

            return DocumentExtractionResponse(
                filename=filename,
                total_pages=total_pages,
                extracted_pages=(
                    total_pages - len(empty_pages)
                ),
                empty_pages=empty_pages,
                total_characters=total_characters,
                pages=pages
            )

        except DocumentProcessingError:
            raise

        except Exception as e:
            logger.exception(
                "PDF extraction failed: %s",
                filename
            )

            raise DocumentProcessingError(
                f"Không thể xử lý PDF: {str(e)}"
            ) from e

        finally:
            if document is not None:
                document.close()
