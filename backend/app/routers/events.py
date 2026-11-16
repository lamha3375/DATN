
from fastapi import APIRouter, HTTPException, Query, Request

from app.services.event_service import EventService


router = APIRouter(
    prefix="/api/events",
    tags=["Events"]
)


@router.get("/")
def get_events(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    keyword: str = Query(default=None)
):
    driver = request.app.state.neo4j_driver

    service = EventService(driver)

    return service.get_all_events(
        skip=skip,
        limit=limit,
        keyword=keyword
    )


@router.get("/{event_id}")
def get_event_detail(
    event_id: str,
    request: Request
):
    driver = request.app.state.neo4j_driver

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
