from django.conf import settings
from django.db import models
from django.utils import timezone


class ChiNhanh(models.Model):
    chi_nhanh_id = models.AutoField(primary_key=True)
    ten_chi_nhanh = models.CharField(max_length=255, null=False)

    class Meta:
        db_table = "ChiNhanh"

    def __str__(self):
        return self.ten_chi_nhanh


class DonViNgoai(models.Model):
    don_vi_ngoai_id = models.AutoField(primary_key=True)
    ten_don_vi = models.CharField(max_length=255, null=False)
    dia_chi = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True, unique=True)
    so_dien_thoai = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "DonViNgoai"

    def __str__(self):
        return self.ten_don_vi


class PhongBan(models.Model):
    phong_ban_id = models.AutoField(primary_key=True)
    chi_nhanh = models.ForeignKey(
        "core.ChiNhanh",
        on_delete=models.CASCADE,
        db_column="chi_nhanh_id",
        null=False,
    )
    truong_phong = models.ForeignKey(
        "core.NguoiDung",
        on_delete=models.SET_NULL,
        db_column="truong_phong_id",
        null=True,
        blank=True,
    )
    ten_phong_ban = models.CharField(max_length=255, null=False)

    class Meta:
        db_table = "PhongBan"

    def __str__(self):
        return self.ten_phong_ban


class NguoiDung(models.Model):
    class ChucVu(models.TextChoices):
        QUAN_TRI = "Quản Trị Hệ Thống", "Quản Trị Hệ Thống"
        LANH_DAO = "Lãnh Đạo", "Lãnh Đạo"
        CHUYEN_VIEN = "Chuyên Viên", "Chuyên Viên"
        VAN_THU = "Văn Thư", "Văn Thư"

    CHUC_VU_CHOICES = ChucVu.choices

    nguoi_dung_id = models.AutoField(primary_key=True)
    tai_khoan = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        db_column="tai_khoan_id",
        null=True,
        blank=True,
        related_name="nguoi_dung_core",
    )
    phong_ban = models.ForeignKey(
        "core.PhongBan",
        on_delete=models.SET_NULL,
        db_column="phong_ban_id",
        null=True,
        blank=True,
    )
    ho_va_ten = models.CharField(max_length=255, null=False)
    chuc_vu = models.CharField(
        max_length=255,
        null=False,
        choices=CHUC_VU_CHOICES,
    )
    email = models.EmailField(null=False, unique=True)
    sdt = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "NguoiDung"

    def __str__(self):
        return self.ho_va_ten


class HoSoVanBan(models.Model):
    THOI_GIAN_BAO_QUAN_CHOICES = (
        ("Theo quy định - 2 năm", "Theo quy định - 2 năm"),
        ("Theo quy định - 5 năm", "Theo quy định - 5 năm"),
        ("Theo quy định - 10 năm", "Theo quy định - 10 năm"),
        ("Vĩnh viễn", "Vĩnh viễn"),
        ("Tạm thời", "Tạm thời"),
    )

    TRANG_THAI_CHOICES = (
        (1, "Hiện hành"),
        (2, "Lưu trữ"),
    )

    ho_so_van_ban_id = models.AutoField(primary_key=True)
    tieu_de_ho_so = models.CharField(max_length=255, null=False)
    ky_hieu_ho_so = models.CharField(max_length=255, unique=True)
    ngay_tao_ho_so = models.DateField(auto_now_add=True)
    nguoi_tao = models.ForeignKey(
        "core.NguoiDung",
        on_delete=models.CASCADE,
        db_column="nguoi_tao_id",
        null=False,
    )
    ngay_cap_nhat = models.DateField(default=timezone.now)
    thoi_gian_bao_quan = models.CharField(
        max_length=255,
        null=False,
        choices=THOI_GIAN_BAO_QUAN_CHOICES,
    )
    so_nam_luu_tru = models.PositiveIntegerField(null=False)
    trang_thai = models.IntegerField(
        null=False,
        choices=TRANG_THAI_CHOICES,
        default=1,
    )
    mo_ta = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "HoSoVanBan"

    def __str__(self):
        return self.ky_hieu_ho_so


class NguoiXuLyHoSo(models.Model):
    nguoi_xu_ly_ho_so_id = models.AutoField(primary_key=True)
    ho_so_van_ban = models.ForeignKey(
        "core.HoSoVanBan",
        on_delete=models.CASCADE,
        db_column="ho_so_van_ban_id",
        null=False,
    )
    nguoi_xu_ly = models.ForeignKey(
        "core.NguoiDung",
        on_delete=models.CASCADE,
        db_column="nguoi_xu_ly_id",
        null=False,
    )

    class Meta:
        db_table = "NguoiXuLyHoSo"

    def __str__(self):
        return f"{self.nguoi_xu_ly} - {self.ho_so_van_ban}"


class PhongXemHoSo(models.Model):
    phong_xem_ho_so_id = models.AutoField(primary_key=True)
    ho_so_van_ban = models.ForeignKey(
        "core.HoSoVanBan",
        on_delete=models.CASCADE,
        db_column="ho_so_van_ban_id",
        null=False,
    )
    phong_ban = models.ForeignKey(
        "core.PhongBan",
        on_delete=models.CASCADE,
        db_column="phong_ban_id",
        null=False,
    )

    class Meta:
        db_table = "PhongXemHoSo"

    def __str__(self):
        return f"{self.phong_ban} - {self.ho_so_van_ban}"


class VanBan(models.Model):
    HINH_THUC_CHOICES = (
        ("Công văn", "Công văn"),
        ("Quyết định", "Quyết định"),
        ("Thông báo", "Thông báo"),
        ("Báo cáo", "Báo cáo"),
        ("Hợp đồng", "Hợp đồng"),
        ("Quy chế", "Quy chế"),
        ("Kế hoạch", "Kế hoạch"),
        ("Chỉ thị", "Chỉ thị"),
        ("Nghị quyết", "Nghị quyết"),
        ("Giấy mời", "Giấy mời"),
        ("Phiếu trình", "Phiếu trình"),
    )

    LOAI_VAN_BAN_CHOICES = (
        ("Văn bản điều hành", "Văn bản điều hành"),
        ("Văn bản tài chính", "Văn bản tài chính"),
        ("Văn bản pháp lý", "Văn bản pháp lý"),
        ("Văn bản nhân sự", "Văn bản nhân sự"),
        ("Báo cáo tài chính", "Báo cáo tài chính"),
        ("Hồ sơ kê khai thuế", "Hồ sơ kê khai thuế"),
        ("Văn bản kế hoạch", "Văn bản kế hoạch"),
        ("Văn bản dự án", "Văn bản dự án"),
        ("Báo cáo tiến độ", "Báo cáo tiến độ"),
    )

    DO_KHAN_CHOICES = (
        ("Hỏa tốc", "Hỏa tốc"),
        ("Khẩn", "Khẩn"),
        ("Bình thường", "Bình thường"),
    )

    DO_MAT_CHOICES = (
        ("Bình thường", "Bình thường"),
        ("Mật", "Mật"),
        ("Tuyệt Mật", "Tuyệt Mật"),
    )

    TRANG_THAI_CHOICES = (
        ("Chờ Xử Lý", "Chờ Xử Lý"),
        ("Đã Xử Lý", "Đã Xử Lý"),
        ("Hoàn Trả", "Hoàn Trả"),
        ("Xem Để Biết", "Xem Để Biết"),
        ("Chờ ban hành", "Chờ ban hành"),
        ("Đã ban hành", "Đã ban hành"),
    )

    PHAN_LOAI_CHOICES = (
        ("Văn bản đi", "Văn bản đi"),
        ("Văn bản đến", "Văn bản đến"),
    )
    
    DON_VI_SOAN_THAO_CHOICES = (
        ("Ban Giám Đốc", "Ban Giám Đốc"),
        ("Phòng Kế Toán", "Phòng Kế Toán"),
        ("Phòng Kiểm Toán", "Phòng Kiểm Toán"),
        ("Phòng Tư Vấn Thuế", "Phòng Tư Vấn Thuế"),
        ("Phòng Hành Chính/Nhân sự", "Phòng Hành Chính/Nhân sự"),
        ("Phòng Đào Tạo Chất Lượng", "Phòng Đào Tạo Chất Lượng"),
    )

    van_ban_id = models.AutoField(primary_key=True)
    lanh_dao_duyet = models.ForeignKey(
        "core.NguoiDung",
        on_delete=models.CASCADE,
        db_column="lanh_dao_duyet_id",
        null=False,
        related_name="+",
    )
    nguoi_tao = models.ForeignKey(
        "core.NguoiDung",
        on_delete=models.CASCADE,
        db_column="nguoi_tao_id",
        null=False,
        related_name="+",
    )
    ho_so_van_ban = models.ForeignKey(
        "core.HoSoVanBan",
        on_delete=models.SET_NULL,
        db_column="ho_so_van_ban_id",
        null=True,
        blank=True,
    )
    so_ky_hieu = models.CharField(max_length=255, null=False)
    trich_yeu = models.CharField(max_length=255, null=False)
    hinh_thuc = models.TextField(
        null=False,
        choices=HINH_THUC_CHOICES,
    )
    loai_van_ban = models.CharField(
        max_length=255,
        null=False,
        choices=LOAI_VAN_BAN_CHOICES,
    )
    don_vi_soan_thao = models.CharField(
        max_length=255,
        null=False,
        choices=DON_VI_SOAN_THAO_CHOICES,
    )
    ngay_van_ban = models.DateField(null=False)
    ngay_den = models.DateField(null=True)
    han_xu_ly = models.DateField(null=True, blank=True)
    ngay_cap_nhat = models.DateField(default=timezone.now)
    do_khan = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=DO_KHAN_CHOICES,
    )
    do_mat = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=DO_MAT_CHOICES,
    )
    file_dinh_kem = models.FileField(upload_to="van_ban/", null=False)
    kich_thuoc = models.BigIntegerField(null=False)
    trang_thai = models.CharField(
        max_length=255,
        null=False,
        choices=TRANG_THAI_CHOICES,
    )
    noi_dung = models.TextField(null=True)
    phan_loai = models.CharField(
        max_length=255,
        null=False,
        choices=PHAN_LOAI_CHOICES,
    )

    class Meta:
        db_table = "VanBan"

    def __str__(self):
        return self.so_ky_hieu


class VanBanLienQuan(models.Model):
    van_ban_lien_quan_id = models.AutoField(primary_key=True)
    van_ban = models.ForeignKey(
        "core.VanBan",
        on_delete=models.CASCADE,
        db_column="van_ban_id",
        null=True,
    )
    file_van_ban = models.FileField(upload_to="van_ban_lien_quan/")
    kich_thuoc = models.IntegerField()

    class Meta:
        db_table = "VanBanLienQuan"

    def __str__(self):
        return f"Văn bản liên quan {self.van_ban_lien_quan_id}"


class VanBanDuyet(models.Model):
    van_ban_duyet_id = models.AutoField(primary_key=True)
    van_ban = models.ForeignKey(
        "core.VanBan",
        on_delete=models.CASCADE,
        db_column="van_ban_id",
        null=False,
    )
    van_thu = models.ForeignKey(
        "core.NguoiDung",
        on_delete=models.CASCADE,
        db_column="van_thu_id",
        null=False,
    )
    ngay_duyet = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "VanBanDuyet"

    def __str__(self):
        return f"Văn bản duyệt {self.van_ban_duyet_id}"


class ChuyenTiep(models.Model):
    chuyen_tiep_id = models.AutoField(primary_key=True)
    van_ban_duyet = models.ForeignKey(
        "core.VanBanDuyet",
        on_delete=models.CASCADE,
        db_column="van_ban_duyet_id",
        null=False,
    )
    ngay_chuyen_tiep = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "ChuyenTiep"

    def __str__(self):
        return f"Chuyển tiếp {self.chuyen_tiep_id}"


class ChuyenTiepChiTiet(models.Model):
    chuyen_tiep_ct_id = models.AutoField(primary_key=True)
    chuyen_tiep = models.ForeignKey(
        "core.ChuyenTiep",
        on_delete=models.CASCADE,
        db_column="chuyen_tiep_id",
        null=False,
    )
    nguoi_dung = models.ForeignKey(
        "core.NguoiDung",
        on_delete=models.CASCADE,
        db_column="nguoi_dung_id",
        null=False,
    )
    phong_ban = models.ForeignKey(
        "core.PhongBan",
        on_delete=models.CASCADE,
        db_column="phong_ban_id",
        null=False,
    )

    class Meta:
        db_table = "ChuyenTiepChiTiet"

    def __str__(self):
        return f"Chi tiết chuyển tiếp {self.chuyen_tiep_ct_id}"


class BanHanh(models.Model):
    ban_hanh_id = models.AutoField(primary_key=True)
    van_ban = models.ForeignKey(
        "core.VanBan",
        on_delete=models.CASCADE,
        db_column="van_ban_id",
        null=False,
    )
    ngay_ban_hanh = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "BanHanh"

    def __str__(self):
        return f"Ban hành {self.ban_hanh_id}"


class BanHanhChiTiep(models.Model):
    ban_hanh_ct_id = models.AutoField(primary_key=True)
    ban_hanh = models.ForeignKey(
        "core.BanHanh",
        on_delete=models.CASCADE,
        db_column="ban_hanh_id",
        null=False,
    )
    phong_ban = models.ForeignKey(
        "core.PhongBan",
        on_delete=models.CASCADE,
        db_column="phong_ban_id",
        null=True,
        blank=True,
    )
    don_vi_ngoai = models.ForeignKey(
        "core.DonViNgoai",
        on_delete=models.CASCADE,
        db_column="don_vi_ngoai_id",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "BanHanhChiTiep"

    def __str__(self):
        return f"Ban hành chi tiết {self.ban_hanh_ct_id}"


class VanBanHoanTra(models.Model):
    van_ban_hoan_tra_id = models.AutoField(primary_key=True)
    van_ban = models.ForeignKey(
        "core.VanBan",
        on_delete=models.CASCADE,
        db_column="van_ban_id",
        null=False,
    )
    ngay_hoan_tra = models.DateField(auto_now_add=True)
    noi_dung = models.TextField(null=False)

    class Meta:
        db_table = "VanBanHoanTra"

    def __str__(self):
        return f"Hoàn trả văn bản {self.van_ban_hoan_tra_id}"


class CongViec(models.Model):
    class NguonGiao(models.TextChoices):
        VAN_BAN_DEN = "Văn bản đến", "Văn bản đến"
        VAN_BAN_DI = "Văn bản đi", "Văn bản đi"

    class TrangThai(models.TextChoices):
        CHO_XU_LY = "Chờ xử lý", "Chờ xử lý"
        DA_HOAN_THANH = "Đã hoàn thành", "Đã hoàn thành"
        HOAN_TRA_CV = "Hoàn trả_CV", "Hoàn trả CV"
        HOAN_TRA_LD = "Hoàn trả_LĐ", "Hoàn trả LĐ"
        CHO_DUYET = "Chờ duyệt", "Chờ duyệt"

    cong_viec_id = models.AutoField(primary_key=True)
    van_ban = models.ForeignKey(
        "core.VanBan",
        on_delete=models.CASCADE,
        db_column="van_ban_id",
        null=True,
        blank=True,
    )
    ten_cong_viec = models.CharField(max_length=255, null=False)
    noi_dung_cong_viec = models.TextField(null=False)
    nguon_giao = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=NguonGiao.choices,
    )
    trang_thai = models.CharField(
        max_length=255,
        null=False,
        choices=TrangThai.choices,
        default=TrangThai.CHO_XU_LY,
    )
    ngay_bat_dau = models.DateField(null=False)
    han_xu_ly = models.DateTimeField(null=False)
    ngay_cap_nhat_giao_viec = models.DateField(default=timezone.now)
    ket_qua_xu_ly = models.TextField(null=True, blank=True)
    ghi_chu = models.TextField(null=True, blank=True)
    ngay_xu_ly = models.DateField(default=timezone.now)
    last_activity = models.DateTimeField(auto_now=True)
    yeu_cau_phe_duyet = models.BooleanField(default=True)
    nguoi_giao = models.ForeignKey(
        "core.NguoiDung",
        on_delete=models.CASCADE,
        db_column="nguoi_giao_id",
        null=False,
        related_name="+",
    )
    nguoi_thuc_hien = models.ForeignKey(
        "core.NguoiDung",
        on_delete=models.CASCADE,
        db_column="nguoi_thuc_hien_id",
        null=False,
        related_name="+",
    )

    class Meta:
        db_table = "CongViec"

    def __str__(self):
        return self.ten_cong_viec

    @property
    def cho_phep_chuyen_vien_xu_ly(self):
        return self.trang_thai in {
            self.TrangThai.CHO_XU_LY,
            self.TrangThai.HOAN_TRA_CV,
        }

    @property
    def dang_cho_lanh_dao_xu_ly(self):
        return self.trang_thai == self.TrangThai.HOAN_TRA_LD


class PhanCongCongViec(models.Model):
    phan_cong_id = models.AutoField(primary_key=True)
    cong_viec = models.ForeignKey(
        "core.CongViec",
        on_delete=models.CASCADE,
        db_column="cong_viec_id",
        null=False,
    )
    nguoi_phoi_hop = models.ForeignKey(
        "core.NguoiDung",
        on_delete=models.CASCADE,
        db_column="nguoi_phoi_hop_id",
        null=False,
    )

    class Meta:
        db_table = "PhanCongCongViec"

    def __str__(self):
        return f"Phân công {self.phan_cong_id}"


class FileCVLienQuan(models.Model):
    class LoaiFile(models.TextChoices):
        CHINH = "CHINH", "Chính"
        LIEN_QUAN = "LIEN_QUAN", "Liên quan"

    class NguonTaiLen(models.TextChoices):
        GIAO_VIEC = "GIAO_VIEC", "File giao việc"
        KET_QUA_XU_LY = "KET_QUA_XU_LY", "File kết quả xử lý"

    file_cv_lien_quan_id = models.AutoField(primary_key=True)
    cong_viec = models.ForeignKey(
        "core.CongViec",
        on_delete=models.CASCADE,
        db_column="cong_viec_id",
        null=False,
    )
    file_van_ban = models.FileField(upload_to="file_cv_lien_quan/", null=False)
    kich_thuoc = models.IntegerField(null=True, blank=True)
    loai_file = models.CharField(
        max_length=20,
        choices=LoaiFile.choices,
        default=LoaiFile.LIEN_QUAN,
        null=False,
    )
    nguon_tai_len = models.CharField(
        max_length=30,
        choices=NguonTaiLen.choices,
        default=NguonTaiLen.GIAO_VIEC,
    )
    nguoi_tai_len = models.ForeignKey(
        "core.NguoiDung",
        on_delete=models.SET_NULL,
        db_column="nguoi_tai_len_id",
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        db_table = "FileCVLienQuan"

    def __str__(self):
        return f"File công việc {self.file_cv_lien_quan_id}"

    @property
    def la_file_ket_qua(self):
        return self.nguon_tai_len == self.NguonTaiLen.KET_QUA_XU_LY


class HoanTraCongViec(models.Model):
    hoan_tra_cong_viec_id = models.AutoField(primary_key=True)
    cong_viec = models.ForeignKey(
        "core.CongViec",
        on_delete=models.CASCADE,
        db_column="cong_viec_id",
        null=False,
    )
    nguoi_hoan_tra = models.ForeignKey(
        "core.NguoiDung",
        on_delete=models.SET_NULL,
        db_column="nguoi_hoan_tra_id",
        null=True,
        blank=True,
        related_name="+",
    )
    ngay_hoan_tra = models.DateField(auto_now_add=True)
    noi_dung = models.TextField(null=False)

    class Meta:
        db_table = "HoanTraCongViec"

    def __str__(self):
        return f"Hoàn trả công việc {self.hoan_tra_cong_viec_id}"


class PheDuyetCongViec(models.Model):
    phe_duyet_cv_id = models.AutoField(primary_key=True)
    cong_viec = models.ForeignKey(
        "core.CongViec",
        on_delete=models.CASCADE,
        db_column="cong_viec_id",
        null=False,
    )
    ngay_duyet = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "PheDuyetCongViec"

    def __str__(self):
        return f"Phê duyệt công việc {self.phe_duyet_cv_id}"
