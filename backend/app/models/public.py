from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utc_now


class Notice(Base):
    __tablename__ = "notices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    notice_type: Mapped[str] = mapped_column(String(30), default="通知", nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_start: Mapped[object | None] = mapped_column(Date)
    display_end: Mapped[object | None] = mapped_column(Date)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))
    created_at: Mapped[object] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class SystemConfig(Base):
    __tablename__ = "system_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    config_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    config_value: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[object] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

