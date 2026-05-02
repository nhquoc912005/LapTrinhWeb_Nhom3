# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db.models import Count

from apps.core.models import ChuKySo, LichSuKySo

from ._data_audit import configure_utf8_output, database_kind, safe_database_identity

User = get_user_model()


class Command(BaseCommand):
    help = "Check digital signature seed data."

    def handle(self, *args, **options):
        configure_utf8_output()
        db = safe_database_identity()

        self.stdout.write("=== Database hiện tại ===")
        self.stdout.write(f"Loại kết nối: {database_kind()}")
        self.stdout.write(f"Engine: {db['engine']}")
        self.stdout.write(f"Name: {db['name']}")
        self.stdout.write(f"Host: {db['host'] or '(không có)'}")
        self.stdout.write(f"User: {db['user'] or '(không có)'}")
        self.stdout.write("")

        total_signatures = ChuKySo.objects.count()
        total_history = LichSuKySo.objects.count()
        history_by_document = LichSuKySo.objects.filter(van_ban__isnull=False, cong_viec__isnull=True).count()
        history_by_task = LichSuKySo.objects.filter(van_ban__isnull=True, cong_viec__isnull=False).count()
        invalid_both = LichSuKySo.objects.filter(van_ban__isnull=False, cong_viec__isnull=False).count()
        invalid_none = LichSuKySo.objects.filter(van_ban__isnull=True, cong_viec__isnull=True).count()

        self.stdout.write("=== Tổng quan chữ ký số ===")
        self.stdout.write(f"ChuKySo: {total_signatures}")
        self.stdout.write(f"LichSuKySo: {total_history}")
        self.stdout.write(f"Lịch sử gắn VanBan: {history_by_document}")
        self.stdout.write(f"Lịch sử gắn CongViec: {history_by_task}")
        self.stdout.write("")

        self.stdout.write("=== Lịch sử ký theo role ===")
        rows = (
            LichSuKySo.objects
            .values("chu_ky_so__nguoi_dung__tai_khoan__role")
            .annotate(total=Count("pk"))
            .order_by("chu_ky_so__nguoi_dung__tai_khoan__role")
        )
        totals_by_role = {
            row["chu_ky_so__nguoi_dung__tai_khoan__role"] or "Không xác định": row["total"]
            for row in rows
        }
        for role in User.Role.values:
            self.stdout.write(f"{role}: {totals_by_role.get(role, 0)}")
        unknown_total = totals_by_role.get("Không xác định", 0)
        if unknown_total:
            self.stdout.write(f"Không xác định: {unknown_total}")
        self.stdout.write("")

        self.stdout.write("=== Kiểm tra constraint LichSuKySo ===")
        if invalid_both or invalid_none:
            self.stdout.write(
                self.style.WARNING(
                    f"Sai constraint: vừa VanBan vừa CongViec = {invalid_both}, cả hai null = {invalid_none}"
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("Không phát hiện bản ghi sai constraint."))
        self.stdout.write("")

        missing_signature_images = 0
        for signature in ChuKySo.objects.select_related("nguoi_dung"):
            if not signature.anh_chu_ky or not default_storage.exists(signature.anh_chu_ky.name):
                missing_signature_images += 1

        missing_signed_files = 0
        for history in LichSuKySo.objects.all():
            if history.file_da_ky and not default_storage.exists(history.file_da_ky.name):
                missing_signed_files += 1

        self.stdout.write("=== Kiểm tra file media ===")
        if missing_signature_images:
            self.stdout.write(self.style.WARNING(f"ChuKySo thiếu ảnh hoặc file không tồn tại: {missing_signature_images}"))
        else:
            self.stdout.write(self.style.SUCCESS("Tất cả ChuKySo có ảnh chữ ký tồn tại trong media."))

        if missing_signed_files:
            self.stdout.write(self.style.WARNING(f"LichSuKySo có file_da_ky không tồn tại: {missing_signed_files}"))
        else:
            self.stdout.write(self.style.SUCCESS("Các file_da_ky đã khai báo đều tồn tại trong media."))
