from django.urls import path

from .views import danh_sach


app_name = "hosovanban"

urlpatterns = [
    path("hosovanban/ho-so-van-ban.html", danh_sach, name="danh_sach"),
    path("hosovanban/them-ho-so-van-ban.html", them_ho_so_van_ban, name="them_ho_so_van_ban"),
    path("hosovanban/chi-tiet/<int:pk>/", chi_tiet_ho_so_van_ban, name="chi_tiet"),
    path("hosovanban/sua/<int:pk>/", sua_ho_so_van_ban, name="sua"),
    path("hosovanban/xoa/<int:pk>/", xoa_ho_so_van_ban, name="xoa"),
]
