from datetime import timedelta

from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from apps.accounts.decorators import role_required
from apps.accounts.models import Customer

from .models import (
    ChuyenTiepChiTiet,
    CongViec,
    HoSoVanBan,
    LichSuHoatDong,
    NguoiDung,
    PhongBan,
    VanBan,
)


# =========================================================
# HẰNG SỐ VĂN BẢN
# =========================================================

INCOMING_KIND = "Văn bản đến"
OUTGOING_KIND = "Văn bản đi"

STATUS_CHO_XU_LY = "Chờ Xử Lý"
STATUS_DA_XU_LY = "Đã Xử Lý"
STATUS_HOAN_TRA = "Hoàn Trả"
STATUS_XEM_DE_BIET = "Xem Để Biết"
STATUS_CHO_BAN_HANH = "Chờ ban hành"
STATUS_DA_BAN_HANH = "Đã ban hành"

CLERK_VISIBLE_OUTGOING_STATUSES = [
    STATUS_CHO_BAN_HANH,
    STATUS_DA_BAN_HANH,
    STATUS_XEM_DE_BIET,
]

OUTGOING_COMPLETED_STATUSES = [
    STATUS_DA_XU_LY,
    STATUS_DA_BAN_HANH,
    STATUS_XEM_DE_BIET,
]

INCOMING_COMPLETED_STATUSES = [
    STATUS_DA_XU_LY,
    STATUS_XEM_DE_BIET,
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


# =========================================================
# HÀM HỖ TRỢ USER CORE
# =========================================================

def _lay_nguoi_dung_core(user):
    """
    Lấy hồ sơ NguoiDung trong app core từ tài khoản đăng nhập.

    Model chung VanBan/CongViec dùng core.NguoiDung,
    không dùng trực tiếp accounts.Customer.
    """
    if not user or not user.is_authenticated:
        return None

    nguoi_dung = NguoiDung.objects.filter(tai_khoan=user).first()

    if not nguoi_dung and getattr(user, "email", None):
        nguoi_dung = NguoiDung.objects.filter(email=user.email).first()

    return nguoi_dung


# =========================================================
# HÀM VẼ BIỂU ĐỒ / THỐNG KÊ
# =========================================================

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
        enriched_items.append({
            **item,
            "percentage": percentage,
        })

        start = end

    if start < 100:
        segments.append(f"#e5e7eb {start:.1f}% 100%")

    return f"conic-gradient({', '.join(segments)})", enriched_items


def _build_weekly_chart(series):
    max_value = max(
        max(item["incoming"], item["outgoing"], item["tasks"])
        for item in series
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
        chart.append({
            **item,
            "incoming_height": round((item["incoming"] / max_value) * 100, 1),
            "outgoing_height": round((item["outgoing"] / max_value) * 100, 1),
            "tasks_height": round((item["tasks"] / max_value) * 100, 1),
        })

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


# =========================================================
# QUERYSET THEO QUYỀN
# =========================================================

def _incoming_queryset_for_user(user):
    """
    Văn bản đến bây giờ dùng model chung VanBan,
    lọc bằng phan_loai = 'Văn bản đến'.
    """
    queryset = VanBan.objects.select_related(
        "nguoi_tao",
        "lanh_dao_duyet",
        "ho_so_van_ban",
    ).filter(
        phan_loai=INCOMING_KIND
    )

    nguoi_dung_core = _lay_nguoi_dung_core(user)

    if user.has_role(Customer.Role.ADMIN, Customer.Role.VAN_THU):
        return queryset

    if user.is_lanh_dao:
        if not nguoi_dung_core:
            return queryset.none()

        return queryset.filter(lanh_dao_duyet=nguoi_dung_core)

    if user.is_chuyen_vien:
        if not nguoi_dung_core:
            return queryset.none()

        return queryset.filter(
            vanbanduyet__chuyentiep__chuyentiepchitiet__nguoi_dung=nguoi_dung_core
        ).distinct()

    return queryset.none()


def _outgoing_queryset_for_user(user):
    queryset = VanBan.objects.select_related(
        "nguoi_tao",
        "lanh_dao_duyet",
        "ho_so_van_ban",
    ).filter(
        phan_loai=OUTGOING_KIND
    )

    nguoi_dung_core = _lay_nguoi_dung_core(user)

    if user.has_role(Customer.Role.ADMIN):
        return queryset

    if user.is_van_thu:
        return queryset.filter(trang_thai__in=CLERK_VISIBLE_OUTGOING_STATUSES)

    if user.is_lanh_dao:
        if not nguoi_dung_core:
            return queryset.none()

        return queryset.filter(lanh_dao_duyet=nguoi_dung_core)

    if user.is_chuyen_vien:
        if not nguoi_dung_core:
            return queryset.none()

        return queryset.filter(nguoi_tao=nguoi_dung_core)

    return queryset.none()


def _task_queryset_for_user(user):
    queryset = CongViec.objects.select_related(
        "nguoi_giao",
        "nguoi_thuc_hien",
        "van_ban",
    )

    nguoi_dung_core = _lay_nguoi_dung_core(user)

    if user.has_role(Customer.Role.ADMIN, Customer.Role.VAN_THU):
        return queryset

    if user.is_lanh_dao:
        if not nguoi_dung_core:
            return queryset.none()

        return queryset.filter(nguoi_giao=nguoi_dung_core)

    if user.is_chuyen_vien:
        if not nguoi_dung_core:
            return queryset.none()

        return queryset.filter(nguoi_thuc_hien=nguoi_dung_core)

    return queryset.none()


# =========================================================
# BUILD DATA DASHBOARD
# =========================================================

def _build_weekly_series(today, incoming_queryset, outgoing_queryset, task_queryset):
    week_days = [
        today - timedelta(days=offset)
        for offset in range(6, -1, -1)
    ]

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
            "label": day.strftime("%a")
            .replace("Mon", "T2")
            .replace("Tue", "T3")
            .replace("Wed", "T4")
            .replace("Thu", "T5")
            .replace("Fri", "T6")
            .replace("Sat", "T7")
            .replace("Sun", "CN"),
            "incoming": incoming_counts[day],
            "outgoing": outgoing_counts[day],
            "tasks": task_counts[day],
        }
        for day in week_days
    ]


def _build_status_breakdown(incoming_queryset, outgoing_queryset, task_queryset):
    pending_count = (
        incoming_queryset.filter(trang_thai=STATUS_CHO_XU_LY).count()
        + outgoing_queryset.filter(trang_thai=STATUS_CHO_XU_LY).count()
        + task_queryset.filter(trang_thai=CongViec.TrangThai.CHO_XU_LY).count()
    )

    waiting_approval_count = (
        outgoing_queryset.filter(trang_thai=STATUS_CHO_BAN_HANH).count()
        + task_queryset.filter(trang_thai=CongViec.TrangThai.CHO_DUYET).count()
    )

    returned_count = (
        incoming_queryset.filter(trang_thai=STATUS_HOAN_TRA).count()
        + outgoing_queryset.filter(trang_thai=STATUS_HOAN_TRA).count()
        + task_queryset.filter(trang_thai__in=TASK_RETURNED_STATUSES).count()
    )

    completed_count = (
        incoming_queryset.filter(trang_thai__in=INCOMING_COMPLETED_STATUSES).count()
        + outgoing_queryset.filter(trang_thai__in=OUTGOING_COMPLETED_STATUSES).count()
        + task_queryset.filter(trang_thai=CongViec.TrangThai.DA_HOAN_THANH).count()
    )

    return [
        {
            "label": "Chờ xử lý",
            "count": pending_count,
            "color": "#f6b10a",
        },
        {
            "label": "Chờ duyệt",
            "count": waiting_approval_count,
            "color": "#7c78d5",
        },
        {
            "label": "Hoàn trả",
            "count": returned_count,
            "color": "#ef4444",
        },
        {
            "label": "Hoàn thành",
            "count": completed_count,
            "color": "#67c46a",
        },
    ]


def _build_recent_documents(incoming_queryset, outgoing_queryset):
    documents = []

    for item in incoming_queryset.order_by("-ngay_cap_nhat", "-van_ban_id")[:6]:
        status_label = item.get_trang_thai_display()

        documents.append({
            "sort_date": item.ngay_cap_nhat,
            "code": item.so_ky_hieu,
            "title": f"[Đến] {item.trich_yeu}",
            "date": (item.ngay_den or timezone.localdate()).strftime("%d/%m/%Y"),
            "status_label": status_label,
            "status_class": _document_status_badge(status_label),
        })

    for item in outgoing_queryset.order_by("-ngay_cap_nhat", "-van_ban_id")[:6]:
        status_label = item.get_trang_thai_display()

        documents.append({
            "sort_date": item.ngay_cap_nhat,
            "code": item.so_ky_hieu,
            "title": f"[Đi] {item.trich_yeu}",
            "date": (item.ngay_van_ban or timezone.localdate()).strftime("%d/%m/%Y"),
            "status_label": status_label,
            "status_class": _document_status_badge(status_label),
        })

    documents.sort(key=lambda item: item["sort_date"], reverse=True)

    for item in documents:
        item.pop("sort_date", None)

    return documents[:5]


def _build_urgent_tasks(task_queryset, today):
    urgent_tasks = []

    for task in task_queryset.exclude(
        trang_thai=CongViec.TrangThai.DA_HOAN_THANH
    ).order_by("han_xu_ly")[:5]:
        priority_label, priority_class = _task_priority_meta(task, today)

        urgent_tasks.append({
            "title": task.ten_cong_viec,
            "assignee": task.nguoi_thuc_hien.ho_va_ten,
            "deadline": task.han_xu_ly.strftime("%d/%m/%Y"),
            "priority_label": priority_label,
            "priority_class": priority_class,
        })

    return urgent_tasks


def _dashboard_metrics(today, incoming_queryset, outgoing_queryset, task_queryset, record_queryset):
    total_documents = incoming_queryset.count() + outgoing_queryset.count()

    incoming_pending = incoming_queryset.filter(
        trang_thai=STATUS_CHO_XU_LY
    ).count()

    outgoing_waiting = outgoing_queryset.filter(
        trang_thai=STATUS_CHO_BAN_HANH
    ).count()

    active_tasks = task_queryset.filter(
        trang_thai__in=TASK_ACTIVE_STATUSES
    ).count()

    pending_total = (
        incoming_pending
        + outgoing_queryset.filter(trang_thai=STATUS_CHO_XU_LY).count()
        + task_queryset.filter(trang_thai=CongViec.TrangThai.CHO_XU_LY).count()
    )

    returned_total = (
        incoming_queryset.filter(trang_thai=STATUS_HOAN_TRA).count()
        + outgoing_queryset.filter(trang_thai=STATUS_HOAN_TRA).count()
        + task_queryset.filter(trang_thai__in=TASK_RETURNED_STATUSES).count()
    )

    completed_total = (
        incoming_queryset.filter(trang_thai__in=INCOMING_COMPLETED_STATUSES).count()
        + outgoing_queryset.filter(trang_thai__in=OUTGOING_COMPLETED_STATUSES).count()
        + task_queryset.filter(trang_thai=CongViec.TrangThai.DA_HOAN_THANH).count()
    )

    overdue_total = (
        incoming_queryset.exclude(
            trang_thai__in=INCOMING_COMPLETED_STATUSES
        ).filter(
            han_xu_ly__lt=today
        ).count()
        + outgoing_queryset.exclude(
            trang_thai__in=OUTGOING_COMPLETED_STATUSES
        ).filter(
            han_xu_ly__lt=today
        ).count()
        + task_queryset.exclude(
            trang_thai=CongViec.TrangThai.DA_HOAN_THANH
        ).filter(
            han_xu_ly__date__lt=today
        ).count()
    )

    active_records = record_queryset.filter(
        trang_thai=HoSoVanBan.TRANG_THAI_CHOICES[0][0]
    ).count()

    completion_rate = round(
        (completed_total / (pending_total + returned_total + completed_total)) * 100,
        1
    ) if (pending_total + returned_total + completed_total) else 0

    current_end = today + timedelta(days=1)
    current_start = today - timedelta(days=29)
    previous_end = current_start
    previous_start = previous_end - timedelta(days=30)

    total_documents_trend = _window_totals(
        [
            (incoming_queryset, "ngay_cap_nhat", {}),
            (outgoing_queryset, "ngay_van_ban", {}),
        ],
        current_start,
        current_end,
        previous_start,
        previous_end,
    )

    incoming_trend = _window_totals(
        [
            (incoming_queryset, "ngay_cap_nhat", {}),
        ],
        current_start,
        current_end,
        previous_start,
        previous_end,
    )

    outgoing_trend = _window_totals(
        [
            (outgoing_queryset, "ngay_van_ban", {}),
        ],
        current_start,
        current_end,
        previous_start,
        previous_end,
    )

    task_trend = _window_totals(
        [
            (task_queryset, "ngay_bat_dau", {}),
        ],
        current_start,
        current_end,
        previous_start,
        previous_end,
    )

    pending_trend = _window_totals(
        [
            (incoming_queryset, "ngay_cap_nhat", {"trang_thai": STATUS_CHO_XU_LY}),
            (outgoing_queryset, "ngay_cap_nhat", {"trang_thai": STATUS_CHO_XU_LY}),
            (task_queryset, "last_activity__date", {"trang_thai": CongViec.TrangThai.CHO_XU_LY}),
        ],
        current_start,
        current_end,
        previous_start,
        previous_end,
    )

    completed_trend = _window_totals(
        [
            (incoming_queryset, "ngay_cap_nhat", {"trang_thai__in": INCOMING_COMPLETED_STATUSES}),
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


# =========================================================
# DASHBOARD
# =========================================================

@role_required(*Customer.Role.values)
def dashboard(request):
    today = timezone.localdate()

    incoming_queryset = _incoming_queryset_for_user(request.user)
    outgoing_queryset = _outgoing_queryset_for_user(request.user)
    task_queryset = _task_queryset_for_user(request.user)
    record_queryset = HoSoVanBan.objects.all()

    status_items = _build_status_breakdown(
        incoming_queryset,
        outgoing_queryset,
        task_queryset,
    )

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
            _build_weekly_series(
                today,
                incoming_queryset,
                outgoing_queryset,
                task_queryset,
            )
        ),
        "status_breakdown": status_breakdown,
        "status_gradient": status_gradient,
        "status_total": sum(item["count"] for item in status_items),
        "status_total_label": "đầu việc",
        "recent_documents": _build_recent_documents(
            incoming_queryset,
            outgoing_queryset,
        ),
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
    """Báo cáo thống kê dựa trên dữ liệu thực từ database."""
    import json as _json
    from datetime import date, timedelta
    from django.db.models import Count, F, Q

    # ── Tab hiện tại ──────────────────────────────────────────────
    tab = request.GET.get('tab', 'van-ban')  # 'van-ban' | 'cong-viec'

    # ── Parse ngày ────────────────────────────────────────────────
    tu_ngay_str = request.GET.get('tu_ngay', '').strip()
    den_ngay_str = request.GET.get('den_ngay', '').strip()
    tu_ngay = den_ngay = None
    loi_ngay = ''
    da_xem = bool(request.GET.get('xem', ''))

    try:
        if tu_ngay_str:
            tu_ngay = date.fromisoformat(tu_ngay_str)
        if den_ngay_str:
            den_ngay = date.fromisoformat(den_ngay_str)
    except ValueError:
        pass

    if da_xem and (not tu_ngay or not den_ngay):
        loi_ngay = 'Vui lòng chọn khoảng thời gian thống kê.'

    today = date.today()

    # ── Dropdown choices ──────────────────────────────────────────
    loai_van_ban_choices = VanBan.LOAI_VAN_BAN_CHOICES
    hinh_thuc_choices = VanBan.HINH_THUC_CHOICES
    don_vi_list = list(
        VanBan.objects.exclude(don_vi_ban_hanh__isnull=True)
                      .exclude(don_vi_ban_hanh='')
                      .values_list('don_vi_ban_hanh', flat=True)
                      .distinct().order_by('don_vi_ban_hanh')
    )
    phong_ban_list = PhongBan.objects.order_by('ten_phong_ban')
    nguoi_dung_list = NguoiDung.objects.select_related('phong_ban').order_by('ho_va_ten')

    # ── Filter params (Tab VB) ────────────────────────────────────
    p_loai_vb  = request.GET.get('loai_van_ban', '')
    p_don_vi   = request.GET.get('don_vi_ban_hanh', '')
    p_tt_vb    = request.GET.get('trang_thai_vb', '')
    p_tieu_chi = request.GET.get('tieu_chi', 'Tổng hợp')

    # ── Filter params (Tab CV) ────────────────────────────────────
    p_doi_tuong  = request.GET.get('doi_tuong', 'Đơn vị')
    p_phong_ban  = request.GET.get('phong_ban', '')
    p_nhan_vien  = request.GET.get('nhan_vien', '')
    p_tt_cv      = request.GET.get('trang_thai_cv', '')

    # ═══════════════════════════════════════════════════════════════
    # TAB 1 – Thống kê văn bản
    # ═══════════════════════════════════════════════════════════════
    vb_qs = VanBan.objects.all()
    if tu_ngay:
        vb_qs = vb_qs.filter(ngay_van_ban__gte=tu_ngay)
    if den_ngay:
        vb_qs = vb_qs.filter(ngay_van_ban__lte=den_ngay)
    if p_loai_vb:
        vb_qs = vb_qs.filter(loai_van_ban=p_loai_vb)
    if p_don_vi:
        vb_qs = vb_qs.filter(don_vi_ban_hanh=p_don_vi)
    if p_tt_vb:
        vb_qs = vb_qs.filter(trang_thai=p_tt_vb)

    tong_vb = vb_qs.count()

    # Đúng hạn: đã xử lý/ban hành & (han_xu_ly là null HOẶC ngay_van_ban <= han_xu_ly)
    TRANG_THAI_HOAN_THANH = ['Đã Xử Lý', 'Đã ban hành', 'Xem Để Biết']
    dung_han_vb = vb_qs.filter(
        Q(trang_thai__in=TRANG_THAI_HOAN_THANH) &
        (Q(han_xu_ly__isnull=True) | Q(ngay_van_ban__lte=F('han_xu_ly')))
    ).count()
    tre_han_vb = vb_qs.filter(
        Q(trang_thai__in=TRANG_THAI_HOAN_THANH) &
        Q(han_xu_ly__isnull=False) &
        Q(ngay_van_ban__gt=F('han_xu_ly'))
    ).count()

    # Tỷ lệ trạng thái cho pie chart
    cho_xu_ly_vb = vb_qs.filter(trang_thai__in=['Chờ Xử Lý', 'Chờ ban hành']).count()
    cho_duyet_vb = vb_qs.filter(trang_thai='Hoàn Trả').count()
    da_ht_vb     = vb_qs.filter(trang_thai__in=TRANG_THAI_HOAN_THANH).count()

    # Bar chart: breakdown theo hinh_thuc
    HINH_THUC_LABELS = ['Quyết định', 'Công văn', 'Thông báo', 'Tờ trình', 'Báo cáo', 'Hợp đồng']
    bar_vb_labels = []
    bar_cho_duyet = []
    bar_cho_xu_ly = []
    bar_hoan_thanh = []

    for ht in HINH_THUC_LABELS:
        sub = vb_qs.filter(hinh_thuc=ht)
        cnt = sub.count()
        if cnt == 0:
            continue
        bar_vb_labels.append(ht)
        bar_cho_duyet.append(sub.filter(trang_thai='Hoàn Trả').count())
        bar_cho_xu_ly.append(sub.filter(trang_thai__in=['Chờ Xử Lý', 'Chờ ban hành']).count())
        bar_hoan_thanh.append(sub.filter(trang_thai__in=TRANG_THAI_HOAN_THANH).count())

    # Bảng chi tiết theo loai_van_ban
    bang_vb = []
    for loai, _ in VanBan.LOAI_VAN_BAN_CHOICES:
        sub = vb_qs.filter(loai_van_ban=loai)
        cnt = sub.count()
        if cnt == 0:
            continue
        dh = sub.filter(
            Q(trang_thai__in=TRANG_THAI_HOAN_THANH) &
            (Q(han_xu_ly__isnull=True) | Q(ngay_van_ban__lte=F('han_xu_ly')))
        ).count()
        th = sub.filter(
            Q(trang_thai__in=TRANG_THAI_HOAN_THANH) &
            Q(han_xu_ly__isnull=False) &
            Q(ngay_van_ban__gt=F('han_xu_ly'))
        ).count()
        cx = sub.filter(trang_thai__in=['Chờ Xử Lý', 'Chờ ban hành']).count()
        bang_vb.append({'loai': loai, 'tong': cnt, 'dung_han': dh, 'tre_han': th, 'cho_xu_ly': cx})

    # ═══════════════════════════════════════════════════════════════
    # TAB 2 – Thống kê công việc
    # ═══════════════════════════════════════════════════════════════
    cv_qs = CongViec.objects.select_related('nguoi_thuc_hien__phong_ban')
    if tu_ngay:
        cv_qs = cv_qs.filter(ngay_bat_dau__gte=tu_ngay)
    if den_ngay:
        cv_qs = cv_qs.filter(ngay_bat_dau__lte=den_ngay)
    if p_phong_ban:
        cv_qs = cv_qs.filter(nguoi_thuc_hien__phong_ban__phong_ban_id=p_phong_ban)
    if p_nhan_vien:
        cv_qs = cv_qs.filter(nguoi_thuc_hien__nguoi_dung_id=p_nhan_vien)
    if p_tt_cv:
        cv_qs = cv_qs.filter(trang_thai=p_tt_cv)

    tong_cv      = cv_qs.count()
    hoan_thanh   = cv_qs.filter(trang_thai=CongViec.TrangThai.DA_HOAN_THANH).count()
    dang_xu_ly   = cv_qs.filter(trang_thai=CongViec.TrangThai.CHO_DUYET).count()
    cho_xu_ly_cv = cv_qs.filter(trang_thai=CongViec.TrangThai.CHO_XU_LY).count()
    hoan_tra_cv  = cv_qs.filter(trang_thai__in=[CongViec.TrangThai.HOAN_TRA_CV, CongViec.TrangThai.HOAN_TRA_LD]).count()

    # Pie chart CV
    pie_cv = {
        'hoan_thanh': hoan_thanh,
        'dang_xu_ly': dang_xu_ly,
        'cho_xu_ly':  cho_xu_ly_cv,
        'hoan_tra':   hoan_tra_cv,
    }

    # Bar chart CV: theo cá nhân hoặc đơn vị
    bar_cv_labels = []
    bar_cv_cho    = []
    bar_cv_dang   = []
    bar_cv_ht     = []

    if p_doi_tuong == 'Cá nhân':
        from django.db.models import Subquery, OuterRef
        people = (cv_qs.values('nguoi_thuc_hien__nguoi_dung_id', 'nguoi_thuc_hien__ho_va_ten')
                       .annotate(cnt=Count('cong_viec_id'))
                       .order_by('-cnt')[:8])
        for p in people:
            pid = p['nguoi_thuc_hien__nguoi_dung_id']
            name = p['nguoi_thuc_hien__ho_va_ten'] or f'ID {pid}'
            sub = cv_qs.filter(nguoi_thuc_hien__nguoi_dung_id=pid)
            bar_cv_labels.append(name[:20])
            bar_cv_cho.append(sub.filter(trang_thai=CongViec.TrangThai.CHO_XU_LY).count())
            bar_cv_dang.append(sub.filter(trang_thai=CongViec.TrangThai.CHO_DUYET).count())
            bar_cv_ht.append(sub.filter(trang_thai=CongViec.TrangThai.DA_HOAN_THANH).count())
    else:
        phong_bans = (cv_qs.values('nguoi_thuc_hien__phong_ban__phong_ban_id',
                                   'nguoi_thuc_hien__phong_ban__ten_phong_ban')
                           .annotate(cnt=Count('cong_viec_id'))
                           .order_by('-cnt')[:8])
        for pb in phong_bans:
            pbid = pb['nguoi_thuc_hien__phong_ban__phong_ban_id']
            name = pb['nguoi_thuc_hien__phong_ban__ten_phong_ban'] or 'Chưa phân công'
            sub = cv_qs.filter(nguoi_thuc_hien__phong_ban__phong_ban_id=pbid)
            bar_cv_labels.append(name[:25])
            bar_cv_cho.append(sub.filter(trang_thai=CongViec.TrangThai.CHO_XU_LY).count())
            bar_cv_dang.append(sub.filter(trang_thai=CongViec.TrangThai.CHO_DUYET).count())
            bar_cv_ht.append(sub.filter(trang_thai=CongViec.TrangThai.DA_HOAN_THANH).count())

    # Bảng chi tiết CV: per tên công việc
    bang_cv = []
    cv_group = (cv_qs.values('ten_cong_viec')
                     .annotate(tong=Count('cong_viec_id'))
                     .order_by('-tong')[:20])
    for row in cv_group:
        tcv = row['ten_cong_viec']
        sub = cv_qs.filter(ten_cong_viec=tcv)
        ht  = sub.filter(trang_thai=CongViec.TrangThai.DA_HOAN_THANH).count()
        dh  = sub.filter(
            trang_thai=CongViec.TrangThai.DA_HOAN_THANH,
            han_xu_ly__gte=today
        ).count()
        th  = sub.filter(
            trang_thai=CongViec.TrangThai.DA_HOAN_THANH,
            han_xu_ly__lt=today
        ).count()
        pct = f'{ht/row["tong"]*100:.1f}%' if row['tong'] else '0.0%'
        bang_cv.append({
            'ten': tcv,
            'tong': row['tong'],
            'hoan_thanh': ht,
            'dung_han': dh,
            'tre_han': th,
            'ty_le': pct,
        })

    # ── Context ────────────────────────────────────────────────────
    context = {
        'tab': tab,
        'tu_ngay': tu_ngay_str,
        'den_ngay': den_ngay_str,
        'da_xem': da_xem,
        'loi_ngay': loi_ngay,

        # Dropdown
        'loai_van_ban_choices': loai_van_ban_choices,
        'hinh_thuc_choices': hinh_thuc_choices,
        'don_vi_list': don_vi_list,
        'phong_ban_list': phong_ban_list,
        'nguoi_dung_list': nguoi_dung_list,

        # Params hiện tại
        'p_loai_vb': p_loai_vb,
        'p_don_vi': p_don_vi,
        'p_tt_vb': p_tt_vb,
        'p_tieu_chi': p_tieu_chi,
        'p_doi_tuong': p_doi_tuong,
        'p_phong_ban': p_phong_ban,
        'p_nhan_vien': p_nhan_vien,
        'p_tt_cv': p_tt_cv,

        # Tab VB - summary
        'tong_vb': tong_vb,
        'dung_han_vb': dung_han_vb,
        'tre_han_vb': tre_han_vb,
        'pct_dung_han_vb': f'{dung_han_vb/tong_vb*100:.1f}' if tong_vb else '0.0',
        'pct_tre_han_vb':  f'{tre_han_vb/tong_vb*100:.1f}'  if tong_vb else '0.0',

        # Tab VB - chart data (JSON for JS)
        'bar_vb_labels_json':  _json.dumps(bar_vb_labels, ensure_ascii=False),
        'bar_cho_duyet_json':  _json.dumps(bar_cho_duyet),
        'bar_cho_xu_ly_json':  _json.dumps(bar_cho_xu_ly),
        'bar_hoan_thanh_json': _json.dumps(bar_hoan_thanh),
        'pie_vb_json': _json.dumps({
            'da_ht': da_ht_vb,
            'cho_xu_ly': cho_xu_ly_vb,
            'cho_duyet': cho_duyet_vb,
        }),

        # Tab VB - bảng
        'bang_vb': bang_vb,

        # Tab CV - summary
        'tong_cv': tong_cv,
        'hoan_thanh': hoan_thanh,
        'dang_xu_ly': dang_xu_ly,
        'pct_hoan_thanh': f'{hoan_thanh/tong_cv*100:.1f}' if tong_cv else '0.0',
        'pct_dang_xu_ly': f'{dang_xu_ly/tong_cv*100:.1f}' if tong_cv else '0.0',

        # Tab CV - chart data (JSON for JS)
        'bar_cv_labels_json': _json.dumps(bar_cv_labels, ensure_ascii=False),
        'bar_cv_cho_json':   _json.dumps(bar_cv_cho),
        'bar_cv_dang_json':  _json.dumps(bar_cv_dang),
        'bar_cv_ht_json':    _json.dumps(bar_cv_ht),
        'pie_cv_json': _json.dumps(pie_cv),

        # Tab CV - bảng
        'bang_cv': bang_cv,

        # Legacy (giữ tương thích nếu có template cũ dùng)
        'loai_bao_cao': tab,
        'tong_vb_den': vb_qs.filter(phan_loai='Văn bản đến').count(),
        'tong_vb_di':  vb_qs.filter(phan_loai='Văn bản đi').count(),
    }
    return render(request, 'bao-cao-thong-ke.html', context)


@role_required(*Customer.Role.values)
def lich_su_hoat_dong(request):
    """Xem lịch sử hoạt động toàn hệ thống."""
    from django.core.paginator import Paginator

    ds = LichSuHoatDong.objects.select_related('nguoi_thuc_hien').order_by('-thoi_gian_thuc_hien')

    # Lọc theo loại đối tượng nếu có
    doi_tuong_loai = request.GET.get('doi_tuong_loai', '').strip()
    hanh_dong = request.GET.get('hanh_dong', '').strip()
    if doi_tuong_loai:
        ds = ds.filter(doi_tuong_loai=doi_tuong_loai)
    if hanh_dong:
        ds = ds.filter(hanh_dong=hanh_dong)

    paginator = Paginator(ds, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'doi_tuong_loai': doi_tuong_loai,
        'hanh_dong': hanh_dong,
        'loai_choices': LichSuHoatDong.DoiTuongLoai.choices,
        'hanh_dong_choices': LichSuHoatDong.HanhDong.choices,
    }
    return render(request, 'core/lich-su-hoat-dong.html', context)