from django.apps import apps
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from .role_groups import sync_user_role_group


# File này định nghĩa tài khoản đăng nhập và ánh xạ tài khoản sang hồ sơ nghiệp vụ.


# Model Customer mở rộng User mặc định để lưu vai trò, phòng ban và quyền truy cập.
class Customer(AbstractUser):
    # Các vai trò chính quyết định menu và quyền thao tác trong hệ thống.
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Quản trị hệ thống"
        LANH_DAO = "LANH_DAO", "Lãnh đạo"
        VAN_THU = "VAN_THU", "Văn thư"
        CHUYEN_VIEN = "CHUYEN_VIEN", "Chuyên viên"

    ROLE_PERMISSION_MAP = {
        Role.ADMIN: "access_admin_area",
        Role.LANH_DAO: "access_lanh_dao_area",
        Role.VAN_THU: "access_van_thu_area",
        Role.CHUYEN_VIEN: "access_chuyen_vien_area",
    }
    ROLE_CORE_CHUC_VU_MAP = {
        Role.ADMIN: "Quản Trị Hệ Thống",
        Role.LANH_DAO: "Lãnh Đạo",
        Role.VAN_THU: "Văn Thư",
        Role.CHUYEN_VIEN: "Chuyên Viên",
    }

    email = models.EmailField("Email", unique=True)
    ho_va_ten = models.CharField("Họ và tên", max_length=255)
    chuc_vu = models.CharField("Chức vụ", max_length=255, blank=True)
    sdt = models.CharField("Số điện thoại", max_length=20, blank=True)
    role = models.CharField("Vai trò", max_length=20, choices=Role.choices, default=Role.CHUYEN_VIEN)

    chi_nhanh = models.ForeignKey(
        "core.ChiNhanh",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="Chi nhánh",
    )
    phong_ban = models.ForeignKey(
        "core.PhongBan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="Phòng ban",
    )

    REQUIRED_FIELDS = ["email", "ho_va_ten"]

    class Meta:
        verbose_name = "Người dùng"
        verbose_name_plural = "Người dùng"
        permissions = [
            ("access_admin_area", "Có thể vào khu vực quản trị hệ thống"),
            ("access_lanh_dao_area", "Có thể vào khu vực lãnh đạo"),
            ("access_van_thu_area", "Có thể vào khu vực văn thư"),
            ("access_chuyen_vien_area", "Có thể vào khu vực chuyên viên"),

            ("manage_users", "Có thể quản lý người dùng"),
            ("manage_departments", "Có thể quản lý chi nhánh và phòng ban"),
            ("view_reports", "Có thể xem báo cáo thống kê"),

            ("present_incoming_document", "Có thể trình văn bản đến"),
            ("edit_incoming_document", "Có thể chỉnh sửa văn bản đến"),
            ("delete_incoming_document", "Có thể xóa văn bản đến"),
            ("return_incoming_document", "Có thể hoàn trả văn bản đến"),
            ("forward_document", "Có thể chuyển tiếp văn bản"),

            ("draft_outgoing_document", "Có thể soạn thảo văn bản đi"),
            ("edit_outgoing_document", "Có thể chỉnh sửa văn bản đi"),
            ("delete_outgoing_document", "Có thể xóa văn bản đi"),
            ("approve_outgoing_document", "Có thể phê duyệt văn bản đi"),
            ("return_outgoing_document", "Có thể hoàn trả văn bản đi"),
            ("issue_outgoing_document", "Có thể ban hành văn bản đi"),

            ("assign_task", "Có thể giao việc"),
            ("edit_task", "Có thể chỉnh sửa công việc"),
            ("delete_task", "Có thể xóa công việc"),
            ("approve_task", "Có thể duyệt công việc"),
            ("return_task", "Có thể hoàn trả công việc"),
            ("process_task", "Có thể xử lý công việc"),
            ("update_task_result", "Có thể cập nhật xử lý công việc"),

            ("manage_records", "Có thể quản lý hồ sơ văn bản"),
            ("add_document_to_record", "Có thể thêm văn bản vào hồ sơ"),
            ("remove_document_from_record", "Có thể xóa văn bản khỏi hồ sơ"),
        ]

    def __str__(self):
        return self.ho_va_ten or self.username

    @property
    def is_admin_role(self):
        # Kiểm tra nhanh tài khoản có vai trò quản trị hay không.
        return self.role == self.Role.ADMIN

    @property
    def is_lanh_dao(self):
        # Dùng trong view/template để giới hạn chức năng của lãnh đạo.
        return self.role == self.Role.LANH_DAO

    @property
    def is_van_thu(self):
        # Dùng trong view/template để giới hạn chức năng của văn thư.
        return self.role == self.Role.VAN_THU

    @property
    def is_chuyen_vien(self):
        # Dùng trong view/template để giới hạn chức năng của chuyên viên.
        return self.role == self.Role.CHUYEN_VIEN

    @property
    def display_name(self):
        return (self.ho_va_ten or self.get_full_name() or self.username).strip()

    @property
    def display_role(self):
        return (self.chuc_vu or self.get_role_display()).strip()

    @property
    def initials(self):
        parts = [part for part in self.display_name.split() if part]
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[-1][0]}".upper()
        if parts:
            return parts[0][:2].upper()
        return self.username[:2].upper()

    @property
    def access_permission_codename(self):
        # Trả về codename quyền tương ứng với role để đồng bộ group/permission.
        return self.ROLE_PERMISSION_MAP.get(self.role, "")

    def has_role(self, *roles):
        # Superuser luôn được phép, các tài khoản khác phải khớp role.
        return self.is_superuser or self.role in roles

    def get_core_chuc_vu(self):
        # Chuẩn hóa chức vụ trước khi đồng bộ sang model NguoiDung của core.
        nguoi_dung_model = apps.get_model("core", "NguoiDung")
        valid_chuc_vu_values = {
            value for value, _ in nguoi_dung_model.CHUC_VU_CHOICES
        }
        normalized_chuc_vu = (self.chuc_vu or "").strip()
        if normalized_chuc_vu in valid_chuc_vu_values:
            return normalized_chuc_vu
        return self.ROLE_CORE_CHUC_VU_MAP.get(
            self.role,
            nguoi_dung_model.ChucVu.CHUYEN_VIEN,
        )

    def sync_core_profile(self):
        # Tạo hoặc cập nhật hồ sơ NguoiDung tương ứng với tài khoản đăng nhập.
        nguoi_dung_model = apps.get_model("core", "NguoiDung")

        try:
            core_profile = self.nguoi_dung_core
        except ObjectDoesNotExist:
            core_profile = None

        if core_profile is None and self.email:
            email_match = nguoi_dung_model.objects.filter(email__iexact=self.email).first()
            if email_match and email_match.tai_khoan_id in (None, self.pk):
                core_profile = email_match

        if core_profile is None:
            core_profile = nguoi_dung_model()

        core_profile.tai_khoan = self
        core_profile.ho_va_ten = (self.ho_va_ten or self.get_full_name() or self.username).strip()
        core_profile.email = self.email
        core_profile.sdt = self.sdt
        core_profile.chuc_vu = self.get_core_chuc_vu()
        if self.phong_ban_id:
            core_profile.phong_ban = self.phong_ban
        core_profile.save()
        return core_profile

    def sync_permission_group(self):
        # Đồng bộ group Django theo role để phần kiểm quyền dùng chung hoạt động.
        return sync_user_role_group(self)

    def sync_access_context(self):
        # Gọi khi đăng nhập/profile để đảm bảo quyền và hồ sơ nghiệp vụ đã sẵn sàng.
        self.sync_permission_group()
        return self.sync_core_profile()

    @property
    def core_profile(self):
        # Trả về hồ sơ nghiệp vụ; nếu chưa có thì tự tạo từ thông tin tài khoản.
        try:
            return self.nguoi_dung_core
        except ObjectDoesNotExist:
            return self.sync_core_profile()
