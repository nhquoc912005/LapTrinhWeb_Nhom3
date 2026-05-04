from django.apps import AppConfig


# Cấu hình app core chứa model dùng chung và các màn dashboard/báo cáo.
class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
