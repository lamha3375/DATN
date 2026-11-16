
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
        keyword = keyword.strip() if keyword else None

        # Tìm kiếm theo các thuộc tính nhân vật
        where_clause = """
        WHERE $keyword IS NULL
           OR toLower(coalesce(c.name, ''))
                CONTAINS toLower($keyword)
           OR toLower(toString(coalesce(c.role, '')))
                CONTAINS toLower($keyword)
           OR toLower(toString(coalesce(c.faction, '')))
                CONTAINS toLower($keyword)
           OR toLower(toString(coalesce(c.historical_notes, '')))
                CONTAINS toLower($keyword)
           OR any(
                alias IN coalesce(c.aliases, [])
                WHERE toLower(alias)
                      CONTAINS toLower($keyword)
           )
        """

        # Đếm tổng số nhân vật
        count_query = f"""
        MATCH (c:NhanVat)
        {where_clause}
        RETURN count(c) AS total
        """

        # Lấy danh sách nhân vật
        data_query = f"""
        MATCH (c:NhanVat)
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

            total = total_record["total"] if total_record else 0

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

        query = """
        MATCH (c:NhanVat)
        WHERE toString(c.person_id) = $character_id
           OR toString(c.id) = $character_id
           OR toString(c.character_id) = $character_id
        RETURN properties(c) AS character
        LIMIT 1
        """

        with self.driver.session(
            database=settings.NEO4J_DATABASE
        ) as session:

            record = session.run(
                query,
                character_id=character_id
            ).single()

            if record is None:
                return None

            return record["character"]
