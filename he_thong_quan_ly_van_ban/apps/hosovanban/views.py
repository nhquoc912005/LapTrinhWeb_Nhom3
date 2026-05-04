from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required

from apps.accounts.decorators import role_required
from apps.accounts.models import Customer
from apps.core.models import (
    HoSoVanBan,
    PhongXemHoSo,
    NguoiXuLyHoSo,
    PhongBan,
    NguoiDung,
    VanBan,
    VanBanLienQuan,
)

from .forms import HoSoVanBanCreateForm, HoSoVanBanUpdateForm
from apps.core.utils.activity_log import ghi_lich_su_ho_so


@role_required(*Customer.Role.values)
def danh_sach(request):
    if hasattr(request.user, "nguoi_dung_core") and request.user.nguoi_dung_core:
        nd = request.user.nguoi_dung_core
    elif hasattr(request.user, "core_profile") and request.user.core_profile:
        nd = request.user.core_profile
    else:
        nd = None

    if nd:
        from django.db.models import Q
        if request.user.is_van_thu or request.user.is_lanh_dao:
            # Văn thư và Lãnh đạo: Xem tất cả hồ sơ
            ds_ho_so = HoSoVanBan.objects.all().order_by("-ho_so_van_ban_id")
        else:
            # Chuyên viên: Xem nếu được gán xử lý HOẶC thuộc phòng ban được xem
            ds_ho_so = HoSoVanBan.objects.filter(
                Q(nguoixulyhoso__nguoi_xu_ly=nd) |
                Q(phongxemhoso__phong_ban=nd.phong_ban)
            ).distinct().order_by("-ho_so_van_ban_id")
    else:
        ds_ho_so = HoSoVanBan.objects.none()
    
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

                ghi_lich_su_ho_so(user=request.user, ho_so=ho_so, hanh_dong="TAO")

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
    
    if hasattr(request.user, "nguoi_dung_core") and request.user.nguoi_dung_core:
        nd = request.user.nguoi_dung_core
    elif hasattr(request.user, "core_profile") and request.user.core_profile:
        nd = request.user.core_profile
    else:
        nd = None

    can_view = False
    if nd:
        if request.user.is_van_thu or request.user.is_lanh_dao:
            # Văn thư và Lãnh đạo được xem tất cả
            can_view = True
        elif ho_so.nguoixulyhoso_set.filter(nguoi_xu_ly=nd).exists():
            # Người xử lý được xem
            can_view = True
        elif ho_so.phongxemhoso_set.filter(phong_ban=nd.phong_ban).exists():
            # Người thuộc phòng ban được gán xem cũng được xem
            can_view = True

    if not can_view:
        messages.error(request, "Bạn không có quyền xem hồ sơ này.")
        return redirect("hosovanban:danh_sach")

    ds_van_ban = ho_so.vanban_set.all().order_by("-ngay_van_ban")
    ds_phong_ban = ho_so.phongxemhoso_set.select_related("phong_ban")
    ds_nguoi_xu_ly = ho_so.nguoixulyhoso_set.select_related("nguoi_xu_ly")
    
    # Quyền thêm văn bản vào hồ sơ
    has_permission = False 
    if request.user.is_van_thu:
        has_permission = True
    elif nd and ho_so.nguoixulyhoso_set.filter(nguoi_xu_ly=nd).exists():
        has_permission = True

    # Quyền gỡ văn bản khỏi hồ sơ dùng cùng logic quyền xử lý hồ sơ.
    can_remove_doc = check_ho_so_permission(request, ho_so)

    can_edit = False
    if request.user.is_van_thu and ho_so.nguoi_tao == nd and ho_so.trang_thai == 1:
        can_edit = True

    can_delete = False
    if request.user.is_van_thu and ho_so.nguoi_tao == nd:
        if ds_van_ban.count() == 0 or ho_so.trang_thai == 2:
            can_delete = True

    return render(
        request,
        "hosovanban/chi-tiet-ho-so-van-ban.html",
        {
            "ho_so": ho_so,
            "ds_van_ban": ds_van_ban,
            "ds_phong_ban": ds_phong_ban,
            "ds_nguoi_xu_ly": ds_nguoi_xu_ly,
            "can_edit": can_edit,
            "can_delete": can_delete,
            "has_permission": has_permission,
            "can_remove_doc": can_remove_doc,
        },
    )

def check_ho_so_permission(request, ho_so):
    """Kiểm tra quyền xử lý hồ sơ."""
    if request.user.is_van_thu:
        return True
        
    if hasattr(request.user, "nguoi_dung_core") and request.user.nguoi_dung_core:
        nd = request.user.nguoi_dung_core
    elif hasattr(request.user, "core_profile") and request.user.core_profile:
        nd = request.user.core_profile
    else:
        return False
        
    return ho_so.nguoixulyhoso_set.filter(nguoi_xu_ly=nd).exists()

@role_required(*Customer.Role.values)
def sua_ho_so_van_ban(request, pk):
    ho_so = get_object_or_404(HoSoVanBan, pk=pk)
    
    if hasattr(request.user, "nguoi_dung_core") and request.user.nguoi_dung_core:
        nd = request.user.nguoi_dung_core
    elif hasattr(request.user, "core_profile") and request.user.core_profile:
        nd = request.user.core_profile
    else:
        nd = None

    # Chỉ người tạo (Văn thư) được sửa hồ sơ
    if not (request.user.is_van_thu and ho_so.nguoi_tao == nd):
        messages.error(request, "Bạn không có quyền chỉnh sửa hồ sơ này.")
        return redirect("hosovanban:chi_tiet", pk=pk)
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

                ghi_lich_su_ho_so(user=request.user, ho_so=ho_so, hanh_dong="SUA")

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

@role_required(*Customer.Role.values)
def xoa_ho_so_van_ban(request, pk):
    if request.method == "POST":
        ho_so = get_object_or_404(HoSoVanBan, pk=pk)
        
        if hasattr(request.user, "nguoi_dung_core") and request.user.nguoi_dung_core:
            nd = request.user.nguoi_dung_core
        elif hasattr(request.user, "core_profile") and request.user.core_profile:
            nd = request.user.core_profile
        else:
            nd = None

        # Chỉ cho xóa khi không còn văn bản nào trong hồ sơ
        if not (request.user.is_van_thu and ho_so.nguoi_tao == nd):
            messages.error(request, "Bạn không có quyền xóa hồ sơ này.")
        elif ho_so.vanban_set.exists():
            messages.error(request, "Không thể xóa hồ sơ đang chứa văn bản.")
        else:
            ghi_lich_su_ho_so(user=request.user, ho_so=ho_so, hanh_dong="XOA")
            ho_so.delete()
            messages.success(request, "Xóa hồ sơ văn bản thành công!")
            
    return redirect("hosovanban:danh_sach")


@role_required(*Customer.Role.values)
def chi_tiet_van_ban_trong_ho_so(request, ho_so_id, vb_id):
    ho_so = get_object_or_404(HoSoVanBan, pk=ho_so_id)
    van_ban = get_object_or_404(VanBan, pk=vb_id, ho_so_van_ban=ho_so)
    ds_van_ban_lien_quan = van_ban.vanbanlienquan_set.all()
    
    has_permission = check_ho_so_permission(request, ho_so)
    can_delete_doc = has_permission and ho_so.trang_thai == 1

    context = {
        "ho_so": ho_so,
        "van_ban": van_ban,
        "ds_van_ban_lien_quan": ds_van_ban_lien_quan,
        "has_permission": has_permission,
        "can_delete_doc": can_delete_doc,
    }
    return render(request, "hosovanban/chi-tiet-van-ban.html", context)


@role_required(*Customer.Role.values)
def xoa_van_ban_khoi_ho_so(request, ho_so_id, vb_id):
    if request.method == "POST":
        ho_so = get_object_or_404(HoSoVanBan, pk=ho_so_id)
        van_ban = get_object_or_404(VanBan, pk=vb_id, ho_so_van_ban=ho_so)

        if not check_ho_so_permission(request, ho_so):
            messages.error(request, "Bạn không có quyền gỡ văn bản khỏi hồ sơ này.")
            return redirect("hosovanban:chi_tiet", pk=ho_so_id)

        if ho_so.trang_thai != 1:
            messages.error(request, "Không thể gỡ văn bản khỏi hồ sơ đã lưu trữ.")
            return redirect("hosovanban:chi_tiet", pk=ho_so_id)

        van_ban.ho_so_van_ban = None
        van_ban.save()
        
        messages.success(request, f"Đã gỡ văn bản [{van_ban.so_ky_hieu}] khỏi hồ sơ.")
    return redirect("hosovanban:chi_tiet", pk=ho_so_id)


# ===== API: Danh sách hồ sơ hiện hành (cho popup dropdown) =====
@login_required
@require_GET
@role_required(Customer.Role.VAN_THU, Customer.Role.CHUYEN_VIEN, Customer.Role.LANH_DAO)
def api_ds_ho_so_hien_hanh(request):
    if hasattr(request.user, "nguoi_dung_core") and request.user.nguoi_dung_core:
        nd = request.user.nguoi_dung_core
    elif hasattr(request.user, "core_profile") and request.user.core_profile:
        nd = request.user.core_profile
    else:
        nd = None

    ds = HoSoVanBan.objects.filter(trang_thai=1)
    if nd:
        from django.db.models import Q
        if request.user.is_van_thu or request.user.is_lanh_dao:
            # Văn thư và Lãnh đạo thấy tất cả hồ sơ hiện hành để xem
            # Tuy nhiên has_permission trong API add doc sẽ kiểm tra kỹ hơn
            ds = ds.order_by("-ho_so_van_ban_id")
        else:
            # Chuyên viên chỉ thấy hồ sơ được gán xử lý
            ds = ds.filter(Q(nguoixulyhoso__nguoi_xu_ly=nd)).distinct().order_by("-ho_so_van_ban_id")
    else:
        ds = ds.none()

    q = request.GET.get("q", "").strip()
    if q:
        from django.db.models import Q
        ds = ds.filter(
            Q(tieu_de_ho_so__icontains=q) | Q(ky_hieu_ho_so__icontains=q)
        )
    data = [
        {
            "id": hs.pk,
            "tieu_de": hs.tieu_de_ho_so,
            "ky_hieu": hs.ky_hieu_ho_so,
        }
        for hs in ds[:50]
    ]
    return JsonResponse({"ho_so": data})


# ===== API: Thêm văn bản vào hồ sơ =====
@login_required
@require_POST
@role_required(Customer.Role.VAN_THU, Customer.Role.CHUYEN_VIEN, Customer.Role.LANH_DAO)
def api_them_van_ban_vao_ho_so(request):
    """Liên kết một VanBan (core) vào một HoSoVanBan."""
    ho_so_id = request.POST.get("ho_so_id")
    van_ban_id = request.POST.get("van_ban_id")

    if not ho_so_id or not van_ban_id:
        return JsonResponse(
            {"ok": False, "error": "Thiếu thông tin hồ sơ hoặc văn bản."},
            status=400,
        )

    ho_so = HoSoVanBan.objects.filter(pk=ho_so_id, trang_thai=1).first()
    if not ho_so:
        return JsonResponse(
            {"ok": False, "error": "Hồ sơ không tồn tại hoặc không ở trạng thái Hiện hành."},
            status=400,
        )

    if not check_ho_so_permission(request, ho_so):
        return JsonResponse(
            {"ok": False, "error": "Bạn không có quyền thêm văn bản vào hồ sơ này."},
            status=403,
        )

    van_ban = VanBan.objects.filter(pk=van_ban_id).first()
    if not van_ban:
        return JsonResponse(
            {"ok": False, "error": "Văn bản không tồn tại."},
            status=404,
        )

    if van_ban.ho_so_van_ban_id:
        return JsonResponse(
            {"ok": False, "error": f"Văn bản đã thuộc hồ sơ \"{van_ban.ho_so_van_ban.tieu_de_ho_so}\". Vui lòng gỡ khỏi hồ sơ cũ trước."},
            status=400,
        )

    van_ban.ho_so_van_ban = ho_so
    van_ban.save(update_fields=["ho_so_van_ban_id"])

    ghi_lich_su_ho_so(
        user=request.user, ho_so=ho_so, hanh_dong="SUA",
        mo_ta=f"Thêm văn bản [{van_ban.so_ky_hieu}] vào hồ sơ",
    )

    return JsonResponse({
        "ok": True,
        "message": f"Đã thêm văn bản \"{van_ban.so_ky_hieu}\" vào hồ sơ \"{ho_so.tieu_de_ho_so}\" thành công.",
    })
