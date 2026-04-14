from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.decorators import role_required
from apps.accounts.models import Customer

from .forms import VanBanDenForm
from .models import VanBanDen, TepVanBanDen, VanBanDenChuyenTiep


# ===== DÙNG CHUNG =====
def _xoa_file_vat_ly(tep_obj):
    if tep_obj and tep_obj.tep:
        tep_obj.tep.delete(save=False)


def _lanh_dao_co_quyen_xu_ly(vb, user):
    return user.is_lanh_dao and vb.lanh_dao_xu_ly_id == user.id


def _chuyen_vien_duoc_phan_cong(vb, user):
    return user.is_chuyen_vien and vb.ds_chuyen_tiep.filter(chuyen_vien=user).exists()


@login_required
@role_required(Customer.Role.VAN_THU, Customer.Role.LANH_DAO, Customer.Role.CHUYEN_VIEN)
def danh_sach_van_ban_den(request):
    # ===== DÙNG CHUNG =====
    ds = VanBanDen.objects.select_related(
        'nguoi_tao',
        'lanh_dao_xu_ly'
    ).all().order_by('-created_at')

    q = request.GET.get('q', '').strip()
    loai_van_ban = request.GET.get('loai_van_ban', '').strip()
    hinh_thuc_van_ban = request.GET.get('hinh_thuc_van_ban', '').strip()
    do_mat = request.GET.get('do_mat', '').strip()
    do_khan = request.GET.get('do_khan', '').strip()
    trang_thai = request.GET.get('trang_thai', '').strip()

    # ===== LÃNH ĐẠO =====
    if request.user.is_lanh_dao:
        ds = ds.filter(lanh_dao_xu_ly=request.user)

    # ===== CHUYÊN VIÊN =====
    elif request.user.is_chuyen_vien:
        ds = ds.filter(ds_chuyen_tiep__chuyen_vien=request.user).distinct()

    # ===== BỘ LỌC DÙNG CHUNG =====
    if q:
        ds = ds.filter(
            Q(so_ky_hieu__icontains=q) |
            Q(trich_yeu__icontains=q) |
            Q(don_vi_ban_hanh__icontains=q)
        )

    if loai_van_ban:
        ds = ds.filter(loai_van_ban=loai_van_ban)

    if hinh_thuc_van_ban:
        ds = ds.filter(hinh_thuc_van_ban=hinh_thuc_van_ban)

    if do_mat:
        ds = ds.filter(do_mat=do_mat)

    if do_khan:
        ds = ds.filter(do_khan=do_khan)

    if trang_thai:
        ds = ds.filter(trang_thai=trang_thai)

    paginator = Paginator(ds, 10)
    page_number = request.GET.get('page')
    ds = paginator.get_page(page_number)

    context = {
        'ds': ds,
        'page_obj': ds,
        'q': q,
        'selected_loai_van_ban': loai_van_ban,
        'selected_hinh_thuc_van_ban': hinh_thuc_van_ban,
        'selected_do_mat': do_mat,
        'selected_do_khan': do_khan,
        'selected_trang_thai': trang_thai,
        'loai_van_ban_choices': VanBanDen.LoaiVanBan.choices,
        'hinh_thuc_van_ban_choices': VanBanDen.HinhThucVanBan.choices,
        'do_mat_choices': VanBanDen.DoMat.choices,
        'do_khan_choices': VanBanDen.DoKhan.choices,
        'trang_thai_choices': VanBanDen.TrangThai.choices,
    }

    if request.user.is_lanh_dao:
        return render(request, 'van_ban_den/lanhdao/danh_sach.html', context)
    elif request.user.is_chuyen_vien:
        return render(request, 'van_ban_den/chuyenvien/danh_sach.html', context)

    return render(request, 'van_ban_den/vanthu/danh_sach.html', context)


@login_required
@role_required(Customer.Role.VAN_THU, Customer.Role.LANH_DAO, Customer.Role.CHUYEN_VIEN)
def chi_tiet_van_ban_den(request, pk):
    vb = get_object_or_404(
        VanBanDen.objects.select_related('nguoi_tao', 'lanh_dao_xu_ly'),
        pk=pk
    )

    # ===== LÃNH ĐẠO =====
    if request.user.is_lanh_dao and not _lanh_dao_co_quyen_xu_ly(vb, request.user):
        messages.error(request, 'Bạn không có quyền xem văn bản này.')
        return redirect('quanlyvanbanden:danh_sach')

    # ===== CHUYÊN VIÊN =====
    if request.user.is_chuyen_vien and not _chuyen_vien_duoc_phan_cong(vb, request.user):
        messages.error(request, 'Bạn không có quyền xem văn bản này.')
        return redirect('quanlyvanbanden:danh_sach')

    file_dinh_kem_list = vb.tep_tin.filter(
        loai=TepVanBanDen.LoaiTep.DINH_KEM
    ).order_by('created_at')

    tai_lieu_lien_quan_list = vb.tep_tin.filter(
        loai=TepVanBanDen.LoaiTep.LIEN_QUAN
    ).order_by('created_at')

    context = {
        'vb': vb,
        'file_dinh_kem_list': file_dinh_kem_list,
        'tai_lieu_lien_quan_list': tai_lieu_lien_quan_list,
    }

    if request.user.is_lanh_dao:
        User = get_user_model()

        chuyen_viens = User.objects.filter(role='CHUYEN_VIEN').order_by('id')

        ds_chuyen_tiep = vb.ds_chuyen_tiep.select_related(
            'chuyen_vien',
            'nguoi_chuyen'
        ).order_by('created_at')

        context.update({
            'chuyen_viens': chuyen_viens,
            'ds_chuyen_tiep': ds_chuyen_tiep,
        })
        template_name = 'van_ban_den/lanhdao/chi_tiet.html'

    elif request.user.is_chuyen_vien:
        ds_chuyen_tiep = vb.ds_chuyen_tiep.select_related(
            'chuyen_vien',
            'nguoi_chuyen'
        ).order_by('created_at')

        context.update({
            'ds_chuyen_tiep': ds_chuyen_tiep,
        })
        template_name = 'van_ban_den/chuyenvien/chi_tiet.html'

    else:
        template_name = 'van_ban_den/vanthu/chi_tiet.html'

    return render(request, template_name, context)


# ===== VĂN THƯ =====
@login_required
@role_required(Customer.Role.VAN_THU)
def them_van_ban_den(request):
    User = get_user_model()
    lanh_daos = User.objects.filter(role='LANH_DAO')

    if request.method == 'POST':
        form = VanBanDenForm(request.POST, request.FILES)
        if form.is_valid():
            vb = form.save(commit=False)

            vb.nguoi_tao = request.user
            vb.trang_thai = VanBanDen.TrangThai.CHO_XU_LY
            vb.ly_do_hoan_tra = ''
            vb.ngay_hoan_tra = None
            vb.save()

            for f in request.FILES.getlist('file_dinh_kem_files'):
                TepVanBanDen.objects.create(
                    van_ban_den=vb,
                    loai=TepVanBanDen.LoaiTep.DINH_KEM,
                    tep=f
                )

            for f in request.FILES.getlist('tai_lieu_lien_quan_files'):
                TepVanBanDen.objects.create(
                    van_ban_den=vb,
                    loai=TepVanBanDen.LoaiTep.LIEN_QUAN,
                    tep=f
                )

            messages.success(request, 'Trình văn bản đến thành công.')
            return redirect('quanlyvanbanden:danh_sach')
    else:
        form = VanBanDenForm()

    return render(request, 'van_ban_den/vanthu/them.html', {
        'form': form,
        'lanh_daos': lanh_daos,
    })


# ===== VĂN THƯ =====
@login_required
@role_required(Customer.Role.VAN_THU)
def sua_van_ban_den(request, pk):
    User = get_user_model()
    vb = get_object_or_404(VanBanDen, pk=pk)
    lanh_daos = User.objects.filter(role='LANH_DAO')

    # ===== ghi nhớ trạng thái cũ =====
    old_trang_thai = vb.trang_thai

    if request.method == 'POST':
        form = VanBanDenForm(request.POST, request.FILES, instance=vb)

        if form.is_valid():
            vb = form.save(commit=False)

            # ===== nếu văn bản đang HOÀN TRẢ mà văn thư cập nhật lại
            # thì đưa về CHỜ XỬ LÝ =====
            if old_trang_thai == VanBanDen.TrangThai.HOAN_TRA:
                vb.trang_thai = VanBanDen.TrangThai.CHO_XU_LY
                vb.ly_do_hoan_tra = ''
                vb.ngay_hoan_tra = None

            vb.save()

            delete_dinh_kem_ids = request.POST.getlist('delete_file_dinh_kem_ids')
            if delete_dinh_kem_ids:
                tep_xoa = TepVanBanDen.objects.filter(
                    id__in=delete_dinh_kem_ids,
                    van_ban_den=vb,
                    loai=TepVanBanDen.LoaiTep.DINH_KEM
                )
                for tep in tep_xoa:
                    _xoa_file_vat_ly(tep)
                    tep.delete()

            delete_lien_quan_ids = request.POST.getlist('delete_tai_lieu_lien_quan_ids')
            if delete_lien_quan_ids:
                tep_xoa = TepVanBanDen.objects.filter(
                    id__in=delete_lien_quan_ids,
                    van_ban_den=vb,
                    loai=TepVanBanDen.LoaiTep.LIEN_QUAN
                )
                for tep in tep_xoa:
                    _xoa_file_vat_ly(tep)
                    tep.delete()

            for f in request.FILES.getlist('file_dinh_kem_files'):
                TepVanBanDen.objects.create(
                    van_ban_den=vb,
                    loai=TepVanBanDen.LoaiTep.DINH_KEM,
                    tep=f
                )

            for f in request.FILES.getlist('tai_lieu_lien_quan_files'):
                TepVanBanDen.objects.create(
                    van_ban_den=vb,
                    loai=TepVanBanDen.LoaiTep.LIEN_QUAN,
                    tep=f
                )

            messages.success(request, 'Chỉnh sửa văn bản đến thành công.')
            return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)
    else:
        form = VanBanDenForm(instance=vb)

    file_dinh_kem_list = vb.tep_tin.filter(
        loai=TepVanBanDen.LoaiTep.DINH_KEM
    ).order_by('created_at')

    tai_lieu_lien_quan_list = vb.tep_tin.filter(
        loai=TepVanBanDen.LoaiTep.LIEN_QUAN
    ).order_by('created_at')

    return render(request, 'van_ban_den/vanthu/sua.html', {
        'form': form,
        'vb': vb,
        'lanh_daos': lanh_daos,
        'file_dinh_kem_list': file_dinh_kem_list,
        'tai_lieu_lien_quan_list': tai_lieu_lien_quan_list,
    })


# ===== VĂN THƯ =====
@login_required
@role_required(Customer.Role.VAN_THU)
def xoa_van_ban_den(request, pk):
    vb = get_object_or_404(VanBanDen, pk=pk)

    if request.method == 'POST':
        for tep in vb.tep_tin.all():
            _xoa_file_vat_ly(tep)
        vb.delete()
        messages.success(request, 'Xóa văn bản đến thành công.')
        return redirect('quanlyvanbanden:danh_sach')

    return render(request, 'van_ban_den/vanthu/xoa.html', {
        'vb': vb,
    })


# ===== LÃNH ĐẠO =====
@login_required
@role_required(Customer.Role.LANH_DAO)
def lanh_dao_luu_van_ban_den(request, pk):
    vb = get_object_or_404(VanBanDen, pk=pk)

    if not _lanh_dao_co_quyen_xu_ly(vb, request.user):
        messages.error(request, 'Bạn không có quyền xử lý văn bản này.')
        return redirect('quanlyvanbanden:danh_sach')

    if request.method == 'POST':
        vb.ds_chuyen_tiep.all().delete()
        vb.trang_thai = VanBanDen.TrangThai.XEM_DE_BIET
        vb.ly_do_hoan_tra = ''
        vb.ngay_hoan_tra = None
        vb.save()

        messages.success(request, 'Đã lưu văn bản với trạng thái "Xem để biết".')
        return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)

    return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)


lanh_dao_xem_de_biet_van_ban_den = lanh_dao_luu_van_ban_den


# ===== LÃNH ĐẠO =====
@login_required
@role_required(Customer.Role.LANH_DAO)
def lanh_dao_chuyen_tiep_van_ban_den(request, pk):
    vb = get_object_or_404(VanBanDen, pk=pk)

    if not _lanh_dao_co_quyen_xu_ly(vb, request.user):
        messages.error(request, 'Bạn không có quyền xử lý văn bản này.')
        return redirect('quanlyvanbanden:danh_sach')

    if request.method == 'POST':
        chuyen_vien_ids = request.POST.getlist('chuyen_vien_ids')

        if not chuyen_vien_ids:
            messages.error(request, 'Vui lòng chọn ít nhất 1 chuyên viên.')
            return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)

        User = get_user_model()
        ds_chuyen_vien = User.objects.filter(
            id__in=chuyen_vien_ids,
            role='CHUYEN_VIEN'
        )

        if not ds_chuyen_vien.exists():
            messages.error(request, 'Danh sách chuyên viên không hợp lệ.')
            return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)

        vb.ds_chuyen_tiep.all().delete()

        for chuyen_vien in ds_chuyen_vien:
            VanBanDenChuyenTiep.objects.create(
                van_ban_den=vb,
                chuyen_vien=chuyen_vien,
                nguoi_chuyen=request.user
            )

        vb.trang_thai = VanBanDen.TrangThai.DA_XU_LY
        vb.ly_do_hoan_tra = ''
        vb.ngay_hoan_tra = None
        vb.save()

        messages.success(request, 'Đã chuyển tiếp văn bản cho chuyên viên.')
        return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)

    return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)


# ===== LÃNH ĐẠO =====
@login_required
@role_required(Customer.Role.LANH_DAO)
def lanh_dao_hoan_tra_van_ban_den(request, pk):
    vb = get_object_or_404(VanBanDen, pk=pk)

    if not _lanh_dao_co_quyen_xu_ly(vb, request.user):
        messages.error(request, 'Bạn không có quyền xử lý văn bản này.')
        return redirect('quanlyvanbanden:danh_sach')

    if request.method == 'POST':
        ly_do_hoan_tra = request.POST.get('ly_do_hoan_tra', '').strip()

        if not ly_do_hoan_tra:
            messages.error(request, 'Vui lòng nhập lý do hoàn trả.')
            return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)

        vb.ds_chuyen_tiep.all().delete()

        vb.ly_do_hoan_tra = ly_do_hoan_tra
        vb.trang_thai = VanBanDen.TrangThai.HOAN_TRA
        vb.ngay_hoan_tra = timezone.localdate()
        vb.save()

        messages.success(request, 'Đã hoàn trả văn bản đến.')
        return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)

    return redirect('quanlyvanbanden:chi_tiet', pk=vb.pk)
