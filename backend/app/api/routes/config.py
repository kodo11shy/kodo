from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.core.datetime import now_utc_naive
from app.core.responses import ok
from app.db.session import get_db
from app.models import SystemConfig, Teacher
from app.schemas.config import ConfigUpdateRequest

router = APIRouter(prefix="/config", tags=["config"])


@router.get("")
def get_config(
    keys: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    query = select(SystemConfig)
    key_list = [key.strip() for key in keys.split(",") if key.strip()] if keys else []
    if key_list:
        query = query.where(SystemConfig.config_key.in_(key_list))

    rows = db.execute(query).scalars().all()
    return ok({row.config_key: row.config_value for row in rows})


@router.put("")
def update_config(
    payload: ConfigUpdateRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    existing_rows = db.execute(
        select(SystemConfig).where(SystemConfig.config_key.in_(payload.values.keys()))
    ).scalars().all()
    existing_by_key = {row.config_key: row for row in existing_rows}

    for key, value in payload.values.items():
        row = existing_by_key.get(key)
        if row is None:
            db.add(SystemConfig(config_key=key, config_value=value, updated_at=now_utc_naive()))
        else:
            row.config_value = value
            row.updated_at = now_utc_naive()
    db.commit()
    return ok({"ok": True})

