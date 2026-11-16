from fastapi import APIRouter, HTTPException, Query, Request
from app.services.source_services import SourceService


router = APIRouter(
    prefix="/api/sources",
    tags=["Sources"]
)


@router.get("/")
def get_sources(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    keyword: str = Query(default=None)
):
    driver = request.app.state.neo4j_driver

    service = SourceService(driver)

    return service.get_all_sources(
        skip=skip,
        limit=limit,
        keyword=keyword
    )


@router.get("/{source_id}")
def get_source_detail(
    source_id: str,
    request: Request
):
    driver = request.app.state.neo4j_driver

    service = SourceService(driver)

    source = service.get_source_by_id(source_id)

    if source is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy nguồn tài liệu."
        )

    return {
        "data": source
    }