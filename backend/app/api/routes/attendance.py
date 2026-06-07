from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.core.datetime import beijing_date, format_beijing_time, now_utc_naive, parse_client_datetime
from app.core.responses import abort, fail, ok
from app.db.session import get_db
from app.models import AttendanceRecord, Student, Teacher
from app.schemas.attendance import CheckinRequest, CheckoutRequest, MakeupCheckinRequest

router = APIRouter(prefix="/attendance", tags=["attendance"])


def _get_student_or_error(db: Session, student_id: int) -> Student:
    student = db.get(Student, student_id)
    if student is None or not student.is_active:
        abort("学生不存在", code=40401, status_code=404)
    return student


def _record_for_date(db: Session, student_id: int, target_date):
    return db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.date == target_date,
        )
    ).scalar_one_or_none()


@router.get("/today")
def today_attendance(
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    today = beijing_date()
    students = db.execute(
        select(Student).where(Student.is_active.is_(True), Student.status == "在读").order_by(Student.id)
    ).scalars().all()
    records = db.execute(
        select(AttendanceRecord).where(AttendanceRecord.date == today)
    ).scalars().all()
    record_by_student = {record.student_id: record for record in records}

    checked_in = []
    not_checked_in = []
    for student in students:
        record = record_by_student.get(student.id)
        if record:
            checked_in.append(
                {
                    "student_id": student.id,
                    "name": student.name,
                    "checkin_time": format_beijing_time(record.checkin_time),
                    "checkout_time": format_beijing_time(record.checkout_time),
                    "pickup_person": record.pickup_person,
                    "is_makeup": record.is_makeup,
                }
            )
        else:
            not_checked_in.append({"student_id": student.id, "name": student.name})

    return ok(
        {
            "date": today.isoformat(),
            "total": len(students),
            "checked_in": checked_in,
            "not_checked_in": not_checked_in,
        }
    )


@router.post("/checkin")
def checkin(
    payload: CheckinRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    _get_student_or_error(db, payload.student_id)
    checkin_time = parse_client_datetime(payload.timestamp) if payload.timestamp else now_utc_naive()
    target_date = beijing_date(checkin_time)
    existing = _record_for_date(db, payload.student_id, target_date)
    if existing:
        return fail("今日已签到", code=40901, status_code=409)

    record = AttendanceRecord(
        student_id=payload.student_id,
        checkin_time=checkin_time,
        checkin_by=current_teacher.id,
        date=target_date,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ok({"id": record.id, "time": format_beijing_time(record.checkin_time), "status": "已签到"})


@router.post("/checkout")
def checkout(
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    _get_student_or_error(db, payload.student_id)
    checkout_time = parse_client_datetime(payload.timestamp) if payload.timestamp else now_utc_naive()
    target_date = beijing_date(checkout_time)
    record = _record_for_date(db, payload.student_id, target_date)
    if record is None:
        return fail("今日还未签到", code=40902, status_code=409)
    if record.checkout_time is not None:
        return fail("今日已签退", code=40903, status_code=409)

    record.checkout_time = checkout_time
    record.pickup_person = payload.pickup_person
    record.checkout_by = current_teacher.id
    db.commit()
    db.refresh(record)
    return ok({"id": record.id, "time": format_beijing_time(record.checkout_time), "status": "已签退"})


@router.post("/makeup-checkin")
def makeup_checkin(
    payload: MakeupCheckinRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    _get_student_or_error(db, payload.student_id)
    checkin_time = parse_client_datetime(payload.timestamp)
    target_date = beijing_date(checkin_time)
    existing = _record_for_date(db, payload.student_id, target_date)
    if existing:
        return fail("该日期已有签到记录", code=40904, status_code=409)

    record = AttendanceRecord(
        student_id=payload.student_id,
        checkin_time=checkin_time,
        checkin_by=current_teacher.id,
        is_makeup=True,
        makeup_reason=payload.reason,
        date=target_date,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ok({"id": record.id, "is_makeup": True, "time": format_beijing_time(record.checkin_time)})
