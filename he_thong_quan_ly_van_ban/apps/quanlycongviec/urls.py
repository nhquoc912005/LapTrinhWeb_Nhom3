from django.urls import path

from .views import giao_viec, xu_ly_cong_viec


app_name = "quanlycongviec"

urlpatterns = [
    path("giao-viec.html", giao_viec, name="giao_viec"),
    path("xu-ly-cong-viec.html", xu_ly_cong_viec, name="xu_ly_cong_viec"),
]
