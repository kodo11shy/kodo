from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.core.datetime import beijing_date
from app.core.responses import abort, fail, ok
from app.db.session import get_db
from app.models import (
    AttendanceRecord,
    MealPhoto,
    MealRecord,
    MealStudentNote,
    Photo,
    PhotoStudent,
    Student,
    Teacher,
)
from app.schemas.meal import MealCreateRequest, MealStudentNoteRequest

router = APIRouter(prefix="/meals", tags=["meals"])

DEFAULT_MEAL_TYPE = "今日餐食"


def _photo_out(photo: Photo | None) -> dict | None:
    if photo is None:
        return None
    return {
        "id": photo.id,
        "file_path": photo.file_path,
        "thumbnail": photo.thumbnail_path,
        "photo_type": photo.photo_type,
        "remark": photo.remark,
    }


def _student_out(student: Student) -> dict:
    return {"id": student.id, "name": student.name, "grade": student.grade}


def _unique_ids(values: list[int]) -> list[int]:
    result = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _normalize_photo_ids(photo_ids: list[int] | dict[str, list[int]] | None) -> list[int]:
    if not photo_ids:
        return []
    if isinstance(photo_ids, dict):
        flattened = []
        for ids in photo_ids.values():
            flattened.extend(ids or [])
        return _unique_ids(flattened)
    return _unique_ids(photo_ids)


def _meal_for_date(db: Session, target_date) -> MealRecord | None:
    return db.execute(
        select(MealRecord)
        .where(MealRecord.meal_date == target_date)
        .order_by(MealRecord.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def _validate_photo_ids(db: Session, photo_ids: list[int]) -> list[int]:
    if not photo_ids:
        return []
    existing = set(db.execute(select(Photo.id).where(Photo.id.in_(photo_ids))).scalars().all())
    return [photo_id for photo_id in photo_ids if photo_id not in existing]


def _validate_student_ids(db: Session, student_ids: list[int]) -> list[int]:
    if not student_ids:
        return []
    existing = set(
        db.execute(
            select(Student.id).where(
                Student.id.in_(student_ids),
                Student.is_active.is_(True),
                Student.status == "在读",
            )
        ).scalars().all()
    )
    return [student_id for student_id in student_ids if student_id not in existing]


def _sync_meal_links(db: Session, meal: MealRecord, payload: MealCreateRequest) -> None:
    photo_ids = _normalize_photo_ids(payload.photo_ids)
    cover_photo_id = payload.cover_photo_id
    if cover_photo_id and cover_photo_id not in photo_ids:
        photo_ids = [cover_photo_id, *photo_ids]
    photo_ids = _unique_ids(photo_ids)

    missing_photos = _validate_photo_ids(db, photo_ids)
    if missing_photos:
        abort(f"照片不存在: {missing_photos}", code=40402, status_code=404)

    student_ids = _unique_ids(payload.student_ids or [])
    missing_students = _validate_student_ids(db, student_ids)
    if missing_students:
        abort(f"学生不存在: {missing_students}", code=40401, status_code=404)

    db.query(MealPhoto).filter(MealPhoto.meal_id == meal.id).delete(synchronize_session=False)
    db.query(MealStudentNote).filter(MealStudentNote.meal_id == meal.id).delete(synchronize_session=False)

    ordered_photo_ids = []
    if cover_photo_id and cover_photo_id in photo_ids:
        ordered_photo_ids.append(cover_photo_id)
    ordered_photo_ids.extend([photo_id for photo_id in photo_ids if photo_id not in ordered_photo_ids])

    for index, photo_id in enumerate(ordered_photo_ids):
        db.add(
            MealPhoto(
                meal_id=meal.id,
                photo_id=photo_id,
                step="cover" if photo_id == cover_photo_id else "general",
                sort_order=index,
            )
        )

    note_text = payload.overall_remark or ""
    for student_id in student_ids:
        db.add(
            MealStudentNote(
                meal_id=meal.id,
                student_id=student_id,
                remark=note_text,
                photo_id=cover_photo_id,
            )
        )

    if ordered_photo_ids and student_ids:
        photos = db.execute(select(Photo).where(Photo.id.in_(ordered_photo_ids))).scalars().all()
        for photo in photos:
            photo.photo_type = "meal"
            existing_student_ids = set(
                db.execute(
                    select(PhotoStudent.student_id).where(PhotoStudent.photo_id == photo.id)
                ).scalars().all()
            )
            is_single = len(student_ids) == 1
            for student_id in student_ids:
                if student_id not in existing_student_ids:
                    db.add(PhotoStudent(photo_id=photo.id, student_id=student_id, is_main=is_single))


def _meal_maps(db: Session, meal_ids: list[int]) -> tuple[dict[int, list[Photo]], dict[int, list[Student]]]:
    if not meal_ids:
        return {}, {}

    photo_rows = db.execute(
        select(MealPhoto, Photo)
        .join(Photo, Photo.id == MealPhoto.photo_id)
        .where(MealPhoto.meal_id.in_(meal_ids))
        .order_by(MealPhoto.meal_id, MealPhoto.sort_order, MealPhoto.id)
    ).all()
    photos_by_meal: dict[int, list[Photo]] = {}
    for meal_photo, photo in photo_rows:
        photos_by_meal.setdefault(meal_photo.meal_id, []).append(photo)

    student_rows = db.execute(
        select(MealStudentNote, Student)
        .join(Student, Student.id == MealStudentNote.student_id)
        .where(MealStudentNote.meal_id.in_(meal_ids))
        .order_by(MealStudentNote.meal_id, Student.id)
    ).all()
    students_by_meal: dict[int, list[Student]] = {}
    seen: dict[int, set[int]] = {}
    for note, student in student_rows:
        seen.setdefault(note.meal_id, set())
        if student.id in seen[note.meal_id]:
            continue
        seen[note.meal_id].add(student.id)
        students_by_meal.setdefault(note.meal_id, []).append(student)

    return photos_by_meal, students_by_meal


def _meal_out(meal: MealRecord, photos: list[Photo] | None = None, students: list[Student] | None = None) -> dict:
    photos = photos or []
    students = students or []
    cover_photo = photos[0] if photos else None
    return {
        "id": meal.id,
        "date": meal.meal_date.isoformat(),
        "meal_date": meal.meal_date.isoformat(),
        "meal_type": DEFAULT_MEAL_TYPE,
        "menu": meal.menu_text,
        "menu_text": meal.menu_text,
        "ingredient_notes": meal.ingredient_notes,
        "cooking_notes": meal.cooking_notes,
        "hygiene_notes": meal.hygiene_notes,
        "overall_remark": meal.overall_remark,
        "cover_photo": _photo_out(cover_photo),
        "cover_photo_id": cover_photo.id if cover_photo else None,
        "photos": [_photo_out(photo) for photo in photos],
        "photo_ids": [photo.id for photo in photos],
        "photo_count": len(photos),
        "students": [_student_out(student) for student in students],
        "student_ids": [student.id for student in students],
        "student_count": len(students),
    }


def _default_students_for_today(db: Session) -> tuple[list[Student], list[Student]]:
    students = db.execute(
        select(Student)
        .where(Student.is_active.is_(True), Student.status == "在读")
        .order_by(Student.id)
    ).scalars().all()
    today = beijing_date()
    checked_ids = set(
        db.execute(
            select(AttendanceRecord.student_id).where(AttendanceRecord.date == today)
        ).scalars().all()
    )
    checked_students = [student for student in students if student.id in checked_ids]
    return checked_students, students


@router.get("/today")
def today_meal(
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    today = beijing_date()
    meal = _meal_for_date(db, today)
    meal_data = None
    if meal:
        photos_by_meal, students_by_meal = _meal_maps(db, [meal.id])
        meal_data = _meal_out(meal, photos_by_meal.get(meal.id), students_by_meal.get(meal.id))

    week_start = today - timedelta(days=6)
    month_start = today.replace(day=1)
    dates = db.execute(select(MealRecord.meal_date).where(MealRecord.meal_date >= week_start)).scalars().all()
    month_dates = [date_value for date_value in dates if date_value >= month_start]
    checked_students, all_students = _default_students_for_today(db)

    return ok(
        {
            "date": today.isoformat(),
            "recorded": meal is not None,
            "meal": meal_data,
            "week_recorded_days": len(set(dates)),
            "month_recorded_days": len(set(month_dates)),
            "default_students": [_student_out(student) for student in checked_students],
            "all_students": [_student_out(student) for student in all_students],
        }
    )


@router.post("")
def create_meal(
    payload: MealCreateRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    target_date = payload.meal_date or beijing_date()
    meal = _meal_for_date(db, target_date)
    created = meal is None
    if meal is None:
        meal = MealRecord(meal_date=target_date, meal_type=DEFAULT_MEAL_TYPE, created_by=current_teacher.id)
        db.add(meal)
        db.flush()

    meal.meal_type = DEFAULT_MEAL_TYPE
    meal.menu_text = payload.menu_text
    meal.ingredient_notes = payload.ingredient_notes
    meal.cooking_notes = payload.cooking_notes
    meal.hygiene_notes = payload.hygiene_notes
    meal.overall_remark = payload.overall_remark
    meal.created_by = meal.created_by or current_teacher.id
    _sync_meal_links(db, meal, payload)

    db.commit()
    db.refresh(meal)
    photos_by_meal, students_by_meal = _meal_maps(db, [meal.id])
    return ok({"id": meal.id, "created": created, "meal": _meal_out(meal, photos_by_meal.get(meal.id), students_by_meal.get(meal.id))})


@router.put("/{meal_id}")
def update_meal(
    meal_id: int,
    payload: MealCreateRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    meal = db.get(MealRecord, meal_id)
    if meal is None:
        return fail("餐食记录不存在", code=40405, status_code=404)

    meal.meal_date = payload.meal_date or meal.meal_date
    meal.meal_type = DEFAULT_MEAL_TYPE
    meal.menu_text = payload.menu_text
    meal.ingredient_notes = payload.ingredient_notes
    meal.cooking_notes = payload.cooking_notes
    meal.hygiene_notes = payload.hygiene_notes
    meal.overall_remark = payload.overall_remark
    _sync_meal_links(db, meal, payload)

    db.commit()
    db.refresh(meal)
    photos_by_meal, students_by_meal = _meal_maps(db, [meal.id])
    return ok({"id": meal.id, "meal": _meal_out(meal, photos_by_meal.get(meal.id), students_by_meal.get(meal.id))})


@router.post("/{meal_id}/student-note")
def add_student_note(
    meal_id: int,
    payload: MealStudentNoteRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    meal = db.get(MealRecord, meal_id)
    if meal is None:
        return fail("餐食记录不存在", code=40405, status_code=404)
    student = db.get(Student, payload.student_id)
    if student is None or not student.is_active:
        return fail("学生不存在", code=40401, status_code=404)
    if payload.photo_id and db.get(Photo, payload.photo_id) is None:
        return fail("照片不存在", code=40402, status_code=404)

    note = MealStudentNote(
        meal_id=meal_id,
        student_id=payload.student_id,
        remark=payload.remark,
        photo_id=payload.photo_id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return ok({"id": note.id})


@router.get("")
def list_meals(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    all_meals = db.execute(
        select(MealRecord).order_by(MealRecord.meal_date.desc(), MealRecord.id.desc())
    ).scalars().all()
    daily_meals = []
    seen_dates = set()
    for meal in all_meals:
        if meal.meal_date in seen_dates:
            continue
        seen_dates.add(meal.meal_date)
        daily_meals.append(meal)

    meals = daily_meals[(page - 1) * page_size : page * page_size]
    meal_ids = [meal.id for meal in meals]
    photos_by_meal, students_by_meal = _meal_maps(db, meal_ids)
    return ok(
        {
            "records": [
                _meal_out(meal, photos_by_meal.get(meal.id), students_by_meal.get(meal.id))
                for meal in meals
            ],
            "total": len(daily_meals),
        }
    )


@router.get("/student/{student_id}")
def student_meal_notes(
    student_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    notes = db.execute(
        select(MealStudentNote, MealRecord, Photo)
        .join(MealRecord, MealRecord.id == MealStudentNote.meal_id)
        .outerjoin(Photo, Photo.id == MealStudentNote.photo_id)
        .where(MealStudentNote.student_id == student_id)
        .order_by(MealRecord.meal_date.desc(), MealStudentNote.created_at.desc())
    ).all()
    return ok(
        {
            "notes": [
                {
                    "id": note.id,
                    "date": meal.meal_date.isoformat(),
                    "meal_type": DEFAULT_MEAL_TYPE,
                    "menu_text": meal.menu_text,
                    "remark": note.remark,
                    "photo": _photo_out(photo) if photo else None,
                }
                for note, meal, photo in notes
            ]
        }
    )


@router.get("/{meal_id}")
def get_meal(
    meal_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    meal = db.get(MealRecord, meal_id)
    if meal is None:
        return fail("餐食记录不存在", code=40405, status_code=404)
    photos_by_meal, students_by_meal = _meal_maps(db, [meal.id])
    return ok({"meal": _meal_out(meal, photos_by_meal.get(meal.id), students_by_meal.get(meal.id))})
