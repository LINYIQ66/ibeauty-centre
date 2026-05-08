-- =====================================================
-- I BEAUTY 数据完整化迁移脚本
-- 添加统计报表、排班管理等增强功能
-- =====================================================

-- 1️⃣ 员工排班表
CREATE TABLE IF NOT EXISTS employee_schedules (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    schedule_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_working BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_id, schedule_date)
);

-- 2️⃣ 每日统计快照表（用于报表）
CREATE TABLE IF NOT EXISTS daily_stats (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL UNIQUE,
    total_appointments INTEGER DEFAULT 0,
    confirmed_appointments INTEGER DEFAULT 0,
    cancelled_appointments INTEGER DEFAULT 0,
    total_revenue DECIMAL(10,2) DEFAULT 0,
    new_clients INTEGER DEFAULT 0,
    working_employees INTEGER DEFAULT 0,
    avg_service_duration DECIMAL(5,2),
    peak_hour INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3️⃣ 每月统计汇总表
CREATE TABLE IF NOT EXISTS monthly_stats (
    id SERIAL PRIMARY KEY,
    stat_month DATE NOT NULL UNIQUE,  -- 每月 1 号
    total_appointments INTEGER DEFAULT 0,
    total_revenue DECIMAL(10,2) DEFAULT 0,
    total_clients INTEGER DEFAULT 0,
    new_clients INTEGER DEFAULT 0,
    returning_clients INTEGER DEFAULT 0,
    top_service_id INTEGER REFERENCES services(id),
    top_employee_id INTEGER REFERENCES employees(id),
    avg_daily_revenue DECIMAL(10,2),
    cancellation_rate DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4️⃣ 服务类别表
CREATE TABLE IF NOT EXISTS service_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    name_en VARCHAR(50),
    description TEXT,
    display_order INTEGER DEFAULT 0,
    icon VARCHAR(50),
    active BOOLEAN DEFAULT true
);

-- 5️⃣ 预约来源追踪
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'walk-in';
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50);

-- 6️⃣ 客户标签系统
CREATE TABLE IF NOT EXISTS client_tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(7) DEFAULT '#666666',
    description TEXT
);

CREATE TABLE IF NOT EXISTS client_tag_map (
    client_id INTEGER REFERENCES clients(id),
    tag_id INTEGER REFERENCES client_tags(id),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (client_id, tag_id)
);

-- 7️⃣ 客户消费记录
CREATE TABLE IF NOT EXISTS client_transactions (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    appointment_id INTEGER REFERENCES appointments(id),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    service_id INTEGER REFERENCES services(id),
    employee_id INTEGER REFERENCES employees(id),
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50),
    payment_status VARCHAR(20) DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8️⃣ 产品库存表
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    cost DECIMAL(10,2),
    price DECIMAL(10,2),
    stock_quantity INTEGER DEFAULT 0,
    reorder_level INTEGER DEFAULT 10,
    supplier VARCHAR(100),
    last_restock_date DATE,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9️⃣ 产品使用记录（关联服务）
CREATE TABLE IF NOT EXISTS product_usage (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    appointment_id INTEGER REFERENCES appointments(id),
    quantity_used DECIMAL(10,2) NOT NULL,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- 🔟 系统设置表
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT,
    setting_type VARCHAR(20) DEFAULT 'text',
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 初始化系统设置
INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('business_name', 'I BEAUTY CENTRE', 'text', '店铺名称'),
('business_hours_start', '09:00', 'time', '营业时间开始'),
('business_hours_end', '23:00', 'time', '营业时间结束'),
('slot_duration', '30', 'number', '预约时段长度（分钟）'),
('currency', 'SGD', 'text', '货币单位'),
('timezone', 'Asia/Singapore', 'text', '时区'),
('whatsapp_number', '6593391705', 'text', 'WhatsApp 业务号码'),
('auto_confirm', 'false', 'boolean', '自动确认预约'),
('sms_notifications', 'true', 'boolean', '启用短信通知'),
('email_notifications', 'true', 'boolean', '启用邮件通知')
ON CONFLICT (setting_key) DO NOTHING;

-- 初始化服务类别
INSERT INTO service_categories (name, name_en, description, display_order, icon) VALUES
('Facial 护理', 'Facial', '面部护理系列', 1, '💆‍♀️'),
('按摩理疗', 'Massage', '身体按摩系列', 2, '💆'),
('美甲美睫', 'Nails & Lashes', '美甲睫毛服务', 3, '💅'),
('养生调理', 'Wellness', '健康养生服务', 4, '🌿')
ON CONFLICT DO NOTHING;

-- 初始化客户标签
INSERT INTO client_tags (name, color, description) VALUES
('VIP', '#FFD700', '高价值客户'),
('新客', '#4CAF50', '首次到店客户'),
('常客', '#2196F3', '经常光顾'),
('敏感肌', '#FF9800', '敏感肌肤'),
('预约偏好 - 早上', '#9C27B0', '喜欢早上预约'),
('预约偏好 - 下午', '#FF5722', '喜欢下午预约')
ON CONFLICT (name) DO NOTHING;

-- 📊 统计报表视图增强
CREATE OR REPLACE VIEW v_business_overview AS
SELECT 
    CURRENT_DATE as report_date,
    (SELECT COUNT(*) FROM appointments WHERE appointment_date = CURRENT_DATE) as today_appointments,
    (SELECT COUNT(*) FROM appointments WHERE appointment_date = CURRENT_DATE AND status = 'confirmed') as today_confirmed,
    (SELECT COUNT(*) FROM appointments WHERE appointment_date = CURRENT_DATE AND status = 'pending') as today_pending,
    (SELECT COALESCE(SUM(price), 0) FROM appointments WHERE appointment_date = CURRENT_DATE AND status IN ('confirmed', 'completed')) as today_revenue,
    (SELECT COUNT(*) FROM appointments WHERE appointment_date = CURRENT_DATE + INTERVAL '1 day') as tomorrow_appointments,
    (SELECT COUNT(DISTINCT client_id) FROM appointments WHERE appointment_date >= CURRENT_DATE - INTERVAL '30 days') as active_clients_30d,
    (SELECT COUNT(*) FROM employees WHERE active = true) as active_employees;

CREATE OR REPLACE VIEW v_revenue_stats AS
SELECT 
    DATE_TRUNC('month', appointment_date) as month,
    COUNT(*) as total_appointments,
    COALESCE(SUM(price), 0) as total_revenue,
    COALESCE(AVG(price), 0) as avg_transaction,
    COUNT(DISTINCT client_id) as unique_clients
FROM appointments
WHERE status IN ('confirmed', 'completed')
GROUP BY DATE_TRUNC('month', appointment_date)
ORDER BY month DESC;

CREATE OR REPLACE VIEW v_employee_performance AS
SELECT 
    e.id,
    e.name,
    e.role,
    COUNT(a.id) as total_appointments,
    COUNT(a.id) FILTER (WHERE a.appointment_date = CURRENT_DATE) as today_appointments,
    COALESCE(SUM(a.price), 0) as weekly_revenue,
    COALESCE(AVG(a.price), 0) as avg_transaction,
    ROUND(COALESCE(AVG(r.rating), 5.0)::numeric, 1) as rating
FROM employees e
LEFT JOIN appointments a ON e.id = a.employee_id 
    AND a.status IN ('confirmed', 'completed')
    AND a.appointment_date >= CURRENT_DATE - INTERVAL '7 days'
LEFT JOIN (SELECT appointment_id, 5.0 as rating FROM appointments WHERE status = 'completed') r ON a.id = r.appointment_id
WHERE e.active = true
GROUP BY e.id, e.name, e.role
ORDER BY weekly_revenue DESC;

-- ⚡ 自动统计触发器函数
CREATE OR REPLACE FUNCTION update_daily_stats()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO daily_stats (stat_date, total_appointments, confirmed_appointments, cancelled_appointments, total_revenue, new_clients)
    SELECT 
        NEW.appointment_date,
        COUNT(*),
        COUNT(*) FILTER (WHERE status = 'confirmed'),
        COUNT(*) FILTER (WHERE status = 'cancelled'),
        COALESCE(SUM(price), 0),
        COUNT(DISTINCT client_id) FILTER (WHERE created_at >= NEW.appointment_date)
    FROM appointments
    WHERE appointment_date = NEW.appointment_date
    GROUP BY appointment_date
    ON CONFLICT (stat_date) DO UPDATE SET
        total_appointments = EXCLUDED.total_appointments,
        confirmed_appointments = EXCLUDED.confirmed_appointments,
        cancelled_appointments = EXCLUDED.cancelled_appointments,
        total_revenue = EXCLUDED.total_revenue,
        new_clients = EXCLUDED.new_clients,
        updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
DROP TRIGGER IF EXISTS trg_update_daily_stats ON appointments;
CREATE TRIGGER trg_update_daily_stats
    AFTER INSERT OR UPDATE OR DELETE ON appointments
    FOR EACH ROW
    EXECUTE FUNCTION update_daily_stats();

-- 📝 添加注释
COMMENT ON TABLE employee_schedules IS '员工排班表';
COMMENT ON TABLE daily_stats IS '每日统计快照';
COMMENT ON TABLE monthly_stats IS '每月统计汇总';
COMMENT ON TABLE client_transactions IS '客户消费记录';
COMMENT ON TABLE product_usage IS '产品使用记录';
COMMENT ON VIEW v_business_overview IS '业务总览视图';
COMMENT ON VIEW v_revenue_stats IS '收入统计视图';
COMMENT ON VIEW v_employee_performance IS '员工业绩视图';

SELECT '✅ 数据完整化迁移完成！' as status;
