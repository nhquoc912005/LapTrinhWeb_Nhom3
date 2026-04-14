from django.urls import path
from . import views

app_name = "quanlyvanbandi"

urlpatterns = [
    path("van-ban-di/", views.van_ban_di, name="van_ban_di"),
    path("van-ban-di/them/", views.van_ban_di_edit, name="them_van_ban_di"),
    path("van-ban-di/<int:vb_pk>/sua/", views.van_ban_di_edit, name="sua_van_ban_di"),
    path("van-ban-di/<int:id>/", views.chi_tiet_van_ban_di, name="chi_tiet_van_ban_di"),

    path("van-ban-di/<int:vb_pk>/phe-duyet/", views.phe_duyet_van_ban_di, name="phe_duyet_van_ban_di"),
    path("van-ban-di/<int:vb_pk>/hoan-tra/", views.hoan_tra_van_ban_di, name="hoan_tra_van_ban_di"),
    path("van-ban-di/<int:vb_pk>/ban-hanh/", views.ban_hanh_van_ban, name="ban_hanh_van_ban"),
    path("van-ban-di/<int:vb_pk>/xoa/", views.xoa_van_ban_di, name="xoa_van_ban_di"),

    # AJAX APIs
    path("api/chi-nhanh-phong-ban/", views.api_chi_nhanh_phong_ban, name="api_chi_nhanh_phong_ban"),
    path("api/nhan-vien/", views.api_nhan_vien_phong_ban, name="api_nhan_vien_phong_ban"),
    path("api/don-vi-ngoai/", views.api_don_vi_ngoai, name="api_don_vi_ngoai"),
]