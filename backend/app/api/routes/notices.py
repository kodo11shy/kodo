from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.core.datetime import now_utc_naive
from app.core.responses import fail, ok
from app.db.session import get_db
from app.models import Notice, Teacher
from app.schemas.notice import NoticeCreateRequest, NoticeUpdateRequest

router = APIRouter(prefix="/notices", tags=["notices"])


def _notice_out(notice: Notice) -> dict:
    return {
        "id": notice.id,
        "title": notice.title,
        "content": notice.content,
        "notice_type": notice.notice_type,
        "is_pinned": notice.is_pinned,
        "is_active": notice.is_active,
        "display_start": notice.display_start.isoformat() if notice.display_start else None,
        "display_end": notice.display_end.isoformat() if notice.display_end else None,
        "created_at": notice.created_at.isoformat() if notice.created_at else None,
    }


@router.post("")
def create_notice(
    payload: NoticeCreateRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    notice = Notice(
        title=payload.title,
        content=payload.content,
        notice_type=payload.notice_type,
        is_pinned=payload.is_pinned,
        display_start=payload.display_start,
        display_end=payload.display_end,
        created_by=current_teacher.id,
    )
    db.add(notice)
    db.commit()
    db.refresh(notice)
    return ok({"id": notice.id})


@router.get("")
def list_notices(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    include_inactive: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    query = select(Notice)
    if not include_inactive:
        query = query.where(Notice.is_active.is_(True))

    notices = db.execute(
        query.order_by(Notice.is_pinned.desc(), Notice.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()
    return ok({"notices": [_notice_out(notice) for notice in notices]})


@router.put("/{notice_id}")
def update_notice(
    notice_id: int,
    payload: NoticeUpdateRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    notice = db.get(Notice, notice_id)
    if notice is None:
        return fail("通知不存在", code=40404, status_code=404)

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(notice, key, value)
    notice.updated_at = now_utc_naive()
    db.commit()
    db.refresh(notice)
    return ok(_notice_out(notice))


@router.delete("/{notice_id}")
def delete_notice(
    notice_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    notice = db.get(Notice, notice_id)
    if notice is None:
        return fail("通知不存在", code=40404, status_code=404)

    notice.is_active = False
    notice.updated_at = now_utc_naive()
    db.commit()
    return ok({"ok": True})

