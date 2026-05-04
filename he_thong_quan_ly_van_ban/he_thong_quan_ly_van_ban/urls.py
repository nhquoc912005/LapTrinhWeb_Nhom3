from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


# File định tuyến cấp project, gom URL của từng app nghiệp vụ vào hệ thống.
urlpatterns = [
    # Trang quản trị Django mặc định.
    path("admin/", admin.site.urls),
    # URL tài khoản: đăng nhập, đăng xuất và thông tin cá nhân.
    path("", include(("apps.accounts.urls", "accounts"), namespace="accounts")),
    # URL lõi: dashboard, báo cáo thống kê và lịch sử hoạt động.
    path("", include(("apps.core.urls", "core"), namespace="core")),
    # Nhóm URL quản lý văn bản đến.
    path(
        "van-ban-den/",
        include(("apps.quanlyvanbanden.urls", "quanlyvanbanden"), namespace="quanlyvanbanden"),
    ),
    # Các app còn lại đang giữ route gốc theo URL hiện có của hệ thống.
    path("", include(("apps.quanlyvanbandi.urls", "quanlyvanbandi"), namespace="quanlyvanbandi")),
    path("", include(("apps.quanlycongviec.urls", "quanlycongviec"), namespace="quanlycongviec")),
    path("", include(("apps.hosovanban.urls", "hosovanban"), namespace="hosovanban")),
]

# Phục vụ file upload trong môi trường phát triển.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
