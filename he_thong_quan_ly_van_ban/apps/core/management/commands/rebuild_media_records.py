import hashlib
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.core.models import (
    ChiNhanh,
    ChuyenTiep,
    ChuyenTiepChiTiet,
    CongViec,
    FileCVLienQuan,
    HoSoVanBan,
    NguoiDung,
    NguoiXuLyHoSo,
    PhongBan,
    PhongXemHoSo,
    VanBan,
    VanBanDuyet,
    VanBanLienQuan,
)
from apps.quanlyvanbanden.models import TepVanBanDen, VanBanDen

from ._data_audit import (
    COUNT_MODELS,
    configure_utf8_output,
    iter_media_files,
    safe_count_model_records,
)


class Command(BaseCommand):
    help = "Tạo lại record tối thiểu từ các file vật lý trong media để UI hiển thị được."

    def handle(self, *args, **options):
        configure_utf8_output()
        self.stdout.write("Không xóa file media, không reset database, không xóa user hiện có.")

        with transaction.atomic():
            context = self._ensure_base_context()
            stats = {
                "core_van_ban": 0,
                "core_van_ban_lien_quan": 0,
                "core_cong_viec": 0,
                "core_file_cv_lien_quan": 0,
                "legacy_van_ban_den": 0,
                "legacy_tep_van_ban_den": 0,
            }

            main_documents = self._rebuild_outgoing_documents(context, stats)
            incoming_documents = self._rebuild_incoming_documents(context, stats)

            anchor_document = (
                main_documents[0]
                if main_documents
                else incoming_documents[0]
                if incoming_documents
                else VanBan.objects.order_by("van_ban_id").first()
            )
            self._rebuild_related_documents(context, anchor_document, stats)
            self._rebuild_task_files(context, anchor_document, stats)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Rebuild media records hoàn tất."))
        self.stdout.write("=== Số record đã tạo mới ===")
        for key, value in stats.items():
            self.stdout.write(f"{key}: {value}")

        self.stdout.write("")
        self.stdout.write("=== Record hiện tại ===")
        for model_label in COUNT_MODELS:
            self.stdout.write(f"{model_label}: {safe_count_model_records(model_label)}")

    def _ensure_base_context(self):
        branch = ChiNhanh.objects.order_by("chi_nhanh_id").first()
        if not branch:
            branch = ChiNhanh.objects.create(ten_chi_nhanh="Auto media branch")

        departments = {
            "van_thu": self._ensure_department(branch, "Phong hanh chinh"),
            "lanh_dao": self._ensure_department(branch, "Ban giam doc"),
            "chuyen_vien": self._ensure_department(branch, "Phong chuyen mon"),
        }

        users = {
            "van_thu": self._ensure_user("VAN_THU", "vanthu", departments["van_thu"]),
            "lanh_dao": self._ensure_user("LANH_DAO", "lanhdao", departments["lanh_dao"]),
            "chuyen_vien": self._ensure_user("CHUYEN_VIEN", "chuyenvien", departments["chuyen_vien"]),
        }

        profiles = {
            name: self._ensure_core_profile(user, departments[name])
            for name, user in users.items()
        }

        record = self._ensure_record(profiles, departments)

        return {
            "branch": branch,
            "departments": departments,
            "users": users,
            "profiles": profiles,
            "record": record,
        }

    def _ensure_department(self, branch, name):
        existing = PhongBan.objects.filter(ten_phong_ban__iexact=name).first()
        if existing:
            return existing
        return PhongBan.objects.create(chi_nhanh=branch, ten_phong_ban=name)

    def _ensure_user(self, role, username, department):
        User = get_user_model()
        user = User.objects.filter(username=username, role=role).first()
        if not user:
            user = User.objects.filter(role=role).order_by("id").first()
        if user:
            update_fields = []
            if not user.phong_ban_id:
                user.phong_ban = department
                update_fields.append("phong_ban")
            if not user.chi_nhanh_id:
                user.chi_nhanh = department.chi_nhanh
                update_fields.append("chi_nhanh")
            if update_fields:
                user.save(update_fields=update_fields)
            return user

        user = User(
            username=username,
            email=f"{username}@local.invalid",
            ho_va_ten=username.replace("_", " ").title(),
            role=role,
            phong_ban=department,
            chi_nhanh=department.chi_nhanh,
            is_active=True,
        )
        user.set_unusable_password()
        user.save()
        return user

    def _ensure_core_profile(self, user, department):
        profile = user.sync_access_context()
        if not profile.phong_ban_id:
            profile.phong_ban = department
            profile.save(update_fields=["phong_ban"])
        return profile

    def _ensure_record(self, profiles, departments):
        record, _ = HoSoVanBan.objects.get_or_create(
            ky_hieu_ho_so="AUTO-MEDIA-HS-001",
            defaults={
                "tieu_de_ho_so": "Ho so khoi phuc tu media",
                "nguoi_tao": profiles["van_thu"],
                "thoi_gian_bao_quan": HoSoVanBan.THOI_GIAN_BAO_QUAN_CHOICES[1][0],
                "so_nam_luu_tru": 5,
                "trang_thai": 1,
                "mo_ta": "Ho so toi thieu duoc tao tu rebuild_media_records.",
            },
        )
        if record.nguoi_tao_id != profiles["van_thu"].pk:
            record.nguoi_tao = profiles["van_thu"]
            record.save(update_fields=["nguoi_tao"])

        for profile in profiles.values():
            NguoiXuLyHoSo.objects.get_or_create(
                ho_so_van_ban=record,
                nguoi_xu_ly=profile,
            )
            if profile.phong_ban_id:
                PhongXemHoSo.objects.get_or_create(
                    ho_so_van_ban=record,
                    phong_ban=profile.phong_ban,
                )

        for department in departments.values():
            PhongXemHoSo.objects.get_or_create(
                ho_so_van_ban=record,
                phong_ban=department,
            )

        return record

    def _rebuild_outgoing_documents(self, context, stats):
        documents = []
        for relative_path, path in iter_media_files("van_ban"):
            document, created = self._ensure_core_document(
                relative_path=relative_path,
                path=path,
                context=context,
                phan_loai=VanBan.PHAN_LOAI_CHOICES[0][0],
                trang_thai=VanBan.TRANG_THAI_CHOICES[4][0],
                code_prefix="AUTO-VBDI",
                creator=context["profiles"]["chuyen_vien"],
                leader=context["profiles"]["lanh_dao"],
            )
            documents.append(document)
            if created:
                stats["core_van_ban"] += 1
            self._ensure_van_ban_duyet(document, context["profiles"]["van_thu"])
        return documents

    def _rebuild_incoming_documents(self, context, stats):
        documents = []
        for relative_path, path in iter_media_files("van_ban_den/tep_tin"):
            document, created = self._ensure_core_document(
                relative_path=relative_path,
                path=path,
                context=context,
                phan_loai=VanBan.PHAN_LOAI_CHOICES[1][0],
                trang_thai=VanBan.TRANG_THAI_CHOICES[1][0],
                code_prefix="AUTO-VBDEN",
                creator=context["profiles"]["van_thu"],
                leader=context["profiles"]["lanh_dao"],
            )
            documents.append(document)
            if created:
                stats["core_van_ban"] += 1
            self._ensure_incoming_forward(document, context)

            legacy_document, legacy_created = self._ensure_legacy_incoming_document(
                relative_path,
                path,
                context,
            )
            if legacy_created:
                stats["legacy_van_ban_den"] += 1

            _, file_created = TepVanBanDen.objects.get_or_create(
                tep=relative_path,
                defaults={
                    "van_ban_den": legacy_document,
                    "loai": TepVanBanDen.LoaiTep.DINH_KEM,
                },
            )
            if file_created:
                stats["legacy_tep_van_ban_den"] += 1

        return documents

    def _rebuild_related_documents(self, context, anchor_document, stats):
        for relative_path, path in iter_media_files("van_ban_lien_quan"):
            if not anchor_document:
                anchor_document, created = self._ensure_core_document(
                    relative_path=relative_path,
                    path=path,
                    context=context,
                    phan_loai=VanBan.PHAN_LOAI_CHOICES[0][0],
                    trang_thai=VanBan.TRANG_THAI_CHOICES[4][0],
                    code_prefix="AUTO-VB-LQ",
                    creator=context["profiles"]["chuyen_vien"],
                    leader=context["profiles"]["lanh_dao"],
                )
                if created:
                    stats["core_van_ban"] += 1

            _, created = VanBanLienQuan.objects.get_or_create(
                file_van_ban=relative_path,
                defaults={
                    "van_ban": anchor_document,
                    "kich_thuoc": self._file_size(relative_path, path),
                },
            )
            if created:
                stats["core_van_ban_lien_quan"] += 1

    def _rebuild_task_files(self, context, anchor_document, stats):
        task, created = CongViec.objects.get_or_create(
            ten_cong_viec="AUTO-MEDIA: Khoi phuc file cong viec",
            defaults={
                "van_ban": anchor_document,
                "ten_cong_viec": "AUTO-MEDIA: Khoi phuc file cong viec",
                "noi_dung_cong_viec": "Cong viec toi thieu duoc tao tu rebuild_media_records.",
                "nguon_giao": CongViec.NguonGiao.VAN_BAN_DI,
                "trang_thai": CongViec.TrangThai.CHO_XU_LY,
                "ngay_bat_dau": timezone.localdate(),
                "han_xu_ly": timezone.now() + timedelta(days=7),
                "nguoi_giao": context["profiles"]["lanh_dao"],
                "nguoi_thuc_hien": context["profiles"]["chuyen_vien"],
                "ghi_chu": "AUTO_MEDIA_REBUILD",
            },
        )
        if created:
            stats["core_cong_viec"] += 1
        else:
            update_fields = []
            if anchor_document and task.van_ban_id != anchor_document.pk:
                task.van_ban = anchor_document
                update_fields.append("van_ban")
            if task.nguoi_giao_id != context["profiles"]["lanh_dao"].pk:
                task.nguoi_giao = context["profiles"]["lanh_dao"]
                update_fields.append("nguoi_giao")
            if task.nguoi_thuc_hien_id != context["profiles"]["chuyen_vien"].pk:
                task.nguoi_thuc_hien = context["profiles"]["chuyen_vien"]
                update_fields.append("nguoi_thuc_hien")
            if update_fields:
                task.save(update_fields=[*update_fields, "last_activity"])

        for relative_path, path in iter_media_files("file_cv_lien_quan"):
            _, file_created = FileCVLienQuan.objects.get_or_create(
                file_van_ban=relative_path,
                defaults={
                    "cong_viec": task,
                    "kich_thuoc": self._file_size(relative_path, path),
                    "loai_file": FileCVLienQuan.LoaiFile.LIEN_QUAN,
                    "nguon_tai_len": FileCVLienQuan.NguonTaiLen.GIAO_VIEC,
                    "nguoi_tai_len": context["profiles"]["lanh_dao"],
                },
            )
            if file_created:
                stats["core_file_cv_lien_quan"] += 1

    def _ensure_core_document(
        self,
        *,
        relative_path,
        path,
        context,
        phan_loai,
        trang_thai,
        code_prefix,
        creator,
        leader,
    ):
        self._assert_relative_file_exists(relative_path, path)

        existing = VanBan.objects.filter(file_dinh_kem=relative_path).first()
        if existing:
            self._sync_auto_core_document(
                existing,
                context=context,
                phan_loai=phan_loai,
                trang_thai=trang_thai,
                creator=creator,
                leader=leader,
            )
            return existing, False

        today = timezone.localdate()
        document = VanBan.objects.create(
            lanh_dao_duyet=leader,
            nguoi_tao=creator,
            ho_so_van_ban=context["record"],
            so_ky_hieu=self._code(code_prefix, relative_path),
            trich_yeu=self._short_text(f"Khoi phuc file {path.name}", 255),
            hinh_thuc=VanBan.HINH_THUC_CHOICES[0][0],
            loai_van_ban=VanBan.LOAI_VAN_BAN_CHOICES[0][0],
            don_vi_ban_hanh="Khoi phuc tu media",
            ngay_van_ban=today,
            ngay_den=today,
            han_xu_ly=today + timedelta(days=7),
            do_khan=VanBan.DO_KHAN_CHOICES[2][0],
            do_mat=VanBan.DO_MAT_CHOICES[0][0],
            file_dinh_kem=relative_path,
            kich_thuoc=self._file_size(relative_path, path),
            trang_thai=trang_thai,
            noi_dung="Record toi thieu duoc tao tu rebuild_media_records.",
            phan_loai=phan_loai,
        )
        return document, True

    def _ensure_legacy_incoming_document(self, relative_path, path, context):
        code = self._unique_legacy_code("AUTO-LEG-VBDEN", relative_path)
        existing = TepVanBanDen.objects.filter(tep=relative_path).select_related("van_ban_den").first()
        if existing:
            self._sync_auto_legacy_document(existing.van_ban_den, context)
            return existing.van_ban_den, False

        document, created = VanBanDen.objects.get_or_create(
            so_ky_hieu=code,
            defaults={
                "don_vi_ban_hanh": "Khoi phuc tu media",
                "trich_yeu": self._short_text(f"Khoi phuc file {path.name}", 500),
                "loai_van_ban": VanBanDen.LoaiVanBan.HANH_CHINH,
                "hinh_thuc_van_ban": VanBanDen.HinhThucVanBan.CONG_VAN,
                "ngay_van_ban": timezone.localdate(),
                "ngay_den": timezone.localdate(),
                "han_xu_ly": timezone.localdate() + timedelta(days=7),
                "do_mat": VanBanDen.DoMat.BINH_THUONG,
                "do_khan": VanBanDen.DoKhan.BINH_THUONG,
                "linh_vuc": "Khoi phuc tu media",
                "noi_dung_xu_ly": "Record toi thieu duoc tao tu rebuild_media_records.",
                "trang_thai": VanBanDen.TrangThai.CHO_XU_LY,
                "lanh_dao_xu_ly": context["users"]["lanh_dao"],
                "nguoi_tao": context["users"]["van_thu"],
            },
        )
        if not created:
            self._sync_auto_legacy_document(document, context)
        return document, created

    def _ensure_van_ban_duyet(self, document, van_thu):
        approval, created = VanBanDuyet.objects.get_or_create(
            van_ban=document,
            defaults={"van_thu": van_thu},
        )
        if not created and self._is_auto_core_document(document) and approval.van_thu_id != van_thu.pk:
            approval.van_thu = van_thu
            approval.save(update_fields=["van_thu"])

    def _ensure_incoming_forward(self, document, context):
        approved = VanBanDuyet.objects.filter(van_ban=document).first()
        if not approved:
            approved = VanBanDuyet.objects.create(
                van_ban=document,
                van_thu=context["profiles"]["van_thu"],
            )

        forwarding = ChuyenTiep.objects.filter(van_ban_duyet=approved).first()
        if not forwarding:
            forwarding = ChuyenTiep.objects.create(van_ban_duyet=approved)

        specialist = context["profiles"]["chuyen_vien"]
        department = specialist.phong_ban or context["departments"]["chuyen_vien"]
        ChuyenTiepChiTiet.objects.get_or_create(
            chuyen_tiep=forwarding,
            nguoi_dung=specialist,
            defaults={"phong_ban": department},
        )

    def _assert_relative_file_exists(self, relative_path, path):
        if path.exists() or default_storage.exists(relative_path):
            return
        raise CommandError(f"Không tìm thấy file vật lý cho đường dẫn tương đối: {relative_path}")

    def _file_size(self, relative_path, path):
        if path.exists():
            return path.stat().st_size
        try:
            return default_storage.size(relative_path)
        except Exception:
            return 0

    def _code(self, prefix, relative_path):
        digest = hashlib.sha1(relative_path.encode("utf-8")).hexdigest()[:10].upper()
        return f"{prefix}-{digest}"

    def _unique_legacy_code(self, prefix, relative_path):
        base = self._code(prefix, relative_path)[:90]
        code = base
        index = 1
        while VanBanDen.objects.filter(so_ky_hieu=code).exists():
            code = f"{base[:85]}-{index}"
            index += 1
        return code

    def _short_text(self, text, max_length):
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def _sync_auto_core_document(self, document, *, context, phan_loai, trang_thai, creator, leader):
        if not self._is_auto_core_document(document):
            return

        update_fields = []
        expected = {
            "nguoi_tao": creator,
            "lanh_dao_duyet": leader,
            "ho_so_van_ban": context["record"],
            "phan_loai": phan_loai,
            "trang_thai": trang_thai,
        }
        for field_name, value in expected.items():
            current_id = getattr(document, f"{field_name}_id", None)
            value_id = getattr(value, "pk", None)
            if value_id is not None:
                if current_id == value_id:
                    continue
                setattr(document, field_name, value)
                update_fields.append(field_name)
            elif getattr(document, field_name) != value:
                setattr(document, field_name, value)
                update_fields.append(field_name)

        if update_fields:
            document.save(update_fields=update_fields)

    def _sync_auto_legacy_document(self, document, context):
        if not str(document.so_ky_hieu).startswith("AUTO-"):
            return

        update_fields = []
        if document.lanh_dao_xu_ly_id != context["users"]["lanh_dao"].pk:
            document.lanh_dao_xu_ly = context["users"]["lanh_dao"]
            update_fields.append("lanh_dao_xu_ly")
        if document.nguoi_tao_id != context["users"]["van_thu"].pk:
            document.nguoi_tao = context["users"]["van_thu"]
            update_fields.append("nguoi_tao")

        if update_fields:
            document.save(update_fields=update_fields)

    def _is_auto_core_document(self, document):
        return str(document.so_ky_hieu).startswith("AUTO-")
