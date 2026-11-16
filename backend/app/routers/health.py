
from fastapi import APIRouter, Request
from datetime import datetime, timezone

router = APIRouter(
    prefix="/health",
    tags=["System Health"]
)


@router.get("/")
def health_check(request: Request):
    """Kiểm tra trạng thái Backend và Neo4j."""

    neo4j_driver = request.app.state.neo4j_driver

    try:
        neo4j_driver.verify_connectivity()

        return {
            "status": "healthy",
            "application": "Tay Son GraphRAG",
            "neo4j": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception:
        return {
            "status": "degraded",
            "application": "Tay Son GraphRAG",
            "neo4j": "disconnected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
