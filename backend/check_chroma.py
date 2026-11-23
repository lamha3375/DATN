
from app.core.chroma_connection import chroma_connection

COLLECTION_NAME = "tay_son_history"

def main():
    # Sử dụng chính cấu hình kết nối của project
    client = chroma_connection.connect()

    collection = client.get_collection(
        name=COLLECTION_NAME
    )

    print("=" * 65)
    print("THONG TIN COLLECTION CHROMADB")
    print("=" * 65)

    print("Collection name:", collection.name)
    print("Total vectors:", collection.count())
    print("Collection metadata:", collection.metadata)

    print("\n" + "=" * 65)
    print("CAC CHUNK DU LIEU MAU")
    print("=" * 65)

    result = collection.peek(
        limit=5
    )

    ids = result.get("ids", [])
    documents = result.get("documents") or []
    metadatas = result.get("metadatas") or []
    embeddings = result.get("embeddings")

    for i, chunk_id in enumerate(ids):
        print(f"\n--- CHUNK {i + 1} ---")
        print("ID:", chunk_id)

        if i < len(metadatas):
            print("Metadata:", metadatas[i])

        if i < len(documents):
            content = documents[i] or ""
            print("Content:", content[:250])

        if embeddings is not None and len(embeddings) > i:
            print(
                "Embedding dimensions:",
                len(embeddings[i])
            )

    print("\n" + "=" * 65)
    print("KIEM TRA HOAN TAT")
    print("=" * 65)


if __name__ == "__main__":
    main()
