import json
from datetime import timedelta, date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils import timezone
from django import forms
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse

from ..accounts.decorators import role_required
from ..accounts.models import Customer
from ..core.models import (
    VanBan, VanBanLienQuan, NguoiDung, VanBanDuyet, VanBanHoanTra, NoiNhanVanBan,
    ChiNhanh, PhongBan, DonViNgoai, BanHanh,
    HoSoVanBan, CongViec, ChuyenTiep, ChuyenTiepChiTiet,
    ChuKySo, LichSuKySo
)
from .forms import VanBanDiForm, validate_file_size, validate_file_extension
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.db import IntegrityError
from apps.core.utils.activity_log import ghi_lich_su_van_ban

STATUS_XEM_DE_BIET = "Xem Để Biết"
STATUS_DA_BAN_HANH = "Đã ban hành"


def _current_core_user(request):
    return request.user.core_profile


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

    return ds_van_ban


def _user_is_document_creator(request, van_ban):
    return van_ban.nguoi_tao_id == _current_core_user(request).pk


def _user_is_assigned_approver(request, van_ban):
    return van_ban.lanh_dao_duyet_id == _current_core_user(request).pk


def _empty_q():
    return Q(pk__in=[])


def _main_flow_q_for_user(user, core_user):
    if user.has_role(Customer.Role.ADMIN):
        return Q()
    if not core_user:
        return _empty_q()
    if user.has_role(Customer.Role.CHUYEN_VIEN):
        return Q(nguoi_tao=core_user)
    if user.has_role(Customer.Role.LANH_DAO):
        return Q(lanh_dao_duyet=core_user)
    if user.has_role(Customer.Role.VAN_THU):
        return Q(vanbanduyet__van_thu=core_user)
    return _empty_q()


def _recipient_q_for_user(core_user):
    if not core_user or not core_user.phong_ban_id:
        return _empty_q()
    return Q(
        trang_thai=STATUS_DA_BAN_HANH,
        noinhanvanban__phong_ban_id=core_user.phong_ban_id,
    )


def _safe_duyet_record(van_ban):
    try:
        return van_ban.vanbanduyet
    except VanBanDuyet.DoesNotExist:
        return None


def _recipient_record_for_user(van_ban, core_user):
    if not core_user or not core_user.phong_ban_id:
        return None
    for noi_nhan in van_ban.noinhanvanban_set.all():
        if noi_nhan.phong_ban_id == core_user.phong_ban_id:
            return noi_nhan
    return None


def _is_main_flow_user(request, van_ban, duyet_record=None):
    user = request.user
    if user.has_role(Customer.Role.ADMIN):
        return True
    core_user = _current_core_user(request)
    if van_ban.nguoi_tao_id == core_user.pk or van_ban.lanh_dao_duyet_id == core_user.pk:
        return True
    duyet_record = duyet_record if duyet_record is not None else _safe_duyet_record(van_ban)
    return bool(
        user.has_role(Customer.Role.VAN_THU)
        and duyet_record
        and duyet_record.van_thu_id == core_user.pk
    )


def _display_status_for_user(request, van_ban, duyet_record=None):
    core_user = _current_core_user(request)
    if _is_main_flow_user(request, van_ban, duyet_record):
        if not request.user.has_role(Customer.Role.VAN_THU) and van_ban.trang_thai == "Chờ ban hành":
            return "Đã Xử Lý"
        return van_ban.trang_thai

    recipient_record = _recipient_record_for_user(van_ban, core_user)
    if recipient_record:
        return recipient_record.trang_thai_nguoi_nhan or STATUS_XEM_DE_BIET

    return van_ban.trang_thai


def _attach_display_statuses(request, documents):
    for van_ban in documents:
        van_ban.hien_thi_trang_thai = _display_status_for_user(
            request,
            van_ban,
            _safe_duyet_record(van_ban),
        )
    return documents


@role_required(*Customer.Role.values)
def van_ban_di(request):
    trang_thai = request.GET.get("trang_thai", "").strip()
    keyword    = request.GET.get("keyword", "").strip()
    don_vi_soan_thao = request.GET.get("don_vi_soan_thao", "").strip()
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

    core_user = _current_core_user(request)
    main_flow_q = _main_flow_q_for_user(user, core_user)
    recipient_q = _recipient_q_for_user(core_user)

    # ── Lọc theo quyền xem ──
    if user.has_role(Customer.Role.CHUYEN_VIEN):
        ds_van_ban_di_list = ds_van_ban_di_list.filter(main_flow_q | recipient_q).distinct()
    elif user.has_role(Customer.Role.LANH_DAO):
        ds_van_ban_di_list = ds_van_ban_di_list.filter(main_flow_q | recipient_q).distinct()
    elif user.has_role(Customer.Role.VAN_THU):
        ds_van_ban_di_list = ds_van_ban_di_list.filter(main_flow_q | recipient_q).distinct()

    # Cảnh báo văn bản sắp đến hạn (chỉ áp dụng cho Lãnh đạo/Chuyên viên)
    today = timezone.localdate()
    han_canh_bao = today + timedelta(days=3)

    canh_bao_qs = VanBan.objects.filter(
        phan_loai="Văn bản đi",
        trang_thai__in=["Chờ Xử Lý", "Hoàn Trả"],
    ).select_related("lanh_dao_duyet", "nguoi_tao").prefetch_related("vanbanhoantra_set")

    if user.has_role(Customer.Role.LANH_DAO):
        canh_bao_van_ban_sap_het_han_raw = list(
            canh_bao_qs.filter(
                lanh_dao_duyet=user.nguoi_dung_core,
            )
        )
    elif user.has_role(Customer.Role.CHUYEN_VIEN):
        canh_bao_van_ban_sap_het_han_raw = list(
            canh_bao_qs.filter(
                nguoi_tao=user.nguoi_dung_core,
            )
        )
    else:
        canh_bao_van_ban_sap_het_han_raw = []

    canh_bao_van_ban_sap_het_han = []
    for vb in canh_bao_van_ban_sap_het_han_raw:
        effective_deadline = vb.han_xu_ly
        if vb.trang_thai == "Hoàn Trả":
            hoan_tra_list = list(vb.vanbanhoantra_set.all())
            if hoan_tra_list:
                latest_hoan_tra = sorted(hoan_tra_list, key=lambda x: x.ngay_hoan_tra, reverse=True)[0]
                effective_deadline = latest_hoan_tra.han_xu_ly_hoan_tra

        if effective_deadline and effective_deadline <= han_canh_bao:
            vb.han_xu_ly_hien_thi = effective_deadline
            so_ngay_con_lai = (effective_deadline - today).days
            vb.so_ngay_con_lai = so_ngay_con_lai
            vb.so_ngay_qua_han = abs(so_ngay_con_lai) if so_ngay_con_lai < 0 else 0
            canh_bao_van_ban_sap_het_han.append(vb)
            
    # Sort by nearest deadline and limit to 20
    canh_bao_van_ban_sap_het_han = sorted(canh_bao_van_ban_sap_het_han, key=lambda x: x.han_xu_ly_hien_thi)[:20]

    # Danh sách đơn vị soạn thảo (người tạo) cho bộ lọc
    creator_ids = ds_van_ban_di_list.values_list("nguoi_tao_id", flat=True).distinct()
    creators = (
        NguoiDung.objects.filter(pk__in=creator_ids)
        .select_related("phong_ban")
        .order_by("ho_va_ten")
    )
    filter_don_vi_choices = [
        (
            str(creator.pk),
            f"{creator.phong_ban.ten_phong_ban} - {creator.ho_va_ten}"
            if creator.phong_ban
            else creator.ho_va_ten,
        )
        for creator in creators
    ]

    # ── Bộ lọc trạng thái: "Dã Xử Lý" của CV/LĐ = Chờ ban hành + Đã ban hành + Đã Xử Lý ──
    if trang_thai:
        if trang_thai == "Đã Xử Lý" and not user.has_role(Customer.Role.VAN_THU):
            ds_van_ban_di_list = ds_van_ban_di_list.filter(
                main_flow_q,
                trang_thai__in=["Đã Xử Lý", "Chờ ban hành", "Đã ban hành"]
            )
        elif trang_thai == STATUS_XEM_DE_BIET:
            ds_van_ban_di_list = ds_van_ban_di_list.filter(recipient_q).exclude(main_flow_q)
        elif trang_thai == STATUS_DA_BAN_HANH:
            ds_van_ban_di_list = ds_van_ban_di_list.filter(main_flow_q, trang_thai=STATUS_DA_BAN_HANH)
        else:
            ds_van_ban_di_list = ds_van_ban_di_list.filter(trang_thai=trang_thai)

    if don_vi_soan_thao:
        try:
            ds_van_ban_di_list = ds_van_ban_di_list.filter(nguoi_tao_id=int(don_vi_soan_thao))
        except ValueError:
            pass

    if keyword:
        ds_van_ban_di_list = ds_van_ban_di_list.filter(
            Q(so_ky_hieu__icontains=keyword) | Q(trich_yeu__icontains=keyword)
        )
    if loai_vb:
        ds_van_ban_di_list = ds_van_ban_di_list.filter(loai_van_ban=loai_vb)
    if hinh_thuc:
        ds_van_ban_di_list = ds_van_ban_di_list.filter(hinh_thuc=hinh_thuc)
    if do_khan:
        ds_van_ban_di_list = ds_van_ban_di_list.filter(do_khan=do_khan)

    ds_van_ban_di_list = ds_van_ban_di_list.select_related(
        "nguoi_tao",
        "nguoi_tao__phong_ban",
        "lanh_dao_duyet",
        "vanbanduyet",
    ).prefetch_related(
        "noinhanvanban_set__phong_ban",
        "noinhanvanban_set__don_vi_ngoai",
    )

    paginator    = Paginator(ds_van_ban_di_list, 10)
    page_number  = request.GET.get("page")
    ds_van_ban_di = paginator.get_page(page_number)
    _attach_display_statuses(request, ds_van_ban_di.object_list)

    context = {
        "ds_van_ban_di": ds_van_ban_di,
        "filter_don_vi_choices":    filter_don_vi_choices,
        "filter_loai_choices":      VanBan.LOAI_VAN_BAN_CHOICES,
        "filter_hinh_thuc_choices": VanBan.HINH_THUC_CHOICES,
        "filter_do_khan_choices":   VanBan.DO_KHAN_CHOICES,
        "filter_trang_thai_choices": trang_thai_filter_choices,
        "selected_trang_thai": trang_thai,
        "selected_don_vi": don_vi_soan_thao,
        "selected_loai_vb": loai_vb,
        "selected_hinh_thuc": hinh_thuc,
        "selected_do_khan": do_khan,
        "keyword": keyword,
        "canh_bao_van_ban_sap_het_han": canh_bao_van_ban_sap_het_han,
    }
    return render(request, "vanbandi/van-ban-di.html", context)


@role_required(Customer.Role.CHUYEN_VIEN, Customer.Role.LANH_DAO)
def van_ban_di_edit(request, vb_pk=None):
    van_ban = None
    ds_chi_nhanh = ChiNhanh.objects.order_by("ten_chi_nhanh")
    user = request.user

    if vb_pk is None and user.has_role(Customer.Role.LANH_DAO):
        raise PermissionDenied

    if vb_pk is not None:
        van_ban = get_object_or_404(VanBan, pk=vb_pk, phan_loai="Văn bản đi")
        if user.has_role(Customer.Role.CHUYEN_VIEN) and not _user_is_document_creator(request, van_ban):
            raise PermissionDenied
        if user.has_role(Customer.Role.LANH_DAO) and not _user_is_assigned_approver(request, van_ban):
            raise PermissionDenied

    is_edit = van_ban is not None

    if request.method == "POST":
        form = VanBanDiForm(request.POST, request.FILES, instance=van_ban)
        files_lien_quan = request.FILES.getlist("file_lien_quan")

        if form.is_valid():
            so_ky_hieu = form.cleaned_data.get('so_ky_hieu', '').strip()
            trich_yeu = form.cleaned_data.get('trich_yeu', '').strip()

            # --- Validate trùng số ký hiệu ---
            qs_check = VanBan.objects.filter(phan_loai="Văn bản đi")
            if is_edit:
                qs_check = qs_check.exclude(pk=van_ban.pk)

            if qs_check.filter(so_ky_hieu__iexact=so_ky_hieu).exists():
                form.add_error(
                    'so_ky_hieu',
                    f'Số ký hiệu "{so_ky_hieu}" đã tồn tại. Vui lòng nhập số ký hiệu khác.'
                )
                return render(request, "vanbandi/them-van-ban-di.html", {
                    "form": form,
                    "instance": van_ban,
                    "is_edit": is_edit,
                    "model_type": "VanBanDi",
                    "existing_file": van_ban.file_dinh_kem if is_edit else None,
                    "existing_lien_quan": van_ban.vanbanlienquan_set.all() if is_edit else [],
                    "ds_chi_nhanh": ds_chi_nhanh,
                })

            # --- Validate trùng trích yếu ---
            if qs_check.filter(trich_yeu__iexact=trich_yeu).exists():
                form.add_error(
                    'trich_yeu',
                    f'Trích yếu "{trich_yeu}" đã tồn tại. Vui lòng nhập trích yếu khác.'
                )
                return render(request, "vanbandi/them-van-ban-di.html", {
                    "form": form,
                    "instance": van_ban,
                    "is_edit": is_edit,
                    "model_type": "VanBanDi",
                    "existing_file": van_ban.file_dinh_kem if is_edit else None,
                    "existing_lien_quan": van_ban.vanbanlienquan_set.all() if is_edit else [],
                    "ds_chi_nhanh": ds_chi_nhanh,
                })

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
                    "ds_chi_nhanh": ds_chi_nhanh,
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

            if request.POST.get("noi_nhan_enabled") == "1":
                phong_ban_ids = [v for v in request.POST.getlist("phong_ban_ids[]") if str(v).isdigit()]
                don_vi_ngoai_ids = [v for v in request.POST.getlist("don_vi_ngoai_ids[]") if str(v).isdigit()]

                NoiNhanVanBan.objects.filter(van_ban=updated_van_ban).delete()

                phong_ban_map = {
                    str(pb.pk): pb
                    for pb in PhongBan.objects.filter(pk__in=set(phong_ban_ids))
                }
                don_vi_ngoai_map = {
                    str(dv.pk): dv
                    for dv in DonViNgoai.objects.filter(pk__in=set(don_vi_ngoai_ids))
                }

                for pb_id in dict.fromkeys(phong_ban_ids):
                    pb = phong_ban_map.get(str(pb_id))
                    if pb is not None:
                        NoiNhanVanBan.objects.create(
                            van_ban=updated_van_ban,
                            phong_ban=pb,
                            don_vi_ngoai=None,
                            trang_thai_nguoi_nhan=STATUS_XEM_DE_BIET,
                        )

                for dv_id in dict.fromkeys(don_vi_ngoai_ids):
                    dv = don_vi_ngoai_map.get(str(dv_id))
                    if dv is not None:
                        NoiNhanVanBan.objects.create(
                            van_ban=updated_van_ban,
                            phong_ban=None,
                            don_vi_ngoai=dv,
                            trang_thai_nguoi_nhan=STATUS_XEM_DE_BIET,
                        )

            hanh_dong = "SUA" if is_edit else "TAO"
            ghi_lich_su_van_ban(
                user=request.user,
                van_ban=updated_van_ban,
                hanh_dong=hanh_dong,
                mo_ta=f"{hanh_dong} văn bản đi [{updated_van_ban.so_ky_hieu}]",
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
            "ds_chi_nhanh": ds_chi_nhanh,
        })

    form = VanBanDiForm(instance=van_ban)
    return render(request, "vanbandi/them-van-ban-di.html", {
        "form": form,
        "instance": van_ban,
        "is_edit": is_edit,
        "model_type": "VanBanDi",
        "existing_file": van_ban.file_dinh_kem if is_edit else None,
        "existing_lien_quan": van_ban.vanbanlienquan_set.all() if is_edit else [],
        "ds_chi_nhanh": ds_chi_nhanh,
    })



@role_required(*Customer.Role.values)
@ensure_csrf_cookie
def chi_tiet_van_ban_di(request, id):
    vb   = get_object_or_404(VanBan, pk=id, phan_loai="Văn bản đi")
    user = request.user

    core_user = _current_core_user(request)

    # ── Cho phép xem nếu văn bản đã ban hành và người dùng thuộc phòng ban nhận ──
    recipient_record = None
    if vb.trang_thai == STATUS_DA_BAN_HANH:
        recipient_record = _recipient_record_for_user(vb, core_user)
    is_in_receiving_dept = recipient_record is not None

    # ── Kiểm tra quyền xem chi tiết ──
    if not is_in_receiving_dept:
        if user.has_role(Customer.Role.CHUYEN_VIEN):
            if not _user_is_document_creator(request, vb):
                raise PermissionDenied

        elif user.has_role(Customer.Role.LANH_DAO):
            if not _user_is_assigned_approver(request, vb):
                raise PermissionDenied

        elif user.has_role(Customer.Role.VAN_THU):
            if vb.trang_thai not in ["Chờ ban hành", "Đã ban hành", "Xem Để Biết"]:
                raise PermissionDenied
            
            duyet = VanBanDuyet.objects.filter(van_ban=vb).first()
            if not duyet or duyet.van_thu_id != core_user.pk:
                raise PermissionDenied

    ds_lien_quan = vb.vanbanlienquan_set.all()
    ds_van_thu   = NguoiDung.objects.filter(
        chuc_vu=NguoiDung.ChucVu.VAN_THU
    ).order_by("ho_va_ten")

    hoan_tra     = vb.vanbanhoantra_set.order_by("-ngay_hoan_tra").first()
    duyet_record = VanBanDuyet.objects.filter(van_ban=vb).first()

    noi_nhan_noi_bo = (
        vb.noinhanvanban_set.filter(phong_ban__isnull=False)
        .select_related("phong_ban", "phong_ban__chi_nhanh", "phong_ban__truong_phong")
        .order_by("phong_ban__chi_nhanh__ten_chi_nhanh", "phong_ban__ten_phong_ban")
    )
    noi_nhan_don_vi_ngoai = (
        vb.noinhanvanban_set.filter(don_vi_ngoai__isnull=False)
        .select_related("don_vi_ngoai")
        .order_by("don_vi_ngoai__ten_don_vi")
    )

    can_view_sensitive_notes = True
    if is_in_receiving_dept:
        if user.has_role(Customer.Role.CHUYEN_VIEN) and not _user_is_document_creator(request, vb):
            can_view_sensitive_notes = False
        elif user.has_role(Customer.Role.LANH_DAO) and not _user_is_assigned_approver(request, vb):
            can_view_sensitive_notes = False
        elif user.has_role(Customer.Role.VAN_THU):
            duyet = VanBanDuyet.objects.filter(van_ban=vb).first()
            if not duyet or duyet.van_thu_id != core_user.pk:
                can_view_sensitive_notes = False

    # ── Hiển thị trạng thái theo vai trò: luồng xử lý dùng trạng thái chính,
    # người nhận dùng trạng thái riêng trên quan hệ nơi nhận.
    hien_thi_trang_thai = _display_status_for_user(request, vb, duyet_record)

    ds_chi_nhanh = ChiNhanh.objects.order_by("ten_chi_nhanh")

    # ===== Dữ liệu cho popup thêm văn bản vào hồ sơ =====
    ds_ho_so = HoSoVanBan.objects.filter(trang_thai=1).order_by('-ho_so_van_ban_id')
    is_van_thu = user.has_role(Customer.Role.VAN_THU)

    return render(request, "vanbandi/chi-tiet-van-ban-di.html", {
        "vb":                  vb,
        "ds_lien_quan":        ds_lien_quan,
        "ds_van_thu":          ds_van_thu,
        "approve_action_url":  reverse("quanlyvanbandi:phe_duyet_van_ban_di", args=[vb.pk]),
        "selected_van_thu_id": None,
        "ghi_chu_mac_dinh":    "",
        "show_approval_modal": False,
        "hoan_tra":            hoan_tra,
        "duyet_record":       duyet_record,
        "ds_chi_nhanh":        ds_chi_nhanh,
        #"ban_hanh_url":        reverse("quanlyvanbandi:ban_hanh_van_ban", args=[vb.pk]),
        "hien_thi_trang_thai":      hien_thi_trang_thai,
        "allow_remove_main_file":    False,
        "allow_remove_related_file": False,
        "ds_ho_so":            ds_ho_so,
        "is_van_thu":          is_van_thu,
        "task": CongViec.objects.filter(van_ban=vb).first(),
        "open_return_modal": request.GET.get("open_return_modal") == "1",
        "noi_nhan_noi_bo": noi_nhan_noi_bo,
        "noi_nhan_don_vi_ngoai": noi_nhan_don_vi_ngoai,
        "can_view_sensitive_notes": can_view_sensitive_notes,
    })

@require_POST
@role_required(Customer.Role.LANH_DAO)
def phe_duyet_van_ban_di(request, vb_pk):
    vb = get_object_or_404(
        VanBan,
        pk=vb_pk,
        phan_loai="Văn bản đi"
    )

    user = _current_core_user(request)

    if user.chuc_vu != NguoiDung.ChucVu.LANH_DAO:
        raise PermissionDenied

    if not _user_is_assigned_approver(request, vb):
        raise PermissionDenied

    if vb.trang_thai in ["Chờ ban hành", "Đã Xử Lý", "Đã ban hành", "Xem Để Biết"]:
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
    vb.save(update_fields=["trang_thai", "lanh_dao_duyet"])

    duyet, _created = VanBanDuyet.objects.get_or_create(
        van_ban=vb,
        defaults={"van_thu": van_thu},
    )

    if duyet.van_thu_id != van_thu.pk:
        duyet.van_thu = van_thu

    duyet.ghi_chu = ghi_chu or None
    duyet.save()

    ghi_lich_su_van_ban(
        user=request.user, van_ban=vb, hanh_dong="DUYET",
        trang_thai_cu="Chờ Xử Lý", trang_thai_moi="Chờ ban hành",
    )

    messages.success(request, "Phê duyệt văn bản thành công.")
    return redirect("quanlyvanbandi:chi_tiet_van_ban_di", id=vb.pk)

@require_POST
@role_required(Customer.Role.LANH_DAO)
def hoan_tra_van_ban_di(request, vb_pk):
    vb = get_object_or_404(
        VanBan,
        pk=vb_pk,
        phan_loai="Văn bản đi",
    )

    nguoi_dung = _current_core_user(request)

    if nguoi_dung.chuc_vu != NguoiDung.ChucVu.LANH_DAO:
        raise PermissionDenied

    if not _user_is_assigned_approver(request, vb):
        raise PermissionDenied

    if vb.trang_thai in ["Chờ ban hành", "Đã ban hành", "Đã Xử Lý", "Xem Để Biết"]:
        messages.warning(request, "Văn bản này không thể hoàn trả.")
        return redirect("quanlyvanbandi:chi_tiet_van_ban_di", id=vb.pk)

    ly_do = request.POST.get("ly_do", "").strip()
    han_xu_ly_raw = request.POST.get("han_xu_ly_hoan_tra", "").strip()

    if not ly_do:
        messages.error(request, "Vui lòng nhập lý do / yêu cầu chỉnh sửa.")
        return redirect(reverse("quanlyvanbandi:chi_tiet_van_ban_di", args=[vb.pk]) + "?open_return_modal=1")

    if not han_xu_ly_raw:
        messages.error(request, "Vui lòng nhập hạn xử lý hoàn trả.")
        return redirect(reverse("quanlyvanbandi:chi_tiet_van_ban_di", args=[vb.pk]) + "?open_return_modal=1")

    try:
        han_xu_ly_hoan_tra = date.fromisoformat(han_xu_ly_raw)
    except ValueError:
        messages.error(request, "Hạn xử lý hoàn trả không hợp lệ.")
        return redirect(reverse("quanlyvanbandi:chi_tiet_van_ban_di", args=[vb.pk]) + "?open_return_modal=1")

    today = timezone.localdate()
    if han_xu_ly_hoan_tra < today:
        messages.error(request, "Hạn xử lý hoàn trả không được nhỏ hơn ngày hiện tại.")
        return redirect(reverse("quanlyvanbandi:chi_tiet_van_ban_di", args=[vb.pk]) + "?open_return_modal=1")

    vb.trang_thai = "Hoàn Trả"
    vb.lanh_dao_duyet = nguoi_dung
    vb.save()

    VanBanHoanTra.objects.create(
        van_ban=vb,
        noi_dung=ly_do,
        han_xu_ly_hoan_tra=han_xu_ly_hoan_tra,
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
            phong_bans = list(
                PhongBan.objects
                .filter(chi_nhanh_id=chi_nhanh_id)
                .select_related("truong_phong")
                .annotate(so_thanh_vien=Count("users"))
                .order_by("ten_phong_ban")
            )
            data = [
                {
                    "id": pb.phong_ban_id,
                    "ten": pb.ten_phong_ban,
                    "so_thanh_vien": pb.so_thanh_vien,
                    "truong_phong": (
                        {
                            "ho_va_ten": pb.truong_phong.ho_va_ten,
                            "sdt": pb.truong_phong.sdt or "",
                            "email": pb.truong_phong.email or "",
                        }
                        if pb.truong_phong_id
                        else None
                    ),
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
@require_http_methods(["GET", "POST", "DELETE"])
def api_don_vi_ngoai(request):
    """Danh sách / thêm / sửa / xóa đơn vị ngoài."""
    if request.method == "GET":
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

    if request.method == "DELETE":
        raw_id = request.GET.get("id", "").strip()
        try:
            dv_id = int(raw_id)
        except ValueError:
            return JsonResponse({"ok": False, "error": "Thiếu hoặc sai id."}, status=400)

        dv = DonViNgoai.objects.filter(pk=dv_id).first()
        if not dv:
            return JsonResponse({"ok": False, "error": "Không tìm thấy đơn vị ngoài."}, status=404)

        dv.delete()
        return JsonResponse({"ok": True})

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Dữ liệu không hợp lệ."}, status=400)

    raw_id = str(payload.get("id") or "").strip()
    ten = str(payload.get("ten") or "").strip()
    dia_chi = str(payload.get("dia_chi") or payload.get("daiDien") or "").strip()
    sdt = str(payload.get("sdt") or "").strip()
    email = str(payload.get("email") or "").strip() or None

    if not ten:
        return JsonResponse({"ok": False, "error": "Thiếu tên đơn vị."}, status=400)
    if not dia_chi:
        return JsonResponse({"ok": False, "error": "Thiếu địa chỉ."}, status=400)

    if raw_id:
        try:
            dv_id = int(raw_id)
        except ValueError:
            return JsonResponse({"ok": False, "error": "Id không hợp lệ."}, status=400)
        dv = DonViNgoai.objects.filter(pk=dv_id).first()
        if not dv:
            return JsonResponse({"ok": False, "error": "Không tìm thấy đơn vị ngoài."}, status=404)
        dv.ten_don_vi = ten
        dv.dia_chi = dia_chi
        dv.so_dien_thoai = sdt
        dv.email = email
    else:
        dv = DonViNgoai(
            ten_don_vi=ten,
            dia_chi=dia_chi,
            so_dien_thoai=sdt,
            email=email,
        )

    try:
        dv.save()
    except IntegrityError:
        return JsonResponse({"ok": False, "error": "Email đã tồn tại."}, status=400)

    return JsonResponse({
        "ok": True,
        "don_vi_ngoai": {
            "id": dv.don_vi_ngoai_id,
            "ten": dv.ten_don_vi,
            "dia_chi": dv.dia_chi or "",
            "sdt": dv.so_dien_thoai or "",
            "email": dv.email or "",
        }
    })


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
        messages.error(request, "Văn bản không ở trạng thái Chờ ban hành.")
        return redirect("quanlyvanbandi:chi_tiet_van_ban_di", id=vb.pk)

    user = _current_core_user(request)

    duyet = VanBanDuyet.objects.filter(van_ban=vb).first()
    if not duyet or duyet.van_thu_id != user.pk:
        messages.error(request, "Bạn không phải văn thư được lãnh đạo chọn để ban hành văn bản này.")
        return redirect("quanlyvanbandi:chi_tiet_van_ban_di", id=vb.pk)

    # Sau khi ban hành, văn bản đi gốc giữ đúng luồng Văn bản đi.
    vb.trang_thai = STATUS_DA_BAN_HANH
    vb.save(update_fields=["trang_thai"])

    BanHanh.objects.get_or_create(van_ban=vb)
    NoiNhanVanBan.objects.filter(van_ban=vb).update(
        trang_thai_nguoi_nhan=STATUS_XEM_DE_BIET,
    )

    ghi_lich_su_van_ban(
        user=request.user, van_ban=vb, hanh_dong="BAN_HANH",
        trang_thai_cu="Chờ ban hành", trang_thai_moi=STATUS_DA_BAN_HANH,
    )

    messages.success(request, "Ban hành văn bản đi thành công.")
    return redirect("quanlyvanbandi:chi_tiet_van_ban_di", id=vb.pk)


# ─────────────────────────────────────────
# ACTION: Xóa văn bản đi
# POST /van-ban-di/<pk>/xoa/
# ─────────────────────────────────────────
@require_POST
@role_required(Customer.Role.CHUYEN_VIEN)
def xoa_van_ban_di(request, vb_pk):
    """Chuyên viên xóa văn bản đi (chỉ khi Chờ Xử Lý)."""
    vb = get_object_or_404(VanBan, pk=vb_pk, phan_loai="Văn bản đi")

    # Chỉ người tạo mới được xóa
    if not _user_is_document_creator(request, vb):
        raise PermissionDenied

    # Chỉ xóa khi chưa được duyệt
    if vb.trang_thai != "Chờ Xử Lý":
        messages.error(request, "Không thể xóa văn bản đã được xử lý.")
        return redirect("quanlyvanbandi:chi_tiet_van_ban_di", id=vb.pk)

    # Xóa các bản ghi liên quan
    vb.vanbanlienquan_set.all().delete()
    ghi_lich_su_van_ban(user=request.user, van_ban=vb, hanh_dong="XOA", trang_thai_cu=vb.trang_thai)
    vb.delete()

    messages.success(request, "Xóa văn bản thành công.")
    return redirect("quanlyvanbandi:van_ban_di")

import os
from django.conf import settings
from django.core.files.base import ContentFile
from .utils_ky_so import sign_pdf_with_ratio

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

    vb = VanBan.objects.filter(pk=vb_pk, phan_loai="Văn bản đi").first()
    if not vb:
        return JsonResponse({"success": False, "message": "Không tìm thấy văn bản đi cần ký."}, status=404)
    user = _current_core_user(request)

    if vb.lanh_dao_duyet_id != user.pk or vb.trang_thai != "Chờ Xử Lý":
        return JsonResponse({"success": False, "message": "Bạn không có quyền ký văn bản này hoặc văn bản không ở trạng thái Chờ Xử Lý."}, status=403)

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
    output_filename = f"vanban_{vb.pk}_signed_{timestamp}.pdf"
    
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

    return JsonResponse({"success": True, "message": "Ký số thành công."})
