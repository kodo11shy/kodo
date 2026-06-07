from pydantic import BaseModel, Field


class PhotoAssociateRequest(BaseModel):
    student_ids: list[int] = Field(min_length=1)
    photo_type: str = "general"
    remark: str | None = None


class PhotoFeaturedRequest(BaseModel):
    is_featured: bool


class PhotoUpdateRequest(BaseModel):
    photo_type: str | None = None
    remark: str | None = None
    is_featured: bool | None = None


class PhotoBatchOperation(BaseModel):
    operation: str = Field(pattern=r"^(delete|feature|unfeature)$")
    photo_ids: list[int] = Field(min_length=1)


class PhotoBatchAssociate(BaseModel):
    photo_ids: list[int] = Field(min_length=1)
    student_ids: list[int] = Field(min_length=1)
    photo_type: str = "general"
    remark: str | None = None
