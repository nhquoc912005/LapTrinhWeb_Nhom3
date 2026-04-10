from django.urls import path

from .views import danh_sach


app_name = "quanlyvanbandi"

urlpatterns = [
    path("van-ban-di.html", danh_sach, name="danh_sach"),
]
