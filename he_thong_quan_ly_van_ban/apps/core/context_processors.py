from django.urls import NoReverseMatch, reverse

from ..accounts.models import Customer


# File này cung cấp dữ liệu layout chung: menu top, sidebar và thông tin user.

ALL_ROLES = tuple(Customer.Role.values)

# Định nghĩa menu trên cùng, mỗi item có URL, icon và nhóm role được phép thấy.
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
        "url_name": "accounts:profile",
        "roles": ALL_ROLES,
        "icon_path": "M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z",
        "help_text": "Chức năng đang chờ tích hợp.",
    },
    {
        "label": "Bộ công cụ quản lý",
        "url_name": "core:bao_cao_thong_ke",
        "roles": ALL_ROLES,
        "icon_path": "M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14H7v-2h5v2zm5-4H7v-2h10v2zm0-4H7V7h10v2z",
        "help_text": "",
    },
    {
        "label": "Hướng dẫn sử dụng",
        "url_name": None,
        "roles": ALL_ROLES,
        "icon_path": "M12 3L1 9l11 6 9-4.91V17h2V9L12 3zm0 13L3.74 11.5 12 7l8.26 4.5L12 16z",
        "help_text": "Chức năng đang chờ tích hợp.",
    },
)

# Định nghĩa sidebar theo nghiệp vụ; active_namespaces giúp giữ active ở trang con.
SIDEBAR_MENU_DEFINITIONS = (
    {
        "label": "Văn bản đến",
        "url_name": "quanlyvanbanden:danh_sach",
        "active_namespaces": ("quanlyvanbanden",),
        "roles": ALL_ROLES,
        "icon_path": "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zm-1 1.5L18.5 9H13zM12 12v4l-3-3-1.4 1.4L13 19.8l5.4-5.4L17 13l-3 3v-4z",
        "help_text": "",
    },
    {
        "label": "Văn bản đi",
        "url_name": "quanlyvanbandi:van_ban_di",
        "active_namespaces": ("quanlyvanbandi",),
        "roles": ALL_ROLES,
        "icon_path": "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zm-1 1.5L18.5 9H13zM12 12V8l3 3 1.4-1.4L11 4.2 5.6 9.6 7 11l3-3v4z",
        "help_text": "",
    },
    {
        "label": "Quản lý công việc",
        "url_name": "quanlycongviec:giao_viec",
        "active_namespaces": ("quanlycongviec",),
        "roles": (Customer.Role.ADMIN, Customer.Role.LANH_DAO),
        "icon_path": "M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8zM4 8h16v10H4zm3 3h10v2H7zm0 4h7v2H7z",
        "help_text": "",
    },
    {
        "label": "Quản lý công việc",
        "url_name": "quanlycongviec:xu_ly_cong_viec",
        "active_namespaces": ("quanlycongviec",),
        "roles": (Customer.Role.CHUYEN_VIEN,),
        "icon_path": "M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8zM4 8h16v10H4zm3 3h10v2H7zm0 4h7v2H7z",
        "help_text": "",
    },
    {
        "label": "Quản lý hồ sơ",
        "url_name": "hosovanban:danh_sach",
        "active_namespaces": ("hosovanban",),
        "roles": ALL_ROLES,
        "icon_path": "M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z",
        "help_text": "",
    },
    {
        "label": "Báo cáo thống kê",
        "url_name": "core:bao_cao_thong_ke",
        "active_view_names": ("core:bao_cao_thong_ke",),
        "roles": ALL_ROLES,
        "icon_path": "M3 13h2v8H3v-8zm4-6h2v14H7V7zm4 3h2v11h-2V10zm4-7h2v18h-2V3zm4 10h2v8h-2v-8z",
        "help_text": "",
    },
)


def _resolve_url(url_name):
    # Reverse URL an toàn; nếu route chưa có thì trả về link tạm để layout không lỗi.
    if not url_name:
        return "#", False
    try:
        return reverse(url_name), True
    except NoReverseMatch:
        return "#", False


def _is_active(definition, current_namespace, current_view_name):
    # Xác định item menu đang active theo namespace hoặc view hiện tại.
    active_namespaces = definition.get("active_namespaces", ())
    if current_namespace in active_namespaces:
        return True
    for namespace in active_namespaces:
        if current_view_name.startswith(f"{namespace}:"):
            return True
    if current_view_name in definition.get("active_view_names", ()):
        return True
    return current_view_name == definition.get("url_name")


def _build_navigation_items(request, definitions):
    # Lọc menu theo role của user và gắn href/active cho template base.
    resolver_match = getattr(request, "resolver_match", None)
    current_namespace = getattr(resolver_match, "namespace", "") or ""
    current_view_name = getattr(resolver_match, "view_name", "") or ""
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
                "active": is_enabled and _is_active(definition, current_namespace, current_view_name),
            }
        )

    return items


def auth_shell(request):
    # Context processor được inject vào mọi template để render shell sau đăng nhập.
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
            "branch_name": getattr(user.chi_nhanh, "ten_chi_nhanh", "Chưa gán"),
            "department_name": getattr(user.phong_ban, "ten_phong_ban", "Chưa gán"),
        },
        "top_menu_items": _build_navigation_items(request, TOP_MENU_DEFINITIONS),
        "sidebar_menu_items": _build_navigation_items(request, SIDEBAR_MENU_DEFINITIONS),
    }
