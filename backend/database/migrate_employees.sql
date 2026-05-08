
-- 添加员工离职相关字段
ALTER TABLE employees ADD COLUMN IF NOT EXISTS departure_date TIMESTAMP;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS departure_reason TEXT;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 创建触发器自动更新 updated_at
CREATE OR REPLACE FUNCTION update_employee_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_employee_updated_at ON employees;
CREATE TRIGGER update_employee_updated_at
    BEFORE UPDATE ON employees
    FOR EACH ROW
    EXECUTE FUNCTION update_employee_updated_at();

-- 插入测试数据（如果为空）
DO $$
BEGIN
    IF (SELECT COUNT(*) FROM employees) = 0 THEN
        INSERT INTO employees (name, name_en, role, specialty, phone, active) VALUES
        ('Annie', 'Annie', '高级美容师', 'Facial 护理', '93391705', true),
        ('Mei', 'Mei', '按摩专家', '经络调理', '93391705', true),
        ('Lin', 'Lin', '美容师', '美甲睫毛', '93391705', true);
    END IF;
END $$;

SELECT 'Migration completed!' as status;
