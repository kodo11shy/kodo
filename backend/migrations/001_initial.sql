CREATE TABLE IF NOT EXISTS teachers (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  phone VARCHAR(20),
  role VARCHAR(20) DEFAULT 'teacher' NOT NULL,
  login_password VARCHAR(255) NOT NULL,
  is_active BOOLEAN DEFAULT TRUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  gender VARCHAR(4),
  birth_date DATE,
  grade VARCHAR(50),
  school_name VARCHAR(100),
  school_class VARCHAR(50),
  school_end_time TIME,
  pickup_method VARCHAR(50) DEFAULT '家长自接' NOT NULL,
  address TEXT,
  enrollment_date DATE,
  status VARCHAR(20) DEFAULT '在读' NOT NULL,
  avatar_url VARCHAR(500),
  interests TEXT,
  personality TEXT,
  weak_subjects TEXT,
  notes TEXT,
  is_active BOOLEAN DEFAULT TRUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS parents (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  relation VARCHAR(20) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  is_primary BOOLEAN DEFAULT FALSE NOT NULL,
  is_emergency BOOLEAN DEFAULT FALSE NOT NULL,
  wechat_openid VARCHAR(100),
  invite_code VARCHAR(20) UNIQUE,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS student_parents (
  id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  parent_id INTEGER NOT NULL REFERENCES parents(id) ON DELETE CASCADE,
  is_authorized BOOLEAN DEFAULT TRUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  CONSTRAINT uq_student_parent UNIQUE(student_id, parent_id)
);

CREATE TABLE IF NOT EXISTS authorized_pickups (
  id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  name VARCHAR(50) NOT NULL,
  relation VARCHAR(20) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  id_card VARCHAR(20),
  is_default BOOLEAN DEFAULT FALSE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS student_health (
  id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  food_allergies TEXT,
  drug_allergies TEXT,
  medical_history TEXT,
  special_notes TEXT,
  current_meds TEXT,
  consent_signed BOOLEAN DEFAULT FALSE NOT NULL,
  consent_signed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS attendance_records (
  id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  checkin_time TIMESTAMP NOT NULL,
  checkout_time TIMESTAMP,
  pickup_person VARCHAR(50),
  checkin_by INTEGER REFERENCES teachers(id),
  checkout_by INTEGER REFERENCES teachers(id),
  is_makeup BOOLEAN DEFAULT FALSE NOT NULL,
  makeup_reason TEXT,
  date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  CONSTRAINT uq_attendance_student_date UNIQUE(student_id, date)
);

CREATE TABLE IF NOT EXISTS photos (
  id SERIAL PRIMARY KEY,
  file_path VARCHAR(500) NOT NULL,
  thumbnail_path VARCHAR(500),
  original_name VARCHAR(200),
  file_size INTEGER,
  width INTEGER,
  height INTEGER,
  photo_type VARCHAR(30) DEFAULT 'general' NOT NULL,
  is_featured BOOLEAN DEFAULT FALSE NOT NULL,
  taken_by INTEGER REFERENCES teachers(id),
  taken_at TIMESTAMP NOT NULL,
  remark TEXT,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS photo_students (
  id SERIAL PRIMARY KEY,
  photo_id INTEGER NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
  student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  is_main BOOLEAN DEFAULT FALSE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  CONSTRAINT uq_photo_student UNIQUE(photo_id, student_id)
);

CREATE TABLE IF NOT EXISTS homework_records (
  id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  subject VARCHAR(20) NOT NULL,
  homework_type VARCHAR(30) DEFAULT '课堂作业' NOT NULL,
  completion_status VARCHAR(20) DEFAULT '待批改' NOT NULL,
  accuracy_status VARCHAR(20),
  error_count INTEGER DEFAULT 0 NOT NULL,
  score INTEGER,
  auto_comment TEXT,
  teacher_remark TEXT,
  recorded_by INTEGER REFERENCES teachers(id),
  homework_date DATE NOT NULL,
  completed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS homework_photos (
  id SERIAL PRIMARY KEY,
  homework_id INTEGER NOT NULL REFERENCES homework_records(id) ON DELETE CASCADE,
  photo_id INTEGER NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
  step VARCHAR(20) NOT NULL,
  sort_order INTEGER DEFAULT 0 NOT NULL,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS notices (
  id SERIAL PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  content TEXT NOT NULL,
  notice_type VARCHAR(30) DEFAULT '通知' NOT NULL,
  is_pinned BOOLEAN DEFAULT FALSE NOT NULL,
  is_active BOOLEAN DEFAULT TRUE NOT NULL,
  display_start DATE,
  display_end DATE,
  created_by INTEGER REFERENCES teachers(id),
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS system_config (
  id SERIAL PRIMARY KEY,
  config_key VARCHAR(100) UNIQUE NOT NULL,
  config_value TEXT,
  description TEXT,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS teacher_remarks (
  id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  record_date DATE NOT NULL,
  content TEXT NOT NULL,
  mood_tag VARCHAR(20),
  created_by INTEGER REFERENCES teachers(id),
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_records (
  id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  fee_type VARCHAR(30) NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  period_start DATE,
  period_end DATE,
  status VARCHAR(20) DEFAULT '未缴' NOT NULL,
  payment_method VARCHAR(30),
  remark TEXT,
  paid_at TIMESTAMP,
  recorded_by INTEGER REFERENCES teachers(id),
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS parent_bindings (
  id SERIAL PRIMARY KEY,
  parent_id INTEGER NOT NULL REFERENCES parents(id) ON DELETE CASCADE,
  wechat_openid VARCHAR(100) UNIQUE NOT NULL,
  bind_at TIMESTAMP DEFAULT NOW() NOT NULL,
  last_login_at TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE NOT NULL
);

CREATE TABLE IF NOT EXISTS meal_records (
  id SERIAL PRIMARY KEY,
  meal_date DATE NOT NULL,
  meal_type VARCHAR(20) DEFAULT '午餐' NOT NULL,
  menu_text TEXT,
  ingredient_notes TEXT,
  cooking_notes TEXT,
  hygiene_notes TEXT,
  overall_remark TEXT,
  created_by INTEGER REFERENCES teachers(id),
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  CONSTRAINT uq_meal_date_type UNIQUE(meal_date, meal_type)
);

CREATE TABLE IF NOT EXISTS meal_photos (
  id SERIAL PRIMARY KEY,
  meal_id INTEGER NOT NULL REFERENCES meal_records(id) ON DELETE CASCADE,
  photo_id INTEGER NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
  step VARCHAR(20),
  sort_order INTEGER DEFAULT 0 NOT NULL,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS meal_student_notes (
  id SERIAL PRIMARY KEY,
  meal_id INTEGER NOT NULL REFERENCES meal_records(id) ON DELETE CASCADE,
  student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  remark TEXT NOT NULL,
  photo_id INTEGER REFERENCES photos(id),
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

INSERT INTO system_config (config_key, config_value, description) VALUES
('tuition_fee', '2800', '每月托管费'),
('meal_fee', '500', '每月餐费'),
('material_fee', '200', '每学期材料费'),
('school_name', '智慧托班', '托班名称'),
('welcome_message', '用心陪伴每一个孩子', '欢迎语')
ON CONFLICT (config_key) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_students_status ON students(status);
CREATE INDEX IF NOT EXISTS idx_student_parents_student ON student_parents(student_id);
CREATE INDEX IF NOT EXISTS idx_student_parents_parent ON student_parents(parent_id);
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance_records(date);
CREATE INDEX IF NOT EXISTS idx_attendance_student_date ON attendance_records(student_id, date);
CREATE INDEX IF NOT EXISTS idx_photos_type ON photos(photo_type);
CREATE INDEX IF NOT EXISTS idx_photos_featured ON photos(is_featured) WHERE is_featured = TRUE;
CREATE INDEX IF NOT EXISTS idx_photo_students_student ON photo_students(student_id);
CREATE INDEX IF NOT EXISTS idx_homework_student_date ON homework_records(student_id, homework_date);
CREATE INDEX IF NOT EXISTS idx_homework_subject ON homework_records(subject);
CREATE INDEX IF NOT EXISTS idx_notices_active ON notices(is_active, display_start, display_end);
CREATE INDEX IF NOT EXISTS idx_remarks_student_date ON teacher_remarks(student_id, record_date);
CREATE INDEX IF NOT EXISTS idx_payments_student ON payment_records(student_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payment_records(status);
CREATE INDEX IF NOT EXISTS idx_parent_bindings_openid ON parent_bindings(wechat_openid);
CREATE INDEX IF NOT EXISTS idx_meal_student_notes_student ON meal_student_notes(student_id);
