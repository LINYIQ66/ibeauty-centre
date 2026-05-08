#!/usr/bin/env python3
"""
I BEAUTY 完整 API 文档
所有数据永久保存到 PostgreSQL
"""

API_ENDPOINTS = {
    # ═══════════════════════════════════════════════════════════
    # 预约管理 - 永久保存
    # ═══════════════════════════════════════════════════════════
    'appointments': {
        'GET /api/appointments': '获取预约列表（支持日期过滤）',
        'GET /api/appointments?date=2026-05-10': '获取指定日期预约',
        'GET /api/appointments?status=pending': '获取待确认预约',
        'POST /api/appointments': '创建新预约（保存到数据库）',
        'PATCH /api/appointments/{id}': '更新预约（确认/取消/改期）',
        'DELETE /api/appointments/{id}': '软删除预约',
        'GET /api/appointments/stats': '预约统计',
    },
    
    # ═══════════════════════════════════════════════════════════
    # 统计数据 - 实时计算 + 历史快照
    # ═══════════════════════════════════════════════════════════
    'statistics': {
        'GET /api/stats': '实时统计（今日/明日/本周）',
        'GET /api/stats/daily?date=2026-05-10': '每日快照统计',
        'GET /api/stats/monthly?month=2026-05': '每月汇总统计',
        'GET /api/stats/revenue': '收入统计（日/周/月/年）',
        'GET /api/stats/overview': '业务总览（v_business_overview）',
        'GET /api/stats/employee-performance': '员工业绩排行',
        'POST /api/stats/regenerate': '重新生成统计快照',
    },
    
    # ═══════════════════════════════════════════════════════════
    # 员工管理 - 永久保存 + 排班
    # ═══════════════════════════════════════════════════════════
    'employees': {
        'GET /api/employees': '获取活跃员工列表',
        'GET /api/employees/all': '获取所有员工（包括离职）',
        'POST /api/employees': '新增员工',
        'PATCH /api/employees/{id}': '更新员工信息',
        'DELETE /api/employees/{id}': '标记为离职（软删除）',
        'GET /api/employees/{id}/schedule': '获取员工排班',
        'POST /api/employees/{id}/schedule': '添加排班',
        'PATCH /api/employees/{id}/schedule/{date}': '更新排班',
        'GET /api/employees/{id}/performance': '员工业绩详情',
    },
    
    # ═══════════════════════════════════════════════════════════
    # 排班管理 - 永久保存
    # ═══════════════════════════════════════════════════════════
    'schedules': {
        'GET /api/schedules?employee_id=1&date=2026-05-10': '查询排班',
        'GET /api/schedules/week?week=2026-W20': '周排班',
        'GET /api/schedules/month?month=2026-05': '月排班',
        'POST /api/schedules': '创建排班',
        'PATCH /api/schedules/{id}': '更新排班',
        'DELETE /api/schedules/{id}': '删除排班',
        'GET /api/schedules/conflicts': '排班冲突检测',
    },
    
    # ═══════════════════════════════════════════════════════════
    # 客户管理 - 永久保存 + 标签
    # ═══════════════════════════════════════════════════════════
    'clients': {
        'GET /api/clients': '客户列表',
        'GET /api/clients/{id}': '客户详情',
        'POST /api/clients': '新增客户',
        'PATCH /api/clients/{id}': '更新客户信息',
        'GET /api/clients/{id}/history': '消费历史',
        'GET /api/clients/{id}/appointments': '预约历史',
        'POST /api/clients/{id}/tags': '添加标签',
        'DELETE /api/clients/{id}/tags/{tag_id}': '移除标签',
        'GET /api/clients/vip': 'VIP 客户列表',
    },
    
    # ═══════════════════════════════════════════════════════════
    # 交易记录 - 永久保存
    # ═══════════════════════════════════════════════════════════
    'transactions': {
        'GET /api/transactions': '交易记录列表',
        'GET /api/transactions?date=2026-05-10': '指定日期交易',
        'GET /api/transactions/{id}': '交易详情',
        'POST /api/transactions': '创建交易记录',
        'PATCH /api/transactions/{id}/payment': '更新支付状态',
        'GET /api/transactions/stats': '交易统计',
    },
    
    # ═══════════════════════════════════════════════════════════
    # 产品库存 - 永久保存
    # ═══════════════════════════════════════════════════════════
    'products': {
        'GET /api/products': '产品列表',
        'GET /api/products/low-stock': '库存预警',
        'POST /api/products': '新增产品',
        'PATCH /api/products/{id}': '更新产品信息',
        'POST /api/products/{id}/restock': '库存补充',
        'POST /api/products/usage': '记录产品使用',
        'GET /api/products/usage/{appointment_id}': '查看产品使用',
    },
    
    # ═══════════════════════════════════════════════════════════
    # 系统设置 - 永久保存
    # ═══════════════════════════════════════════════════════════
    'settings': {
        'GET /api/settings': '获取所有设置',
        'GET /api/settings/{key}': '获取单个设置',
        'PATCH /api/settings/{key}': '更新设置',
        'GET /api/settings/business-hours': '营业时间',
        'PATCH /api/settings/business-hours': '更新营业时间',
    },
    
    # ═══════════════════════════════════════════════════════════
    # 报表导出
    # ═══════════════════════════════════════════════════════════
    'reports': {
        'GET /api/reports/daily?date=2026-05-10': '日报',
        'GET /api/reports/weekly?week=2026-W20': '周报',
        'GET /api/reports/monthly?month=2026-05': '月报',
        'GET /api/reports/export?format=csv&type=daily': '导出 CSV',
        'GET /api/reports/export?format=excel&type=monthly': '导出 Excel',
    }
}

# 打印 API 文档
print("=" * 70)
print("I BEAUTY 完整 API 文档")
print("所有数据永久保存到 PostgreSQL")
print("=" * 70)

for category, endpoints in API_ENDPOINTS.items():
    print(f"\n📁 {category.upper()}")
    print("-" * 70)
    for endpoint, description in endpoints.items():
        print(f"  {endpoint:50s} {description}")

print("\n" + "=" * 70)
print(f"总计：{sum(len(v) for v in API_ENDPOINTS.values())} 个 API 端点")
print("=" * 70)
