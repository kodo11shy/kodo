from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine

router = APIRouter(prefix="/health", tags=["health"])


def _check_database() -> tuple[bool, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
        return True, "connected"
    except Exception as exc:
        return False, str(exc)


def _check_upload_dir() -> tuple[bool, str]:
    try:
        upload_root = settings.resolved_upload_root()
        upload_root.mkdir(parents=True, exist_ok=True)
        probe = upload_root / ".healthcheck"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True, str(upload_root)
    except Exception as exc:
        return False, str(exc)


@router.get("")
def health_check():
    database_ok, database_message = _check_database()
    upload_ok, upload_message = _check_upload_dir()
    healthy = database_ok and upload_ok

    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "ok" if healthy else "error",
            "service": settings.app_name,
            "env": settings.app_env,
            "checks": {
                "database": {
                    "ok": database_ok,
                    "message": database_message,
                    "dialect": engine.dialect.name,
                },
                "upload_dir": {
                    "ok": upload_ok,
                    "message": upload_message,
                },
            },
        },
    )
