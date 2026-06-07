from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utc_now


class TeacherRemark(Base):
    __tablename__ = "teacher_remarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    record_date: Mapped[object] = mapped_column(Date, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    mood_tag: Mapped[str | None] = mapped_column(String(20))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))
    created_at: Mapped[object] = mapped_column(DateTime, default=utc_now, nullable=False)


class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    fee_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[object] = mapped_column(Numeric(10, 2), nullable=False)
    period_start: Mapped[object | None] = mapped_column(Date)
    period_end: Mapped[object | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="未缴", nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(30))
    remark: Mapped[str | None] = mapped_column(Text)
    paid_at: Mapped[object | None] = mapped_column(DateTime)
    recorded_by: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))
    created_at: Mapped[object] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class ParentBinding(Base):
    __tablename__ = "parent_bindings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("parents.id", ondelete="CASCADE"), nullable=False)
    wechat_openid: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    bind_at: Mapped[object] = mapped_column(DateTime, default=utc_now, nullable=False)
    last_login_at: Mapped[object | None] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
