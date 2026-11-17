
import logging

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
)

from app.services.event_service import EventService


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/events",
    tags=["Events"]
)


# =====================================================
# GET ALL EVENTS
# =====================================================

@router.get(
    "/",
    summary="Lấy danh sách sự kiện lịch sử",
    description="Hỗ trợ phân trang và tìm kiếm theo từ khóa."
)
def get_events(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    keyword: str | None = Query(default=None, max_length=200)
):

    driver = request.app.state.neo4j_driver

    try:

        service = EventService(driver)

        return service.get_all_events(
            skip=skip,
            limit=limit,
            keyword=keyword
        )

    except Exception:

        logger.exception(
            "Lỗi khi lấy danh sách sự kiện."
        )

        raise HTTPException(
            status_code=500,
            detail="Không thể lấy danh sách sự kiện."
        )


# =====================================================
# GET EVENT DETAIL
# =====================================================

@router.get(
    "/{event_id}",
    summary="Lấy chi tiết sự kiện theo ID"
)
def get_event_detail(
    event_id: str,
    request: Request
):

    driver = request.app.state.neo4j_driver

    try:

        service = EventService(driver)

        event = service.get_event_by_id(event_id)

        if event is None:

            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy sự kiện."
            )

        return {
            "data": event
        }

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Lỗi khi lấy chi tiết sự kiện: %s",
            event_id
        )

        raise HTTPException(
            status_code=500,
            detail="Không thể lấy chi tiết sự kiện."
        )
