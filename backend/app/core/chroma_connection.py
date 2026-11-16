import chromadb
from pathlib import Path


class ChromaConnection:
    def __init__(self):
        self.client = None

    def connect(self):
        if self.client is None:
            persist_directory = Path("data/chroma")
            persist_directory.mkdir(parents=True, exist_ok=True)

            self.client = chromadb.PersistentClient(
                path=str(persist_directory)
            )

        return self.client


chroma_connection = ChromaConnection()