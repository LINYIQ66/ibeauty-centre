
-- 1. 增强 clients 表
ALTER TABLE clients ADD COLUMN IF NOT EXISTS gender VARCHAR(20);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS email VARCHAR(100);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS birthday DATE;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS membership_level VARCHAR(50) DEFAULT 'regular';
ALTER TABLE clients ADD COLUMN IF NOT EXISTS total_spent DECIMAL(10,2) DEFAULT 0;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS total_visits INTEGER DEFAULT 0;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS last_visit DATE;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 2. 客户标签表
CREATE TABLE IF NOT EXISTS client_tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#3b82f6',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 客户 - 标签关联表
CREATE TABLE IF NOT EXISTS client_tag_map (
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES client_tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (client_id, tag_id)
);

-- 4. 客户消费记录表
CREATE TABLE IF NOT EXISTS client_transactions (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    appointment_id INTEGER REFERENCES appointments(id) ON DELETE SET NULL,
    service_id INTEGER REFERENCES services(id) ON DELETE SET NULL,
    employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    amount DECIMAL(10,2) NOT NULL,
    transaction_type VARCHAR(50) DEFAULT 'service',
    payment_method VARCHAR(50),
    payment_status VARCHAR(50) DEFAULT 'completed',
    points_earned INTEGER DEFAULT 0,
    points_used INTEGER DEFAULT 0,
    notes TEXT,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 创建索引加速查询
CREATE INDEX IF NOT EXISTS idx_clients_phone ON clients(phone);
CREATE INDEX IF NOT EXISTS idx_clients_membership ON clients(membership_level);
CREATE INDEX IF NOT EXISTS idx_clients_created ON clients(created_at);
CREATE INDEX IF NOT EXISTS idx_transactions_client ON client_transactions(client_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON client_transactions(transaction_date);

-- 6. 插入默认标签
INSERT INTO client_tags (name, color, description) VALUES
('VIP', '#fbbf24', '重要客户'),
('新客户', '#10b981', '首次到访'),
('常客', '#3b82f6', '频繁消费'),
('敏感肌', '#f43f5e', '皮肤敏感'),
('推销勿扰', '#6b7280', '不喜欢推销'),
('生日月', '#8b5cf6', '本月生日')
ON CONFLICT (name) DO NOTHING;

-- 7. 创建客户视图
CREATE OR REPLACE VIEW v_client_stats AS
SELECT 
    c.id,
    c.name,
    c.phone,
    c.membership_level,
    COUNT(DISTINCT a.id) as total_visits,
    COALESCE(SUM(a.price), 0) as total_spent,
    MAX(a.appointment_date) as last_visit,
    MIN(a.created_at) as first_visit
FROM clients c
LEFT JOIN appointments a ON c.id = a.client_id AND a.status != 'cancelled'
GROUP BY c.id, c.name, c.phone, c.membership_level;

-- 8. 自动更新 trigger
CREATE OR REPLACE FUNCTION update_client_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- 更新 client 总消费和访问次数
    UPDATE clients SET
        total_visits = (SELECT COUNT(*) FROM appointments WHERE client_id = NEW.client_id AND status != 'cancelled'),
        total_spent = (SELECT COALESCE(SUM(price), 0) FROM appointments WHERE client_id = NEW.client_id AND status != 'cancelled'),
        last_visit = NEW.appointment_date,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.client_id;
    
    -- 插入交易记录
    INSERT INTO client_transactions (
        client_id, appointment_id, service_id, employee_id,
        amount, transaction_type, payment_status
    ) VALUES (
        NEW.client_id, NEW.id, NEW.service_id, NEW.employee_id,
        NEW.price, 'service', 'completed'
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 9. 绑定 trigger
DROP TRIGGER IF EXISTS update_client_stats_trigger ON appointments;
CREATE TRIGGER update_client_stats_trigger
AFTER INSERT ON appointments
FOR EACH ROW
EXECUTE FUNCTION update_client_stats();

SELECT 'Customer management database setup completed!' as status;
