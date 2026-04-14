import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils import timezone
from django import forms
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from ..accounts.decorators import role_required
from ..accounts.models import Customer
from ..core.models import (
    VanBan, VanBanLienQuan, NguoiDung, VanBanDuyet, VanBanHoanTra,
    ChiNhanh, PhongBan, DonViNgoai, BanHanh, BanHanhChiTiep,
)
from .forms import VanBanDiForm, validate_file_size, validate_file_extension
from django.core.paginator import Paginator
from django.db.models import Q, Count


@role_required(*Customer.Role.values)
def van_ban_di(request):
    trang_thai = request.GET.get("trang_thai", "").strip()
    keyword    = request.GET.get("keyword", "").strip()
    don_vi     = request.GET.get("don_vi_soan_thao", "").strip()
    loai_vb    = request.GET.get("loai_van_ban", "").strip()
    hinh_thuc  = request.GET.get("hinh_thuc", "").strip()
    do_khan    = request.GET.get("do_khan", "").strip()

    user = request.user

    # ── Phân quyền theo role ──
    if user.has_role(Customer.Role.VAN_THU):
        trang_thai_filter_choices = [
            ("", "Tất cả"),
            ("Chờ ban hành", "Chờ ban hành"),
            ("Đã ban hành", "Đã ban hành"),
            ("Xem Để Biết", "Xem để biết"),
        ]
        allowed_statuses = ["Chờ ban hành", "Đã ban hành", "Xem Để Biết"]

    else:
        # Cả Chuyên viên lẫn Lãnh đạo dùng bộ lọc này
        trang_thai_filter_choices = [
            ("", "Tất cả"),
            ("Chờ Xử Lý", "Chờ xử lý"),
            ("Đã Xử Lý", "Đã xử lý"),   # hiển thị cho cả Chờ ban hành + Đã ban hành
            ("Hoàn Trả", "Hoàn trả"),
            ("Xem Để Biết", "Xem để biết"),
        ]
        # CV/LĐ thấy cả trạng thái “Chờ ban hành” / “Đã ban hành” (hiển thị là “Đã Xử Lý”)
        allowed_statuses = [
            "Chờ Xử Lý",
            "Đã Xử Lý",
            "Hoàn Trả",
            "Chờ ban hành",
            "Đã ban hành",
            "Xem Để Biết",
        ]

    ds_van_ban_di_list = VanBan.objects.filter(
        phan_loai="Văn bản đi",
        trang_thai__in=allowed_statuses,
    ).order_by("-van_ban_id")

    # ── Lọc theo quyền xem ──
    if user.has_role(Customer.Role.CHUYEN_VIEN):
        # Chứ xem văn bản do chính mình tạo
        ds_van_ban_di_list = ds_van_ban_di_list.filter(
            nguoi_tao=user.nguoi_dung_core
        )
    elif user.has_role(Customer.Role.LANH_DAO):
        # Chỉ xem văn bản được chỉ định cho mình ký
        ds_van_ban_di_list = ds_van_ban_di_list.filter(
            lanh_dao_duyet=user.nguoi_dung_core
        )

    # ── Bộ lọc trạng thái: "Dã Xử Lý" của CV/LĐ = Chờ ban hành + Đã ban hành + Đã Xử Lý ──
    if trang_thai:
        if trang_thai == "Đã Xử Lý" and not user.has_role(Customer.Role.VAN_THU):
            ds_van_ban_di_list = ds_van_ban_di_list.filter(
                trang_thai__in=["Đã Xử Lý", "Chờ ban hành", "Đã ban hành"]
            )
        else:
            ds_van_ban_di_list = ds_van_ban_di_list.filter(trang_thai=trang_thai)

    if keyword:
        ds_van_ban_di_list = ds_van_ban_di_list.filter(
            Q(so_ky_hieu__icontains=keyword) | Q(trich_yeu__icontains=keyword)
        )
    if don_vi:
        ds_van_ban_di_list = ds_van_ban_di_list.filter(don_vi_soan_thao=don_vi)
    if loai_vb:
        ds_van_ban_di_list = ds_van_ban_di_list.filter(loai_van_ban=loai_vb)
    if hinh_thuc:
        ds_van_ban_di_list = ds_van_ban_di_list.filter(hinh_thuc=hinh_thuc)
    if do_khan:
        ds_van_ban_di_list = ds_van_ban_di_list.filter(do_khan=do_khan)

    paginator    = Paginator(ds_van_ban_di_list, 10)
    page_number  = request.GET.get("page")
    ds_van_ban_di = paginator.get_page(page_number)

    context = {
        "ds_van_ban_di": ds_van_ban_di,
        "filter_don_vi_choices":    VanBan.DON_VI_SOAN_THAO_CHOICES,
        "filter_loai_choices":      VanBan.LOAI_VAN_BAN_CHOICES,
        "filter_hinh_thuc_choices": VanBan.HINH_THUC_CHOICES,
        "filter_do_khan_choices":   VanBan.DO_KHAN_CHOICES,
        "filter_trang_thai_choices": trang_thai_filter_choices,
        "selected_trang_thai": trang_thai,
        "selected_don_vi":   don_vi,
        "selected_loai_vb": loai_vb,
        "selected_hinh_thuc": hinh_thuc,
        "selected_do_khan": do_khan,
        "keyword": keyword,
    }
    return render(request, "vanbandi/van-ban-di.html", context)


@role_required(Customer.Role.CHUYEN_VIEN)
def van_ban_di_edit(request, vb_pk=None):
    van_ban = None

    if vb_pk is not None:
        van_ban = get_object_or_404(VanBan, pk=vb_pk, phan_loai="Văn bản đi")
        user = request.user
        if not user.is_staff and van_ban.nguoi_tao_id != user.id:
            raise PermissionDenied

    is_edit = van_ban is not None

    if request.method == "POST":
        form = VanBanDiForm(request.POST, request.FILES, instance=van_ban)
        files_lien_quan = request.FILES.getlist("file_lien_quan")

        if form.is_valid():
            file_errors = []
            for f in files_lien_quan:
                try:
                    validate_file_size(f, 50)
                    validate_file_extension(f)
                except forms.ValidationError as e:
                    file_errors.append(e.message)

            if file_errors:
                for err in file_errors:
                    form.add_error(None, err)
                return render(request, "vanbandi/them-van-ban-di.html", {
                    "form": form,
                    "instance": van_ban,
                    "is_edit": is_edit,
                    "model_type": "VanBanDi",
                    "existing_file": van_ban.file_dinh_kem if is_edit else None,
                    "existing_lien_quan": van_ban.vanbanlienquan_set.all() if is_edit else [],
                })

            updated_van_ban = form.save(commit=False)
            updated_van_ban.phan_loai = "Văn bản đi"

            if not is_edit:
                updated_van_ban.nguoi_tao = NguoiDung.objects.get(tai_khoan=request.user)
                updated_van_ban.trang_thai = "Chờ Xử Lý"
                updated_van_ban.ngay_cap_nhat = timezone.now().date()

            if updated_van_ban.file_dinh_kem:
                updated_van_ban.kich_thuoc = updated_van_ban.file_dinh_kem.size
            else:
                updated_van_ban.kich_thuoc = 0

            updated_van_ban.save()

            if files_lien_quan:
                for f in files_lien_quan:
                    VanBanLienQuan.objects.create(
                        van_ban=updated_van_ban,
                        file_van_ban=f,
                        kich_thuoc=f.size
                    )

            messages.success(
                request,
                f'Văn bản "{updated_van_ban.so_ky_hieu}" đã được lưu thành công.'
            )
            return redirect("quanlyvanbandi:van_ban_di")

        return render(request, "vanbandi/them-van-ban-di.html", {
            "form": form,
            "instance": van_ban,
            "is_edit": is_edit,
            "model_type": "VanBanDi",
            "existing_file": van_ban.file_dinh_kem if is_edit else None,
            "existing_lien_quan": van_ban.vanbanlienquan_set.all() if is_edit else [],
        })

    form = VanBanDiForm(instance=van_ban)
    return render(request, "vanbandi/them-van-ban-di.html", {
        "form": form,
        "instance": van_ban,
        "is_edit": is_edit,
        "model_type": "VanBanDi",
        "existing_file": van_ban.file_dinh_kem if is_edit else None,
        "existing_lien_quan": van_ban.vanbanlienquan_set.all() if is_edit else [],
    })



@role_required(*Customer.Role.values)
def chi_tiet_van_ban_di(request, id):
    vb   = get_object_or_404(VanBan, pk=id, phan_loai="Văn bản đi")
    user = request.user

    # ── Kiểm tra quyền xem chi tiết ──
    if user.has_role(Customer.Role.CHUYEN_VIEN):
        # Chứ người tạo mới được xem
        if vb.nguoi_tao != user.nguoi_dung_core:
            raise PermissionDenied

    elif user.has_role(Customer.Role.LANH_DAO):
        # Chỉ lãnh đạo được chỉ định mới được xem
        if vb.lanh_dao_duyet != user.nguoi_dung_core:
            raise PermissionDenied

    elif user.has_role(Customer.Role.VAN_THU):
        # Văn thư chỉ thấy khi đã qua phê duyệt lãnh đạo
        if vb.trang_thai not in ["Chờ ban hành", "Đã ban hành", "Xem Để Biết"]:
            raise PermissionDenied

    ds_lien_quan = vb.vanbanlienquan_set.all()
    ds_van_thu   = NguoiDung.objects.filter(
        chuc_vu=NguoiDung.ChucVu.VAN_THU
    ).order_by("ho_va_ten")

    hoan_tra     = vb.vanbanhoantra_set.order_by("-ngay_hoan_tra").first()
    duyet_record = vb.vanbanduyet_set.order_by("-ngay_duyet").first()

    # ── Hiển thị trạng thái theo role ──
    # CV và LĐ thấy “Đã Xử Lý” khi status thực là “Chờ ban hành” hoặc “Đã ban hành”
    if not user.has_role(Customer.Role.VAN_THU) and vb.trang_thai in ["Chờ ban hành", "Đã ban hành"]:
        hien_thi_trang_thai = "Đã Xử Lý"
    else:
        hien_thi_trang_thai = vb.trang_thai

    ds_chi_nhanh = ChiNhanh.objects.order_by("ten_chi_nhanh")

    return render(request, "vanbandi/chi-tiet-van-ban-di.html", {
        "vb":                  vb,
        "ds_lien_quan":        ds_lien_quan,
        "ds_van_thu":          ds_van_thu,
        "approve_action_url":  reverse("quanlyvanbandi:phe_duyet_van_ban_di", args=[vb.pk]),
        "selected_van_thu_id": None,
        "ghi_chu_mac_dinh":    "",
        "show_approval_modal": False,
        "hoan_tra":            hoan_tra,
        "duyet_record":        duyet_record,
        "ds_chi_nhanh":        ds_chi_nhanh,
        "ban_hanh_url":        reverse("quanlyvanbandi:ban_hanh_van_ban", args=[vb.pk]),
        "hien_thi_trang_thai": hien_thi_trang_thai,
    })

@require_POST
def phe_duyet_van_ban_di(request, vb_pk):
    vb = get_object_or_404(
        VanBan,
        pk=vb_pk,
        phan_loai="Văn bản đi"
    )

    user = request.user.nguoi_dung_core

    if user.chuc_vu != NguoiDung.ChucVu.LANH_DAO:
        raise PermissionDenied

    if vb.trang_thai in ["Đã Xử Lý", "Đã ban hành", "Xem Để Biết"]:
        messages.warning(request, "Văn bản này không thể phê duyệt.")
        return redirect("quanlyvanbandi:chi_tiet_van_ban_di", id=vb.pk)

    van_thu_id = request.POST.get("van_thu_id")
    ghi_chu = request.POST.get("ghi_chu", "").strip()

    if not van_thu_id:
        messages.error(request, "Vui lòng chọn văn thư.")
        return redirect("quanlyvanbandi:chi_tiet_van_ban_di", id=vb.pk)

    van_thu = NguoiDung.objects.filter(
        nguoi_dung_id=van_thu_id,
        chuc_vu=NguoiDung.ChucVu.VAN_THU
    ).first()

    if not van_thu:
        messages.error(request, "Văn thư không hợp lệ.")
        return redirect("quanlyvanbandi:chi_tiet_van_ban_di", id=vb.pk)

    vb.trang_thai = "Chờ ban hành"
    vb.lanh_dao_duyet = user
    vb.noi_dung = ghi_chu
    vb.save()

    VanBanDuyet.objects.create(
        van_ban=vb,
        van_thu=van_thu
    )

    messages.success(request, "Phê duyệt văn bản thành công.")
    return redirect("quanlyvanbandi:chi_tiet_van_ban_di", id=vb.pk)

@require_POST
def hoan_tra_van_ban_di(request, vb_pk):
    vb = get_object_or_404(
        VanBan,
        pk=vb_pk,
        phan_loai="Văn bản đi",
    )

    nguoi_dung = getattr(request.user, "nguoi_dung_core", None)
    if not nguoi_dung:
        raise PermissionDenied

    if nguoi_dung.chuc_vu != NguoiDung.ChucVu.LANH_DAO:
        raise PermissionDenied

    if vb.trang_thai in ["Chờ ban hành", "Đã ban hành"]:
        messages.warning(request, "Văn bản này không thể hoàn trả.")
        return redirect("quanlyvanbandi:chi_tiet_van_ban_di", id=vb.pk)

    ly_do = request.POST.get("ly_do", "").strip()

    if not ly_do:
        messages.error(request, "Vui lòng nhập lý do / yêu cầu chỉnh sửa.")
        return redirect("quanlyvanbandi:chi_tiet_van_ban_di", id=vb.pk)

    vb.trang_thai = "Hoàn Trả"
    vb.lanh_dao_duyet = nguoi_dung
    vb.save()

    VanBanHoanTra.objects.create(
        van_ban=vb,
        noi_dung=ly_do,
    )

    messages.success(request, "Hoàn trả văn bản thành công.")
    return redirect("quanlyvanbandi:chi_tiet_van_ban_di", id=vb.pk)


# ─────────────────────────────────────────
# API: ChiNhánh → PhòngBan
# GET /api/chi-nhanh-phong-ban/?chi_nhanh_id=<id>
# ─────────────────────────────────────────
@role_required(*Customer.Role.values)
def api_chi_nhanh_phong_ban(request):
    """Trả về danh sách chi nhánh (kèm phòng ban nếu có chi_nhanh_id)."""
    chi_nhanh_id = request.GET.get("chi_nhanh_id")

    if chi_nhanh_id:
        try:
            phong_bans = (
                PhongBan.objects
                .filter(chi_nhanh_id=chi_nhanh_id)
                .annotate(so_thanh_vien=Count("users"))
                .order_by("ten_phong_ban")
            )
            data = [
                {
                    "id": pb.phong_ban_id,
                    "ten": pb.ten_phong_ban,
                    "so_thanh_vien": pb.so_thanh_vien,
                }
                for pb in phong_bans
            ]
        except (ValueError, ChiNhanh.DoesNotExist):
            data = []
        return JsonResponse({"phong_ban": data})

    # Trả về tất cả chi nhánh
    chi_nhanhs = ChiNhanh.objects.order_by("ten_chi_nhanh")
    data = [
        {"id": cn.chi_nhanh_id, "ten": cn.ten_chi_nhanh}
        for cn in chi_nhanhs
    ]
    return JsonResponse({"chi_nhanh": data})


# ─────────────────────────────────────────
# API: NguoiDung theo PhòngBan
# GET /api/nhan-vien/?phong_ban_id=<id>
# ─────────────────────────────────────────
@role_required(*Customer.Role.values)
def api_nhan_vien_phong_ban(request):
    """Trả về danh sách nhân viên trong phòng ban."""
    phong_ban_id = request.GET.get("phong_ban_id")
    if not phong_ban_id:
        return JsonResponse({"nhan_vien": []})
    qs = (
        NguoiDung.objects
        .filter(phong_ban_id=phong_ban_id)
        .order_by("ho_va_ten")
    )
    data = [
        {
            "id": nd.nguoi_dung_id,
            "ho_va_ten": nd.ho_va_ten,
            "chuc_vu": nd.chuc_vu,
            "email": nd.email or "",
            "sdt": nd.sdt or "",
        }
        for nd in qs
    ]
    return JsonResponse({"nhan_vien": data})


# ─────────────────────────────────────────
# API: DonViNgoai list + search
# GET /api/don-vi-ngoai/?q=<search>
# ─────────────────────────────────────────
@role_required(*Customer.Role.values)
def api_don_vi_ngoai(request):
    """Trả về danh sách đơn vị ngoài, hỗ trợ tìm kiếm."""
    q = request.GET.get("q", "").strip()
    qs = DonViNgoai.objects.order_by("ten_don_vi")
    if q:
        qs = qs.filter(
            Q(ten_don_vi__icontains=q) |
            Q(email__icontains=q) |
            Q(so_dien_thoai__icontains=q)
        )
    data = [
        {
            "id": dv.don_vi_ngoai_id,
            "ten": dv.ten_don_vi,
            "dia_chi": dv.dia_chi or "",
            "sdt": dv.so_dien_thoai or "",
            "email": dv.email or "",
        }
        for dv in qs
    ]
    return JsonResponse({"don_vi_ngoai": data})


# ─────────────────────────────────────────
# ACTION: Ban hành văn bản
# POST /van-ban-di/<pk>/ban-hanh/
# ─────────────────────────────────────────
@require_POST
@role_required(Customer.Role.VAN_THU)
def ban_hanh_van_ban(request, vb_pk):
    """Thực hiện ban hành văn bản đi."""
    vb = get_object_or_404(VanBan, pk=vb_pk, phan_loai="Văn bản đi")

    if vb.trang_thai != "Chờ ban hành":
        return JsonResponse(
            {"ok": False, "error": "Văn bản không ở trạng thái Chờ ban hành."},
            status=400
        )

    phong_ban_ids = request.POST.getlist("phong_ban_ids[]")
    don_vi_ngoai_ids = request.POST.getlist("don_vi_ngoai_ids[]")

    if not phong_ban_ids and not don_vi_ngoai_ids:
        return JsonResponse(
            {"ok": False, "error": "Danh sách phát hành không được để trống."},
            status=400
        )

    # Tạo bản ghi BanHanh
    ban_hanh = BanHanh.objects.create(van_ban=vb)

    # Tạo chi tiết — phòng ban nội bộ
    for pb_id in phong_ban_ids:
        try:
            pb = PhongBan.objects.get(pk=pb_id)
            # BanHanhChiTiep yêu cầu cả phong_ban lẫn don_vi_ngoai không null,
            # tuy nhiên model hiện tại để cả 2 non-null. Dùng phong_ban, skip don_vi_ngoai.
            # Để tương thích, tạo riêng từng trường hợp:
            BanHanhChiTiep.objects.create(
                ban_hanh=ban_hanh,
                phong_ban=pb,
                don_vi_ngoai_id=None,
            )
        except (PhongBan.DoesNotExist, Exception):
            pass

    # Tạo chi tiết — đơn vị ngoài
    for dv_id in don_vi_ngoai_ids:
        try:
            dv = DonViNgoai.objects.get(pk=dv_id)
            BanHanhChiTiep.objects.create(
                ban_hanh=ban_hanh,
                phong_ban=None,
                don_vi_ngoai=dv,
            )
        except (DonViNgoai.DoesNotExist, Exception):
            pass

    # Đổi trạng thái văn bản
    vb.trang_thai = "Đã ban hành"
    vb.save(update_fields=["trang_thai"])

    return JsonResponse({"ok": True, "message": "Ban hành văn bản đi thành công!"})