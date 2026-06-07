# 托班管理系统后端

FastAPI + PostgreSQL 后端。当前完成第一阶段骨架、核心表模型、老师登录、学生、签到、照片、作业、首页、通知和配置接口。

## 目录

```text
backend/
├── app/
│   ├── api/          # API 路由
│   ├── core/         # 配置、响应、认证工具
│   ├── db/           # 数据库连接和初始化
│   ├── models/       # SQLAlchemy 模型
│   └── schemas/      # Pydantic 请求/响应模型
├── migrations/       # SQL 建表脚本
├── uploads/          # 后续图片上传目录
└── requirements.txt
```

## 本地启动

推荐直接运行：

```powershell
.\scripts\start-dev.ps1
```

该脚本会使用 SQLite 本地联调数据库，并在 `http://localhost:8000` 启动后端。

手动启动：

```powershell
cd backend
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

默认会根据 `DATABASE_URL` 自动建表，并在 teachers 表为空时创建默认管理员。

如果本机暂时没有 PostgreSQL，可在 `.env` 中临时改用 SQLite 联调：

```text
DATABASE_URL=sqlite:///./tuoban_dev.db
```

正式环境仍建议使用 PostgreSQL。

开发默认密码：

```text
123456
```

生产环境必须修改 `.env` 中的 `DEFAULT_TEACHER_PASSWORD` 和 `TOKEN_SECRET`。

## 已完成接口

```text
POST /api/auth/teacher/login
GET  /api/students
POST /api/students
GET  /api/attendance/today
POST /api/attendance/checkin
POST /api/attendance/checkout
POST /api/attendance/makeup-checkin
POST /api/photos/upload
POST /api/photos/{id}/associate
GET  /api/photos
GET  /api/photos/featured
PUT  /api/photos/{id}/featured
POST /api/homework
PUT  /api/homework/{id}/grade
PUT  /api/homework/{id}/correct
GET  /api/homework
GET  /api/public/homepage
POST /api/notices
GET  /api/notices
PUT  /api/notices/{id}
DELETE /api/notices/{id}
GET  /api/config
PUT  /api/config
POST /api/remarks
GET  /api/remarks
POST /api/payments
GET  /api/payments/summary
GET  /api/payments/fee-standard
GET  /api/growth/overview/{student_id}
GET  /api/growth/timeline/{student_id}
POST /api/auth/parent/bind
GET  /api/auth/parent/auto-login
GET  /api/parent/students
GET  /api/parent/growth/{student_id}
GET  /api/parent/homework/{student_id}
GET  /api/parent/photos/{student_id}
POST /api/meals
POST /api/meals/{id}/student-note
GET  /api/meals
GET  /api/meals/student/{student_id}
GET  /api/students/{id}
PUT  /api/students/{id}
GET  /api/students/{id}/pickups
PUT  /api/students/{id}/pickups
POST /api/students/{id}/health/consent
```

请求：

```json
{
  "password": "123456"
}
```

成功：

```json
{
  "code": 0,
  "data": {
    "token": "...",
    "teacher": {
      "id": 1,
      "name": "管理员",
      "role": "admin"
    }
  },
  "message": "ok"
}
```

失败：

```json
{
  "code": 40001,
  "data": null,
  "message": "密码错误"
}
```

## 建表 SQL

当前建表 SQL 在：

```text
backend/migrations/001_initial.sql
```
