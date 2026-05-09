#!/usr/bin/env python3
"""
I BEAUTY 预约系统后端 API
by 安妮 · Knowledge Engineer Agent
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import socket
from datetime import datetime, timedelta
import uuid
import re
from urllib.parse import urlparse, parse_qs
import cgi

DB_PATH = "/tmp/ibeauty-app/backend/database/data.json"
LOG_PATH = "/tmp/ibeauty-app/backend/logs/appointments.log"
VIDEOS_PATH = "/tmp/beauty_spa_photos/videos/"

# 初始化数据
def init_db():
    if not os.path.exists(DB_PATH):
        data = {
            "services": [
                {"id": 1, "name": "深层清洁 Facial", "name_en": "Deep Cleansing", "duration": 60, "price": 68, "category": "facial"},
                {"id": 2, "name": "补水嫩肤 Facial", "name_en": "Hydration Facial", "duration": 75, "price": 88, "category": "facial"},
                {"id": 3, "name": "美白祛斑 Facial", "name_en": "Whitening Facial", "duration": 90, "price": 108, "category": "facial"},
                {"id": 4, "name": "抗衰除皱 Facial", "name_en": "Anti-Aging Facial", "duration": 110, "price": 128, "category": "facial"},
                {"id": 5, "name": "暗疮护理 Facial", "name_en": "Acne Treatment", "duration": 120, "price": 138, "category": "facial"},
                {"id": 6, "name": "全身放松按摩", "name_en": "Relaxing Massage", "duration": 60, "price": 68, "category": "massage"},
                {"id": 7, "name": "消脂塑型按摩", "name_en": "Slimming Massage", "duration": 60, "price": 88, "category": "massage"},
                {"id": 8, "name": "经络排毒按摩", "name_en": "Meridian Detox", "duration": 90, "price": 199, "category": "massage"},
                {"id": 9, "name": "艾灸养生", "name_en": "Moxibustion", "duration": 60, "price": 88, "category": "wellness"},
                {"id": 10, "name": "嫁接睫毛", "name_en": "Eyelash Extensions", "duration": 90, "price": 68, "category": "beauty"}
            ],
            "client_tags": [
                {"id": 1, "name": "VIP", "color": "#f59e0b"},
                {"id": 2, "name": "常客", "color": "#25d366"},
                {"id": 3, "name": "新客户", "color": "#0088cc"},
                {"id": 4, "name": "敏感肌", "color": "#c41e3a"},
                {"id": 5, "name": "高消费", "color": "#9b59b6"}
            ],
            "commission_rules": [
                {"id": 1, "service_id": null, "service_name": "默认", "commission_type": "percentage", "commission_value": 30, "min_guarantee": 20},
                {"id": 2, "service_id": 1, "service_name": "深层清洁 Facial", "commission_type": "percentage", "commission_value": 25, "min_guarantee": 15},
                {"id": 3, "service_id": 5, "service_name": "暗疮护理 Facial", "commission_type": "percentage", "commission_value": 35, "min_guarantee": 25}
            ],
            "transactions": [
                {"id": 1, "date": "2026-05-08", "client_name": "林女士", "client_phone": "91234567", "service_name": "暗疮护理 Facial", "employee_name": "Lisa", "amount": 138, "payment_method": "现金", "status": "completed", "notes": "", "created_at": "2026-05-08T12:07:42"},
                {"id": 2, "date": "2026-05-08", "client_name": "测试客户", "client_phone": "88888888", "service_name": "深层清洁 Facial", "employee_name": "Annie", "amount": 68, "payment_method": "PayNow", "status": "completed", "notes": "Admin添加", "created_at": "2026-05-08T12:27:06"}
            ],
            "expenses": [
                {"id": 1, "date": "2026-05-01", "category": "租金", "description": "5月店铺租金", "amount": 5000, "payment_method": "银行转账", "notes": "", "created_at": "2026-05-01T09:00:00"},
                {"id": 2, "date": "2026-05-05", "category": "用品采购", "description": "Facial 护理产品补货", "amount": 850, "payment_method": "PayNow", "notes": "含深层清洁液、面膜", "created_at": "2026-05-05T10:30:00"},
                {"id": 3, "date": "2026-05-07", "category": "水电费", "description": "4月水电账单", "amount": 320, "payment_method": "GIRO", "notes": "", "created_at": "2026-05-07T08:00:00"},
                {"id": 4, "date": "2026-05-08", "category": "营销推广", "description": "小红书推广费", "amount": 500, "payment_method": "PayNow", "notes": "5月推广计划", "created_at": "2026-05-08T11:00:00"}
            ],
            "employee_commissions": [],
            "employees": [
                {"id": 1, "name": "Annie", "role": "高级美容师", "specialty": "Facial Specialist", "active": True},
                {"id": 2, "name": "Mei", "role": "按摩专家", "specialty": "Massage Therapist", "active": True},
                {"id": 3, "name": "Lin", "role": "美容师", "specialty": "Beauty Therapist", "active": True}
            ],
            "clients": [],
            "appointments": [],
            "conversations": []
        }
        save_db(data)
        log_operation("INIT", "system", 0, "Database initialized")
    else:
        # Migration: upgrade existing clients to full schema
        db = load_db()
        changed = False
        for c in db.get("clients", []):
            if "status" not in c:
                c["status"] = "active"
                c["gender"] = c.get("gender", "")
                c["birthday"] = c.get("birthday", "")
                c["email"] = c.get("email", "")
                c["address"] = c.get("address", "")
                c["notes"] = c.get("notes", "")
                c["membership_level"] = c.get("membership_level", "regular")
                c["tags"] = c.get("tags", [])
                c["total_visits"] = c.get("total_visits", c.get("visit_count", 0))
                c["total_spent"] = c.get("total_spent", 0)
                c["last_visit"] = c.get("last_visit")
                c["updated_at"] = c.get("updated_at", c.get("created_at"))
                if "visit_count" in c:
                    del c["visit_count"]
                changed = True
        if "client_tags" not in db:
            db["client_tags"] = [
                {"id": 1, "name": "VIP", "color": "#f59e0b"},
                {"id": 2, "name": "常客", "color": "#25d366"},
                {"id": 3, "name": "新客户", "color": "#0088cc"},
                {"id": 4, "name": "敏感肌", "color": "#c41e3a"},
                {"id": 5, "name": "高消费", "color": "#9b59b6"}
            ]
            changed = True
        if "transactions" not in db:
            db["transactions"] = []
            changed = True
        if "expenses" not in db:
            db["expenses"] = []
            changed = True
        if "employee_commissions" not in db:
            db["employee_commissions"] = []
            changed = True
        if "commission_rules" not in db:
            db["commission_rules"] = [
                {"id": 1, "service_id": None, "service_name": "默认", "commission_type": "percentage", "commission_value": 30, "min_guarantee": 20}
            ]
            changed = True
        if changed:
            save_db(db)
            log_operation("MIGRATE", "schema", 0, "Client data upgraded to full schema")
    return load_db()

def load_db():
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_db(data):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_operation(action, entity_type, entity_id, details):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details
    }
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

class BookingAPIHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        db = load_db()
        
        # 处理视频文件下载
        if self.path.startswith('/videos/'):
            filename = self.path.split('/videos/')[1]
            filepath = os.path.join(VIDEOS_PATH, filename)
            
            if os.path.exists(filepath) and os.path.isfile(filepath):
                self.send_response(200)
                # 根据文件扩展名设置 Content-Type
                if filename.endswith('.mp4'):
                    self.send_header('Content-Type', 'video/mp4')
                elif filename.endswith('.webm'):
                    self.send_header('Content-Type', 'video/webm')
                elif filename.endswith('.ogv') or filename.endswith('.ogg'):
                    self.send_header('Content-Type', 'video/ogg')
                else:
                    self.send_header('Content-Type', 'application/octet-stream')
                
                file_size = os.path.getsize(filepath)
                self.send_header('Content-Length', str(file_size))
                self.send_header('Content-Disposition', f'inline; filename="{filename}"')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                with open(filepath, 'rb') as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_response(404)
                self.end_headers()
                return
        
        if self.path == '/api/services':
            self.send_json({"services": db["services"]})
        
        elif self.path == '/api/employees':
            # 返回活跃员工
            active = [e for e in db["employees"] if e.get("active", True)]
            # 添加统计信息
            today = datetime.now().strftime("%Y-%m-%d")
            for emp in active:
                emp_today = [a for a in db["appointments"] if a["employee_id"] == emp["id"] and a["date"] == today]
                emp["today_apts"] = len([a for a in emp_today if a["status"] != "cancelled"])
                emp["weekly_revenue"] = sum(a["price"] for a in db["appointments"] if a["employee_id"] == emp["id"] and a["status"] == "confirmed")
                emp["rating"] = 5.0
            self.send_json({"employees": active})
        
        elif self.path == '/api/employees/all':
            # 返回所有员工（包括已离职）
            for emp in db["employees"]:
                emp_today = [a for a in db["appointments"] if a["employee_id"] == emp["id"]]
                emp["today_apts"] = len([a for a in emp_today if a["status"] != "cancelled"])
                emp["weekly_revenue"] = sum(a["price"] for a in db["appointments"] if a["employee_id"] == emp["id"] and a["status"] == "confirmed")
                emp["rating"] = 5.0
            self.send_json({"employees": db["employees"]})
        
        elif self.path == '/api/clients':
            self.send_json({"clients": db["clients"]})
        
        elif self.path == '/api/client-tags':
            tags = db.get("client_tags", [
                {"id": 1, "name": "VIP", "color": "#f59e0b"},
                {"id": 2, "name": "常客", "color": "#25d366"},
                {"id": 3, "name": "新客户", "color": "#0088cc"},
                {"id": 4, "name": "敏感肌", "color": "#c41e3a"},
                {"id": 5, "name": "高消费", "color": "#9b59b6"}
            ])
            self.send_json({"tags": tags})
        
        elif self.path.startswith('/api/clients/') and self.path.endswith('/transactions'):
            # GET /api/clients/{id}/transactions
            client_id = int(self.path.split('/')[3])
            # 从预约记录生成交易记录
            client_appts = [a for a in db["appointments"] if a.get("client_id") == client_id]
            transactions = []
            for apt in client_appts:
                transactions.append({
                    "id": apt["id"],
                    "transaction_date": apt.get("created_at", apt.get("date", "")),
                    "service_name": apt.get("service_name", "服务"),
                    "employee_name": apt.get("employee_name", ""),
                    "amount": apt.get("price", 0),
                    "status": "completed" if apt.get("status") == "confirmed" else apt.get("status", "pending")
                })
            self.send_json({"transactions": transactions})
        
        elif self.path.startswith('/api/clients/'):
            # GET /api/clients/{id}
            try:
                client_id = int(self.path.split('/')[-1])
                client = next((c for c in db["clients"] if c["id"] == client_id), None)
                if client:
                    self.send_json({"client": client})
                else:
                    self.send_json({"error": "Client not found"}, 404)
            except:
                self.send_json({"error": "Invalid client ID"}, 400)
        
        elif self.path.startswith('/api/appointments'):
            date_str = self.path.split('?date=')[-1] if '?date=' in self.path else None
            appointments = db["appointments"]
            if date_str:
                appointments = [a for a in appointments if a["date"] == date_str]
            self.send_json({"appointments": appointments})
        
        elif self.path.startswith('/api/availability'):
            # 查询可用时间段
            from urllib.parse import parse_qs, urlparse
            params = parse_qs(urlparse(self.path).query)
            employee_id = int(params.get('employee_id', [1])[0])
            date = params.get('date', [datetime.now().strftime("%Y-%m-%d")])[0]
            duration = int(params.get('duration', [60])[0])
            
            slots = []
            for hour in range(9, 21):
                for minute in [0, 30]:
                    time_str = f"{hour:02d}:{minute:02d}"
                    # 检查是否已被占用
                    is_booked = any(
                        a["employee_id"] == employee_id and 
                        a["date"] == date and 
                        a["time"] == time_str and
                        a["status"] != "cancelled"
                        for a in db["appointments"]
                    )
                    if not is_booked:
                        slots.append({"time": time_str, "available": True})
            
            self.send_json({"slots": slots, "date": date, "employee_id": employee_id})
        
        elif self.path == '/api/stats':
            today = datetime.now().strftime("%Y-%m-%d")
            this_month = datetime.now().strftime("%Y-%m")
            today_apts = [a for a in db["appointments"] if a["date"] == today]
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            tomorrow_apts = [a for a in db["appointments"] if a["date"] == tomorrow]
            
            revenue = sum(a["price"] for a in db["appointments"] if a["status"] == "confirmed")
            
            # Client stats
            clients = [c for c in db["clients"] if c.get("status") != "deleted"]
            active_clients = clients
            new_this_month = [c for c in clients if c.get("created_at", "").startswith(this_month)]
            total_clients = len(clients)
            confirmed_apts = [a for a in db["appointments"] if a["status"] == "confirmed"]
            total_revenue = sum(a["price"] for a in confirmed_apts)
            
            from collections import Counter
            client_revenue = Counter()
            for a in confirmed_apts:
                cid = a.get("client_id")
                if cid:
                    client_revenue[cid] += a.get("price", 0)
            bookings_per_client = round(len(confirmed_apts) / max(total_clients, 1), 1)
            
            self.send_json({
                "today_count": len(today_apts),
                "today_confirmed": len([a for a in today_apts if a["status"] == "confirmed"]),
                "tomorrow_count": len(tomorrow_apts),
                "weekly_revenue": revenue,
                "cancelled_count": len([a for a in db["appointments"] if a["status"] == "cancelled"]),
                "total_clients": total_clients,
                "active_clients": len(active_clients),
                "new_clients_this_month": len(new_this_month),
                "total_revenue": total_revenue,
                "bookings_per_client": bookings_per_client,
                "total_clients_count": total_clients,
                "vip_clients": len([c for c in clients if c.get("membership_level") == "vip"]),
                "new_clients_today": len([c for c in clients if c.get("created_at", "").startswith(today)])
            })
        
        elif self.path == '/api/transactions':
            date_filter = self.path.split('?date=')[-1] if '?date=' in self.path else None
            transactions = db.get("transactions", [])
            if date_filter:
                transactions = [t for t in transactions if t["date"] == date_filter]
            self.send_json({"transactions": transactions})
        
        elif self.path == '/api/expenses':
            expenses = db.get("expenses", [])
            self.send_json({"expenses": expenses})
        
        elif self.path == '/api/commission-rules':
            rules = db.get("commission_rules", [])
            self.send_json({"rules": rules})
        
        elif self.path == '/api/employee-commissions':
            commissions = db.get("employee_commissions", [])
            self.send_json({"commissions": commissions})
        
        elif self.path == '/api/finance-stats':
            today = datetime.now().strftime("%Y-%m-%d")
            this_month = today[:7]
            
            transactions = db.get("transactions", [])
            expenses = db.get("expenses", [])
            
            total_revenue = sum(t["amount"] for t in transactions if t.get("status") == "completed")
            month_revenue = sum(t["amount"] for t in transactions if t.get("status") == "completed" and t["date"].startswith(this_month))
            today_revenue = sum(t["amount"] for t in transactions if t.get("status") == "completed" and t["date"] == today)
            total_expenses = sum(e["amount"] for e in expenses)
            month_expenses = sum(e["amount"] for e in expenses if e["date"].startswith(this_month))
            
            from collections import Counter
            service_revenue = Counter()
            for t in transactions:
                if t.get("status") == "completed":
                    service_revenue[t.get("service_name", "其他")] += t["amount"]
            
            emp_revenue = Counter()
            for t in transactions:
                if t.get("status") == "completed":
                    emp_revenue[t.get("employee_name", "未分配")] += t["amount"]
            
            payment_methods = Counter()
            for t in transactions:
                if t.get("status") == "completed":
                    payment_methods[t.get("payment_method", "其他")] += t["amount"]
            
            expense_categories = Counter()
            for e in expenses:
                expense_categories[e["category"]] += e["amount"]
            
            commissions_data = db.get("employee_commissions", [])
            month_commissions_paid = sum(c["amount"] for c in commissions_data if c.get("date","").startswith(this_month) and c.get("status") == "paid")
            pending_commissions = sum(c["amount"] for c in commissions_data if c.get("status") == "pending")
            
            self.send_json({
                "total_revenue": total_revenue,
                "month_revenue": month_revenue,
                "today_revenue": today_revenue,
                "total_expenses": total_expenses,
                "month_expenses": month_expenses,
                "net_profit": total_revenue - total_expenses,
                "month_net_profit": month_revenue - month_expenses,
                "service_revenue": dict(service_revenue),
                "emp_revenue": dict(emp_revenue),
                "payment_methods": dict(payment_methods),
                "expense_categories": dict(expense_categories),
                "transaction_count": len(transactions),
                "expense_count": len(expenses),
                "month_commissions_paid": month_commissions_paid,
                "pending_commissions": pending_commissions,
                "avg_transaction": round(month_revenue / max(len([t for t in transactions if t.get("status") == "completed" and t["date"].startswith(this_month)]), 1), 2)
            })
        
        elif self.path == '/api/list-videos':
            # GET endpoint for listing videos
            os.makedirs(VIDEOS_PATH, exist_ok=True)
            videos = []
            total_size = 0
            today = datetime.now().strftime('%Y-%m-%d')
            uploaded_today = 0
            
            try:
                for filename in os.listdir(VIDEOS_PATH):
                    if filename.startswith('.'):
                        continue
                    file_path = os.path.join(VIDEOS_PATH, filename)
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        total_size += size
                        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        if mtime.strftime('%Y-%m-%d') == today:
                            uploaded_today += 1
                        
                        videos.append({
                            "name": filename,
                            "size": size,
                            "url": f"/api/video/{filename}",
                            "modified": mtime.isoformat()
                        })
                
                # Sort by modification time, newest first
                videos.sort(key=lambda x: x['modified'], reverse=True)
            except Exception as e:
                log_operation("ERROR", "system", 0, f"Error listing videos: {str(e)}")
            
            self.send_json({
                "success": True,
                "videos": videos,
                "totalCount": len(videos),
                "totalSize": total_size,
                "uploadedToday": uploaded_today
            })
        
        elif self.path.startswith('/api/video/'):
            # GET endpoint for serving video files
            filename = self.path.replace('/api/video/', '')
            file_path = os.path.join(VIDEOS_PATH, filename)
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.send_response(200)
                # 根据文件扩展名设置 Content-Type
                if filename.endswith('.mp4'):
                    self.send_header('Content-Type', 'video/mp4')
                elif filename.endswith('.mov'):
                    self.send_header('Content-Type', 'video/quicktime')
                elif filename.endswith('.webm'):
                    self.send_header('Content-Type', 'video/webm')
                elif filename.endswith('.ogv') or filename.endswith('.ogg'):
                    self.send_header('Content-Type', 'video/ogg')
                else:
                    self.send_header('Content-Type', 'application/octet-stream')
                
                file_size = os.path.getsize(file_path)
                self.send_header('Content-Length', str(file_size))
                self.send_header('Content-Disposition', f'inline; filename="{filename}"')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_json({"error": "Video not found"}, 404)
        
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        db = load_db()
        
        # 处理视频上传（多部分表单数据）
        if self.path == '/api/upload-video':
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' in content_type:
                # 解析多部分表单数据
                boundary = content_type.split("boundary=")[1].encode() if "boundary=" in content_type else b''
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                
                # 简单的多部分解析
                parts = body.split(b'--' + boundary)
                for part in parts:
                    if b'filename=' in part:
                        # 提取文件名
                        filename_start = part.find(b'filename="') + 10
                        filename_end = part.find(b'"', filename_start)
                        filename = part[filename_start:filename_end].decode('utf-8')
                        
                        # 提取文件内容
                        content_start = part.find(b'\r\n\r\n') + 4
                        content_end = part.rfind(b'\r\n')
                        file_content = part[content_start:content_end]
                        
                        # 保存文件
                        os.makedirs(VIDEOS_PATH, exist_ok=True)
                        file_path = os.path.join(VIDEOS_PATH, filename)
                        with open(file_path, 'wb') as f:
                            f.write(file_content)
                        
                        self.send_json({
                            "success": True,
                            "filename": filename,
                            "size": len(file_content),
                            "link": f"/videos/{filename}"
                        }, 201)
                        return
            
            self.send_json({"error": "Invalid upload"}, 400)
            return
        
        # 处理视频列表
        if self.path == '/api/list-videos':
            videos = []
            if os.path.exists(VIDEOS_PATH):
                for filename in os.listdir(VIDEOS_PATH):
                    filepath = os.path.join(VIDEOS_PATH, filename)
                    if os.path.isfile(filepath):
                        videos.append({
                            "name": filename,
                            "size": os.path.getsize(filepath),
                            "uploadTime": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                            "link": f"/videos/{filename}"
                        })
            videos.sort(key=lambda x: x["uploadTime"], reverse=True)
            self.send_json({"videos": videos}, 200)
            return
        
        # 处理视频删除
        if self.path == '/api/delete-video':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
                filename = data.get("filename", "")
                filepath = os.path.join(VIDEOS_PATH, filename)
                
                if os.path.exists(filepath):
                    os.remove(filepath)
                    self.send_json({"success": True}, 200)
                else:
                    self.send_json({"error": "File not found"}, 404)
            except Exception as e:
                self.send_json({"error": str(e)}, 400)
            return
        
        # 其他 POST 请求处理
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(body)
        except:
            self.send_json({"error": "Invalid JSON"}, 400)
            return
        
        if self.path == '/api/appointments':
            # 创建预约
            today_str = datetime.now().strftime("%Y-%m-%d")
            apt_id = len(db["appointments"]) + 1
            new_apt = {
                "id": apt_id,
                "client_id": data.get("client_id"),
                "client_name": data.get("client_name"),
                "client_phone": data.get("client_phone"),
                "service_id": data.get("service_id"),
                "service_name": data.get("service_name"),
                "employee_id": data.get("employee_id"),
                "employee_name": data.get("employee_name"),
                "date": data.get("date"),
                "time": data.get("time"),
                "duration": data.get("duration"),
                "price": data.get("price"),
                "source": data.get("source", "website"),
                "status": "pending",
                "notes": data.get("notes", ""),
                "created_at": datetime.now().isoformat()
            }
            
            db["appointments"].append(new_apt)
            
            # 自动创建或更新客户（通过电话去重）
            phone = data.get("client_phone", "")
            name = data.get("client_name", "")
            existing_client = next((c for c in db["clients"] if c.get("phone") == phone and c.get("status") != "deleted"), None)
            
            if existing_client:
                # 更新已有客户
                new_apt["client_id"] = existing_client["id"]
                existing_client["total_visits"] = existing_client.get("total_visits", 0) + 1
                existing_client["total_spent"] = existing_client.get("total_spent", 0) + (data.get("price") or 0)
                existing_client["last_visit"] = data.get("date", today_str)
                existing_client["updated_at"] = datetime.now().isoformat()
                if name and not existing_client.get("name"):
                    existing_client["name"] = name
            else:
                # 创建新客户（完整字段）
                new_client = {
                    "id": len(db["clients"]) + 1,
                    "name": name or phone,
                    "phone": phone,
                    "gender": "",
                    "birthday": "",
                    "email": "",
                    "address": "",
                    "notes": "",
                    "status": "active",
                    "membership_level": "regular",
                    "tags": [],
                    "total_visits": 1,
                    "total_spent": data.get("price") or 0,
                    "last_visit": data.get("date", today_str),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                db["clients"].append(new_client)
                new_apt["client_id"] = new_client["id"]
            
            save_db(db)
            log_operation("CREATE", "appointment", apt_id, f"New booking: {new_apt}")
            
            self.send_json({"success": True, "appointment": new_apt}, 201)
        
        elif self.path == '/api/chat':
            # 聊天处理
            message = data.get("message", "")
            platform = data.get("platform", "whatsapp")
            
            response_text = ""
            options = []
            appointment_preview = None
            
            # 解析预约信息
            if "预约" in message or "book" in message.lower():
                # 提取服务
                service_map = {
                    "暗疮": {"name": "暗疮护理 Facial", "duration": 120, "price": 138},
                    "深层清洁": {"name": "深层清洁 Facial", "duration": 60, "price": 68},
                    "补水": {"name": "补水嫩肤 Facial", "duration": 75, "price": 88},
                    "美白": {"name": "美白祛斑 Facial", "duration": 90, "price": 108},
                    "抗衰": {"name": "抗衰除皱 Facial", "duration": 110, "price": 128},
                    "全身放松": {"name": "全身放松按摩", "duration": 60, "price": 68},
                    "消脂": {"name": "消脂塑型按摩", "duration": 60, "price": 88},
                    "经络": {"name": "经络排毒按摩", "duration": 90, "price": 199},
                    "艾灸": {"name": "艾灸养生", "duration": 60, "price": 88},
                    "睫毛": {"name": "嫁接睫毛", "duration": 90, "price": 68},
                }
                service_info = None
                for key, info in service_map.items():
                    if key in message:
                        service_info = info
                        break
                
                # 提取员工
                employees = {e["name"].lower(): e for e in db["employees"] if e.get("active", True)}
                employee_id = None
                employee_name = None
                for emp_name, emp in employees.items():
                    if emp_name in message.lower():
                        employee_id = emp["id"]
                        employee_name = emp["name"]
                        break
                
                # 提取日期
                today = datetime.now()
                date_str = None
                if "今天" in message:
                    date_str = today.strftime("%Y-%m-%d")
                elif "明天" in message:
                    date_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")
                elif "后天" in message:
                    date_str = (today + timedelta(days=2)).strftime("%Y-%m-%d")
                else:
                    # 尝试匹配日期格式 MM月DD日 或 YYYY-MM-DD 或 MM/DD
                    date_match = re.search(r'(\d{1,2})月(\d{1,2})日', message)
                    if date_match:
                        month, day = int(date_match.group(1)), int(date_match.group(2))
                        year = today.year
                        try:
                            d = datetime(year, month, day)
                            date_str = d.strftime("%Y-%m-%d")
                        except:
                            pass
                
                # 提取时间
                time_str = None
                time_match = re.search(r'(\d{1,2}):(\d{2})', message)
                if time_match:
                    time_str = time_match.group(0)
                else:
                    # 先判断上午/下午
                    am_pm_match = re.search(r'(下午|晚上)(\d{1,2})点', message)
                    if am_pm_match:
                        h = int(am_pm_match.group(2)) + 12
                        time_str = f"{h:02d}:00"
                    else:
                        am_pm_match = re.search(r'(上午|早上)(\d{1,2})点', message)
                        if am_pm_match:
                            time_str = f"{int(am_pm_match.group(2)):02d}:00"
                        else:
                            # 普通 x点y分
                            time_match = re.search(r'(\d{1,2})点(\d{0,2})', message)
                            if time_match:
                                h = int(time_match.group(1))
                                m = int(time_match.group(2)) if time_match.group(2) else 0
                                time_str = f"{h:02d}:{m:02d}"
                
                if service_info and date_str:
                    appointment_preview = {
                        "service": service_info["name"],
                        "staff": employee_name or "待分配",
                        "date": date_str,
                        "time": time_str or "待确认",
                        "duration": service_info["duration"],
                        "price": service_info["price"]
                    }
                    # 如果时间和员工都齐全，自动创建临时预约
                    if employee_name and time_str and date_str:
                        response_text = f"已为您安排如下："
                    else:
                        missing = []
                        if not employee_name:
                            emp_names = [e["name"] for e in db["employees"] if e.get("active", True)]
                            options = [f"找 {n}" for n in emp_names]
                            missing.append("选择美容师")
                        if not time_str:
                            options = ["10:00", "11:00", "13:00", "14:00", "15:00", "16:00", "17:00"]
                            missing.append("选择时间")
                        response_text = f"还需要{' & '.join(missing)}："
                elif service_info:
                    response_text = f"好的，{service_info['name']} ($ {service_info['price']})。请问您想预约哪一天？"
                    options = ["今天", "明天", "后天"]
                elif "facial" in message.lower() or "护理" in message:
                    response_text = "好的，请问您想预约哪种面部护理？"
                    options = ["深层清洁 ($68)", "补水嫩肤 ($88)", "美白祛斑 ($108)", "暗疮护理 ($138)"]
                elif "按摩" in message:
                    response_text = "好的，请问您想预约哪种按摩？"
                    options = ["全身放松 ($68)", "消脂塑型 ($88)", "经络排毒 ($199)"]
                else:
                    response_text = "请问您想预约什么服务？我们有 Facial、按摩、艾灸等项目。"
                    options = ["预约 Facial", "预约按摩", "查看服务"]
            
            elif "取消" in message:
                response_text = "请问您的姓名或电话号码？我帮您查询预约。"
            
            elif "我的预约" in message or "查询" in message:
                # 查找最近24小时内的对话，获取客户信息
                user_apts = [a for a in db["appointments"] if a.get("client_phone") in message or a.get("client_name") in message]
                if user_apts:
                    response_text = f"找到 {len(user_apts)} 个预约：\n"
                    for apt in user_apts[:5]:
                        status_icon = {"pending": "⏳", "confirmed": "✅", "cancelled": "❌", "rescheduled": "🔄"}.get(apt["status"], "📋")
                        response_text += f"{status_icon} #{apt['id']} {apt['date']} {apt['time']} {apt['service_name']} - {apt['employee_name']}\n"
                    options = ["取消预约", "改期", "新增预约"]
                else:
                    response_text = "请提供您的姓名或电话号码，我帮您查询预约。"
            
            else:
                response_text = "您好！我是 I BEAUTY 预约助手 💆‍♀️\n我可以帮您：预约服务、查询预约、取消或改期。\n请问有什么可以帮您？"
                options = ["预约 Facial", "预约按摩", "我的预约"]
            
            conv_id = str(uuid.uuid4())[:8]
            self.send_json({
                "conversation_id": conv_id,
                "reply": response_text,
                "options": options,
                "appointment_preview": appointment_preview
            })
        
        elif self.path == '/api/employees':
            data = json.loads(body)
            # 添加新员工
            new_emp = {
                "id": len([e for e in db["employees"] if isinstance(e.get("id"), int)]) + 1,
                "name": data.get("name"),
                "role": data.get("role", "美容师"),
                "specialty": data.get("specialty", "综合"),
                "active": data.get("active", True),
                "created_at": datetime.now().isoformat()
            }
            if not new_emp["name"]:
                self.send_json({"error": "Name is required"}, 400)
                return
            db["employees"].append(new_emp)
            save_db(db)
            log_operation("CREATE", "employee", new_emp["id"], f"New employee: {new_emp['name']}")
            self.send_json({"success": True, "employee": new_emp}, 201)
        
        elif self.path == '/api/clients':
            # 添加客户
            new_client = {
                "id": len(db["clients"]) + 1,
                "name": data.get("name"),
                "phone": data.get("phone"),
                "gender": data.get("gender", ""),
                "birthday": data.get("birthday", ""),
                "email": data.get("email", ""),
                "address": data.get("address", ""),
                "notes": data.get("notes", ""),
                "membership_level": data.get("membership_level", "regular"),
                "tags": data.get("tags", []),
                "total_visits": 0,
                "total_spent": 0,
                "last_visit": None,
                "created_at": datetime.now().isoformat()
            }
            if not new_client["name"] or not new_client["phone"]:
                self.send_json({"error": "Name and phone are required"}, 400)
                return
            db["clients"].append(new_client)
            save_db(db)
            log_operation("CREATE", "client", new_client["id"], f"New client: {new_client['name']} - {new_client['phone']}")
            self.send_json({"success": True, "client": new_client}, 201)
        
        elif self.path == '/api/transactions':
            t_id = len(db.get("transactions", [])) + 1
            new_t = {
                "id": t_id,
                "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
                "client_name": data.get("client_name", ""),
                "client_phone": data.get("client_phone", ""),
                "service_name": data.get("service_name", ""),
                "employee_name": data.get("employee_name", ""),
                "amount": data.get("amount", 0),
                "payment_method": data.get("payment_method", "现金"),
                "status": data.get("status", "completed"),
                "notes": data.get("notes", ""),
                "created_at": datetime.now().isoformat()
            }
            if "transactions" not in db:
                db["transactions"] = []
            db["transactions"].append(new_t)
            save_db(db)
            log_operation("CREATE", "transaction", t_id, f"New payment: ${new_t['amount']}")
            self.send_json({"success": True, "transaction": new_t}, 201)
        
        elif self.path == '/api/expenses':
            e_id = len(db.get("expenses", [])) + 1
            new_e = {
                "id": e_id,
                "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
                "category": data.get("category", "其他"),
                "description": data.get("description", ""),
                "amount": data.get("amount", 0),
                "payment_method": data.get("payment_method", "现金"),
                "notes": data.get("notes", ""),
                "created_at": datetime.now().isoformat()
            }
            if "expenses" not in db:
                db["expenses"] = []
            db["expenses"].append(new_e)
            save_db(db)
            log_operation("CREATE", "expense", e_id, f"New expense: ${new_e['amount']}")
            self.send_json({"success": True, "expense": new_e}, 201)
        
        elif self.path == '/api/employee-commissions':
            c_id = len(db.get("employee_commissions", [])) + 1
            new_c = {
                "id": c_id,
                "employee_id": data.get("employee_id"),
                "employee_name": data.get("employee_name"),
                "amount": data.get("amount", 0),
                "commission_rate": data.get("commission_rate", 0),
                "service_name": data.get("service_name", ""),
                "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
                "status": data.get("status", "pending"),
                "notes": data.get("notes", ""),
                "created_at": datetime.now().isoformat()
            }
            if "employee_commissions" not in db:
                db["employee_commissions"] = []
            db["employee_commissions"].append(new_c)
            save_db(db)
            self.send_json({"success": True, "commission": new_c}, 201)
        
        elif self.path == '/api/commission-rules':
            r_id = len(db.get("commission_rules", [])) + 1
            new_r = {
                "id": r_id,
                "service_id": data.get("service_id"),
                "service_name": data.get("service_name", "默认"),
                "commission_type": data.get("commission_type", "percentage"),
                "commission_value": data.get("commission_value", 30),
                "min_guarantee": data.get("min_guarantee", 0)
            }
            if "commission_rules" not in db:
                db["commission_rules"] = []
            db["commission_rules"].append(new_r)
            save_db(db)
            self.send_json({"success": True, "rule": new_r}, 201)
        
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def do_PUT(self):
        # PUT 也转发到 PATCH 处理
        self.do_PATCH()
        return
    
    def do_PATCH(self):
        db = load_db()
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(body)
        except:
            self.send_json({"error": "Invalid JSON"}, 400)
            return
        
        if '/api/appointments/' in self.path:
            apt_id = int(self.path.split('/')[-1])
            apt = next((a for a in db["appointments"] if a["id"] == apt_id), None)
            
            if apt:
                if "status" in data:
                    apt["status"] = data["status"]
                    apt["updated_at"] = datetime.now().isoformat()
                    log_operation("UPDATE", "appointment", apt_id, f"Status changed to {data['status']}")
                
                if "date" in data or "time" in data:
                    if "date" in data:
                        apt["date"] = data["date"]
                    if "time" in data:
                        apt["time"] = data["time"]
                    apt["status"] = "rescheduled"
                    log_operation("RESCHEDULE", "appointment", apt_id, f"Rescheduled to {data.get('date', apt['date'])} {data.get('time', apt['time'])}")
                
                save_db(db)
                self.send_json({"success": True, "appointment": apt})
            else:
                self.send_json({"error": "Appointment not found"}, 404)
        
        elif '/api/employees/' in self.path:
            emp_id = int(self.path.split('/')[-1])
            emp = next((e for e in db["employees"] if e["id"] == emp_id), None)
            
            if emp:
                if "active" in data:
                    emp["active"] = data["active"]
                    status = "active" if data["active"] else "inactive (departed)"
                    log_operation("UPDATE", "employee", emp_id, f"Status changed to {status}")
                if "name" in data:
                    emp["name"] = data["name"]
                if "role" in data:
                    emp["role"] = data["role"]
                if "specialty" in data:
                    emp["specialty"] = data["specialty"]
                emp["updated_at"] = datetime.now().isoformat()
                save_db(db)
                self.send_json({"success": True, "employee": emp})
            else:
                self.send_json({"error": "Employee not found"}, 404)
        
        elif '/api/clients/' in self.path:
            client_id = int(self.path.split('/')[-1])
            client = next((c for c in db["clients"] if c["id"] == client_id), None)
            
            if client:
                updatable = ["name", "phone", "gender", "birthday", "email", "address", 
                            "notes", "membership_level", "tags", "status"]
                for field in updatable:
                    if field in data:
                        client[field] = data[field]
                client["updated_at"] = datetime.now().isoformat()
                save_db(db)
                log_operation("UPDATE", "client", client_id, f"Client updated: {client['name']}")
                self.send_json({"success": True, "client": client})
            else:
                self.send_json({"error": "Client not found"}, 404)
        
        elif '/api/transactions/' in self.path:
            t_id = int(self.path.split('/')[-1])
            t = next((tx for tx in db.get("transactions", []) if tx["id"] == t_id), None)
            if t:
                updatable = ["date", "client_name", "client_phone", "service_name", "employee_name",
                            "amount", "payment_method", "status", "notes"]
                for f in updatable:
                    if f in data:
                        t[f] = data[f]
                save_db(db)
                self.send_json({"success": True, "transaction": t})
            else:
                self.send_json({"error": "Transaction not found"}, 404)
        
        elif '/api/expenses/' in self.path:
            e_id = int(self.path.split('/')[-1])
            e = next((ex for ex in db.get("expenses", []) if ex["id"] == e_id), None)
            if e:
                updatable = ["date", "category", "description", "amount", "payment_method", "notes"]
                for f in updatable:
                    if f in data:
                        e[f] = data[f]
                save_db(db)
                self.send_json({"success": True, "expense": e})
            else:
                self.send_json({"error": "Expense not found"}, 404)
        
        elif '/api/employee-commissions/' in self.path:
            c_id = int(self.path.split('/')[-1])
            c = next((cm for cm in db.get("employee_commissions", []) if cm["id"] == c_id), None)
            if c:
                updatable = ["status", "amount", "notes"]
                for f in updatable:
                    if f in data:
                        c[f] = data[f]
                save_db(db)
                self.send_json({"success": True, "commission": c})
            else:
                self.send_json({"error": "Commission not found"}, 404)
        
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")

    def do_DELETE(self):
        db = load_db()
        
        if '/api/clients/' in self.path:
            client_id = int(self.path.split('/')[-1])
            client = next((c for c in db["clients"] if c["id"] == client_id), None)
            if client:
                client["status"] = "deleted"
                client["deleted_at"] = datetime.now().isoformat()
                save_db(db)
                log_operation("DELETE", "client", client_id, f"Client soft-deleted: {client['name']}")
                self.send_json({"success": True, "message": f"Client {client['name']} soft-deleted"})
            else:
                self.send_json({"error": "Client not found"}, 404)
        
        elif '/api/transactions/' in self.path:
            t_id = int(self.path.split('/')[-1])
            items = db.get("transactions", [])
            item = next((x for x in items if x["id"] == t_id), None)
            if item:
                item["status"] = "cancelled"
                save_db(db)
                self.send_json({"success": True})
            else:
                self.send_json({"error": "Not found"}, 404)
        
        elif '/api/expenses/' in self.path:
            e_id = int(self.path.split('/')[-1])
            items = db.get("expenses", [])
            item = next((x for x in items if x["id"] == e_id), None)
            if item:
                items.remove(item)
                save_db(db)
                self.send_json({"success": True})
            else:
                self.send_json({"error": "Not found"}, 404)
        
        elif '/api/employee-commissions/' in self.path:
            c_id = int(self.path.split('/')[-1])
            items = db.get("employee_commissions", [])
            item = next((x for x in items if x["id"] == c_id), None)
            if item:
                items.remove(item)
                save_db(db)
                self.send_json({"success": True})
            else:
                self.send_json({"error": "Not found"}, 404)
        
        # Video upload endpoints
        elif self.path == '/api/upload-video':
            # Handle multipart form data
            content_type = self.headers['Content-Type']
            if 'multipart/form-data' in content_type:
                # Parse boundary
                boundary = content_type.split("boundary=")[1].encode()
                body = self.rfile.read(int(self.headers['Content-Length']))
                
                # Extract filename and file data
                parts = body.split(b'--' + boundary)
                filename = None
                file_data = None
                
                for part in parts:
                    if b'filename=' in part:
                        # Extract filename
                        filename_start = part.find(b'filename="') + 10
                        filename_end = part.find(b'"', filename_start)
                        filename = part[filename_start:filename_end].decode()
                        
                        # Extract file data
                        file_start = part.find(b'\r\n\r\n') + 4
                        file_end = part.rfind(b'\r\n')
                        file_data = part[file_start:file_end]
                        break
                
                if filename and file_data:
                    # Ensure videos directory exists
                    os.makedirs(VIDEOS_PATH, exist_ok=True)
                    
                    # Save file
                    file_path = os.path.join(VIDEOS_PATH, filename)
                    with open(file_path, 'wb') as f:
                        f.write(file_data)
                    
                    # Log upload
                    log_operation("UPLOAD_VIDEO", "system", 0, f"Video uploaded: {filename} ({len(file_data)} bytes)")
                    
                    self.send_json({
                        "success": True,
                        "filename": filename,
                        "size": len(file_data),
                        "url": f"/api/video/{filename}"
                    })
                else:
                    self.send_json({"error": "No file received"}, 400)
            else:
                self.send_json({"error": "Invalid content type"}, 400)
        
        elif self.path == '/api/list-videos':
            # List all uploaded videos
            os.makedirs(VIDEOS_PATH, exist_ok=True)
            videos = []
            total_size = 0
            today = datetime.now().strftime('%Y-%m-%d')
            uploaded_today = 0
            
            try:
                for filename in os.listdir(VIDEOS_PATH):
                    if filename.startswith('.'):
                        continue
                    file_path = os.path.join(VIDEOS_PATH, filename)
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        total_size += size
                        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        if mtime.strftime('%Y-%m-%d') == today:
                            uploaded_today += 1
                        
                        videos.append({
                            "name": filename,
                            "size": size,
                            "url": f"/api/video/{filename}",
                            "modified": mtime.isoformat()
                        })
                
                # Sort by modification time, newest first
                videos.sort(key=lambda x: x['modified'], reverse=True)
            except Exception as e:
                log_operation("ERROR", "system", 0, f"Error listing videos: {str(e)}")
            
            self.send_json({
                "success": True,
                "videos": videos,
                "totalCount": len(videos),
                "totalSize": total_size,
                "uploadedToday": uploaded_today
            })
        
        elif self.path.startswith('/api/video/'):
            # Serve video file
            filename = self.path.replace('/api/video/', '')
            file_path = os.path.join(VIDEOS_PATH, filename)
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.send_response(200)
                self.send_header('Content-Type', 'video/mp4')
                self.send_header('Content-Disposition', f'inline; filename="{filename}"')
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_json({"error": "Video not found"}, 404)
        
        elif self.path.startswith('/api/delete-video'):
            # Delete video file
            body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
            try:
                data = json.loads(body)
                filename = data.get('filename', '')
                file_path = os.path.join(VIDEOS_PATH, filename)
                
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    os.remove(file_path)
                    log_operation("DELETE_VIDEO", "system", 0, f"Video deleted: {filename}")
                    self.send_json({"success": True})
                else:
                    self.send_json({"error": "File not found"}, 404)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        
        else:
            self.send_json({"error": "Not found"}, 404)

def run_server(port=8082):
    server = HTTPServer(('0.0.0.0', port), BookingAPIHandler)
    server.allow_reuse_address = True
    server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print(f"🚀 I BEAUTY API Server running on port {port}")
    print(f"📍 http://localhost:{port}")
    init_db()
    server.serve_forever()

if __name__ == "__main__":
    run_server()
