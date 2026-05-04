from django.urls import path

from .views import login_view, logout_view, profile_view


app_name = "accounts"

# URL của app tài khoản: đăng nhập, thông tin cá nhân và đăng xuất.
urlpatterns = [
    # Màn đăng nhập ở route gốc của hệ thống.
    path("", login_view, name="login"),
    # Màn thông tin cá nhân sau khi đăng nhập.
    path("profile/", profile_view, name="profile"),
    # Route kết thúc phiên đăng nhập.
    path("logout/", logout_view, name="logout"),
]
