
from fastapi import APIRouter, HTTPException, Query, Request

from app.services.graph_service import GraphService


router = APIRouter(
    prefix="/api/graph",
    tags=["Knowledge Graph"]
)


@router.get("/")
def get_graph(
    request: Request,
    keyword: str = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500)
):
    driver = request.app.state.neo4j_driver

    service = GraphService(driver)

    return service.get_graph(
        keyword=keyword,
        limit=limit
    )


@router.get("/search")
def search_entities(
    request: Request,
    keyword: str = Query(
        ...,
        min_length=1,
        max_length=200
    ),
    entity_type: str = Query(
        default=None,
        description="NhanVat, SuKien hoặc DiaDiem"
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100
    )
):
    """
    Tìm kiếm nhân vật, sự kiện và địa điểm trong Knowledge Graph.
    """

    driver = request.app.state.neo4j_driver

    service = GraphService(driver)

    try:
        return service.search_entities(
            keyword=keyword,
            entity_type=entity_type,
            limit=limit
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get("/node/{node_id}")
def get_node_neighbors(
    node_id: str,
    request: Request,
    limit: int = Query(default=50, ge=1, le=200)
):
    driver = request.app.state.neo4j_driver

    service = GraphService(driver)

    result = service.get_node_neighbors(
        node_id=node_id,
        limit=limit
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy node trong đồ thị."
        )

    return result
