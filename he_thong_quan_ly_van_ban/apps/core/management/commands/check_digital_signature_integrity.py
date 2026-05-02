# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.models import LichSuKySo
from apps.core.utils.digital_signature import verify_signed_file

from ._data_audit import configure_utf8_output, database_kind


class Command(BaseCommand):
    help = "Verify SHA-256 integrity for all digital signature history records."

    def handle(self, *args, **options):
        configure_utf8_output()

        valid_count = 0
        changed_count = 0
        missing_file_count = 0
        missing_hash_count = 0

        histories = (
            LichSuKySo.objects
            .select_related("chu_ky_so__nguoi_dung", "van_ban", "cong_viec")
            .order_by("lich_su_ky_so_id")
        )

        with transaction.atomic():
            for history in histories:
                result = verify_signed_file(history)

                if not result.has_hash:
                    missing_hash_count += 1

                if result.file_missing:
                    missing_file_count += 1
                    continue

                if result.has_hash and result.verified:
                    valid_count += 1
                elif result.has_hash:
                    changed_count += 1

        self.stdout.write("=== Kiểm tra toàn vẹn chữ ký số ===")
        self.stdout.write(f"Database hiện tại: {database_kind()}")
        self.stdout.write(f"Tổng lịch sử ký số: {histories.count()}")
        self.stdout.write(f"Chữ ký hợp lệ: {valid_count}")
        self.stdout.write(f"Chữ ký bị thay đổi file: {changed_count}")
        self.stdout.write(f"Chữ ký thiếu file: {missing_file_count}")
        self.stdout.write(f"Chữ ký chưa có hash: {missing_hash_count}")

        if changed_count or missing_file_count or missing_hash_count:
            self.stdout.write(self.style.WARNING("Có chữ ký số cần kiểm tra lại."))
        else:
            self.stdout.write(self.style.SUCCESS("Tất cả chữ ký số còn nguyên vẹn."))
