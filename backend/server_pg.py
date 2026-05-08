#!/usr/bin/env python3
"""
I BEAUTY 预约系统后端 API - PostgreSQL 版本
by 安妮 · Knowledge Engineer Agent
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from datetime import datetime, timedelta
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import parse_qs, urlparse

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ibeauty_appointments',
    'user': 'ibeauty_user',
    'password': 'ibeauty2026'
}

LOG_PATH = "/tmp/ibeauty-app/backend/logs/appointments.log"

def calculate_end_time(start_time_str, duration_minutes):
    """计算结束时间"""
    if not start_time_str:
        return None
    try:
        # 解析开始时间 (格式：HH:MM)
        parts = start_time_str.split(':')
        start_minutes = int(parts[0]) * 60 + int(parts[1])
        
        # 计算结束时间（分钟）
        end_minutes = start_minutes + duration_minutes
        
        # 转换为 HH:MM 格式
        end_hour = end_minutes // 60
        end_minute = end_minutes % 60
        
        return f"{end_hour:02d}:{end_minute:02d}"
    except:
        return None

def get_db_connection():
    """获取数据库连接"""
    return psycopg2.connect(**DB_CONFIG)

def log_operation(action, entity_type, entity_id, details):
    """记录操作日志（同时写入数据库和文件）"""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    
    # 写入文件日志
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details
    }
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    # 写入数据库日志
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO operation_logs (action, entity_type, entity_id, details)
            VALUES (%s, %s, %s, %s)
        """, (action, entity_type, entity_id, json.dumps(details, ensure_ascii=False)))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Log to DB failed: {e}")

class BookingAPIHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        # 处理 datetime 和 Decimal 序列化
        from decimal import Decimal
        def json_default(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=json_default).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        params = parse_qs(parsed_path.query)
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            if path == '/api/services':
                cur.execute("SELECT * FROM services WHERE active = true ORDER BY id")
                services = cur.fetchall()
                # 转换为普通字典并处理 decimal
                result = []
                for s in services:
                    d = dict(s)
                    d['price'] = float(d['price']) if d['price'] else 0
                    result.append(d)
                self.send_json({"services": result})
            
            elif path == '/api/employees/all':
                cur.execute("SELECT * FROM employees ORDER BY id")
                employees = cur.fetchall()
                self.send_json({"employees": [dict(e) for e in employees]})
            
            elif path == '/api/client-tags':
                cur.execute("SELECT * FROM client_tags ORDER BY id")
                tags = cur.fetchall()
                self.send_json({"tags": [dict(t) for t in tags]})
            
            elif path == '/api/employees':
                cur.execute("SELECT * FROM employees WHERE active = true ORDER BY id")
                employees = cur.fetchall()
                self.send_json({"employees": [dict(e) for e in employees]})
            
            elif path == '/api/clients':
                cur.execute("""
                    SELECT c.*, 
                           COALESCE(COUNT(a.id), 0) as total_visits,
                           COALESCE(SUM(a.price), 0) as total_spent,
                           MAX(a.appointment_date) as last_visit
                    FROM clients c
                    LEFT JOIN appointments a ON c.id = a.client_id AND a.status != 'cancelled'
                    GROUP BY c.id
                    ORDER BY c.created_at DESC
                """)
                clients = cur.fetchall()
                
                # 获取每个客户的标签
                result = []
                for c in clients:
                    client_dict = dict(c)
                    cur.execute("""
                        SELECT t.id, t.name, t.color
                        FROM client_tags t
                        JOIN client_tag_map m ON t.id = m.tag_id
                        WHERE m.client_id = %s
                    """, (c['id'],))
                    client_dict['tags'] = [dict(t) for t in cur.fetchall()]
                    client_dict['total_spent'] = float(client_dict['total_spent']) if client_dict['total_spent'] else 0
                    result.append(client_dict)
                
                self.send_json({"clients": result})
            
            elif path.startswith('/api/appointments'):
                date_filter = params.get('date', [None])[0]
                
                if date_filter:
                    cur.execute("""
                        SELECT a.*, c.name as client_name, c.phone as client_phone,
                               s.name as service_name, e.name as employee_name
                        FROM appointments a
                        LEFT JOIN clients c ON a.client_id = c.id
                        LEFT JOIN services s ON a.service_id = s.id
                        LEFT JOIN employees e ON a.employee_id = e.id
                        WHERE a.appointment_date = %s
                        ORDER BY a.appointment_time
                    """, (date_filter,))
                else:
                    cur.execute("""
                        SELECT a.*, c.name as client_name, c.phone as client_phone,
                               s.name as service_name, e.name as employee_name
                        FROM appointments a
                        LEFT JOIN clients c ON a.client_id = c.id
                        LEFT JOIN services s ON a.service_id = s.id
                        LEFT JOIN employees e ON a.employee_id = e.id
                        ORDER BY a.appointment_date DESC, a.appointment_time DESC
                        LIMIT 50
                    """)
                
                appointments = cur.fetchall()
                result = []
                for a in appointments:
                    d = dict(a)
                    d['price'] = float(d['price']) if d['price'] else 0
                    if 'created_at' in d and d['created_at']:
                        d['created_at'] = d['created_at'].isoformat()
                    result.append(d)
                
                self.send_json({"appointments": result})
            
            elif path.startswith('/api/availability'):
                employee_id = int(params.get('employee_id', [1])[0])
                date = params.get('date', [datetime.now().strftime("%Y-%m-%d")])[0]
                duration = int(params.get('duration', [60])[0])
                
                # 获取当天该员工已预约的时间段
                cur.execute("""
                    SELECT appointment_time, duration, status
                    FROM appointments
                    WHERE employee_id = %s AND appointment_date = %s AND status != 'cancelled'
                    ORDER BY appointment_time
                """, (employee_id, date))
                
                booked = cur.fetchall()
                booked_slots = []
                for b in booked:
                    start_minutes = b['appointment_time'].total_seconds() // 60
                    end_minutes = start_minutes + b['duration']
                    booked_slots.append({
                        'start': start_minutes,
                        'end': end_minutes
                    })
                
                # 营业时间：9:00 - 23:00（早上 9 点到晚上 11 点）
                open_time = 9 * 60    # 09:00
                close_time = 23 * 60  # 23:00
                
                slots = []
                for minutes in range(open_time, close_time, 30):
                    # 检查是否与已预约时间冲突
                    is_booked = False
                    for booked_slot in booked_slots:
                        # 检查重叠
                        if not (minutes + duration <= booked_slot['start'] or minutes >= booked_slot['end']):
                            is_booked = True
                            break
                    
                    # 检查是否超出营业时间
                    if minutes + duration > close_time:
                        is_booked = True
                    
                    time_str = f"{int(minutes//60):02d}:{int(minutes%60):02d}"
                    slots.append({
                        'time': time_str,
                        'available': not is_booked
                    })
                
                self.send_json({
                    'slots': slots,
                    'date': date,
                    'employee_id': employee_id
                })
            
            elif path == '/api/stats':
                today = datetime.now().strftime("%Y-%m-%d")
                tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                
                # 今日统计
                cur.execute("""
                    SELECT COUNT(*) as total,
                           COUNT(*) FILTER (WHERE status = 'confirmed') as confirmed,
                           COUNT(*) FILTER (WHERE status = 'pending') as pending,
                           COALESCE(SUM(price) FILTER (WHERE status = 'confirmed'), 0) as revenue
                    FROM appointments WHERE appointment_date = %s
                """, (today,))
                today_stats = cur.fetchone()
                
                # 明日统计
                cur.execute("SELECT COUNT(*) as total FROM appointments WHERE appointment_date = %s", (tomorrow,))
                tomorrow_stats = cur.fetchone()
                
                # 本周收入
                cur.execute("""
                    SELECT COALESCE(SUM(price), 0) as total
                    FROM appointments
                    WHERE status IN ('confirmed', 'completed')
                    AND appointment_date >= DATE_TRUNC('week', CURRENT_DATE)
                """)
                weekly_stats = cur.fetchone()
                
                # 本月取消
                cur.execute("""
                    SELECT COUNT(*) as total
                    FROM appointments
                    WHERE status = 'cancelled'
                    AND appointment_date >= DATE_TRUNC('month', CURRENT_DATE)
                """)
                cancelled_stats = cur.fetchone()
                
                # 总统计（所有时间，所有状态）
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_appointments,
                        COUNT(DISTINCT client_id) as total_clients,
                        COALESCE(SUM(price), 0) as total_revenue
                    FROM appointments
                """)
                total_stats = cur.fetchone()
                
                # 今日新增客户
                cur.execute("""
                    SELECT COUNT(*) as new_clients
                    FROM clients
                    WHERE created_at >= CURRENT_DATE
                """)
                new_clients = cur.fetchone()
                
                # VIP 客户数
                cur.execute("""
                    SELECT COUNT(*) as vip_clients
                    FROM clients
                    WHERE membership_level = 'vip'
                """)
                vip_stats = cur.fetchone()
                
                self.send_json({
                    'today_count': today_stats['total'] or 0,
                    'today_confirmed': today_stats['confirmed'] or 0,
                    'today_pending': today_stats['pending'] or 0,
                    'today_revenue': float(today_stats['revenue']) if today_stats['revenue'] else 0,
                    'tomorrow_count': tomorrow_stats['total'] or 0,
                    'weekly_revenue': float(weekly_stats['total']) if weekly_stats['total'] else 0,
                    'monthly_cancelled': cancelled_stats['total'] or 0,
                    'total_appointments': total_stats['total_appointments'] or 0,
                    'total_clients': total_stats['total_clients'] or 0,
                    'total_revenue': float(total_stats['total_revenue']) if total_stats['total_revenue'] else 0,
                    'new_clients_today': new_clients['new_clients'] or 0,
                    'vip_clients': vip_stats['vip_clients'] or 0,
                    'avg_order_value': float(total_stats['total_revenue'] / max(total_stats['total_clients'], 1)) if total_stats['total_revenue'] else 0
                })
            
            elif path == '/api/logs':
                limit = int(params.get('limit', [50])[0])
                cur.execute("""
                    SELECT * FROM operation_logs
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))
                logs = cur.fetchall()
                result = []
                for log in logs:
                    d = dict(log)
                    if 'created_at' in d and d['created_at']:
                        d['created_at'] = d['created_at'].isoformat()
                    result.append(d)
                self.send_json({"logs": result})
            
            else:
                self.send_json({"error": "Not found"}, 404)
        
        except Exception as e:
            self.send_json({"error": str(e)}, 500)
        
        finally:
            cur.close()
            conn.close()
    
    def do_POST(self):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(body)
        except:
            self.send_json({"error": "Invalid JSON"}, 400)
            return
        
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            if path == '/api/appointments/reschedule':
                # 改期专用端点
                apt_id = data.get('appointment_id')
                new_date = data.get('date')
                new_time = data.get('time')
                
                if not apt_id or not new_date or not new_time:
                    self.send_json({"error": "appointment_id, date, and time required"}, 400)
                    return
                
                # 检查预约是否存在
                cur.execute("SELECT * FROM appointments WHERE id = %s", (apt_id,))
                apt = cur.fetchone()
                
                if not apt:
                    self.send_json({"error": "Appointment not found"}, 404)
                    return
                
                employee_id = data.get('employee_id', apt['employee_id'])
                duration = data.get('duration', apt['duration'])
                
                # 计算结束时间
                time_parts = new_time.split(':')
                start_minutes = int(time_parts[0]) * 60 + int(time_parts[1])
                end_minutes = start_minutes + duration
                end_hour = end_minutes // 60
                end_min = end_minutes % 60
                new_end_time = f"{end_hour:02d}:{end_min:02d}"
                
                # 检查时间冲突
                cur.execute("""
                    SELECT id FROM appointments
                    WHERE employee_id = %s
                    AND appointment_date = %s
                    AND status != 'cancelled'
                    AND id != %s
                    AND (
                        (appointment_time < %s AND appointment_end_time > %s) OR
                        (appointment_time >= %s AND appointment_time < %s)
                    )
                """, (employee_id, new_date, apt_id, new_time, new_end_time, new_time, new_end_time))
                
                conflict = cur.fetchone()
                if conflict:
                    self.send_json({"success": False, "error": "该时间段已被占用"}, 409)
                    return
                
                # 执行改期
                cur.execute("""
                    UPDATE appointments SET
                        appointment_date = %s,
                        appointment_time = %s,
                        appointment_end_time = %s,
                        status = 'pending',
                        rescheduled_from = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING *
                """, (new_date, new_time, new_end_time,
                      f"{apt['appointment_date']} {str(apt['appointment_time'])[:5]}", apt_id))
                
                updated_apt = cur.fetchone()
                conn.commit()
                
                log_operation("RESCHEDULE", "appointment", apt_id, {
                    "from": f"{apt['appointment_date']} {str(apt['appointment_time'])[:5]}",
                    "to": f"{new_date} {new_time[:5]}"
                })
                
                self.send_json({"success": True, "appointment": dict(updated_apt)})
            
            elif self.path == '/api/appointments':
                # 创建预约
                client_phone = data.get('client_phone')
                client_name = data.get('client_name')
                
                # 查找或创建客户
                cur.execute("SELECT id FROM clients WHERE phone = %s", (client_phone,))
                client = cur.fetchone()
                
                if client:
                    client_id = client['id']
                    # 更新客户信息
                    cur.execute("""
                        UPDATE clients
                        SET name = %s, visit_count = visit_count + 1, last_visit = CURRENT_DATE
                        WHERE id = %s
                    """, (client_name, client_id))
                else:
                    # 创建新客户
                    cur.execute("""
                        INSERT INTO clients (name, phone, visit_count, last_visit)
                        VALUES (%s, %s, 1, CURRENT_DATE)
                        RETURNING id
                    """, (client_name, client_phone))
                    client_id = cur.fetchone()['id']
                
                # 创建预约
                cur.execute("""
                    INSERT INTO appointments (
                        client_id, service_id, employee_id,
                        appointment_date, appointment_time, appointment_end_time,
                        duration, price, status, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    client_id,
                    data.get('service_id'),
                    data.get('employee_id'),
                    data.get('date'),
                    data.get('time'),
                    calculate_end_time(data.get('time'), data.get('duration')),
                    data.get('duration'),
                    data.get('price'),
                    'pending',
                    data.get('notes', '')
                ))
                
                apt_id = cur.fetchone()['id']
                
                # 获取完整预约信息
                cur.execute("""
                    SELECT a.*, c.name as client_name, c.phone as client_phone,
                           s.name as service_name, e.name as employee_name
                    FROM appointments a
                    LEFT JOIN clients c ON a.client_id = c.id
                    LEFT JOIN services s ON a.service_id = s.id
                    LEFT JOIN employees e ON a.employee_id = e.id
                    WHERE a.id = %s
                """, (apt_id,))
                
                new_apt = cur.fetchone()
                conn.commit()
                
                # 记录日志
                log_operation("CREATE", "appointment", apt_id, {
                    "client": client_name,
                    "service": data.get('service_name'),
                    "date": data.get('date'),
                    "time": data.get('time')
                })
                
                self.send_json({"success": True, "appointment": dict(new_apt)}, 201)
            
            elif self.path == '/api/clients':
                # 新增客户
                cur.execute("""
                    INSERT INTO clients (name, phone, gender, email, birthday, address, notes, membership_level)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    data.get('name'),
                    data.get('phone'),
                    data.get('gender'),
                    data.get('email'),
                    data.get('birthday'),
                    data.get('address'),
                    data.get('notes'),
                    data.get('membership_level', 'regular')
                ))
                
                client_id = cur.fetchone()['id']
                
                # 保存标签
                tags = data.get('tags', [])
                for tag in tags:
                    cur.execute("""
                        INSERT INTO client_tag_map (client_id, tag_id)
                        VALUES (%s, %s)
                        ON CONFLICT (client_id, tag_id) DO NOTHING
                    """, (client_id, tag.get('id')))
                
                # 获取完整客户信息
                cur.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
                new_client = cur.fetchone()
                conn.commit()
                
                log_operation("CREATE", "client", client_id, {"name": data.get('name')})
                self.send_json({"success": True, "client": dict(new_client)}, 201)
            
            elif self.path == '/api/client-tags':
                # 创建标签（后端管理用）
                cur.execute("""
                    INSERT INTO client_tags (name, color, description)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (
                    data.get('name'),
                    data.get('color', '#3b82f6'),
                    data.get('description', '')
                ))
                tag_id = cur.fetchone()['id']
                conn.commit()
                self.send_json({"success": True, "tag": {"id": tag_id}}, 201)
            
            elif self.path == '/api/employees':
                # 新增员工
                cur.execute("""
                    INSERT INTO employees (name, role, specialty, phone, email, active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    data.get('name'),
                    data.get('role', '美容师'),
                    data.get('specialty', ''),
                    data.get('phone', ''),
                    data.get('email', ''),
                    data.get('active', True)
                ))
                
                emp_id = cur.fetchone()['id']
                
                # 获取完整员工信息
                cur.execute("SELECT * FROM employees WHERE id = %s", (emp_id,))
                new_emp = cur.fetchone()
                conn.commit()
                
                # 记录日志
                log_operation("CREATE", "employee", emp_id, {
                    "name": data.get('name'),
                    "role": data.get('role')
                })
                
                self.send_json({"success": True, "employee": dict(new_emp)}, 201)
            
            elif self.path == '/api/chat':
                # 聊天处理（简化版本）
                message = data.get('message', '')
                
                response_text = "您好！我是 I BEAUTY 预约助手 💆‍♀️\n我可以帮您预约服务、查询预约。\n请问有什么可以帮您？"
                options = ["预约 Facial", "预约按摩", "我的预约"]
                
                if "预约" in message:
                    if "facial" in message.lower() or "护理" in message:
                        response_text = "好的，请问您想预约哪种面部护理？\n1. 深层清洁 ($68)\n2. 补水嫩肤 ($88)\n3. 美白祛斑 ($108)"
                        options = ["深层清洁", "补水嫩肤", "美白祛斑"]
                    elif "按摩" in message:
                        response_text = "好的，请问您想预约哪种按摩？\n1. 全身放松 ($68)\n2. 消脂塑型 ($88)\n3. 经络排毒 ($199)"
                        options = ["全身放松", "消脂塑型", "经络排毒"]
                
                conv_id = str(uuid.uuid4())[:8]
                self.send_json({
                    "conversation_id": conv_id,
                    "reply": response_text,
                    "options": options
                })
            
            else:
                self.send_json({"error": "Not found"}, 404)
        
        except Exception as e:
            conn.rollback()
            self.send_json({"error": str(e)}, 500)
        
        finally:
            cur.close()
            conn.close()
    
    def do_PATCH(self):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(body)
        except:
            self.send_json({"error": "Invalid JSON"}, 400)
            return
        
        try:
            if '/api/appointments/' in self.path:
                apt_id = int(self.path.split('/')[-1])
                
                # 检查预约是否存在
                cur.execute("SELECT * FROM appointments WHERE id = %s", (apt_id,))
                apt = cur.fetchone()
                
                if not apt:
                    self.send_json({"error": "Appointment not found"}, 404)
                    return
                
                updates = []
                values = []
                
                if "status" in data:
                    # 不允许删除，只能标记状态
                    if data["status"] == 'cancelled':
                        updates.append("status = %s, cancelled_at = CURRENT_TIMESTAMP")
                        values.append(data["status"])
                        
                        if "cancelled_reason" in data:
                            updates.append("cancelled_reason = %s")
                            values.append(data["cancelled_reason"])
                        
                        log_operation("CANCEL", "appointment", apt_id, {"reason": data.get("cancelled_reason")})
                    
                    elif data["status"] == 'rescheduled':
                        updates.append("status = %s")
                        values.append(data["status"])
                        log_operation("RESCHEDULE", "appointment", apt_id, data)
                    
                    else:
                        updates.append("status = %s")
                        values.append(data["status"])
                        log_operation("UPDATE", "appointment", apt_id, {"status": data["status"]})
                
                if "date" in data:
                    updates.append("appointment_date = %s")
                    values.append(data["date"])
                
                if "time" in data:
                    updates.append("appointment_time = %s")
                    values.append(data["time"])
                
                if updates:
                    values.append(apt_id)
                    query = f"UPDATE appointments SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING *"
                    cur.execute(query, values)
                    
                    updated_apt = cur.fetchone()
                    conn.commit()
                    
                    self.send_json({"success": True, "appointment": dict(updated_apt)})
                else:
                    self.send_json({"error": "No fields to update"}, 400)
            
            elif '/api/clients/' in self.path and self.path.endswith('/transactions'):
                client_id = int(self.path.split('/')[-2])
                cur.execute("""
                    SELECT t.*, s.name as service_name, e.name as employee_name
                    FROM client_transactions t
                    LEFT JOIN services s ON t.service_id = s.id
                    LEFT JOIN employees e ON t.employee_id = e.id
                    WHERE t.client_id = %s
                    ORDER BY t.transaction_date DESC
                    LIMIT 50
                """, (client_id,))
                transactions = cur.fetchall()
                self.send_json({"transactions": [dict(t) for t in transactions]})
            
            elif '/api/clients/' in self.path:
                # 更新客户
                client_id = int(self.path.split('/')[-1])
                
                cur.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
                client = cur.fetchone()
                
                if not client:
                    self.send_json({"error": "Client not found"}, 404)
                    return
                
                updates = []
                values = []
                
                for field in ['name', 'phone', 'gender', 'email', 'birthday', 'address', 'notes', 'membership_level']:
                    if field in data:
                        updates.append(f"{field} = %s")
                        values.append(data[field])
                
                if updates:
                    values.append(client_id)
                    query = f"UPDATE clients SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING *"
                    cur.execute(query, values)
                    updated_client = cur.fetchone()
                    
                    # 更新标签
                    if 'tags' in data:
                        # 删除旧标签
                        cur.execute("DELETE FROM client_tag_map WHERE client_id = %s", (client_id,))
                        # 添加新标签
                        for tag in data['tags']:
                            cur.execute("""
                                INSERT INTO client_tag_map (client_id, tag_id)
                                VALUES (%s, %s)
                                ON CONFLICT (client_id, tag_id) DO NOTHING
                            """, (client_id, tag.get('id')))
                    
                    conn.commit()
                    log_operation("UPDATE", "client", client_id, data)
                    self.send_json({"success": True, "client": dict(updated_client)})
                else:
                    self.send_json({"error": "No fields to update"}, 400)
            
            elif '/api/employees/' in self.path:
                emp_id = int(self.path.split('/')[-1])
                
                # 检查员工是否存在
                cur.execute("SELECT * FROM employees WHERE id = %s", (emp_id,))
                emp = cur.fetchone()
                
                if not emp:
                    self.send_json({"error": "Employee not found"}, 404)
                    return
                
                updates = []
                values = []
                
                if "name" in data:
                    updates.append("name = %s")
                    values.append(data["name"])
                
                if "role" in data:
                    updates.append("role = %s")
                    values.append(data["role"])
                
                if "specialty" in data:
                    updates.append("specialty = %s")
                    values.append(data["specialty"])
                
                if "phone" in data:
                    updates.append("phone = %s")
                    values.append(data["phone"])
                
                if "email" in data:
                    updates.append("email = %s")
                    values.append(data["email"])
                
                if "active" in data:
                    updates.append("active = %s")
                    values.append(data["active"])
                    if not data["active"]:
                        updates.append("departure_date = CURRENT_DATE")
                    log_operation("UPDATE", "employee", emp_id, {"active": data["active"]})
                else:
                    log_operation("UPDATE", "employee", emp_id, data)
                
                if updates:
                    values.append(emp_id)
                    query = f"UPDATE employees SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING *"
                    cur.execute(query, values)
                    
                    updated_emp = cur.fetchone()
                    conn.commit()
                    
                    self.send_json({"success": True, "employee": dict(updated_emp)})
                else:
                    self.send_json({"error": "No fields to update"}, 400)
            
            else:
                self.send_json({"error": "Not found"}, 404)
        
        except Exception as e:
            conn.rollback()
            self.send_json({"error": str(e)}, 500)
        
        finally:
            cur.close()
            conn.close()
    
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")

def run_server(port=8082):
    server = HTTPServer(('0.0.0.0', port), BookingAPIHandler)
    print(f"🚀 I BEAUTY API Server (PostgreSQL) running on port {port}")
    print(f"📍 http://localhost:{port}")
    print(f"🗄️  Database: PostgreSQL @ {DB_CONFIG['database']}")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
