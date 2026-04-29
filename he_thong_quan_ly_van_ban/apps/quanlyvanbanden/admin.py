from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from apps.core.models import VanBan, VanBanLienQuan


class VanBanDenAdmin(admin.ModelAdmin):
    list_display = (
        'van_ban_id',
        'so_ky_hieu',
        'don_vi_ban_hanh',
        'ngay_den',
        'han_xu_ly',
        'trang_thai',
    )
    search_fields = (
        'so_ky_hieu',
        'don_vi_ban_hanh',
        'trich_yeu',
    )
    list_filter = (
        'loai_van_ban',
        'hinh_thuc',
        'do_mat',
        'do_khan',
        'trang_thai',
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(phan_loai='Văn bản đến')


class VanBanLienQuanAdmin(admin.ModelAdmin):
    list_display = (
        'van_ban_lien_quan_id',
        'van_ban',
        'file_van_ban',
        'kich_thuoc',
    )
    search_fields = (
        'van_ban__so_ky_hieu',
        'file_van_ban',
    )


# Nếu core/admin.py đã đăng ký VanBan rồi thì bỏ qua để tránh lỗi AlreadyRegistered
try:
    admin.site.register(VanBan, VanBanDenAdmin)
except AlreadyRegistered:
    pass

try:
    admin.site.register(VanBanLienQuan, VanBanLienQuanAdmin)
except AlreadyRegistered:
    pass