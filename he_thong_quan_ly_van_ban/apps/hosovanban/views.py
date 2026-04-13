from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from apps.accounts.decorators import role_required
from apps.accounts.models import Customer
from apps.core.models import (
    HoSoVanBan,
    PhongXemHoSo,
    NguoiXuLyHoSo,
    PhongBan,
    NguoiDung,
)

from .forms import HoSoVanBanCreateForm, HoSoVanBanUpdateForm


@role_required(*Customer.Role.values)
def danh_sach(request):
    ds_ho_so = HoSoVanBan.objects.all().order_by("-ho_so_van_ban_id")
    
    tab = request.GET.get('tab', 'all')
    status_filter = request.GET.get('status', '')
    don_vi_filter = request.GET.get('don_vi', '')
    nam_filter = request.GET.get('nam', '')
    q = request.GET.get('q', '').strip()
    
    if tab == 'hien-hanh':
        ds_ho_so = ds_ho_so.filter(trang_thai=1)
    elif tab == 'luu-tru':
        ds_ho_so = ds_ho_so.filter(trang_thai=2)
        
    if status_filter == 'Hiện hành':
        ds_ho_so = ds_ho_so.filter(trang_thai=1)
    elif status_filter == 'Lưu trữ':
        ds_ho_so = ds_ho_so.filter(trang_thai=2)
        
    if don_vi_filter:
        ds_ho_so = ds_ho_so.filter(phongxemhoso__phong_ban__ten_phong_ban=don_vi_filter).distinct()
        
    if nam_filter:
        ds_ho_so = ds_ho_so.filter(ngay_tao_ho_so__year=nam_filter)
        
    if q:
        from django.db.models import Q
        ds_ho_so = ds_ho_so.filter(Q(tieu_de_ho_so__icontains=q) | Q(ky_hieu_ho_so__icontains=q))

    nam_choices = HoSoVanBan.objects.dates('ngay_tao_ho_so', 'year', order='DESC')
    nam_choices = [d.year for d in nam_choices]
    
    active_filters = []
    if status_filter: active_filters.append(status_filter)
    if don_vi_filter: active_filters.append(don_vi_filter)
    if nam_filter: active_filters.append(f"Năm {nam_filter}")
    if q: active_filters.append(f"Từ khóa: {q}")
    active_filters_text = " | ".join(active_filters)
    
    paginator = Paginator(ds_ho_so, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    ds_phong_ban = PhongBan.objects.all().order_by("ten_phong_ban")
    
    return render(
        request,
        "hosovanban/ho-so-van-ban.html",
        {
            "ds_ho_so": page_obj,
            "ds_phong_ban": ds_phong_ban,
            "nam_choices": nam_choices,
            "active_filters_text": active_filters_text,
            "current_tab": tab,
            "current_status": status_filter,
            "current_don_vi": don_vi_filter,
            "current_nam": nam_filter,
            "current_q": q,
            "page_obj": page_obj,
        },
    )


@role_required(Customer.Role.VAN_THU)
def them_ho_so_van_ban(request):
    ds_phong_ban = PhongBan.objects.all().order_by("ten_phong_ban")
    ds_nguoi_dung = (
        NguoiDung.objects.select_related("phong_ban")
        .all()
        .order_by("phong_ban__ten_phong_ban", "ho_va_ten")
    )

    if request.method == "POST":
        form = HoSoVanBanCreateForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    ho_so = form.save(commit=False)

                    if hasattr(request.user, "nguoi_dung_core"):
                        ho_so.nguoi_tao = request.user.nguoi_dung_core
                    elif hasattr(request.user, "core_profile"):
                        ho_so.nguoi_tao = request.user.core_profile
                    else:
                        messages.error(request, "Tài khoản của bạn chưa được liên kết với thông tin người dùng.")
                        return render(
                            request,
                            "hosovanban/them-ho-so-van-ban.html",
                            {
                                "form": form,
                                "today": timezone.now().date(),
                                "ds_phong_ban": ds_phong_ban,
                                "ds_nguoi_dung": ds_nguoi_dung,
                            },
                        )

                    ho_so.trang_thai = 1
                    ho_so.save()

                    # nhiều phòng ban chỉ được xem
                    for pb in form.cleaned_data["phong_ban"]:
                        PhongXemHoSo.objects.create(
                            ho_so_van_ban=ho_so,
                            phong_ban=pb,
                        )

                    # nhiều người xử lý có quyền chỉnh sửa
                    for nd in form.cleaned_data["nguoi_xu_ly"]:
                        NguoiXuLyHoSo.objects.create(
                            ho_so_van_ban=ho_so,
                            nguoi_xu_ly=nd,
                        )

                messages.success(request, "Thêm hồ sơ văn bản thành công!")
                return redirect("hosovanban:danh_sach")

            except Exception as e:
                messages.error(request, f"Có lỗi xảy ra khi thêm hồ sơ văn bản: {e}")
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin nhập.")
    else:
        form = HoSoVanBanCreateForm()

    return render(
        request,
        "hosovanban/them-ho-so-van-ban.html",
        {
            "form": form,
            "today": timezone.now().date(),
            "ds_phong_ban": ds_phong_ban,
            "ds_nguoi_dung": ds_nguoi_dung,
        },
    )

@role_required(*Customer.Role.values)
def chi_tiet_ho_so_van_ban(request, pk):
    ho_so = get_object_or_404(HoSoVanBan, pk=pk)
    ds_van_ban = ho_so.vanban_set.all().order_by("-ngay_van_ban")
    ds_phong_ban = ho_so.phongxemhoso_set.select_related("phong_ban")
    ds_nguoi_xu_ly = ho_so.nguoixulyhoso_set.select_related("nguoi_xu_ly")
    
    return render(
        request,
        "hosovanban/chi-tiet-ho-so-van-ban.html",
        {
            "ho_so": ho_so,
            "ds_van_ban": ds_van_ban,
            "ds_phong_ban": ds_phong_ban,
            "ds_nguoi_xu_ly": ds_nguoi_xu_ly,
        },
    )

@role_required(Customer.Role.VAN_THU)
def sua_ho_so_van_ban(request, pk):
    ho_so = get_object_or_404(HoSoVanBan, pk=pk)
    if ho_so.trang_thai == 2:
        messages.error(request, "Hồ sơ đã được lưu trữ, không thể chỉnh sửa.")
        return redirect("hosovanban:chi_tiet", pk=pk)
        
    ds_phong_ban = PhongBan.objects.all().order_by("ten_phong_ban")
    ds_nguoi_dung = (
        NguoiDung.objects.select_related("phong_ban")
        .all()
        .order_by("phong_ban__ten_phong_ban", "ho_va_ten")
    )
    
    if request.method == "POST":
        form = HoSoVanBanUpdateForm(request.POST, instance=ho_so)
        if form.is_valid():
            try:
                with transaction.atomic():
                    ho_so = form.save(commit=False)
                    ho_so.ngay_cap_nhat = timezone.now().date()
                    ho_so.save()

                    PhongXemHoSo.objects.filter(ho_so_van_ban=ho_so).delete()
                    for pb in form.cleaned_data["phong_ban"]:
                        PhongXemHoSo.objects.create(ho_so_van_ban=ho_so, phong_ban=pb)

                    NguoiXuLyHoSo.objects.filter(ho_so_van_ban=ho_so).delete()
                    for nd in form.cleaned_data["nguoi_xu_ly"]:
                        NguoiXuLyHoSo.objects.create(ho_so_van_ban=ho_so, nguoi_xu_ly=nd)

                messages.success(request, "Cập nhật hồ sơ thành công")
                return redirect("hosovanban:chi_tiet", pk=pk)
            except Exception as e:
                messages.error(request, f"Có lỗi xảy ra: {e}")
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin nhập.")
    else:
        init_phong_ban = ho_so.phongxemhoso_set.values_list('phong_ban_id', flat=True)
        init_nguoi_xu_ly = ho_so.nguoixulyhoso_set.values_list('nguoi_xu_ly_id', flat=True)
        
        form = HoSoVanBanUpdateForm(instance=ho_so, initial={
            'phong_ban': init_phong_ban,
            'nguoi_xu_ly': init_nguoi_xu_ly,
        })
        
        return render(
        request,
        "hosovanban/sua-ho-so-van-ban.html",
        {
            "form": form,
            "ho_so": ho_so,
            "today": ho_so.ngay_tao_ho_so,
            "current_date": timezone.now().date(),
            "ds_phong_ban": ds_phong_ban,
            "ds_nguoi_dung": ds_nguoi_dung,
        },
    )

@role_required(Customer.Role.VAN_THU)
def xoa_ho_so_van_ban(request, pk):
    if request.method == "POST":
        ho_so = get_object_or_404(HoSoVanBan, pk=pk)
        
        if ho_so.trang_thai == 1 and ho_so.vanban_set.exists():
            messages.error(request, "Hồ sơ đang chứa văn bản đang hiện hành , không được phép xóa.")
        else:
            ho_so.delete()
            messages.success(request, "Xóa hồ sơ văn bản thành công!")
            
    return redirect("hosovanban:danh_sach")