"""
Helper ghi lịch sử hoạt động vào bảng LichSuHoatDong.

Dùng trong các view để tự động ghi lại ai làm gì, lúc nào.
Nếu ghi lịch sử lỗi thì bỏ qua an toàn – không crash chức năng chính.
"""
import logging

logger = logging.getLogger(__name__)


def _lay_nguoi_dung_core(user):
    # Resolve Customer sang NguoiDung để lịch sử hoạt động lưu đúng người thực hiện.
    """Lấy NguoiDung từ request.user (dùng nội bộ)."""
    if not user or not user.is_authenticated:
        return None
    try:
        from apps.core.models import NguoiDung
        nd = NguoiDung.objects.filter(tai_khoan=user).first()
        if not nd and getattr(user, "email", None):
            nd = NguoiDung.objects.filter(email=user.email).first()
        return nd
    except Exception:
        return None


def ghi_lich_su(
    *,
    user=None,
    nguoi_dung=None,
    doi_tuong_loai: str,
    doi_tuong_id: int,
    hanh_dong: str,
    mo_ta: str = "",
    truoc_thay_doi: dict = None,
    sau_thay_doi: dict = None,
):
    # Hàm ghi audit log dùng chung; lỗi ghi log không được làm hỏng nghiệp vụ chính.
    """
    Ghi một bản ghi vào LichSuHoatDong.

    Tham số:
        user        – request.user (nếu không truyền nguoi_dung)
        nguoi_dung  – core.NguoiDung (nếu đã resolve trước)
        doi_tuong_loai – "VAN_BAN" | "CONG_VIEC" | "HO_SO"
        doi_tuong_id   – pk của đối tượng
        hanh_dong      – "TAO" | "SUA" | "XOA" | "DUYET" | "HOAN_TRA"
                         | "CHUYEN_TIEP" | "BAN_HANH" | "KY_SO"
        mo_ta       – mô tả tùy chọn
        truoc_thay_doi – dict JSON trạng thái trước (tuỳ chọn)
        sau_thay_doi   – dict JSON trạng thái sau (tuỳ chọn)
    """
    try:
        from apps.core.models import LichSuHoatDong

        if nguoi_dung is None and user is not None:
            nguoi_dung = _lay_nguoi_dung_core(user)

        LichSuHoatDong.objects.create(
            doi_tuong_loai=doi_tuong_loai,
            doi_tuong_id=doi_tuong_id,
            nguoi_thuc_hien=nguoi_dung,
            hanh_dong=hanh_dong,
            mo_ta=mo_ta or "",
            truoc_thay_doi=truoc_thay_doi,
            sau_thay_doi=sau_thay_doi,
        )
    except Exception as exc:
        logger.warning("Không thể ghi lịch sử hoạt động: %s", exc)


# ─── Shortcut wrappers theo loại đối tượng ────────────────────────────────────

def ghi_lich_su_van_ban(*, user=None, nguoi_dung=None, van_ban, hanh_dong: str, mo_ta: str = "", trang_thai_cu: str = "", trang_thai_moi: str = ""):
    # Shortcut ghi lịch sử cho thao tác trên văn bản.
    truoc = {"trang_thai": trang_thai_cu} if trang_thai_cu else None
    sau = {"trang_thai": trang_thai_moi} if trang_thai_moi else None
    ghi_lich_su(
        user=user,
        nguoi_dung=nguoi_dung,
        doi_tuong_loai="VAN_BAN",
        doi_tuong_id=van_ban.pk,
        hanh_dong=hanh_dong,
        mo_ta=mo_ta or f"{hanh_dong} văn bản [{van_ban.so_ky_hieu}]",
        truoc_thay_doi=truoc,
        sau_thay_doi=sau,
    )


def ghi_lich_su_cong_viec(*, user=None, nguoi_dung=None, cong_viec, hanh_dong: str, mo_ta: str = "", trang_thai_cu: str = "", trang_thai_moi: str = ""):
    # Shortcut ghi lịch sử cho thao tác trên công việc.
    truoc = {"trang_thai": trang_thai_cu} if trang_thai_cu else None
    sau = {"trang_thai": trang_thai_moi} if trang_thai_moi else None
    ghi_lich_su(
        user=user,
        nguoi_dung=nguoi_dung,
        doi_tuong_loai="CONG_VIEC",
        doi_tuong_id=cong_viec.pk,
        hanh_dong=hanh_dong,
        mo_ta=mo_ta or f"{hanh_dong} công việc [{cong_viec.ten_cong_viec}]",
        truoc_thay_doi=truoc,
        sau_thay_doi=sau,
    )


def ghi_lich_su_ho_so(*, user=None, nguoi_dung=None, ho_so, hanh_dong: str, mo_ta: str = ""):
    # Shortcut ghi lịch sử cho thao tác trên hồ sơ văn bản.
    ghi_lich_su(
        user=user,
        nguoi_dung=nguoi_dung,
        doi_tuong_loai="HO_SO",
        doi_tuong_id=ho_so.pk,
        hanh_dong=hanh_dong,
        mo_ta=mo_ta or f"{hanh_dong} hồ sơ [{ho_so.tieu_de_ho_so}]",
    )
