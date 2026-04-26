import unicodedata

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.role_groups import ensure_role_groups, sync_user_role_group
from apps.core.models import ChiNhanh, PhongBan


User = get_user_model()

DEFAULT_PASSWORD = "123"

BRANCH_SPECS = [
    {
        "key": "hn",
        "name": "Trụ sở Hà Nội",
        "aliases": [
            "Trụ sở Hà Nội",
            "Chi nhánh Hà Nội",
            "Chi nhanh Ha Noi",
            "Tong cong ty ATAX",
        ],
    },
    {
        "key": "dn",
        "name": "Chi nhánh Đà Nẵng",
        "aliases": [
            "Chi nhánh Đà Nẵng",
            "Chi nhanh Da Nang",
            "Đà Nẵng",
            "Da Nang",
        ],
    },
    {
        "key": "hcm",
        "name": "Chi nhánh TP.HCM",
        "aliases": [
            "Chi nhánh TP.HCM",
            "Chi nhánh TP Hồ Chí Minh",
            "Chi nhanh TP Ho Chi Minh",
            "TP.HCM",
            "TP HCM",
            "Ho Chi Minh",
        ],
    },
]

DEPARTMENT_SPECS = {
    "ban_giam_doc": {
        "name": "Ban Giám đốc",
        "aliases": ["Ban Giám đốc", "Ban Giám Đốc", "Ban Giam Doc"],
    },
    "van_thu": {
        "name": "Văn thư",
        "aliases": ["Văn thư", "Văn Thư", "Van thu"],
    },
    "ke_toan": {
        "name": "Kế toán",
        "aliases": ["Kế toán", "Kế Toán", "Phòng Kế Toán", "Phong Ke Toan"],
    },
    "kiem_toan": {
        "name": "Kiểm toán",
        "aliases": ["Kiểm toán", "Kiểm Toán", "Phòng Kiểm Toán", "Phong Kiem Toan"],
    },
    "tu_van_thue": {
        "name": "Tư vấn thuế",
        "aliases": [
            "Tư vấn thuế",
            "Tư Vấn Thuế",
            "Phòng Tư Vấn Thuế",
            "Phong Tu Van Thue",
        ],
    },
    "hanh_chinh": {
        "name": "Hành chính",
        "aliases": [
            "Hành chính",
            "Hành Chính",
            "Phòng Hành Chính/Nhân sự",
            "Phong Hanh Chinh Nhan Su",
        ],
    },
    "dao_tao": {
        "name": "Đào tạo",
        "aliases": [
            "Đào tạo",
            "Đào Tạo",
            "Phòng Đào Tạo Chất Lượng",
            "Phong Dao Tao Chat Luong",
        ],
    },
}

SPECIALIST_DEPARTMENT_KEYS = [
    "ke_toan",
    "kiem_toan",
    "tu_van_thue",
    "hanh_chinh",
    "dao_tao",
]
BRANCH_KEYS = [spec["key"] for spec in BRANCH_SPECS]
LEADER_BRANCH_KEYS = ["hn", "hcm", "dn", "hn", "hcm"]

FAMILY_NAMES = [
    "Nguyễn",
    "Trần",
    "Lê",
    "Phạm",
    "Hoàng",
    "Phan",
    "Vũ",
    "Đặng",
    "Bùi",
    "Đỗ",
    "Hồ",
    "Ngô",
]
MIDDLE_NAMES = [
    "Văn",
    "Minh",
    "Thu",
    "Quang",
    "Hoài",
    "Thanh",
    "Gia",
    "Ngọc",
    "Đức",
    "Khánh",
]
GIVEN_NAMES = [
    "An",
    "Khoa",
    "Hà",
    "Huy",
    "Linh",
    "Nam",
    "Trang",
    "Duy",
    "Phúc",
    "Mai",
    "Bảo",
    "Nhi",
    "Tuấn",
    "Vy",
    "Long",
    "Thảo",
    "Sơn",
    "Hạnh",
    "Kiên",
    "Yến",
    "Tâm",
    "Nhật",
    "Quân",
    "Hương",
    "Đạt",
]


def normalize_label(value):
    normalized = unicodedata.normalize("NFKD", value or "").replace("Đ", "D").replace(
        "đ", "d"
    )
    without_marks = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    alpha_numeric = "".join(
        char.lower() if char.isalnum() else " " for char in without_marks
    )
    return " ".join(alpha_numeric.split())


class Command(BaseCommand):
    help = "Tao/cap nhat 95 tai khoan mau theo vai tro cho he thong."

    def handle(self, *args, **options):
        self._configure_output_encoding()
        self.stats = {
            "branches_created": 0,
            "departments_created": 0,
            "users_created": 0,
            "users_updated": 0,
            "core_profiles_synced": 0,
        }
        self.sample_accounts = []

        self.stdout.write("Đang seed tài khoản mẫu...")

        with transaction.atomic():
            self.role_groups = ensure_role_groups(User)
            self.branches = self._ensure_branches()
            self.departments = self._ensure_departments()
            self._seed_users()
            self._assign_department_heads()

        self.stdout.write(self.style.SUCCESS("Seed tài khoản mẫu hoàn tất."))
        self._print_summary()
        self._print_accounts()

    def _configure_output_encoding(self):
        for wrapper in (self.stdout, self.stderr):
            stream = getattr(wrapper, "_out", None)
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="backslashreplace")

    def _find_existing_by_aliases(self, objects, field_name, aliases):
        normalized_aliases = [normalize_label(alias) for alias in aliases]
        for obj in objects:
            obj_label = normalize_label(getattr(obj, field_name))
            for alias in normalized_aliases:
                if obj_label == alias or alias in obj_label or obj_label in alias:
                    return obj
        return None

    def _ensure_branches(self):
        branches = {}
        existing_branches = list(ChiNhanh.objects.all().order_by("chi_nhanh_id"))

        for spec in BRANCH_SPECS:
            branch = self._find_existing_by_aliases(
                existing_branches,
                "ten_chi_nhanh",
                [spec["name"], *spec["aliases"]],
            )
            if branch is None:
                branch = ChiNhanh.objects.create(ten_chi_nhanh=spec["name"])
                existing_branches.append(branch)
                self.stats["branches_created"] += 1
            branches[spec["key"]] = branch

        return branches

    def _ensure_departments(self):
        departments = {}

        for branch_key, branch in self.branches.items():
            existing_departments = list(
                PhongBan.objects.filter(chi_nhanh=branch).order_by("phong_ban_id")
            )
            for department_key, spec in DEPARTMENT_SPECS.items():
                department = self._find_existing_by_aliases(
                    existing_departments,
                    "ten_phong_ban",
                    [spec["name"], *spec["aliases"]],
                )
                if department is None:
                    department = PhongBan.objects.create(
                        chi_nhanh=branch,
                        ten_phong_ban=spec["name"],
                    )
                    existing_departments.append(department)
                    self.stats["departments_created"] += 1

                departments[(branch_key, department_key)] = department

        return departments

    def _seed_users(self):
        for spec in self._build_account_specs():
            user = User.objects.filter(username=spec["username"]).first()
            created = user is None

            if user is None:
                user = User(username=spec["username"])

            email_owner = (
                User.objects.filter(email__iexact=spec["email"])
                .exclude(pk=user.pk)
                .first()
            )
            if email_owner:
                raise CommandError(
                    "Email mẫu "
                    f"{spec['email']} đã thuộc về username {email_owner.username}."
                )

            user.email = spec["email"]
            user.ho_va_ten = spec["ho_va_ten"]
            user.sdt = spec["sdt"]
            user.role = spec["role"]
            user.chuc_vu = spec["chuc_vu"]
            user.chi_nhanh = spec["chi_nhanh"]
            user.phong_ban = spec["phong_ban"]
            user.is_active = True
            user.is_staff = False
            user.is_superuser = False
            user.set_password(DEFAULT_PASSWORD)
            user.save()

            sync_user_role_group(user, role_groups=self.role_groups)
            user.sync_core_profile()

            self.stats["users_created" if created else "users_updated"] += 1
            self.stats["core_profiles_synced"] += 1
            self.sample_accounts.append(user)

    def _build_account_specs(self):
        full_names = self._full_name_pool()
        name_index = 0
        phone_number = 1
        account_specs = []

        def next_identity():
            nonlocal name_index, phone_number
            identity = {
                "ho_va_ten": full_names[name_index],
                "sdt": f"090100{phone_number:04d}",
            }
            name_index += 1
            phone_number += 1
            return identity

        for index in range(1, 51):
            department_key = SPECIALIST_DEPARTMENT_KEYS[
                (index - 1) % len(SPECIALIST_DEPARTMENT_KEYS)
            ]
            branch_key = BRANCH_KEYS[(index - 1) % len(BRANCH_KEYS)]
            department = self.departments[(branch_key, department_key)]
            identity = next_identity()
            account_specs.append(
                {
                    **identity,
                    "username": f"chuyenvien{index:02d}",
                    "email": f"chuyenvien{index:02d}@atax.demo",
                    "role": User.Role.CHUYEN_VIEN,
                    "chuc_vu": f"Chuyên viên {DEPARTMENT_SPECS[department_key]['name']}",
                    "chi_nhanh": self.branches[branch_key],
                    "phong_ban": department,
                }
            )

        for index in range(1, 6):
            branch_key = LEADER_BRANCH_KEYS[index - 1]
            department = self.departments[(branch_key, "ban_giam_doc")]
            identity = next_identity()
            account_specs.append(
                {
                    **identity,
                    "username": f"lanhdao{index:02d}",
                    "email": f"lanhdao{index:02d}@atax.demo",
                    "role": User.Role.LANH_DAO,
                    "chuc_vu": "Lãnh đạo Ban Giám đốc",
                    "chi_nhanh": self.branches[branch_key],
                    "phong_ban": department,
                }
            )

        for index in range(1, 41):
            branch_key = BRANCH_KEYS[(index - 1) % len(BRANCH_KEYS)]
            department = self.departments[(branch_key, "van_thu")]
            identity = next_identity()
            account_specs.append(
                {
                    **identity,
                    "username": f"vanthu{index:02d}",
                    "email": f"vanthu{index:02d}@atax.demo",
                    "role": User.Role.VAN_THU,
                    "chuc_vu": "Văn thư",
                    "chi_nhanh": self.branches[branch_key],
                    "phong_ban": department,
                }
            )

        return account_specs

    def _full_name_pool(self):
        required_count = 95
        full_names = []

        for index in range(required_count):
            family_name = FAMILY_NAMES[index % len(FAMILY_NAMES)]
            middle_name = MIDDLE_NAMES[(index // len(FAMILY_NAMES)) % len(MIDDLE_NAMES)]
            given_name = GIVEN_NAMES[(index * 7) % len(GIVEN_NAMES)]
            full_names.append(f"{family_name} {middle_name} {given_name}")

        if len(set(full_names)) != required_count:
            raise CommandError("Dữ liệu họ tên mẫu đang bị trùng.")
        return full_names

    def _assign_department_heads(self):
        leaders = [
            user
            for user in self.sample_accounts
            if user.role == User.Role.LANH_DAO and user.phong_ban_id
        ]
        if not leaders:
            return

        leaders_by_branch = {}
        for leader in leaders:
            leaders_by_branch.setdefault(leader.chi_nhanh_id, leader)

        for branch in self.branches.values():
            leader = leaders_by_branch.get(branch.pk, leaders[0])
            core_profile = leader.sync_core_profile()
            departments = PhongBan.objects.filter(chi_nhanh=branch)
            for department in departments:
                if department.truong_phong_id != core_profile.pk:
                    department.truong_phong = core_profile
                    department.save(update_fields=["truong_phong"])

    def _print_summary(self):
        self.stdout.write("")
        self.stdout.write("Tổng kết:")
        self.stdout.write(f" - ChiNhanh tạo mới: {self.stats['branches_created']}")
        self.stdout.write(f" - PhongBan tạo mới: {self.stats['departments_created']}")
        self.stdout.write(f" - User tạo mới: {self.stats['users_created']}")
        self.stdout.write(f" - User cập nhật: {self.stats['users_updated']}")
        self.stdout.write(
            f" - Hồ sơ core đã đồng bộ: {self.stats['core_profiles_synced']}"
        )

    def _print_accounts(self):
        self.stdout.write("")
        self.stdout.write("username | password | role | phòng ban")
        for user in self.sample_accounts:
            department_name = user.phong_ban.ten_phong_ban if user.phong_ban else "-"
            self.stdout.write(
                f"{user.username} | {DEFAULT_PASSWORD} | {user.role} | {department_name}"
            )
