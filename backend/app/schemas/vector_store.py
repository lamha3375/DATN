from pydantic import BaseModel, Field


class VectorStoreResponse(BaseModel):
    collection_name: str = Field(..., min_length=1)

    document_name: str = Field(..., min_length=1)

    total_vectors: int = Field(..., ge=0)

    dimensions: int = Field(..., gt=0)

    status: str