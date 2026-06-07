from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utc_now


class HomeworkRecord(Base):
    __tablename__ = "homework_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    subject: Mapped[str] = mapped_column(String(20), nullable=False)
    homework_type: Mapped[str] = mapped_column(String(30), default="课堂作业", nullable=False)
    completion_status: Mapped[str] = mapped_column(String(20), default="待批改", nullable=False)
    accuracy_status: Mapped[str | None] = mapped_column(String(20))
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score: Mapped[int | None] = mapped_column(Integer)
    auto_comment: Mapped[str | None] = mapped_column(Text)
    teacher_remark: Mapped[str | None] = mapped_column(Text)
    recorded_by: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))
    graded_by: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))
    corrected_by: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))
    graded_at: Mapped[object | None] = mapped_column(DateTime)
    corrected_at: Mapped[object | None] = mapped_column(DateTime)
    homework_date: Mapped[object] = mapped_column(Date, nullable=False)
    completed_at: Mapped[object | None] = mapped_column(DateTime)
    created_at: Mapped[object] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class HomeworkPhoto(Base):
    __tablename__ = "homework_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey("homework_records.id", ondelete="CASCADE"), nullable=False)
    photo_id: Mapped[int] = mapped_column(ForeignKey("photos.id", ondelete="CASCADE"), nullable=False)
    step: Mapped[str] = mapped_column(String(20), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime, default=utc_now, nullable=False)

