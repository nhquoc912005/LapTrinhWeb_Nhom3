from django.urls import path

from .views import bao_cao_thong_ke, dashboard, lich_su_hoat_dong

app_name = "core"

# URL lõi: dashboard, báo cáo thống kê và lịch sử hoạt động.
urlpatterns = [
    # Màn tổng quan sau khi đăng nhập.
    path("dashboard/", dashboard, name="dashboard"),
    # Màn báo cáo thống kê văn bản/công việc.
    path("bao-cao-thong-ke.html", bao_cao_thong_ke, name="bao_cao_thong_ke"),
    # Màn xem audit log thao tác trong hệ thống.
    path("lich-su/", lich_su_hoat_dong, name="lich_su_hoat_dong"),
]
