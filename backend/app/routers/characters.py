from fastapi import APIRouter, HTTPException, Query, Request

from app.services.character_service import CharacterService


router = APIRouter(
    prefix="/api/characters",
    tags=["Characters"]
)


@router.get("/")
def get_characters(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    keyword: str = Query(default=None)
):
    driver = request.app.state.neo4j_driver

    service = CharacterService(driver)

    return service.get_all_characters(
        skip=skip,
        limit=limit,
        keyword=keyword
    )


@router.get("/{character_id}")
def get_character_detail(
    character_id: str,
    request: Request
):
    driver = request.app.state.neo4j_driver

    service = CharacterService(driver)

    character = service.get_character_by_id(character_id)

    if character is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy nhân vật."
        )

    return {
        "data": character
    }