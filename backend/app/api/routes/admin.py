import secrets
import string

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.datetime import now_utc_naive
from app.core.homework_rules import is_allowed_homework_subject
from app.core.responses import fail, ok
from app.core.security import hash_password
from app.db.session import get_db
from app.models import Parent, ParentBinding, Student, StudentParent, Teacher
from app.schemas.admin import TeacherCreateRequest, TeacherResetPasswordRequest, TeacherUpdateRequest

router = APIRouter(prefix="/admin", tags=["admin"])


def _teacher_out(teacher: Teacher) -> dict:
    return {
        "id": teacher.id,
        "name": teacher.name,
        "phone": teacher.phone,
        "role": teacher.role,
        "subject": teacher.subject,
        "is_active": teacher.is_active,
        "wechat_bound": bool(teacher.wechat_openid),
        "wechat_openid": teacher.wechat_openid,
        "created_at": teacher.created_at.isoformat() if teacher.created_at else None,
        "updated_at": teacher.updated_at.isoformat() if teacher.updated_at else None,
    }


def _temp_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _teacher_openid_conflict(db: Session, openid: str, teacher_id: int | None = None) -> bool:
    query = select(Teacher).where(Teacher.wechat_openid == openid)
    if teacher_id is not None:
        query = query.where(Teacher.id != teacher_id)
    return db.execute(query).scalar_one_or_none() is not None


def _normalize_teacher_subject(subject: str | None):
    if subject in ("", "不限（管理员）"):
        return None
    return subject


def _validate_teacher_subject(subject: str | None):
    subject = _normalize_teacher_subject(subject)
    if subject is not None and not is_allowed_homework_subject(subject):
        return None, fail("老师学科只能是语文或数学", code=40008, status_code=400)
    return subject, None


@router.get("/teachers")
def list_teachers(
    db: Session = Depends(get_db),
    current_admin: Teacher = Depends(get_current_admin),
):
    teachers = db.execute(select(Teacher).order_by(Teacher.id)).scalars().all()
    return ok({"teachers": [_teacher_out(teacher) for teacher in teachers]})


@router.post("/teachers")
def create_teacher(
    payload: TeacherCreateRequest,
    db: Session = Depends(get_db),
    current_admin: Teacher = Depends(get_current_admin),
):
    if payload.wechat_openid and _teacher_openid_conflict(db, payload.wechat_openid):
        return fail("该微信已绑定其他老师", code=40006, status_code=400)

    subject, error = _validate_teacher_subject(payload.subject)
    if error is not None:
        return error

    teacher = Teacher(
        name=payload.name,
        phone=payload.phone,
        role=payload.role,
        subject=subject,
        wechat_openid=payload.wechat_openid,
        login_password=hash_password(payload.password),
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return ok({"teacher": _teacher_out(teacher)})


@router.put("/teachers/{teacher_id}")
def update_teacher(
    teacher_id: int,
    payload: TeacherUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: Teacher = Depends(get_current_admin),
):
    teacher = db.get(Teacher, teacher_id)
    if teacher is None:
        return fail("老师不存在", code=40403, status_code=404)

    values = payload.model_dump(exclude_unset=True)
    if "subject" in values:
        subject, error = _validate_teacher_subject(values["subject"])
        if error is not None:
            return error
        values["subject"] = subject

    if "wechat_openid" in values and values["wechat_openid"]:
        if _teacher_openid_conflict(db, values["wechat_openid"], teacher_id=teacher.id):
            return fail("该微信已绑定其他老师", code=40006, status_code=400)

    for key, value in values.items():
        setattr(teacher, key, value)
    teacher.updated_at = now_utc_naive()
    db.commit()
    db.refresh(teacher)
    return ok({"teacher": _teacher_out(teacher)})


@router.post("/teachers/{teacher_id}/reset-password")
def reset_teacher_password(
    teacher_id: int,
    payload: TeacherResetPasswordRequest,
    db: Session = Depends(get_db),
    current_admin: Teacher = Depends(get_current_admin),
):
    teacher = db.get(Teacher, teacher_id)
    if teacher is None:
        return fail("老师不存在", code=40403, status_code=404)

    new_password = payload.password or _temp_password()
    teacher.login_password = hash_password(new_password)
    teacher.updated_at = now_utc_naive()
    db.commit()
    return ok({"teacher_id": teacher.id, "temporary_password": new_password})


@router.delete("/teachers/{teacher_id}")
def disable_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_admin: Teacher = Depends(get_current_admin),
):
    teacher = db.get(Teacher, teacher_id)
    if teacher is None:
        return fail("老师不存在", code=40403, status_code=404)
    if teacher.id == current_admin.id:
        return fail("不能禁用当前登录的管理员", code=40007, status_code=400)

    teacher.is_active = False
    teacher.updated_at = now_utc_naive()
    db.commit()
    return ok({"teacher_id": teacher.id, "is_active": False})


@router.get("/parent-bindings")
def list_parent_bindings(
    db: Session = Depends(get_db),
    current_admin: Teacher = Depends(get_current_admin),
):
    parents = db.execute(select(Parent).order_by(Parent.id)).scalars().all()
    parent_ids = [parent.id for parent in parents]
    bindings = []
    links = []
    if parent_ids:
        bindings = db.execute(
            select(ParentBinding).where(ParentBinding.parent_id.in_(parent_ids)).order_by(ParentBinding.id)
        ).scalars().all()
        links = db.execute(
            select(StudentParent, Student)
            .join(Student, Student.id == StudentParent.student_id)
            .where(StudentParent.parent_id.in_(parent_ids))
            .order_by(StudentParent.parent_id, Student.id)
        ).all()

    bindings_by_parent: dict[int, list[ParentBinding]] = {}
    for binding in bindings:
        bindings_by_parent.setdefault(binding.parent_id, []).append(binding)

    students_by_parent: dict[int, list[dict]] = {}
    for link, student in links:
        students_by_parent.setdefault(link.parent_id, []).append(
            {
                "id": student.id,
                "name": student.name,
                "grade": student.grade,
                "status": student.status,
                "is_authorized": link.is_authorized,
            }
        )

    return ok(
        {
            "parents": [
                {
                    "id": parent.id,
                    "name": parent.name,
                    "relation": parent.relation,
                    "phone": parent.phone,
                    "invite_code": parent.invite_code,
                    "wechat_openid": parent.wechat_openid,
                    "bindings": [
                        {
                            "id": binding.id,
                            "wechat_openid": binding.wechat_openid,
                            "is_active": binding.is_active,
                            "bind_at": binding.bind_at.isoformat() if binding.bind_at else None,
                            "last_login_at": binding.last_login_at.isoformat()
                            if binding.last_login_at
                            else None,
                        }
                        for binding in bindings_by_parent.get(parent.id, [])
                    ],
                    "students": students_by_parent.get(parent.id, []),
                }
                for parent in parents
            ]
        }
    )


@router.post("/parent-bindings/{binding_id}/disable")
def disable_parent_binding(
    binding_id: int,
    db: Session = Depends(get_db),
    current_admin: Teacher = Depends(get_current_admin),
):
    binding = db.get(ParentBinding, binding_id)
    if binding is None:
        return fail("绑定不存在", code=40406, status_code=404)
    binding.is_active = False
    db.commit()
    return ok({"binding_id": binding.id, "is_active": False})


@router.post("/parents/{parent_id}/unbind-student/{student_id}")
def unbind_parent_student(
    parent_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_admin: Teacher = Depends(get_current_admin),
):
    link = db.execute(
        select(StudentParent).where(
            StudentParent.parent_id == parent_id,
            StudentParent.student_id == student_id,
        )
    ).scalar_one_or_none()
    if link is None:
        return fail("家长学生关联不存在", code=40407, status_code=404)
    link.is_authorized = False
    db.commit()
    return ok({"parent_id": parent_id, "student_id": student_id, "is_authorized": False})


@router.post("/students/{student_id}/withdraw")
def withdraw_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_admin: Teacher = Depends(get_current_admin),
):
    student = db.get(Student, student_id)
    if student is None:
        return fail("学生不存在", code=40401, status_code=404)

    student.status = "已退班"
    student.updated_at = now_utc_naive()
    links = db.execute(
        select(StudentParent).where(
            StudentParent.student_id == student_id,
            StudentParent.is_authorized.is_(True),
        )
    ).scalars().all()
    for link in links:
        link.is_authorized = False
    db.commit()
    return ok({"student_id": student.id, "status": student.status, "revoked_parent_links": len(links)})


@router.post("/students/{student_id}/restore")
def restore_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_admin: Teacher = Depends(get_current_admin),
):
    student = db.get(Student, student_id)
    if student is None:
        return fail("学生不存在", code=40401, status_code=404)
    student.status = "在读"
    student.is_active = True
    student.updated_at = now_utc_naive()
    db.commit()
    return ok({"student_id": student.id, "status": student.status, "restored_parent_links": 0})
