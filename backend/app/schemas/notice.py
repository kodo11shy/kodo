from datetime import date

from pydantic import BaseModel, Field


class NoticeCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    notice_type: str = "通知"
    is_pinned: bool = False
    display_start: date | None = None
    display_end: date | None = None


class NoticeUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    content: str | None = None
    notice_type: str | None = None
    is_pinned: bool | None = None
    is_active: bool | None = None
    display_start: date | None = None
    display_end: date | None = None

