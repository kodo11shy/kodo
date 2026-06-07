"""
Reset the development database to a clean new-term state.

Keeps:
- teachers
- students
- parents
- student-parent links
- authorized pickups
- student health records
- system config

Clears:
- attendance
- homework
- photos and photo links
- meals
- teacher remarks
- payment records
- notices
- parent WeChat bindings/login state

Usage:
    cd backend
    python scripts/reset-new-term.py --apply
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))
load_dotenv(BACKEND_ROOT / ".env")

from sqlalchemy import select

from app.core.homework_rules import HOMEWORK_SUBJECTS_JSON, is_allowed_homework_subject
from app.core.security import hash_password
from app.db.init_db import create_tables, seed_default_config, seed_default_teacher
from app.db.session import SessionLocal
from app.models import (
    AttendanceRecord,
    HomeworkPhoto,
    HomeworkRecord,
    MealPhoto,
    MealRecord,
    MealStudentNote,
    Notice,
    Parent,
    ParentBinding,
    PaymentRecord,
    Photo,
    PhotoStudent,
    Student,
    StudentParent,
    SystemConfig,
    Teacher,
    TeacherRemark,
)


RUNTIME_MODELS = [
    HomeworkPhoto,
    MealPhoto,
    MealStudentNote,
    PhotoStudent,
    AttendanceRecord,
    HomeworkRecord,
    MealRecord,
    TeacherRemark,
    PaymentRecord,
    Notice,
    ParentBinding,
    Photo,
]


def _backup_sqlite_db() -> Path | None:
    db_path = BACKEND_ROOT / "tuoban_dev.db"
    if not db_path.exists():
        return None

    backup_dir = BACKEND_ROOT / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"tuoban_dev.before-new-term.{stamp}.db"
    shutil.copy2(db_path, backup_path)
    return backup_path


def _count_rows(db) -> dict[str, int]:
    models = [
        Teacher,
        Student,
        Parent,
        StudentParent,
        AttendanceRecord,
        HomeworkRecord,
        Photo,
        MealRecord,
        TeacherRemark,
        PaymentRecord,
        Notice,
        ParentBinding,
    ]
    return {model.__tablename__: db.query(model).count() for model in models}


def _ensure_default_admin(db) -> None:
    seed_default_teacher(db)
    admin = db.execute(select(Teacher).where(Teacher.role == "admin").order_by(Teacher.id)).scalars().first()
    if admin is None:
        db.add(
            Teacher(
                name="管理员",
                role="admin",
                login_password=hash_password("123456"),
                subject=None,
                is_active=True,
            )
        )


def _normalize_kept_data(db) -> None:
    _ensure_default_admin(db)
    seed_default_config(db)

    subject_config = db.execute(
        select(SystemConfig).where(SystemConfig.config_key == "homework_subjects")
    ).scalar_one_or_none()
    if subject_config is not None:
        subject_config.config_value = HOMEWORK_SUBJECTS_JSON
        subject_config.description = "作业科目列表（固定：语文、数学）"

    for teacher in db.query(Teacher).filter(Teacher.name.like("temp %")).all():
        db.delete(teacher)
    db.flush()

    for teacher in db.query(Teacher).all():
        teacher.is_active = True
        if teacher.role == "admin":
            teacher.subject = None
        elif teacher.subject and not is_allowed_homework_subject(teacher.subject):
            teacher.subject = None

    active_teachers = db.query(Teacher).filter(Teacher.role == "teacher").order_by(Teacher.id).all()
    subjects_in_use = {teacher.subject for teacher in active_teachers if teacher.subject}
    unassigned_teachers = [teacher for teacher in active_teachers if not teacher.subject]

    if "语文" not in subjects_in_use:
        if unassigned_teachers:
            unassigned_teachers.pop(0).subject = "语文"
        else:
            db.add(
                Teacher(
                    name="语文老师",
                    role="teacher",
                    subject="语文",
                    login_password=hash_password("123456"),
                    is_active=True,
                )
            )

    subjects_in_use = {teacher.subject for teacher in db.query(Teacher).filter(Teacher.role == "teacher").all() if teacher.subject}
    if "数学" not in subjects_in_use:
        if unassigned_teachers:
            unassigned_teachers.pop(0).subject = "数学"
        else:
            db.add(
                Teacher(
                    name="数学老师",
                    role="teacher",
                    subject="数学",
                    login_password=hash_password("123456"),
                    is_active=True,
                )
            )

    for student in db.query(Student).all():
        student.status = "在读"
        student.is_active = True

    for link in db.query(StudentParent).all():
        link.is_authorized = True

    for parent in db.query(Parent).all():
        parent.wechat_openid = None


def reset_new_term(apply: bool) -> None:
    create_tables()

    with SessionLocal() as db:
        before = _count_rows(db)
        print("[BEFORE]")
        for table, count in before.items():
            print(f"  {table}: {count}")

        if not apply:
            print("\n[DRY-RUN] No data changed. Re-run with --apply to reset.")
            return

        backup_path = _backup_sqlite_db()
        if backup_path is not None:
            print(f"\n[BACKUP] {backup_path}")

        for model in RUNTIME_MODELS:
            db.query(model).delete(synchronize_session=False)

        _normalize_kept_data(db)
        db.commit()

        after = _count_rows(db)
        print("\n[AFTER]")
        for table, count in after.items():
            print(f"  {table}: {count}")

        print("\n[OK] New-term state is ready.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Actually reset runtime data.")
    args = parser.parse_args()
    reset_new_term(apply=args.apply)


if __name__ == "__main__":
    main()
