
from fastapi import APIRouter, HTTPException, Query, Request

from app.services.graph_service import GraphService


router = APIRouter(
    prefix="/api/graph",
    tags=["Knowledge Graph"]
)


# GET FULL GRAPH

@router.get("/")
def get_graph(
    request: Request,
    keyword: str = Query(
        default=None,
        description="Từ khóa tìm kiếm trong Knowledge Graph"
    ),
    limit: int = Query(500, ge=1, le=500)
):
    driver = request.app.state.neo4j_driver

    service = GraphService(driver)

    try:
        return service.get_graph(
            keyword=keyword,
            limit=limit
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy Knowledge Graph: {str(error)}"
        )


# =========================================================
# SEARCH ENTITIES
# =========================================================

@router.get("/search")
def search_entities(
    request: Request,
    keyword: str = Query(
        ...,
        min_length=1,
        max_length=200,
        description="Từ khóa tìm kiếm"
    ),
    entity_type: str = Query(
        default=None,
        description=(
            "Loại thực thể: Person, Event, Location, "
            "Faction, Policy, Document, Unit, Tactics, Source. "
            "Có thể truyền tên tiếng Việt tương ứng."
        )
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100
    )
):
    """
    Tìm kiếm thực thể trong Knowledge Graph.

    Hỗ trợ:
    - Person: Nhân vật
    - Event: Sự kiện
    - Location: Địa điểm
    - Faction: Phe phái
    - Policy: Chính sách
    - Document: Văn kiện
    - Unit: Đơn vị
    - Tactics: Chiến thuật
    - Source: Nguồn tư liệu
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

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi tìm kiếm thực thể: {str(error)}"
        )


# =========================================================
# GET NODE NEIGHBORS
# =========================================================

@router.get("/node/{node_id}")
def get_node_neighbors(
    node_id: str,
    request: Request,
    limit: int = Query(
        default=50,
        ge=1,
        le=200
    )
):
    """
    Lấy node trung tâm và các node có quan hệ trực tiếp.
    """

    driver = request.app.state.neo4j_driver

    service = GraphService(driver)

    try:
        result = service.get_node_neighbors(
            node_id=node_id,
            limit=limit
        )

        # GraphService trả graph rỗng nếu không tìm thấy node.
        if not result or not result.get("center"):
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy node trong đồ thị."
            )

        return result

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy node lân cận: {str(error)}"
        )
