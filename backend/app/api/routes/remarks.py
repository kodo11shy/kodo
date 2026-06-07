from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.core.datetime import beijing_date
from app.core.responses import fail, ok
from app.db.session import get_db
from app.models import Student, Teacher, TeacherRemark
from app.schemas.remark import RemarkCreateRequest

router = APIRouter(prefix="/remarks", tags=["remarks"])


def _remark_out(remark: TeacherRemark) -> dict:
    return {
        "id": remark.id,
        "student_id": remark.student_id,
        "date": remark.record_date.isoformat(),
        "content": remark.content,
        "mood_tag": remark.mood_tag,
        "created_at": remark.created_at.isoformat() if remark.created_at else None,
    }


@router.post("")
def create_remark(
    payload: RemarkCreateRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    student = db.get(Student, payload.student_id)
    if student is None or not student.is_active:
        return fail("学生不存在", code=40401, status_code=404)

    remark = TeacherRemark(
        student_id=payload.student_id,
        record_date=payload.record_date or beijing_date(),
        content=payload.content,
        mood_tag=payload.mood_tag,
        created_by=current_teacher.id,
    )
    db.add(remark)
    db.commit()
    db.refresh(remark)
    return ok({"id": remark.id})


@router.get("")
def list_remarks(
    student_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    remarks = db.execute(
        select(TeacherRemark)
        .where(TeacherRemark.student_id == student_id)
        .order_by(TeacherRemark.record_date.desc(), TeacherRemark.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()
    return ok({"remarks": [_remark_out(remark) for remark in remarks]})

