-- I BEAUTY 预约系统数据库架构
-- PostgreSQL 16
-- by 安妮 · Knowledge Engineer Agent

-- ═══════════════════════════════════════════════════════════
-- 服务表
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    duration INTEGER NOT NULL CHECK (duration > 0),
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    category VARCHAR(50),
    description TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ═══════════════════════════════════════════════════════════
-- 员工表
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    role VARCHAR(50),
    specialty VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ═══════════════════════════════════════════════════════════
-- 客户表
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(100),
    total_spent DECIMAL(10,2) DEFAULT 0,
    visit_count INTEGER DEFAULT 0,
    last_visit DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ═══════════════════════════════════════════════════════════
-- 预约表（核心表）
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    service_id INTEGER REFERENCES services(id),
    employee_id INTEGER REFERENCES employees(id),
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    appointment_end_time TIME,
    duration INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'cancelled', 'rescheduled', 'completed')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cancelled_at TIMESTAMP,
    cancelled_reason TEXT,
    rescheduled_from INTEGER REFERENCES appointments(id)
);

-- ═══════════════════════════════════════════════════════════
-- 操作日志表（审计）
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS operation_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    user_info JSONB,
    details JSONB,
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ═══════════════════════════════════════════════════════════
-- 对话记录表（聊天预约）
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(50) UNIQUE NOT NULL,
    platform VARCHAR(20),
    user_identifier VARCHAR(100),
    messages JSONB,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ═══════════════════════════════════════════════════════════
-- 索引优化
-- ═══════════════════════════════════════════════════════════
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_appointments_employee_date ON appointments(employee_id, appointment_date);
CREATE INDEX idx_appointments_time ON appointments(appointment_date, appointment_time);
CREATE INDEX idx_clients_phone ON clients(phone);
CREATE INDEX idx_operation_logs_entity ON operation_logs(entity_type, entity_id);
CREATE INDEX idx_operation_logs_created ON operation_logs(created_at);
CREATE INDEX idx_conversations_id ON conversations(conversation_id);

-- ═══════════════════════════════════════════════════════════
-- 触发器：自动更新 updated_at
-- ═══════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_services_updated_at BEFORE UPDATE ON services
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ═══════════════════════════════════════════════════════════
-- 视图：今日预约概览
-- ═══════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW v_today_appointments AS
SELECT 
    a.id,
    a.appointment_date,
    a.appointment_time,
    a.duration,
    a.price,
    a.status,
    c.name AS client_name,
    c.phone AS client_phone,
    s.name AS service_name,
    e.name AS employee_name
FROM appointments a
LEFT JOIN clients c ON a.client_id = c.id
LEFT JOIN services s ON a.service_id = s.id
LEFT JOIN employees e ON a.employee_id = e.id
WHERE a.appointment_date = CURRENT_DATE
ORDER BY a.appointment_time;

-- ═══════════════════════════════════════════════════════════
-- 视图：高价值客户（累计消费>$500）
-- ═══════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW v_high_value_clients AS
SELECT 
    c.id,
    c.name,
    c.phone,
    c.total_spent,
    c.visit_count,
    c.last_visit
FROM clients c
WHERE c.total_spent >= 500
ORDER BY c.total_spent DESC;

-- ═══════════════════════════════════════════════════════════
-- 插入初始数据
-- ═══════════════════════════════════════════════════════════

-- 服务
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

-- 员工
INSERT INTO employees (name, name_en, role, specialty, phone) VALUES
('Annie', 'Annie', '高级美容师', 'Facial Specialist', '93391705'),
('Mei', 'Mei', '按摩专家', 'Massage Therapist', '93391705'),
('Lin', 'Lin', '美容师', 'Beauty Therapist', '93391705');

-- ═══════════════════════════════════════════════════════════
-- 权限设置
-- ═══════════════════════════════════════════════════════════
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ibeauty_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ibeauty_user;

COMMENT ON DATABASE ibeauty_appointments IS 'I BEAUTY CENTRE 预约管理系统';
