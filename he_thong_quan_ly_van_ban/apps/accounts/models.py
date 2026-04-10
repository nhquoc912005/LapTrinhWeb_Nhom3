from django.contrib.auth.models import AbstractUser
from django.db import models

class Customer(AbstractUser):
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

    email = models.EmailField("Email",unique=True)
    ho_va_ten = models.CharField("Họ và tên",max_length=255)
    chuc_vu = models.CharField("Chức vụ",max_length=255,blank=True)
    sdt = models.CharField("Số điện thoại",max_length=20,blank=True)
    role = models.CharField("Vai trò",max_length=20,choices=Role.choices, default=Role.CHUYEN_VIEN)

    chi_nhanh = models.ForeignKey("core.ChiNhanh",on_delete=models.SET_NULL,null=True,blank=True,related_name="users",verbose_name="Chi nhánh")
    phong_ban = models.ForeignKey("core.PhongBan",on_delete=models.SET_NULL,null=True,blank=True,related_name="users",verbose_name="Phòng ban")

    REQUIRED_FIELDS = ["email","ho_va_ten"]

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
# Create your models here.

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
        return self.role == self.Role.ADMIN
    @property
    def is_lanh_dao(self):
        return self.role == self.Role.LANH_DAO
    @property
    def is_van_thu(self):
        return self.role == self.Role.VAN_THU
    @property
    def is_chuyen_vien(self):
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
        return self.ROLE_PERMISSION_MAP.get(self.role, "")

    def has_role(self, *roles):
        return self.is_superuser or self.role in roles
