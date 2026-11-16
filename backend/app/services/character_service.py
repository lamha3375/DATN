
from app.core.config import settings


class CharacterService:
    def __init__(self, driver):
        self.driver = driver

    def get_all_characters(
        self,
        skip: int = 0,
        limit: int = 20,
        keyword: str = None
    ):
        skip = max(0, skip)
        limit = max(1, limit)

        keyword = (
            keyword.strip()
            if keyword and keyword.strip()
            else None
        )

        where_clause = """
        WHERE $keyword IS NULL
           OR toLower(coalesce(c.id, '')) CONTAINS toLower($keyword)
           OR toLower(coalesce(c.name, '')) CONTAINS toLower($keyword)
           OR toLower(coalesce(c.alias, '')) CONTAINS toLower($keyword)
           OR toLower(coalesce(c.role, '')) CONTAINS toLower($keyword)
           OR toLower(coalesce(c.dynasty, '')) CONTAINS toLower($keyword)
           OR toLower(coalesce(c.bio, '')) CONTAINS toLower($keyword)
           OR toLower(coalesce(c.period, '')) CONTAINS toLower($keyword)
           OR toLower(coalesce(c.module, '')) CONTAINS toLower($keyword)
        """

        count_query = f"""
        MATCH (c:Person)
        {where_clause}
        RETURN count(c) AS total
        """

        data_query = f"""
        MATCH (c:Person)
        {where_clause}
        RETURN properties(c) AS character
        ORDER BY toLower(coalesce(c.name, '')) ASC
        SKIP $skip
        LIMIT $limit
        """

        with self.driver.session(
            database=settings.NEO4J_DATABASE
        ) as session:

            total_record = session.run(
                count_query,
                keyword=keyword
            ).single()

            total = (
                total_record["total"]
                if total_record else 0
            )

            result = session.run(
                data_query,
                keyword=keyword,
                skip=skip,
                limit=limit
            )

            characters = [
                record["character"]
                for record in result
            ]

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": characters
        }

    def get_character_by_id(self, character_id: str):
        if not character_id:
            return None

        query = """
        MATCH (c:Person {id: $character_id})
        RETURN properties(c) AS character
        LIMIT 1
        """

        with self.driver.session(
            database=settings.NEO4J_DATABASE
        ) as session:

            record = session.run(
                query,
                character_id=character_id.strip()
            ).single()

            if record is None:
                return None

            return record["character"]
