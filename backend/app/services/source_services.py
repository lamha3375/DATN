
from app.core.config import settings


class SourceService:
    def __init__(self, driver):
        self.driver = driver

    def get_all_sources(
        self,
        skip: int = 0,
        limit: int = 20,
        keyword: str = None
    ):
        keyword = keyword.strip() if keyword else None

        # Tìm kiếm trên tất cả thuộc tính của node
        query = """
        MATCH (s:NguonTaiLieu)
        WITH s, properties(s) AS props
        WHERE $keyword IS NULL
           OR any(
               key IN keys(props)
               WHERE toLower(toString(props[key]))
                     CONTAINS toLower($keyword)
           )
        RETURN props AS source
        ORDER BY coalesce(
            s.source_name,
            s.title,
            s.name,
            s.source_id
        ) ASC
        SKIP $skip
        LIMIT $limit
        """

        # Đếm tổng số nguồn tài liệu phù hợp
        count_query = """
        MATCH (s:NguonTaiLieu)
        WITH s, properties(s) AS props
        WHERE $keyword IS NULL
           OR any(
               key IN keys(props)
               WHERE toLower(toString(props[key]))
                     CONTAINS toLower($keyword)
           )
        RETURN count(s) AS total
        """

        with self.driver.session(
            database=settings.NEO4J_DATABASE
        ) as session:

            total_result = session.run(
                count_query,
                keyword=keyword
            )

            total_record = total_result.single()
            total = total_record["total"] if total_record else 0

            result = session.run(
                query,
                skip=skip,
                limit=limit,
                keyword=keyword
            )

            sources = [
                record["source"]
                for record in result
            ]

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": sources
        }

    def get_source_by_id(self, source_id: str):
        query = """
        MATCH (s:NguonTaiLieu)
        WHERE toString(s.source_id) = $source_id
           OR toString(s.document_id) = $source_id
           OR toString(s.id) = $source_id
        RETURN properties(s) AS source
        LIMIT 1
        """

        with self.driver.session(
            database=settings.NEO4J_DATABASE
        ) as session:

            result = session.run(
                query,
                source_id=source_id
            )

            record = result.single()

            if record is None:
                return None

            return record["source"]
