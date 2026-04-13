from django.urls import path
from .views import danh_sach
from .views import them_ho_so_van_ban
from .views import chi_tiet_ho_so_van_ban
from .views import sua_ho_so_van_ban
from .views import xoa_ho_so_van_ban
from .views import chi_tiet_van_ban_trong_ho_so
from .views import xoa_van_ban_khoi_ho_so
app_name = "hosovanban"
urlpatterns = [
    path("hosovanban/ho-so-van-ban.html", danh_sach, name="danh_sach"),
    path("hosovanban/them-ho-so-van-ban.html", them_ho_so_van_ban, name="them_ho_so_van_ban"),
    path("hosovanban/chi-tiet/<int:pk>/", chi_tiet_ho_so_van_ban, name="chi_tiet"),
    path("hosovanban/sua/<int:pk>/", sua_ho_so_van_ban, name="sua"),
    path("hosovanban/xoa/<int:pk>/", xoa_ho_so_van_ban, name="xoa"),
    path("hosovanban/chi-tiet/<int:ho_so_id>/van-ban/<int:vb_id>/", chi_tiet_van_ban_trong_ho_so, name="chi_tiet_van_ban"),
    path("hosovanban/chi-tiet/<int:ho_so_id>/van-ban/<int:vb_id>/xoa/", xoa_van_ban_khoi_ho_so, name="xoa_van_ban_khoi_ho_so"),
]