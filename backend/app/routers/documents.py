
import hashlib
import json
import logging

from pathlib import Path
from typing import Any, Optional

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    status,
)

from starlette.concurrency import run_in_threadpool

from app.core.neo4j_connection import neo4j_connection

from app.services.document_service import (
    DocumentService,
    DocumentProcessingError,
)

from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService
from app.services.document_processing_service import (
    DocumentProcessingService,
)

from app.schemas.document import DocumentExtractionResponse
from app.schemas.chunk import ChunkingResponse
from app.schemas.embedding import EmbeddingResponse
from app.schemas.vector_store import VectorStoreResponse
from app.schemas.document_processing import DocumentProcessingResponse


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# ============================================================
# CONFIGURATION
# ============================================================

MAX_FILE_SIZE = 100 * 1024 * 1024

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DOCUMENTS_DIR = PROJECT_ROOT / "documents"

MANIFEST_PATH = (
    Path(__file__).resolve().parents[2]
    / ".document_sync_manifest.json"
)


# ============================================================
# SERVICES
# ============================================================

embedding_service = EmbeddingService()

vector_store_service = VectorStoreService()

document_processing_service = DocumentProcessingService()


# ============================================================
# PDF VALIDATION
# ============================================================

def _validate_pdf_filename(filename: Optional[str]) -> str:
    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Tên file không hợp lệ.",
        )

    filename = Path(filename).name

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Chỉ hỗ trợ file PDF.",
        )

    return filename


async def _read_pdf_upload(file: UploadFile) -> bytes:
    _validate_pdf_filename(file.filename)

    pdf_bytes = await file.read(MAX_FILE_SIZE + 1)

    if len(pdf_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File PDF vượt quá giới hạn 100 MB.",
        )

    if not pdf_bytes:
        raise HTTPException(
            status_code=400,
            detail="File PDF không được để trống.",
        )

    return pdf_bytes


def _read_pdf_from_disk(pdf_path: Path) -> bytes:
    if not pdf_path.is_file():
        raise FileNotFoundError(
            f"Không tìm thấy tài liệu: {pdf_path.name}"
        )

    file_size = pdf_path.stat().st_size

    if file_size > MAX_FILE_SIZE:
        raise ValueError(
            f"File vượt quá giới hạn 100 MB: {pdf_path.name}"
        )

    if file_size == 0:
        raise ValueError(
            f"File PDF rỗng: {pdf_path.name}"
        )

    return pdf_path.read_bytes()


# ============================================================
# DOCUMENT IDENTIFICATION
# ============================================================

def _stable_document_id(filename: str) -> str:
    """
    ID thống nhất với DocumentFile trong Neo4j.

    Ví dụ:
        FILE:Lịch sử Việt Nam 4.pdf
    """

    filename = Path(filename).name

    return f"FILE:{filename}"


def _calculate_content_hash(pdf_bytes: bytes) -> str:
    """
    Hash SHA256 của file PDF gốc.

    Cùng một file phải có cùng content_hash ở:
    - Manifest
    - Neo4j DocumentFile
    - ChromaDB chunks
    """

    return hashlib.sha256(pdf_bytes).hexdigest()


# ============================================================
# NEO4J DOCUMENT FILE MANAGEMENT
# ============================================================

def _update_document_file(
    document_id: str,
    filename: str,
    sync_status: str,
    content_hash: Optional[str] = None,
    total_pages: Optional[int] = None,
    total_chunks: Optional[int] = None,
    relative_path: Optional[str] = None,
    last_error: Optional[str] = None,
) -> None:
    """
    Tạo hoặc cập nhật node DocumentFile.

    Không xóa hoặc chỉnh sửa bất kỳ relationship lịch sử nào.

    MERGE chỉ tác động đến node DocumentFile có document_id tương ứng.
    Những quan hệ USES_FILE và TRICH_DAN_TU_NGUON được giữ nguyên.
    """

    driver = neo4j_connection.get_driver()

    query = """
    MERGE (df:DocumentFile {
        document_id: $document_id
    })

    ON CREATE SET
        df.created_at = datetime()

    SET
        df.filename = $filename,
        df.sync_status = $sync_status,
        df.updated_at = datetime(),
        df.content_hash = coalesce(
            $content_hash,
            df.content_hash
        ),
        df.total_pages = coalesce(
            $total_pages,
            df.total_pages
        ),
        df.total_chunks = coalesce(
            $total_chunks,
            df.total_chunks
        ),
        df.relative_path = coalesce(
            $relative_path,
            df.relative_path
        ),
        df.last_error = $last_error

    RETURN df.document_id AS document_id
    """

    with driver.session() as session:
        record = session.run(
            query,
            document_id=document_id,
            filename=filename,
            sync_status=sync_status,
            content_hash=content_hash,
            total_pages=total_pages,
            total_chunks=total_chunks,
            relative_path=relative_path,
            last_error=last_error,
        ).single()

    if record is None:
        raise RuntimeError(
            f"Không thể cập nhật DocumentFile: {document_id}"
        )


def _mark_document_processing(
    document_id: str,
    filename: str,
    relative_path: Optional[str] = None,
) -> None:
    _update_document_file(
        document_id=document_id,
        filename=filename,
        sync_status="processing",
        relative_path=relative_path,
        last_error=None,
    )


def _mark_document_failed(
    document_id: str,
    filename: str,
    error: str,
    relative_path: Optional[str] = None,
) -> None:
    _update_document_file(
        document_id=document_id,
        filename=filename,
        sync_status="failed",
        relative_path=relative_path,
        last_error=error[:2000],
    )


def _mark_document_synced(
    document_id: str,
    filename: str,
    content_hash: str,
    total_pages: int,
    total_chunks: int,
    relative_path: Optional[str] = None,
) -> None:
    _update_document_file(
        document_id=document_id,
        filename=filename,
        sync_status="synced",
        content_hash=content_hash,
        total_pages=total_pages,
        total_chunks=total_chunks,
        relative_path=relative_path,
        last_error=None,
    )


# ============================================================
# MANIFEST MANAGEMENT
# ============================================================

def _load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        return {}

    try:
        with MANIFEST_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            logger.warning(
                "Manifest không hợp lệ, khởi tạo lại."
            )
            return {}

        return data

    except (json.JSONDecodeError, OSError):
        logger.exception(
            "Không thể đọc document sync manifest."
        )
        return {}


def _save_manifest(manifest: dict[str, Any]) -> None:
    MANIFEST_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_path = MANIFEST_PATH.with_suffix(".tmp")

    try:
        with temp_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                manifest,
                file,
                ensure_ascii=False,
                indent=4,
            )

        temp_path.replace(MANIFEST_PATH)

    except Exception:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)

        raise


# ============================================================
# PDF PROCESSING PIPELINE
# ============================================================

def _process_pdf_in_batches(
    pdf_bytes: bytes,
    filename: str,
    relative_path: Optional[str] = None,
) -> dict:
    """
    Xử lý một PDF hoàn chỉnh.

    Tên hàm được giữ lại để tương thích với router cũ.

    Thực tế:
    - Trích xuất toàn bộ trang.
    - Chunk toàn bộ tài liệu để chunk_index không bị reset
      giữa các batch trang.
    - Embedding vẫn được thực hiện theo batch trong
      EmbeddingService.
    """

    filename = Path(filename).name

    document_id = _stable_document_id(filename)

    content_hash = _calculate_content_hash(pdf_bytes)

    _mark_document_processing(
        document_id=document_id,
        filename=filename,
        relative_path=relative_path,
    )

    try:
        # ----------------------------------------------------
        # 1. EXTRACT PDF
        # ----------------------------------------------------

        document = DocumentService.extract_pdf(
            pdf_bytes,
            filename,
        )

        total_pages = document.total_pages

        extracted_pages = document.extracted_pages

        logger.info(
            "Đã trích xuất PDF %s: %s/%s trang.",
            filename,
            extracted_pages,
            total_pages,
        )

        # ----------------------------------------------------
        # 2. CHUNK DOCUMENT
        # ----------------------------------------------------

        chunk_result = ChunkingService.chunk_document(
            document,
            document_id=document_id,
            content_hash=content_hash,
        )

        chunks = chunk_result.chunks

        if not chunks:
            raise ValueError(
                f"PDF không có nội dung để tạo chunks: {filename}"
            )

        # Kiểm tra định danh và hash trước khi lưu.
        for chunk in chunks:
            if chunk.document_id != document_id:
                raise ValueError(
                    "document_id của chunk không khớp tài liệu."
                )

            if chunk.content_hash != content_hash:
                raise ValueError(
                    "content_hash của chunk không khớp PDF."
                )

        logger.info(
            "PDF %s: tạo được %s chunks.",
            filename,
            len(chunks),
        )

        # ----------------------------------------------------
        # 3. EMBEDDING + STORE CHROMADB
        # ----------------------------------------------------

        processing_result = (
            document_processing_service.process_chunks(
                chunks,
                finalize_document=True,
            )
        )

        if processing_result.get("status") not in (
            "success",
            "completed",
        ):
            raise RuntimeError(
                "Không thể hoàn tất lưu chunks vào ChromaDB: "
                f"{processing_result}"
            )

        # ----------------------------------------------------
        # 4. UPDATE NEO4J DOCUMENTFILE
        # ----------------------------------------------------

        _mark_document_synced(
            document_id=document_id,
            filename=filename,
            content_hash=content_hash,
            total_pages=total_pages,
            total_chunks=len(chunks),
            relative_path=relative_path,
        )

        # ----------------------------------------------------
        # 5. RESPONSE
        # ----------------------------------------------------

        result = {
            "document_name": filename,
            "document_id": document_id,
            "content_hash": content_hash,
            "total_pages": total_pages,
            "extracted_pages": extracted_pages,
            "total_chunks": len(chunks),
            "previously_stored": processing_result.get(
                "previously_stored",
                0,
            ),
            "newly_stored": processing_result.get(
                "newly_stored",
                0,
            ),
            "removed_stale_chunks": processing_result.get(
                "removed_stale_chunks",
                0,
            ),
            "total_stored": vector_store_service.get_collection_count(),
            "status": "success",
        }

        logger.info(
            "Hoàn tất xử lý PDF %s: %s chunks.",
            filename,
            len(chunks),
        )

        return result

    except Exception as exc:
        logger.exception(
            "Lỗi khi xử lý PDF: %s",
            filename,
        )

        try:
            _mark_document_failed(
                document_id=document_id,
                filename=filename,
                error=str(exc),
                relative_path=relative_path,
            )

        except Exception:
            logger.exception(
                "Không thể cập nhật trạng thái lỗi DocumentFile: %s",
                document_id,
            )

        raise


# ============================================================
# DOCUMENT FOLDER SYNCHRONIZATION
# ============================================================

def _sync_document_folder() -> dict:
    logger.info(
        "Bắt đầu đồng bộ thư mục PDF: %s",
        DOCUMENTS_DIR,
    )

    if not DOCUMENTS_DIR.exists():
        raise FileNotFoundError(
            f"Không tìm thấy thư mục documents: {DOCUMENTS_DIR}"
        )

    # Chỉ lấy PDF trực tiếp trong documents.
    pdf_files = sorted(
        (
            path
            for path in DOCUMENTS_DIR.iterdir()
            if path.is_file()
            and path.suffix.lower() == ".pdf"
        ),
        key=lambda path: path.name.casefold(),
    )

    manifest = _load_manifest()

    results = []

    skipped_files = 0
    successful_files = 0
    failed_files = 0

    total_new_chunks = 0
    total_existing_chunks = 0
    total_removed_chunks = 0

    logger.info(
        "Tìm thấy %s file PDF.",
        len(pdf_files),
    )

    for pdf_path in pdf_files:
        filename = pdf_path.name

        document_id = _stable_document_id(filename)

        relative_path = f"documents/{filename}"

        try:
            # ------------------------------------------------
            # 1. READ PDF
            # ------------------------------------------------

            pdf_bytes = _read_pdf_from_disk(pdf_path)

            content_hash = _calculate_content_hash(pdf_bytes)

            # ------------------------------------------------
            # 2. CHECK EXISTING DATA
            # ------------------------------------------------

            previous_data = manifest.get(
                filename,
                {},
            )

            previous_hash = previous_data.get(
                "content_hash"
            )

            existing_chunk_ids = (
                vector_store_service.get_document_chunk_ids(
                    document_id
                )
            )

            # Chỉ skip khi:
            # - Hash PDF không thay đổi.
            # - ChromaDB vẫn còn chunks.
            # - Manifest có thông tin chunk hợp lệ.

            if (
                previous_hash == content_hash
                and existing_chunk_ids
                and previous_data.get("total_chunks", 0) > 0
            ):
                _mark_document_synced(
                    document_id=document_id,
                    filename=filename,
                    content_hash=content_hash,
                    total_pages=previous_data.get(
                        "total_pages",
                        0,
                    ),
                    total_chunks=previous_data.get(
                        "total_chunks",
                        len(existing_chunk_ids),
                    ),
                    relative_path=relative_path,
                )

                skipped_files += 1

                results.append({
                    "document_name": filename,
                    "document_id": document_id,
                    "content_hash": content_hash,
                    "total_chunks": len(existing_chunk_ids),
                    "status": "skipped",
                    "message": (
                        "Tài liệu không thay đổi, "
                        "đã được index."
                    ),
                })

                logger.info(
                    "Bỏ qua PDF không thay đổi: %s",
                    filename,
                )

                continue

            # ------------------------------------------------
            # 3. PROCESS PDF
            # ------------------------------------------------

            logger.info(
                "Bắt đầu đồng bộ PDF: %s",
                filename,
            )

            result = _process_pdf_in_batches(
                pdf_bytes,
                filename,
                relative_path=relative_path,
            )

            # ------------------------------------------------
            # 4. UPDATE MANIFEST
            # ------------------------------------------------

            manifest[filename] = {
                "document_id": document_id,
                "content_hash": content_hash,
                "total_chunks": result["total_chunks"],
                "total_pages": result["total_pages"],
            }

            _save_manifest(manifest)

            successful_files += 1

            total_new_chunks += result["newly_stored"]

            total_existing_chunks += result["previously_stored"]

            total_removed_chunks += result["removed_stale_chunks"]

            results.append(result)

        except Exception as exc:
            failed_files += 1

            logger.exception(
                "Không thể đồng bộ PDF: %s",
                filename,
            )

            # Nếu lỗi xảy ra trước khi pipeline bắt đầu,
            # vẫn ghi nhận trạng thái failed trong Neo4j.
            try:
                _mark_document_failed(
                    document_id=document_id,
                    filename=filename,
                    error=str(exc),
                    relative_path=relative_path,
                )

            except Exception:
                logger.exception(
                    "Không thể ghi trạng thái failed cho %s.",
                    filename,
                )

            results.append({
                "document_name": filename,
                "document_id": document_id,
                "status": "failed",
                "error": str(exc),
            })

    # --------------------------------------------------------
    # 5. SUMMARY
    # --------------------------------------------------------

    if failed_files == 0:
        overall_status = "success"

    elif successful_files > 0 or skipped_files > 0:
        overall_status = "partial_success"

    else:
        overall_status = "failed"

    response = {
        "status": overall_status,
        "documents_directory": str(DOCUMENTS_DIR),
        "total_files": len(pdf_files),
        "successful_files": successful_files,
        "skipped_files": skipped_files,
        "failed_files": failed_files,
        "newly_stored_chunks": total_new_chunks,
        "previously_stored_chunks": total_existing_chunks,
        "removed_stale_chunks": total_removed_chunks,
        "total_vector_store_chunks": (
            vector_store_service.get_collection_count()
        ),
        "results": results,
    }

    logger.info(
        "Đồng bộ thư mục hoàn tất: %s",
        response,
    )

    return response


# ============================================================
# API 1: EXTRACT
# ============================================================

@router.post(
    "/extract",
    response_model=DocumentExtractionResponse,
    summary="Trích xuất nội dung từ PDF",
)
async def extract_document(
    file: UploadFile = File(...),
):
    try:
        filename = _validate_pdf_filename(file.filename)

        pdf_bytes = await _read_pdf_upload(file)

        return await run_in_threadpool(
            DocumentService.extract_pdf,
            pdf_bytes,
            filename,
        )

    except HTTPException:
        raise

    except DocumentProcessingError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:
        logger.exception(
            "Unexpected error while extracting PDF."
        )

        raise HTTPException(
            status_code=500,
            detail="Đã xảy ra lỗi khi trích xuất tài liệu PDF.",
        )

    finally:
        await file.close()


# ============================================================
# API 2: CHUNK
# ============================================================

@router.post(
    "/chunk",
    response_model=ChunkingResponse,
    summary="Chia văn bản thành các chunks",
)
async def chunk_document(
    document: DocumentExtractionResponse,
):
    try:
        return ChunkingService.chunk_document(document)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:
        logger.exception(
            "Unexpected error while chunking document."
        )

        raise HTTPException(
            status_code=500,
            detail="Đã xảy ra lỗi khi chia văn bản thành chunks.",
        )


# ============================================================
# API 3: EMBEDDING
# ============================================================

@router.post(
    "/embed",
    response_model=EmbeddingResponse,
    summary="Chuyển chunks thành vector embedding",
)
def embed_document(
    request: ChunkingResponse,
):
    try:
        if not request.chunks:
            raise HTTPException(
                status_code=400,
                detail="Không có chunks để tạo embedding.",
            )

        return embedding_service.embed_chunks(
            chunks=request.chunks,
        )

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:
        logger.exception(
            "Unexpected error while generating embeddings."
        )

        raise HTTPException(
            status_code=500,
            detail="Đã xảy ra lỗi khi tạo vector embedding.",
        )


# ============================================================
# API 4: STORE
# ============================================================

@router.post(
    "/store",
    response_model=VectorStoreResponse,
    summary="Lưu vector embedding vào ChromaDB",
)
def store_document_embeddings(
    request: EmbeddingResponse,
):
    try:
        return vector_store_service.store_embeddings(
            request=request,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:
        logger.exception(
            "Lỗi khi lưu embedding vào ChromaDB."
        )

        raise HTTPException(
            status_code=500,
            detail="Đã xảy ra lỗi khi lưu vector vào ChromaDB.",
        )


# ============================================================
# API 5: PROCESS SINGLE PDF
# ============================================================

@router.post(
    "/process",
    response_model=DocumentProcessingResponse,
    summary="Tự động xử lý PDF và đồng bộ Neo4j, ChromaDB",
)
async def process_document(
    file: UploadFile = File(...),
):
    try:
        filename = _validate_pdf_filename(file.filename)

        pdf_bytes = await _read_pdf_upload(file)

        return await run_in_threadpool(
            _process_pdf_in_batches,
            pdf_bytes,
            filename,
        )

    except HTTPException:
        raise

    except DocumentProcessingError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:
        logger.exception(
            "Lỗi khi xử lý PDF."
        )

        raise HTTPException(
            status_code=500,
            detail="Đã xảy ra lỗi khi xử lý tài liệu PDF.",
        )

    finally:
        await file.close()


# ============================================================
# API 6: SYNC DOCUMENT FOLDER
# ============================================================

@router.post(
    "/sync-folder",
    summary="Đồng bộ toàn bộ PDF trong documents vào Neo4j và ChromaDB",
)
async def sync_document_folder():
    try:
        return await run_in_threadpool(
            _sync_document_folder,
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except Exception:
        logger.exception(
            "Lỗi khi đồng bộ thư mục PDF."
        )

        raise HTTPException(
            status_code=500,
            detail="Đã xảy ra lỗi khi đồng bộ thư mục tài liệu.",
        )
