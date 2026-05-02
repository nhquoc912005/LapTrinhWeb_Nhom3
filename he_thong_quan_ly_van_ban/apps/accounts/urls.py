from django.urls import path

from .views import login_view, logout_view, profile_view


app_name = "accounts"

urlpatterns = [
    path("", login_view, name="login"),
    path("profile/", profile_view, name="profile"),
    path("logout/", logout_view, name="logout"),
]
