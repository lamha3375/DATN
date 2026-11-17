
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

        query = """
        MATCH (s:Source)
        WITH s, properties(s) AS props
        WHERE $keyword IS NULL
           OR any(
               key IN keys(props)
               WHERE toLower(toString(props[key]))
                     CONTAINS toLower($keyword)
           )
        RETURN props AS source
        ORDER BY coalesce(
            s.name,
            s.id,
            s.file
        ) ASC
        SKIP $skip
        LIMIT $limit
        """

        count_query = """
        MATCH (s:Source)
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

            total_record = session.run(
                count_query,
                keyword=keyword
            ).single()

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
        MATCH (s:Source)
        WHERE toString(s.id) = $source_id
        RETURN properties(s) AS source
        LIMIT 1
        """

        with self.driver.session(
            database=settings.NEO4J_DATABASE
        ) as session:

            record = session.run(
                query,
                source_id=source_id
            ).single()

            if record is None:
                return None

            return record["source"]
