
from typing import Optional

from app.core.config import settings


class EventService:

    def __init__(self, driver):
        self.driver = driver

    # =====================================================
    # GET ALL EVENTS
    # =====================================================

    def get_all_events(
        self,
        skip: int = 0,
        limit: int = 20,
        keyword: Optional[str] = None
    ):

        keyword = keyword.strip() if keyword else None

        query = """
        MATCH (e:Event)

        WHERE $keyword IS NULL
           OR toLower(coalesce(e.name, ''))
                CONTAINS toLower($keyword)
           OR toLower(coalesce(e.description, ''))
                CONTAINS toLower($keyword)
           OR toLower(coalesce(e.significance, ''))
                CONTAINS toLower($keyword)
           OR toLower(coalesce(e.result, ''))
                CONTAINS toLower($keyword)
           OR toLower(coalesce(e.eventType, ''))
                CONTAINS toLower($keyword)

        RETURN
            e.id AS event_id,
            e.name AS event_name,
            e.startDate AS start_date,
            e.endDate AS end_date,
            e.period AS period,
            e.module AS module,
            e.description AS description,
            e.significance AS significance,
            e.result AS result,
            e.eventType AS event_type,
            e.tags AS tags,
            e.rag_text AS rag_text

        ORDER BY e.startDate ASC

        SKIP $skip
        LIMIT $limit
        """

        count_query = """
        MATCH (e:Event)

        WHERE $keyword IS NULL
           OR toLower(coalesce(e.name, ''))
                CONTAINS toLower($keyword)
           OR toLower(coalesce(e.description, ''))
                CONTAINS toLower($keyword)
           OR toLower(coalesce(e.significance, ''))
                CONTAINS toLower($keyword)
           OR toLower(coalesce(e.result, ''))
                CONTAINS toLower($keyword)
           OR toLower(coalesce(e.eventType, ''))
                CONTAINS toLower($keyword)

        RETURN count(e) AS total
        """

        with self.driver.session(
            database=settings.NEO4J_DATABASE
        ) as session:

            total_result = session.run(
                count_query,
                keyword=keyword
            )

            total = total_result.single()["total"]

            result = session.run(
                query,
                skip=skip,
                limit=limit,
                keyword=keyword
            )

            events = [
                record.data()
                for record in result
            ]

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": events
        }

    # =====================================================
    # GET EVENT BY ID
    # =====================================================

    def get_event_by_id(self, event_id: str):

        query = """
        MATCH (e:Event {id: $event_id})

        RETURN
            e.id AS event_id,
            e.name AS event_name,
            e.startDate AS start_date,
            e.endDate AS end_date,
            e.period AS period,
            e.module AS module,
            e.description AS description,
            e.significance AS significance,
            e.result AS result,
            e.eventType AS event_type,
            e.tags AS tags,
            e.rag_text AS rag_text

        LIMIT 1
        """

        with self.driver.session(
            database=settings.NEO4J_DATABASE
        ) as session:

            result = session.run(
                query,
                event_id=event_id
            )

            record = result.single()

            if record is None:
                return None

            return record.data()
