from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Customer


# File này tự đồng bộ quyền và hồ sơ core khi tài khoản Customer được lưu.


@receiver(post_save, sender=Customer)
def sync_customer_core_profile(sender, instance, raw, **kwargs):
    # Bỏ qua dữ liệu fixture/raw để tránh chạy đồng bộ khi import dữ liệu thô.
    if raw:
        return
    # Cần kiểm tra thêm khi chạy thực tế nếu signal tạo vòng lặp save ngoài ý muốn.
    instance.sync_access_context()
