from django.urls import path

from .views import danh_sach


app_name = "quanlyvanbanden"

urlpatterns = [
    path("van-ban-den.html", danh_sach, name="danh_sach"),
]
