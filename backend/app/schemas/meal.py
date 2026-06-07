from datetime import date

from pydantic import BaseModel, Field


class MealCreateRequest(BaseModel):
    meal_date: date | None = None
    meal_type: str = "午餐"
    menu_text: str | None = None
    ingredient_notes: str | None = None
    cooking_notes: str | None = None
    hygiene_notes: str | None = None
    overall_remark: str | None = None
    photo_ids: dict[str, list[int]] = Field(default_factory=dict)


class MealStudentNoteRequest(BaseModel):
    student_id: int
    remark: str = Field(min_length=1)
    photo_id: int | None = None

