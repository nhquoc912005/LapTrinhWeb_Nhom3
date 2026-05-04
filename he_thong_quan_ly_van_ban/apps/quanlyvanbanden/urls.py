from django.urls import path
from . import views

app_name = 'quanlyvanbanden'

# URL văn bản đến: danh sách, thêm/sửa/xóa, chi tiết và thao tác lãnh đạo.
urlpatterns = [
    # ===== DÙNG CHUNG =====
    path('', views.danh_sach_van_ban_den, name='danh_sach'),
    path('them/', views.them_van_ban_den, name='them'),
    path('<int:pk>/', views.chi_tiet_van_ban_den, name='chi_tiet'),
    path('<int:pk>/sua/', views.sua_van_ban_den, name='sua'),
    path('<int:pk>/xoa/', views.xoa_van_ban_den, name='xoa'),

    # ===== LÃNH ĐẠO =====
    # Nút Lưu -> trạng thái Xem để biết
    path('<int:pk>/luu/', views.lanh_dao_luu_van_ban_den, name='lanh_dao_luu'),
    
    # API Ký số
    path('<int:vb_pk>/ky-so/', views.api_ky_so_van_ban, name='api_ky_so_van_ban'),

    # Nút Chuyển tiếp -> chọn danh sách chuyên viên
    path('<int:pk>/chuyen-tiep/', views.lanh_dao_chuyen_tiep_van_ban_den, name='lanh_dao_chuyen_tiep'),

    # Nút Hoàn trả -> nhập lý do hoàn trả
    path('<int:pk>/hoan-tra/', views.lanh_dao_hoan_tra_van_ban_den, name='lanh_dao_hoan_tra'),

    # ===== TƯƠNG THÍCH CODE CŨ =====
    # Nếu template cũ còn đang gọi route phe-duyet thì vẫn chạy bình thường
    path('<int:pk>/phe-duyet/', views.lanh_dao_luu_van_ban_den, name='lanh_dao_phe_duyet'),
]
