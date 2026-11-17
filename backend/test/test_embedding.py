import os

os.environ["USE_TF"] = "0"
os.environ["USE_FLAX"] = "0"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from app.schemas.chunk import TextChunk
from app.services.embedding_service import EmbeddingService


service = EmbeddingService()

chunks = [
    TextChunk(
        chunk_id="CHUNK_001",
        document_id="lich_su_tay_son_test",
        document_name="lich_su_tay_son.pdf",
        source_id=None,
        content_hash="test-content-hash",
        token_count=24,
        page_number=1,
        content="Năm 1771, phong trào khởi nghĩa Tây Sơn bùng nổ tại Bình Định.",
        character_count=65,
        chunk_index=1
    ),
    TextChunk(
        chunk_id="CHUNK_002",
        document_id="lich_su_tay_son_test",
        document_name="lich_su_tay_son.pdf",
        source_id=None,
        content_hash="test-content-hash",
        token_count=27,
        page_number=2,
        content="Nguyễn Huệ là một trong những lãnh tụ tiêu biểu của phong trào Tây Sơn.",
        character_count=75,
        chunk_index=2
    )
]

result = service.embed_chunks(chunks)

print("Model:", result.model_name)
print("Total chunks:", result.total_chunks)
print("Dimensions:", result.dimensions)

for item in result.embeddings:
    print("\nChunk ID:", item.chunk_id)
    print("Vector dimensions:", len(item.embedding))
    print("First 5 values:", item.embedding[:5])