
from typing import Optional
from pydantic import BaseModel


class EventResponse(BaseModel):
    event_id: str
    event_name: Optional[str] = None

    start_date: Optional[str] = None
    end_date: Optional[str] = None

    description: Optional[str] = None
    significance: Optional[str] = None
    result: Optional[str] = None

    people: Optional[str] = None
    location: Optional[str] = None

    event_type: Optional[str] = None
    time_precision: Optional[str] = None

    verification_status: Optional[str] = None
    scope_status: Optional[str] = None
