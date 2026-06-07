from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.homework_rules import HOMEWORK_SUBJECTS_JSON
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import engine
from app.models import SystemConfig, Teacher


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_compatible_schema()


def _add_column_if_missing(table_name: str, column_name: str, ddl: str) -> None:
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns(table_name)}
    if column_name in columns:
        return
    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))


def ensure_compatible_schema() -> None:
    inspector = inspect(engine)
    datetime_type = "TIMESTAMP" if engine.dialect.name == "postgresql" else "DATETIME"

    if "teachers" in inspector.get_table_names():
        _add_column_if_missing("teachers", "wechat_openid", "wechat_openid VARCHAR(100)")
        _add_column_if_missing("teachers", "updated_at", f"updated_at {datetime_type}")
        with engine.begin() as connection:
            connection.execute(text("UPDATE teachers SET updated_at = created_at WHERE updated_at IS NULL"))
        _add_column_if_missing("teachers", "subject", "subject VARCHAR(20)")

    if "homework_records" in inspector.get_table_names():
        _add_column_if_missing("homework_records", "graded_by", "graded_by INTEGER REFERENCES teachers(id)")
        _add_column_if_missing("homework_records", "corrected_by", "corrected_by INTEGER REFERENCES teachers(id)")
        _add_column_if_missing("homework_records", "graded_at", f"graded_at {datetime_type}")
        _add_column_if_missing("homework_records", "corrected_at", f"corrected_at {datetime_type}")


def seed_default_teacher(db: Session) -> None:
    exists = db.execute(select(Teacher.id).limit(1)).scalar_one_or_none()
    if exists is not None:
        return

    teacher = Teacher(
        name=settings.default_teacher_name,
        role="admin",
        login_password=hash_password(settings.default_teacher_password),
    )
    db.add(teacher)
    db.commit()


def seed_default_config(db: Session) -> None:
    defaults = [
        ("tuition_fee", "2800", "每月托管费"),
        ("meal_fee", "500", "每月餐费"),
        ("material_fee", "200", "每学期材料费"),
        ("school_name", "智慧托班", "托班名称"),
        ("welcome_message", "用心陪伴每一个孩子", "欢迎语"),
        ("contact_wechat", "", "联系微信号"),
        ("contact_phone", "", "联系电话"),
        ("homework_subjects", HOMEWORK_SUBJECTS_JSON, "作业科目列表（固定：语文、数学）"),
        ("homework_types", '["课堂作业","家庭作业","练习题","背诵","其他"]', "作业类型列表（JSON 数组）"),
    ]
    existing_keys = set(db.execute(select(SystemConfig.config_key)).scalars().all())
    for key, value, description in defaults:
        if key in existing_keys:
            continue
        db.add(SystemConfig(config_key=key, config_value=value, description=description))
    subject_config = db.execute(
        select(SystemConfig).where(SystemConfig.config_key == "homework_subjects")
    ).scalar_one_or_none()
    if subject_config is not None:
        subject_config.config_value = HOMEWORK_SUBJECTS_JSON
        subject_config.description = "作业科目列表（固定：语文、数学）"
    db.commit()
