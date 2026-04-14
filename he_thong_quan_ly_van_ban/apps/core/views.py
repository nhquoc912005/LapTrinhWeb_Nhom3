from datetime import timedelta

from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from apps.accounts.decorators import role_required
from apps.accounts.models import Customer
from apps.quanlyvanbanden.models import VanBanDen

from .models import CongViec, HoSoVanBan, VanBan

OUTGOING_KIND = VanBan.PHAN_LOAI_CHOICES[0][0]
OUTGOING_STATUS_CHO_XU_LY = VanBan.TRANG_THAI_CHOICES[0][0]
OUTGOING_STATUS_DA_XU_LY = VanBan.TRANG_THAI_CHOICES[1][0]
OUTGOING_STATUS_HOAN_TRA = VanBan.TRANG_THAI_CHOICES[2][0]
OUTGOING_STATUS_XEM_DE_BIET = VanBan.TRANG_THAI_CHOICES[3][0]
OUTGOING_STATUS_CHO_BAN_HANH = VanBan.TRANG_THAI_CHOICES[4][0]
OUTGOING_STATUS_DA_BAN_HANH = VanBan.TRANG_THAI_CHOICES[5][0]

CLERK_VISIBLE_OUTGOING_STATUSES = [
    OUTGOING_STATUS_CHO_BAN_HANH,
    OUTGOING_STATUS_DA_BAN_HANH,
    OUTGOING_STATUS_XEM_DE_BIET,
]
OUTGOING_COMPLETED_STATUSES = [
    OUTGOING_STATUS_DA_XU_LY,
    OUTGOING_STATUS_DA_BAN_HANH,
    OUTGOING_STATUS_XEM_DE_BIET,
]
INCOMING_COMPLETED_STATUSES = [
    VanBanDen.TrangThai.DA_XU_LY,
    VanBanDen.TrangThai.XEM_DE_BIET,
]
TASK_RETURNED_STATUSES = [
    CongViec.TrangThai.HOAN_TRA_CV,
    CongViec.TrangThai.HOAN_TRA_LD,
]
TASK_ACTIVE_STATUSES = [
    CongViec.TrangThai.CHO_XU_LY,
    CongViec.TrangThai.CHO_DUYET,
    *TASK_RETURNED_STATUSES,
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


def _build_trend(current, previous):
    delta = current - previous
    if delta > 0:
        return f"+{delta}", "up"
    if delta < 0:
        return str(delta), "down"
    return "0", "neutral"


def _window_totals(parts, current_start, current_end, previous_start, previous_end):
    current_total = 0
    previous_total = 0

    for queryset, date_lookup, filters in parts:
        current_filters = {
            f"{date_lookup}__gte": current_start,
            f"{date_lookup}__lt": current_end,
            **filters,
        }
        previous_filters = {
            f"{date_lookup}__gte": previous_start,
            f"{date_lookup}__lt": previous_end,
            **filters,
        }
        current_total += queryset.filter(**current_filters).count()
        previous_total += queryset.filter(**previous_filters).count()

    return _build_trend(current_total, previous_total)


def _document_status_badge(status_label):
    normalized = (status_label or "").lower()
    if "đã" in normalized or "hoàn thành" in normalized:
        return "badge-da-xu-ly"
    if "chờ" in normalized:
        return "badge-cho-xu-ly"
    return "badge-dang-xu-ly"


def _task_priority_meta(task, today):
    remaining_days = (task.han_xu_ly.date() - today).days
    if remaining_days < 0:
        return "Quá hạn", "priority-high"
    if remaining_days <= 2:
        return "Cao", "priority-high"
    return "Trung bình", "priority-medium"


def _incoming_queryset_for_user(user):
    queryset = VanBanDen.objects.select_related("nguoi_tao", "lanh_dao_xu_ly").all()

    if user.has_role(Customer.Role.ADMIN, Customer.Role.VAN_THU):
        return queryset
    if user.is_lanh_dao:
        return queryset.filter(lanh_dao_xu_ly=user)
    if user.is_chuyen_vien:
        return queryset.filter(ds_chuyen_tiep__chuyen_vien=user).distinct()
    return queryset.none()


def _outgoing_queryset_for_user(user):
    queryset = VanBan.objects.select_related("nguoi_tao", "lanh_dao_duyet", "ho_so_van_ban").filter(
        phan_loai=OUTGOING_KIND
    )

    if user.has_role(Customer.Role.ADMIN):
        return queryset
    if user.is_van_thu:
        return queryset.filter(trang_thai__in=CLERK_VISIBLE_OUTGOING_STATUSES)
    if user.is_lanh_dao:
        return queryset.filter(lanh_dao_duyet=user.core_profile)
    if user.is_chuyen_vien:
        return queryset.filter(nguoi_tao=user.core_profile)
    return queryset.none()


def _task_queryset_for_user(user):
    queryset = CongViec.objects.select_related("nguoi_giao", "nguoi_thuc_hien", "van_ban")

    if user.has_role(Customer.Role.ADMIN, Customer.Role.VAN_THU):
        return queryset
    if user.is_lanh_dao:
        return queryset.filter(nguoi_giao=user.core_profile)
    if user.is_chuyen_vien:
        return queryset.filter(nguoi_thuc_hien=user.core_profile)
    return queryset.none()


def _build_weekly_series(today, incoming_queryset, outgoing_queryset, task_queryset):
    week_days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    incoming_counts = {
        day: incoming_queryset.filter(ngay_den=day).count()
        for day in week_days
    }
    outgoing_counts = {
        day: outgoing_queryset.filter(ngay_van_ban=day).count()
        for day in week_days
    }
    task_counts = {
        day: task_queryset.filter(ngay_bat_dau=day).count()
        for day in week_days
    }

    return [
        {
            "label": day.strftime("%a").replace("Mon", "T2").replace("Tue", "T3").replace("Wed", "T4").replace("Thu", "T5").replace("Fri", "T6").replace("Sat", "T7").replace("Sun", "CN"),
            "incoming": incoming_counts[day],
            "outgoing": outgoing_counts[day],
            "tasks": task_counts[day],
        }
        for day in week_days
    ]


def _build_status_breakdown(incoming_queryset, outgoing_queryset, task_queryset):
    pending_count = (
        incoming_queryset.filter(trang_thai=VanBanDen.TrangThai.CHO_XU_LY).count()
        + outgoing_queryset.filter(trang_thai=OUTGOING_STATUS_CHO_XU_LY).count()
        + task_queryset.filter(trang_thai=CongViec.TrangThai.CHO_XU_LY).count()
    )
    waiting_approval_count = (
        outgoing_queryset.filter(trang_thai=OUTGOING_STATUS_CHO_BAN_HANH).count()
        + task_queryset.filter(trang_thai=CongViec.TrangThai.CHO_DUYET).count()
    )
    returned_count = (
        incoming_queryset.filter(trang_thai=VanBanDen.TrangThai.HOAN_TRA).count()
        + outgoing_queryset.filter(trang_thai=OUTGOING_STATUS_HOAN_TRA).count()
        + task_queryset.filter(trang_thai__in=TASK_RETURNED_STATUSES).count()
    )
    completed_count = (
        incoming_queryset.filter(trang_thai__in=INCOMING_COMPLETED_STATUSES).count()
        + outgoing_queryset.filter(trang_thai__in=OUTGOING_COMPLETED_STATUSES).count()
        + task_queryset.filter(trang_thai=CongViec.TrangThai.DA_HOAN_THANH).count()
    )

    return [
        {"label": "Chờ xử lý", "count": pending_count, "color": "#f6b10a"},
        {"label": "Chờ duyệt", "count": waiting_approval_count, "color": "#7c78d5"},
        {"label": "Hoàn trả", "count": returned_count, "color": "#ef4444"},
        {"label": "Hoàn thành", "count": completed_count, "color": "#67c46a"},
    ]


def _build_recent_documents(incoming_queryset, outgoing_queryset):
    documents = []

    for item in incoming_queryset.order_by("-created_at")[:6]:
        documents.append(
            {
                "sort_date": item.created_at.date(),
                "code": item.so_ky_hieu,
                "title": f"[Đến] {item.trich_yeu}",
                "date": (item.ngay_den or timezone.localdate()).strftime("%d/%m/%Y"),
                "status_label": item.get_trang_thai_display(),
                "status_class": _document_status_badge(item.get_trang_thai_display()),
            }
        )

    for item in outgoing_queryset.order_by("-ngay_cap_nhat")[:6]:
        status_label = item.get_trang_thai_display()
        documents.append(
            {
                "sort_date": item.ngay_cap_nhat,
                "code": item.so_ky_hieu,
                "title": f"[Đi] {item.trich_yeu}",
                "date": (item.ngay_van_ban or timezone.localdate()).strftime("%d/%m/%Y"),
                "status_label": status_label,
                "status_class": _document_status_badge(status_label),
            }
        )

    documents.sort(key=lambda item: item["sort_date"], reverse=True)
    for item in documents:
        item.pop("sort_date", None)
    return documents[:5]


def _build_urgent_tasks(task_queryset, today):
    urgent_tasks = []
    for task in task_queryset.exclude(trang_thai=CongViec.TrangThai.DA_HOAN_THANH).order_by("han_xu_ly")[:5]:
        priority_label, priority_class = _task_priority_meta(task, today)
        urgent_tasks.append(
            {
                "title": task.ten_cong_viec,
                "assignee": task.nguoi_thuc_hien.ho_va_ten,
                "deadline": task.han_xu_ly.strftime("%d/%m/%Y"),
                "priority_label": priority_label,
                "priority_class": priority_class,
            }
        )
    return urgent_tasks


def _dashboard_metrics(today, incoming_queryset, outgoing_queryset, task_queryset, record_queryset):
    total_documents = incoming_queryset.count() + outgoing_queryset.count()
    incoming_pending = incoming_queryset.filter(trang_thai=VanBanDen.TrangThai.CHO_XU_LY).count()
    outgoing_waiting = outgoing_queryset.filter(trang_thai=OUTGOING_STATUS_CHO_BAN_HANH).count()
    active_tasks = task_queryset.filter(trang_thai__in=TASK_ACTIVE_STATUSES).count()
    pending_total = incoming_pending + outgoing_queryset.filter(trang_thai=OUTGOING_STATUS_CHO_XU_LY).count() + task_queryset.filter(
        trang_thai=CongViec.TrangThai.CHO_XU_LY
    ).count()
    returned_total = (
        incoming_queryset.filter(trang_thai=VanBanDen.TrangThai.HOAN_TRA).count()
        + outgoing_queryset.filter(trang_thai=OUTGOING_STATUS_HOAN_TRA).count()
        + task_queryset.filter(trang_thai__in=TASK_RETURNED_STATUSES).count()
    )
    completed_total = (
        incoming_queryset.filter(trang_thai__in=INCOMING_COMPLETED_STATUSES).count()
        + outgoing_queryset.filter(trang_thai__in=OUTGOING_COMPLETED_STATUSES).count()
        + task_queryset.filter(trang_thai=CongViec.TrangThai.DA_HOAN_THANH).count()
    )

    overdue_total = (
        incoming_queryset.exclude(trang_thai__in=INCOMING_COMPLETED_STATUSES).filter(han_xu_ly__lt=today).count()
        + outgoing_queryset.exclude(trang_thai__in=OUTGOING_COMPLETED_STATUSES).filter(han_xu_ly__lt=today).count()
        + task_queryset.exclude(trang_thai=CongViec.TrangThai.DA_HOAN_THANH).filter(han_xu_ly__date__lt=today).count()
    )
    active_records = record_queryset.filter(trang_thai=HoSoVanBan.TRANG_THAI_CHOICES[0][0]).count()
    completion_rate = round((completed_total / (pending_total + returned_total + completed_total)) * 100, 1) if (pending_total + returned_total + completed_total) else 0

    current_end = today + timedelta(days=1)
    current_start = today - timedelta(days=29)
    previous_end = current_start
    previous_start = previous_end - timedelta(days=30)

    total_documents_trend = _window_totals(
        [
            (incoming_queryset, "created_at__date", {}),
            (outgoing_queryset, "ngay_van_ban", {}),
        ],
        current_start,
        current_end,
        previous_start,
        previous_end,
    )
    incoming_trend = _window_totals(
        [(incoming_queryset, "created_at__date", {})],
        current_start,
        current_end,
        previous_start,
        previous_end,
    )
    outgoing_trend = _window_totals(
        [(outgoing_queryset, "ngay_van_ban", {})],
        current_start,
        current_end,
        previous_start,
        previous_end,
    )
    task_trend = _window_totals(
        [(task_queryset, "ngay_bat_dau", {})],
        current_start,
        current_end,
        previous_start,
        previous_end,
    )
    pending_trend = _window_totals(
        [
            (incoming_queryset, "created_at__date", {"trang_thai": VanBanDen.TrangThai.CHO_XU_LY}),
            (outgoing_queryset, "ngay_cap_nhat", {"trang_thai": OUTGOING_STATUS_CHO_XU_LY}),
            (task_queryset, "last_activity__date", {"trang_thai": CongViec.TrangThai.CHO_XU_LY}),
        ],
        current_start,
        current_end,
        previous_start,
        previous_end,
    )
    completed_trend = _window_totals(
        [
            (incoming_queryset, "updated_at__date", {"trang_thai__in": INCOMING_COMPLETED_STATUSES}),
            (outgoing_queryset, "ngay_cap_nhat", {"trang_thai__in": OUTGOING_COMPLETED_STATUSES}),
            (task_queryset, "last_activity__date", {"trang_thai": CongViec.TrangThai.DA_HOAN_THANH}),
        ],
        current_start,
        current_end,
        previous_start,
        previous_end,
    )

    return [
        {
            "label": "Tổng văn bản",
            "value": total_documents,
            "subtitle": f"30 ngày gần đây: {total_documents_trend[0]}",
            "trend": total_documents_trend[0],
            "trend_direction": total_documents_trend[1],
            "accent": "#3b82f6",
            "icon_path": "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zm-1 1.5L18.5 9H13zM6 20V4h5v7h7v9z",
        },
        {
            "label": "Văn bản đến",
            "value": incoming_queryset.count(),
            "subtitle": f"Chờ xử lý: {incoming_pending}",
            "trend": incoming_trend[0],
            "trend_direction": incoming_trend[1],
            "accent": "#10b981",
            "icon_path": "M19 7v4H5V7h14m0-2H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2m-7 9 4-4h-3V4h-2v6H8z",
        },
        {
            "label": "Văn bản đi",
            "value": outgoing_queryset.count(),
            "subtitle": f"Chờ ban hành: {outgoing_waiting}",
            "trend": outgoing_trend[0],
            "trend_direction": outgoing_trend[1],
            "accent": "#a855f7",
            "icon_path": "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zm-2 15-4-4h3V9h2v4h3zm1-7V3.5L18.5 9z",
        },
        {
            "label": "Công việc",
            "value": task_queryset.count(),
            "subtitle": f"Đang thực hiện: {active_tasks}",
            "trend": task_trend[0],
            "trend_direction": task_trend[1],
            "accent": "#f59e0b",
            "icon_path": "M20 7h-4V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2M10 5h4v2h-4zm10 13H4v-5h16zm0-7H4V9h16z",
        },
        {
            "label": "Chờ xử lý",
            "value": pending_total,
            "subtitle": f"Hoàn trả: {returned_total}",
            "trend": pending_trend[0],
            "trend_direction": pending_trend[1],
            "accent": "#eab308",
            "icon_path": "M12 1a11 11 0 1 0 11 11A11 11 0 0 0 12 1m1 11V6h-2v7h6v-2z",
        },
        {
            "label": "Đã hoàn thành",
            "value": completed_total,
            "subtitle": f"Tỷ lệ: {completion_rate}% | Quá hạn: {overdue_total}",
            "trend": completed_trend[0],
            "trend_direction": completed_trend[1],
            "accent": "#14b8a6",
            "icon_path": "M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2m-1 15-4-4 1.41-1.41L11 14.17l6.59-6.58L19 9z",
        },
    ]


def _recent_documents_url(user):
    if user.has_role(Customer.Role.ADMIN):
        return reverse("quanlyvanbandi:van_ban_di")
    return reverse("quanlyvanbanden:danh_sach")


def _urgent_tasks_url(user):
    if user.is_chuyen_vien:
        return reverse("quanlycongviec:xu_ly_cong_viec")
    return reverse("quanlycongviec:giao_viec")


@role_required(*Customer.Role.values)
def dashboard(request):
    today = timezone.localdate()
    incoming_queryset = _incoming_queryset_for_user(request.user)
    outgoing_queryset = _outgoing_queryset_for_user(request.user)
    task_queryset = _task_queryset_for_user(request.user)
    record_queryset = HoSoVanBan.objects.all()

    status_items = _build_status_breakdown(incoming_queryset, outgoing_queryset, task_queryset)
    status_gradient, status_breakdown = _build_status_gradient(status_items)

    context = {
        "dashboard_metrics": _dashboard_metrics(
            today,
            incoming_queryset,
            outgoing_queryset,
            task_queryset,
            record_queryset,
        ),
        "weekly_chart": _build_weekly_chart(
            _build_weekly_series(today, incoming_queryset, outgoing_queryset, task_queryset)
        ),
        "status_breakdown": status_breakdown,
        "status_gradient": status_gradient,
        "status_total": sum(item["count"] for item in status_items),
        "status_total_label": "đầu việc",
        "recent_documents": _build_recent_documents(incoming_queryset, outgoing_queryset),
        "recent_documents_url": _recent_documents_url(request.user),
        "urgent_tasks": _build_urgent_tasks(task_queryset, today),
        "urgent_tasks_url": _urgent_tasks_url(request.user),
        "record_total": record_queryset.count(),
        "record_active_total": record_queryset.filter(
            trang_thai=HoSoVanBan.TRANG_THAI_CHOICES[0][0]
        ).count(),
    }
    return render(request, "core/dashboard.html", context)


@role_required(*Customer.Role.values)
def bao_cao_thong_ke(request):
    return render(request, "bao-cao-thong-ke.html")
