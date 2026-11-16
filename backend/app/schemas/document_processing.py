from pydantic import BaseModel, Field


class DocumentProcessingResponse(BaseModel):
    document_name: str

    total_pages: int = Field(..., ge=0)
    extracted_pages: int = Field(..., ge=0)

    total_chunks: int = Field(..., ge=0)
    previously_stored: int = Field(..., ge=0)
    newly_stored: int = Field(..., ge=0)

    total_stored: int = Field(..., ge=0)

    status: str