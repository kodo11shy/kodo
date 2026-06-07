from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utc_now


class MealRecord(Base):
    __tablename__ = "meal_records"
    __table_args__ = (UniqueConstraint("meal_date", "meal_type", name="uq_meal_date_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    meal_date: Mapped[object] = mapped_column(Date, nullable=False)
    meal_type: Mapped[str] = mapped_column(String(20), default="午餐", nullable=False)
    menu_text: Mapped[str | None] = mapped_column(Text)
    ingredient_notes: Mapped[str | None] = mapped_column(Text)
    cooking_notes: Mapped[str | None] = mapped_column(Text)
    hygiene_notes: Mapped[str | None] = mapped_column(Text)
    overall_remark: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))
    created_at: Mapped[object] = mapped_column(DateTime, default=utc_now, nullable=False)


class MealPhoto(Base):
    __tablename__ = "meal_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    meal_id: Mapped[int] = mapped_column(ForeignKey("meal_records.id", ondelete="CASCADE"), nullable=False)
    photo_id: Mapped[int] = mapped_column(ForeignKey("photos.id", ondelete="CASCADE"), nullable=False)
    step: Mapped[str | None] = mapped_column(String(20))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime, default=utc_now, nullable=False)


class MealStudentNote(Base):
    __tablename__ = "meal_student_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    meal_id: Mapped[int] = mapped_column(ForeignKey("meal_records.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    remark: Mapped[str] = mapped_column(Text, nullable=False)
    photo_id: Mapped[int | None] = mapped_column(ForeignKey("photos.id"))
    created_at: Mapped[object] = mapped_column(DateTime, default=utc_now, nullable=False)

