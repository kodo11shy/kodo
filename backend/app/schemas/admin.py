from pydantic import BaseModel, Field


class TeacherCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    role: str = Field(default="teacher", pattern=r"^(admin|teacher)$")
    subject: str | None = Field(default=None, max_length=20)
    wechat_openid: str | None = Field(default=None, max_length=100)


class TeacherUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    phone: str | None = Field(default=None, max_length=20)
    role: str | None = Field(default=None, pattern=r"^(admin|teacher)$")
    subject: str | None = Field(default=None, max_length=20)
    is_active: bool | None = None
    wechat_openid: str | None = Field(default=None, max_length=100)


class TeacherResetPasswordRequest(BaseModel):
    password: str | None = Field(default=None, min_length=1, max_length=100)
