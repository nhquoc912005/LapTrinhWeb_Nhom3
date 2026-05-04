import json
import sys
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.apps import apps
from django.db import connection
from django.db.utils import DatabaseError, OperationalError, ProgrammingError


# File tiện ích dùng chung cho các command kiểm tra dữ liệu seed/database.


MEDIA_DIRECTORIES = (
    ("core.VanBan.file_dinh_kem", "van_ban"),
    ("core.VanBanLienQuan.file_van_ban", "van_ban_lien_quan"),
    ("core.FileCVLienQuan.file_van_ban", "file_cv_lien_quan"),
    ("quanlyvanbanden.TepVanBanDen.tep", "van_ban_den/tep_tin"),
)

COUNT_MODELS = (
    "accounts.Customer",
    "core.NguoiDung",
    "core.VanBan",
    "core.VanBanLienQuan",
    "core.CongViec",
    "core.FileCVLienQuan",
    "core.HoSoVanBan",
    "quanlyvanbanden.VanBanDen",
    "quanlyvanbanden.TepVanBanDen",
)

DOCUMENT_FIXTURE_MODELS = (
    "core.vanban",
    "core.vanbanlienquan",
    "core.congviec",
    "core.filecvlienquan",
    "quanlyvanbanden.vanbanden",
    "quanlyvanbanden.tepvanbanden",
)


def configure_utf8_output():
    # Đảm bảo console Windows in tiếng Việt ổn định khi chạy command.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def database_settings():
    # Lấy cấu hình database mặc định từ Django connection.
    return connection.settings_dict


def database_kind():
    # Xác định loại database hiện tại để command in cảnh báo phù hợp.
    engine = str(database_settings().get("ENGINE", "")).lower()
    if "sqlite" in engine:
        return "SQLite"
    if "postgresql" in engine or "postgres" in engine:
        return "PostgreSQL/Supabase"
    return "Khác"


def is_sqlite_database():
    return database_kind() == "SQLite"


def safe_database_identity():
    db = database_settings()
    return {
        "engine": db.get("ENGINE") or "",
        "name": db.get("NAME") or "",
        "host": db.get("HOST") or "",
        "user": db.get("USER") or "",
        "kind": database_kind(),
    }


def media_root():
    return Path(settings.MEDIA_ROOT)


def count_physical_files(relative_dir):
    directory = media_root() / relative_dir
    if not directory.exists():
        return 0
    return sum(1 for path in directory.rglob("*") if path.is_file())


def iter_media_files(relative_dir):
    directory = media_root() / relative_dir
    if not directory.exists():
        return []

    result = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        relative_name = path.relative_to(media_root()).as_posix()
        result.append((relative_name, path))
    return result


def count_model_records(model_label):
    app_label, model_name = model_label.split(".", 1)
    model = apps.get_model(app_label, model_name)
    return model.objects.count()


def safe_count_model_records(model_label):
    try:
        return count_model_records(model_label)
    except (DatabaseError, OperationalError, ProgrammingError) as exc:
        return f"Lỗi: {exc.__class__.__name__}: {exc}"


def fixture_path():
    return Path(settings.BASE_DIR) / "old_data.json"


def fixture_model_counts(path=None):
    path = Path(path or fixture_path())
    if not path.exists():
        return None

    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = [data]

    counter = Counter()
    for item in data:
        if isinstance(item, dict) and item.get("model"):
            counter[item["model"].lower()] += 1

    return counter
