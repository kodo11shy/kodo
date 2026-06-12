import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.core.config import settings
from app.core.datetime import now_utc_naive
from app.core.responses import fail, ok
from app.core.security import create_token, verify_password
from app.db.session import get_db
from app.models import Parent, ParentBinding, Student, StudentParent, Teacher
from app.schemas.auth import ParentBindRequest, TeacherBindWechatRequest, TeacherLoginRequest, WechatSessionRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/teacher/login")
def teacher_login(payload: TeacherLoginRequest, db: Session = Depends(get_db)):
    login_id = (payload.phone or "").strip()
    if not login_id:
        return fail("请输入账号或手机号", code=40000, status_code=400)

    query = select(Teacher).where(
        Teacher.is_active.is_(True),
        or_(Teacher.phone == login_id, Teacher.name == login_id),
    )
    teachers = db.execute(query).scalars().all()
    teacher = next(
        (item for item in teachers if verify_password(payload.password, item.login_password)),
        None,
    )
    if teacher is None:
        return fail("账号或密码错误", code=40001, status_code=401)

    token = create_token(
        subject=f"teacher:{teacher.id}",
        extra={"teacher_id": teacher.id, "role": teacher.role},
    )
    return ok(
        {
            "token": token,
            "teacher": {
                "id": teacher.id,
                "name": teacher.name,
                "role": teacher.role,
                "subject": teacher.subject,
                "wechat_bound": bool(teacher.wechat_openid),
            },
        }
    )


@router.post("/wechat/session")
def wechat_session(payload: WechatSessionRequest):
    if settings.wechat_mock_login:
        openid = payload.mock_openid or (f"mock_{payload.code}" if payload.code else None)
        if not openid:
            return fail("开发模式下需要 mock_openid 或 code", code=40003, status_code=400)
        return ok({"openid": openid, "mock": True})

    if not payload.code:
        return fail("缺少微信登录 code", code=40004, status_code=400)
    if not settings.wechat_app_id or not settings.wechat_app_secret:
        return fail("未配置微信小程序 appId/appSecret", code=50001, status_code=500)

    try:
        response = httpx.get(
            "https://api.weixin.qq.com/sns/jscode2session",
            params={
                "appid": settings.wechat_app_id,
                "secret": settings.wechat_app_secret,
                "js_code": payload.code,
                "grant_type": "authorization_code",
            },
            timeout=8,
        )
        data = response.json()
    except Exception:
        return fail("微信登录服务请求失败", code=50201, status_code=502)

    if "openid" not in data:
        return fail(data.get("errmsg", "微信登录失败"), code=40005, status_code=400)
    return ok({"openid": data["openid"], "mock": False})


@router.post("/teacher/bind-wechat")
def teacher_bind_wechat(
    payload: TeacherBindWechatRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    existing = db.execute(
        select(Teacher).where(
            Teacher.wechat_openid == payload.openid,
            Teacher.id != current_teacher.id,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return fail("该微信已绑定其他老师", code=40006, status_code=400)

    current_teacher.wechat_openid = payload.openid
    current_teacher.updated_at = now_utc_naive()
    db.commit()
    return ok({"teacher_id": current_teacher.id, "wechat_bound": True})


@router.post("/parent/bind")
def parent_bind(payload: ParentBindRequest, db: Session = Depends(get_db)):
    parent = db.execute(
        select(Parent).where(Parent.invite_code == payload.invite_code)
    ).scalar_one_or_none()
    if parent is None:
        return fail("邀请码无效", code=40002, status_code=400)

    parent.wechat_openid = payload.wechat_openid
    binding = db.execute(
        select(ParentBinding).where(ParentBinding.wechat_openid == payload.wechat_openid)
    ).scalar_one_or_none()
    if binding is None:
        db.add(ParentBinding(parent_id=parent.id, wechat_openid=payload.wechat_openid))
    else:
        binding.parent_id = parent.id
        binding.is_active = True
    db.commit()

    student_ids = db.execute(
        select(StudentParent.student_id)
        .join(Student, Student.id == StudentParent.student_id)
        .where(
            StudentParent.parent_id == parent.id,
            StudentParent.is_authorized.is_(True),
            Student.status == "在读",
            Student.is_active.is_(True),
        )
    ).scalars().all()
    token = create_token(subject=f"parent:{parent.id}", extra={"parent_id": parent.id, "role": "parent"})
    return ok({"token": token, "student_ids": student_ids})


@router.get("/parent/auto-login")
def parent_auto_login(wechat_openid: str, db: Session = Depends(get_db)):
    binding = db.execute(
        select(ParentBinding).where(
            ParentBinding.wechat_openid == wechat_openid,
            ParentBinding.is_active.is_(True),
        )
    ).scalar_one_or_none()
    if binding is None:
        return fail("未绑定", code=40103, status_code=401)

    parent = db.get(Parent, binding.parent_id)
    if parent is None:
        return fail("账号不可用", code=40102, status_code=401)
    student_ids = db.execute(
        select(StudentParent.student_id)
        .join(Student, Student.id == StudentParent.student_id)
        .where(
            StudentParent.parent_id == parent.id,
            StudentParent.is_authorized.is_(True),
            Student.status == "在读",
            Student.is_active.is_(True),
        )
    ).scalars().all()
    students = db.execute(select(Student).where(Student.id.in_(student_ids))).scalars().all()
    token = create_token(subject=f"parent:{parent.id}", extra={"parent_id": parent.id, "role": "parent"})
    return ok(
        {
            "token": token,
            "parents": [{"id": parent.id, "name": parent.name, "relation": parent.relation}],
            "students": [{"id": student.id, "name": student.name, "grade": student.grade} for student in students],
        }
    )
