from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PaymentCreateRequest(BaseModel):
    student_id: int
    fee_type: str = Field(min_length=1, max_length=30)
    amount: Decimal
    period_start: date | None = None
    period_end: date | None = None
    status: str = "未缴"
    payment_method: str | None = None
    remark: str | None = None
    paid_at: datetime | None = None

