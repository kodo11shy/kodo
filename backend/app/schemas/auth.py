from pydantic import BaseModel, Field


class TeacherLoginRequest(BaseModel):
    phone: str | None = Field(default=None, max_length=50)
    password: str = Field(min_length=1)


class TeacherOut(BaseModel):
    id: int
    name: str
    role: str


class TeacherLoginData(BaseModel):
    token: str
    teacher: TeacherOut


class ParentBindRequest(BaseModel):
    invite_code: str = Field(min_length=1)
    wechat_openid: str = Field(min_length=1)


class WechatSessionRequest(BaseModel):
    code: str | None = None
    mock_openid: str | None = None


class TeacherBindWechatRequest(BaseModel):
    openid: str = Field(min_length=1, max_length=100)
