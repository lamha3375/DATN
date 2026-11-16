import logging

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    status
)
from flask import app
from streamlit import form
from starlette.concurrency import run_in_threadpool


from app.services.document_service import (
    DocumentService,
    DocumentProcessingError
)

from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService
from app.services.document_processing_service import (
    DocumentProcessingService
)

from app.schemas.document import DocumentExtractionResponse
from app.schemas.chunk import ChunkingResponse
from app.schemas.embedding import EmbeddingResponse
from app.schemas.vector_store import VectorStoreResponse
from app.schemas.document_processing import (
    DocumentProcessingResponse
)


logger = logging.getLogger(__name__)
document_processing_service = DocumentProcessingService()

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


# Khởi tạo Embedding Service
embedding_service = EmbeddingService()
vector_store_service = VectorStoreService()


@router.post(
    "/extract",
    response_model=DocumentExtractionResponse,
    summary="Trích xuất nội dung từ PDF"
)
async def extract_document(
    file: UploadFile = File(...)
):
    try:
        # Kiểm tra tên và định dạng file
        if (
            not file.filename
            or not file.filename.lower().endswith(".pdf")
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chỉ hỗ trợ file PDF."
            )

        # Đọc tối đa 20 MB + 1 byte
        pdf_bytes = await file.read(MAX_FILE_SIZE + 1)

        # Kiểm tra dung lượng
        if len(pdf_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File PDF vượt quá giới hạn 20 MB."
            )

        # Kiểm tra file rỗng
        if not pdf_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File PDF không được để trống."
            )

        # Trích xuất nội dung PDF
        result = DocumentService.extract_pdf(
            pdf_bytes=pdf_bytes,
            filename=file.filename
        )

        return result

    except HTTPException:
        raise

    except DocumentProcessingError as e:
        logger.warning("Document processing error: %s", e)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception:
        logger.exception("Unexpected error while extracting PDF.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Đã xảy ra lỗi khi trích xuất tài liệu PDF."
        )

    finally:
        await file.close()


@router.post(
    "/chunk",
    response_model=ChunkingResponse,
    summary="Chia văn bản thành các chunks"
)
async def chunk_document(
    document: DocumentExtractionResponse
):
    try:
        result = ChunkingService.chunk_document(
            document=document
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception:
        logger.exception("Unexpected error while chunking document.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Đã xảy ra lỗi khi chia văn bản thành chunks."
        )


@router.post(
    "/embed",
    response_model=EmbeddingResponse,
    summary="Chuyển chunks thành vector embedding"
)
def embed_document(
    request: ChunkingResponse
):
    try:
        if not request.chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không có chunks để tạo embedding."
            )

        result = embedding_service.embed_chunks(
            chunks=request.chunks
        )

        return result

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception:
        logger.exception("Unexpected error while generating embeddings.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Đã xảy ra lỗi khi tạo vector embedding."
        )

@router.post(
    "/store",
    response_model=VectorStoreResponse,
    summary="Lưu vector embedding vào ChromaDB"
)
def store_document_embeddings(request: EmbeddingResponse):
    try:
        result = vector_store_service.store_embeddings(
            request=request
        )
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception:
        logging.exception("Lỗi khi lưu embedding vào ChromaDB")
        raise HTTPException(
            status_code=500,
            detail="Đã xảy ra lỗi khi lưu vector vào ChromaDB."
        )

def _process_pdf(
    pdf_bytes: bytes,
    filename: str
) -> dict:

    # Bước 1: Trích xuất nội dung PDF
    document = DocumentService.extract_pdf(
        pdf_bytes=pdf_bytes,
        filename=filename
    )

    # Bước 2: Chia văn bản thành chunks
    chunk_result = ChunkingService.chunk_document(
        document=document
    )

    # Bước 3: Embedding theo batch và lưu ChromaDB
    processing_result = (
        document_processing_service.process_chunks(
            chunks=chunk_result.chunks
        )
    )

    return {
        "document_name": document.filename,
        "total_pages": document.total_pages,
        "extracted_pages": document.extracted_pages,
        "total_chunks": chunk_result.total_chunks,
        **processing_result
    }


@router.post(
    "/process",
    response_model=DocumentProcessingResponse,
    summary="Tự động xử lý PDF và lưu vector vào ChromaDB"
)
async def process_document(file: UploadFile = File(...)):

    try:
        # Kiểm tra định dạng
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Chỉ hỗ trợ file PDF."
            )

        # Đọc file và kiểm tra dung lượng
        pdf_bytes = await file.read(MAX_FILE_SIZE + 1)

        if len(pdf_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File PDF vượt quá giới hạn 20 MB."
            )

        if not pdf_bytes:
            raise HTTPException(
                status_code=400,
                detail="File PDF không được để trống."
            )

        # Chạy tác vụ nặng ngoài event loop
        result = await run_in_threadpool(
            _process_pdf,
            pdf_bytes,
            file.filename
        )

        return result

    except HTTPException:
        raise

    except DocumentProcessingError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception:
        logger.exception("Lỗi khi xử lý toàn bộ tài liệu PDF")

        raise HTTPException(
            status_code=500,
            detail="Đã xảy ra lỗi khi xử lý tài liệu PDF."
        )

    finally:
        await file.close()