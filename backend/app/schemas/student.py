from datetime import date, time

from pydantic import BaseModel, Field


class StudentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    gender: str | None = None
    birth_date: date | None = None
    grade: str | None = None
    school_name: str | None = None
    school_class: str | None = None
    school_end_time: time | None = None
    pickup_method: str | None = None
    address: str | None = None
    enrollment_date: date | None = None
    parent1_name: str | None = None
    parent1_relation: str | None = None
    parent1_phone: str | None = None
    parent2_name: str | None = None
    parent2_relation: str | None = None
    parent2_phone: str | None = None


class StudentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=50)
    gender: str | None = None
    birth_date: date | None = None
    grade: str | None = None
    school_name: str | None = None
    school_class: str | None = None
    school_end_time: time | None = None
    pickup_method: str | None = None
    address: str | None = None
    enrollment_date: date | None = None
    status: str | None = None
    avatar_url: str | None = None
    interests: str | None = None
    personality: str | None = None
    weak_subjects: str | None = None
    notes: str | None = None


class PickupIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    relation: str = Field(min_length=1, max_length=20)
    phone: str = Field(min_length=1, max_length=20)
    id_card: str | None = None
    is_default: bool = False


class PickupsUpdateRequest(BaseModel):
    pickups: list[PickupIn]


class HealthConsentRequest(BaseModel):
    signed: bool
