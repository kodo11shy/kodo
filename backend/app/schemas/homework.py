from datetime import date

from pydantic import BaseModel, Field


class HomeworkCreateRequest(BaseModel):
    student_id: int
    subject: str = Field(min_length=1, max_length=20)
    homework_type: str = "课堂作业"
    photo_ids: list[int] = Field(min_length=1, max_length=9)
    remark: str | None = None
    homework_date: date | None = None


class HomeworkGradeRequest(BaseModel):
    photo_ids: list[int] = Field(min_length=1, max_length=9)
    accuracy_status: str | None = None
    error_count: int = Field(default=0, ge=0)
    score: int = Field(ge=1, le=10)
    remark: str | None = None


class HomeworkCorrectRequest(BaseModel):
    photo_ids: list[int] = Field(min_length=1, max_length=9)
    remark: str | None = None

