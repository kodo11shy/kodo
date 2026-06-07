from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utc_now


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint("student_id", "date", name="uq_attendance_student_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    checkin_time: Mapped[object] = mapped_column(DateTime, nullable=False)
    checkout_time: Mapped[object | None] = mapped_column(DateTime)
    pickup_person: Mapped[str | None] = mapped_column(String(50))
    checkin_by: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))
    checkout_by: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))
    is_makeup: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    makeup_reason: Mapped[str | None] = mapped_column(Text)
    date: Mapped[object] = mapped_column(Date, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime, default=utc_now, nullable=False)

