from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.core.datetime import beijing_date
from app.core.responses import fail, ok
from app.db.session import get_db
from app.models import MealPhoto, MealRecord, MealStudentNote, Photo, Student, Teacher
from app.schemas.meal import MealCreateRequest, MealStudentNoteRequest

router = APIRouter(prefix="/meals", tags=["meals"])


def _photo_out(photo: Photo) -> dict:
    return {"id": photo.id, "file_path": photo.file_path, "thumbnail": photo.thumbnail_path, "remark": photo.remark}


def _validate_photo_ids(db: Session, photo_ids: list[int]) -> list[int]:
    if not photo_ids:
        return []
    existing = set(db.execute(select(Photo.id).where(Photo.id.in_(photo_ids))).scalars().all())
    return [photo_id for photo_id in photo_ids if photo_id not in existing]


@router.post("")
def create_meal(
    payload: MealCreateRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    all_photo_ids = [photo_id for ids in payload.photo_ids.values() for photo_id in ids]
    missing = _validate_photo_ids(db, all_photo_ids)
    if missing:
        return fail(f"照片不存在: {missing}", code=40402, status_code=404)

    meal = MealRecord(
        meal_date=payload.meal_date or beijing_date(),
        meal_type=payload.meal_type,
        menu_text=payload.menu_text,
        ingredient_notes=payload.ingredient_notes,
        cooking_notes=payload.cooking_notes,
        hygiene_notes=payload.hygiene_notes,
        overall_remark=payload.overall_remark,
        created_by=current_teacher.id,
    )
    db.add(meal)
    db.flush()

    for step, ids in payload.photo_ids.items():
        for index, photo_id in enumerate(ids):
            db.add(MealPhoto(meal_id=meal.id, photo_id=photo_id, step=step, sort_order=index))
    db.commit()
    db.refresh(meal)
    return ok({"id": meal.id})


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
    meals = db.execute(
        select(MealRecord)
        .order_by(MealRecord.meal_date.desc(), MealRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()
    meal_ids = [meal.id for meal in meals]
    rows = []
    if meal_ids:
        rows = db.execute(
            select(MealPhoto, Photo)
            .join(Photo, Photo.id == MealPhoto.photo_id)
            .where(MealPhoto.meal_id.in_(meal_ids))
            .order_by(MealPhoto.meal_id, MealPhoto.step, MealPhoto.sort_order)
        ).all()

    photos_by_meal: dict[int, dict[str, list[dict]]] = {}
    for meal_photo, photo in rows:
        photos_by_meal.setdefault(meal_photo.meal_id, {})
        photos_by_meal[meal_photo.meal_id].setdefault(meal_photo.step or "general", []).append(_photo_out(photo))

    return ok(
        {
            "records": [
                {
                    "id": meal.id,
                    "date": meal.meal_date.isoformat(),
                    "meal_type": meal.meal_type,
                    "menu": meal.menu_text,
                    "photos": photos_by_meal.get(meal.id, {}),
                    "overall_remark": meal.overall_remark,
                }
                for meal in meals
            ]
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
        .order_by(MealStudentNote.created_at.desc())
    ).all()
    return ok(
        {
            "notes": [
                {
                    "id": note.id,
                    "date": meal.meal_date.isoformat(),
                    "meal_type": meal.meal_type,
                    "remark": note.remark,
                    "photo": _photo_out(photo) if photo else None,
                }
                for note, meal, photo in notes
            ]
        }
    )

