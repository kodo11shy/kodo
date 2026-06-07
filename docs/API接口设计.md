---
title: 托班管理系统 - API 接口设计
created: 2026-06-05
tags: [项目, 技术设计, API, 托班管理]
---

# 🏫 托班管理系统 · API 接口设计

> **后端框架**：Python FastAPI
> **基础路径**：`https://你的域名.com/api`
> **认证方式**：老师端用 Token（密码登录后获取），家长端用微信 OpenID
> **返回格式**：统一 `{ "code": 0, "data": {...}, "message": "ok" }`

---

## 一、认证相关

### 1.1 老师登录

```
POST /api/auth/teacher/login
  请求：{ "password": "管理密码" }
  返回：{ "token": "xxx", "teacher": { id, name, role } }

说明：首次启动时设置默认密码
```

### 1.2 家长绑定

```
POST /api/auth/parent/bind
  请求：{ "invite_code": "ABCD12", "wechat_openid": "xxx" }
  返回：{ "token": "xxx", "student_ids": [1, 2] }

说明：家长用邀请码绑定微信，以后自动登录
```

### 1.3 家长自动登录

```
GET /api/auth/parent/auto-login
  请求头：Authorization: Bearer <token>
  返回：{ "parents": [...], "students": [...] }
```

---

## 二、学生档案 🧑‍🎓

### 2.1 创建学生

```
POST /api/students
  请求：{
    "name": "小明",
    "gender": "男",
    "birth_date": "2017-03-15",
    "grade": "三年级",
    "school_name": "实验小学",
    "school_class": "2班",
    "address": "xx路xx号",
    "parent1_name": "张伟",
    "parent1_relation": "爸爸",
    "parent1_phone": "138xxxx",
    "parent2_name": "李丽",
    "parent2_relation": "妈妈",
    "parent2_phone": "139xxxx"
  }
  返回：{ "id": 1 }
```

### 2.2 获取所有学生（老师用）

```
GET /api/students
  返回：{
    "students": [
      { "id": 1, "name": "小明", "grade": "三年级", "status": "在读", ... }
    ]
  }
  支持参数：?status=在读  ?keyword=小明（搜索）
```

### 2.3 获取单个学生详情

```
GET /api/students/{id}
  返回：{ "id": 1, "name": "小明", ..., "health": {...}, "parents": [...] }
```

### 2.4 更新学生信息

```
PUT /api/students/{id}
  请求：{ "name": "小明", "grade": "四年级", ... }
  返回：{ "id": 1 }
```

### 2.5 获取接送授权人

```
GET /api/students/{id}/pickups
  返回：{ "pickups": [{ "id": 1, "name": "张伟", "relation": "爸爸", ... }] }
```

### 2.6 更新接送授权人

```
PUT /api/students/{id}/pickups
  请求：{ "pickups": [{ "name": "张伟", "relation": "爸爸", "phone": "138xxx" }, ...] }
```

### 2.7 签署健康告知书

```
POST /api/students/{id}/health/consent
  请求：{ "signed": true }
  返回：{ "ok": true }
```

---

## 三、签到签退 🏁

### 3.1 签到

```
POST /api/attendance/checkin
  请求：{ "student_id": 1, "timestamp": "2026-06-05T08:02:00" }
  返回：{ "id": 1, "time": "08:02", "status": "已签到" }
```

### 3.2 签退

```
POST /api/attendance/checkout
  请求：{ "student_id": 1, "timestamp": "2026-06-05T17:30:00", "pickup_person": "爸爸" }
  返回：{ "id": 1, "time": "17:30", "status": "已签退" }
```

### 3.3 补签到

```
POST /api/attendance/makeup-checkin
  请求：{ "student_id": 1, "timestamp": "2026-06-05T08:15:00", "reason": "早上忘记签了" }
  返回：{ "id": 1, "is_makeup": true }
```

### 3.4 获取今日状态（老师打开签到页时调用）

```
GET /api/attendance/today
  返回：{
    "date": "2026-06-05",
    "total": 20,
    "checked_in": [
      { "student_id": 1, "name": "小明", "checkin_time": "08:02", "pickup_person": null }
    ],
    "not_checked_in": [
      { "student_id": 2, "name": "小红" }
    ]
  }
```

### 3.5 获取某学生出勤统计

```
GET /api/attendance/statistics/{student_id}?month=2026-06
  返回：{
    "total_days": 22,
    "attended_days": 20,
    "makeup_days": 1,
    "attendance_rate": "90.9%"
  }
```

---

## 四、拍照记录 📸

### 4.1 上传照片

```
POST /api/photos/upload
  请求：multipart/form-data（图片文件）
  返回：{ "photo_id": 1, "file_path": "/photos/2026/06/05/xxx.jpg", "thumbnail": "..." }
```

### 4.2 关联学生

```
POST /api/photos/{id}/associate
  请求：{ "student_ids": [1, 2, 3], "photo_type": "activity", "remark": "搭积木" }
  返回：{ "ok": true }
```

### 4.3 标记精选

```
PUT /api/photos/{id}/featured
  请求：{ "is_featured": true }
  返回：{ "ok": true }
```

### 4.4 获取学生照片列表

```
GET /api/photos?student_id=1&type=homework&page=1&page_size=20
  返回：{
    "photos": [
      { "id": 1, "thumbnail": "...", "taken_at": "2026-06-05", "remark": "..." }
    ],
    "total": 36
  }
```

### 4.5 获取精选照片（用于招生展示）

```
GET /api/photos/featured?page=1&page_size=10
  返回：{ "photos": [...] }
```

---

## 五、作业管理 📚

### 5.1 创建作业记录（第一步：做完）

```
POST /api/homework
  请求：{
    "student_id": 1,
    "subject": "数学",
    "homework_type": "课堂作业",
    "photo_ids": [1, 2, 3],          -- 完成证明照片
    "remark": "小明今天在学校写完了"   -- 语音备注
  }
  返回：{ "id": 1, "status": "待批改" }
```

### 5.2 批改（第二步：批改）

```
PUT /api/homework/{id}/grade
  请求：{
    "photo_ids": [4, 5],              -- 批改后照片
    "accuracy_status": "有错已讲解",
    "error_count": 3,
    "score": 7,
    "remark": "口算错了3道，已讲解凑十法"
  }
  返回：{ "id": 1, "status": "已批改" }
```

### 5.3 改错完成（第三步：改错）

```
PUT /api/homework/{id}/correct
  请求：{
    "photo_ids": [6],                  -- 改错后照片
    "remark": "三道错题全部改对了"
  }
  返回：{ "id": 1, "status": "已完成" }
```

### 5.4 获取作业列表（按学生）

```
GET /api/homework?student_id=1&page=1&page_size=20
  返回：{
    "records": [
      {
        "id": 1,
        "date": "2026-06-05",
        "subject": "数学",
        "status": "已完成",
        "accuracy": "全对",
        "score": 9,
        "photos": { "done": [...], "graded": [...], "corrected": [...] },
        "remark": "..."
      }
    ]
  }
```

### 5.5 获取作业评分趋势（用于曲线图）

```
GET /api/homework/trend/{student_id}?weeks=4
  返回：{
    "trend": [
      { "date": "2026-06-01", "avg_score": 7.5, "count": 2 },
      { "date": "2026-06-02", "avg_score": 8.0, "count": 1 }
    ],
    "subject_avg": [
      { "subject": "语文", "avg_score": 6.5 },
      { "subject": "数学", "avg_score": 8.8 }
    ],
    "perfect_rate": 0.65
  }
```

---

## 六、餐食与食育 🍱

### 6.1 创建餐食记录

```
POST /api/meals
  请求：{
    "meal_date": "2026-06-05",
    "meal_type": "午餐",
    "menu_text": "土豆炖排骨+清炒青菜+紫菜蛋花汤",
    "ingredient_notes": "今天买了排骨和青菜",
    "cooking_notes": "排骨焯水炖40分钟",
    "hygiene_notes": "厨房已消毒",
    "overall_remark": "今天大家吃得很香",
    "photo_ids": { "shopping": [1], "cooking": [2,3], "done": [4], "kids_eating": [5] }
  }
  返回：{ "id": 1 }
```

### 6.2 添加个别学生餐食记录

```
POST /api/meals/{id}/student-note
  请求：{
    "student_id": 1,
    "remark": "吃了两碗，平时在家不吃芹菜",
    "photo_id": 6
  }
  返回：{ "id": 1 }
```

### 6.3 获取餐食列表（公共展示）

```
GET /api/meals?page=1&page_size=10
  返回：{
    "records": [
      {
        "id": 1,
        "date": "2026-06-05",
        "menu": "土豆炖排骨...",
        "photos": { "done": [...], "kids_eating": [...] },
        "overall_remark": "今天大家吃得很香"
      }
    ]
  }
```

### 6.4 获取某学生的餐食特别记录

```
GET /api/meals/student/{student_id}
  返回：{ "notes": [{ "date": "...", "remark": "吃了两碗" }] }
```

---

## 七、老师评语 📝

### 7.1 写评语

```
POST /api/remarks
  请求：{ "student_id": 1, "record_date": "2026-06-05", "content": "今天主动举手回答问题", "mood_tag": "开心" }
  返回：{ "id": 1 }
```

### 7.2 获取学生评语列表

```
GET /api/remarks?student_id=1&page=1
  返回：{ "remarks": [{ "date": "...", "content": "...", "mood_tag": "..." }] }
```

---

## 八、成长档案 & 时间线 🌟

### 8.1 获取学生成长时间线

```
GET /api/growth/timeline/{student_id}?days=30
  返回：{
    "timeline": [
      {
        "date": "2026-06-05",
        "type": "homework",        -- homework / remark / meal / milestone / photo
        "title": "数学 · 全对",
        "description": "数学口算全对，评分9分",
        "score": 9,
        "photos": [...],
        "source_id": 1
      },
      {
        "date": "2026-06-05",
        "type": "meal",
        "title": "🍱 餐食记录",
        "description": "吃了两碗青菜",
        "photos": [...]
      }
    ]
  }
```

### 8.2 获取成长概览（档案首页）

```
GET /api/growth/overview/{student_id}
  返回：{
    "student_info": { "name": "小明", "grade": "三年级", "enrollment_days": 120 },
    "current_month": {
      "attendance_rate": "90%",
      "avg_score": 7.8,
      "homework_count": 18,
      "remark_count": 5
    },
    "latest_remark": "这个月进步很大..."
  }
```

### 8.3 创建成长里程碑

```
POST /api/growth/milestones
  请求：{
    "student_id": 1,
    "title": "第一次独立完成作业",
    "description": "今天自己主动完成数学作业，没有让老师提醒",
    "milestone_date": "2026-06-01",
    "milestone_type": "study",
    "photo_id": 10
  }
  返回：{ "id": 1 }
```

---

## 九、通知公告 📢

### 9.1 创建通知

```
POST /api/notices
  请求：{
    "title": "6月25日停课通知",
    "content": "因电力检修，6月25日停课一天...",
    "notice_type": "放假",
    "is_pinned": true,
    "display_start": "2026-06-20",
    "display_end": "2026-06-25"
  }
  返回：{ "id": 1 }
```

### 9.2 获取首页通知列表（公开，无需登录）

```
GET /api/notices/active
  返回：{
    "notices": [
      { "id": 1, "title": "6月25日停课通知", "content": "...", "is_pinned": true }
    ]
  }
```

### 9.3 获取所有通知（老师管理用）

```
GET /api/notices?page=1
  返回：{ "notices": [...], "total": 10 }
```

### 9.4 删除通知

```
DELETE /api/notices/{id}
```

---

## 十、缴费记录 💰

### 10.1 记一笔

```
POST /api/payments
  请求：{
    "student_id": 1,
    "fee_type": "学费",
    "amount": 2800.00,
    "period_start": "2026-06-01",
    "period_end": "2026-06-30",
    "status": "已缴",
    "payment_method": "微信转账",
    "remark": "6月学费"
  }
  返回：{ "id": 1 }
```

### 10.2 缴费总览

```
GET /api/payments/summary?month=2026-06
  返回：{
    "total_fee": 8400,
    "paid": 5600,
    "unpaid": 2800,
    "details": [
      { "student_name": "小明", "fee_type": "学费", "amount": 2800, "status": "已缴" },
      { "student_name": "小红", "fee_type": "学费", "amount": 2800, "status": "已缴" },
      { "student_name": "小华", "fee_type": "学费", "amount": 2800, "status": "未缴" }
    ]
  }
```

### 10.3 获取收费标准（公开）

```
GET /api/payments/fee-standard
  返回：{
    "items": [
      { "name": "托管费", "amount": 2800, "unit": "元/月", "description": "周一至周五放学后" },
      { "name": "餐费", "amount": 500, "unit": "元/月", "description": "每日一餐两点" },
      { "name": "材料费", "amount": 200, "unit": "元/学期", "description": "学习材料" }
    ]
  }
```

---

## 十一、家长端专用 👪

### 11.1 获取家长关联的学生

```
GET /api/parent/students
  返回：{
    "students": [
      {
        "id": 1,
        "name": "小明",
        "grade": "三年级",
        "today_checkin": "08:02",
        "today_checkout": null
      }
    ]
  }
```

### 11.2 家长查看自己孩子的时间线

```
GET /api/parent/growth/{student_id}
  -- 同 8.1，但权限限制只能看自己孩子
```

### 11.3 家长查看自己孩子的作业

```
GET /api/parent/homework/{student_id}
  -- 同 5.4，但只能看，不能操作
```

### 11.4 获取首页公开信息

```
GET /api/public/homepage
  请求头：不需要认证
  返回：{
    "school_name": "智慧托班",
    "welcome_message": "用心陪伴每一个孩子",
    "notices": [...],
    "fee_standard": [...],
    "featured_photos": [...]
  }
```

---

## 十二、系统配置 ⚙️

### 12.1 获取配置

```
GET /api/config?keys=tuition_fee,meal_fee,school_name
  返回：{
    "tuition_fee": "2800",
    "meal_fee": "500",
    "school_name": "智慧托班"
  }
```

### 12.2 更新配置（管理员）

```
PUT /api/config
  请求：{ "tuition_fee": "3000", "school_name": "新名称" }
  返回：{ "ok": true }
```

---

## 三、接口汇总

| 分类 | 数量 | 说明 |
|------|------|------|
| 认证 | 3 | 登录、绑定、自动登录 |
| 学生档案 | 7 | 增删改查 + 授权人 + 健康 |
| 签到签退 | 5 | 签到、签退、补签、今日状态、统计 |
| 拍照 | 5 | 上传、关联、精选、列表、精选集 |
| 作业管理 | 5 | 创建、批改、改错、列表、趋势 |
| 餐食 | 4 | 创建、个别记录、列表、学生记录 |
| 评语 | 2 | 写、查 |
| 成长档案 | 3 | 时间线、概览、里程碑 |
| 通知公告 | 4 | 创建、活跃列表、管理列表、删除 |
| 缴费 | 3 | 记账、总览、收费标准 |
| 家长端 | 4 | 学生列表、时间线、作业、首页 |
| 系统配置 | 2 | 读、写 |
| **合计** | **47** | |

---

> **关联文档**：[数据库设计](数据库设计.md) | [需求终稿](需求终稿-2026-06-05.md)
