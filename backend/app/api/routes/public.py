import json

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.datetime import beijing_date
from app.core.responses import ok
from app.core.uploads import public_upload_path
from app.db.session import get_db
from app.models import Notice, Photo, SystemConfig

router = APIRouter(prefix="/public", tags=["public"])


FEE_CONFIGS = [
    ("tuition_fee", "托管费", "元/月", "周一至周五放学后"),
    ("meal_fee", "餐费", "元/月", "每日一餐两点"),
    ("material_fee", "材料费", "元/学期", "学习材料"),
]


def _config_map(db: Session) -> dict[str, str]:
    rows = db.execute(select(SystemConfig)).scalars().all()
    return {item.config_key: item.config_value or "" for item in rows}


def _fee_custom_items(configs: dict[str, str]) -> list[dict[str, object]]:
    raw = configs.get("fee_custom_items", "")
    if not raw:
        return []

    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []

    if not isinstance(parsed, list):
        return []

    items: list[dict[str, object]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        item = dict(item)
        item["name"] = name
        items.append(item)
    return items


def _fee_standard(configs: dict[str, str]) -> list[dict[str, str]]:
    custom_items = _fee_custom_items(configs)
    standard_overrides = {
        str(item.get("key")): item
        for item in custom_items
        if item.get("is_standard") and item.get("key")
    }

    fee_standard: list[dict[str, str]] = []
    for key, default_name, default_unit, default_description in FEE_CONFIGS:
        override = standard_overrides.get(key)
        fee_standard.append(
            {
                "name": str(override.get("name") if override else default_name),
                "amount": configs.get(key, ""),
                "unit": str(override.get("unit") if override else default_unit),
                "description": str(
                    override.get("description") if override else default_description
                ),
            }
        )

    for item in custom_items:
        if item.get("is_standard"):
            continue
        fee_standard.append(
            {
                "name": str(item.get("name") or ""),
                "amount": str(item.get("amount") or ""),
                "unit": str(item.get("unit") or ""),
                "description": str(item.get("description") or ""),
            }
        )
    return fee_standard


@router.get("/homepage")
def homepage(db: Session = Depends(get_db)):
    today = beijing_date()
    configs = _config_map(db)

    notices = db.execute(
        select(Notice)
        .where(
            Notice.is_active.is_(True),
            or_(Notice.display_start.is_(None), Notice.display_start <= today),
            or_(Notice.display_end.is_(None), Notice.display_end >= today),
        )
        .order_by(Notice.is_pinned.desc(), Notice.created_at.desc())
        .limit(5)
    ).scalars().all()

    featured_photos = db.execute(
        select(Photo)
        .where(Photo.is_featured.is_(True))
        .order_by(Photo.taken_at.desc())
        .limit(10)
    ).scalars().all()

    fee_standard = _fee_standard(configs)

    return ok(
        {
            "school_name": configs.get("school_name", "智慧托班"),
            "welcome_message": configs.get("welcome_message", "用心陪伴每一个孩子"),
            "contact_wechat": configs.get("contact_wechat", ""),
            "contact_phone": configs.get("contact_phone", ""),
            "notices": [
                {
                    "id": notice.id,
                    "title": notice.title,
                    "content": notice.content,
                    "notice_type": notice.notice_type,
                    "is_pinned": notice.is_pinned,
                }
                for notice in notices
            ],
            "fee_standard": fee_standard,
            "featured_photos": [
                {
                    "id": photo.id,
                    "file_path": public_upload_path(photo.file_path),
                    "thumbnail": public_upload_path(photo.thumbnail_path),
                    "remark": photo.remark,
                }
                for photo in featured_photos
            ],
        }
    )
