from app.models.attendance import AttendanceRecord
from app.models.homework import HomeworkPhoto, HomeworkRecord
from app.models.meal import MealPhoto, MealRecord, MealStudentNote
from app.models.photo import Photo, PhotoStudent
from app.models.public import Notice, SystemConfig
from app.models.remark_payment import ParentBinding, PaymentRecord, TeacherRemark
from app.models.student import (
    AuthorizedPickup,
    Parent,
    Student,
    StudentHealth,
    StudentParent,
)
from app.models.teacher import Teacher

__all__ = [
    "AttendanceRecord",
    "AuthorizedPickup",
    "HomeworkPhoto",
    "HomeworkRecord",
    "MealPhoto",
    "MealRecord",
    "MealStudentNote",
    "Notice",
    "Parent",
    "ParentBinding",
    "PaymentRecord",
    "Photo",
    "PhotoStudent",
    "Student",
    "StudentHealth",
    "StudentParent",
    "SystemConfig",
    "Teacher",
    "TeacherRemark",
]
