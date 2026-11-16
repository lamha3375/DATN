
from neo4j import GraphDatabase
from app.core.config import settings


class Neo4jConnection:

    def __init__(self):
        self.driver = None

    def connect(self):
        """Khởi tạo kết nối Neo4j."""

        if self.driver is not None:
            return

        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(
                settings.NEO4J_USERNAME,
                settings.NEO4J_PASSWORD
            )
        )

        try:
            driver.verify_connectivity()
            self.driver = driver
            print("Neo4j connection established successfully.")

        except Exception:
            driver.close()
            raise

    def close(self):
        """Đóng kết nối Neo4j."""

        if self.driver is not None:
            self.driver.close()
            self.driver = None
            print("Neo4j connection closed.")

    def get_driver(self):
        if self.driver is None:
            raise RuntimeError(
                "Neo4j chưa được kết nối. Hãy gọi connect() trước."
            )

        return self.driver

    def check_connection(self):
        if self.driver is None:
            return False

        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False


neo4j_connection = Neo4jConnection()
