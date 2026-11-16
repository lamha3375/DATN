import re
import fitz

from app.schemas.document import (
    PageContent,
    DocumentExtractionResponse
)


class DocumentProcessingError(Exception):
    pass


class DocumentService:

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Chuẩn hóa văn bản trích xuất từ PDF.
        """

        if not text:
            return ""

        # Chuẩn hóa ký tự khoảng trắng
        text = text.replace("\xa0", " ")
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")
        text = text.replace("\t", " ")

        # Xử lý khoảng trắng trên từng dòng
        lines = [
            re.sub(r" {2,}", " ", line).strip()
            for line in text.split("\n")
        ]

        text = "\n".join(lines)

        # Giảm các dòng trống liên tiếp
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

                # Trích xuất văn bản
                raw_text = page.get_text(
                    "text",
                    sort=True
                )

                # Chuẩn hóa văn bản
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

            total_pages = len(document)
            document.close()

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
            raise DocumentProcessingError(
                f"Không thể xử lý PDF: {str(e)}"
            ) from e