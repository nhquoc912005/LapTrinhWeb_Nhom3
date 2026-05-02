from django.core.management.base import BaseCommand

from ._data_audit import (
    COUNT_MODELS,
    DOCUMENT_FIXTURE_MODELS,
    MEDIA_DIRECTORIES,
    configure_utf8_output,
    count_physical_files,
    fixture_model_counts,
    fixture_path,
    media_root,
    safe_count_model_records,
    safe_database_identity,
)


class Command(BaseCommand):
    help = "Kiểm tra database hiện tại, media vật lý và nội dung old_data.json."

    def handle(self, *args, **options):
        configure_utf8_output()
        db = safe_database_identity()

        self.stdout.write("=== Database hiện tại ===")
        self.stdout.write(f"Engine: {db['engine']}")
        self.stdout.write(f"Name: {db['name']}")
        self.stdout.write(f"Host: {db['host'] or '(không có)'}")
        self.stdout.write(f"User: {db['user'] or '(không có)'}")
        self.stdout.write(f"Loại kết nối: {db['kind']}")
        self.stdout.write("")

        self.stdout.write("=== Media vật lý ===")
        self.stdout.write(f"MEDIA_ROOT: {media_root()}")
        for label, relative_dir in MEDIA_DIRECTORIES:
            count = count_physical_files(relative_dir)
            self.stdout.write(f"{relative_dir}/ ({label}): {count} file")
        self.stdout.write("")

        self.stdout.write("=== Record trong database ===")
        for model_label in COUNT_MODELS:
            count = safe_count_model_records(model_label)
            self.stdout.write(f"{model_label}: {count}")
        self.stdout.write("")

        self.stdout.write("=== old_data.json ===")
        path = fixture_path()
        self.stdout.write(f"Đường dẫn: {path}")
        if not path.exists():
            self.stdout.write("Không tìm thấy old_data.json.")
            return

        counts = fixture_model_counts(path)
        total = sum(counts.values())
        self.stdout.write(f"Tổng object: {total}")
        self.stdout.write("Các model có trong fixture:")
        for model_label, count in sorted(counts.items()):
            self.stdout.write(f" - {model_label}: {count}")

        self.stdout.write("Kiểm tra model văn bản/file cần có:")
        missing_models = []
        for model_label in DOCUMENT_FIXTURE_MODELS:
            count = counts.get(model_label, 0)
            if count == 0:
                missing_models.append(model_label)
            self.stdout.write(f" - {model_label}: {count}")

        if missing_models:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    "old_data.json đang thiếu dữ liệu văn bản/file/công việc. "
                    "Nếu import fixture này thì Supabase vẫn sẽ không có record để UI hiển thị file media."
                )
            )
