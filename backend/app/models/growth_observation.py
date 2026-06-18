from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utc_now


class GrowthObservationDraft(Base):
    __tablename__ = "growth_observation_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    period_start: Mapped[object] = mapped_column(Date, nullable=False)
    period_end: Mapped[object] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    suggested_content: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_tags: Mapped[str | None] = mapped_column(Text)
    source_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))
    reviewed_at: Mapped[object | None] = mapped_column(DateTime)
    created_at: Mapped[object] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class GrowthObservation(Base):
    __tablename__ = "growth_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    observation_date: Mapped[object] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    dimension_tags: Mapped[str | None] = mapped_column(Text)
    parent_visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_draft_id: Mapped[int | None] = mapped_column(ForeignKey("growth_observation_drafts.id"))
    status: Mapped[str] = mapped_column(String(20), default="approved", nullable=False)
    confirmed_by: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))
    created_at: Mapped[object] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class GrowthObservationSource(Base):
    __tablename__ = "growth_observation_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    source_date: Mapped[object] = mapped_column(Date, nullable=False)
    title: Mapped[str | None] = mapped_column(String(100))
    summary: Mapped[str | None] = mapped_column(Text)
    draft_id: Mapped[int | None] = mapped_column(ForeignKey("growth_observation_drafts.id", ondelete="CASCADE"))
    observation_id: Mapped[int | None] = mapped_column(ForeignKey("growth_observations.id", ondelete="CASCADE"))
    created_at: Mapped[object] = mapped_column(DateTime, default=utc_now, nullable=False)
