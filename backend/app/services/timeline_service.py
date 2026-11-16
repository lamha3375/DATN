
from typing import Any, Dict, List, Optional

from app.core.config import settings


class TimelineService:

    def __init__(self, driver):
        self.driver = driver

    @staticmethod
    def extract_year(start_date: Any) -> Optional[int]:
        """
        Trích năm từ các định dạng:
        1771
        1773-08
        1785-01-05
        """
        if start_date is None:
            return None

        date_text = str(start_date).strip()

        if len(date_text) >= 4 and date_text[:4].isdigit():
            return int(date_text[:4])

        return None

    def get_timeline(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        keyword: Optional[str] = None,
        limit: int = 500
    ) -> Dict[str, Any]:

        # Kiểm tra khoảng năm
        if (
            start_year is not None
            and end_year is not None
            and start_year > end_year
        ):
            raise ValueError(
                "Năm bắt đầu không được lớn hơn năm kết thúc."
            )

        if limit < 1:
            raise ValueError("Limit phải lớn hơn 0.")

        keyword = keyword.strip() if keyword else None

        query = """
        MATCH (e:Event)

        WITH e,
             properties(e) AS props,
             toInteger(substring(toString(e.startDate), 0, 4))
             AS event_year

        WHERE e.startDate IS NOT NULL
          AND event_year IS NOT NULL

          AND ($start_year IS NULL
               OR event_year >= $start_year)

          AND ($end_year IS NULL
               OR event_year <= $end_year)

          AND (
              $keyword IS NULL
              OR any(
                  value IN [
                      e.name,
                      e.period,
                      e.eventType,
                      e.description,
                      e.result,
                      e.significance,
                      e.tags
                  ]
                  WHERE value IS NOT NULL
                    AND toLower(toString(value))
                        CONTAINS toLower($keyword)
              )
          )

        RETURN props AS event,
               event_year AS year

        ORDER BY event_year ASC,
                 toString(e.startDate) ASC

        LIMIT $limit
        """

        with self.driver.session(
            database=settings.NEO4J_DATABASE
        ) as session:

            result = session.run(
                query,
                start_year=start_year,
                end_year=end_year,
                keyword=keyword,
                limit=limit
            )

            events = [
                {
                    "year": record["year"],
                    "event": record["event"]
                }
                for record in result
            ]

        # Nhóm sự kiện theo năm
        timeline: Dict[int, List[Dict[str, Any]]] = {}

        for item in events:
            year = item["year"]
            event = item["event"]

            timeline.setdefault(year, []).append(event)

        # Tạo dữ liệu Timeline
        timeline_data = [
            {
                "year": year,
                "events": timeline[year]
            }
            for year in sorted(timeline.keys())
        ]

        return {
            "total": len(events),
            "start_year": start_year,
            "end_year": end_year,
            "data": timeline_data
        }
