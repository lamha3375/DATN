
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    event_id: Optional[str] = None
    event_name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    time_precision: Optional[str] = None
    event_type: Optional[str] = None
    people: Any = None
    location: Any = None
    description: Optional[str] = None
    significance: Optional[str] = None
    result: Optional[str] = None
    verification_status: Optional[str] = None


class TimelineResponse(BaseModel):
    total: int
    start_date: str
    end_date: str
    events: List[TimelineEvent] = Field(default_factory=list)
