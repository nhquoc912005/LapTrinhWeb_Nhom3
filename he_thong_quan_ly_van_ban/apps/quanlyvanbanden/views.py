import os
import json
from datetime import timedelta
from types import SimpleNamespace

from django.conf import settings
from django.core.files.base import ContentFile
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required
from apps.accounts.models import Customer
from apps.core.models import (
    ChuyenTiep,
    ChuyenTiepChiTiet,
    NguoiDung,
    VanBan,
    VanBanDuyet,
    VanBanHoanTra,
    VanBanLienQuan,
    HoSoVanBan,
    ChuKySo,
    LichSuKySo,
)

from .forms import VanBanDenForm
from apps.core.models import CongViec
from apps.core.utils.activity_log import ghi_lich_su_van_ban
from apps.quanlyvanbandi.utils_ky_so import sign_pdf_with_ratio


# =========================================================
# HẰNG SỐ DÙNG CHUNG
# =========================================================

PHAN_LOAI_VAN_BAN_DEN = 'Văn bản đến'

TRANG_THAI_CHO_XU_LY = 'Chờ Xử Lý'
TRANG_THAI_DA_XU_LY = 'Đã Xử Lý'
TRANG_THAI_HOAN_TRA = 'Hoàn Trả'
TRANG_THAI_XEM_DE_BIET = 'Xem Để Biết'


# =========================================================
# HÀM HỖ TRỢ
# =========================================================

def _lay_nguoi_dung_core(user):
    """
    Lấy NguoiDung trong app core từ tài khoản đang đăng nhập.
    Model chung VanBan dùng core.NguoiDung, không dùng trực tiếp accounts.Customer.
    """
    if not user or not user.is_authenticated:
        return None

    nguoi_dung = NguoiDung.objects.filter(tai_khoan=user).first()

    if not nguoi_dung and getattr(user, 'email', None):
        nguoi_dung = NguoiDung.objects.filter(email=user.email).first()

    return nguoi_dung


def _kiem_tra_nguoi_dung_core(request):
    nguoi_dung = _lay_nguoi_dung_core(request.user)

    if not nguoi_dung:
        messages.error(
            request,
            'Tài khoản của bạn chưa được liên kết với hồ sơ người dùng trong hệ thống.'
        )
        return None

    return nguoi_dung


def _xoa_file_vat_ly(file_field):
    if file_field:
        file_field.delete(save=False)


def _ten_file(file_field):
    if file_field:
        return os.path.basename(file_field.name)
    return ''


def _gan_alias_van_ban(vb):
    """
    Giữ alias tên cũ để template cũ ít bị vỡ hơn.

    Tên cũ bên app quanlyvanbanden:
    - hinh_thuc_van_ban
    - noi_dung_xu_ly
    - lanh_dao_xu_ly
    - ly_do_hoan_tra
    - ngay_hoan_tra

    Tên thật trong model chung:
    - hinh_thuc
    - noi_dung
    - lanh_dao_duyet
    - VanBanHoanTra.noi_dung
    - VanBanHoanTra.ngay_hoan_tra
    """

    vb.id = vb.pk
    vb.hinh_thuc_van_ban = vb.hinh_thuc
    vb.noi_dung_xu_ly = vb.noi_dung
    vb.lanh_dao_xu_ly = vb.lanh_dao_duyet
    vb.lanh_dao_xu_ly_id = vb.lanh_dao_duyet_id
    vb.created_at = vb.ngay_cap_nhat
    vb.updated_at = vb.ngay_cap_nhat

    hoan_tra = VanBanHoanTra.objects.filter(
        van_ban=vb
    ).order_by('-ngay_hoan_tra', '-van_ban_hoan_tra_id').first()

    vb.ly_do_hoan_tra = hoan_tra.noi_dung if hoan_tra else ''
    vb.ngay_hoan_tra = hoan_tra.ngay_hoan_tra if hoan_tra else None

    return vb


def _gan_alias_danh_sach(ds_van_ban):
    for vb in ds_van_ban:
        _gan_alias_van_ban(vb)

    return ds_van_ban


def _lanh_dao_co_quyen_xu_ly(vb, nguoi_dung_core):
    return (
        nguoi_dung_core
        and nguoi_dung_core.chuc_vu == NguoiDung.ChucVu.LANH_DAO
        and vb.lanh_dao_duyet_id == nguoi_dung_core.pk
    )


def _chuyen_vien_duoc_phan_cong(vb, nguoi_dung_core):
    if not nguoi_dung_core:
        return False

    return ChuyenTiepChiTiet.objects.filter(
        chuyen_tiep__van_ban_duyet__van_ban=vb,
        nguoi_dung=nguoi_dung_core,
    ).exists()


def _lay_file_dinh_kem_list(vb):
    """
    Model chung chỉ có 1 file chính: VanBan.file_dinh_kem.
    Hàm này bọc lại thành list để template cũ vẫn có thể for.
    """
    if not vb.file_dinh_kem:
        return []

    return [
        SimpleNamespace(
            id='main',
            pk='main',
            tep=vb.file_dinh_kem,
            file_van_ban=vb.file_dinh_kem,
            ten_file=_ten_file(vb.file_dinh_kem),
            created_at=vb.ngay_cap_nhat,
            loai='DINH_KEM',
        )
    ]


def _lay_tai_lieu_lien_quan_list(vb):
    ds_file = VanBanLienQuan.objects.filter(
        van_ban=vb
    ).order_by('van_ban_lien_quan_id')

    ket_qua = []

    for tep in ds_file:
        tep.id = tep.pk
        tep.tep = tep.file_van_ban
        tep.ten_file = _ten_file(tep.file_van_ban)
        tep.created_at = None
        tep.loai = 'LIEN_QUAN'
        ket_qua.append(tep)

    return ket_qua


def _lay_ds_chuyen_tiep(vb):
    """
    Model chung:
    VanBan -> VanBanDuyet -> ChuyenTiep -> ChuyenTiepChiTiet

    Template cũ có thể đang dùng:
    - item.chuyen_vien
    - item.nguoi_chuyen
    - item.created_at

    Nên hàm này bọc dữ liệu chung về dạng gần giống model cũ.
    """
    ds = ChuyenTiepChiTiet.objects.select_related(
        'nguoi_dung',
        'phong_ban',
        'chuyen_tiep',
        'chuyen_tiep__van_ban_duyet',
        'chuyen_tiep__van_ban_duyet__van_thu',
    ).filter(
        chuyen_tiep__van_ban_duyet__van_ban=vb
    ).order_by('chuyen_tiep__ngay_chuyen_tiep', 'chuyen_tiep_ct_id')

    ket_qua = []

    for item in ds:
        chuyen_vien = item.nguoi_dung
        chuyen_vien.id = chuyen_vien.pk

        ket_qua.append(
            SimpleNamespace(
                id=item.pk,
                pk=item.pk,
                chuyen_vien=chuyen_vien,
                nguoi_chuyen=item.chuyen_tiep.van_ban_duyet.van_thu,
                created_at=item.chuyen_tiep.ngay_chuyen_tiep,
                phong_ban=item.phong_ban,
            )
        )

    return ket_qua


def _lay_chuyen_viens():
    ds = list(
        NguoiDung.objects.select_related(
            'phong_ban',
            'tai_khoan',
        ).filter(
            chuc_vu=NguoiDung.ChucVu.CHUYEN_VIEN
        ).order_by('phong_ban__ten_phong_ban', 'ho_va_ten')
    )

    for nd in ds:
        nd.id = nd.pk
        nd.role = Customer.Role.CHUYEN_VIEN
        nd.username = nd.tai_khoan.username if nd.tai_khoan else nd.email
        nd.get_full_name = lambda nd=nd: nd.ho_va_ten

    return ds


def _lay_hoac_tao_van_ban_duyet(vb):
    van_thu = vb.nguoi_tao

    obj, created = VanBanDuyet.objects.get_or_create(
        van_ban=vb,
        van_thu=van_thu,
    )

    return obj


def _xoa_chuyen_tiep_cu(vb):
    ChuyenTiep.objects.filter(
        van_ban_duyet__van_ban=vb
    ).delete()


def gan_thong_tin_canh_bao_han_xu_ly(ds_van_ban):
    today = timezone.localdate()

    for vb in ds_van_ban:
        if vb.han_xu_ly:
            so_ngay_con_lai = (vb.han_xu_ly - today).days
            vb.so_ngay_con_lai = so_ngay_con_lai
            vb.so_ngay_qua_han = abs(so_ngay_con_lai) if so_ngay_con_lai < 0 else 0
        else:
            vb.so_ngay_con_lai = None
            vb.so_ngay_qua_han = 0

        _gan_alias_van_ban(vb)

    return ds_van_ban


# =========================================================
# DANH SÁCH VĂN BẢN ĐẾN
# =========================================================

@login_required
@role_required(Customer.Role.VAN_THU, Customer.Role.LANH_DAO, Customer.Role.CHUYEN_VIEN)
def danh_sach_van_ban_den(request):
    nguoi_dung_core = _kiem_tra_nguoi_dung_core(request)

    if not nguoi_dung_core:
        return redirect('accounts:login')

    ds = VanBan.objects.select_related(
        'nguoi_tao',
        'lanh_dao_duyet',
        'ho_so_van_ban',
    ).filter(
        phan_loai=PHAN_LOAI_VAN_BAN_DEN
    ).order_by('-ngay_cap_nhat', '-van_ban_id')

    q = request.GET.get('q', '').strip()
    loai_van_ban = request.GET.get('loai_van_ban', '').strip()
    hinh_thuc_van_ban = request.GET.get('hinh_thuc_van_ban', '').strip()
    do_mat = request.GET.get('do_mat', '').strip()
    do_khan = request.GET.get('do_khan', '').strip()
    trang_thai = request.GET.get('trang_thai', '').strip()

    today = timezone.localdate()
    han_canh_bao = today + timedelta(days=3)

    canh_bao_qs = VanBan.objects.select_related(
        'nguoi_tao',
        'lanh_dao_duyet',
    ).filter(
        phan_loai=PHAN_LOAI_VAN_BAN_DEN,
        han_xu_ly__isnull=False,
        han_xu_ly__lte=han_canh_bao,
        trang_thai__in=[
            TRANG_THAI_CHO_XU_LY,
            TRANG_THAI_HOAN_TRA,
        ]
    )

    canh_bao_van_ban_sap_het_han = []

    if request.user.is_lanh_dao:
        ds = ds.filter(lanh_dao_duyet=nguoi_dung_core)

        canh_bao_van_ban_sap_het_han = canh_bao_qs.filter(
            lanh_dao_duyet=nguoi_dung_core
        ).order_by('han_xu_ly')[:20]

    elif request.user.is_chuyen_vien:
        ds = ds.filter(
            vanbanduyet__chuyentiep__chuyentiepchitiet__nguoi_dung=nguoi_dung_core
        ).distinct()

        # Chuyên viên chỉ xem văn bản được chuyển tiếp nên không hiển thị cảnh báo hạn xử lý.
        canh_bao_van_ban_sap_het_han = []

    elif request.user.is_van_thu:
        canh_bao_van_ban_sap_het_han = canh_bao_qs.order_by('han_xu_ly')[:20]

    canh_bao_van_ban_sap_het_han = gan_thong_tin_canh_bao_han_xu_ly(
        canh_bao_van_ban_sap_het_han
    )

    if q:
        ds = ds.filter(
            Q(so_ky_hieu__icontains=q) |
            Q(trich_yeu__icontains=q) |
            Q(don_vi_ban_hanh__icontains=q)
        )

    if loai_van_ban:
        ds = ds.filter(loai_van_ban=loai_van_ban)

    if hinh_thuc_van_ban:
        ds = ds.filter(hinh_thuc=hinh_thuc_van_ban)

    if do_mat:
        ds = ds.filter(do_mat=do_mat)

    if do_khan:
        ds = ds.filter(do_khan=do_khan)

    if trang_thai:
        ds = ds.filter(trang_thai=trang_thai)

    paginator = Paginator(ds, 10)
    page_number = request.GET.get('page')
    ds = paginator.get_page(page_number)

    _gan_alias_danh_sach(ds)

    context = {
        'ds': ds,
        'page_obj': ds,
        'q': q,
        'selected_loai_van_ban': loai_van_ban,
        'selected_hinh_thuc_van_ban': hinh_thuc_van_ban,
        'selected_do_mat': do_mat,
        'selected_do_khan': do_khan,
        'selected_trang_thai': trang_thai,
        'loai_van_ban_choices': VanBan.LOAI_VAN_BAN_CHOICES,
        'hinh_thuc_van_ban_choices': VanBan.HINH_THUC_CHOICES,
        'do_mat_choices': VanBan.DO_MAT_CHOICES,
        'do_khan_choices': VanBan.DO_KHAN_CHOICES,
        'trang_thai_choices': VanBan.TRANG_THAI_CHOICES,
        'canh_bao_van_ban_sap_het_han': canh_bao_van_ban_sap_het_han,
    }

    if request.user.is_lanh_dao:
        return render(request, 'van_ban_den/lanhdao/danh_sach.html', context)

    if request.user.is_chuyen_vien:
        return render(request, 'van_ban_den/chuyenvien/danh_sach.html', context)

    return render(request, 'van_ban_den/vanthu/danh_sach.html', context)


# =========================================================
# CHI TIẾT VĂN BẢN ĐẾN
# =========================================================

@login_required
@role_required(Customer.Role.VAN_THU, Customer.Role.LANH_DAO, Customer.Role.CHUYEN_VIEN)
@ensure_csrf_cookie
def chi_tiet_van_ban_den(request, pk):
    nguoi_dung_core = _kiem_tra_nguoi_dung_core(request)

    if not nguoi_dung_core:
        return redirect('accounts:login')

    vb = get_object_or_404(
        VanBan.objects.select_related('nguoi_tao', 'lanh_dao_duyet'),
        pk=pk,
        phan_loai=PHAN_LOAI_VAN_BAN_DEN,
    )

    _gan_alias_van_ban(vb)

    if request.user.is_lanh_dao and not _lanh_dao_co_quyen_xu_ly(vb, nguoi_dung_core):
        messages.error(request, 'Bạn không có quyền xem văn bản này.')
        return redirect('quanlyvanbanden:danh_sach')

    if request.user.is_chuyen_vien and not _chuyen_vien_duoc_phan_cong(vb, nguoi_dung_core):
        messages.error(request, 'Bạn không có quyền xem văn bản này.')
        return redirect('quanlyvanbanden:danh_sach')

    file_dinh_kem_list = _lay_file_dinh_kem_list(vb)
    tai_lieu_lien_quan_list = _lay_tai_lieu_lien_quan_list(vb)

    ds_ho_so = HoSoVanBan.objects.filter(trang_thai=1).order_by('-ho_so_van_ban_id')

    context = {
        'vb': vb,
        'file_dinh_kem_list': file_dinh_kem_list,
        'tai_lieu_lien_quan_list': tai_lieu_lien_quan_list,
        'task': CongViec.objects.filter(van_ban_den=vb).first(),
        'ds_ho_so': ds_ho_so,
        'is_van_thu': request.user.is_van_thu,
    }

    if request.user.is_lanh_dao:
        context.update({
            'chuyen_viens': _lay_chuyen_viens(),
            'ds_chuyen_tiep': _lay_ds_chuyen_tiep(vb),
        })

        template_name = 'van_ban_den/lanhdao/chi_tiet.html'

    elif request.user.is_chuyen_vien:
        context.update({
            'ds_chuyen_tiep': _lay_ds_chuyen_tiep(vb),
        })

        template_name = 'van_ban_den/chuyenvien/chi_tiet.html'

    else:
        template_name = 'van_ban_den/vanthu/chi_tiet.html'

    return render(request, template_name, context)


# =========================================================
# VĂN THƯ - THÊM VĂN BẢN ĐẾN
# =========================================================

@login_required
@role_required(Customer.Role.VAN_THU)
def them_van_ban_den(request):
    nguoi_dung_core = _kiem_tra_nguoi_dung_core(request)

    if not nguoi_dung_core:
        return redirect('accounts:login')

    lanh_daos = NguoiDung.objects.filter(
        chuc_vu=NguoiDung.ChucVu.LANH_DAO
    ).order_by('ho_va_ten')

    if request.method == 'POST':
        form = VanBanDenForm(request.POST, request.FILES)

        file_dinh_kem_files = request.FILES.getlist('file_dinh_kem_files')
        file_dinh_kem_don = request.FILES.get('file_dinh_kem')

        file_chinh = file_dinh_kem_files[0] if file_dinh_kem_files else file_dinh_kem_don

        if not file_chinh:
            messages.error(request, 'Vui lòng chọn ít nhất 1 file đính kèm chính.')
        elif form.is_valid():
            vb = form.save(commit=False)

            vb.nguoi_tao = nguoi_dung_core
            vb.trang_thai = TRANG_THAI_CHO_XU_LY
            vb.phan_loai = PHAN_LOAI_VAN_BAN_DEN
            vb.file_dinh_kem = file_chinh
            vb.kich_thuoc = file_chinh.size

            vb.save()

            # Nếu input file_dinh_kem_files cho phép nhiều file,
            # file đầu tiên là file chính, các file còn lại lưu vào văn bản liên quan.
            for f in file_dinh_kem_files[1:]:
                VanBanLienQuan.objects.create(
                    van_ban=vb,
                    file_van_ban=f,
                    kich_thuoc=f.size
                )

            for f in request.FILES.getlist('tai_lieu_lien_quan_files'):
                VanBanLienQuan.objects.create(
                    van_ban=vb,
                    file_van_ban=f,
                    kich_thuoc=f.size
                )

            ghi_lich_su_van_ban(
                user=request.user, van_ban=vb, hanh_dong="TAO",
                mo_ta=f"Thêm văn bản đến [{vb.so_ky_hieu}]",
            )

            messages.success(request, 'Trình văn bản đến thành công.')
            return redirect('quanlyvanbanden:danh_sach')
    else:
        form = VanBanDenForm()

    return render(request, 'van_ban_den/vanthu/them.html', {
        'form': form,
        'lanh_daos': lanh_daos,
    })


# =========================================================
# VĂN THƯ - SỬA VĂN BẢN ĐẾN
# =========================================================

@login_required
@role_required(Customer.Role.VAN_THU)
def sua_van_ban_den(request, pk):
    nguoi_dung_core = _kiem_tra_nguoi_dung_core(request)

    if not nguoi_dung_core:
        return redirect('accounts:login')

    vb = get_object_or_404(
        VanBan,
        pk=pk,
        phan_loai=PHAN_LOAI_VAN_BAN_DEN,
    )

    _gan_alias_van_ban(vb)

    if vb.trang_thai in [
        TRANG_THAI_DA_XU_LY,
        TRANG_THAI_XEM_DE_BIET,
    ]:
        messages.error(
            request,
            'Văn bản này đã được lãnh đạo lưu hoặc chuyển tiếp nên văn thư không thể chỉnh sửa.'
        )
        return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)

    lanh_daos = NguoiDung.objects.filter(
        chuc_vu=NguoiDung.ChucVu.LANH_DAO
    ).order_by('ho_va_ten')

    old_trang_thai = vb.trang_thai

    if request.method == 'POST':
        form = VanBanDenForm(request.POST, request.FILES, instance=vb)

        if form.is_valid():
            vb = form.save(commit=False)

            if old_trang_thai == TRANG_THAI_HOAN_TRA:
                vb.trang_thai = TRANG_THAI_CHO_XU_LY

            file_dinh_kem_files = request.FILES.getlist('file_dinh_kem_files')
            file_dinh_kem_don = request.FILES.get('file_dinh_kem')
            file_chinh_moi = file_dinh_kem_files[0] if file_dinh_kem_files else file_dinh_kem_don

            if file_chinh_moi:
                if vb.file_dinh_kem:
                    _xoa_file_vat_ly(vb.file_dinh_kem)

                vb.file_dinh_kem = file_chinh_moi
                vb.kich_thuoc = file_chinh_moi.size

            if not vb.file_dinh_kem:
                messages.error(request, 'Văn bản phải có file đính kèm chính.')
            else:
                vb.save()

                delete_lien_quan_ids = request.POST.getlist('delete_tai_lieu_lien_quan_ids')

                if delete_lien_quan_ids:
                    tep_xoa = VanBanLienQuan.objects.filter(
                        van_ban_lien_quan_id__in=delete_lien_quan_ids,
                        van_ban=vb,
                    )

                    for tep in tep_xoa:
                        _xoa_file_vat_ly(tep.file_van_ban)
                        tep.delete()

                # Nếu có nhiều file đính kèm mới, file đầu là file chính,
                # các file còn lại thêm vào tài liệu liên quan.
                for f in file_dinh_kem_files[1:]:
                    VanBanLienQuan.objects.create(
                        van_ban=vb,
                        file_van_ban=f,
                        kich_thuoc=f.size
                    )

                for f in request.FILES.getlist('tai_lieu_lien_quan_files'):
                    VanBanLienQuan.objects.create(
                        van_ban=vb,
                        file_van_ban=f,
                        kich_thuoc=f.size
                    )

                ghi_lich_su_van_ban(
                    user=request.user, van_ban=vb, hanh_dong="SUA",
                    mo_ta=f"Sửa văn bản đến [{vb.so_ky_hieu}]",
                )

                messages.success(request, 'Chỉnh sửa văn bản đến thành công.')
                return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)
    else:
        form = VanBanDenForm(instance=vb)

    file_dinh_kem_list = _lay_file_dinh_kem_list(vb)
    tai_lieu_lien_quan_list = _lay_tai_lieu_lien_quan_list(vb)

    return render(request, 'van_ban_den/vanthu/sua.html', {
        'form': form,
        'vb': vb,
        'lanh_daos': lanh_daos,
        'file_dinh_kem_list': file_dinh_kem_list,
        'tai_lieu_lien_quan_list': tai_lieu_lien_quan_list,
    })


# =========================================================
# VĂN THƯ - XÓA VĂN BẢN ĐẾN
# =========================================================

@login_required
@role_required(Customer.Role.VAN_THU)
def xoa_van_ban_den(request, pk):
    vb = get_object_or_404(
        VanBan,
        pk=pk,
        phan_loai=PHAN_LOAI_VAN_BAN_DEN,
    )

    _gan_alias_van_ban(vb)

    if request.method == 'POST':
        # Chỉ cho xóa khi văn bản chưa được xử lý
        if vb.trang_thai not in [TRANG_THAI_CHO_XU_LY, TRANG_THAI_HOAN_TRA]:
            messages.error(request, 'Chỉ được xóa văn bản đến ở trạng thái Chờ Xử Lý hoặc Hoàn Trả.')
            return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)

        if vb.file_dinh_kem:
            _xoa_file_vat_ly(vb.file_dinh_kem)

        for tep in VanBanLienQuan.objects.filter(van_ban=vb):
            _xoa_file_vat_ly(tep.file_van_ban)
            tep.delete()

        ghi_lich_su_van_ban(
            user=request.user, van_ban=vb, hanh_dong="XOA",
            trang_thai_cu=vb.trang_thai,
        )
        vb.delete()

        messages.success(request, 'Xóa văn bản đến thành công.')
        return redirect('quanlyvanbanden:danh_sach')

    return render(request, 'van_ban_den/vanthu/xoa.html', {
        'vb': vb,
    })


# =========================================================
# LÃNH ĐẠO - LƯU / XEM ĐỂ BIẾT
# =========================================================

@login_required
@role_required(Customer.Role.LANH_DAO)
def lanh_dao_luu_van_ban_den(request, pk):
    nguoi_dung_core = _kiem_tra_nguoi_dung_core(request)

    if not nguoi_dung_core:
        return redirect('accounts:login')

    vb = get_object_or_404(
        VanBan,
        pk=pk,
        phan_loai=PHAN_LOAI_VAN_BAN_DEN,
    )

    if not _lanh_dao_co_quyen_xu_ly(vb, nguoi_dung_core):
        messages.error(request, 'Bạn không có quyền xử lý văn bản này.')
        return redirect('quanlyvanbanden:danh_sach')

    if request.method == 'POST':
        _xoa_chuyen_tiep_cu(vb)

        vb.trang_thai = TRANG_THAI_XEM_DE_BIET
        vb.save()

        _lay_hoac_tao_van_ban_duyet(vb)

        ghi_lich_su_van_ban(
            user=request.user, van_ban=vb, hanh_dong="DUYET",
            trang_thai_cu=TRANG_THAI_CHO_XU_LY, trang_thai_moi=TRANG_THAI_XEM_DE_BIET,
        )

        messages.success(request, 'Đã lưu văn bản với trạng thái "Xem để biết".')
        return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)

    return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)


lanh_dao_xem_de_biet_van_ban_den = lanh_dao_luu_van_ban_den


# =========================================================
# LÃNH ĐẠO - CHUYỂN TIẾP
# =========================================================

@login_required
@role_required(Customer.Role.LANH_DAO)
def lanh_dao_chuyen_tiep_van_ban_den(request, pk):
    nguoi_dung_core = _kiem_tra_nguoi_dung_core(request)

    if not nguoi_dung_core:
        return redirect('accounts:login')

    vb = get_object_or_404(
        VanBan,
        pk=pk,
        phan_loai=PHAN_LOAI_VAN_BAN_DEN,
    )

    if not _lanh_dao_co_quyen_xu_ly(vb, nguoi_dung_core):
        messages.error(request, 'Bạn không có quyền xử lý văn bản này.')
        return redirect('quanlyvanbanden:danh_sach')

    if vb.trang_thai != TRANG_THAI_XEM_DE_BIET:
        messages.error(
            request,
            'Bạn cần bấm "Lưu" văn bản trước khi chuyển tiếp cho chuyên viên.'
        )
        return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)

    if request.method == 'POST':
        chuyen_vien_ids = request.POST.getlist('chuyen_vien_ids')

        if not chuyen_vien_ids:
            messages.error(request, 'Vui lòng chọn ít nhất 1 chuyên viên.')
            return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)

        # Hỗ trợ cả 2 trường hợp:
        # 1. Template gửi id của core.NguoiDung
        # 2. Template cũ gửi id của accounts.Customer
        ds_chuyen_vien = NguoiDung.objects.select_related('phong_ban').filter(
            Q(nguoi_dung_id__in=chuyen_vien_ids) |
            Q(tai_khoan_id__in=chuyen_vien_ids),
            chuc_vu=NguoiDung.ChucVu.CHUYEN_VIEN,
        ).distinct()

        if not ds_chuyen_vien.exists():
            messages.error(request, 'Danh sách chuyên viên không hợp lệ.')
            return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)

        _xoa_chuyen_tiep_cu(vb)

        van_ban_duyet = _lay_hoac_tao_van_ban_duyet(vb)

        chuyen_tiep = ChuyenTiep.objects.create(
            van_ban_duyet=van_ban_duyet
        )

        for chuyen_vien in ds_chuyen_vien:
            if not chuyen_vien.phong_ban:
                messages.error(
                    request,
                    f'Chuyên viên "{chuyen_vien.ho_va_ten}" chưa có phòng ban nên không thể chuyển tiếp.'
                )
                return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)

            ChuyenTiepChiTiet.objects.create(
                chuyen_tiep=chuyen_tiep,
                nguoi_dung=chuyen_vien,
                phong_ban=chuyen_vien.phong_ban,
            )

        vb.trang_thai = TRANG_THAI_DA_XU_LY
        vb.save()

        messages.success(request, 'Đã chuyển tiếp văn bản cho chuyên viên.')
        return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)

    return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)


# =========================================================
# LÃNH ĐẠO - HOÀN TRẢ
# =========================================================

@login_required
@role_required(Customer.Role.LANH_DAO)
def lanh_dao_hoan_tra_van_ban_den(request, pk):
    nguoi_dung_core = _kiem_tra_nguoi_dung_core(request)

    if not nguoi_dung_core:
        return redirect('accounts:login')

    vb = get_object_or_404(
        VanBan,
        pk=pk,
        phan_loai=PHAN_LOAI_VAN_BAN_DEN,
    )

    if not _lanh_dao_co_quyen_xu_ly(vb, nguoi_dung_core):
        messages.error(request, 'Bạn không có quyền xử lý văn bản này.')
        return redirect('quanlyvanbanden:danh_sach')

    if request.method == 'POST':
        ly_do_hoan_tra = request.POST.get('ly_do_hoan_tra', '').strip()

        if not ly_do_hoan_tra:
            messages.error(request, 'Vui lòng nhập lý do hoàn trả.')
            return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)

        _xoa_chuyen_tiep_cu(vb)

        VanBanHoanTra.objects.create(
            van_ban=vb,
            noi_dung=ly_do_hoan_tra,
        )

        vb.trang_thai = TRANG_THAI_HOAN_TRA
        vb.save()

        ghi_lich_su_van_ban(
            user=request.user, van_ban=vb, hanh_dong="HOAN_TRA",
            trang_thai_cu=TRANG_THAI_XEM_DE_BIET, trang_thai_moi=TRANG_THAI_HOAN_TRA,
        )

        messages.success(request, 'Đã hoàn trả văn bản đến.')
        return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)

    return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)


# =========================================================
# LÃNH ĐẠO - KÝ SỐ
# =========================================================

@require_POST
@login_required
def api_ky_so_van_ban(request, vb_pk):
    if not request.user.has_role(Customer.Role.LANH_DAO):
        return JsonResponse({"success": False, "message": "Bạn không có quyền ký số văn bản này."}, status=403)

    try:
        data = json.loads(request.body)
        x_ratio = float(data.get("x_ratio", 0))
        y_ratio = float(data.get("y_ratio", 0))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"success": False, "message": "Tọa độ không hợp lệ."}, status=400)

    vb = VanBan.objects.filter(pk=vb_pk, phan_loai=PHAN_LOAI_VAN_BAN_DEN).first()
    if not vb:
        return JsonResponse({"success": False, "message": "Không tìm thấy văn bản đến cần ký."}, status=404)
    user = _kiem_tra_nguoi_dung_core(request)
    if not user:
        return JsonResponse({"success": False, "message": "Tài khoản chưa liên kết hồ sơ người dùng."}, status=400)

    if vb.lanh_dao_duyet_id != user.pk or vb.trang_thai not in [TRANG_THAI_CHO_XU_LY, TRANG_THAI_HOAN_TRA]:
        return JsonResponse({"success": False, "message": "Bạn không có quyền ký văn bản này hoặc văn bản không ở trạng thái Chờ Xử Lý / Hoàn Trả."}, status=403)

    try:
        chu_ky_so = ChuKySo.objects.get(nguoi_dung=user)
        if not chu_ky_so.anh_chu_ky:
            return JsonResponse({"success": False, "message": "Tài khoản chưa cấu hình ảnh chữ ký."}, status=400)
        signature_image_path = chu_ky_so.anh_chu_ky.path
    except ChuKySo.DoesNotExist:
        return JsonResponse({"success": False, "message": "Tài khoản chưa có thông tin chữ ký số."}, status=400)

    if not vb.file_dinh_kem:
        return JsonResponse({"success": False, "message": "Văn bản chưa có file đính kèm."}, status=400)

    input_pdf_path = vb.file_dinh_kem.path
    if not vb.file_dinh_kem.name.lower().endswith(".pdf"):
        return JsonResponse({"success": False, "message": "Chỉ hỗ trợ ký số trên file PDF."}, status=400)
    if not os.path.exists(input_pdf_path):
        return JsonResponse({"success": False, "message": "Không tìm thấy file PDF gốc."}, status=404)
    if not os.path.exists(signature_image_path):
        return JsonResponse({"success": False, "message": "Không tìm thấy file ảnh chữ ký."}, status=404)

    pfx_path = os.path.join(settings.BASE_DIR, 'apps', 'core', 'certs', 'dummy_cert.pfx')
    pfx_password = "123456"
    if not os.path.exists(pfx_path):
        return JsonResponse({"success": False, "message": "Không tìm thấy chứng thư số hệ thống."}, status=500)

    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    output_filename = f"vanban_den_{vb.pk}_signed_{timestamp}.pdf"
    
    import tempfile
    temp_dir = tempfile.gettempdir()
    output_pdf_path = os.path.join(temp_dir, output_filename)

    try:
        sign_pdf_with_ratio(
            input_pdf_path=input_pdf_path,
            output_pdf_path=output_pdf_path,
            signature_image_path=signature_image_path,
            x_ratio=x_ratio,
            y_ratio=y_ratio,
            pfx_path=pfx_path,
            pfx_password=pfx_password
        )
        with open(output_pdf_path, "rb") as f:
            signed_bytes = f.read()

        import hashlib
        file_hash = hashlib.sha256(signed_bytes).hexdigest()

        vb.file_dinh_kem.save(output_filename, ContentFile(signed_bytes), save=False)
        vb.kich_thuoc = len(signed_bytes)
        # Không đổi trạng thái
        vb.save(update_fields=["file_dinh_kem", "kich_thuoc"])

        LichSuKySo.objects.update_or_create(
            van_ban=vb,
            defaults={
                'chu_ky_so': chu_ky_so,
                'hash_tai_lieu': file_hash,
                'file_hash': file_hash,
                'file_da_ky': ContentFile(signed_bytes, name=output_filename),
                'cong_viec': None,
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Lỗi khi ký số: {str(e)}"}, status=500)
    finally:
        if os.path.exists(output_pdf_path):
            os.remove(output_pdf_path)

    return JsonResponse({"success": True, "message": "Ký số thành công!"})
