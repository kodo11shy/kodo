import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_ROOT / ".env")


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_first(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return value
    return default


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "托班管理系统 API")
    app_env: str = os.getenv("APP_ENV", "development")
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/tuoban",
    )
    token_secret: str = _env_first("TOKEN_SECRET", "SECRET_KEY", default="please-change-this-secret")
    token_expire_hours: int = int(os.getenv("TOKEN_EXPIRE_HOURS", "168"))
    default_teacher_name: str = os.getenv("DEFAULT_TEACHER_NAME", "管理员")
    default_teacher_password: str = os.getenv("DEFAULT_TEACHER_PASSWORD", "123456")
    auto_create_tables: bool = _env_bool("AUTO_CREATE_TABLES", True)
    upload_root: str = _env_first("UPLOAD_ROOT", "UPLOAD_DIR", default="uploads")
    wechat_app_id: str = os.getenv("WECHAT_APP_ID", "")
    wechat_app_secret: str = os.getenv("WECHAT_APP_SECRET", "")
    wechat_mock_login: bool = _env_bool("WECHAT_MOCK_LOGIN", True)

    def resolved_upload_root(self) -> Path:
        path = Path(self.upload_root)
        return path if path.is_absolute() else BACKEND_ROOT / path


settings = Settings()
