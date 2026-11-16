
from app.core.config import settings


class EventService:

    def __init__(self, driver):
        self.driver = driver

    def get_all_events(
        self,
        skip: int = 0,
        limit: int = 20,
        keyword: str = None
    ):
        keyword = keyword.strip() if keyword else None

        query = """
        MATCH (e:SuKien)

        WHERE $keyword IS NULL
           OR toLower(coalesce(e.event_name, ''))
                CONTAINS toLower($keyword)
           OR toLower(coalesce(e.description, ''))
                CONTAINS toLower($keyword)

        RETURN
            e.event_id AS event_id,
            e.event_name AS event_name,
            e.start_date AS start_date,
            e.end_date AS end_date,
            e.description AS description,
            e.significance AS significance,
            e.result AS result,
            e.people AS people,
            e.location AS location,
            e.event_type AS event_type,
            e.time_precision AS time_precision,
            e.verification_status AS verification_status,
            e.scope_status AS scope_status

        ORDER BY e.start_date ASC

        SKIP $skip
        LIMIT $limit
        """

        count_query = """
        MATCH (e:SuKien)

        WHERE $keyword IS NULL
           OR toLower(coalesce(e.event_name, ''))
                CONTAINS toLower($keyword)
           OR toLower(coalesce(e.description, ''))
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

    def get_event_by_id(self, event_id: str):

        query = """
        MATCH (e:SuKien {event_id: $event_id})

        RETURN
            e.event_id AS event_id,
            e.event_name AS event_name,
            e.start_date AS start_date,
            e.end_date AS end_date,
            e.description AS description,
            e.significance AS significance,
            e.result AS result,
            e.people AS people,
            e.location AS location,
            e.event_type AS event_type,
            e.time_precision AS time_precision,
            e.verification_status AS verification_status,
            e.scope_status AS scope_status

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
