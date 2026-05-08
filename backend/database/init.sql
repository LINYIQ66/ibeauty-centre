
-- I BEAUTY 预约系统数据库
-- by 安妮 · Knowledge Engineer Agent

CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    name_en TEXT,
    duration INTEGER NOT NULL,
    price REAL NOT NULL,
    category TEXT,
    description TEXT,
    active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    name_en TEXT,
    role TEXT,
    specialty TEXT,
    phone TEXT,
    active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT UNIQUE,
    email TEXT,
    total_spent REAL DEFAULT 0,
    visit_count INTEGER DEFAULT 0,
    last_visit DATETIME,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    service_id INTEGER,
    employee_id INTEGER,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    duration INTEGER,
    price REAL,
    status TEXT DEFAULT 'pending',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (service_id) REFERENCES services(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

CREATE TABLE IF NOT EXISTS operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    user_info TEXT,
    details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 插入初始数据
INSERT INTO services (name, name_en, duration, price, category, description) VALUES
('深层清洁 Facial', 'Deep Cleansing Facial', 60, 68, 'facial', '彻底清洁毛孔，去除黑头'),
('补水嫩肤 Facial', 'Hydration Facial', 75, 88, 'facial', '深层补水，改善肌肤干燥'),
('美白祛斑 Facial', 'Whitening Facial', 90, 108, 'facial', '淡化色斑，提亮肤色'),
('抗衰除皱 Facial', 'Anti-Aging Facial', 110, 128, 'facial', '减少细纹，紧致肌肤'),
('暗疮护理 Facial', 'Acne Treatment', 120, 138, 'facial', '针对痘痘肌肤的专业护理'),
('全身放松按摩', 'Relaxing Massage', 60, 68, 'massage', '舒缓压力，放松全身肌肉'),
('消脂塑型按摩', 'Slimming Massage', 60, 88, 'massage', '帮助塑形，减少脂肪'),
('经络排毒按摩', 'Meridian Detox', 90, 199, 'massage', '疏通经络，排毒养生'),
('艾灸养生', 'Moxibustion', 60, 88, 'wellness', '温经散寒，调理身体'),
('嫁接睫毛', 'Eyelash Extensions', 90, 68, 'beauty', '自然浓密睫毛效果');

INSERT INTO employees (name, name_en, role, specialty, phone) VALUES
('Annie', 'Annie', '高级美容师', 'Facial Specialist', '93391705'),
('Mei', 'Mei', '按摩专家', 'Massage Therapist', '93391705'),
('Lin', 'Lin', '美容师', 'Beauty Therapist', '93391705');

-- 创建索引
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_clients_phone ON clients(phone);
