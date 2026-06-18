from datetime import date

from pydantic import BaseModel, Field


class GrowthObservationDraftCreateRequest(BaseModel):
    student_id: int
    start_date: date | None = None
    end_date: date | None = None
    days: int = Field(default=7, ge=1, le=90)
    source_types: list[str] = Field(default_factory=list)
    title: str | None = Field(default=None, max_length=100)


class GrowthObservationConfirmRequest(BaseModel):
    draft_id: int | None = None
    student_id: int
    observation_date: date | None = None
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    dimension_tags: list[str] = Field(default_factory=list)
    parent_visible: bool = False
    source_refs: list[dict] = Field(default_factory=list)


class GrowthObservationUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=100)
    content: str | None = None
    dimension_tags: list[str] | None = None
    parent_visible: bool | None = None
    status: str | None = Field(default=None, pattern=r"^(approved|published|hidden|rejected)$")


class GrowthObservationDraftReviewRequest(BaseModel):
    status: str = Field(pattern=r"^(pending|approved|rejected)$")
