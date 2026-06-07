from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.responses import abort
from app.core.security import decode_token
from app.db.session import get_db
from app.models import Parent, Teacher


def get_current_teacher(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Teacher:
    if not authorization or not authorization.startswith("Bearer "):
        abort("未登录", code=40100, status_code=401)

    payload = decode_token(authorization.removeprefix("Bearer ").strip())
    if not payload or "teacher_id" not in payload:
        abort("登录已失效", code=40101, status_code=401)

    teacher = db.get(Teacher, int(payload["teacher_id"]))
    if teacher is None or not teacher.is_active:
        abort("账号不可用", code=40102, status_code=401)
    return teacher


def get_current_admin(
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Teacher:
    if current_teacher.role != "admin":
        abort("需要管理员权限", code=40300, status_code=403)
    return current_teacher


def get_current_parent(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Parent:
    if not authorization or not authorization.startswith("Bearer "):
        abort("未登录", code=40100, status_code=401)

    payload = decode_token(authorization.removeprefix("Bearer ").strip())
    if not payload or "parent_id" not in payload:
        abort("登录已失效", code=40101, status_code=401)

    parent = db.get(Parent, int(payload["parent_id"]))
    if parent is None:
        abort("账号不可用", code=40102, status_code=401)
    return parent
