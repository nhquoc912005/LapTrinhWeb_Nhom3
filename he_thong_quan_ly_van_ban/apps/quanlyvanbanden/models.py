from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone


class VanBanDen(models.Model):
    class LoaiVanBan(models.TextChoices):
        HANH_CHINH = "HANH_CHINH", "Hành chính"
        QUYET_DINH = "QUYET_DINH", "Quyết định"
        CONG_VAN = "CONG_VAN", "Công văn"
        THONG_TU = "THONG_TU", "Thông tư"
        THONG_BAO = "THONG_BAO", "Thông báo"
        BAO_CAO = "BAO_CAO", "Báo cáo"
        KE_HOACH = "KE_HOACH", "Kế hoạch"

    class HinhThucVanBan(models.TextChoices):
        CONG_VAN = "CONG_VAN", "Công văn"
        QUYET_DINH = "QUYET_DINH", "Quyết định"
        THONG_TU = "THONG_TU", "Thông tư"
        THONG_BAO = "THONG_BAO", "Thông báo"
        TO_TRINH = "TO_TRINH", "Tờ trình"

    class DoMat(models.TextChoices):
        BINH_THUONG = "BINH_THUONG", "Bình thường"
        MAT = "MAT", "Mật"
        TOI_MAT = "TOI_MAT", "Tối mật"

    class DoKhan(models.TextChoices):
        BINH_THUONG = "BINH_THUONG", "Bình thường"
        KHAN = "KHAN", "Khẩn"
        HOA_TOC = "HOA_TOC", "Hỏa tốc"

    class TrangThai(models.TextChoices):
        CHO_XU_LY = "CHO_XU_LY", "Chờ xử lý"
        DA_XU_LY = "DA_XU_LY", "Đã xử lý"
        HOAN_TRA = "HOAN_TRA", "Hoàn trả"
        XEM_DE_BIET = "XEM_DE_BIET", "Xem để biết"

    so_ky_hieu = models.CharField(max_length=100, unique=True)
    don_vi_ban_hanh = models.CharField(max_length=255)
    trich_yeu = models.CharField(max_length=500)
    loai_van_ban = models.CharField(
        max_length=50,
        choices=LoaiVanBan.choices,
        default=LoaiVanBan.HANH_CHINH,
    )
    hinh_thuc_van_ban = models.CharField(
        max_length=30,
        choices=HinhThucVanBan.choices,
        default=HinhThucVanBan.CONG_VAN,
    )
    ngay_van_ban = models.DateField()
    ngay_den = models.DateField(default=timezone.now)
    han_xu_ly = models.DateField(blank=True, null=True)
    do_mat = models.CharField(
        max_length=20,
        choices=DoMat.choices,
        default=DoMat.BINH_THUONG,
    )
    do_khan = models.CharField(
        max_length=20,
        choices=DoKhan.choices,
        default=DoKhan.BINH_THUONG,
    )
    linh_vuc = models.CharField(max_length=255, blank=True, null=True)
    noi_dung_xu_ly = models.TextField(blank=True)
    ly_do_hoan_tra = models.TextField(blank=True)
    ngay_hoan_tra = models.DateField(blank=True, null=True)
    trang_thai = models.CharField(
        max_length=20,
        choices=TrangThai.choices,
        default=TrangThai.CHO_XU_LY,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    lanh_dao_xu_ly = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="van_ban_den_duoc_giao",
        limit_choices_to={"role": "LANH_DAO"},
    )
    nguoi_tao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="van_ban_den_da_tao",
    )

    def __str__(self):
        return self.so_ky_hieu


class TepVanBanDen(models.Model):
    class LoaiTep(models.TextChoices):
        DINH_KEM = "DINH_KEM", "File đính kèm"
        LIEN_QUAN = "LIEN_QUAN", "Tài liệu liên quan"

    van_ban_den = models.ForeignKey(
        VanBanDen,
        on_delete=models.CASCADE,
        related_name="tep_tin",
    )
    loai = models.CharField(max_length=20, choices=LoaiTep.choices)
    tep = models.FileField(
        upload_to="van_ban_den/tep_tin/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    "pdf",
                    "doc",
                    "docx",
                    "xls",
                    "xlsx",
                    "png",
                    "jpg",
                    "jpeg",
                ],
            ),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.tep.name


class VanBanDenChuyenTiep(models.Model):
    van_ban_den = models.ForeignKey(
        VanBanDen,
        on_delete=models.CASCADE,
        related_name="ds_chuyen_tiep",
    )
    chuyen_vien = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="van_ban_den_duoc_chuyen_tiep",
        limit_choices_to={"role": "CHUYEN_VIEN"},
    )
    nguoi_chuyen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="van_ban_den_da_chuyen_tiep",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("van_ban_den", "chuyen_vien"),)

    def __str__(self):
        return f"{self.van_ban_den} -> {self.chuyen_vien}"
