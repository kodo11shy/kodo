import secrets
import string

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.core.datetime import now_utc_naive
from app.core.responses import fail, ok
from app.db.session import get_db
from app.models import AuthorizedPickup, Parent, ParentBinding, Student, StudentHealth, StudentParent, Teacher
from app.schemas.student import HealthConsentRequest, PickupsUpdateRequest, StudentCreateRequest, StudentUpdateRequest

router = APIRouter(prefix="/students", tags=["students"])


def _invite_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(6))


def student_summary(student: Student) -> dict:
    return {
        "id": student.id,
        "name": student.name,
        "gender": student.gender,
        "grade": student.grade,
        "school_name": student.school_name,
        "school_class": student.school_class,
        "status": student.status,
        "avatar_url": student.avatar_url,
    }


def student_detail_out(db: Session, student: Student) -> dict:
    parents = db.execute(
        select(Parent, StudentParent)
        .join(StudentParent, StudentParent.parent_id == Parent.id)
        .where(StudentParent.student_id == student.id)
    ).all()
    parent_ids = [parent.id for parent, _link in parents]
    active_bindings = set()
    if parent_ids:
        active_bindings = set(
            db.execute(
                select(ParentBinding.parent_id).where(
                    ParentBinding.parent_id.in_(parent_ids),
                    ParentBinding.is_active.is_(True),
                )
            ).scalars().all()
        )
    pickups = db.execute(
        select(AuthorizedPickup).where(AuthorizedPickup.student_id == student.id).order_by(AuthorizedPickup.id)
    ).scalars().all()
    health = db.execute(select(StudentHealth).where(StudentHealth.student_id == student.id)).scalar_one_or_none()
    return {
        **student_summary(student),
        "birth_date": student.birth_date.isoformat() if student.birth_date else None,
        "school_end_time": student.school_end_time.isoformat() if student.school_end_time else None,
        "pickup_method": student.pickup_method,
        "address": student.address,
        "enrollment_date": student.enrollment_date.isoformat() if student.enrollment_date else None,
        "interests": student.interests,
        "personality": student.personality,
        "weak_subjects": student.weak_subjects,
        "notes": student.notes,
        "parents": [
            {
                "id": parent.id,
                "name": parent.name,
                "relation": parent.relation,
                "phone": parent.phone,
                "is_primary": parent.is_primary,
                "is_emergency": parent.is_emergency,
                "is_authorized": link.is_authorized,
                "invite_code": parent.invite_code,
                "wechat_bound": bool(parent.wechat_openid) or parent.id in active_bindings,
            }
            for parent, link in parents
        ],
        "pickups": [
            {
                "id": pickup.id,
                "name": pickup.name,
                "relation": pickup.relation,
                "phone": pickup.phone,
                "id_card": pickup.id_card,
                "is_default": pickup.is_default,
            }
            for pickup in pickups
        ],
        "health": {
            "food_allergies": health.food_allergies if health else None,
            "drug_allergies": health.drug_allergies if health else None,
            "medical_history": health.medical_history if health else None,
            "special_notes": health.special_notes if health else None,
            "current_meds": health.current_meds if health else None,
            "consent_signed": health.consent_signed if health else False,
            "consent_signed_at": health.consent_signed_at.isoformat() if health and health.consent_signed_at else None,
        },
    }


@router.get("")
def list_students(
    status: str = Query(default="在读"),
    keyword: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    query = select(Student).where(Student.is_active.is_(True))
    if status:
        query = query.where(Student.status == status)
    if keyword:
        like_keyword = f"%{keyword}%"
        query = query.where(
            or_(
                Student.name.ilike(like_keyword),
                Student.grade.ilike(like_keyword),
                Student.school_name.ilike(like_keyword),
            )
        )

    students = db.execute(query.order_by(Student.id)).scalars().all()
    return ok({"students": [student_summary(student) for student in students]})


@router.post("")
def create_student(
    payload: StudentCreateRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    student = Student(
        name=payload.name,
        gender=payload.gender,
        birth_date=payload.birth_date,
        grade=payload.grade,
        school_name=payload.school_name,
        school_class=payload.school_class,
        school_end_time=payload.school_end_time,
        pickup_method=payload.pickup_method or "家长自接",
        address=payload.address,
        enrollment_date=payload.enrollment_date,
    )
    db.add(student)
    db.flush()

    parent_specs = [
        (payload.parent1_name, payload.parent1_relation, payload.parent1_phone, True),
        (payload.parent2_name, payload.parent2_relation, payload.parent2_phone, False),
    ]
    for name, relation, phone, is_primary in parent_specs:
        if not name or not relation or not phone:
            continue
        parent = Parent(name=name, relation=relation, phone=phone, is_primary=is_primary, invite_code=_invite_code())
        db.add(parent)
        db.flush()
        db.add(StudentParent(student_id=student.id, parent_id=parent.id, is_authorized=True))

    db.commit()
    return ok({"id": student.id})


@router.get("/{student_id}")
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    student = db.get(Student, student_id)
    if student is None or not student.is_active:
        return fail("学生不存在", code=40401, status_code=404)
    return ok(student_detail_out(db, student))


@router.put("/{student_id}")
def update_student(
    student_id: int,
    payload: StudentUpdateRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    student = db.get(Student, student_id)
    if student is None or not student.is_active:
        return fail("学生不存在", code=40401, status_code=404)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, key, value)
    student.updated_at = now_utc_naive()
    db.commit()
    db.refresh(student)
    return ok({"id": student.id})


@router.get("/{student_id}/pickups")
def get_pickups(
    student_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    pickups = db.execute(
        select(AuthorizedPickup).where(AuthorizedPickup.student_id == student_id).order_by(AuthorizedPickup.id)
    ).scalars().all()
    return ok(
        {
            "pickups": [
                {
                    "id": pickup.id,
                    "name": pickup.name,
                    "relation": pickup.relation,
                    "phone": pickup.phone,
                    "id_card": pickup.id_card,
                    "is_default": pickup.is_default,
                }
                for pickup in pickups
            ]
        }
    )


@router.put("/{student_id}/pickups")
def update_pickups(
    student_id: int,
    payload: PickupsUpdateRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    student = db.get(Student, student_id)
    if student is None or not student.is_active:
        return fail("学生不存在", code=40401, status_code=404)
    db.query(AuthorizedPickup).filter(AuthorizedPickup.student_id == student_id).delete()
    for pickup in payload.pickups:
        db.add(
            AuthorizedPickup(
                student_id=student_id,
                name=pickup.name,
                relation=pickup.relation,
                phone=pickup.phone,
                id_card=pickup.id_card,
                is_default=pickup.is_default,
            )
        )
    db.commit()
    return ok({"ok": True})


@router.post("/{student_id}/health/consent")
def sign_health_consent(
    student_id: int,
    payload: HealthConsentRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    student = db.get(Student, student_id)
    if student is None or not student.is_active:
        return fail("学生不存在", code=40401, status_code=404)
    health = db.execute(select(StudentHealth).where(StudentHealth.student_id == student_id)).scalar_one_or_none()
    if health is None:
        health = StudentHealth(student_id=student_id)
        db.add(health)
    health.consent_signed = payload.signed
    health.consent_signed_at = now_utc_naive() if payload.signed else None
    health.updated_at = now_utc_naive()
    db.commit()
    return ok({"ok": True})
