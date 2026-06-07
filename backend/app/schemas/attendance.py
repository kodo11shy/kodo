from datetime import datetime

from pydantic import BaseModel, Field


class CheckinRequest(BaseModel):
    student_id: int
    timestamp: datetime | None = None


class CheckoutRequest(BaseModel):
    student_id: int
    timestamp: datetime | None = None
    pickup_person: str = Field(min_length=1, max_length=50)


class MakeupCheckinRequest(BaseModel):
    student_id: int
    timestamp: datetime
    reason: str = Field(min_length=1)

