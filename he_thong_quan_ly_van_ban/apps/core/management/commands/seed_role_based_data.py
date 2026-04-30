# -*- coding: utf-8 -*-
import os
from collections import defaultdict
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.core.models import (
    BanHanh,
    ChiNhanh,
    ChuyenTiep,
    ChuyenTiepChiTiet,
    CongViec,
    DonViNgoai,
    FileCVLienQuan,
    HoSoVanBan,
    HoanTraCongViec,
    NguoiDung,
    NguoiXuLyHoSo,
    NoiNhanVanBan,
    PheDuyetCongViec,
    PhanCongCongViec,
    PhongBan,
    PhongXemHoSo,
    VanBan,
    VanBanDuyet,
    VanBanHoanTra,
    VanBanLienQuan,
)
from apps.quanlyvanbanden.models import (
    TepVanBanDen,
    VanBanDen,
    VanBanDenChuyenTiep,
)

from ._data_audit import configure_utf8_output, database_kind


User = get_user_model()

BRANCHES = {
    "hn": "Trụ sở Hà Nội",
    "dn": "Chi nhánh Đà Nẵng",
    "hcm": "Chi nhánh TP.HCM",
}

DEPARTMENTS = {
    "ban_giam_doc": "Ban Giám Đốc",
    "van_thu": "Văn Thư",
    "ke_toan": "Phòng Kế Toán",
    "kiem_toan": "Phòng Kiểm Toán",
    "tu_van_thue": "Phòng Tư Vấn Thuế",
    "hanh_chinh": "Phòng Hành Chính/Nhân sự",
    "dao_tao": "Phòng Đào Tạo Chất Lượng",
}

USER_SPECS = {
    "admin": {
        "username": "admin.demo",
        "email": "admin.demo@role-seed.local",
        "name": "Quản trị Demo",
        "role": User.Role.ADMIN,
        "branch": "hn",
        "department": "ban_giam_doc",
        "title": "Quản trị hệ thống",
        "is_staff": True,
        "is_superuser": True,
    },
    "leader": {
        "username": "lanhdao.demo",
        "email": "lanhdao.demo@role-seed.local",
        "name": "Lãnh đạo Demo",
        "role": User.Role.LANH_DAO,
        "branch": "hn",
        "department": "ban_giam_doc",
        "title": "Lãnh đạo phụ trách",
    },
    "clerk": {
        "username": "vanthu.demo",
        "email": "vanthu.demo@role-seed.local",
        "name": "Văn thư Demo",
        "role": User.Role.VAN_THU,
        "branch": "hn",
        "department": "hanh_chinh",
        "title": "Văn thư hành chính",
    },
    "specialist": {
        "username": "chuyenvien.demo",
        "email": "chuyenvien.demo@role-seed.local",
        "name": "Chuyên viên Demo",
        "role": User.Role.CHUYEN_VIEN,
        "branch": "hn",
        "department": "ke_toan",
        "title": "Chuyên viên xử lý nghiệp vụ",
    },
    "assistant": {
        "username": "chuyenvien.phoihop",
        "email": "chuyenvien.phoihop@role-seed.local",
        "name": "Chuyên viên Phối hợp",
        "role": User.Role.CHUYEN_VIEN,
        "branch": "hn",
        "department": "kiem_toan",
        "title": "Chuyên viên phối hợp",
    },
    "backup_leader": {
        "username": "lanhdao.phu",
        "email": "lanhdao.phu@role-seed.local",
        "name": "Lãnh đạo Phụ trách",
        "role": User.Role.LANH_DAO,
        "branch": "dn",
        "department": "ban_giam_doc",
        "title": "Lãnh đạo chi nhánh",
    },
    "backup_clerk": {
        "username": "vanthu.phu",
        "email": "vanthu.phu@role-seed.local",
        "name": "Văn thư Phụ trách",
        "role": User.Role.VAN_THU,
        "branch": "hcm",
        "department": "hanh_chinh",
        "title": "Văn thư chi nhánh",
    },
}


class Command(BaseCommand):
    help = "Seed role based demo data with Django ORM."

    def add_arguments(self, parser):
        parser.add_argument(
            "--per-role",
            type=int,
            default=25,
            help="Number of role-visible business records to seed.",
        )

    def handle(self, *args, **options):
        configure_utf8_output()
        per_role = max(1, options["per_role"])
        password = os.getenv("ROLE_SEED_PASSWORD", "123")

        self.stdout.write(f"Database hiện tại: {database_kind()}")
        self.stdout.write(f"Seed role-based data với per-role={per_role}")
        self.stdout.write("Không xóa dữ liệu cũ, không reset database, không xóa user hiện có.")

        seeder = RoleBasedSeeder(self, per_role, password)
        with transaction.atomic():
            seeder.run()

        seeder.print_summary()


class RoleBasedSeeder:
    def __init__(self, command, per_role, password):
        self.command = command
        self.per_role = per_role
        self.password = password
        self.today = timezone.localdate()
        self.now = timezone.now()
        self.stats = defaultdict(int)

        self.branches = {}
        self.departments = {}
        self.users = {}
        self.profiles = {}
        self.outside_units = []
        self.records = []
        self.outgoing_documents = []
        self.incoming_documents = []
        self.legacy_incoming_documents = []
        self.tasks = []

    def run(self):
        self.seed_branches_departments()
        self.seed_users()
        self.seed_outside_units()
        self.seed_records()
        self.seed_outgoing_documents()
        self.seed_incoming_documents()
        self.seed_tasks()

    def seed_branches_departments(self):
        for branch_key, branch_name in BRANCHES.items():
            branch, created = ChiNhanh.objects.get_or_create(ten_chi_nhanh=branch_name)
            self.branches[branch_key] = branch
            self._track("ADMIN", "ChiNhanh", created)

            for department_key, department_name in DEPARTMENTS.items():
                department, dept_created = PhongBan.objects.get_or_create(
                    chi_nhanh=branch,
                    ten_phong_ban=department_name,
                )
                self.departments[(branch_key, department_key)] = department
                self._track("ADMIN", "PhongBan", dept_created)

    def seed_users(self):
        for key, spec in USER_SPECS.items():
            branch = self.branches[spec["branch"]]
            department = self.departments[(spec["branch"], spec["department"])]
            user, created = User.objects.update_or_create(
                username=spec["username"],
                defaults={
                    "email": spec["email"],
                    "ho_va_ten": spec["name"],
                    "chuc_vu": spec["title"],
                    "role": spec["role"],
                    "chi_nhanh": branch,
                    "phong_ban": department,
                    "is_active": True,
                    "is_staff": spec.get("is_staff", False),
                    "is_superuser": spec.get("is_superuser", False),
                },
            )
            if created or not user.has_usable_password():
                user.set_password(self.password)
                user.save(update_fields=["password"])

            profile = self.sync_profile(user, department)
            self.users[key] = user
            self.profiles[key] = profile
            self._track("ADMIN", "Customer", created)
            self._track("ADMIN", "NguoiDung", created)

    def sync_profile(self, user, department):
        if hasattr(user, "sync_access_context"):
            profile = user.sync_access_context()
        elif hasattr(user, "sync_core_profile"):
            profile = user.sync_core_profile()
        else:
            profile, _ = NguoiDung.objects.update_or_create(
                tai_khoan=user,
                defaults={
                    "phong_ban": department,
                    "ho_va_ten": user.ho_va_ten,
                    "chuc_vu": user.chuc_vu,
                    "email": user.email,
                    "sdt": user.sdt,
                },
            )

        if profile.phong_ban_id != department.pk:
            profile.phong_ban = department
            profile.save(update_fields=["phong_ban"])
        return profile

    def seed_outside_units(self):
        for index in range(1, self.per_role + 1):
            unit, created = DonViNgoai.objects.update_or_create(
                email=f"donvi.role.seed.{index:03d}@example.com",
                defaults={
                    "ten_don_vi": f"Đơn vị phối hợp số {index:03d}",
                    "dia_chi": f"Số {index} phố Mẫu, Hà Nội",
                    "so_dien_thoai": f"02438{index:05d}",
                },
            )
            self.outside_units.append(unit)
            self._track("ADMIN", "DonViNgoai", created)

    def seed_records(self):
        for index in range(1, self.per_role + 1):
            record, created = HoSoVanBan.objects.update_or_create(
                ky_hieu_ho_so=f"RB-HS-{index:03d}",
                defaults={
                    "tieu_de_ho_so": f"Hồ sơ kiểm thử phân quyền {index:03d}",
                    "nguoi_tao": self.profiles["clerk"],
                    "thoi_gian_bao_quan": self._choice(HoSoVanBan.THOI_GIAN_BAO_QUAN_CHOICES, index),
                    "so_nam_luu_tru": 5 + (index % 6),
                    "trang_thai": HoSoVanBan.TRANG_THAI_CHOICES[index % len(HoSoVanBan.TRANG_THAI_CHOICES)][0],
                    "mo_ta": "Dữ liệu mẫu phục vụ kiểm thử theo role.",
                },
            )
            self.records.append(record)
            self._track("ADMIN", "HoSoVanBan", created)

            for profile_key in ("leader", "clerk", "specialist", "assistant"):
                _, link_created = NguoiXuLyHoSo.objects.get_or_create(
                    ho_so_van_ban=record,
                    nguoi_xu_ly=self.profiles[profile_key],
                )
                self._track("CHUYEN_VIEN", "NguoiXuLyHoSo", link_created)

            for department in {
                self.profiles["leader"].phong_ban,
                self.profiles["clerk"].phong_ban,
                self.profiles["specialist"].phong_ban,
            }:
                if department:
                    _, view_created = PhongXemHoSo.objects.get_or_create(
                        ho_so_van_ban=record,
                        phong_ban=department,
                    )
                    self._track("ADMIN", "PhongXemHoSo", view_created)

    def seed_outgoing_documents(self):
        statuses = [
            VanBan.TRANG_THAI_CHOICES[0][0],
            VanBan.TRANG_THAI_CHOICES[2][0],
            VanBan.TRANG_THAI_CHOICES[3][0],
            VanBan.TRANG_THAI_CHOICES[4][0],
            VanBan.TRANG_THAI_CHOICES[5][0],
        ]
        approved_statuses = {
            VanBan.TRANG_THAI_CHOICES[3][0],
            VanBan.TRANG_THAI_CHOICES[4][0],
            VanBan.TRANG_THAI_CHOICES[5][0],
        }

        for index in range(1, self.per_role + 1):
            status = statuses[(index - 1) % len(statuses)]
            file_path = self.ensure_demo_file(
                f"van_ban/seed_role_based/vb_di_{index:03d}.pdf",
                f"Văn bản đi mẫu {index:03d}",
            )
            document, created = VanBan.objects.update_or_create(
                so_ky_hieu=f"RB-VBDI-{index:03d}",
                defaults={
                    "lanh_dao_duyet": self.profiles["leader"],
                    "nguoi_tao": self.profiles["specialist"],
                    "ho_so_van_ban": self.records[(index - 1) % len(self.records)],
                    "trich_yeu": f"Tờ trình xử lý nghiệp vụ số {index:03d}",
                    "hinh_thuc": self._choice(VanBan.HINH_THUC_CHOICES, index),
                    "loai_van_ban": self._choice(VanBan.LOAI_VAN_BAN_CHOICES, index),
                    "don_vi_ban_hanh": self.profiles["specialist"].phong_ban.ten_phong_ban,
                    "ngay_van_ban": self.today - timedelta(days=index % 30),
                    "ngay_den": self.today - timedelta(days=(index + 1) % 30),
                    "han_xu_ly": self.today + timedelta(days=3 + index % 10),
                    "ngay_cap_nhat": self.today,
                    "do_khan": self._choice(VanBan.DO_KHAN_CHOICES, index),
                    "do_mat": self._choice(VanBan.DO_MAT_CHOICES, index),
                    "file_dinh_kem": file_path,
                    "kich_thuoc": self.file_size(file_path),
                    "trang_thai": status,
                    "noi_dung": "Nội dung mẫu phục vụ lãnh đạo duyệt và văn thư ban hành.",
                    "phan_loai": VanBan.PHAN_LOAI_CHOICES[0][0],
                },
            )
            self.outgoing_documents.append(document)
            self._track("LANH_DAO", "VanBan", created)

            related_path = self.ensure_demo_file(
                f"van_ban_lien_quan/seed_role_based/vb_di_lq_{index:03d}.pdf",
                f"Tài liệu liên quan văn bản đi {index:03d}",
            )
            _, related_created = VanBanLienQuan.objects.get_or_create(
                file_van_ban=related_path,
                defaults={
                    "van_ban": document,
                    "kich_thuoc": self.file_size(related_path),
                },
            )
            self._track("LANH_DAO", "VanBanLienQuan", related_created)

            if status in approved_statuses:
                approval, approval_created = VanBanDuyet.objects.update_or_create(
                    van_ban=document,
                    defaults={"van_thu": self.profiles["clerk"]},
                )
                self._track("VAN_THU", "VanBanDuyet", approval_created)
                self.ensure_forwarding(approval, role_bucket="VAN_THU")

            if status == VanBan.TRANG_THAI_CHOICES[5][0]:
                issue, issue_created = BanHanh.objects.get_or_create(van_ban=document)
                self._track("VAN_THU", "BanHanh", issue_created)
                self.ensure_receivers(document, index)

            if status == VanBan.TRANG_THAI_CHOICES[2][0]:
                _, return_created = VanBanHoanTra.objects.get_or_create(
                    van_ban=document,
                    noi_dung=f"Yêu cầu chuyên viên bổ sung hồ sơ số {index:03d}.",
                )
                self._track("LANH_DAO", "VanBanHoanTra", return_created)

    def seed_incoming_documents(self):
        core_statuses = [
            VanBan.TRANG_THAI_CHOICES[0][0],
            VanBan.TRANG_THAI_CHOICES[1][0],
            VanBan.TRANG_THAI_CHOICES[2][0],
            VanBan.TRANG_THAI_CHOICES[3][0],
        ]
        legacy_statuses = [
            VanBanDen.TrangThai.CHO_XU_LY,
            VanBanDen.TrangThai.DA_XU_LY,
            VanBanDen.TrangThai.HOAN_TRA,
            VanBanDen.TrangThai.XEM_DE_BIET,
        ]

        for index in range(1, self.per_role + 1):
            file_path = self.ensure_demo_file(
                f"van_ban/seed_role_based/vb_den_core_{index:03d}.pdf",
                f"Văn bản đến core mẫu {index:03d}",
            )
            core_document, created = VanBan.objects.update_or_create(
                so_ky_hieu=f"RB-VBDEN-CORE-{index:03d}",
                defaults={
                    "lanh_dao_duyet": self.profiles["leader"],
                    "nguoi_tao": self.profiles["clerk"],
                    "ho_so_van_ban": self.records[(index - 1) % len(self.records)],
                    "trich_yeu": f"Công văn đến cần xử lý số {index:03d}",
                    "hinh_thuc": self._choice(VanBan.HINH_THUC_CHOICES, index),
                    "loai_van_ban": self._choice(VanBan.LOAI_VAN_BAN_CHOICES, index),
                    "don_vi_ban_hanh": self.outside_units[(index - 1) % len(self.outside_units)].ten_don_vi,
                    "ngay_van_ban": self.today - timedelta(days=(index * 2) % 30),
                    "ngay_den": self.today - timedelta(days=index % 12),
                    "han_xu_ly": self.today + timedelta(days=2 + index % 12),
                    "ngay_cap_nhat": self.today,
                    "do_khan": self._choice(VanBan.DO_KHAN_CHOICES, index),
                    "do_mat": self._choice(VanBan.DO_MAT_CHOICES, index),
                    "file_dinh_kem": file_path,
                    "kich_thuoc": self.file_size(file_path),
                    "trang_thai": core_statuses[(index - 1) % len(core_statuses)],
                    "noi_dung": "Văn bản đến mẫu được gán cho lãnh đạo và chuyển chuyên viên.",
                    "phan_loai": VanBan.PHAN_LOAI_CHOICES[1][0],
                },
            )
            self.incoming_documents.append(core_document)
            self._track("LANH_DAO", "VanBanDenCore", created)

            approval, approval_created = VanBanDuyet.objects.update_or_create(
                van_ban=core_document,
                defaults={"van_thu": self.profiles["clerk"]},
            )
            self._track("VAN_THU", "VanBanDuyet", approval_created)
            self.ensure_forwarding(approval, role_bucket="CHUYEN_VIEN")

            legacy_document, legacy_created = VanBanDen.objects.update_or_create(
                so_ky_hieu=f"RB-VBDEN-{index:03d}",
                defaults={
                    "don_vi_ban_hanh": self.outside_units[(index - 1) % len(self.outside_units)].ten_don_vi,
                    "trich_yeu": f"Văn bản đến legacy số {index:03d}",
                    "loai_van_ban": self._choice(VanBanDen.LoaiVanBan.choices, index),
                    "hinh_thuc_van_ban": self._choice(VanBanDen.HinhThucVanBan.choices, index),
                    "ngay_van_ban": self.today - timedelta(days=index % 30),
                    "ngay_den": self.today,
                    "han_xu_ly": self.today + timedelta(days=3 + index % 10),
                    "do_mat": self._choice(VanBanDen.DoMat.choices, index),
                    "do_khan": self._choice(VanBanDen.DoKhan.choices, index),
                    "linh_vuc": "Quản lý văn bản",
                    "noi_dung_xu_ly": "Dữ liệu mẫu cho app quanlyvanbanden.",
                    "trang_thai": legacy_statuses[(index - 1) % len(legacy_statuses)],
                    "lanh_dao_xu_ly": self.users["leader"],
                    "nguoi_tao": self.users["clerk"],
                },
            )
            self.legacy_incoming_documents.append(legacy_document)
            self._track("VAN_THU", "VanBanDen", legacy_created)

            attachment_path = self.ensure_demo_file(
                f"van_ban_den/tep_tin/seed_role_based/vb_den_{index:03d}.pdf",
                f"Tệp văn bản đến {index:03d}",
            )
            attachment = TepVanBanDen.objects.filter(tep=attachment_path).first()
            if attachment:
                created_attachment = False
                if attachment.van_ban_den_id != legacy_document.pk:
                    attachment.van_ban_den = legacy_document
                    attachment.loai = TepVanBanDen.LoaiTep.DINH_KEM
                    attachment.save(update_fields=["van_ban_den", "loai"])
            else:
                TepVanBanDen.objects.create(
                    van_ban_den=legacy_document,
                    loai=TepVanBanDen.LoaiTep.DINH_KEM,
                    tep=attachment_path,
                )
                created_attachment = True
            self._track("VAN_THU", "TepVanBanDen", created_attachment)

            _, transfer_created = VanBanDenChuyenTiep.objects.update_or_create(
                van_ban_den=legacy_document,
                chuyen_vien=self.users["specialist"],
                defaults={"nguoi_chuyen": self.users["leader"]},
            )
            self._track("CHUYEN_VIEN", "VanBanDenChuyenTiep", transfer_created)

    def seed_tasks(self):
        statuses = [
            CongViec.TrangThai.CHO_XU_LY,
            CongViec.TrangThai.CHO_DUYET,
            CongViec.TrangThai.DA_HOAN_THANH,
            CongViec.TrangThai.HOAN_TRA_CV,
            CongViec.TrangThai.HOAN_TRA_LD,
        ]

        for index in range(1, self.per_role + 1):
            status = statuses[(index - 1) % len(statuses)]
            start_date = self.today - timedelta(days=index % 15)
            due_time = timezone.now() + timedelta(days=2 + index % 14)
            document = self.outgoing_documents[(index - 1) % len(self.outgoing_documents)]
            incoming_document = self.incoming_documents[(index - 1) % len(self.incoming_documents)]
            task, created = CongViec.objects.update_or_create(
                ten_cong_viec=f"RB-CV-{index:03d} - Xử lý nghiệp vụ theo role",
                defaults={
                    "van_ban": document,
                    "van_ban_den": incoming_document,
                    "noi_dung_cong_viec": f"Kiểm tra, xử lý và báo cáo kết quả nghiệp vụ số {index:03d}.",
                    "nguon_giao": self._choice(CongViec.NguonGiao.choices, index),
                    "trang_thai": status,
                    "ngay_bat_dau": start_date,
                    "han_xu_ly": due_time,
                    "ngay_cap_nhat_giao_viec": self.today,
                    "ket_qua_xu_ly": "Đã xử lý và chờ lãnh đạo duyệt." if status in {
                        CongViec.TrangThai.CHO_DUYET,
                        CongViec.TrangThai.DA_HOAN_THANH,
                    } else "",
                    "ghi_chu": "Dữ liệu công việc mẫu theo role.",
                    "ngay_xu_ly": self.today,
                    "yeu_cau_phe_duyet": True,
                    "nguoi_giao": self.profiles["leader"],
                    "nguoi_thuc_hien": self.profiles["specialist"],
                },
            )
            self.tasks.append(task)
            self._track("LANH_DAO", "CongViec", created)
            self._track("CHUYEN_VIEN", "CongViecDuocGiao", created)

            _, collaborator_created = PhanCongCongViec.objects.get_or_create(
                cong_viec=task,
                nguoi_phoi_hop=self.profiles["assistant"],
            )
            self._track("CHUYEN_VIEN", "PhanCongCongViec", collaborator_created)

            task_file_path = self.ensure_demo_file(
                f"file_cv_lien_quan/seed_role_based/giao_viec_{index:03d}.pdf",
                f"File giao việc {index:03d}",
            )
            _, task_file_created = FileCVLienQuan.objects.get_or_create(
                file_van_ban=task_file_path,
                defaults={
                    "cong_viec": task,
                    "kich_thuoc": self.file_size(task_file_path),
                    "loai_file": FileCVLienQuan.LoaiFile.CHINH,
                    "nguon_tai_len": FileCVLienQuan.NguonTaiLen.GIAO_VIEC,
                    "nguoi_tai_len": self.profiles["leader"],
                },
            )
            self._track("CHUYEN_VIEN", "FileCVLienQuan", task_file_created)

            if status in {CongViec.TrangThai.CHO_DUYET, CongViec.TrangThai.DA_HOAN_THANH}:
                result_path = self.ensure_demo_file(
                    f"file_cv_lien_quan/seed_role_based/ket_qua_{index:03d}.pdf",
                    f"File kết quả xử lý {index:03d}",
                )
                _, result_created = FileCVLienQuan.objects.get_or_create(
                    file_van_ban=result_path,
                    defaults={
                        "cong_viec": task,
                        "kich_thuoc": self.file_size(result_path),
                        "loai_file": FileCVLienQuan.LoaiFile.LIEN_QUAN,
                        "nguon_tai_len": FileCVLienQuan.NguonTaiLen.KET_QUA_XU_LY,
                        "nguoi_tai_len": self.profiles["specialist"],
                    },
                )
                self._track("CHUYEN_VIEN", "FileKetQuaXuLy", result_created)

            if status == CongViec.TrangThai.DA_HOAN_THANH:
                _, approved_created = PheDuyetCongViec.objects.get_or_create(cong_viec=task)
                self._track("LANH_DAO", "PheDuyetCongViec", approved_created)

            if status in {CongViec.TrangThai.HOAN_TRA_CV, CongViec.TrangThai.HOAN_TRA_LD}:
                returner = (
                    self.profiles["leader"]
                    if status == CongViec.TrangThai.HOAN_TRA_CV
                    else self.profiles["specialist"]
                )
                _, return_created = HoanTraCongViec.objects.get_or_create(
                    cong_viec=task,
                    noi_dung=f"Hoàn trả để bổ sung nội dung công việc số {index:03d}.",
                    defaults={"nguoi_hoan_tra": returner},
                )
                self._track("LANH_DAO", "HoanTraCongViec", return_created)

    def ensure_forwarding(self, approval, role_bucket):
        transfer, transfer_created = ChuyenTiep.objects.get_or_create(van_ban_duyet=approval)
        self._track(role_bucket, "ChuyenTiep", transfer_created)
        _, detail_created = ChuyenTiepChiTiet.objects.get_or_create(
            chuyen_tiep=transfer,
            nguoi_dung=self.profiles["specialist"],
            defaults={"phong_ban": self.profiles["specialist"].phong_ban},
        )
        self._track(role_bucket, "ChuyenTiepChiTiet", detail_created)

    def ensure_receivers(self, document, index):
        department = self.departments[("hn", "ke_toan")]
        _, dept_created = NoiNhanVanBan.objects.get_or_create(
            van_ban=document,
            phong_ban=department,
            don_vi_ngoai=None,
        )
        self._track("VAN_THU", "NoiNhanVanBan", dept_created)

        outside_unit = self.outside_units[(index - 1) % len(self.outside_units)]
        _, outside_created = NoiNhanVanBan.objects.get_or_create(
            van_ban=document,
            phong_ban=None,
            don_vi_ngoai=outside_unit,
        )
        self._track("VAN_THU", "NoiNhanVanBan", outside_created)

    def ensure_demo_file(self, relative_path, title):
        if not default_storage.exists(relative_path):
            content = (
                "%PDF-1.4\n"
                f"1 0 obj << /Title ({title}) >> endobj\n"
                "2 0 obj << /Length 44 >> stream\n"
                f"{title}\n"
                "endstream endobj\n"
                "%%EOF\n"
            ).encode("utf-8")
            default_storage.save(relative_path, ContentFile(content))
            self.stats["FILES:created"] += 1
        return relative_path

    def file_size(self, relative_path):
        try:
            return default_storage.size(relative_path)
        except Exception:
            return 0

    def _choice(self, choices, index):
        return choices[(index - 1) % len(choices)][0]

    def _track(self, role, model_name, created):
        if created:
            self.stats[f"{role}:{model_name}"] += 1

    def print_summary(self):
        self.command.stdout.write("")
        self.command.stdout.write(self.command.style.SUCCESS("Seed role-based data hoàn tất."))
        self.command.stdout.write(
            "Lưu ý: core.BanHanhChiTiep không tồn tại trong schema hiện tại; "
            "command đã dùng core.NoiNhanVanBan cho dữ liệu nơi nhận/phát hành."
        )
        self.command.stdout.write("")
        self.command.stdout.write("=== Dữ liệu tạo mới theo role ===")
        for role in ("ADMIN", "LANH_DAO", "VAN_THU", "CHUYEN_VIEN"):
            role_stats = {
                key.split(":", 1)[1]: value
                for key, value in sorted(self.stats.items())
                if key.startswith(f"{role}:")
            }
            total = sum(role_stats.values())
            self.command.stdout.write(f"{role}: {total} record mới")
            for model_name, value in role_stats.items():
                self.command.stdout.write(f" - {model_name}: {value}")

        self.command.stdout.write(f"FILES: {self.stats.get('FILES:created', 0)} file demo mới")
        self.command.stdout.write("")
        self.command.stdout.write("=== Tài khoản demo chính ===")
        self.command.stdout.write("admin.demo / ROLE_SEED_PASSWORD hoặc 123")
        self.command.stdout.write("lanhdao.demo / ROLE_SEED_PASSWORD hoặc 123")
        self.command.stdout.write("vanthu.demo / ROLE_SEED_PASSWORD hoặc 123")
        self.command.stdout.write("chuyenvien.demo / ROLE_SEED_PASSWORD hoặc 123")
