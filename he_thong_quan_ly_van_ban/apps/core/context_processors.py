from django.urls import NoReverseMatch, reverse

from ..accounts.models import Customer


ALL_ROLES = tuple(Customer.Role.values)

TOP_MENU_DEFINITIONS = (
    {
        "label": "Trang chủ",
        "url_name": "core:dashboard",
        "roles": ALL_ROLES,
        "icon_path": "M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z",
        "help_text": "",
    },
    {
        "label": "Thông tin cá nhân",
        "url_name": None,
        "roles": ALL_ROLES,
        "icon_path": "M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z",
        "help_text": "Chuc nang dang cho tich hop.",
    },
    {
        "label": "Bộ công cụ quản lý",
        "url_name": "core:bao_cao_thong_ke",
        "roles": (Customer.Role.ADMIN, Customer.Role.LANH_DAO),
        "icon_path": "M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14H7v-2h5v2zm5-4H7v-2h10v2zm0-4H7V7h10v2z",
        "help_text": "Module bao cao dang cho tich hop.",
    },
    {
        "label": "Hướng dẫn sử dụng",
        "url_name": None,
        "roles": ALL_ROLES,
        "icon_path": "M12 3L1 9l11 6 9-4.91V17h2V9L12 3zm0 13L3.74 11.5 12 7l8.26 4.5L12 16z",
        "help_text": "Chuc nang dang cho tich hop.",
    },
)

SIDEBAR_MENU_DEFINITIONS = (
    {
        "label": "Tổng quan",
        "url_name": "core:dashboard",
        "roles": ALL_ROLES,
        "icon_path": "M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z",
        "help_text": "",
    },
    {
        "label": "Văn bản đến",
        "url_name": "quanlyvanbanden:danh_sach",
        "roles": ALL_ROLES,
        "icon_path": "M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z",
        "help_text": "Module van ban den chua duoc tich hop vao Django URLs.",
    },
    {
        "label": "Văn bản đi",
        "url_name": "quanlyvanbandi:van_ban_di",
        "roles": ALL_ROLES,
        "icon_path": "M2.01 21L23 12 2.01 3 2 10l15 2-15 2z",
        "help_text": "",
    },
    {
        "label": "Quản lý công việc",
        "url_name": "quanlycongviec:giao_viec",
        "roles": (Customer.Role.ADMIN, Customer.Role.LANH_DAO, Customer.Role.VAN_THU),
        "icon_path": "M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z",
        "help_text": "",
    },
    {
        "label": "Quản lý công việc",
        "url_name": "quanlycongviec:xu_ly_cong_viec",
        "roles": (Customer.Role.CHUYEN_VIEN,),
        "icon_path": "M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z",
        "help_text": "",
    },
    {
        "label": "Hồ sơ văn bản",
        "url_name": "hosovanban:danh_sach",
        "roles": ALL_ROLES,
        "icon_path": "M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z",
        "help_text": "Module ho so van ban dang cho tich hop.",
    },
    {
        "label": "Báo cáo thống kê",
        "url_name": "core:bao_cao_thong_ke",
        "roles": ALL_ROLES,
        "icon_path": "M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 3c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6zm7 13H5v-.23c0-.62.28-1.2.76-1.58C7.47 15.82 9.64 15 12 15s4.53.82 6.24 2.19c.48.38.76.97.76 1.58V19z",
        "help_text": "Module bao cao thong ke dang cho tich hop.",
    },
)


def _resolve_url(url_name):
    if not url_name:
        return "#", False
    try:
        return reverse(url_name), True
    except NoReverseMatch:
        return "#", False


def _build_navigation_items(request, definitions):
    current_view_name = getattr(getattr(request, "resolver_match", None), "view_name", "")
    user = request.user
    items = []

    for definition in definitions:
        if not user.has_role(*definition["roles"]):
            continue

        href, is_enabled = _resolve_url(definition["url_name"])
        items.append(
            {
                **definition,
                "href": href,
                "is_enabled": is_enabled,
                "active": is_enabled and current_view_name == definition["url_name"],
            }
        )

    return items


def auth_shell(request):
    if not getattr(request.user, "is_authenticated", False):
        return {
            "current_role": "",
            "current_role_display": "",
            "shell_user": {},
            "top_menu_items": [],
            "sidebar_menu_items": [],
        }

    user = request.user
    return {
        "current_role": user.role,
        "current_role_display": user.display_role,
        "shell_user": {
            "display_name": user.display_name,
            "role_display": user.display_role,
            "initials": user.initials,
            "branch_name": getattr(user.chi_nhanh, "ten_chi_nhanh", "Chua gan"),
            "department_name": getattr(user.phong_ban, "ten_phong_ban", "Chua gan"),
        },
        "top_menu_items": _build_navigation_items(request, TOP_MENU_DEFINITIONS),
        "sidebar_menu_items": _build_navigation_items(request, SIDEBAR_MENU_DEFINITIONS),
    }
