
import logging

from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_pipeline_service import rag_pipeline_service


router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chat"]
)

logger = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):

    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Câu hỏi không được để trống."
        )

    try:
        result = rag_pipeline_service.run(
            query=query,
            vector_top_k=request.vector_top_k,
            graph_top_k=request.graph_top_k
        )

        answer = result["answer"]

        return ChatResponse(
            query=query,
            answer=answer["answer"],
            sources=answer["sources"],
            has_sufficient_context=answer["has_sufficient_context"],
            metadata=result["metadata"]
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception:
        logger.exception("Lỗi khi xử lý yêu cầu Chat")

        raise HTTPException(
            status_code=502,
            detail="Không thể xử lý câu hỏi hiện tại. Vui lòng thử lại."
        )
