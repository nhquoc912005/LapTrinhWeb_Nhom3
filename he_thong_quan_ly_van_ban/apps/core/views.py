from django.shortcuts import render

from apps.accounts.decorators import role_required
from apps.accounts.models import Customer


DASHBOARD_METRICS = [
    {
        "label": "Tổng văn bản",
        "value": "742",
        "subtitle": "Văn bản trong tháng",
        "trend": "+12.5%",
        "trend_direction": "up",
        "accent": "#3b82f6",
        "icon_path": "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zm-1 1.5L18.5 9H13zM6 20V4h5v7h7v9z",
    },
    {
        "label": "Văn bản đến",
        "value": "371",
        "subtitle": "Chờ xử lý: 45",
        "trend": "+8.3%",
        "trend_direction": "up",
        "accent": "#10b981",
        "icon_path": "M19 7v4H5V7h14m0-2H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2m-7 9 4-4h-3V4h-2v6H8z",
    },
    {
        "label": "Văn bản đi",
        "value": "309",
        "subtitle": "Chờ duyệt: 28",
        "trend": "+5.7%",
        "trend_direction": "up",
        "accent": "#a855f7",
        "icon_path": "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zm-2 15-4-4h3V9h2v4h3zm1-7V3.5L18.5 9z",
    },
    {
        "label": "Công việc",
        "value": "156",
        "subtitle": "Đang thực hiện: 68",
        "trend": "-3.2%",
        "trend_direction": "down",
        "accent": "#f59e0b",
        "icon_path": "M20 7h-4V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2M10 5h4v2h-4zm10 13H4v-5h16zm0-7H4V9h16z",
    },
    {
        "label": "Chờ xử lý",
        "value": "73",
        "subtitle": "Cần xử lý gấp",
        "trend": "+15.8%",
        "trend_direction": "up",
        "accent": "#eab308",
        "icon_path": "M12 1a11 11 0 1 0 11 11A11 11 0 0 0 12 1m1 11V6h-2v7h6v-2z",
    },
    {
        "label": "Đã hoàn thành",
        "value": "531",
        "subtitle": "Tỷ lệ: 82.5%",
        "trend": "+18.4%",
        "trend_direction": "up",
        "accent": "#14b8a6",
        "icon_path": "M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2m-1 15-4-4 1.41-1.41L11 14.17l6.59-6.58L19 9z",
    },
]

WEEKLY_SERIES = [
    {"label": "T2", "incoming": 12, "outgoing": 8, "tasks": 15},
    {"label": "T3", "incoming": 15, "outgoing": 11, "tasks": 18},
    {"label": "T4", "incoming": 10, "outgoing": 14, "tasks": 12},
    {"label": "T5", "incoming": 18, "outgoing": 9, "tasks": 20},
    {"label": "T6", "incoming": 14, "outgoing": 16, "tasks": 16},
    {"label": "T7", "incoming": 8, "outgoing": 5, "tasks": 8},
    {"label": "CN", "incoming": 5, "outgoing": 3, "tasks": 5},
]

STATUS_BREAKDOWN = [
    {"label": "Đã duyệt", "count": 531, "color": "#7c78d5"},
    {"label": "Chờ xử lý", "count": 118, "color": "#9a9af1"},
    {"label": "Đang thực hiện", "count": 73, "color": "#67c46a"},
    {"label": "Quá hạn", "count": 18, "color": "#f6b10a"},
]

RECENT_DOCUMENTS = [
    {
        "code": "VB001/2024",
        "title": "Về việc triển khai công tác quản lý văn bản năm 2024",
        "date": "28/01/2024",
        "status_label": "Chờ xử lý",
        "status_class": "badge-cho-xu-ly",
    },
    {
        "code": "VB002/2024",
        "title": "Thông báo về lịch họp tuần",
        "date": "28/01/2024",
        "status_label": "Chờ xử lý",
        "status_class": "badge-cho-xu-ly",
    },
    {
        "code": "VB003/2024",
        "title": "Báo cáo tình hình hoạt động quý I",
        "date": "27/01/2024",
        "status_label": "Đã xử lý",
        "status_class": "badge-da-xu-ly",
    },
    {
        "code": "VB004/2024",
        "title": "Kế hoạch triển khai dự án mới",
        "date": "27/01/2024",
        "status_label": "Đang xử lý",
        "status_class": "badge-dang-xu-ly",
    },
    {
        "code": "VB005/2024",
        "title": "Quyết định về việc điều chỉnh nhân sự",
        "date": "26/01/2024",
        "status_label": "Chờ xử lý",
        "status_class": "badge-cho-xu-ly",
    },
]

URGENT_TASKS = [
    {
        "title": "Hoàn thành báo cáo tháng 1",
        "assignee": "Nguyễn Văn A",
        "deadline": "29/01/2024",
        "priority_label": "Cao",
        "priority_class": "priority-high",
    },
    {
        "title": "Kiểm tra hồ sơ văn bản",
        "assignee": "Trần Thị B",
        "deadline": "30/01/2024",
        "priority_label": "Cao",
        "priority_class": "priority-high",
    },
    {
        "title": "Chuẩn bị tài liệu họp",
        "assignee": "Lê Văn C",
        "deadline": "31/01/2024",
        "priority_label": "Trung bình",
        "priority_class": "priority-medium",
    },
]


def _build_status_gradient(items):
    total = sum(item["count"] for item in items)
    if total <= 0:
        return "conic-gradient(#e5e7eb 0 100%)", []

    start = 0
    segments = []
    enriched_items = []

    for item in items:
        percentage = round((item["count"] / total) * 100, 1)
        end = start + percentage
        segments.append(f"{item['color']} {start:.1f}% {end:.1f}%")
        enriched_items.append({**item, "percentage": percentage})
        start = end

    if start < 100:
        segments.append(f"#e5e7eb {start:.1f}% 100%")

    return f"conic-gradient({', '.join(segments)})", enriched_items


def _build_weekly_chart(series):
    max_value = max(
        max(item["incoming"], item["outgoing"], item["tasks"]) for item in series
    )
    if max_value <= 0:
        return [
            {
                **item,
                "incoming_height": 0,
                "outgoing_height": 0,
                "tasks_height": 0,
            }
            for item in series
        ]

    chart = []
    for item in series:
        chart.append(
            {
                **item,
                "incoming_height": round((item["incoming"] / max_value) * 100, 1),
                "outgoing_height": round((item["outgoing"] / max_value) * 100, 1),
                "tasks_height": round((item["tasks"] / max_value) * 100, 1),
            }
        )
    return chart


@role_required(*Customer.Role.values)
def dashboard(request):
    status_gradient, status_breakdown = _build_status_gradient(STATUS_BREAKDOWN)
    context = {
        "dashboard_metrics": DASHBOARD_METRICS,
        "weekly_chart": _build_weekly_chart(WEEKLY_SERIES),
        "status_breakdown": status_breakdown,
        "status_gradient": status_gradient,
        "recent_documents": RECENT_DOCUMENTS,
        "urgent_tasks": URGENT_TASKS,
    }
    return render(request, "core/dashboard.html", context)


@role_required(*Customer.Role.values)
def bao_cao_thong_ke(request):
    return render(request, "bao-cao-thong-ke.html")
