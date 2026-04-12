from django.urls import path
from .views import danh_sach

app_name = "hosovanban"

urlpatterns = [
    path("ho-so-van-ban.html", danh_sach, name="danh_sach"),
]
