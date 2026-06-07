from datetime import date

from pydantic import BaseModel, Field


class RemarkCreateRequest(BaseModel):
    student_id: int
    record_date: date | None = None
    content: str = Field(min_length=1)
    mood_tag: str | None = None

