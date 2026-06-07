from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.core.responses import fail, ok
from app.db.session import get_db
from app.models import PaymentRecord, Student, SystemConfig, Teacher
from app.schemas.payment import PaymentCreateRequest

router = APIRouter(prefix="/payments", tags=["payments"])

FEE_CONFIGS = [
    ("tuition_fee", "托管费", "元/月", "周一至周五放学后"),
    ("meal_fee", "餐费", "元/月", "每日一餐两点"),
    ("material_fee", "材料费", "元/学期", "学习材料"),
]


def _payment_out(payment: PaymentRecord, student_name: str | None = None) -> dict:
    result = {
        "id": payment.id,
        "student_id": payment.student_id,
        "fee_type": payment.fee_type,
        "amount": float(payment.amount),
        "period_start": payment.period_start.isoformat() if payment.period_start else None,
        "period_end": payment.period_end.isoformat() if payment.period_end else None,
        "status": payment.status,
        "payment_method": payment.payment_method,
        "remark": payment.remark,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
    }
    if student_name is not None:
        result["student_name"] = student_name
    return result


@router.post("")
def create_payment(
    payload: PaymentCreateRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    student = db.get(Student, payload.student_id)
    if student is None or not student.is_active:
        return fail("学生不存在", code=40401, status_code=404)

    payment = PaymentRecord(
        student_id=payload.student_id,
        fee_type=payload.fee_type,
        amount=payload.amount,
        period_start=payload.period_start,
        period_end=payload.period_end,
        status=payload.status,
        payment_method=payload.payment_method,
        remark=payload.remark,
        paid_at=payload.paid_at,
        recorded_by=current_teacher.id,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return ok({"id": payment.id})


@router.get("/summary")
def payment_summary(
    month: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    query = select(PaymentRecord, Student.name).join(Student, Student.id == PaymentRecord.student_id)
    if month:
        start = f"{month}-01"
        if len(month) == 7:
            year = int(month[:4])
            month_num = int(month[5:7])
            next_year = year + 1 if month_num == 12 else year
            next_month = 1 if month_num == 12 else month_num + 1
            end = f"{next_year:04d}-{next_month:02d}-01"
            query = query.where(PaymentRecord.period_start >= start, PaymentRecord.period_start < end)

    rows = db.execute(query.order_by(PaymentRecord.id.desc())).all()
    details = [_payment_out(payment, student_name) for payment, student_name in rows]
    total_fee = sum(Decimal(str(item["amount"])) for item in details)
    paid = sum(Decimal(str(item["amount"])) for item in details if item["status"] == "已缴")
    unpaid = sum(Decimal(str(item["amount"])) for item in details if item["status"] != "已缴")

    return ok(
        {
            "total_fee": float(total_fee),
            "paid": float(paid),
            "unpaid": float(unpaid),
            "details": details,
        }
    )


@router.get("/fee-standard")
def fee_standard(db: Session = Depends(get_db)):
    configs = {row.config_key: row.config_value or "" for row in db.execute(select(SystemConfig)).scalars().all()}
    return ok(
        {
            "items": [
                {
                    "name": name,
                    "amount": configs.get(key, ""),
                    "unit": unit,
                    "description": description,
                }
                for key, name, unit, description in FEE_CONFIGS
            ]
        }
    )

