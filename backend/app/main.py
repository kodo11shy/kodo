from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.core.responses import ApiError, fail, ok
from app.db.init_db import create_tables, seed_default_config, seed_default_teacher
from app.db.session import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.auto_create_tables:
        create_tables()
        with SessionLocal() as db:
            seed_default_teacher(db)
            seed_default_config(db)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)
settings.resolved_upload_root().mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.resolved_upload_root()), name="uploads")


@app.get("/")
def root():
    return ok({"service": settings.app_name, "env": settings.app_env})


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return fail(exc.message, code=exc.code, status_code=exc.status_code)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return fail("服务器内部错误", code=50000, status_code=500)
