"""
种子数据脚本 — 生成测试数据供前端联调使用

用法：
    cd backend
    python seed.py

安全重复执行：若检测到已有数据则跳过（可用 --force 强制重新插入）
"""

import argparse
import base64
import io
import os
import random
import secrets
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from uuid import uuid4

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 确保能导入 app 模块
BACKEND_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_ROOT))

# 加载 .env
from dotenv import load_dotenv
load_dotenv(BACKEND_ROOT / ".env")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import hash_password
from app.db.base import Base
from app.db.init_db import seed_default_config, seed_default_teacher
from app.models import (
    AttendanceRecord,
    AuthorizedPickup,
    HomeworkPhoto,
    HomeworkRecord,
    MealPhoto,
    MealRecord,
    MealStudentNote,
    Notice,
    Parent,
    ParentBinding,
    PaymentRecord,
    Photo,
    PhotoStudent,
    Student,
    StudentHealth,
    StudentParent,
    SystemConfig,
    Teacher,
    TeacherRemark,
)

# ── 数据库连接 ──────────────────────────────────────────────

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/tuoban")

# SQLite 开发模式
SQLITE_PATH = BACKEND_ROOT / "tuoban_dev.db"
USE_SQLITE = os.getenv("APP_ENV", "development") == "development" or "--sqlite" in sys.argv or DATABASE_URL.startswith("sqlite")

if USE_SQLITE or "--sqlite" in sys.argv:
    if DATABASE_URL.startswith("sqlite"):
        db_url = DATABASE_URL
    else:
        db_url = f"sqlite:///{SQLITE_PATH.as_posix()}"
    connect_args = {"check_same_thread": False}
else:
    db_url = DATABASE_URL
    connect_args = {}

print(f"[DB] 数据库: {db_url.split('://')[0]}://...")
engine = create_engine(db_url, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)

# ── 静态数据 ──────────────────────────────────────────────

SUBJECTS = ["语文", "数学"]
HOMEWORK_TYPES = ["课堂作业", "家庭作业", "单元练习", "随堂测试"]
MOOD_TAGS = ["😊 开心", "😌 认真", "🌟 进步", "💪 努力"]
SCHOOL_NAMES = ["阳光小学", "实验小学", "第一小学", "第二小学", "育才小学", "中心幼儿园"]
GRADES = ["大班", "中班", "小班", "一年级", "二年级", "三年级"]
PICKUP_METHODS = ["家长自接", "校车接送", "长辈接送"]
FEE_TYPES = ["托管费", "餐费", "材料费", "活动费", "其他"]
PAYMENT_METHODS = ["微信支付", "支付宝", "现金", "银行转账"]
PAYMENT_STATUSES = ["已缴", "未缴", "部分缴纳"]
NOTICE_TYPES = ["通知", "活动", "放假", "提醒"]

STUDENTS_DATA = [
    {"name": "张小明", "gender": "男", "grade": "大班", "school_name": "中心幼儿园", "school_class": "大（1）班",
     "birth_date": date(2020, 3, 15), "interests": "画画、积木", "personality": "活泼开朗，喜欢交朋友",
     "weak_subjects": "语文", "school_end_time": time(16, 30), "address": "阳光花园8栋301"},
    {"name": "李小花", "gender": "女", "grade": "中班", "school_name": "中心幼儿园", "school_class": "中（2）班",
     "birth_date": date(2020, 8, 22), "interests": "跳舞、唱歌", "personality": "文静细心，做事认真",
     "weak_subjects": "", "school_end_time": time(16, 30), "address": "阳光花园12栋502"},
    {"name": "王浩然", "gender": "男", "grade": "一年级", "school_name": "实验小学", "school_class": "一（3）班",
     "birth_date": date(2019, 5, 10), "interests": "恐龙、乐高", "personality": "好奇心强，喜欢提问",
     "weak_subjects": "语文", "school_end_time": time(15, 50), "address": "翠湖居5栋201"},
    {"name": "赵雨萱", "gender": "女", "grade": "大班", "school_name": "中心幼儿园", "school_class": "大（1）班",
     "birth_date": date(2020, 1, 8), "interests": "手工、阅读", "personality": "乖巧懂事，有爱心",
     "weak_subjects": "数学", "school_end_time": time(16, 30), "address": "阳光花园15栋101"},
    {"name": "刘一辰", "gender": "男", "grade": "二年级", "school_name": "第一小学", "school_class": "二（2）班",
     "birth_date": date(2018, 11, 3), "interests": "足球、科学实验", "personality": "精力充沛，运动健将",
     "weak_subjects": "数学", "school_end_time": time(15, 50), "address": "碧水湾7栋302"},
    {"name": "陈思琪", "gender": "女", "grade": "中班", "school_name": "中心幼儿园", "school_class": "中（1）班",
     "birth_date": date(2020, 9, 18), "interests": "画画、过家家", "personality": "温柔体贴，乐于助人",
     "weak_subjects": "", "school_end_time": time(16, 30), "address": "翠湖居2栋603"},
]

PARENTS_DATA = {
    "张小明": [
        {"name": "张伟", "relation": "爸爸", "phone": "13800138001", "is_primary": True, "is_emergency": True},
        {"name": "王芳", "relation": "妈妈", "phone": "13900139001", "is_primary": False, "is_emergency": False},
    ],
    "李小花": [
        {"name": "李强", "relation": "爸爸", "phone": "13800138002", "is_primary": True, "is_emergency": True},
        {"name": "刘娟", "relation": "妈妈", "phone": "13900139002", "is_primary": False, "is_emergency": True},
    ],
    "王浩然": [
        {"name": "王刚", "relation": "爸爸", "phone": "13800138003", "is_primary": True, "is_emergency": True},
    ],
    "赵雨萱": [
        {"name": "赵明", "relation": "爸爸", "phone": "13800138004", "is_primary": True, "is_emergency": True},
        {"name": "陈静", "relation": "妈妈", "phone": "13900139004", "is_primary": False, "is_emergency": False},
        {"name": "赵丽", "relation": "姑姑", "phone": "13700137004", "is_primary": False, "is_emergency": True},
    ],
    "刘一辰": [
        {"name": "刘洋", "relation": "爸爸", "phone": "13800138005", "is_primary": True, "is_emergency": True},
        {"name": "周婷", "relation": "妈妈", "phone": "13900139005", "is_primary": False, "is_emergency": False},
    ],
    "陈思琪": [
        {"name": "陈浩", "relation": "爸爸", "phone": "13800138006", "is_primary": True, "is_emergency": True},
    ],
}

PICKUPS_DATA = {
    "张小明": [
        {"name": "张伟", "relation": "爸爸", "phone": "13800138001", "is_default": True},
        {"name": "王芳", "relation": "妈妈", "phone": "13900139001", "is_default": False},
        {"name": "张爷爷", "relation": "爷爷", "phone": "13600136001", "is_default": False},
    ],
    "李小花": [
        {"name": "李强", "relation": "爸爸", "phone": "13800138002", "is_default": True},
        {"name": "刘晓", "relation": "奶奶", "phone": "13600136002", "is_default": False},
    ],
    "王浩然": [
        {"name": "王刚", "relation": "爸爸", "phone": "13800138003", "is_default": True},
        {"name": "王爷爷", "relation": "爷爷", "phone": "13600136003", "is_default": False},
    ],
    "赵雨萱": [
        {"name": "赵明", "relation": "爸爸", "phone": "13800138004", "is_default": True},
        {"name": "陈静", "relation": "妈妈", "phone": "13900139004", "is_default": False},
        {"name": "赵丽", "relation": "姑姑", "phone": "13700137004", "is_default": False},
    ],
    "刘一辰": [
        {"name": "刘洋", "relation": "爸爸", "phone": "13800138005", "is_default": True},
    ],
    "陈思琪": [
        {"name": "陈浩", "relation": "爸爸", "phone": "13800138006", "is_default": True},
        {"name": "陈奶奶", "relation": "奶奶", "phone": "13600136006", "is_default": False},
    ],
}

# ── 工具函数 ──────────────────────────────────────────────

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def random_time(base_hour=7, base_minute=30, variance=45):
    """生成签到/签退时间"""
    mins = base_hour * 60 + base_minute + random.randint(-variance, variance)
    return time(mins // 60 % 24, mins % 60)


def generate_photo_path():
    """生成模拟照片路径"""
    now = datetime.now()
    name = f"{uuid4().hex[:12]}.jpg"
    return f"/uploads/photos/{now.year}/{now.month:02d}/{now.day:02d}/{name}"


FALLBACK_JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////"
    "2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAX/"
    "xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAH/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAEFAqf/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAEDAQE/ASP/"
    "xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAECAQE/ASP/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAY/Aqf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAE/IV//"
    "2gAMAwEAAgADAAAAEP/EFBQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQMBAT8QH//EFBQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQIBAT8QH//EFBABAQAAAAAAAAAAAAAAAAAA"
    "ABD/2gAIAQEAAT8QH//Z"
)


def ensure_demo_photo_file(file_path: str, photo_type: str, index: int) -> None:
    """为种子照片记录生成真实 jpg 文件，避免小程序演示时出现 404/破图。"""
    rel_path = file_path.lstrip("/").replace("/", os.sep)
    target = BACKEND_ROOT / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)

    try:
        from PIL import Image, ImageDraw

        palettes = {
            "meal": ("#FFF2DF", "#FF8C5A", "#36C2A0"),
            "homework": ("#EEF2FF", "#5B7FFF", "#FFD166"),
            "activity": ("#FFF7EF", "#FF7E5F", "#36C2A0"),
            "daily": ("#F7F8FC", "#5B7FFF", "#FF8C5A"),
            "general": ("#FFFAF7", "#36C2A0", "#5B7FFF"),
        }
        bg, primary, secondary = palettes.get(photo_type, palettes["general"])
        img = Image.new("RGB", (900, 675), bg)
        draw = ImageDraw.Draw(img)

        # 轻量绘本感占位图：模拟托班照片场景，不包含文字，避免字体依赖。
        draw.rounded_rectangle((40, 40, 860, 635), radius=44, fill="#FFFFFF")
        draw.rectangle((40, 445, 860, 635), fill="#F3E6D7")
        draw.ellipse((-120, 360, 350, 780), fill="#DDF4E9")
        draw.ellipse((520, 350, 1040, 790), fill="#E6ECFF")

        # 低桌
        draw.rounded_rectangle((270, 375, 640, 445), radius=28, fill="#D9A66F")
        draw.rectangle((310, 435, 335, 555), fill="#B98655")
        draw.rectangle((575, 435, 600, 555), fill="#B98655")

        # 两个孩子
        for cx, shirt, hair in [(260, primary, "#5B4638"), (640, secondary, "#4A3B31")]:
            draw.ellipse((cx - 58, 210, cx + 58, 326), fill="#FFD7B5")
            draw.pieslice((cx - 70, 185, cx + 70, 288), 180, 360, fill=hair)
            draw.ellipse((cx - 25, 255, cx - 13, 267), fill="#31405A")
            draw.ellipse((cx + 13, 255, cx + 25, 267), fill="#31405A")
            draw.arc((cx - 28, 270, cx + 28, 305), 10, 170, fill="#C46A4A", width=4)
            draw.rounded_rectangle((cx - 68, 326, cx + 68, 460), radius=34, fill=shirt)
            draw.line((cx - 60, 362, cx - 115, 410), fill="#FFD7B5", width=20)
            draw.line((cx + 60, 362, cx + 115, 410), fill="#FFD7B5", width=20)

        # 积木/画纸/餐盘，根据类型略微变化
        if photo_type == "meal":
            draw.ellipse((390, 315, 510, 395), fill="#FFFFFF", outline=primary, width=8)
            draw.ellipse((423, 337, 477, 375), fill="#FFD166")
            draw.rounded_rectangle((520, 315, 600, 382), radius=20, fill=secondary)
        elif photo_type == "homework":
            draw.rounded_rectangle((375, 300, 530, 410), radius=14, fill="#F9FBFF", outline=primary, width=8)
            draw.line((405, 332, 500, 332), fill="#C7D2FF", width=8)
            draw.line((405, 365, 475, 365), fill="#C7D2FF", width=8)
            draw.line((545, 315, 610, 380), fill="#FF8C5A", width=12)
        else:
            for x, y, color in [(390, 330, primary), (450, 300, "#FFD166"), (510, 350, secondary)]:
                draw.rounded_rectangle((x, y, x + 62, y + 62), radius=12, fill=color)

        # 植物和窗户
        draw.rounded_rectangle((94, 92, 230, 210), radius=18, fill="#EAF5FF")
        draw.line((162, 92, 162, 210), fill="#FFFFFF", width=8)
        draw.line((94, 151, 230, 151), fill="#FFFFFF", width=8)
        draw.rectangle((735, 338, 765, 505), fill="#8B6B4E")
        draw.ellipse((665, 250, 790, 380), fill="#8DDCC6")
        draw.ellipse((725, 205, 835, 330), fill="#36C2A0")

        # 角落小标识色块，帮助照片有区分度
        draw.ellipse((760, 78, 815, 133), fill=primary)
        draw.ellipse((805, 102, 835, 132), fill=secondary)

        img.save(target, "JPEG", quality=88, optimize=True)
    except Exception:
        target.write_bytes(FALLBACK_JPEG)


# ── 种子执行 ──────────────────────────────────────────────

def seed(db: Session, force: bool = False):
    """执行种子数据插入"""

    # 检测是否已有学生数据
    existing_count = db.query(Student).count()
    if existing_count > 0 and not force:
        print(f"[WARN] 数据库已有 {existing_count} 个学生，跳过插入（使用 --force 重新生成）")
        # 但确保基础数据存在
        seed_default_teacher(db)
        seed_default_config(db)
        db.commit()
        return

    if force:
        print("[RESET] 强制模式：清空所有数据...")
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()

    print("[SEED] 开始播种测试数据...\n")

    # ── 1. 基础数据 ──
    seed_default_teacher(db)
    seed_default_config(db)

    # 创建第二个老师
    teacher2 = Teacher(
        name="李老师",
        phone="13800001111",
        role="teacher",
        login_password=hash_password("123456"),
    )
    db.add(teacher2)
    db.flush()
    print("  [OK] 教师账号（管理员/123456，李老师/123456）")

    # 所有老师
    teachers = db.query(Teacher).all()
    admin_teacher = teachers[0]
    all_teachers = teachers

    # 简化的教师列表（留给后续随机引用）
    teacher_ids = [t.id for t in all_teachers]

    # ── 2. 学生 + 家长 + 接人授权 + 健康信息 ──
    student_map = {}  # name -> student obj
    parent_map = {}   # name -> parent obj list

    for sd in STUDENTS_DATA:
        student = Student(
            name=sd["name"],
            gender=sd["gender"],
            birth_date=sd["birth_date"],
            grade=sd["grade"],
            school_name=sd["school_name"],
            school_class=sd["school_class"],
            school_end_time=sd["school_end_time"],
            pickup_method=random.choice(PICKUP_METHODS),
            address=sd["address"],
            enrollment_date=date(2025, 9, 1),
            status="在读",
            interests=sd["interests"],
            personality=sd["personality"],
            weak_subjects=sd["weak_subjects"],
            notes="",
        )
        db.add(student)
        db.flush()
        student_map[sd["name"]] = student

        # 家长
        p_list = []
        for pd in PARENTS_DATA.get(sd["name"], []):
            parent = Parent(
                name=pd["name"],
                relation=pd["relation"],
                phone=pd["phone"],
                is_primary=pd["is_primary"],
                is_emergency=pd["is_emergency"],
                invite_code=f"TB{student.id}{random.randint(100,999)}",
            )
            db.add(parent)
            db.flush()
            p_list.append(parent)

            # 关联
            db.add(StudentParent(student_id=student.id, parent_id=parent.id))
        parent_map[sd["name"]] = p_list

        # 接人授权
        for pkd in PICKUPS_DATA.get(sd["name"], []):
            pickup = AuthorizedPickup(
                student_id=student.id,
                name=pkd["name"],
                relation=pkd["relation"],
                phone=pkd["phone"],
                is_default=pkd["is_default"],
            )
            db.add(pickup)

        # 健康信息
        health = StudentHealth(
            student_id=student.id,
            food_allergies=random.choice(["", "", "花生过敏", "牛奶不耐受", ""]),
            drug_allergies="",
            medical_history=random.choice(["", "", "", "", "轻度哮喘", ""]),
            special_notes="",
            consent_signed=True,
            consent_signed_at=utc_now(),
        )
        db.add(health)

        print(f"  [OK] 学生 {student.name}（{student.grade}）+ 家长 {len(p_list)} 人 + 接送人 + 健康信息")

    db.flush()

    # 家长绑定（模拟家长绑定了微信）
    all_parents = db.query(Parent).all()
    for i, parent in enumerate(all_parents):
        binding = ParentBinding(
            parent_id=parent.id,
            wechat_openid=f"wx_openid_{parent.id:04d}",
            bind_at=utc_now() - timedelta(days=random.randint(1, 60)),
            last_login_at=utc_now() - timedelta(days=random.randint(0, 7)),
        )
        db.add(binding)

    print("  [OK] 家长微信绑定")

    # ── 3. 考勤记录（近7天） ──
    all_students = db.query(Student).all()
    today = date.today()
    attendance_count = 0
    for day_offset in range(7):
        d = today - timedelta(days=day_offset)
        if d.weekday() >= 5:  # 跳过周末
            continue
        for student in all_students:
            # 80% 出勤率
            if random.random() < 0.2:
                continue
            checkin_h = random.randint(7, 9)
            checkin_m = random.randint(0, 59)
            checkout_h = random.randint(17, 19)
            checkout_m = random.randint(0, 59)
            record = AttendanceRecord(
                student_id=student.id,
                checkin_time=datetime(d.year, d.month, d.day, checkin_h, checkin_m),
                checkout_time=datetime(d.year, d.month, d.day, checkout_h, checkout_m),
                pickup_person=random.choice(["爸爸", "妈妈", "爷爷", "奶奶"]),
                checkin_by=random.choice(teacher_ids),
                checkout_by=random.choice(teacher_ids),
                date=d,
            )
            db.add(record)
            attendance_count += 1
    print(f"  [OK] 考勤记录 {attendance_count} 条（近7天）")

    # ── 4. 照片（模拟数据，没有真实图片文件） ──
    photo_types = ["general", "activity", "daily", "meal", "homework"]
    photo_remarks = [
        "今天户外活动",
        "午餐时间",
        "课间活动",
        "课堂作品",
        "阅读时间",
        "午睡时间",
        "手工课",
        "集体活动",
    ]
    photos_created = []

    for _ in range(30):
        ptype = random.choice(photo_types)
        file_path = generate_photo_path()
        ensure_demo_photo_file(file_path, ptype, len(photos_created))
        photo = Photo(
            file_path=file_path,
            original_name=f"photo_{uuid4().hex[:8]}.jpg",
            photo_type=ptype,
            is_featured=random.random() < 0.15,
            taken_by=random.choice(teacher_ids),
            taken_at=utc_now() - timedelta(days=random.randint(0, 14), hours=random.randint(0, 8)),
            remark=random.choice(photo_remarks) if random.random() < 0.6 else None,
        )
        db.add(photo)
        db.flush()
        photos_created.append(photo)

        # 关联 1-3 个学生
        associated_students = random.sample(all_students, k=random.randint(1, min(3, len(all_students))))
        for i_ps, s in enumerate(associated_students):
            db.add(PhotoStudent(
                photo_id=photo.id,
                student_id=s.id,
                is_main=(i_ps == 0 and len(associated_students) == 1),
            ))

    print(f"  [OK] 照片 {len(photos_created)} 张（已关联学生、含精选）")

    # ── 5. 作业记录 ──
    homework_count = 0
    for student in all_students:
        for _ in range(random.randint(3, 6)):
            hw_date = today - timedelta(days=random.randint(0, 20))
            if hw_date.weekday() >= 5:
                continue
            statuses = ["待批改", "已批改", "已订正"]
            weight = [0.3, 0.4, 0.3]
            status = random.choices(statuses, weights=weight, k=1)[0]
            score = random.randint(60, 100) if status != "待批改" else None

            homework = HomeworkRecord(
                student_id=student.id,
                subject=random.choice(SUBJECTS),
                homework_type=random.choice(HOMEWORK_TYPES),
                completion_status=random.choice(["已完成", "未完成", "部分完成"]),
                accuracy_status=random.choice(["优秀", "良好", "及格", "待提高"]) if status != "待批改" else None,
                error_count=random.randint(0, 8) if status != "待批改" else 0,
                score=score,
                auto_comment=random.choice(["", "书写认真", "进步明显", "继续加油", "正确率高"]),
                teacher_remark=random.choice(["", "继续保持！", "书写有进步", "要多练习哦"]),
                recorded_by=random.choice(teacher_ids),
                homework_date=hw_date,
                completed_at=datetime(hw_date.year, hw_date.month, hw_date.day, random.randint(16, 18), random.randint(0, 59)) if status != "待批改" else None,
            )
            db.add(homework)
            db.flush()
            homework_count += 1

            # 给部分作业关联照片
            if random.random() < 0.5:
                for step_name in ["done", "graded", "corrected"]:
                    step_done = {"done": True, "graded": status != "待批改", "corrected": status == "已订正"}
                    if step_done.get(step_name, False) and photos_created:
                        hw_photo = random.choice(photos_created)
                        db.add(HomeworkPhoto(
                            homework_id=homework.id,
                            photo_id=hw_photo.id,
                            step=step_name,
                        ))

    print(f"  [OK] 作业记录 {homework_count} 条")

    # ── 6. 成长档案（评语） ──
    remark_count = 0
    for student in all_students:
        for _ in range(random.randint(2, 5)):
            remark_date = today - timedelta(days=random.randint(0, 30))
            remark = TeacherRemark(
                student_id=student.id,
                record_date=remark_date,
                content=random.choice([
                    f"{student.name}今天表现很好，认真完成了所有作业。",
                    f"{student.name}在课堂上积极参与，回答问题很主动。",
                    f"{student.name}和小朋友们相处融洽，很有礼貌。",
                    f"{student.name}今天完成课堂练习很认真。",
                    f"{student.name}午饭吃得很好，全部吃完了。",
                    f"{student.name}在语文练习上有进步，表达更清楚了。",
                    f"{student.name}今天帮助了其他小朋友，值得表扬。",
                    f"{student.name}作业书写越来越工整了，继续加油！",
                ]),
                mood_tag=random.choice(["😊 开心", "😌 认真", "🌟 进步", "💪 努力", "😄 愉快"]),
                created_by=random.choice(teacher_ids),
            )
            db.add(remark)
            remark_count += 1
    print(f"  [OK] 成长评语 {remark_count} 条")

    # ── 7. 餐食记录 ──
    meal_count = 0
    for day_offset in range(10):
        d = today - timedelta(days=day_offset)
        if d.weekday() >= 5:
            continue
        for meal_type in ["早餐", "午餐", "下午点心"]:
            if random.random() < 0.3:
                continue
            menus = {
                "早餐": "牛奶、鸡蛋、小米粥、小笼包",
                "午餐": "米饭、红烧鸡腿、番茄炒蛋、紫菜蛋花汤",
                "下午点心": "水果拼盘、酸奶、小饼干",
            }
            meal = MealRecord(
                meal_date=d,
                meal_type=meal_type,
                menu_text=menus.get(meal_type, "标准餐食"),
                ingredient_notes="食材新鲜，来源可追溯",
                cooking_notes="少油少盐，适合儿童口味",
                hygiene_notes="厨房卫生达标",
                overall_remark=random.choice(["孩子们都吃得很开心", "今天饭菜很受欢迎", "全部吃完，没有浪费"]),
                created_by=random.choice(teacher_ids),
            )
            db.add(meal)
            db.flush()
            meal_count += 1

            # 关联餐食照片
            for step_name in ["shopping", "cooking", "done", "kids_eating"]:
                if random.random() < 0.6 and photos_created:
                    mp = random.choice(photos_created)
                    db.add(MealPhoto(meal_id=meal.id, photo_id=mp.id, step=step_name))

        # 学生餐食评价
        for student in all_students:
            if random.random() < 0.3:
                # 找当天某个餐食
                meal_record = db.query(MealRecord).filter(
                    MealRecord.meal_date == d
                ).first()
                if meal_record:
                    db.add(MealStudentNote(
                        meal_id=meal_record.id,
                        student_id=student.id,
                        remark=random.choice(["全部吃完了", "吃了一半", "不太喜欢吃青菜", "喝了两碗汤", "吃完还添了饭"]),
                    ))
    print(f"  [OK] 餐食记录 {meal_count} 条（含学生评价）")

    # ── 8. 收费记录 ──
    payment_count = 0
    for student in all_students:
        for fee_type in ["托管费", "餐费"]:
            amounts = {"托管费": 2800, "餐费": 500}
            amount = amounts.get(fee_type, random.randint(100, 3000))
            status = random.choice(["已缴", "未缴"])
            payment = PaymentRecord(
                student_id=student.id,
                fee_type=fee_type,
                amount=amount,
                period_start=date(today.year, today.month, 1),
                period_end=date(today.year, today.month, 1) + timedelta(days=30),
                status=status,
                payment_method=random.choice(PAYMENT_METHODS) if status == "已缴" else None,
                paid_at=utc_now() - timedelta(days=random.randint(1, 10)) if status == "已缴" else None,
                recorded_by=random.choice(teacher_ids),
            )
            db.add(payment)
            payment_count += 1
    print(f"  [OK] 收费记录 {payment_count} 条")

    # ── 9. 通知公告 ──
    notices_data = [
        {"title": "六一儿童节活动通知", "content": "亲爱的家长朋友们：\n\n六一儿童节即将到来，我园将于6月1日上午9:00举办庆祝活动，届时请家长准时参加。\n\n节目单：\n1. 合唱表演\n2. 舞蹈表演\n3. 亲子游戏\n4. 美食分享\n\n期待您的参与！",
         "notice_type": "活动", "is_pinned": True, "display_start": today - timedelta(days=5), "display_end": today + timedelta(days=10)},
        {"title": "五一放假安排", "content": "根据国家法定节假日安排，五一劳动节放假时间为5月1日至5月5日，共5天。\n5月6日（周二）正常上课。\n\n请家长合理安排假期时间，注意孩子安全。",
         "notice_type": "放假", "is_pinned": True, "display_start": today - timedelta(days=15), "display_end": today + timedelta(days=20)},
        {"title": "春季传染病预防温馨提示", "content": "春季是传染病高发期，请家长注意：\n1. 勤洗手、勤通风\n2. 避免去人群密集场所\n3. 如有发热症状请及时就医\n4. 保持良好的作息习惯",
         "notice_type": "提醒", "is_pinned": False, "display_start": today - timedelta(days=3), "display_end": today + timedelta(days=14)},
        {"title": "关于调整接送时间的通知", "content": "从下周一开始，下午放学时间调整为17:30，请家长按时接孩子。\n\n如有特殊原因需要延迟接孩子，请提前联系老师。",
         "notice_type": "通知", "is_pinned": False, "display_start": today - timedelta(days=7), "display_end": today + timedelta(days=7)},
        {"title": "家长会邀请函", "content": "本学期家长会定于本周五晚上7:00召开，请各位家长准时参加。\n\n会议内容：\n1. 本学期教学总结\n2. 孩子成长汇报\n3. 下半学期计划\n\n地点：多功能教室",
         "notice_type": "活动", "is_pinned": False, "display_start": today - timedelta(days=2), "display_end": today + timedelta(days=5)},
        {"title": "本周食谱", "content": "**本周食谱（6月1日-6月5日）**\n\n周一：红烧鸡腿、番茄炒蛋\n周二：清蒸鱼、西兰花\n周三：肉末豆腐、炒青菜\n周四：土豆炖牛肉、紫菜蛋花汤\n周五：扬州炒饭、水果沙拉",
         "notice_type": "通知", "is_pinned": False, "display_start": today - timedelta(days=1), "display_end": today + timedelta(days=5)},
    ]
    for nd in notices_data:
        notice = Notice(
            title=nd["title"],
            content=nd["content"],
            notice_type=nd["notice_type"],
            is_pinned=nd["is_pinned"],
            is_active=True,
            display_start=nd["display_start"],
            display_end=nd["display_end"],
            created_by=random.choice(teacher_ids),
        )
        db.add(notice)
    print(f"  [OK] 通知公告 {len(notices_data)} 条")

    # ── 10. 更新系统配置 ──
    config_updates = {
        "school_name": "阳光宝贝托班",
        "welcome_message": "用心陪伴每一个孩子快乐成长",
    }
    for key, value in config_updates.items():
        existing = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
        if existing:
            existing.config_value = value
    print("  [OK] 系统配置已更新")

    # ── 提交 ──
    db.commit()
    print(f"\n[DONE] 种子数据完成！共 {db.query(Student).count()} 个学生")
    print(f"   统计：")
    print(f"   - 教师: {db.query(Teacher).count()} 人")
    print(f"   - 学生: {db.query(Student).count()} 人")
    print(f"   - 家长: {db.query(Parent).count()} 人")
    print(f"   - 考勤: {db.query(AttendanceRecord).count()} 条")
    print(f"   - 照片: {db.query(Photo).count()} 张")
    print(f"   - 作业: {db.query(HomeworkRecord).count()} 条")
    print(f"   - 评语: {db.query(TeacherRemark).count()} 条")
    print(f"   - 餐食: {db.query(MealRecord).count()} 条")
    print(f"   - 收费: {db.query(PaymentRecord).count()} 条")
    print(f"   - 通知: {db.query(Notice).count()} 条")
    print()
    print("登录账号：")
    print("   教师端：管理员 / 123456")
    print("   家长端：使用任意家长的 invite_code 绑定")
    print("          （如张小明家长的邀请码可用 /api/parent/bind 查询）")


# ── 入口 ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="托班管理系统种子数据")
    parser.add_argument("--force", action="store_true", help="强制重新插入（先清空）")
    parser.add_argument("--sqlite", action="store_true", help="使用 SQLite 模式")
    args = parser.parse_args()

    print("=" * 50)
    print("托班管理系统 - 测试数据生成器")
    print("=" * 50)

    # 确保表存在，使用本脚本解析后的数据库连接。
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db, force=args.force)
    finally:
        db.close()


if __name__ == "__main__":
    main()
