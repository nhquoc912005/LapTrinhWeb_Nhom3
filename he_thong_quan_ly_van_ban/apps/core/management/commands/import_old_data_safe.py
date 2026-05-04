from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from ._data_audit import (
    COUNT_MODELS,
    configure_utf8_output,
    fixture_path,
    is_sqlite_database,
    safe_count_model_records,
    safe_database_identity,
)


# Command import dữ liệu cũ theo hướng an toàn, tránh ghi đè dữ liệu đang có.
class Command(BaseCommand):
    help = "Import old_data.json vào PostgreSQL/Supabase hiện tại, không cho import nhầm vào SQLite."

    def handle(self, *args, **options):
        configure_utf8_output()
        db = safe_database_identity()
        self.stdout.write("=== Database đích ===")
        self.stdout.write(f"Engine: {db['engine']}")
        self.stdout.write(f"Name: {db['name']}")
        self.stdout.write(f"Host: {db['host'] or '(không có)'}")
        self.stdout.write(f"User: {db['user'] or '(không có)'}")
        self.stdout.write(f"Loại kết nối: {db['kind']}")
        self.stdout.write("")

        if is_sqlite_database():
            raise CommandError("Bạn đang import vào SQLite, không phải Supabase")

        path = fixture_path()
        if not path.exists():
            raise CommandError(f"Không tìm thấy fixture: {path}")

        self.stdout.write("Bắt đầu import old_data.json...")
        call_command("loaddata", "old_data.json")
        self.stdout.write(self.style.SUCCESS("Import old_data.json hoàn tất."))
        self.stdout.write("")

        self.stdout.write("=== Record sau import ===")
        for model_label in COUNT_MODELS:
            if model_label in {
                "accounts.Customer",
                "core.NguoiDung",
                "core.HoSoVanBan",
                "core.VanBan",
                "core.VanBanLienQuan",
                "core.CongViec",
                "core.FileCVLienQuan",
                "quanlyvanbanden.VanBanDen",
                "quanlyvanbanden.TepVanBanDen",
            }:
                self.stdout.write(f"{model_label}: {safe_count_model_records(model_label)}")
