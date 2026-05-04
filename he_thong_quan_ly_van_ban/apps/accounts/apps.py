from django.apps import AppConfig

# Cấu hình app accounts, nơi quản lý tài khoản và phân quyền đăng nhập.
class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'

    def ready(self):
        # Nạp signal đồng bộ hồ sơ/quyền khi Customer được lưu.
        from . import signals  # noqa: F401
