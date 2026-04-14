from collections import defaultdict
from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.role_groups import ensure_role_groups, sync_user_role_group
from apps.core.models import (
    BanHanh,
    BanHanhChiTiep,
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
    PheDuyetCongViec,
    PhanCongCongViec,
    PhongBan,
    PhongXemHoSo,
    VanBan,
    VanBanDuyet,
    VanBanHoanTra,
    VanBanLienQuan,
)
from apps.quanlyvanbanden.models import TepVanBanDen, VanBanDen, VanBanDenChuyenTiep

User = get_user_model()

DEMO_PASSWORD = "Admin@123"
SEED_FILE_PREFIX = "seed"
DEFAULT_RECORD_COUNT = 7
DEFAULT_OUTGOING_COUNT = 11
DEFAULT_INCOMING_COUNT = 11
DEFAULT_TASK_COUNT = 13

DEPT_BAN_GIAM_DOC = VanBan.DON_VI_SOAN_THAO_CHOICES[0][0]
DEPT_KE_TOAN = VanBan.DON_VI_SOAN_THAO_CHOICES[1][0]
DEPT_KIEM_TOAN = VanBan.DON_VI_SOAN_THAO_CHOICES[2][0]
DEPT_TU_VAN_THUE = VanBan.DON_VI_SOAN_THAO_CHOICES[3][0]
DEPT_HANH_CHINH = VanBan.DON_VI_SOAN_THAO_CHOICES[4][0]
DEPT_DAO_TAO = VanBan.DON_VI_SOAN_THAO_CHOICES[5][0]
DEPT_VAN_THU = "Văn thư"

PHAN_LOAI_VAN_BAN_DI = VanBan.PHAN_LOAI_CHOICES[0][0]
VAN_BAN_STATUS_CHO_XU_LY = VanBan.TRANG_THAI_CHOICES[0][0]
VAN_BAN_STATUS_HOAN_TRA = VanBan.TRANG_THAI_CHOICES[2][0]
VAN_BAN_STATUS_CHO_BAN_HANH = VanBan.TRANG_THAI_CHOICES[4][0]
VAN_BAN_STATUS_DA_BAN_HANH = VanBan.TRANG_THAI_CHOICES[5][0]

HINH_THUC_CONG_VAN = VanBan.HINH_THUC_CHOICES[0][0]
HINH_THUC_QUYET_DINH = VanBan.HINH_THUC_CHOICES[1][0]
HINH_THUC_THONG_BAO = VanBan.HINH_THUC_CHOICES[2][0]
HINH_THUC_BAO_CAO = VanBan.HINH_THUC_CHOICES[3][0]
HINH_THUC_PHIEU_TRINH = VanBan.HINH_THUC_CHOICES[10][0]

LOAI_VAN_BAN_DIEU_HANH = VanBan.LOAI_VAN_BAN_CHOICES[0][0]
LOAI_VAN_BAN_TAI_CHINH = VanBan.LOAI_VAN_BAN_CHOICES[1][0]
LOAI_VAN_BAN_KE_HOACH = VanBan.LOAI_VAN_BAN_CHOICES[6][0]
LOAI_BAO_CAO_TIEN_DO = VanBan.LOAI_VAN_BAN_CHOICES[8][0]

DO_KHAN_HOA_TOC = VanBan.DO_KHAN_CHOICES[0][0]
DO_KHAN_KHAN = VanBan.DO_KHAN_CHOICES[1][0]
DO_KHAN_BINH_THUONG = VanBan.DO_KHAN_CHOICES[2][0]

DO_MAT_BINH_THUONG = VanBan.DO_MAT_CHOICES[0][0]
DO_MAT_MAT = VanBan.DO_MAT_CHOICES[1][0]
DO_MAT_TUYET_MAT = VanBan.DO_MAT_CHOICES[2][0]

HO_SO_BAO_QUAN_5_NAM = HoSoVanBan.THOI_GIAN_BAO_QUAN_CHOICES[1][0]
HO_SO_BAO_QUAN_10_NAM = HoSoVanBan.THOI_GIAN_BAO_QUAN_CHOICES[2][0]
HO_SO_BAO_QUAN_TAM_THOI = HoSoVanBan.THOI_GIAN_BAO_QUAN_CHOICES[4][0]
HO_SO_TRANG_THAI_HIEN_HANH = HoSoVanBan.TRANG_THAI_CHOICES[0][0]
HO_SO_TRANG_THAI_LUU_TRU = HoSoVanBan.TRANG_THAI_CHOICES[1][0]

DEPARTMENT_LABELS = {
    "ban_giam_doc": DEPT_BAN_GIAM_DOC,
    "van_thu": DEPT_VAN_THU,
    "ke_toan": DEPT_KE_TOAN,
    "kiem_toan": DEPT_KIEM_TOAN,
    "tu_van_thue": DEPT_TU_VAN_THUE,
    "hanh_chinh": DEPT_HANH_CHINH,
    "dao_tao": DEPT_DAO_TAO,
}

BRANCH_SPECS = {
    "hn": {
        "name": "Trụ sở Hà Nội",
        "departments": ["ban_giam_doc", "van_thu", "ke_toan", "kiem_toan", "hanh_chinh"],
    },
    "dn": {
        "name": "Chi nhánh Đà Nẵng",
        "departments": ["ban_giam_doc", "van_thu", "kiem_toan", "hanh_chinh"],
    },
    "hcm": {
        "name": "Chi nhánh TP.HCM",
        "departments": ["ban_giam_doc", "van_thu", "tu_van_thue", "ke_toan", "dao_tao"],
    },
}

OUTSIDE_UNIT_SPECS = [
    {
        "key": "so_tai_chinh_hn",
        "name": "Sở Tài chính Hà Nội",
        "email": "sotc.hn.demo@example.com",
        "phone": "02438251234",
        "address": "15 Tràng Thi, Hoàn Kiếm, Hà Nội",
    },
    {
        "key": "cuc_thue_hcm",
        "name": "Cục Thuế TP.HCM",
        "email": "cucthue.hcm.demo@example.com",
        "phone": "02839301234",
        "address": "63 Vũ Tông Phan, Quận 2, TP.HCM",
    },
    {
        "key": "cong_nghe_sao_viet",
        "name": "Công ty Cổ phần Công nghệ Sao Việt",
        "email": "saoviet.demo@example.com",
        "phone": "02836281234",
        "address": "25 Nguyễn Hữu Cảnh, Bình Thạnh, TP.HCM",
    },
]

USER_SPECS = [
    {
        "key": "admin",
        "username": "admin.demo",
        "email": "admin.demo@example.com",
        "full_name": "Quản trị Demo",
        "phone": "0909000001",
        "role": User.Role.ADMIN,
        "branch": "hn",
        "department": "ban_giam_doc",
        "job_title": "Quản trị hệ thống",
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "key": "lanhdao_hn",
        "username": "lanhdao.hn",
        "email": "lanhdao.hn@example.com",
        "full_name": "Nguyễn Minh An",
        "phone": "0909000002",
        "role": User.Role.LANH_DAO,
        "branch": "hn",
        "department": "ban_giam_doc",
        "job_title": "Giám đốc điều hành Hà Nội",
    },
    {
        "key": "lanhdao_hcm",
        "username": "lanhdao.hcm",
        "email": "lanhdao.hcm@example.com",
        "full_name": "Trần Quang Phúc",
        "phone": "0909000003",
        "role": User.Role.LANH_DAO,
        "branch": "hcm",
        "department": "ban_giam_doc",
        "job_title": "Giám đốc điều hành TP.HCM",
    },
    {
        "key": "vanthu_hn",
        "username": "vanthu.hn",
        "email": "vanthu.hn@example.com",
        "full_name": "Lê Thu Hà",
        "phone": "0909000004",
        "role": User.Role.VAN_THU,
        "branch": "hn",
        "department": "van_thu",
        "job_title": "Văn thư tổng hợp Hà Nội",
    },
    {
        "key": "vanthu_hcm",
        "username": "vanthu.hcm",
        "email": "vanthu.hcm@example.com",
        "full_name": "Phạm Thu Trang",
        "phone": "0909000005",
        "role": User.Role.VAN_THU,
        "branch": "hcm",
        "department": "van_thu",
        "job_title": "Văn thư tổng hợp TP.HCM",
    },
    {
        "key": "lanhdao_dn",
        "username": "lanhdao.dn",
        "email": "lanhdao.dn@example.com",
        "full_name": "Ngô Quốc Bảo",
        "phone": "0909000012",
        "role": User.Role.LANH_DAO,
        "branch": "dn",
        "department": "ban_giam_doc",
        "job_title": "Giám đốc điều hành Đà Nẵng",
    },
    {
        "key": "vanthu_dn",
        "username": "vanthu.dn",
        "email": "vanthu.dn@example.com",
        "full_name": "Tạ Ngọc Hân",
        "phone": "0909000013",
        "role": User.Role.VAN_THU,
        "branch": "dn",
        "department": "van_thu",
        "job_title": "Văn thư tổng hợp Đà Nẵng",
    },
    {
        "key": "cv_ketoan_hn",
        "username": "cv.ketoan.hn",
        "email": "cv.ketoan.hn@example.com",
        "full_name": "Đỗ Anh Khoa",
        "phone": "0909000006",
        "role": User.Role.CHUYEN_VIEN,
        "branch": "hn",
        "department": "ke_toan",
        "job_title": "Chuyên viên kế toán",
    },
    {
        "key": "cv_kiemtoan_hn",
        "username": "cv.kiemtoan.hn",
        "email": "cv.kiemtoan.hn@example.com",
        "full_name": "Nguyễn Mai Linh",
        "phone": "0909000007",
        "role": User.Role.CHUYEN_VIEN,
        "branch": "hn",
        "department": "kiem_toan",
        "job_title": "Chuyên viên kiểm toán",
    },
    {
        "key": "cv_hanhchinh_hn",
        "username": "cv.hanhchinh.hn",
        "email": "cv.hanhchinh.hn@example.com",
        "full_name": "Phan Hoài Nam",
        "phone": "0909000008",
        "role": User.Role.CHUYEN_VIEN,
        "branch": "hn",
        "department": "hanh_chinh",
        "job_title": "Chuyên viên hành chính",
    },
    {
        "key": "cv_thue_hcm",
        "username": "cv.thue.hcm",
        "email": "cv.thue.hcm@example.com",
        "full_name": "Vũ Bảo Ngọc",
        "phone": "0909000009",
        "role": User.Role.CHUYEN_VIEN,
        "branch": "hcm",
        "department": "tu_van_thue",
        "job_title": "Chuyên viên tư vấn thuế",
    },
    {
        "key": "cv_ketoan_hcm",
        "username": "cv.ketoan.hcm",
        "email": "cv.ketoan.hcm@example.com",
        "full_name": "Bùi Khánh Duy",
        "phone": "0909000010",
        "role": User.Role.CHUYEN_VIEN,
        "branch": "hcm",
        "department": "ke_toan",
        "job_title": "Chuyên viên kế toán chi nhánh",
    },
    {
        "key": "cv_kiemtoan_dn",
        "username": "cv.kiemtoan.dn",
        "email": "cv.kiemtoan.dn@example.com",
        "full_name": "Trịnh Đức Nam",
        "phone": "0909000011",
        "role": User.Role.CHUYEN_VIEN,
        "branch": "dn",
        "department": "kiem_toan",
        "job_title": "Chuyên viên kiểm toán Đà Nẵng",
    },
]


class Command(BaseCommand):
    help = "Tạo dữ liệu demo đầy đủ để test tay toàn bộ hệ thống quản lý văn bản."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count-per-feature",
            type=int,
            default=None,
            help="Thiết lập nhanh cùng một số lượng cho 4 nhóm: hồ sơ, văn bản đến, văn bản đi, công việc.",
        )
        parser.add_argument(
            "--record-count",
            type=int,
            default=DEFAULT_RECORD_COUNT,
            help="Số lượng hồ sơ văn bản cần tạo.",
        )
        parser.add_argument(
            "--outgoing-count",
            type=int,
            default=DEFAULT_OUTGOING_COUNT,
            help="Số lượng văn bản đi cần tạo.",
        )
        parser.add_argument(
            "--incoming-count",
            type=int,
            default=DEFAULT_INCOMING_COUNT,
            help="Số lượng văn bản đến cần tạo.",
        )
        parser.add_argument(
            "--task-count",
            type=int,
            default=DEFAULT_TASK_COUNT,
            help="Số lượng công việc cần tạo.",
        )

    def handle(self, *args, **options):
        self._configure_output_encoding()
        self.stats = defaultdict(lambda: {"created": 0, "reused": 0})
        self.created_seed_files = 0
        self.demo_accounts = []
        self.role_groups = ensure_role_groups(User)
        self.today = timezone.localdate()
        self.now = timezone.now()
        uniform_target = options.get("count_per_feature")
        self.record_count = max(1, options["record_count"])
        self.outgoing_count = max(1, options["outgoing_count"])
        self.incoming_count = max(1, options["incoming_count"])
        self.task_count = max(1, options["task_count"])
        if uniform_target:
            target = max(1, uniform_target)
            self.record_count = target
            self.outgoing_count = target
            self.incoming_count = target
            self.task_count = target
        self.user_spec_map = {spec["key"]: spec for spec in USER_SPECS}
        self.specialist_specs = [
            spec for spec in USER_SPECS if spec["role"] == User.Role.CHUYEN_VIEN
        ]
        self.specialist_keys = [spec["key"] for spec in self.specialist_specs]
        self.specialist_keys_by_branch = defaultdict(list)
        for spec in self.specialist_specs:
            self.specialist_keys_by_branch[spec["branch"]].append(spec["key"])
        self.leader_keys_by_branch = {
            spec["branch"]: spec["key"]
            for spec in USER_SPECS
            if spec["role"] == User.Role.LANH_DAO
        }
        self.clerk_keys_by_branch = {
            spec["branch"]: spec["key"]
            for spec in USER_SPECS
            if spec["role"] == User.Role.VAN_THU
        }

        self.stdout.write("Đang seed dữ liệu demo cho hệ thống...")

        with transaction.atomic():
            self.branches = self._seed_branches()
            self.departments = self._seed_departments()
            self.outside_units = self._seed_outside_units()
            self.users, self.core_users = self._seed_users()
            self._assign_department_heads()
            self.records = self._seed_records()
            self.outgoing_docs = self._seed_outgoing_documents()
            self.incoming_docs = self._seed_incoming_documents()
            self.tasks = self._seed_tasks()

        self.stdout.write(self.style.SUCCESS("Seed dữ liệu demo hoàn tất."))
        self._print_account_summary()
        self._print_model_summary()

    def _configure_output_encoding(self):
        for wrapper in (self.stdout, self.stderr):
            stream = getattr(wrapper, "_out", None)
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="backslashreplace")

    def _track(self, label, created):
        bucket = self.stats[label]
        bucket["created" if created else "reused"] += 1

    def _upsert_one(self, model, label, lookup, defaults=None):
        defaults = defaults or {}
        obj = model.objects.filter(**lookup).order_by("pk").first()
        created = obj is None

        if obj is None:
            obj = model.objects.create(**lookup, **defaults)
        else:
            changed_fields = []
            for field_name, value in defaults.items():
                current_value = getattr(obj, field_name)
                if current_value != value:
                    setattr(obj, field_name, value)
                    changed_fields.append(field_name)
            if changed_fields:
                obj.save(update_fields=changed_fields)

        self._track(label, created)
        return obj

    def _seed_branches(self):
        branches = {}
        for branch_key, spec in BRANCH_SPECS.items():
            branches[branch_key] = self._upsert_one(
                ChiNhanh,
                "ChiNhanh",
                {"ten_chi_nhanh": spec["name"]},
            )
        return branches

    def _seed_departments(self):
        departments = {}
        for branch_key, spec in BRANCH_SPECS.items():
            branch = self.branches[branch_key]
            for dept_key in spec["departments"]:
                departments[(branch_key, dept_key)] = self._upsert_one(
                    PhongBan,
                    "PhongBan",
                    {
                        "chi_nhanh": branch,
                        "ten_phong_ban": DEPARTMENT_LABELS[dept_key],
                    },
                )
        return departments

    def _seed_outside_units(self):
        units = {}
        for spec in OUTSIDE_UNIT_SPECS:
            units[spec["key"]] = self._upsert_one(
                DonViNgoai,
                "DonViNgoai",
                {"email": spec["email"]},
                {
                    "ten_don_vi": spec["name"],
                    "dia_chi": spec["address"],
                    "so_dien_thoai": spec["phone"],
                },
            )
        return units

    def _seed_users(self):
        users = {}
        core_users = {}

        for spec in USER_SPECS:
            branch = self.branches[spec["branch"]]
            department = self.departments[(spec["branch"], spec["department"])]

            user = User.objects.filter(username=spec["username"]).first()
            created = user is None

            if user is None:
                user = User(username=spec["username"])

            user.email = spec["email"]
            user.ho_va_ten = spec["full_name"]
            user.sdt = spec["phone"]
            user.role = spec["role"]
            user.chuc_vu = spec["job_title"]
            user.chi_nhanh = branch
            user.phong_ban = department
            user.is_active = True
            user.is_staff = spec.get("is_staff", spec["role"] == User.Role.ADMIN)
            user.is_superuser = spec.get("is_superuser", False)
            user.set_password(DEMO_PASSWORD)
            user.save()

            sync_user_role_group(user, role_groups=self.role_groups)

            core_profile_before = NguoiDung.objects.filter(
                Q(tai_khoan=user) | Q(email__iexact=spec["email"])
            ).first()
            core_profile = user.sync_core_profile()
            core_created = core_profile_before is None

            core_profile.ho_va_ten = spec["full_name"]
            core_profile.email = spec["email"]
            core_profile.sdt = spec["phone"]
            core_profile.phong_ban = department
            core_profile.chuc_vu = User.ROLE_CORE_CHUC_VU_MAP.get(
                spec["role"],
                NguoiDung.ChucVu.CHUYEN_VIEN,
            )
            core_profile.save()

            self._track("Customer", created)
            self._track("NguoiDung", core_created)

            users[spec["key"]] = user
            core_users[spec["key"]] = core_profile
            self.demo_accounts.append(user)

        return users, core_users

    def _assign_department_heads(self):
        head_specs = [
            (("hn", "ban_giam_doc"), "lanhdao_hn"),
            (("hn", "van_thu"), "vanthu_hn"),
            (("hn", "ke_toan"), "lanhdao_hn"),
            (("hn", "kiem_toan"), "lanhdao_hn"),
            (("hn", "hanh_chinh"), "lanhdao_hn"),
            (("hcm", "ban_giam_doc"), "lanhdao_hcm"),
            (("hcm", "van_thu"), "vanthu_hcm"),
            (("hcm", "tu_van_thue"), "lanhdao_hcm"),
            (("hcm", "ke_toan"), "lanhdao_hcm"),
            (("hcm", "dao_tao"), "lanhdao_hcm"),
            (("dn", "ban_giam_doc"), "lanhdao_dn"),
            (("dn", "van_thu"), "vanthu_dn"),
            (("dn", "kiem_toan"), "lanhdao_dn"),
            (("dn", "hanh_chinh"), "lanhdao_dn"),
        ]

        for (branch_key, dept_key), user_key in head_specs:
            department = self.departments[(branch_key, dept_key)]
            head = self.core_users[user_key]
            if department.truong_phong_id != head.pk:
                department.truong_phong = head
                department.save(update_fields=["truong_phong"])

    def _expand_specs_to_target(self, base_specs, target_count, builder):
        extra_needed = max(0, target_count - len(base_specs))
        if extra_needed:
            base_specs.extend(builder(extra_needed))
        return base_specs

    def _branch_name(self, branch_key):
        return self.branches[branch_key].ten_chi_nhanh

    def _specialists_for_branch(self, branch_key):
        specialists = self.specialist_keys_by_branch.get(branch_key) or []
        return specialists or self.specialist_keys

    def _drafting_unit_for_user_key(self, user_key):
        department_key = self.user_spec_map[user_key]["department"]
        return DEPARTMENT_LABELS.get(department_key, DEPT_BAN_GIAM_DOC)

    def _build_bulk_record_specs(self, extra_needed):
        topics = [
            "điều hành văn bản nội bộ",
            "tiếp nhận và xử lý văn bản đến",
            "lưu trữ hồ sơ chuyên môn",
            "phối hợp ban hành văn bản",
            "kiểm tra tiến độ xử lý công việc",
        ]
        branch_cycle = ["hn", "hcm", "dn"]
        specs = []

        for index in range(1, extra_needed + 1):
            branch_key = branch_cycle[(index - 1) % len(branch_cycle)]
            creator_key = self.clerk_keys_by_branch[branch_key]
            specialist_keys = self._specialists_for_branch(branch_key)
            topic = topics[(index - 1) % len(topics)]
            status = HO_SO_TRANG_THAI_LUU_TRU if index % 5 == 0 else HO_SO_TRANG_THAI_HIEN_HANH
            retention = (
                HO_SO_BAO_QUAN_TAM_THOI
                if index % 5 == 0
                else HO_SO_BAO_QUAN_10_NAM if index % 2 == 0 else HO_SO_BAO_QUAN_5_NAM
            )
            retention_years = 3 if retention == HO_SO_BAO_QUAN_TAM_THOI else 10 if retention == HO_SO_BAO_QUAN_10_NAM else 5
            handler_keys = specialist_keys[:2] if len(specialist_keys) > 1 else specialist_keys
            primary_department_key = self.user_spec_map[specialist_keys[0]]["department"]

            specs.append(
                {
                    "key": f"hoso_bulk_{index:03d}",
                    "code": f"HS-SEED-BULK-{index:03d}",
                    "title": f"Hồ sơ {topic} - {self._branch_name(branch_key)} - đợt {index:03d}",
                    "creator": creator_key,
                    "retention": retention,
                    "retention_years": retention_years,
                    "status": status,
                    "description": f"Hồ sơ seed số lượng lớn phục vụ test tay chức năng hồ sơ tại {self._branch_name(branch_key).lower()}.",
                    "departments": [
                        (branch_key, "ban_giam_doc"),
                        (branch_key, "van_thu"),
                        (branch_key, primary_department_key),
                    ],
                    "handlers": handler_keys,
                }
            )

        return specs

    def _build_bulk_outgoing_specs(self, extra_needed):
        topics = [
            ("rà soát văn bản điều hành", HINH_THUC_CONG_VAN, LOAI_VAN_BAN_DIEU_HANH),
            ("đề xuất ngân sách số hóa", HINH_THUC_PHIEU_TRINH, LOAI_VAN_BAN_TAI_CHINH),
            ("thông báo phân công xử lý", HINH_THUC_THONG_BAO, LOAI_VAN_BAN_DIEU_HANH),
            ("ban hành kế hoạch kiểm tra", HINH_THUC_QUYET_DINH, LOAI_VAN_BAN_KE_HOACH),
            ("báo cáo tiến độ xử lý", HINH_THUC_BAO_CAO, LOAI_BAO_CAO_TIEN_DO),
        ]
        priorities = [DO_KHAN_BINH_THUONG, DO_KHAN_KHAN, DO_KHAN_HOA_TOC]
        privacies = [DO_MAT_BINH_THUONG, DO_MAT_MAT, DO_MAT_TUYET_MAT]
        status_cycle = [
            VAN_BAN_STATUS_CHO_XU_LY,
            VAN_BAN_STATUS_HOAN_TRA,
            VAN_BAN_STATUS_CHO_BAN_HANH,
            VAN_BAN_STATUS_DA_BAN_HANH,
            VAN_BAN_STATUS_CHO_XU_LY,
        ]
        record_keys = list(self.records.keys())
        outside_keys = list(self.outside_units.keys())
        specs = []

        for index in range(1, extra_needed + 1):
            specialist_key = self.specialist_keys[(index - 1) % len(self.specialist_keys)]
            branch_key = self.user_spec_map[specialist_key]["branch"]
            leader_key = self.leader_keys_by_branch.get(branch_key, "lanhdao_hn")
            clerk_key = self.clerk_keys_by_branch.get(branch_key, "vanthu_hn")
            topic, form, doc_type = topics[(index - 1) % len(topics)]
            status = status_cycle[(index - 1) % len(status_cycle)]
            specialists_in_branch = self._specialists_for_branch(branch_key)
            related_targets = specialists_in_branch[:2] if len(specialists_in_branch) > 1 else specialists_in_branch

            spec = {
                "key": f"vbdi_bulk_{index:03d}",
                "code": f"SEED/VBDI-BULK-{index:03d}",
                "summary": f"{topic.capitalize()} tại {self._branch_name(branch_key)} đợt {index:03d}",
                "creator": specialist_key,
                "leader": leader_key,
                "record": record_keys[(index - 1) % len(record_keys)],
                "status": status,
                "form": form,
                "doc_type": doc_type,
                "drafting_unit": self._drafting_unit_for_user_key(specialist_key),
                "issue_date": self.today - timedelta(days=(index % 20) + 1),
                "received_date": self.today - timedelta(days=index % 18),
                "deadline": self.today + timedelta(days=(index % 10) + 2),
                "priority": priorities[(index - 1) % len(priorities)],
                "privacy": privacies[(index - 1) % len(privacies)],
                "note": f"Văn bản đi seed số lượng lớn để test role và bộ lọc. Mã đợt {index:03d}.",
                "related_files": [
                    {
                        "stem": f"vbdi-bulk-{index:03d}-phu-luc",
                        "title": f"Phụ lục văn bản đi bulk {index:03d}",
                    }
                ],
            }

            if status == VAN_BAN_STATUS_HOAN_TRA:
                spec["return_note"] = f"Lãnh đạo yêu cầu cập nhật lại nội dung và phụ lục cho văn bản bulk {index:03d}."
            if status in {VAN_BAN_STATUS_CHO_BAN_HANH, VAN_BAN_STATUS_DA_BAN_HANH}:
                spec["approval_clerk"] = clerk_key
            if status == VAN_BAN_STATUS_CHO_BAN_HANH:
                spec["forward_targets"] = related_targets
            if status == VAN_BAN_STATUS_DA_BAN_HANH:
                spec["issue_targets"] = {
                    "departments": [
                        (branch_key, "van_thu"),
                        (branch_key, self.user_spec_map[specialist_key]["department"]),
                    ],
                    "outside_units": [outside_keys[(index - 1) % len(outside_keys)]],
                }

            specs.append(spec)

        return specs

    def _build_bulk_incoming_specs(self, extra_needed):
        topics = [
            ("đề nghị phối hợp rà soát hồ sơ", VanBanDen.LoaiVanBan.CONG_VAN, VanBanDen.HinhThucVanBan.CONG_VAN),
            ("thông báo lịch kiểm tra", VanBanDen.LoaiVanBan.THONG_BAO, VanBanDen.HinhThucVanBan.THONG_BAO),
            ("yêu cầu bổ sung hồ sơ", VanBanDen.LoaiVanBan.CONG_VAN, VanBanDen.HinhThucVanBan.TO_TRINH),
            ("kế hoạch kiểm tra nội bộ", VanBanDen.LoaiVanBan.KE_HOACH, VanBanDen.HinhThucVanBan.THONG_BAO),
            ("báo cáo tiến độ triển khai", VanBanDen.LoaiVanBan.BAO_CAO, VanBanDen.HinhThucVanBan.THONG_BAO),
        ]
        status_cycle = [
            VanBanDen.TrangThai.CHO_XU_LY,
            VanBanDen.TrangThai.DA_XU_LY,
            VanBanDen.TrangThai.HOAN_TRA,
            VanBanDen.TrangThai.XEM_DE_BIET,
            VanBanDen.TrangThai.DA_XU_LY,
        ]
        priorities = [
            VanBanDen.DoKhan.BINH_THUONG,
            VanBanDen.DoKhan.KHAN,
            VanBanDen.DoKhan.HOA_TOC,
        ]
        privacies = [
            VanBanDen.DoMat.BINH_THUONG,
            VanBanDen.DoMat.MAT,
            VanBanDen.DoMat.TOI_MAT,
        ]
        branch_cycle = ["hn", "hcm", "dn"]
        outside_keys = list(self.outside_units.keys())
        specs = []

        for index in range(1, extra_needed + 1):
            branch_key = branch_cycle[(index - 1) % len(branch_cycle)]
            creator_key = self.clerk_keys_by_branch[branch_key]
            leader_key = self.leader_keys_by_branch[branch_key]
            specialists = self._specialists_for_branch(branch_key)
            topic, doc_type, form = topics[(index - 1) % len(topics)]
            status = status_cycle[(index - 1) % len(status_cycle)]

            spec = {
                "key": f"vbden_bulk_{index:03d}",
                "code": f"SEED-VBDEN-BULK-{index:03d}",
                "issuing_unit": self.outside_units[outside_keys[(index - 1) % len(outside_keys)]].ten_don_vi,
                "summary": f"{topic.capitalize()} - {self._branch_name(branch_key)} - đợt {index:03d}",
                "creator": creator_key,
                "leader": leader_key,
                "status": status,
                "document_type": doc_type,
                "form": form,
                "issue_date": self.today - timedelta(days=(index % 22) + 2),
                "received_date": self.today - timedelta(days=index % 20),
                "deadline": self.today + timedelta(days=(index % 9) + 2),
                "priority": priorities[(index - 1) % len(priorities)],
                "privacy": privacies[(index - 1) % len(privacies)],
                "field": f"Lĩnh vực tiếp nhận {index:03d}",
                "processing_note": f"Văn bản đến bulk {index:03d} phục vụ test phân quyền và lọc trạng thái.",
                "forward_to": [],
            }

            if status == VanBanDen.TrangThai.DA_XU_LY:
                spec["forward_to"] = specialists[:2] if len(specialists) > 1 else specialists
            if status == VanBanDen.TrangThai.HOAN_TRA:
                spec["return_reason"] = f"Lãnh đạo yêu cầu văn thư bổ sung nội dung trình cho văn bản đến bulk {index:03d}."
                spec["return_date"] = self.today - timedelta(days=1)

            specs.append(spec)

        return specs

    def _build_bulk_task_specs(self, extra_needed):
        status_cycle = [
            CongViec.TrangThai.CHO_XU_LY,
            CongViec.TrangThai.CHO_DUYET,
            CongViec.TrangThai.DA_HOAN_THANH,
            CongViec.TrangThai.HOAN_TRA_CV,
            CongViec.TrangThai.HOAN_TRA_LD,
        ]
        topics = [
            "Rà soát văn bản trình ký",
            "Tổng hợp báo cáo xử lý",
            "Chuẩn bị phát hành văn bản",
            "Bổ sung hồ sơ giải trình",
            "Theo dõi tiến độ phối hợp",
        ]
        outgoing_doc_keys = list(self.outgoing_docs.keys())
        specs = []

        for index in range(1, extra_needed + 1):
            assignee_key = self.specialist_keys[(index - 1) % len(self.specialist_keys)]
            branch_key = self.user_spec_map[assignee_key]["branch"]
            assigner_key = self.leader_keys_by_branch.get(branch_key, "lanhdao_hn")
            collaborators = [
                key for key in self._specialists_for_branch(branch_key) if key != assignee_key
            ]
            status = status_cycle[(index - 1) % len(status_cycle)]
            source = (
                CongViec.NguonGiao.VAN_BAN_DI
                if index % 2 == 0
                else CongViec.NguonGiao.VAN_BAN_DEN
            )
            result_text = ""
            if status in {
                CongViec.TrangThai.CHO_DUYET,
                CongViec.TrangThai.DA_HOAN_THANH,
                CongViec.TrangThai.HOAN_TRA_CV,
            }:
                result_text = f"Đã xử lý công việc bulk {index:03d}, đính kèm báo cáo và kiến nghị tiếp theo."

            spec = {
                "key": f"task_bulk_{index:03d}",
                "title": f"[SEED-TASK-BULK-{index:03d}] {topics[(index - 1) % len(topics)]}",
                "content": f"Công việc bulk {index:03d} dùng để test danh sách, chi tiết và phân quyền theo vai trò.",
                "assigner": assigner_key,
                "assignee": assignee_key,
                "collaborators": collaborators[:1],
                "document": outgoing_doc_keys[(index - 1) % len(outgoing_doc_keys)] if source == CongViec.NguonGiao.VAN_BAN_DI else None,
                "source": source,
                "status": status,
                "start_offset": -(index % 7),
                "deadline_offset": (index % 8) + 2,
                "requires_approval": status != CongViec.TrangThai.DA_HOAN_THANH or index % 2 == 0,
                "note": f"Ghi chú seed cho công việc bulk {index:03d}.",
                "result": result_text,
            }

            if status == CongViec.TrangThai.DA_HOAN_THANH and spec["requires_approval"]:
                spec["approved"] = True
            if status == CongViec.TrangThai.HOAN_TRA_CV:
                spec["return_note"] = f"Lãnh đạo hoàn trả công việc bulk {index:03d} để chuyên viên cập nhật lại kết quả."
                spec["returned_by"] = assigner_key
            if status == CongViec.TrangThai.HOAN_TRA_LD:
                spec["return_note"] = f"Chuyên viên xin điều chỉnh phạm vi xử lý cho công việc bulk {index:03d}."
                spec["returned_by"] = assignee_key

            specs.append(spec)

        return specs

    def _seed_records(self):
        records = {}
        specs = [
            {
                "key": "hoso_hn_dieu_hanh",
                "code": "HS-SEED-2026-001",
                "title": "Hồ sơ văn bản điều hành quý II/2026",
                "creator": "vanthu_hn",
                "retention": HO_SO_BAO_QUAN_5_NAM,
                "retention_years": 5,
                "status": HO_SO_TRANG_THAI_HIEN_HANH,
                "description": "Hồ sơ mẫu phục vụ demo luồng văn bản đi và giao việc tại trụ sở Hà Nội.",
                "departments": [("hn", "ban_giam_doc"), ("hn", "van_thu"), ("hn", "ke_toan")],
                "handlers": ["cv_ketoan_hn", "cv_kiemtoan_hn"],
            },
            {
                "key": "hoso_hn_tiep_nhan",
                "code": "HS-SEED-2026-002",
                "title": "Hồ sơ tiếp nhận và xử lý văn bản đến Hà Nội",
                "creator": "vanthu_hn",
                "retention": HO_SO_BAO_QUAN_10_NAM,
                "retention_years": 10,
                "status": HO_SO_TRANG_THAI_HIEN_HANH,
                "description": "Dùng để gắn các văn bản đi phản hồi sau khi lãnh đạo xử lý văn bản đến.",
                "departments": [("hn", "ban_giam_doc"), ("hn", "kiem_toan"), ("hn", "hanh_chinh")],
                "handlers": ["cv_kiemtoan_hn", "cv_hanhchinh_hn"],
            },
            {
                "key": "hoso_hcm_dieu_hanh",
                "code": "HS-SEED-2026-003",
                "title": "Hồ sơ điều hành chi nhánh TP.HCM",
                "creator": "vanthu_hcm",
                "retention": HO_SO_BAO_QUAN_5_NAM,
                "retention_years": 5,
                "status": HO_SO_TRANG_THAI_HIEN_HANH,
                "description": "Dùng để demo hồ sơ văn bản, văn bản đi và công việc tại chi nhánh TP.HCM.",
                "departments": [("hcm", "ban_giam_doc"), ("hcm", "van_thu"), ("hcm", "tu_van_thue")],
                "handlers": ["cv_thue_hcm", "cv_ketoan_hcm"],
            },
            {
                "key": "hoso_luu_tru",
                "code": "HS-SEED-2025-ARCHIVE",
                "title": "Hồ sơ lưu trữ quyết định điều hành năm 2025",
                "creator": "vanthu_hcm",
                "retention": HO_SO_BAO_QUAN_TAM_THOI,
                "retention_years": 3,
                "status": HO_SO_TRANG_THAI_LUU_TRU,
                "description": "Hồ sơ mẫu ở trạng thái lưu trữ để demo danh sách và chi tiết hồ sơ.",
                "departments": [("hcm", "ban_giam_doc"), ("hcm", "van_thu"), ("dn", "kiem_toan")],
                "handlers": ["vanthu_hcm", "cv_kiemtoan_dn"],
            },
        ]
        specs = self._expand_specs_to_target(
            specs,
            self.record_count,
            self._build_bulk_record_specs,
        )

        for spec in specs:
            record = self._upsert_one(
                HoSoVanBan,
                "HoSoVanBan",
                {"ky_hieu_ho_so": spec["code"]},
                {
                    "tieu_de_ho_so": spec["title"],
                    "nguoi_tao": self.core_users[spec["creator"]],
                    "ngay_cap_nhat": self.today,
                    "thoi_gian_bao_quan": spec["retention"],
                    "so_nam_luu_tru": spec["retention_years"],
                    "trang_thai": spec["status"],
                    "mo_ta": spec["description"],
                },
            )

            self._sync_record_departments(
                record,
                [self.departments[item] for item in spec["departments"]],
            )
            self._sync_record_handlers(
                record,
                [self.core_users[user_key] for user_key in spec["handlers"]],
            )
            records[spec["key"]] = record

        return records

    def _sync_record_departments(self, record, departments):
        desired_ids = {department.pk for department in departments}
        PhongXemHoSo.objects.filter(ho_so_van_ban=record).exclude(
            phong_ban_id__in=desired_ids
        ).delete()

        for department in departments:
            _, created = PhongXemHoSo.objects.get_or_create(
                ho_so_van_ban=record,
                phong_ban=department,
            )
            self._track("PhongXemHoSo", created)

    def _sync_record_handlers(self, record, handlers):
        desired_ids = {handler.pk for handler in handlers}
        NguoiXuLyHoSo.objects.filter(ho_so_van_ban=record).exclude(
            nguoi_xu_ly_id__in=desired_ids
        ).delete()

        for handler in handlers:
            _, created = NguoiXuLyHoSo.objects.get_or_create(
                ho_so_van_ban=record,
                nguoi_xu_ly=handler,
            )
            self._track("NguoiXuLyHoSo", created)

    def _deadline(self, day_offset):
        target_date = self.today + timedelta(days=day_offset)
        return timezone.make_aware(datetime.combine(target_date, time(17, 0)))

    def _ensure_seed_file(self, relative_path, title, description=""):
        relative_path = relative_path.replace("\\", "/")
        if not default_storage.exists(relative_path):
            pdf_content = self._build_pdf_bytes(title, description)
            default_storage.save(relative_path, ContentFile(pdf_content))
            self.created_seed_files += 1
        return relative_path, default_storage.size(relative_path)

    def _build_pdf_bytes(self, title, description):
        text = f"{title} - {description}".strip()[:110]
        safe_text = (
            text.encode("latin-1", errors="replace")
            .decode("latin-1")
            .replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )
        stream = (
            "BT\n"
            "/F1 14 Tf\n"
            "40 780 Td\n"
            f"({safe_text}) Tj\n"
            "ET\n"
        )
        stream_bytes = stream.encode("latin-1")
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            (
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
            ),
            b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream_bytes), stream_bytes),
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]

        pdf_parts = [b"%PDF-1.4\n"]
        offsets = [0]
        current_length = len(pdf_parts[0])

        for index, obj in enumerate(objects, start=1):
            object_block = b"%d 0 obj\n%s\nendobj\n" % (index, obj)
            offsets.append(current_length)
            pdf_parts.append(object_block)
            current_length += len(object_block)

        xref_offset = current_length
        xref = [b"xref\n0 6\n", b"0000000000 65535 f \n"]
        for offset in offsets[1:]:
            xref.append(b"%010d 00000 n \n" % offset)

        trailer = b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n%d\n%%EOF\n" % xref_offset
        return b"".join(pdf_parts + xref + [trailer])

    def _seed_outgoing_documents(self):
        documents = {}
        specs = [
            {
                "key": "vbdi_001",
                "code": "SEED/VBDI-001",
                "summary": "Dự thảo công văn rà soát văn bản quý II/2026",
                "creator": "cv_ketoan_hn",
                "leader": "lanhdao_hn",
                "record": "hoso_hn_dieu_hanh",
                "status": VAN_BAN_STATUS_CHO_XU_LY,
                "form": HINH_THUC_CONG_VAN,
                "doc_type": LOAI_VAN_BAN_DIEU_HANH,
                "drafting_unit": DEPT_KE_TOAN,
                "issue_date": self.today - timedelta(days=5),
                "received_date": self.today - timedelta(days=4),
                "deadline": self.today + timedelta(days=5),
                "priority": DO_KHAN_KHAN,
                "privacy": DO_MAT_BINH_THUONG,
                "note": "Bản dự thảo chờ lãnh đạo xem xét và phê duyệt.",
                "related_files": [
                    {"stem": "vbdi-001-phu-luc", "title": "Phụ lục rà soát văn bản quý II"}
                ],
            },
            {
                "key": "vbdi_002",
                "code": "SEED/VBDI-002",
                "summary": "Tờ trình bổ sung ngân sách số hóa hồ sơ",
                "creator": "cv_kiemtoan_hn",
                "leader": "lanhdao_hn",
                "record": "hoso_hn_tiep_nhan",
                "status": VAN_BAN_STATUS_HOAN_TRA,
                "form": HINH_THUC_PHIEU_TRINH,
                "doc_type": LOAI_VAN_BAN_TAI_CHINH,
                "drafting_unit": DEPT_KIEM_TOAN,
                "issue_date": self.today - timedelta(days=9),
                "received_date": self.today - timedelta(days=8),
                "deadline": self.today + timedelta(days=3),
                "priority": DO_KHAN_HOA_TOC,
                "privacy": DO_MAT_MAT,
                "note": "Lãnh đạo đã hoàn trả để bổ sung căn cứ pháp lý và số liệu đối chiếu.",
                "return_note": "Bổ sung thuyết minh chi phí đầu tư và căn cứ pháp lý trước khi trình lại.",
                "related_files": [
                    {"stem": "vbdi-002-bang-so-lieu", "title": "Bảng tổng hợp chi phí số hóa hồ sơ"}
                ],
            },
            {
                "key": "vbdi_003",
                "code": "SEED/VBDI-003",
                "summary": "Thông báo phân công xử lý văn bản đến đợt 2",
                "creator": "cv_thue_hcm",
                "leader": "lanhdao_hcm",
                "record": "hoso_hcm_dieu_hanh",
                "status": VAN_BAN_STATUS_CHO_BAN_HANH,
                "form": HINH_THUC_THONG_BAO,
                "doc_type": LOAI_VAN_BAN_DIEU_HANH,
                "drafting_unit": DEPT_TU_VAN_THUE,
                "issue_date": self.today - timedelta(days=3),
                "received_date": self.today - timedelta(days=2),
                "deadline": self.today + timedelta(days=7),
                "priority": DO_KHAN_BINH_THUONG,
                "privacy": DO_MAT_BINH_THUONG,
                "note": "Đã được lãnh đạo phê duyệt và chuyển sang văn thư chờ ban hành.",
                "approval_clerk": "vanthu_hcm",
                "forward_targets": ["cv_thue_hcm", "cv_ketoan_hcm"],
                "related_files": [
                    {"stem": "vbdi-003-danh-sach", "title": "Danh sách đầu việc theo dõi sau khi ban hành"}
                ],
            },
            {
                "key": "vbdi_004",
                "code": "SEED/VBDI-004",
                "summary": "Quyết định ban hành quy chế phối hợp lưu trữ",
                "creator": "cv_ketoan_hcm",
                "leader": "lanhdao_hcm",
                "record": "hoso_luu_tru",
                "status": VAN_BAN_STATUS_DA_BAN_HANH,
                "form": HINH_THUC_QUYET_DINH,
                "doc_type": LOAI_VAN_BAN_KE_HOACH,
                "drafting_unit": DEPT_BAN_GIAM_DOC,
                "issue_date": self.today - timedelta(days=15),
                "received_date": self.today - timedelta(days=14),
                "deadline": self.today + timedelta(days=10),
                "priority": DO_KHAN_BINH_THUONG,
                "privacy": DO_MAT_BINH_THUONG,
                "note": "Đã ban hành cho các phòng ban nội bộ và đơn vị ngoài liên quan.",
                "approval_clerk": "vanthu_hcm",
                "issue_targets": {
                    "departments": [("hcm", "van_thu"), ("hcm", "dao_tao"), ("hn", "hanh_chinh")],
                    "outside_units": ["so_tai_chinh_hn", "cong_nghe_sao_viet"],
                },
                "related_files": [
                    {"stem": "vbdi-004-phu-luc", "title": "Phụ lục danh mục tài liệu lưu trữ"}
                ],
            },
            {
                "key": "vbdi_005",
                "code": "SEED/VBDI-005",
                "summary": "Báo cáo tiến độ xử lý văn bản đến tuần 15",
                "creator": "cv_hanhchinh_hn",
                "leader": "lanhdao_hn",
                "record": "hoso_hn_tiep_nhan",
                "status": VAN_BAN_STATUS_CHO_XU_LY,
                "form": HINH_THUC_BAO_CAO,
                "doc_type": LOAI_BAO_CAO_TIEN_DO,
                "drafting_unit": DEPT_HANH_CHINH,
                "issue_date": self.today - timedelta(days=2),
                "received_date": self.today - timedelta(days=1),
                "deadline": self.today + timedelta(days=4),
                "priority": DO_KHAN_BINH_THUONG,
                "privacy": DO_MAT_TUYET_MAT,
                "note": "Báo cáo mẫu do chuyên viên khác tạo để test quyền sửa văn bản đi.",
                "related_files": [],
            },
        ]
        specs = self._expand_specs_to_target(
            specs,
            self.outgoing_count,
            self._build_bulk_outgoing_specs,
        )

        for spec in specs:
            main_path, main_size = self._ensure_seed_file(
                f"{SEED_FILE_PREFIX}/van_ban/{slugify(spec['code'])}.pdf",
                spec["code"],
                spec["summary"],
            )
            document = VanBan.objects.filter(
                phan_loai=PHAN_LOAI_VAN_BAN_DI,
                so_ky_hieu=spec["code"],
            ).order_by("pk").first()
            created = document is None

            if document is None:
                document = VanBan(
                    phan_loai=PHAN_LOAI_VAN_BAN_DI,
                    so_ky_hieu=spec["code"],
                )

            document.lanh_dao_duyet = self.core_users[spec["leader"]]
            document.nguoi_tao = self.core_users[spec["creator"]]
            document.ho_so_van_ban = self.records[spec["record"]]
            document.trich_yeu = spec["summary"]
            document.hinh_thuc = spec["form"]
            document.loai_van_ban = spec["doc_type"]
            document.don_vi_soan_thao = spec["drafting_unit"]
            document.ngay_van_ban = spec["issue_date"]
            document.ngay_den = spec["received_date"]
            document.han_xu_ly = spec["deadline"]
            document.ngay_cap_nhat = self.today
            document.do_khan = spec["priority"]
            document.do_mat = spec["privacy"]
            document.trang_thai = spec["status"]
            document.noi_dung = spec["note"]
            document.file_dinh_kem = main_path
            document.kich_thuoc = main_size
            document.save()
            self._track("VanBan", created)

            self._sync_outgoing_related_files(document, spec["related_files"])

            approval = None
            if spec.get("approval_clerk"):
                approval = self._sync_outgoing_approval(document, self.core_users[spec["approval_clerk"]])
            if spec.get("return_note"):
                self._sync_outgoing_return(document, spec["return_note"])
            if spec.get("issue_targets"):
                self._sync_issue_records(document, spec["issue_targets"])
            if approval and spec.get("forward_targets"):
                self._sync_forward_records(
                    approval,
                    [self.core_users[user_key] for user_key in spec["forward_targets"]],
                )

            documents[spec["key"]] = document

        return documents

    def _sync_outgoing_related_files(self, document, file_specs):
        desired_paths = set()
        for file_spec in file_specs:
            relative_path, file_size = self._ensure_seed_file(
                f"{SEED_FILE_PREFIX}/van_ban_lien_quan/{slugify(file_spec['stem'])}.pdf",
                document.so_ky_hieu,
                file_spec["title"],
            )
            desired_paths.add(relative_path)
            related_file = VanBanLienQuan.objects.filter(
                van_ban=document,
                file_van_ban=relative_path,
            ).order_by("pk").first()
            created = related_file is None

            if related_file is None:
                related_file = VanBanLienQuan(
                    van_ban=document,
                    file_van_ban=relative_path,
                )

            related_file.kich_thuoc = file_size
            related_file.save()
            self._track("VanBanLienQuan", created)

        VanBanLienQuan.objects.filter(
            van_ban=document,
            file_van_ban__startswith=f"{SEED_FILE_PREFIX}/van_ban_lien_quan/",
        ).exclude(file_van_ban__in=desired_paths).delete()

    def _sync_outgoing_approval(self, document, clerk):
        approval = VanBanDuyet.objects.filter(van_ban=document).order_by("pk").first()
        created = approval is None

        if approval is None:
            approval = VanBanDuyet(van_ban=document)

        approval.van_thu = clerk
        approval.save()
        self._track("VanBanDuyet", created)
        return approval

    def _sync_outgoing_return(self, document, return_note):
        return_record = VanBanHoanTra.objects.filter(van_ban=document).order_by("pk").first()
        created = return_record is None

        if return_record is None:
            return_record = VanBanHoanTra(van_ban=document)

        return_record.noi_dung = return_note
        return_record.save()
        self._track("VanBanHoanTra", created)
        return return_record

    def _sync_issue_records(self, document, issue_targets):
        issue_record = BanHanh.objects.filter(van_ban=document).order_by("pk").first()
        created = issue_record is None

        if issue_record is None:
            issue_record = BanHanh(van_ban=document)

        issue_record.save()
        self._track("BanHanh", created)

        desired_pairs = set()
        for branch_key, dept_key in issue_targets.get("departments", []):
            department = self.departments[(branch_key, dept_key)]
            desired_pairs.add((department.pk, None))
            detail = BanHanhChiTiep.objects.filter(
                ban_hanh=issue_record,
                phong_ban=department,
                don_vi_ngoai__isnull=True,
            ).order_by("pk").first()
            created = detail is None
            if detail is None:
                detail = BanHanhChiTiep(
                    ban_hanh=issue_record,
                    phong_ban=department,
                    don_vi_ngoai=None,
                )
                detail.save()
            self._track("BanHanhChiTiep", created)

        for outside_key in issue_targets.get("outside_units", []):
            outside_unit = self.outside_units[outside_key]
            desired_pairs.add((None, outside_unit.pk))
            detail = BanHanhChiTiep.objects.filter(
                ban_hanh=issue_record,
                phong_ban__isnull=True,
                don_vi_ngoai=outside_unit,
            ).order_by("pk").first()
            created = detail is None
            if detail is None:
                detail = BanHanhChiTiep(
                    ban_hanh=issue_record,
                    phong_ban=None,
                    don_vi_ngoai=outside_unit,
                )
                detail.save()
            self._track("BanHanhChiTiep", created)

        for detail in BanHanhChiTiep.objects.filter(ban_hanh=issue_record):
            pair = (detail.phong_ban_id, detail.don_vi_ngoai_id)
            if pair not in desired_pairs:
                detail.delete()

    def _sync_forward_records(self, approval, recipients):
        transfer = ChuyenTiep.objects.filter(van_ban_duyet=approval).order_by("pk").first()
        created = transfer is None

        if transfer is None:
            transfer = ChuyenTiep(van_ban_duyet=approval)

        transfer.save()
        self._track("ChuyenTiep", created)

        desired_pairs = set()
        for recipient in recipients:
            if recipient.phong_ban_id is None:
                continue
            desired_pairs.add((recipient.pk, recipient.phong_ban_id))
            detail = ChuyenTiepChiTiet.objects.filter(
                chuyen_tiep=transfer,
                nguoi_dung=recipient,
                phong_ban=recipient.phong_ban,
            ).order_by("pk").first()
            created = detail is None
            if detail is None:
                detail = ChuyenTiepChiTiet(
                    chuyen_tiep=transfer,
                    nguoi_dung=recipient,
                    phong_ban=recipient.phong_ban,
                )
                detail.save()
            self._track("ChuyenTiepChiTiet", created)

        for detail in ChuyenTiepChiTiet.objects.filter(chuyen_tiep=transfer):
            pair = (detail.nguoi_dung_id, detail.phong_ban_id)
            if pair not in desired_pairs:
                detail.delete()

    def _seed_incoming_documents(self):
        documents = {}
        specs = [
            {
                "key": "vbden_001",
                "code": "SEED-VBDEN-001",
                "issuing_unit": self.outside_units["so_tai_chinh_hn"].ten_don_vi,
                "summary": "Công văn đề nghị rà soát tình hình quản lý hồ sơ quý II",
                "creator": "vanthu_hn",
                "leader": "lanhdao_hn",
                "status": VanBanDen.TrangThai.CHO_XU_LY,
                "document_type": VanBanDen.LoaiVanBan.CONG_VAN,
                "form": VanBanDen.HinhThucVanBan.CONG_VAN,
                "issue_date": self.today - timedelta(days=4),
                "received_date": self.today - timedelta(days=3),
                "deadline": self.today + timedelta(days=5),
                "priority": VanBanDen.DoKhan.KHAN,
                "privacy": VanBanDen.DoMat.BINH_THUONG,
                "field": "Lưu trữ hồ sơ",
                "processing_note": "Trình lãnh đạo xem xét hướng phân công xử lý.",
                "forward_to": [],
            },
            {
                "key": "vbden_002",
                "code": "SEED-VBDEN-002",
                "issuing_unit": self.outside_units["cong_nghe_sao_viet"].ten_don_vi,
                "summary": "Thông báo lịch làm việc về số hóa tài liệu lưu trữ",
                "creator": "vanthu_hn",
                "leader": "lanhdao_hn",
                "status": VanBanDen.TrangThai.DA_XU_LY,
                "document_type": VanBanDen.LoaiVanBan.THONG_BAO,
                "form": VanBanDen.HinhThucVanBan.THONG_BAO,
                "issue_date": self.today - timedelta(days=7),
                "received_date": self.today - timedelta(days=6),
                "deadline": self.today + timedelta(days=2),
                "priority": VanBanDen.DoKhan.BINH_THUONG,
                "privacy": VanBanDen.DoMat.BINH_THUONG,
                "field": "Công nghệ thông tin",
                "processing_note": "Lãnh đạo đã chuyển tiếp cho chuyên viên phụ trách phối hợp triển khai.",
                "forward_to": ["cv_ketoan_hn", "cv_kiemtoan_hn"],
            },
            {
                "key": "vbden_003",
                "code": "SEED-VBDEN-003",
                "issuing_unit": self.outside_units["cuc_thue_hcm"].ten_don_vi,
                "summary": "Tờ trình yêu cầu bổ sung hồ sơ giải trình thuế",
                "creator": "vanthu_hcm",
                "leader": "lanhdao_hcm",
                "status": VanBanDen.TrangThai.HOAN_TRA,
                "document_type": VanBanDen.LoaiVanBan.CONG_VAN,
                "form": VanBanDen.HinhThucVanBan.TO_TRINH,
                "issue_date": self.today - timedelta(days=8),
                "received_date": self.today - timedelta(days=7),
                "deadline": self.today + timedelta(days=1),
                "priority": VanBanDen.DoKhan.HOA_TOC,
                "privacy": VanBanDen.DoMat.MAT,
                "field": "Thuế",
                "processing_note": "Văn thư đã trình lãnh đạo và đang chờ chỉnh sửa theo góp ý.",
                "return_reason": "Bổ sung phụ lục kê khai và xác nhận của đơn vị ban hành trước khi trình lại.",
                "return_date": self.today - timedelta(days=1),
                "forward_to": [],
            },
            {
                "key": "vbden_004",
                "code": "SEED-VBDEN-004",
                "issuing_unit": self.outside_units["so_tai_chinh_hn"].ten_don_vi,
                "summary": "Kế hoạch kiểm tra công tác lưu trữ hồ sơ cuối năm",
                "creator": "vanthu_hcm",
                "leader": "lanhdao_hcm",
                "status": VanBanDen.TrangThai.XEM_DE_BIET,
                "document_type": VanBanDen.LoaiVanBan.KE_HOACH,
                "form": VanBanDen.HinhThucVanBan.THONG_BAO,
                "issue_date": self.today - timedelta(days=10),
                "received_date": self.today - timedelta(days=9),
                "deadline": self.today + timedelta(days=8),
                "priority": VanBanDen.DoKhan.BINH_THUONG,
                "privacy": VanBanDen.DoMat.BINH_THUONG,
                "field": "Kế hoạch",
                "processing_note": "Lưu xem để biết và theo dõi chung trong đơn vị.",
                "forward_to": [],
            },
            {
                "key": "vbden_005",
                "code": "SEED-VBDEN-005",
                "issuing_unit": self.outside_units["cong_nghe_sao_viet"].ten_don_vi,
                "summary": "Báo cáo tiến độ triển khai phần mềm quản lý văn bản",
                "creator": "vanthu_hcm",
                "leader": "lanhdao_hcm",
                "status": VanBanDen.TrangThai.DA_XU_LY,
                "document_type": VanBanDen.LoaiVanBan.BAO_CAO,
                "form": VanBanDen.HinhThucVanBan.THONG_BAO,
                "issue_date": self.today - timedelta(days=5),
                "received_date": self.today - timedelta(days=4),
                "deadline": self.today + timedelta(days=4),
                "priority": VanBanDen.DoKhan.KHAN,
                "privacy": VanBanDen.DoMat.BINH_THUONG,
                "field": "Phần mềm quản lý",
                "processing_note": "Đã giao chuyên viên theo dõi và tổng hợp phương án phản hồi.",
                "forward_to": ["cv_thue_hcm", "cv_ketoan_hcm"],
            },
        ]
        specs = self._expand_specs_to_target(
            specs,
            self.incoming_count,
            self._build_bulk_incoming_specs,
        )

        for spec in specs:
            document = self._upsert_one(
                VanBanDen,
                "VanBanDen",
                {"so_ky_hieu": spec["code"]},
                {
                    "don_vi_ban_hanh": spec["issuing_unit"],
                    "trich_yeu": spec["summary"],
                    "loai_van_ban": spec["document_type"],
                    "hinh_thuc_van_ban": spec["form"],
                    "ngay_van_ban": spec["issue_date"],
                    "ngay_den": spec["received_date"],
                    "han_xu_ly": spec["deadline"],
                    "do_mat": spec["privacy"],
                    "do_khan": spec["priority"],
                    "linh_vuc": spec["field"],
                    "noi_dung_xu_ly": spec["processing_note"],
                    "ly_do_hoan_tra": spec.get("return_reason", ""),
                    "ngay_hoan_tra": spec.get("return_date"),
                    "nguoi_tao": self.users[spec["creator"]],
                    "lanh_dao_xu_ly": self.users[spec["leader"]],
                    "trang_thai": spec["status"],
                },
            )
            self._sync_incoming_files(document)
            self._sync_incoming_forwarding(
                document,
                self.users[spec["leader"]],
                [self.users[user_key] for user_key in spec["forward_to"]],
            )
            documents[spec["key"]] = document

        return documents

    def _sync_incoming_files(self, document):
        file_specs = [
            {
                "relative_path": f"{SEED_FILE_PREFIX}/van_ban_den/{slugify(document.so_ky_hieu)}-dinh-kem.pdf",
                "title": f"{document.so_ky_hieu} - File đính kèm",
                "file_type": TepVanBanDen.LoaiTep.DINH_KEM,
            },
            {
                "relative_path": f"{SEED_FILE_PREFIX}/van_ban_den/{slugify(document.so_ky_hieu)}-lien-quan.pdf",
                "title": f"{document.so_ky_hieu} - Tài liệu liên quan",
                "file_type": TepVanBanDen.LoaiTep.LIEN_QUAN,
            },
        ]

        desired_paths = set()
        for file_spec in file_specs:
            relative_path, _ = self._ensure_seed_file(
                file_spec["relative_path"],
                file_spec["title"],
                document.trich_yeu,
            )
            desired_paths.add(relative_path)
            attachment = TepVanBanDen.objects.filter(
                van_ban_den=document,
                loai=file_spec["file_type"],
                tep=relative_path,
            ).order_by("pk").first()
            created = attachment is None
            if attachment is None:
                attachment = TepVanBanDen(
                    van_ban_den=document,
                    loai=file_spec["file_type"],
                    tep=relative_path,
                )
                attachment.save()
            self._track("TepVanBanDen", created)

        TepVanBanDen.objects.filter(
            van_ban_den=document,
            tep__startswith=f"{SEED_FILE_PREFIX}/van_ban_den/",
        ).exclude(tep__in=desired_paths).delete()

    def _sync_incoming_forwarding(self, document, leader, specialists):
        desired_ids = {specialist.pk for specialist in specialists}
        VanBanDenChuyenTiep.objects.filter(van_ban_den=document).exclude(
            chuyen_vien_id__in=desired_ids
        ).delete()

        for specialist in specialists:
            forwarding, created = VanBanDenChuyenTiep.objects.get_or_create(
                van_ban_den=document,
                chuyen_vien=specialist,
                defaults={"nguoi_chuyen": leader},
            )
            if forwarding.nguoi_chuyen_id != leader.pk:
                forwarding.nguoi_chuyen = leader
                forwarding.save(update_fields=["nguoi_chuyen"])
            self._track("VanBanDenChuyenTiep", created)

    def _seed_tasks(self):
        tasks = {}
        specs = [
            {
                "key": "task_01",
                "title": "[SEED-TASK-01] Rà soát dự thảo công văn thuế quý II",
                "content": "Kiểm tra căn cứ pháp lý, chuẩn hóa thể thức trình ký và chuẩn bị ý kiến góp ý cho lãnh đạo.",
                "assigner": "lanhdao_hn",
                "assignee": "cv_ketoan_hn",
                "collaborators": ["cv_kiemtoan_hn"],
                "document": "vbdi_001",
                "source": CongViec.NguonGiao.VAN_BAN_DI,
                "status": CongViec.TrangThai.CHO_XU_LY,
                "start_offset": -1,
                "deadline_offset": 5,
                "requires_approval": True,
                "note": "Ưu tiên kiểm tra phần căn cứ viện dẫn và danh sách nơi nhận.",
                "result": "",
            },
            {
                "key": "task_02",
                "title": "[SEED-TASK-02] Soạn báo cáo giải trình cho lãnh đạo",
                "content": "Tổng hợp nội dung xử lý văn bản đến và gửi báo cáo để lãnh đạo phê duyệt.",
                "assigner": "lanhdao_hn",
                "assignee": "cv_kiemtoan_hn",
                "collaborators": ["cv_hanhchinh_hn"],
                "document": "vbdi_002",
                "source": CongViec.NguonGiao.VAN_BAN_DI,
                "status": CongViec.TrangThai.CHO_DUYET,
                "start_offset": -2,
                "deadline_offset": 4,
                "requires_approval": True,
                "note": "Đã nộp báo cáo và chờ lãnh đạo phản hồi.",
                "result": "Đã hoàn tất báo cáo giải trình, kèm bảng đối chiếu số liệu và đề xuất hướng chỉnh sửa.",
            },
            {
                "key": "task_03",
                "title": "[SEED-TASK-03] Hoàn thiện hồ sơ ban hành thông báo nội bộ",
                "content": "Chuẩn hóa danh sách phát hành, xác nhận nội dung cuối cùng trước khi văn thư ban hành.",
                "assigner": "lanhdao_hcm",
                "assignee": "cv_thue_hcm",
                "collaborators": ["cv_ketoan_hcm"],
                "document": "vbdi_003",
                "source": CongViec.NguonGiao.VAN_BAN_DI,
                "status": CongViec.TrangThai.DA_HOAN_THANH,
                "start_offset": -5,
                "deadline_offset": 3,
                "requires_approval": True,
                "note": "Công việc đã được lãnh đạo phê duyệt hoàn thành.",
                "result": "Đã rà soát danh sách phát hành, xác minh nơi nhận và cập nhật bản cuối cùng để ban hành.",
                "approved": True,
            },
            {
                "key": "task_04",
                "title": "[SEED-TASK-04] Bổ sung số liệu kiểm toán chi nhánh Hà Nội",
                "content": "Cập nhật lại số liệu kiểm toán theo góp ý của lãnh đạo và nộp lại bản giải trình.",
                "assigner": "lanhdao_hn",
                "assignee": "cv_ketoan_hn",
                "collaborators": [],
                "document": "vbdi_002",
                "source": CongViec.NguonGiao.VAN_BAN_DI,
                "status": CongViec.TrangThai.HOAN_TRA_CV,
                "start_offset": -4,
                "deadline_offset": 6,
                "requires_approval": True,
                "note": "Lãnh đạo đã hoàn trả để bổ sung lại số liệu và căn cứ đối chiếu.",
                "result": "Đã cập nhật lần 1 bảng số liệu, chờ chuyên viên bổ sung thêm chứng từ kèm theo.",
                "return_note": "Bổ sung thêm bảng đối chiếu số liệu gốc trước khi trình lại.",
                "returned_by": "lanhdao_hn",
            },
            {
                "key": "task_05",
                "title": "[SEED-TASK-05] Xin ý kiến lại về kế hoạch lưu trữ hồ sơ",
                "content": "Chuyên viên tổng hợp phương án xử lý, hoàn trả lãnh đạo để điều chỉnh lại hướng giao việc.",
                "assigner": "lanhdao_hn",
                "assignee": "cv_hanhchinh_hn",
                "collaborators": ["cv_kiemtoan_hn"],
                "document": None,
                "source": CongViec.NguonGiao.VAN_BAN_DEN,
                "status": CongViec.TrangThai.HOAN_TRA_LD,
                "start_offset": -3,
                "deadline_offset": 2,
                "requires_approval": True,
                "note": "Chuyên viên đã hoàn trả để xin điều chỉnh phạm vi công việc.",
                "result": "",
                "return_note": "Đề nghị lãnh đạo làm rõ phạm vi tài liệu cần số hóa trong đợt này.",
                "returned_by": "cv_hanhchinh_hn",
            },
            {
                "key": "task_06",
                "title": "[SEED-TASK-06] Chuẩn bị bản phát hành gửi đơn vị ngoài",
                "content": "Kiểm tra nơi nhận ngoài đơn vị và chuẩn bị bản phát hành cuối cùng cho văn thư.",
                "assigner": "lanhdao_hcm",
                "assignee": "cv_ketoan_hcm",
                "collaborators": ["cv_thue_hcm"],
                "document": "vbdi_004",
                "source": CongViec.NguonGiao.VAN_BAN_DI,
                "status": CongViec.TrangThai.CHO_XU_LY,
                "start_offset": 0,
                "deadline_offset": 7,
                "requires_approval": True,
                "note": "Cần rà soát lại danh sách đơn vị ngoài trước khi gửi chính thức.",
                "result": "",
            },
            {
                "key": "task_07",
                "title": "[SEED-TASK-07] Tổng hợp phản hồi văn bản đến lĩnh vực thuế",
                "content": "Tổng hợp phản hồi của các bộ phận về văn bản đến liên quan đến thuế và trình lãnh đạo.",
                "assigner": "lanhdao_hcm",
                "assignee": "cv_thue_hcm",
                "collaborators": ["cv_ketoan_hcm"],
                "document": None,
                "source": CongViec.NguonGiao.VAN_BAN_DEN,
                "status": CongViec.TrangThai.CHO_DUYET,
                "start_offset": -2,
                "deadline_offset": 3,
                "requires_approval": True,
                "note": "Đã gửi báo cáo xử lý và chờ phê duyệt.",
                "result": "Đã tổng hợp phản hồi từ các phòng ban, kèm đề xuất lịch phản hồi cho đơn vị ban hành.",
            },
            {
                "key": "task_08",
                "title": "[SEED-TASK-08] Đối chiếu hồ sơ kiểm toán chi nhánh Đà Nẵng",
                "content": "Kiểm tra lại danh mục hồ sơ kiểm toán và cập nhật vào hệ thống lưu trữ dùng chung.",
                "assigner": "lanhdao_hcm",
                "assignee": "cv_kiemtoan_dn",
                "collaborators": [],
                "document": None,
                "source": CongViec.NguonGiao.VAN_BAN_DEN,
                "status": CongViec.TrangThai.DA_HOAN_THANH,
                "start_offset": -6,
                "deadline_offset": 2,
                "requires_approval": False,
                "note": "Công việc hoàn thành và không yêu cầu phê duyệt lại.",
                "result": "Đã đối chiếu đủ 24 hồ sơ kiểm toán và cập nhật danh mục vào kho lưu trữ dùng chung.",
            },
        ]
        specs = self._expand_specs_to_target(
            specs,
            self.task_count,
            self._build_bulk_task_specs,
        )

        for spec in specs:
            related_document = self.outgoing_docs.get(spec["document"]) if spec["document"] else None
            task = CongViec.objects.filter(
                ten_cong_viec=spec["title"],
                nguoi_giao=self.core_users[spec["assigner"]],
                nguoi_thuc_hien=self.core_users[spec["assignee"]],
            ).order_by("pk").first()
            created = task is None

            if task is None:
                task = CongViec(
                    ten_cong_viec=spec["title"],
                    nguoi_giao=self.core_users[spec["assigner"]],
                    nguoi_thuc_hien=self.core_users[spec["assignee"]],
                )

            task.van_ban = related_document
            task.noi_dung_cong_viec = spec["content"]
            task.nguon_giao = spec["source"]
            task.trang_thai = spec["status"]
            task.ngay_bat_dau = self.today + timedelta(days=spec["start_offset"])
            task.han_xu_ly = self._deadline(spec["deadline_offset"])
            task.ngay_cap_nhat_giao_viec = self.today
            task.ket_qua_xu_ly = spec["result"]
            task.ghi_chu = spec["note"]
            task.ngay_xu_ly = self.today if spec["result"] else self.today - timedelta(days=1)
            task.yeu_cau_phe_duyet = spec["requires_approval"]
            task.save()
            self._track("CongViec", created)

            self._sync_task_collaborators(
                task,
                [self.core_users[user_key] for user_key in spec["collaborators"]],
            )
            self._sync_task_attachments(task, spec)

            if spec.get("return_note"):
                self._sync_task_return(
                    task,
                    self.core_users[spec["returned_by"]],
                    spec["return_note"],
                )
            if spec.get("approved"):
                self._sync_task_approval(task)

            tasks[spec["key"]] = task

        return tasks

    def _sync_task_collaborators(self, task, collaborators):
        desired_ids = {collaborator.pk for collaborator in collaborators}
        PhanCongCongViec.objects.filter(cong_viec=task).exclude(
            nguoi_phoi_hop_id__in=desired_ids
        ).delete()

        for collaborator in collaborators:
            _, created = PhanCongCongViec.objects.get_or_create(
                cong_viec=task,
                nguoi_phoi_hop=collaborator,
            )
            self._track("PhanCongCongViec", created)

    def _sync_task_attachments(self, task, spec):
        assignment_files = [
            {
                "relative_path": f"{SEED_FILE_PREFIX}/file_cv_lien_quan/{slugify(spec['key'])}-giao-viec.pdf",
                "title": f"{spec['title']} - Phiếu giao việc",
                "file_kind": FileCVLienQuan.LoaiFile.CHINH,
            },
            {
                "relative_path": f"{SEED_FILE_PREFIX}/file_cv_lien_quan/{slugify(spec['key'])}-tai-lieu-lien-quan.pdf",
                "title": f"{spec['title']} - Tài liệu liên quan",
                "file_kind": FileCVLienQuan.LoaiFile.LIEN_QUAN,
            },
        ]
        result_files = []
        if spec["result"]:
            result_files.append(
                {
                    "relative_path": f"{SEED_FILE_PREFIX}/file_cv_lien_quan/{slugify(spec['key'])}-ket-qua.pdf",
                    "title": f"{spec['title']} - Báo cáo xử lý",
                    "file_kind": FileCVLienQuan.LoaiFile.LIEN_QUAN,
                }
            )

        self._sync_task_file_group(
            task,
            assignment_files,
            source=FileCVLienQuan.NguonTaiLen.GIAO_VIEC,
            uploader=self.core_users[spec["assigner"]],
        )
        self._sync_task_file_group(
            task,
            result_files,
            source=FileCVLienQuan.NguonTaiLen.KET_QUA_XU_LY,
            uploader=self.core_users[spec["assignee"]],
        )

    def _sync_task_file_group(self, task, file_specs, *, source, uploader):
        desired_paths = set()
        for file_spec in file_specs:
            relative_path, file_size = self._ensure_seed_file(
                file_spec["relative_path"],
                file_spec["title"],
                task.ten_cong_viec,
            )
            desired_paths.add(relative_path)
            attachment = FileCVLienQuan.objects.filter(
                cong_viec=task,
                file_van_ban=relative_path,
                nguon_tai_len=source,
            ).order_by("pk").first()
            created = attachment is None

            if attachment is None:
                attachment = FileCVLienQuan(
                    cong_viec=task,
                    file_van_ban=relative_path,
                    nguon_tai_len=source,
                )

            attachment.kich_thuoc = file_size
            attachment.loai_file = file_spec["file_kind"]
            attachment.nguoi_tai_len = uploader
            attachment.save()
            self._track("FileCVLienQuan", created)

        FileCVLienQuan.objects.filter(
            cong_viec=task,
            nguon_tai_len=source,
            file_van_ban__startswith=f"{SEED_FILE_PREFIX}/file_cv_lien_quan/",
        ).exclude(file_van_ban__in=desired_paths).delete()

    def _sync_task_return(self, task, returned_by, note):
        return_record = HoanTraCongViec.objects.filter(cong_viec=task).order_by("pk").first()
        created = return_record is None

        if return_record is None:
            return_record = HoanTraCongViec(cong_viec=task)

        return_record.nguoi_hoan_tra = returned_by
        return_record.noi_dung = note
        return_record.save()
        self._track("HoanTraCongViec", created)

    def _sync_task_approval(self, task):
        approval = PheDuyetCongViec.objects.filter(cong_viec=task).order_by("pk").first()
        created = approval is None

        if approval is None:
            approval = PheDuyetCongViec(cong_viec=task)
            approval.save()

        self._track("PheDuyetCongViec", created)

    def _print_account_summary(self):
        self.stdout.write("")
        self.stdout.write("Tài khoản demo có thể dùng để đăng nhập:")
        for user in sorted(self.demo_accounts, key=lambda item: item.username):
            department_name = user.phong_ban.ten_phong_ban if user.phong_ban else "-"
            self.stdout.write(
                f" - {user.username} | {DEMO_PASSWORD} | {user.role} | {department_name}"
            )

    def _print_model_summary(self):
        summary_models = [
            ("ChiNhanh", ChiNhanh),
            ("PhongBan", PhongBan),
            ("DonViNgoai", DonViNgoai),
            ("Customer", User),
            ("NguoiDung", NguoiDung),
            ("HoSoVanBan", HoSoVanBan),
            ("PhongXemHoSo", PhongXemHoSo),
            ("NguoiXuLyHoSo", NguoiXuLyHoSo),
            ("VanBan", VanBan),
            ("VanBanLienQuan", VanBanLienQuan),
            ("VanBanDuyet", VanBanDuyet),
            ("ChuyenTiep", ChuyenTiep),
            ("ChuyenTiepChiTiet", ChuyenTiepChiTiet),
            ("BanHanh", BanHanh),
            ("BanHanhChiTiep", BanHanhChiTiep),
            ("VanBanHoanTra", VanBanHoanTra),
            ("VanBanDen", VanBanDen),
            ("VanBanDenChuyenTiep", VanBanDenChuyenTiep),
            ("TepVanBanDen", TepVanBanDen),
            ("CongViec", CongViec),
            ("PhanCongCongViec", PhanCongCongViec),
            ("FileCVLienQuan", FileCVLienQuan),
            ("HoanTraCongViec", HoanTraCongViec),
            ("PheDuyetCongViec", PheDuyetCongViec),
        ]

        self.stdout.write("")
        self.stdout.write("Tổng kết số bản ghi:")
        for label, model in summary_models:
            created = self.stats[label]["created"]
            reused = self.stats[label]["reused"]
            self.stdout.write(
                f" - {label}: tạo mới {created}, tái sử dụng {reused}, tổng hiện có {model.objects.count()}"
            )
        self.stdout.write(
            f" - Seed files: tạo mới {self.created_seed_files}, thư mục lưu tại media/{SEED_FILE_PREFIX}/"
        )
