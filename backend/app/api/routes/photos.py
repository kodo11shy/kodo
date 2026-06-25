from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.core.config import settings
from app.core.datetime import BEIJING_TZ, now_utc_naive
from app.core.responses import fail, ok
from app.core.uploads import public_upload_path
from app.db.session import get_db
from app.models import Photo, PhotoStudent, Student, Teacher
from app.schemas.photo import (
    PhotoAssociateRequest,
    PhotoBatchAssociate,
    PhotoBatchOperation,
    PhotoFeaturedRequest,
    PhotoUpdateRequest,
)

try:
    from PIL import Image

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

router = APIRouter(prefix="/photos", tags=["photos"])

ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
STUDENT_REQUIRED_PHOTO_TYPES = {"homework"}


def _delete_photo_file(photo: Photo) -> None:
    """Delete the physical file from disk."""
    try:
        relative_path = photo.file_path
        if relative_path.startswith("/uploads/"):
            relative_path = relative_path[len("/uploads/"):]
        disk_path = settings.resolved_upload_root() / relative_path
        if disk_path.exists():
            disk_path.unlink()
        if photo.thumbnail_path:
            thumb_path = photo.thumbnail_path
            if thumb_path.startswith("/uploads/"):
                thumb_path = thumb_path[len("/uploads/"):]
            thumb_disk = settings.resolved_upload_root() / thumb_path
            if thumb_disk.exists():
                thumb_disk.unlink()
    except OSError:
        pass


def _photo_out(photo: Photo) -> dict:
    return {
        "id": photo.id,
        "file_path": public_upload_path(photo.file_path),
        "thumbnail": public_upload_path(photo.thumbnail_path),
        "photo_type": photo.photo_type,
        "is_featured": photo.is_featured,
        "taken_at": photo.taken_at.isoformat() if photo.taken_at else None,
        "remark": photo.remark,
    }


def _validate_student_ids(db: Session, student_ids: list[int]) -> tuple[set[int], list[int]]:
    if not student_ids:
        return set(), []
    students = db.execute(
        select(Student).where(Student.id.in_(student_ids), Student.is_active.is_(True))
    ).scalars().all()
    valid_ids = {student.id for student in students}
    missing_ids = [student_id for student_id in student_ids if student_id not in valid_ids]
    return valid_ids, missing_ids


@router.post("/upload")
def upload_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    suffix = ALLOWED_IMAGE_TYPES.get(file.content_type or "")
    if suffix is None:
        original_suffix = Path(file.filename or "").suffix.lower()
        suffix = original_suffix if original_suffix in {".jpg", ".jpeg", ".png", ".webp"} else None
    if suffix is None:
        return fail("只支持 jpg/png/webp 图片", code=41501, status_code=415)

    today = datetime.now(BEIJING_TZ)
    relative_dir = Path("photos") / today.strftime("%Y") / today.strftime("%m") / today.strftime("%d")
    upload_dir = settings.resolved_upload_root() / relative_dir
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}{suffix}"
    disk_path = upload_dir / filename
    size = 0
    with disk_path.open("wb") as output:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            output.write(chunk)

    public_path = public_upload_path(str(Path("uploads") / relative_dir / filename))

    # Generate thumbnail (480px max side) if Pillow is available
    thumb_public_path = None
    if HAS_PILLOW:
        try:
            thumb_filename = f"{Path(filename).stem}_thumb{suffix}"
            thumb_disk_path = upload_dir / thumb_filename
            img = Image.open(disk_path)
            max_size = 480
            w, h = img.size
            if w > max_size or h > max_size:
                if w > h:
                    new_w = max_size
                    new_h = int(h * max_size / w)
                else:
                    new_h = max_size
                    new_w = int(w * max_size / h)
                img = img.resize((new_w, new_h), Image.LANCZOS)
            img.save(thumb_disk_path, quality=85)
            thumb_public_path = public_upload_path(
                str(Path("uploads") / relative_dir / thumb_filename)
            )
        except Exception:
            thumb_public_path = None  # Thumbnail failed, fall back to original

    photo = Photo(
        file_path=public_path,
        thumbnail_path=thumb_public_path,
        original_name=file.filename,
        file_size=size,
        photo_type="general",
        taken_by=current_teacher.id,
        taken_at=now_utc_naive(),
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)

    return ok({"photo_id": photo.id, "file_path": public_upload_path(photo.file_path), "thumbnail": public_upload_path(photo.thumbnail_path)})


@router.get("")
def list_photos(
    student_id: int | None = Query(default=None),
    type: str | None = Query(default=None),
    associated: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    query = select(Photo)
    if student_id is not None:
        query = query.join(PhotoStudent, PhotoStudent.photo_id == Photo.id).where(
            PhotoStudent.student_id == student_id
        )
    if type:
        query = query.where(Photo.photo_type == type)
    if associated is not None:
        subq = select(PhotoStudent.photo_id).distinct()
        if associated:
            query = query.where(Photo.id.in_(subq))
        else:
            query = query.where(~Photo.id.in_(subq))

    # Build count query (same filters, no pagination)
    count_q = select(Photo.id)
    if student_id is not None:
        count_q = count_q.join(PhotoStudent, PhotoStudent.photo_id == Photo.id).where(
            PhotoStudent.student_id == student_id
        )
    if type:
        count_q = count_q.where(Photo.photo_type == type)
    if associated is not None:
        subq = select(PhotoStudent.photo_id).distinct()
        if associated:
            count_q = count_q.where(Photo.id.in_(subq))
        else:
            count_q = count_q.where(~Photo.id.in_(subq))
    total = len(db.execute(count_q).scalars().all())

    photos = db.execute(
        query.order_by(Photo.taken_at.desc(), Photo.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()
    return ok({"photos": [_photo_out(photo) for photo in photos], "total": total})


@router.get("/featured")
def featured_photos(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    photos = db.execute(
        select(Photo)
        .where(Photo.is_featured.is_(True))
        .order_by(Photo.taken_at.desc(), Photo.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()
    return ok({"photos": [_photo_out(photo) for photo in photos]})


@router.post("/batch")
def batch_operation(
    payload: PhotoBatchOperation,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    photos = db.execute(select(Photo).where(Photo.id.in_(payload.photo_ids))).scalars().all()
    if not photos:
        return fail("未找到任何照片", code=40402, status_code=404)
    ids = [p.id for p in photos]

    if payload.operation == "delete":
        for photo in photos:
            _delete_photo_file(photo)
        db.query(PhotoStudent).filter(PhotoStudent.photo_id.in_(ids)).delete(
            synchronize_session=False
        )
        db.query(Photo).filter(Photo.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return ok({"deleted": len(photos)})
    if payload.operation == "feature":
        db.query(Photo).filter(Photo.id.in_(ids)).update(
            {"is_featured": True}, synchronize_session=False
        )
        db.commit()
        return ok({"updated": len(photos)})
    if payload.operation == "unfeature":
        db.query(Photo).filter(Photo.id.in_(ids)).update(
            {"is_featured": False}, synchronize_session=False
        )
        db.commit()
        return ok({"updated": len(photos)})
    return fail("不支持的操作", code=40001)


@router.post("/batch/associate")
def batch_associate(
    payload: PhotoBatchAssociate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    photos = db.execute(select(Photo).where(Photo.id.in_(payload.photo_ids))).scalars().all()
    if not photos:
        return fail("未找到任何照片", code=40402, status_code=404)
    if payload.photo_type in STUDENT_REQUIRED_PHOTO_TYPES and not payload.student_ids:
        return fail("作业照片需要选择学生", code=40002, status_code=400)
    _, missing = _validate_student_ids(db, payload.student_ids)
    if missing:
        return fail(f"学生不存在: {missing}", code=40401, status_code=404)

    is_single = len(payload.student_ids) == 1
    count = 0
    for photo in photos:
        photo.photo_type = payload.photo_type
        if payload.remark is not None:
            photo.remark = payload.remark
        existing = set(
            db.execute(
                select(PhotoStudent.student_id).where(PhotoStudent.photo_id == photo.id)
            )
            .scalars()
            .all()
        )
        for sid in payload.student_ids:
            if sid not in existing:
                db.add(PhotoStudent(photo_id=photo.id, student_id=sid, is_main=is_single))
                count += 1
    db.commit()
    return ok({"updated_photos": len(photos), "new_associations": count})


@router.put("/{photo_id}/featured")
def update_featured(
    photo_id: int,
    payload: PhotoFeaturedRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    photo = db.get(Photo, photo_id)
    if photo is None:
        return fail("照片不存在", code=40402, status_code=404)
    photo.is_featured = payload.is_featured
    db.commit()
    return ok({"ok": True})


@router.post("/{photo_id}/associate")
def associate_photo(
    photo_id: int,
    payload: PhotoAssociateRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    photo = db.get(Photo, photo_id)
    if photo is None:
        return fail("照片不存在", code=40402, status_code=404)
    if payload.photo_type in STUDENT_REQUIRED_PHOTO_TYPES and not payload.student_ids:
        return fail("作业照片需要选择学生", code=40002, status_code=400)

    _, missing_ids = _validate_student_ids(db, payload.student_ids)
    if missing_ids:
        return fail(f"学生不存在: {missing_ids}", code=40401, status_code=404)

    photo.photo_type = payload.photo_type
    photo.remark = payload.remark

    existing_ids = set(
        db.execute(select(PhotoStudent.student_id).where(PhotoStudent.photo_id == photo.id)).scalars().all()
    )
    is_single = len(payload.student_ids) == 1
    for student_id in payload.student_ids:
        if student_id in existing_ids:
            continue
        db.add(PhotoStudent(photo_id=photo.id, student_id=student_id, is_main=is_single))

    db.commit()
    return ok({"ok": True})


@router.put("/{photo_id}")
def update_photo(
    photo_id: int,
    payload: PhotoUpdateRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    photo = db.get(Photo, photo_id)
    if photo is None:
        return fail("照片不存在", code=40402, status_code=404)
    if payload.photo_type is not None:
        photo.photo_type = payload.photo_type
    if payload.remark is not None:
        photo.remark = payload.remark
    if payload.is_featured is not None:
        photo.is_featured = payload.is_featured
    db.commit()
    db.refresh(photo)
    return ok({"photo": _photo_out(photo)})


@router.delete("/{photo_id}")
def delete_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    photo = db.get(Photo, photo_id)
    if photo is None:
        return fail("照片不存在", code=40402, status_code=404)
    _delete_photo_file(photo)
    db.query(PhotoStudent).filter(PhotoStudent.photo_id == photo.id).delete()
    db.delete(photo)
    db.commit()
    return ok({"ok": True})
