
import logging

from fastapi import APIRouter, HTTPException, Query, Request

from app.services.timeline_service import TimelineService


router = APIRouter(
    prefix="/api/timeline",
    tags=["Timeline"]
)

logger = logging.getLogger(__name__)


@router.get("/")
def get_timeline(
    request: Request,
    start_year: int = Query(default=None, ge=1771, le=1802),
    end_year: int = Query(default=None, ge=1771, le=1802),
    keyword: str = Query(default=None, max_length=200)
):
    if (
        start_year is not None
        and end_year is not None
        and start_year > end_year
    ):
        raise HTTPException(
            status_code=400,
            detail="Năm bắt đầu không được lớn hơn năm kết thúc."
        )

    driver = getattr(request.app.state, "neo4j_driver", None)

    if driver is None:
        raise HTTPException(
            status_code=503,
            detail="Neo4j chưa được khởi tạo."
        )

    try:
        service = TimelineService(driver)

        return service.get_timeline(
            start_year=start_year,
            end_year=end_year,
            keyword=keyword
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception("Lỗi khi truy xuất Timeline")

        raise HTTPException(
            status_code=500,
            detail="Không thể truy xuất dòng thời gian lịch sử."
        )
