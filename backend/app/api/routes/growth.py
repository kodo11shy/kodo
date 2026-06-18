import json
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.core.datetime import beijing_date, now_utc_naive
from app.core.responses import fail, ok
from app.db.session import get_db
from app.models import (
    AttendanceRecord,
    GrowthObservation,
    GrowthObservationDraft,
    GrowthObservationSource,
    HomeworkRecord,
    MealRecord,
    MealStudentNote,
    Photo,
    PhotoStudent,
    Student,
    Teacher,
    TeacherRemark,
)
from app.schemas.growth_observation import (
    GrowthObservationConfirmRequest,
    GrowthObservationDraftCreateRequest,
    GrowthObservationDraftReviewRequest,
    GrowthObservationUpdateRequest,
)

router = APIRouter(prefix="/growth", tags=["growth"])


def _json_dump(value: list[str] | list[dict] | None) -> str:
    return json.dumps(value or [], ensure_ascii=False, separators=(",", ":"))


def _json_load_list(value: str | None) -> list:
    if not value:
        return []
    try:
        loaded = json.loads(value)
    except (TypeError, ValueError):
        return []
    return loaded if isinstance(loaded, list) else []


def _get_active_student(db: Session, student_id: int) -> Student | None:
    student = db.get(Student, student_id)
    if student is None or not student.is_active:
        return None
    return student


def _date_from_datetime(value: object | None) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return beijing_date()


def _photo_out(photo: Photo) -> dict:
    return {
        "id": photo.id,
        "file_path": photo.file_path,
        "thumbnail": photo.thumbnail_path,
        "photo_type": photo.photo_type,
        "remark": photo.remark,
    }


def _event(
    *,
    source_type: str,
    source_id: int,
    event_date: date,
    title: str,
    description: str | None = None,
    score: int | None = None,
    tags: list[str] | None = None,
    photos: list[dict] | None = None,
    parent_visible: bool = True,
) -> dict:
    return {
        "date": event_date.isoformat(),
        "type": source_type,
        "source_type": source_type,
        "source_id": source_id,
        "title": title,
        "description": description,
        "score": score,
        "tags": tags or [],
        "photos": photos or [],
        "parent_visible": parent_visible,
    }


def _archive_events(
    db: Session,
    student_id: int,
    start_date: date,
    include_private: bool = True,
) -> list[dict]:
    events: list[dict] = []

    attendance_rows = db.execute(
        select(AttendanceRecord)
        .where(AttendanceRecord.student_id == student_id, AttendanceRecord.date >= start_date)
        .order_by(AttendanceRecord.date.desc(), AttendanceRecord.id.desc())
    ).scalars().all()
    for record in attendance_rows:
        checkin = record.checkin_time.isoformat(timespec="minutes") if record.checkin_time else None
        checkout = record.checkout_time.isoformat(timespec="minutes") if record.checkout_time else None
        description = " / ".join(part for part in [f"签到 {checkin}" if checkin else None, f"签退 {checkout}" if checkout else None] if part)
        events.append(
            _event(
                source_type="attendance",
                source_id=record.id,
                event_date=record.date,
                title="到班记录",
                description=description or "已记录到班情况",
                tags=["出勤"],
            )
        )

    homework_rows = db.execute(
        select(HomeworkRecord)
        .where(HomeworkRecord.student_id == student_id, HomeworkRecord.homework_date >= start_date)
        .order_by(HomeworkRecord.homework_date.desc(), HomeworkRecord.id.desc())
    ).scalars().all()
    for record in homework_rows:
        title_parts = [record.subject, record.completion_status]
        if record.accuracy_status:
            title_parts.append(record.accuracy_status)
        events.append(
            _event(
                source_type="homework",
                source_id=record.id,
                event_date=record.homework_date,
                title=" · ".join(part for part in title_parts if part),
                description=record.teacher_remark,
                score=record.score,
                tags=["作业"],
            )
        )

    remark_rows = db.execute(
        select(TeacherRemark)
        .where(TeacherRemark.student_id == student_id, TeacherRemark.record_date >= start_date)
        .order_by(TeacherRemark.record_date.desc(), TeacherRemark.id.desc())
    ).scalars().all()
    for remark in remark_rows:
        events.append(
            _event(
                source_type="remark",
                source_id=remark.id,
                event_date=remark.record_date,
                title="老师评语",
                description=remark.content,
                tags=[remark.mood_tag] if remark.mood_tag else ["评语"],
            )
        )

    meal_rows = db.execute(
        select(MealStudentNote, MealRecord)
        .join(MealRecord, MealRecord.id == MealStudentNote.meal_id)
        .where(MealStudentNote.student_id == student_id, MealRecord.meal_date >= start_date)
        .order_by(MealRecord.meal_date.desc(), MealStudentNote.id.desc())
    ).all()
    for note, meal in meal_rows:
        events.append(
            _event(
                source_type="meal",
                source_id=note.id,
                event_date=meal.meal_date,
                title="今日餐食",
                description=note.remark or meal.overall_remark or meal.menu_text,
                tags=["餐食"],
            )
        )

    photo_rows = db.execute(
        select(Photo)
        .join(PhotoStudent, PhotoStudent.photo_id == Photo.id)
        .where(PhotoStudent.student_id == student_id)
        .order_by(Photo.taken_at.desc(), Photo.id.desc())
        .limit(200)
    ).scalars().all()
    for photo in photo_rows:
        event_date = _date_from_datetime(photo.taken_at)
        if event_date < start_date:
            continue
        events.append(
            _event(
                source_type="photo",
                source_id=photo.id,
                event_date=event_date,
                title="照片记录",
                description=photo.remark,
                tags=[photo.photo_type or "photo"],
                photos=[_photo_out(photo)],
            )
        )

    observation_query = select(GrowthObservation).where(
        GrowthObservation.student_id == student_id,
        GrowthObservation.observation_date >= start_date,
        GrowthObservation.status != "rejected",
    )
    if not include_private:
        observation_query = observation_query.where(GrowthObservation.parent_visible.is_(True))
    observations = db.execute(
        observation_query.order_by(GrowthObservation.observation_date.desc(), GrowthObservation.id.desc())
    ).scalars().all()
    for observation in observations:
        events.append(
            _event(
                source_type="observation",
                source_id=observation.id,
                event_date=observation.observation_date,
                title=observation.title,
                description=observation.content,
                tags=_json_load_list(observation.dimension_tags),
                parent_visible=observation.parent_visible,
            )
        )

    events.sort(key=lambda item: (item["date"], item["source_type"], item["source_id"]), reverse=True)
    return events


def _archive_summary(events: list[dict]) -> dict:
    by_type: dict[str, int] = {}
    for item in events:
        by_type[item["source_type"]] = by_type.get(item["source_type"], 0) + 1
    return {"total": len(events), "by_type": by_type}


def _source_from_event(
    event: dict,
    *,
    student_id: int,
    draft_id: int | None = None,
    observation_id: int | None = None,
) -> GrowthObservationSource:
    return GrowthObservationSource(
        student_id=student_id,
        source_type=event["source_type"],
        source_id=int(event["source_id"]),
        source_date=date.fromisoformat(event["date"]),
        title=event.get("title"),
        summary=event.get("description"),
        draft_id=draft_id,
        observation_id=observation_id,
    )


def _source_out(source: GrowthObservationSource) -> dict:
    return {
        "id": source.id,
        "source_type": source.source_type,
        "source_id": source.source_id,
        "date": source.source_date.isoformat(),
        "title": source.title,
        "summary": source.summary,
    }


def _draft_out(db: Session, draft: GrowthObservationDraft) -> dict:
    sources = db.execute(
        select(GrowthObservationSource)
        .where(GrowthObservationSource.draft_id == draft.id)
        .order_by(GrowthObservationSource.source_date.desc(), GrowthObservationSource.id.desc())
    ).scalars().all()
    return {
        "id": draft.id,
        "student_id": draft.student_id,
        "period_start": draft.period_start.isoformat(),
        "period_end": draft.period_end.isoformat(),
        "title": draft.title,
        "summary": draft.summary,
        "suggested_content": draft.suggested_content,
        "suggested_tags": _json_load_list(draft.suggested_tags),
        "source_count": draft.source_count,
        "status": draft.status,
        "sources": [_source_out(source) for source in sources],
        "created_at": draft.created_at.isoformat() if draft.created_at else None,
    }


def _observation_out(db: Session, observation: GrowthObservation) -> dict:
    sources = db.execute(
        select(GrowthObservationSource)
        .where(GrowthObservationSource.observation_id == observation.id)
        .order_by(GrowthObservationSource.source_date.desc(), GrowthObservationSource.id.desc())
    ).scalars().all()
    return {
        "id": observation.id,
        "student_id": observation.student_id,
        "date": observation.observation_date.isoformat(),
        "title": observation.title,
        "content": observation.content,
        "dimension_tags": _json_load_list(observation.dimension_tags),
        "parent_visible": observation.parent_visible,
        "source_draft_id": observation.source_draft_id,
        "status": observation.status,
        "sources": [_source_out(source) for source in sources],
        "created_at": observation.created_at.isoformat() if observation.created_at else None,
        "updated_at": observation.updated_at.isoformat() if observation.updated_at else None,
    }


def _build_candidate_text(student: Student, events: list[dict], period_start: date, period_end: date) -> tuple[str, str, list[str]]:
    if not events:
        return (
            f"{student.name} 暂无可整理的成长记录",
            "本周期内还没有足够的签到、作业、照片、餐食或评语记录，可等日常数据自然积累后再生成观察。",
            ["待观察"],
        )

    by_type = _archive_summary(events)["by_type"]
    tags = []
    if by_type.get("homework"):
        tags.append("学习")
    if by_type.get("meal") or by_type.get("attendance"):
        tags.append("生活")
    if by_type.get("photo") or by_type.get("remark"):
        tags.append("日常表现")
    tags = tags or ["成长记录"]

    lines = [
        f"本候选观察整理了 {period_start.isoformat()} 至 {period_end.isoformat()} 期间的 {len(events)} 条日常记录。",
        "可参考来源包括：" + "、".join(f"{key} {value} 条" for key, value in by_type.items()),
    ]
    for event in events[:6]:
        detail = f"- {event['date']} {event['title']}"
        if event.get("description"):
            detail += f"：{event['description']}"
        lines.append(detail)

    summary = "；".join(f"{key} {value} 条" for key, value in by_type.items())
    return summary, "\n".join(lines), tags


@router.get("/overview/{student_id}")
def growth_overview(
    student_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    student = _get_active_student(db, student_id)
    if student is None:
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

    latest_observation = db.execute(
        select(GrowthObservation)
        .where(GrowthObservation.student_id == student_id, GrowthObservation.status != "rejected")
        .order_by(GrowthObservation.observation_date.desc(), GrowthObservation.id.desc())
        .limit(1)
    ).scalar_one_or_none()

    enrollment_days = None
    if student.enrollment_date:
        enrollment_days = (today - student.enrollment_date).days + 1

    avg_score = float(homework_stats[0]) if homework_stats[0] is not None else None
    observation_count = db.execute(
        select(func.count(GrowthObservation.id)).where(
            GrowthObservation.student_id == student_id,
            GrowthObservation.observation_date >= month_start,
            GrowthObservation.observation_date < next_month,
            GrowthObservation.status != "rejected",
        )
    ).scalar_one()
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
                "observation_count": observation_count,
            },
            "latest_remark": latest_remark.content if latest_remark else None,
            "latest_observation": _observation_out(db, latest_observation) if latest_observation else None,
        }
    )


@router.get("/timeline/{student_id}")
def growth_timeline(
    student_id: int,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    student = _get_active_student(db, student_id)
    if student is None:
        return fail("学生不存在", code=40401, status_code=404)

    start_date = beijing_date() - timedelta(days=days)
    timeline = _archive_events(db, student_id, start_date, include_private=True)
    return ok({"timeline": timeline, "summary": _archive_summary(timeline)})


@router.get("/archive/{student_id}")
def growth_archive(
    student_id: int,
    days: int = Query(default=30, ge=1, le=365),
    include_private: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    student = _get_active_student(db, student_id)
    if student is None:
        return fail("学生不存在", code=40401, status_code=404)

    start_date = beijing_date() - timedelta(days=days)
    events = _archive_events(db, student_id, start_date, include_private=include_private)
    return ok(
        {
            "student": {"id": student.id, "name": student.name, "grade": student.grade},
            "period": {"start_date": start_date.isoformat(), "end_date": beijing_date().isoformat(), "days": days},
            "summary": _archive_summary(events),
            "events": events,
        }
    )


@router.post("/observations/drafts")
def create_observation_draft(
    payload: GrowthObservationDraftCreateRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    student = _get_active_student(db, payload.student_id)
    if student is None:
        return fail("学生不存在", code=40401, status_code=404)

    period_end = payload.end_date or beijing_date()
    period_start = payload.start_date or (period_end - timedelta(days=payload.days - 1))
    events = _archive_events(db, payload.student_id, period_start, include_private=True)
    events = [event for event in events if event["source_type"] != "observation" and event["date"] <= period_end.isoformat()]
    if payload.source_types:
        allowed = set(payload.source_types)
        events = [event for event in events if event["source_type"] in allowed]

    summary, content, tags = _build_candidate_text(student, events, period_start, period_end)
    draft = GrowthObservationDraft(
        student_id=payload.student_id,
        period_start=period_start,
        period_end=period_end,
        title=payload.title or f"{student.name}成长观察候选",
        summary=summary,
        suggested_content=content,
        suggested_tags=_json_dump(tags),
        source_count=len(events),
        status="pending",
        created_by=current_teacher.id,
    )
    db.add(draft)
    db.flush()
    for event in events:
        db.add(_source_from_event(event, student_id=payload.student_id, draft_id=draft.id))
    db.commit()
    db.refresh(draft)
    return ok({"draft": _draft_out(db, draft)})


@router.get("/observations/drafts")
def list_observation_drafts(
    student_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    query = select(GrowthObservationDraft)
    if student_id is not None:
        query = query.where(GrowthObservationDraft.student_id == student_id)
    if status:
        query = query.where(GrowthObservationDraft.status == status)
    drafts = db.execute(
        query.order_by(GrowthObservationDraft.created_at.desc(), GrowthObservationDraft.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()
    return ok({"drafts": [_draft_out(db, draft) for draft in drafts]})


@router.put("/observations/drafts/{draft_id}")
def review_observation_draft(
    draft_id: int,
    payload: GrowthObservationDraftReviewRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    draft = db.get(GrowthObservationDraft, draft_id)
    if draft is None:
        return fail("候选观察不存在", code=40408, status_code=404)
    draft.status = payload.status
    draft.reviewed_by = current_teacher.id
    draft.reviewed_at = now_utc_naive()
    draft.updated_at = now_utc_naive()
    db.commit()
    db.refresh(draft)
    return ok({"draft": _draft_out(db, draft)})


@router.post("/observations/confirm")
def confirm_observation(
    payload: GrowthObservationConfirmRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    student = _get_active_student(db, payload.student_id)
    if student is None:
        return fail("学生不存在", code=40401, status_code=404)

    draft = db.get(GrowthObservationDraft, payload.draft_id) if payload.draft_id else None
    if payload.draft_id and draft is None:
        return fail("候选观察不存在", code=40408, status_code=404)

    observation = GrowthObservation(
        student_id=payload.student_id,
        observation_date=payload.observation_date or beijing_date(),
        title=payload.title,
        content=payload.content,
        dimension_tags=_json_dump(payload.dimension_tags),
        parent_visible=payload.parent_visible,
        source_draft_id=draft.id if draft else None,
        status="approved",
        confirmed_by=current_teacher.id,
    )
    db.add(observation)
    db.flush()

    if draft:
        draft.status = "approved"
        draft.reviewed_by = current_teacher.id
        draft.reviewed_at = now_utc_naive()
        draft.updated_at = now_utc_naive()
        draft_sources = db.execute(
            select(GrowthObservationSource).where(GrowthObservationSource.draft_id == draft.id)
        ).scalars().all()
        for source in draft_sources:
            db.add(
                GrowthObservationSource(
                    student_id=source.student_id,
                    source_type=source.source_type,
                    source_id=source.source_id,
                    source_date=source.source_date,
                    title=source.title,
                    summary=source.summary,
                    observation_id=observation.id,
                )
            )
    else:
        for item in payload.source_refs:
            try:
                source_date = date.fromisoformat(str(item.get("date") or item.get("source_date")))
                source_id = int(item.get("source_id"))
            except (TypeError, ValueError):
                continue
            db.add(
                GrowthObservationSource(
                    student_id=payload.student_id,
                    source_type=str(item.get("source_type") or item.get("type") or "manual"),
                    source_id=source_id,
                    source_date=source_date,
                    title=item.get("title"),
                    summary=item.get("summary") or item.get("description"),
                    observation_id=observation.id,
                )
            )

    db.commit()
    db.refresh(observation)
    return ok({"observation": _observation_out(db, observation)})


@router.get("/observations")
def list_observations(
    student_id: int | None = Query(default=None),
    parent_visible: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    query = select(GrowthObservation).where(GrowthObservation.status != "rejected")
    if student_id is not None:
        query = query.where(GrowthObservation.student_id == student_id)
    if parent_visible is not None:
        query = query.where(GrowthObservation.parent_visible.is_(parent_visible))
    observations = db.execute(
        query.order_by(GrowthObservation.observation_date.desc(), GrowthObservation.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()
    return ok({"observations": [_observation_out(db, observation) for observation in observations]})


@router.get("/observations/student/{student_id}")
def student_observations(
    student_id: int,
    parent_visible: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    student = _get_active_student(db, student_id)
    if student is None:
        return fail("学生不存在", code=40401, status_code=404)
    query = select(GrowthObservation).where(
        GrowthObservation.student_id == student_id,
        GrowthObservation.status != "rejected",
    )
    if parent_visible is not None:
        query = query.where(GrowthObservation.parent_visible.is_(parent_visible))
    observations = db.execute(
        query.order_by(GrowthObservation.observation_date.desc(), GrowthObservation.id.desc())
    ).scalars().all()
    return ok({"observations": [_observation_out(db, observation) for observation in observations]})


@router.put("/observations/{observation_id}")
def update_observation(
    observation_id: int,
    payload: GrowthObservationUpdateRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    observation = db.get(GrowthObservation, observation_id)
    if observation is None:
        return fail("成长观察不存在", code=40409, status_code=404)
    if payload.title is not None:
        observation.title = payload.title
    if payload.content is not None:
        observation.content = payload.content
    if payload.dimension_tags is not None:
        observation.dimension_tags = _json_dump(payload.dimension_tags)
    if payload.parent_visible is not None:
        observation.parent_visible = payload.parent_visible
    if payload.status is not None:
        observation.status = payload.status
    observation.updated_at = now_utc_naive()
    db.commit()
    db.refresh(observation)
    return ok({"observation": _observation_out(db, observation)})
