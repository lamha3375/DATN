import os
import warnings
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.neo4j_connection import neo4j_connection

from app.routers import health, events, characters, timeline, graph, sources, documents, chat
from fastapi.middleware.cors import CORSMiddleware

# Tắt thông báo oneDNN
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
# Sử dụng Keras legacy
os.environ["TF_USE_LEGACY_KERAS"] = "1"
# Ẩn Python warnings
warnings.filterwarnings("ignore")
# Giảm log TensorFlow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
logging.getLogger("tensorflow").setLevel(logging.ERROR)
##########

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        neo4j_connection.connect()

        app.state.neo4j_driver = (
            neo4j_connection.get_driver()
        )

        print("Application startup successful.")

    except Exception as error:
        print(f"Neo4j connection failed: {error}")
        neo4j_connection.close()
        raise

    yield

    neo4j_connection.close()
    print("Application shutdown.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Hệ thống hỗ trợ học tập và khám phá "
        "Lịch sử Việt Nam dựa trên Knowledge Graph và GraphRAG."
    ),
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5501",
        "http://127.0.0.1:5501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(health.router)
app.include_router(events.router)
app.include_router(characters.router)
app.include_router(timeline.router)
app.include_router(graph.router)
app.include_router(sources.router)
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {
        "message": "Welcome to Tay Son GraphRAG API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }
