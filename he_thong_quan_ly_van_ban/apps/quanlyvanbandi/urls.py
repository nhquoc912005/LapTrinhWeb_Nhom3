from django.urls import path
from . import views

app_name = "quanlyvanbandi"

urlpatterns = [
    path("van-ban-di/", views.van_ban_di, name="van_ban_di"),
    path("van-ban-di/them/", views.van_ban_di_edit, name="them_van_ban_di"),
    path("van-ban-di/<int:vb_pk>/sua/", views.van_ban_di_edit, name="sua_van_ban_di"),
    path("van-ban-di/<int:id>/", views.chi_tiet_van_ban_di, name="chi_tiet_van_ban_di"),

    path("van-ban-di/<int:vb_pk>/phe-duyet/",views.phe_duyet_van_ban_di,name="phe_duyet_van_ban_di",),
    path("van-ban-di/<int:vb_pk>/hoan-tra/",views.hoan_tra_van_ban_di,name="hoan_tra_van_ban_di",),
]