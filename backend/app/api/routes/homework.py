from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.core.datetime import beijing_date, now_utc_naive
from app.core.homework_rules import ALLOWED_HOMEWORK_SUBJECTS, is_allowed_homework_subject
from app.core.responses import fail, ok
from app.db.session import get_db
from app.models import AttendanceRecord, HomeworkPhoto, HomeworkRecord, Photo, Student, Teacher
from app.schemas.homework import HomeworkCorrectRequest, HomeworkCreateRequest, HomeworkGradeRequest

router = APIRouter(prefix="/homework", tags=["homework"])


def _get_active_student(db: Session, student_id: int) -> Student | None:
    student = db.get(Student, student_id)
    if student is None or not student.is_active:
        return None
    return student


def _validate_photos(db: Session, photo_ids: list[int]):
    photos = db.execute(select(Photo).where(Photo.id.in_(photo_ids))).scalars().all()
    existing_ids = {photo.id for photo in photos}
    missing_ids = [photo_id for photo_id in photo_ids if photo_id not in existing_ids]
    if missing_ids:
        return None, missing_ids
    return photos, []


def _add_homework_photos(db: Session, homework_id: int, photo_ids: list[int], step: str) -> None:
    for index, photo_id in enumerate(photo_ids):
        db.add(
            HomeworkPhoto(
                homework_id=homework_id,
                photo_id=photo_id,
                step=step,
                sort_order=index,
            )
        )


def _merge_remark(existing: str | None, label: str, remark: str | None) -> str | None:
    if not remark:
        return existing
    line = f"{label}: {remark}"
    return line if not existing else f"{existing}\n{line}"


def _photo_out(photo: Photo) -> dict:
    return {
        "id": photo.id,
        "file_path": photo.file_path,
        "thumbnail": photo.thumbnail_path,
        "taken_at": photo.taken_at.isoformat() if photo.taken_at else None,
        "remark": photo.remark,
    }


def _get_teacher_name_map(db: Session) -> dict[int, str]:
    """Return {teacher_id: teacher_name} for all active teachers."""
    teachers = db.execute(select(Teacher).where(Teacher.is_active.is_(True))).scalars().all()
    return {t.id: t.name for t in teachers}


@router.post("")
def create_homework(
    payload: HomeworkCreateRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    if _get_active_student(db, payload.student_id) is None:
        return fail("学生不存在", code=40401, status_code=404)

    photos, missing_ids = _validate_photos(db, payload.photo_ids)
    if missing_ids:
        return fail(f"照片不存在: {missing_ids}", code=40402, status_code=404)

    # 非管理员老师，学科锁定为老师自己的学科，避免前端误传造成串科。
    if current_teacher.role == "admin":
        subject = payload.subject
    else:
        if not current_teacher.subject:
            return fail("当前老师未配置学科，请联系管理员", code=40008, status_code=400)
        subject = current_teacher.subject

    if not is_allowed_homework_subject(subject):
        return fail("作业科目只能是语文或数学", code=40009, status_code=400)

    homework_date = payload.homework_date or beijing_date()
    checked_in = db.execute(
        select(AttendanceRecord.id).where(
            AttendanceRecord.student_id == payload.student_id,
            AttendanceRecord.date == homework_date,
        )
    ).scalar_one_or_none()
    if checked_in is None:
        return fail("只能给当天已签到学生新建作业", code=40010, status_code=400)

    duplicated = db.execute(
        select(HomeworkRecord.id).where(
            HomeworkRecord.student_id == payload.student_id,
            HomeworkRecord.subject == subject,
            HomeworkRecord.homework_date == homework_date,
        )
    ).scalar_one_or_none()
    if duplicated is not None:
        return fail("该学生今天已提交该科目作业", code=40011, status_code=400)

    record = HomeworkRecord(
        student_id=payload.student_id,
        subject=subject,
        homework_type=payload.homework_type,
        completion_status="待批改",
        teacher_remark=_merge_remark(None, "完成", payload.remark),
        recorded_by=current_teacher.id,
        homework_date=homework_date,
    )
    db.add(record)
    db.flush()
    _add_homework_photos(db, record.id, payload.photo_ids, "done")
    db.commit()
    db.refresh(record)
    return ok({"id": record.id, "status": record.completion_status})


@router.put("/{homework_id}/grade")
def grade_homework(
    homework_id: int,
    payload: HomeworkGradeRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    record = db.get(HomeworkRecord, homework_id)
    if record is None:
        return fail("作业记录不存在", code=40403, status_code=404)

    photos, missing_ids = _validate_photos(db, payload.photo_ids)
    if missing_ids:
        return fail(f"照片不存在: {missing_ids}", code=40402, status_code=404)

    record.completion_status = "已批改"
    record.accuracy_status = payload.accuracy_status
    record.error_count = payload.error_count
    record.score = payload.score
    record.graded_by = current_teacher.id
    record.graded_at = now_utc_naive()
    record.teacher_remark = _merge_remark(record.teacher_remark, "批改", payload.remark)
    record.updated_at = now_utc_naive()
    _add_homework_photos(db, record.id, payload.photo_ids, "graded")
    db.commit()
    return ok({"id": record.id, "status": record.completion_status})


@router.put("/{homework_id}/correct")
def correct_homework(
    homework_id: int,
    payload: HomeworkCorrectRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    record = db.get(HomeworkRecord, homework_id)
    if record is None:
        return fail("作业记录不存在", code=40403, status_code=404)

    photos, missing_ids = _validate_photos(db, payload.photo_ids)
    if missing_ids:
        return fail(f"照片不存在: {missing_ids}", code=40402, status_code=404)

    record.completion_status = "已完成"
    record.corrected_by = current_teacher.id
    record.corrected_at = now_utc_naive()
    record.teacher_remark = _merge_remark(record.teacher_remark, "改错", payload.remark)
    record.completed_at = now_utc_naive()
    record.updated_at = now_utc_naive()
    _add_homework_photos(db, record.id, payload.photo_ids, "corrected")
    db.commit()
    return ok({"id": record.id, "status": record.completion_status})


@router.get("")
def list_homework(
    student_id: int | None = Query(default=None),
    subject: str | None = Query(default=None),
    homework_date: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    query = select(HomeworkRecord).where(HomeworkRecord.subject.in_(ALLOWED_HOMEWORK_SUBJECTS))

    if student_id is not None:
        query = query.where(HomeworkRecord.student_id == student_id)

    if subject is not None:
        if subject not in ALLOWED_HOMEWORK_SUBJECTS:
            return ok({"records": []})
        query = query.where(HomeworkRecord.subject == subject)
    elif current_teacher.role != "admin" and current_teacher.subject:
        # 非管理员老师，只看到自己学科的作业
        query = query.where(HomeworkRecord.subject == current_teacher.subject)

    if homework_date is not None:
        query = query.where(HomeworkRecord.homework_date == homework_date)

    records = db.execute(
        query.order_by(HomeworkRecord.homework_date.desc(), HomeworkRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    if not records:
        return ok({"records": []})

    record_ids = [record.id for record in records]
    rows = db.execute(
        select(HomeworkPhoto, Photo)
        .join(Photo, Photo.id == HomeworkPhoto.photo_id)
        .where(HomeworkPhoto.homework_id.in_(record_ids))
        .order_by(HomeworkPhoto.homework_id, HomeworkPhoto.step, HomeworkPhoto.sort_order)
    ).all()

    photos_by_record: dict[int, dict[str, list[dict]]] = {
        record_id: {"done": [], "graded": [], "corrected": []} for record_id in record_ids
    }
    for homework_photo, photo in rows:
        photos_by_record.setdefault(homework_photo.homework_id, {"done": [], "graded": [], "corrected": []})
        photos_by_record[homework_photo.homework_id].setdefault(homework_photo.step, []).append(_photo_out(photo))

    student_ids = {record.student_id for record in records}
    students = db.execute(select(Student).where(Student.id.in_(student_ids))).scalars().all()
    student_names = {student.id: student.name for student in students}

    # 获取老师姓名映射（用于审计显示）
    teacher_names = _get_teacher_name_map(db)

    return ok(
        {
            "records": [
                {
                    "id": record.id,
                    "student_id": record.student_id,
                    "student_name": student_names.get(record.student_id),
                    "date": record.homework_date.isoformat(),
                    "subject": record.subject,
                    "homework_type": record.homework_type,
                    "status": record.completion_status,
                    "accuracy": record.accuracy_status,
                    "error_count": record.error_count,
                    "score": record.score,
                    "photos": photos_by_record.get(record.id, {"done": [], "graded": [], "corrected": []}),
                    "remark": record.teacher_remark,
                    "completed_at": record.completed_at.isoformat() if record.completed_at else None,
                    "recorded_by": record.recorded_by,
                    "graded_by": record.graded_by,
                    "corrected_by": record.corrected_by,
                    "graded_at": record.graded_at.isoformat() if record.graded_at else None,
                    "corrected_at": record.corrected_at.isoformat() if record.corrected_at else None,
                    "recorded_by_name": teacher_names.get(record.recorded_by) if record.recorded_by else None,
                    "graded_by_name": teacher_names.get(record.graded_by) if record.graded_by else None,
                    "corrected_by_name": teacher_names.get(record.corrected_by) if record.corrected_by else None,
                }
                for record in records
            ]
        }
    )
