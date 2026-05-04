import hashlib
from dataclasses import dataclass
from pathlib import Path

from django.core.files.storage import default_storage


# File này hỗ trợ tính hash và kiểm tra toàn vẹn file đã ký số.

HASH_ALGORITHM = "SHA-256"
HASH_CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class SignatureVerificationResult:
    # Kết quả kiểm tra chữ ký số trả về cho profile và các màn chi tiết.
    has_hash: bool
    file_missing: bool
    verified: bool
    expected_hash: str
    current_hash: str
    file_name: str
    message: str


def _file_name(file_value):
    if not file_value:
        return ""
    return getattr(file_value, "name", None) or str(file_value)


def _has_file(file_value):
    return bool(_file_name(file_value))


def _storage_for(file_value):
    return getattr(file_value, "storage", default_storage)


def calculate_file_sha256(file_path):
    # Tính SHA-256 cho file vật lý hoặc file lưu qua Django storage.
    name = _file_name(file_path)
    if not name:
        raise FileNotFoundError("Missing file path")

    path = Path(name)
    sha256 = hashlib.sha256()

    if path.is_absolute():
        if not path.exists():
            raise FileNotFoundError(name)
        with path.open("rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(HASH_CHUNK_SIZE), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    storage = _storage_for(file_path)
    if not storage.exists(name):
        raise FileNotFoundError(name)

    with storage.open(name, "rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(HASH_CHUNK_SIZE), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_signed_object_file_path(obj):
    # Tìm file nguồn cần kiểm tra từ lịch sử ký, văn bản, công việc hoặc file liên quan.
    from apps.core.models import CongViec, FileCVLienQuan, LichSuKySo, VanBan, VanBanLienQuan

    if obj is None:
        return None

    if isinstance(obj, LichSuKySo):
        target = obj.van_ban or obj.cong_viec
        return get_signed_object_file_path(target)

    if isinstance(obj, VanBan):
        if _has_file(obj.file_dinh_kem):
            return obj.file_dinh_kem
        related_file = (
            VanBanLienQuan.objects
            .filter(van_ban=obj)
            .order_by("van_ban_lien_quan_id")
            .first()
        )
        if related_file and _has_file(related_file.file_van_ban):
            return related_file.file_van_ban
        return None

    if isinstance(obj, CongViec):
        task_files = FileCVLienQuan.objects.filter(cong_viec=obj)
        task_file = (
            task_files.filter(nguon_tai_len=FileCVLienQuan.NguonTaiLen.KET_QUA_XU_LY)
            .order_by("file_cv_lien_quan_id")
            .first()
            or task_files.filter(loai_file=FileCVLienQuan.LoaiFile.CHINH)
            .order_by("file_cv_lien_quan_id")
            .first()
            or task_files.order_by("file_cv_lien_quan_id").first()
        )
        if task_file and _has_file(task_file.file_van_ban):
            return task_file.file_van_ban
        if obj.van_ban_id:
            return get_signed_object_file_path(obj.van_ban)
        if obj.van_ban_den_id:
            return get_signed_object_file_path(obj.van_ban_den)
        return None

    if isinstance(obj, FileCVLienQuan):
        return obj.file_van_ban if _has_file(obj.file_van_ban) else None

    if isinstance(obj, VanBanLienQuan):
        return obj.file_van_ban if _has_file(obj.file_van_ban) else None

    for attr_name in ("file_dinh_kem", "file_van_ban", "tep", "file_da_ky"):
        file_value = getattr(obj, attr_name, None)
        if _has_file(file_value):
            return file_value

    return None


def verify_signed_file(lich_su_ky_so, *, persist=True):
    # So sánh hash hiện tại với hash đã lưu và cập nhật cờ verified nếu cần.
    expected_hash = (lich_su_ky_so.file_hash or "").strip().lower()
    source_file = get_signed_object_file_path(lich_su_ky_so)
    file_name = _file_name(source_file)
    current_hash = ""
    file_missing = False

    if source_file:
        try:
            current_hash = calculate_file_sha256(source_file)
        except FileNotFoundError:
            file_missing = True
    else:
        file_missing = True

    if not expected_hash:
        verified = False
        message = "Chữ ký chưa có hash SHA-256"
    elif file_missing:
        verified = False
        message = "Thiếu tệp nguồn để kiểm tra"
    elif current_hash == expected_hash:
        verified = True
        message = "Tệp còn nguyên vẹn"
    else:
        verified = False
        message = "Tệp đã bị thay đổi sau khi ký"

    if persist and lich_su_ky_so.pk and lich_su_ky_so.verified != verified:
        lich_su_ky_so.verified = verified
        lich_su_ky_so.save(update_fields=["verified"])

    return SignatureVerificationResult(
        has_hash=bool(expected_hash),
        file_missing=file_missing,
        verified=verified,
        expected_hash=expected_hash,
        current_hash=current_hash,
        file_name=file_name,
        message=message,
    )
