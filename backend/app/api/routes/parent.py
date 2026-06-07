from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_parent
from app.core.datetime import beijing_date, format_beijing_time
from app.core.homework_rules import ALLOWED_HOMEWORK_SUBJECTS
from app.core.responses import fail, ok
from app.db.session import get_db
from app.models import (
    AttendanceRecord,
    HomeworkPhoto,
    HomeworkRecord,
    MealRecord,
    MealStudentNote,
    Parent,
    Photo,
    PhotoStudent,
    Student,
    StudentParent,
    TeacherRemark,
)

router = APIRouter(prefix="/parent", tags=["parent"])


def _authorized_student_ids(db: Session, parent_id: int) -> list[int]:
    return db.execute(
        select(StudentParent.student_id)
        .join(Student, Student.id == StudentParent.student_id)
        .where(
            StudentParent.parent_id == parent_id,
            StudentParent.is_authorized.is_(True),
            Student.status == "在读",
            Student.is_active.is_(True),
        )
    ).scalars().all()


def _ensure_parent_can_view(db: Session, parent: Parent, student_id: int) -> None | object:
    if student_id not in _authorized_student_ids(db, parent.id):
        return fail("无权查看该学生", code=40301, status_code=403)
    return None


@router.get("/students")
def parent_students(
    db: Session = Depends(get_db),
    current_parent: Parent = Depends(get_current_parent),
):
    student_ids = _authorized_student_ids(db, current_parent.id)
    students = db.execute(select(Student).where(Student.id.in_(student_ids))).scalars().all()
    today = beijing_date()
    records = db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.student_id.in_(student_ids),
            AttendanceRecord.date == today,
        )
    ).scalars().all()
    attendance_by_student = {record.student_id: record for record in records}

    return ok(
        {
            "students": [
                {
                    "id": student.id,
                    "name": student.name,
                    "grade": student.grade,
                    "today_checkin": format_beijing_time(attendance_by_student.get(student.id).checkin_time)
                    if attendance_by_student.get(student.id)
                    else None,
                    "today_checkout": format_beijing_time(attendance_by_student.get(student.id).checkout_time)
                    if attendance_by_student.get(student.id)
                    else None,
                }
                for student in students
            ]
        }
    )


@router.get("/dashboard/today")
def parent_dashboard_today(
    student_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_parent: Parent = Depends(get_current_parent),
):
    student_ids = _authorized_student_ids(db, current_parent.id)
    if not student_ids:
        return ok(
            {
                "student": None,
                "attendance_today": None,
                "latest_photos": [],
                "meal_today": None,
                "homework_today": None,
                "latest_remark": None,
            }
        )

    target_student_id = student_id or student_ids[0]
    if target_student_id not in student_ids:
        return fail("无权查看该学生", code=40301, status_code=403)

    student = db.get(Student, target_student_id)
    if student is None or not student.is_active:
        return fail("学生不存在", code=40401, status_code=404)

    today = beijing_date()
    attendance = db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.student_id == target_student_id,
            AttendanceRecord.date == today,
        )
    ).scalar_one_or_none()

    latest_photos = db.execute(
        select(Photo)
        .join(PhotoStudent, PhotoStudent.photo_id == Photo.id)
        .where(PhotoStudent.student_id == target_student_id)
        .order_by(Photo.taken_at.desc(), Photo.id.desc())
        .limit(9)
    ).scalars().all()

    meal_row = db.execute(
        select(MealStudentNote, MealRecord, Photo)
        .join(MealRecord, MealRecord.id == MealStudentNote.meal_id)
        .outerjoin(Photo, Photo.id == MealStudentNote.photo_id)
        .where(MealStudentNote.student_id == target_student_id)
        .order_by(MealRecord.meal_date.desc(), MealStudentNote.id.desc())
        .limit(1)
    ).first()

    homework = db.execute(
        select(HomeworkRecord)
        .where(
            HomeworkRecord.student_id == target_student_id,
            HomeworkRecord.subject.in_(ALLOWED_HOMEWORK_SUBJECTS),
        )
        .order_by(HomeworkRecord.homework_date.desc(), HomeworkRecord.id.desc())
        .limit(1)
    ).scalar_one_or_none()

    remark = db.execute(
        select(TeacherRemark)
        .where(TeacherRemark.student_id == target_student_id)
        .order_by(TeacherRemark.record_date.desc(), TeacherRemark.id.desc())
        .limit(1)
    ).scalar_one_or_none()

    meal_today = None
    if meal_row:
        meal_note, meal, meal_photo = meal_row
        meal_today = {
            "id": meal.id,
            "date": meal.meal_date.isoformat(),
            "meal_type": meal.meal_type,
            "menu_text": meal.menu_text,
            "overall_remark": meal.overall_remark,
            "student_remark": meal_note.remark,
            "photo": {
                "id": meal_photo.id,
                "file_path": meal_photo.file_path,
                "thumbnail": meal_photo.thumbnail_path,
            }
            if meal_photo
            else None,
        }

    return ok(
        {
            "student": {
                "id": student.id,
                "name": student.name,
                "grade": student.grade,
                "initial": (student.name or "")[:1],
            },
            "attendance_today": {
                "date": today.isoformat(),
                "checkin_time": format_beijing_time(attendance.checkin_time) if attendance else None,
                "checkout_time": format_beijing_time(attendance.checkout_time) if attendance else None,
            },
            "latest_photos": [
                {
                    "id": photo.id,
                    "file_path": photo.file_path,
                    "thumbnail": photo.thumbnail_path,
                    "photo_type": photo.photo_type,
                    "taken_at": photo.taken_at.isoformat() if photo.taken_at else None,
                    "remark": photo.remark,
                }
                for photo in latest_photos
            ],
            "meal_today": meal_today,
            "homework_today": {
                "id": homework.id,
                "date": homework.homework_date.isoformat(),
                "subject": homework.subject,
                "status": homework.completion_status,
                "accuracy": homework.accuracy_status,
                "score": homework.score,
                "remark": homework.teacher_remark,
            }
            if homework
            else None,
            "latest_remark": {
                "id": remark.id,
                "date": remark.record_date.isoformat(),
                "content": remark.content,
                "mood_tag": remark.mood_tag,
            }
            if remark
            else None,
        }
    )


@router.get("/homework/{student_id}")
def parent_homework(
    student_id: int,
    db: Session = Depends(get_db),
    current_parent: Parent = Depends(get_current_parent),
):
    denied = _ensure_parent_can_view(db, current_parent, student_id)
    if denied:
        return denied

    records = db.execute(
        select(HomeworkRecord)
        .where(
            HomeworkRecord.student_id == student_id,
            HomeworkRecord.subject.in_(ALLOWED_HOMEWORK_SUBJECTS),
        )
        .order_by(HomeworkRecord.homework_date.desc(), HomeworkRecord.id.desc())
        .limit(50)
    ).scalars().all()
    record_ids = [record.id for record in records]
    rows = []
    if record_ids:
        rows = db.execute(
            select(HomeworkPhoto, Photo)
            .join(Photo, Photo.id == HomeworkPhoto.photo_id)
            .where(HomeworkPhoto.homework_id.in_(record_ids))
            .order_by(HomeworkPhoto.homework_id, HomeworkPhoto.step, HomeworkPhoto.sort_order)
        ).all()

    photos_by_record = {record_id: {"done": [], "graded": [], "corrected": []} for record_id in record_ids}
    for homework_photo, photo in rows:
        photos_by_record[homework_photo.homework_id][homework_photo.step].append(
            {"id": photo.id, "file_path": photo.file_path, "thumbnail": photo.thumbnail_path}
        )

    return ok(
        {
            "records": [
                {
                    "id": record.id,
                    "date": record.homework_date.isoformat(),
                    "subject": record.subject,
                    "status": record.completion_status,
                    "accuracy": record.accuracy_status,
                    "score": record.score,
                    "error_count": record.error_count,
                    "photos": photos_by_record.get(record.id, {"done": [], "graded": [], "corrected": []}),
                    "remark": record.teacher_remark,
                }
                for record in records
            ]
        }
    )


@router.get("/growth/{student_id}")
def parent_growth(
    student_id: int,
    db: Session = Depends(get_db),
    current_parent: Parent = Depends(get_current_parent),
):
    denied = _ensure_parent_can_view(db, current_parent, student_id)
    if denied:
        return denied

    student = db.get(Student, student_id)
    today = beijing_date()
    month_start = today.replace(day=1)
    start_date = today - timedelta(days=30)

    homework_count = db.execute(
        select(func.count(HomeworkRecord.id)).where(
            HomeworkRecord.student_id == student_id,
            HomeworkRecord.homework_date >= month_start,
            HomeworkRecord.subject.in_(ALLOWED_HOMEWORK_SUBJECTS),
        )
    ).scalar_one()
    avg_score = db.execute(
        select(func.avg(HomeworkRecord.score)).where(
            HomeworkRecord.student_id == student_id,
            HomeworkRecord.homework_date >= month_start,
            HomeworkRecord.subject.in_(ALLOWED_HOMEWORK_SUBJECTS),
        )
    ).scalar_one()
    attended_days = db.execute(
        select(func.count(AttendanceRecord.id)).where(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.date >= month_start,
        )
    ).scalar_one()

    homework_records = db.execute(
        select(HomeworkRecord)
        .where(
            HomeworkRecord.student_id == student_id,
            HomeworkRecord.homework_date >= start_date,
            HomeworkRecord.subject.in_(ALLOWED_HOMEWORK_SUBJECTS),
        )
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

    timeline = [
        {
            "date": record.homework_date.isoformat(),
            "type": "homework",
            "title": f"{record.subject} · {record.completion_status}",
            "description": record.teacher_remark,
            "score": record.score,
            "source_id": record.id,
        }
        for record in homework_records
    ]
    timeline.extend(
        {
            "date": remark.record_date.isoformat(),
            "type": "remark",
            "title": "老师评语",
            "description": remark.content,
            "score": None,
            "source_id": remark.id,
        }
        for remark in remarks
    )
    timeline.extend(
        {
            "date": meal.meal_date.isoformat(),
            "type": "meal",
            "title": f"{meal.meal_type}记录",
            "description": note.remark,
            "score": None,
            "source_id": note.id,
        }
        for note, meal in meal_notes
    )
    timeline.sort(key=lambda item: item["date"], reverse=True)

    return ok(
        {
            "overview": {
                "student_info": {"id": student.id, "name": student.name, "grade": student.grade},
                "current_month": {
                    "attended_days": attended_days,
                    "avg_score": round(float(avg_score), 1) if avg_score is not None else None,
                    "homework_count": homework_count,
                },
            },
            "timeline": timeline,
        }
    )


@router.get("/photos/{student_id}")
def parent_photos(
    student_id: int,
    db: Session = Depends(get_db),
    current_parent: Parent = Depends(get_current_parent),
):
    denied = _ensure_parent_can_view(db, current_parent, student_id)
    if denied:
        return denied

    photos = db.execute(
        select(Photo)
        .join(PhotoStudent, PhotoStudent.photo_id == Photo.id)
        .where(PhotoStudent.student_id == student_id)
        .order_by(Photo.taken_at.desc(), Photo.id.desc())
        .limit(100)
    ).scalars().all()
    return ok(
        {
            "photos": [
                {
                    "id": photo.id,
                    "file_path": photo.file_path,
                    "thumbnail": photo.thumbnail_path,
                    "photo_type": photo.photo_type,
                    "taken_at": photo.taken_at.isoformat() if photo.taken_at else None,
                    "remark": photo.remark,
                }
                for photo in photos
            ]
        }
    )
