
import os
import warnings
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.neo4j_connection import neo4j_connection

from app.routers import (
    health,
    events,
    characters,
    timeline,
    graph,
    sources,
    documents,
    chat,
)


# =========================================
# ENVIRONMENT CONFIGURATION
# =========================================

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_USE_LEGACY_KERAS"] = "1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

warnings.filterwarnings("ignore")
logging.getLogger("tensorflow").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


# =========================================
# LIFESPAN
# =========================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    try:
        neo4j_connection.connect()

        app.state.neo4j_driver = (
            neo4j_connection.get_driver()
        )

        logger.info(
            "Application startup successful."
        )

    except Exception as error:

        logger.exception(
            "Neo4j connection failed: %s",
            error
        )

        neo4j_connection.close()
        raise

    yield

    neo4j_connection.close()

    logger.info(
        "Application shutdown."
    )


# =========================================
# FASTAPI APPLICATION
# =========================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Hệ thống hỗ trợ học tập và khám phá "
        "Lịch sử Việt Nam dựa trên Knowledge Graph và GraphRAG."
    ),
    lifespan=lifespan,
)


# =========================================
# CORS CONFIGURATION
# =========================================

ALLOWED_ORIGINS = [
    # Local frontend
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:5501",
    "http://localhost:5501",

    # Frontend Dev Tunnel
    "https://s5983811-5500.asse.devtunnels.ms",
]

app.add_middleware(
    CORSMiddleware,

    allow_origins=ALLOWED_ORIGINS,

    allow_credentials=True,

    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],

    allow_headers=["*"],

    expose_headers=["*"],

    max_age=600,
)


# =========================================
# API ROUTERS
# =========================================

app.include_router(health.router)
app.include_router(events.router)
app.include_router(characters.router)
app.include_router(timeline.router)
app.include_router(graph.router)
app.include_router(sources.router)
app.include_router(documents.router)
app.include_router(chat.router)


# =========================================
# ROOT ENDPOINT
# =========================================

@app.get("/")
def root():

    return {
        "message": "Welcome to Tay Son GraphRAG API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


# =========================================
# HEALTH CHECK
# =========================================

@app.get("/cors-test")
def cors_test():

    return {
        "status": "ok",
        "message": "FastAPI CORS endpoint is working."
    }
