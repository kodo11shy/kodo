from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.core.datetime import beijing_date
from app.core.responses import fail, ok
from app.db.session import get_db
from app.models import AttendanceRecord, HomeworkRecord, MealRecord, MealStudentNote, Student, Teacher, TeacherRemark

router = APIRouter(prefix="/growth", tags=["growth"])


@router.get("/overview/{student_id}")
def growth_overview(
    student_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    student = db.get(Student, student_id)
    if student is None or not student.is_active:
        return fail("学生不存在", code=40401, status_code=404)

    today = beijing_date()
    month_start = today.replace(day=1)
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)

    attended_days = db.execute(
        select(func.count(AttendanceRecord.id)).where(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.date >= month_start,
            AttendanceRecord.date < next_month,
        )
    ).scalar_one()

    homework_stats = db.execute(
        select(func.avg(HomeworkRecord.score), func.count(HomeworkRecord.id)).where(
            HomeworkRecord.student_id == student_id,
            HomeworkRecord.homework_date >= month_start,
            HomeworkRecord.homework_date < next_month,
        )
    ).one()

    latest_remark = db.execute(
        select(TeacherRemark)
        .where(TeacherRemark.student_id == student_id)
        .order_by(TeacherRemark.record_date.desc(), TeacherRemark.id.desc())
        .limit(1)
    ).scalar_one_or_none()

    enrollment_days = None
    if student.enrollment_date:
        enrollment_days = (today - student.enrollment_date).days + 1

    avg_score = float(homework_stats[0]) if homework_stats[0] is not None else None
    return ok(
        {
            "student_info": {
                "id": student.id,
                "name": student.name,
                "grade": student.grade,
                "school_name": student.school_name,
                "enrollment_days": enrollment_days,
            },
            "current_month": {
                "attended_days": attended_days,
                "avg_score": round(avg_score, 1) if avg_score is not None else None,
                "homework_count": homework_stats[1],
                "remark_count": db.execute(
                    select(func.count(TeacherRemark.id)).where(
                        TeacherRemark.student_id == student_id,
                        TeacherRemark.record_date >= month_start,
                        TeacherRemark.record_date < next_month,
                    )
                ).scalar_one(),
            },
            "latest_remark": latest_remark.content if latest_remark else None,
        }
    )


@router.get("/timeline/{student_id}")
def growth_timeline(
    student_id: int,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    student = db.get(Student, student_id)
    if student is None or not student.is_active:
        return fail("学生不存在", code=40401, status_code=404)

    start_date = beijing_date() - timedelta(days=days)
    homework_records = db.execute(
        select(HomeworkRecord)
        .where(HomeworkRecord.student_id == student_id, HomeworkRecord.homework_date >= start_date)
        .order_by(HomeworkRecord.homework_date.desc(), HomeworkRecord.id.desc())
    ).scalars().all()
    remarks = db.execute(
        select(TeacherRemark)
        .where(TeacherRemark.student_id == student_id, TeacherRemark.record_date >= start_date)
        .order_by(TeacherRemark.record_date.desc(), TeacherRemark.id.desc())
    ).scalars().all()
    meal_notes = db.execute(
        select(MealStudentNote, MealRecord)
        .join(MealRecord, MealRecord.id == MealStudentNote.meal_id)
        .where(MealStudentNote.student_id == student_id, MealRecord.meal_date >= start_date)
        .order_by(MealRecord.meal_date.desc(), MealStudentNote.id.desc())
    ).all()

    timeline = []
    for record in homework_records:
        title_parts = [record.subject]
        if record.accuracy_status:
            title_parts.append(record.accuracy_status)
        timeline.append(
            {
                "date": record.homework_date.isoformat(),
                "type": "homework",
                "title": " · ".join(title_parts),
                "description": record.teacher_remark,
                "score": record.score,
                "source_id": record.id,
            }
        )

    for remark in remarks:
        timeline.append(
            {
                "date": remark.record_date.isoformat(),
                "type": "remark",
                "title": "老师评语",
                "description": remark.content,
                "score": None,
                "source_id": remark.id,
            }
        )

    for meal_note, meal in meal_notes:
        timeline.append(
            {
                "date": meal.meal_date.isoformat(),
                "type": "meal",
                "title": f"{meal.meal_type}记录",
                "description": meal_note.remark,
                "score": None,
                "source_id": meal_note.id,
            }
        )

    timeline.sort(key=lambda item: item["date"], reverse=True)
    return ok({"timeline": timeline})
