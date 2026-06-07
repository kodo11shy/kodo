from fastapi import APIRouter

from app.api.routes import (
    admin,
    attendance,
    auth,
    config,
    growth,
    health,
    homework,
    meals,
    notices,
    parent,
    payments,
    photos,
    public,
    remarks,
    students,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(students.router)
api_router.include_router(health.router)
api_router.include_router(attendance.router)
api_router.include_router(photos.router)
api_router.include_router(homework.router)
api_router.include_router(public.router)
api_router.include_router(notices.router)
api_router.include_router(config.router)
api_router.include_router(remarks.router)
api_router.include_router(payments.router)
api_router.include_router(growth.router)
api_router.include_router(parent.router)
api_router.include_router(meals.router)
