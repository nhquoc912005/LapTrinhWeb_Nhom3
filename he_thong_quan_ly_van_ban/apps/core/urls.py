from django.urls import path

from .views import bao_cao_thong_ke, dashboard

app_name = "core"

urlpatterns = [
    path("dashboard/", dashboard, name="dashboard"),
    path("bao-cao-thong-ke.html", bao_cao_thong_ke, name="bao_cao_thong_ke"),
]
