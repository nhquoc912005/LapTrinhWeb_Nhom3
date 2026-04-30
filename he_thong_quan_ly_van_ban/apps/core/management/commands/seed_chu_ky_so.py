# -*- coding: utf-8 -*-
import os
from datetime import timedelta
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.core.models import (
    BanHanh,
    ChiNhanh,
    ChuKySo,
    ChuyenTiep,
    ChuyenTiepChiTiet,
    CongViec,
    FileCVLienQuan,
    HoSoVanBan,
    LichSuKySo,
    NguoiDung,
    NguoiXuLyHoSo,
    PheDuyetCongViec,
    PhanCongCongViec,
    PhongBan,
    PhongXemHoSo,
    VanBan,
    VanBanDuyet,
)
from apps.core.utils.digital_signature import (
    HASH_ALGORITHM,
    calculate_file_sha256,
    get_signed_object_file_path,
    verify_signed_file,
)

from ._data_audit import configure_utf8_output, database_kind


User = get_user_model()

ROLE_USER_SPECS = {
    User.Role.ADMIN: {
        "username": "admin.demo",
        "email": "admin.demo@role-seed.local",
        "name": "Quản trị Demo",
        "department": "Ban Giám Đốc",
        "title": "Quản trị hệ thống",
        "is_staff": True,
        "is_superuser": True,
    },
    User.Role.LANH_DAO: {
        "username": "lanhdao.demo",
        "email": "lanhdao.demo@role-seed.local",
        "name": "Lãnh đạo Demo",
        "department": "Ban Giám Đốc",
        "title": "Lãnh đạo Ban Giám Đốc",
    },
    User.Role.VAN_THU: {
        "username": "vanthu.demo",
        "email": "vanthu.demo@role-seed.local",
        "name": "Văn thư Demo",
        "department": "Phòng Hành Chính/Nhân sự",
        "title": "Văn thư hành chính",
    },
    User.Role.CHUYEN_VIEN: {
        "username": "chuyenvien.demo",
        "email": "chuyenvien.demo@role-seed.local",
        "name": "Chuyên viên Demo",
        "department": "Phòng Kế Toán",
        "title": "Chuyên viên xử lý nghiệp vụ",
    },
}


class Command(BaseCommand):
    help = "Seed digital signature data for each role."

    def add_arguments(self, parser):
        parser.add_argument(
            "--per-role",
            type=int,
            default=25,
            help="Number of signing history records per role.",
        )

    def handle(self, *args, **options):
        configure_utf8_output()
        per_role = max(1, options["per_role"])
        password = os.getenv("ROLE_SEED_PASSWORD")

        self.stdout.write(f"Database hiện tại: {database_kind()}")
        self.stdout.write(f"Seed chữ ký số với per-role={per_role}")
        self.stdout.write("Không xóa dữ liệu cũ, không reset database, không xóa user hiện có.")

        seeder = DigitalSignatureSeeder(self, per_role, password)
        with transaction.atomic():
            seeder.run()

        seeder.print_summary()


class DigitalSignatureSeeder:
    def __init__(self, command, per_role, password):
        self.command = command
        self.per_role = per_role
        self.password = password
        self.today = timezone.localdate()
        self.now = timezone.now()
        self.stats = {
            "users_created": 0,
            "core_profiles_synced": 0,
            "chu_ky_so_created": 0,
            "chu_ky_so_updated_file": 0,
            "lich_su_created": 0,
            "lich_su_updated": 0,
            "van_ban_created": 0,
            "cong_viec_created": 0,
            "files_created": 0,
            "hash_backfilled": 0,
            "hash_missing_source": 0,
        }
        self.branch = None
        self.departments = {}
        self.role_users = {}
        self.role_profiles = {}
        self.role_signatures = {}
        self.used_document_ids = set()
        self.used_task_ids = set()

    def run(self):
        self.ensure_background()
        self.ensure_role_users()
        self.ensure_signatures_for_all_role_users()
        self.seed_histories()
        self.backfill_existing_hashes()

    def ensure_background(self):
        self.branch, _ = ChiNhanh.objects.get_or_create(ten_chi_nhanh="Trụ sở Hà Nội")
        for name in {
            "Ban Giám Đốc",
            "Phòng Hành Chính/Nhân sự",
            "Phòng Kế Toán",
            "Phòng Kiểm Toán",
        }:
            department, _ = PhongBan.objects.get_or_create(
                chi_nhanh=self.branch,
                ten_phong_ban=name,
            )
            self.departments[name] = department

    def ensure_role_users(self):
        for role, spec in ROLE_USER_SPECS.items():
            department = self.departments[spec["department"]]
            user, created = User.objects.update_or_create(
                username=spec["username"],
                defaults={
                    "email": spec["email"],
                    "ho_va_ten": spec["name"],
                    "chuc_vu": spec["title"],
                    "role": role,
                    "chi_nhanh": self.branch,
                    "phong_ban": department,
                    "is_active": True,
                    "is_staff": spec.get("is_staff", False),
                    "is_superuser": spec.get("is_superuser", False),
                },
            )
            if self.password and (created or not user.has_usable_password()):
                user.set_password(self.password)
                user.save(update_fields=["password"])
            elif created and not user.has_usable_password():
                user.set_unusable_password()
                user.save(update_fields=["password"])
            if created:
                self.stats["users_created"] += 1

            profile = self.sync_profile(user, department)
            self.role_users[role] = user
            self.role_profiles[role] = profile

    def sync_profile(self, user, department):
        profile = NguoiDung.objects.filter(tai_khoan=user).first()
        if profile is None and not user.email:
            user.email = f"user-{user.pk}@role-seed.local"
            user.save(update_fields=["email"])

        if profile is not None:
            pass
        elif hasattr(user, "sync_access_context"):
            profile = user.sync_access_context()
        elif hasattr(user, "sync_core_profile"):
            profile = user.sync_core_profile()
        else:
            profile, _ = NguoiDung.objects.update_or_create(
                tai_khoan=user,
                defaults={
                    "phong_ban": department,
                    "ho_va_ten": user.ho_va_ten or user.username,
                    "chuc_vu": user.chuc_vu,
                    "email": user.email,
                    "sdt": user.sdt,
                },
            )

        update_fields = []
        if profile.phong_ban_id != department.pk:
            profile.phong_ban = department
            update_fields.append("phong_ban")
        if update_fields:
            profile.save(update_fields=update_fields)
        self.stats["core_profiles_synced"] += 1
        return profile

    def ensure_signatures_for_all_role_users(self):
        users = User.objects.filter(role__in=User.Role.values).order_by("id")
        for user in users:
            department = user.phong_ban or self.departments.get("Phòng Hành Chính/Nhân sự")
            profile = self.sync_profile(user, department)
            signature, created = ChuKySo.objects.get_or_create(nguoi_dung=profile)
            if created:
                self.stats["chu_ky_so_created"] += 1

            if not signature.anh_chu_ky or not default_storage.exists(signature.anh_chu_ky.name):
                signed_time = self.now
                signature.anh_chu_ky = self.ensure_signature_image(
                    f"anh_chu_ky/seed_chu_ky_so/chu_ky_{user.pk}.png",
                    profile.ho_va_ten,
                    signed_time,
                )
                signature.save(update_fields=["anh_chu_ky"])
                self.stats["chu_ky_so_updated_file"] += 1

            if user.role in self.role_profiles and profile.pk == self.role_profiles[user.role].pk:
                self.role_signatures[user.role] = signature

        for role, profile in self.role_profiles.items():
            self.role_signatures[role] = ChuKySo.objects.get(nguoi_dung=profile)

    def should_sign_document(self, role, index):
        if role == User.Role.CHUYEN_VIEN:
            return index % 3 != 0
        return index % 5 != 0

    def seed_histories(self):
        for role in (User.Role.ADMIN, User.Role.LANH_DAO, User.Role.VAN_THU, User.Role.CHUYEN_VIEN):
            document_pool = self.document_pool(role)
            task_pool = self.task_pool(role)

            for index in range(1, self.per_role + 1):
                signed_time = self.now - timedelta(days=(index - 1) % 30, hours=self.role_offset(role))
                if self.should_sign_document(role, index):
                    document = self.take_document(role, index, document_pool)
                    self.ensure_history(
                        role=role,
                        index=index,
                        signed_time=signed_time,
                        van_ban=document,
                        cong_viec=None,
                    )
                else:
                    task = self.take_task(role, index, task_pool)
                    self.ensure_history(
                        role=role,
                        index=index,
                        signed_time=signed_time,
                        van_ban=None,
                        cong_viec=task,
                    )

    def document_pool(self, role):
        qs = (
            VanBan.objects
            .filter(so_ky_hieu__startswith=f"CKS-{role}-VB-")
            .exclude(lich_su_ky_so__isnull=False)
            .order_by("van_ban_id")
        )
        profile = self.role_profiles[role]
        if role == User.Role.LANH_DAO:
            qs = qs.filter(lanh_dao_duyet=profile)
        elif role == User.Role.VAN_THU:
            qs = qs.filter(nguoi_tao=profile)
        elif role == User.Role.CHUYEN_VIEN:
            qs = qs.filter(
                vanbanduyet__chuyentiep__chuyentiepchitiet__nguoi_dung=profile
            ).distinct()
        return list(qs[: self.per_role * 2])

    def task_pool(self, role):
        qs = (
            CongViec.objects
            .filter(ten_cong_viec__startswith=f"CKS-{role}-CV-")
            .exclude(lich_su_ky_so__isnull=False)
            .order_by("cong_viec_id")
        )
        profile = self.role_profiles[role]
        if role == User.Role.LANH_DAO:
            qs = qs.filter(nguoi_giao=profile)
        elif role == User.Role.CHUYEN_VIEN:
            qs = qs.filter(nguoi_thuc_hien=profile)
        return list(qs[: self.per_role * 2])

    def take_document(self, role, index, pool):
        while pool:
            document = pool.pop(0)
            if document.pk not in self.used_document_ids:
                self.used_document_ids.add(document.pk)
                return document
        document = self.ensure_document(role, index + 2000)
        self.used_document_ids.add(document.pk)
        return document

    def take_task(self, role, index, pool):
        while pool:
            task = pool.pop(0)
            if task.pk not in self.used_task_ids:
                self.used_task_ids.add(task.pk)
                return task
        task = self.ensure_task(role, index + 2000)
        self.used_task_ids.add(task.pk)
        return task

    def ensure_record(self, role, index):
        record, _ = HoSoVanBan.objects.update_or_create(
            ky_hieu_ho_so=f"CKS-HS-{role}-{index:03d}",
            defaults={
                "tieu_de_ho_so": f"Hồ sơ ký số {role} số {index:03d}",
                "nguoi_tao": self.role_profiles[User.Role.VAN_THU],
                "thoi_gian_bao_quan": HoSoVanBan.THOI_GIAN_BAO_QUAN_CHOICES[1][0],
                "so_nam_luu_tru": 5,
                "trang_thai": HoSoVanBan.TRANG_THAI_CHOICES[0][0],
                "mo_ta": "Hồ sơ nền cho dữ liệu chữ ký số.",
            },
        )
        for profile in self.role_profiles.values():
            NguoiXuLyHoSo.objects.get_or_create(ho_so_van_ban=record, nguoi_xu_ly=profile)
            if profile.phong_ban_id:
                PhongXemHoSo.objects.get_or_create(ho_so_van_ban=record, phong_ban=profile.phong_ban)
        return record

    def ensure_document(self, role, index):
        status = self.document_status(role, index)
        phan_loai = self.document_type(role, index)
        file_path = self.ensure_pdf_file(
            f"van_ban/seed_chu_ky_so/{role.lower()}_{index:03d}.pdf",
            f"Tài liệu ký số {role} {index:03d}",
        )
        document, created = VanBan.objects.update_or_create(
            so_ky_hieu=f"CKS-{role}-VB-{index:03d}",
            defaults={
                "lanh_dao_duyet": self.role_profiles[User.Role.LANH_DAO],
                "nguoi_tao": self.document_creator(role),
                "ho_so_van_ban": self.ensure_record(role, index),
                "trich_yeu": f"Tài liệu ký số cho vai trò {role} số {index:03d}",
                "hinh_thuc": VanBan.HINH_THUC_CHOICES[index % len(VanBan.HINH_THUC_CHOICES)][0],
                "loai_van_ban": VanBan.LOAI_VAN_BAN_CHOICES[index % len(VanBan.LOAI_VAN_BAN_CHOICES)][0],
                "don_vi_ban_hanh": self.document_creator(role).phong_ban.ten_phong_ban,
                "ngay_van_ban": self.today - timedelta(days=index % 30),
                "ngay_den": self.today - timedelta(days=index % 10),
                "han_xu_ly": self.today + timedelta(days=3 + index % 10),
                "ngay_cap_nhat": self.today,
                "do_khan": VanBan.DO_KHAN_CHOICES[index % len(VanBan.DO_KHAN_CHOICES)][0],
                "do_mat": VanBan.DO_MAT_CHOICES[index % len(VanBan.DO_MAT_CHOICES)][0],
                "file_dinh_kem": file_path,
                "kich_thuoc": self.storage_size(file_path),
                "trang_thai": status,
                "noi_dung": "Dữ liệu mẫu phục vụ chức năng chữ ký số.",
                "phan_loai": phan_loai,
            },
        )
        if created:
            self.stats["van_ban_created"] += 1

        approval, _ = VanBanDuyet.objects.update_or_create(
            van_ban=document,
            defaults={"van_thu": self.role_profiles[User.Role.VAN_THU]},
        )
        if status == VanBan.TRANG_THAI_CHOICES[5][0]:
            BanHanh.objects.get_or_create(van_ban=document)
        if phan_loai == VanBan.PHAN_LOAI_CHOICES[1][0] or role in {User.Role.VAN_THU, User.Role.CHUYEN_VIEN}:
            transfer, _ = ChuyenTiep.objects.get_or_create(van_ban_duyet=approval)
            ChuyenTiepChiTiet.objects.get_or_create(
                chuyen_tiep=transfer,
                nguoi_dung=self.role_profiles[User.Role.CHUYEN_VIEN],
                defaults={"phong_ban": self.role_profiles[User.Role.CHUYEN_VIEN].phong_ban},
            )
        return document

    def document_status(self, role, index):
        if role == User.Role.LANH_DAO:
            return [VanBan.TRANG_THAI_CHOICES[1][0], VanBan.TRANG_THAI_CHOICES[4][0]][index % 2]
        if role == User.Role.VAN_THU:
            return [VanBan.TRANG_THAI_CHOICES[5][0], VanBan.TRANG_THAI_CHOICES[3][0]][index % 2]
        if role == User.Role.CHUYEN_VIEN:
            return VanBan.TRANG_THAI_CHOICES[1][0]
        return VanBan.TRANG_THAI_CHOICES[3][0]

    def document_type(self, role, index):
        if role == User.Role.VAN_THU and index % 2 == 0:
            return VanBan.PHAN_LOAI_CHOICES[1][0]
        if role == User.Role.CHUYEN_VIEN:
            return VanBan.PHAN_LOAI_CHOICES[1][0]
        return VanBan.PHAN_LOAI_CHOICES[0][0]

    def document_creator(self, role):
        if role == User.Role.CHUYEN_VIEN:
            return self.role_profiles[User.Role.VAN_THU]
        if role == User.Role.VAN_THU:
            return self.role_profiles[User.Role.VAN_THU]
        return self.role_profiles[User.Role.CHUYEN_VIEN]

    def ensure_task(self, role, index):
        status = self.task_status(role, index)
        document = self.ensure_document_for_task(role, index)
        task, created = CongViec.objects.update_or_create(
            ten_cong_viec=f"CKS-{role}-CV-{index:03d}",
            defaults={
                "van_ban": document,
                "van_ban_den": document if document.phan_loai == VanBan.PHAN_LOAI_CHOICES[1][0] else None,
                "noi_dung_cong_viec": f"Công việc ký số cho vai trò {role} số {index:03d}.",
                "nguon_giao": CongViec.NguonGiao.VAN_BAN_DI,
                "trang_thai": status,
                "ngay_bat_dau": self.today - timedelta(days=index % 20),
                "han_xu_ly": timezone.now() + timedelta(days=2 + index % 12),
                "ngay_cap_nhat_giao_viec": self.today,
                "ket_qua_xu_ly": "Đã cập nhật kết quả xử lý." if status in {
                    CongViec.TrangThai.CHO_DUYET,
                    CongViec.TrangThai.DA_HOAN_THANH,
                } else "",
                "ghi_chu": "Dữ liệu công việc phục vụ lịch sử ký số.",
                "ngay_xu_ly": self.today,
                "yeu_cau_phe_duyet": True,
                "nguoi_giao": self.role_profiles[User.Role.LANH_DAO],
                "nguoi_thuc_hien": self.role_profiles[User.Role.CHUYEN_VIEN],
            },
        )
        if created:
            self.stats["cong_viec_created"] += 1

        PhanCongCongViec.objects.get_or_create(
            cong_viec=task,
            nguoi_phoi_hop=self.role_profiles[User.Role.CHUYEN_VIEN],
        )
        file_path = self.ensure_pdf_file(
            f"file_cv_lien_quan/seed_chu_ky_so/{role.lower()}_cv_{index:03d}.pdf",
            f"Hồ sơ công việc ký số {role} {index:03d}",
        )
        FileCVLienQuan.objects.get_or_create(
            file_van_ban=file_path,
            defaults={
                "cong_viec": task,
                "kich_thuoc": self.storage_size(file_path),
                "loai_file": FileCVLienQuan.LoaiFile.LIEN_QUAN,
                "nguon_tai_len": FileCVLienQuan.NguonTaiLen.KET_QUA_XU_LY,
                "nguoi_tai_len": self.role_profiles[User.Role.CHUYEN_VIEN],
            },
        )
        if status == CongViec.TrangThai.DA_HOAN_THANH:
            PheDuyetCongViec.objects.get_or_create(cong_viec=task)
        return task

    def ensure_document_for_task(self, role, index):
        return self.ensure_document(role, 1000 + index)

    def task_status(self, role, index):
        if role == User.Role.LANH_DAO:
            return [CongViec.TrangThai.CHO_DUYET, CongViec.TrangThai.DA_HOAN_THANH][index % 2]
        if role == User.Role.CHUYEN_VIEN:
            statuses = [
                CongViec.TrangThai.CHO_XU_LY,
                CongViec.TrangThai.CHO_DUYET,
                CongViec.TrangThai.DA_HOAN_THANH,
                CongViec.TrangThai.HOAN_TRA_CV,
                CongViec.TrangThai.HOAN_TRA_LD,
            ]
            return statuses[index % len(statuses)]
        if role == User.Role.VAN_THU:
            return CongViec.TrangThai.DA_HOAN_THANH
        return CongViec.TrangThai.CHO_DUYET

    def ensure_history(self, *, role, index, signed_time, van_ban, cong_viec):
        signature = self.role_signatures[role]
        signer_name = signature.nguoi_dung.ho_va_ten
        target = van_ban or cong_viec
        target_label = "van_ban" if van_ban else "cong_viec"
        file_path = self.ensure_signature_image(
            f"file_da_ky/seed_chu_ky_so/{role.lower()}_{target_label}_{index:03d}.png",
            signer_name,
            signed_time,
        )
        signature_image_path = self.ensure_signature_image(
            f"chu_ky_so/seed_chu_ky_so/{role.lower()}_{target_label}_{index:03d}.png",
            signer_name,
            signed_time,
        )
        source_file = get_signed_object_file_path(target)
        try:
            file_hash = calculate_file_sha256(source_file)
        except FileNotFoundError:
            source_name = getattr(source_file, "name", "")
            if not source_name:
                raise
            self.ensure_pdf_file(source_name, f"Tệp nguồn ký số {role} {index:03d}")
            file_hash = calculate_file_sha256(source_file)

        lookup = {"van_ban": van_ban} if van_ban else {"cong_viec": cong_viec}
        history, created = LichSuKySo.objects.update_or_create(
            **lookup,
            defaults={
                "chu_ky_so": signature,
                "cong_viec": None if van_ban else cong_viec,
                "van_ban": van_ban if van_ban else None,
                "hash_tai_lieu": file_hash,
                "file_hash": file_hash,
                "hash_algorithm": HASH_ALGORITHM,
                "file_da_ky": file_path,
                "signature_image": signature_image_path,
                "verified": True,
            },
        )
        if created:
            self.stats["lich_su_created"] += 1
        else:
            self.stats["lich_su_updated"] += 1

        LichSuKySo.objects.filter(pk=history.pk).update(thoi_gian_ky=signed_time)
        verify_signed_file(history)

    def backfill_existing_hashes(self):
        histories = (
            LichSuKySo.objects
            .select_related("chu_ky_so__nguoi_dung", "van_ban", "cong_viec")
            .order_by("lich_su_ky_so_id")
        )
        for history in histories:
            update_fields = []

            if not history.file_hash:
                source_file = get_signed_object_file_path(history)
                try:
                    history.file_hash = calculate_file_sha256(source_file)
                except FileNotFoundError:
                    self.stats["hash_missing_source"] += 1
                    verify_signed_file(history)
                    continue
                update_fields.append("file_hash")
                self.stats["hash_backfilled"] += 1

            if history.hash_algorithm != HASH_ALGORITHM:
                history.hash_algorithm = HASH_ALGORITHM
                update_fields.append("hash_algorithm")

            if not history.signature_image or not default_storage.exists(history.signature_image.name):
                signed_time = history.thoi_gian_ky or self.now
                signer_name = history.chu_ky_so.nguoi_dung.ho_va_ten
                history.signature_image = self.ensure_signature_image(
                    f"chu_ky_so/seed_chu_ky_so/backfill_{history.pk:05d}.png",
                    signer_name,
                    signed_time,
                )
                update_fields.append("signature_image")

            if update_fields:
                history.save(update_fields=update_fields)

            verify_signed_file(history)

    def ensure_pdf_file(self, relative_path, title):
        if not default_storage.exists(relative_path):
            content = (
                "%PDF-1.4\n"
                f"1 0 obj << /Title ({title}) >> endobj\n"
                "2 0 obj << /Length 64 >> stream\n"
                f"{title}\nDữ liệu mẫu chữ ký số.\n"
                "endstream endobj\n%%EOF\n"
            ).encode("utf-8")
            default_storage.save(relative_path, ContentFile(content))
            self.stats["files_created"] += 1
        return relative_path

    def ensure_signature_image(self, relative_path, signer_name, signed_time):
        if not default_storage.exists(relative_path):
            image = self.render_signature_image(signer_name, signed_time)
            default_storage.save(relative_path, ContentFile(image))
            self.stats["files_created"] += 1
        return relative_path

    def render_signature_image(self, signer_name, signed_time):
        from PIL import Image, ImageDraw, ImageFont

        image = Image.new("RGB", (760, 260), "#f8fafc")
        draw = ImageDraw.Draw(image)
        draw.rectangle((18, 18, 742, 242), fill="#ffffff", outline="#0f6c92", width=3)
        draw.rectangle((34, 34, 726, 226), outline="#d1d5dc", width=1)

        title_font = self.load_font(30, bold=True)
        body_font = self.load_font(24)
        small_font = self.load_font(20)

        draw.text((56, 55), "Ảnh chữ ký", fill="#0f172a", font=title_font)
        draw.text((56, 108), f"Ký bởi: {signer_name}", fill="#1f2937", font=body_font)
        draw.text(
            (56, 150),
            f"Thời gian: {signed_time.strftime('%d/%m/%Y %H:%M')}",
            fill="#1f2937",
            font=body_font,
        )
        draw.text((56, 192), "Trạng thái: Đã ký", fill="#047857", font=small_font)

        output = BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()

    def load_font(self, size, *, bold=False):
        from PIL import ImageFont

        candidates = [
            "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for path in candidates:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
        return ImageFont.load_default()

    def storage_size(self, relative_path):
        try:
            return default_storage.size(relative_path)
        except Exception:
            return 0

    def role_offset(self, role):
        return {
            User.Role.ADMIN: 1,
            User.Role.LANH_DAO: 3,
            User.Role.VAN_THU: 5,
            User.Role.CHUYEN_VIEN: 7,
        }.get(role, 0)

    def print_summary(self):
        self.command.stdout.write("")
        self.command.stdout.write(self.command.style.SUCCESS("Seed chữ ký số hoàn tất."))
        self.command.stdout.write(f"ChuKySo tạo mới: {self.stats['chu_ky_so_created']}")
        self.command.stdout.write(f"ChuKySo cập nhật ảnh: {self.stats['chu_ky_so_updated_file']}")
        self.command.stdout.write(f"LichSuKySo tạo mới: {self.stats['lich_su_created']}")
        self.command.stdout.write(f"LichSuKySo cập nhật: {self.stats['lich_su_updated']}")
        self.command.stdout.write(f"VanBan nền tạo mới: {self.stats['van_ban_created']}")
        self.command.stdout.write(f"CongViec nền tạo mới: {self.stats['cong_viec_created']}")
        self.command.stdout.write(f"File demo tạo mới: {self.stats['files_created']}")
        self.command.stdout.write(f"LichSuKySo backfill SHA-256: {self.stats['hash_backfilled']}")
        self.command.stdout.write(f"LichSuKySo thiếu file nguồn: {self.stats['hash_missing_source']}")
        self.command.stdout.write("")
        self.command.stdout.write("Tài khoản demo chính: admin.demo, lanhdao.demo, vanthu.demo, chuyenvien.demo")
