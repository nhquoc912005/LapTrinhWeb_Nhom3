from django.contrib import admin
from .models import VanBanDen, TepVanBanDen


@admin.register(VanBanDen)
class VanBanDenAdmin(admin.ModelAdmin):
    list_display = ('id', 'so_ky_hieu', 'don_vi_ban_hanh', 'ngay_den', 'trang_thai')
    search_fields = ('so_ky_hieu', 'don_vi_ban_hanh', 'trich_yeu')
    list_filter = ('loai_van_ban', 'hinh_thuc_van_ban', 'do_mat', 'do_khan', 'trang_thai')


@admin.register(TepVanBanDen)
class TepVanBanDenAdmin(admin.ModelAdmin):
    list_display = ('id', 'van_ban_den', 'loai', 'ten_file', 'created_at')
    search_fields = ('van_ban_den__so_ky_hieu', 'tep')
    list_filter = ('loai', 'created_at')
