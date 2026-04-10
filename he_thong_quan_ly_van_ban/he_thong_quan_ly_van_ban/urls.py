from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("apps.accounts.urls", "accounts"), namespace="accounts")),
    path("", include(("apps.core.urls", "core"), namespace="core")),
    path("", include(("apps.quanlyvanbanden.urls", "quanlyvanbanden"), namespace="quanlyvanbanden")),
    path("", include(("apps.quanlyvanbandi.urls", "quanlyvanbandi"), namespace="quanlyvanbandi")),
    path("", include(("apps.quanlycongviec.urls", "quanlycongviec"), namespace="quanlycongviec")),
    path("", include(("apps.hosovanban.urls", "hosovanban"), namespace="hosovanban")),
]
