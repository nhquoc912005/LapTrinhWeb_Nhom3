import hashlib
import os
import tempfile
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db import models, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.timezone import make_aware
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required
from apps.accounts.models import Customer
from apps.core.models import (
    ChuKySo,
    CongViec,
    FileCVLienQuan,
    HoanTraCongViec,
    LichSuKySo,
    NguoiDung,
    PheDuyetCongViec,
    PhanCongCongViec,
    VanBan,
)
from apps.quanlyvanbandi.utils_ky_so import sign_pdf_with_ratio

from .forms import ProcessTaskForm, ReturnTaskForm, UpdateTaskResultForm
from apps.core.utils.activity_log import ghi_lich_su_cong_viec


# File này xử lý giao việc, xử lý kết quả, duyệt/hoàn trả công việc và ký số công việc.


def _task_queryset():
    # Queryset chuẩn cho công việc, nạp trước các quan hệ dùng ở danh sách/chi tiết.
    return CongViec.objects.select_related("nguoi_giao", "nguoi_thuc_hien", "van_ban").prefetch_related(
        "filecvlienquan_set",
        "phancongcongviec_set__nguoi_phoi_hop",
        "hoantracongviec_set__nguoi_hoan_tra",
    )


def _get_task(task_id):
    # Lấy công việc hoặc trả 404 nếu task_id không tồn tại.
    return get_object_or_404(_task_queryset(), pk=task_id)


def _task_list_route_name(user):
    # Chọn màn danh sách phù hợp sau khi thao tác xong theo vai trò.
    if user.is_chuyen_vien:
        return "quanlycongviec:xu_ly_cong_viec"
    if user.has_role(Customer.Role.LANH_DAO, Customer.Role.ADMIN):
        return "quanlycongviec:giao_viec"
    return "core:dashboard"


def _redirect_task_list(request):
    # Redirect về danh sách công việc tương ứng với user hiện tại.
    return redirect(_task_list_route_name(request.user))


def _push_form_errors(request, form):
    # Đưa lỗi form vào Django messages để template hiển thị.
    for error in form.non_field_errors():
        messages.error(request, error)

    for field_name, errors in form.errors.items():
        if field_name == "__all__":
            continue
        for error in errors:
            messages.error(request, error)


def _nguoi_dung_la_lanh_dao(nguoi_dung):
    # Kiểm tra một hồ sơ NguoiDung có chức vụ lãnh đạo hay không.
    tai_khoan = getattr(nguoi_dung, "tai_khoan", None)
    if tai_khoan:
        return tai_khoan.role == Customer.Role.LANH_DAO
    return nguoi_dung.chuc_vu == NguoiDung.ChucVu.LANH_DAO


def _user_is_task_manager(request, task):
    # Kiểm tra người dùng có quyền quản lý công việc này.
    return request.user.has_role(Customer.Role.ADMIN) or (
        request.user.is_lanh_dao and request.user.core_profile.pk == task.nguoi_giao_id
    )


def _user_is_task_signer(request, task):
    # Kiểm tra người dùng hiện tại có được ký số công việc này không.
    return request.user.is_lanh_dao and request.user.core_profile.pk == task.nguoi_giao_id


def _user_is_assignee(request, task):
    # Kiểm tra người dùng hiện tại có phải người thực hiện chính.
    return request.user.is_chuyen_vien and request.user.core_profile.pk == task.nguoi_thuc_hien_id


def _task_has_result(task):
    # Kiểm tra công việc đã có nội dung hoặc file kết quả xử lý.
    return bool(task.ket_qua_xu_ly) or FileCVLienQuan.objects.filter(
        cong_viec=task,
        nguon_tai_len=FileCVLienQuan.NguonTaiLen.KET_QUA_XU_LY,
    ).exists()


def _can_view_task(request, task):
    # Quyền xem chi tiết công việc cho quản lý, văn thư, người giao hoặc người thực hiện.
    if request.user.has_role(Customer.Role.ADMIN, Customer.Role.VAN_THU):
        return True
    user_core_id = request.user.core_profile.pk
    return user_core_id in {task.nguoi_giao_id, task.nguoi_thuc_hien_id}


def _can_process_task(request, task):
    # Quyền chuyên viên gửi/cập nhật kết quả xử lý.
    return _user_is_assignee(request, task) and task.cho_phep_chuyen_vien_xu_ly


def _can_return_to_leader(request, task):
    # Quyền chuyên viên hoàn trả lại công việc cho lãnh đạo.
    return (
        _user_is_assignee(request, task)
        and task.trang_thai in {CongViec.TrangThai.CHO_XU_LY, CongViec.TrangThai.HOAN_TRA_CV}
        and _nguoi_dung_la_lanh_dao(task.nguoi_giao)
    )


def _can_return_to_specialist(request, task):
    # Quyền lãnh đạo trả công việc về chuyên viên để bổ sung.
    return _user_is_task_manager(request, task) and task.trang_thai == CongViec.TrangThai.CHO_DUYET


def _parse_task_dates(ngay_bat_dau_str, han_xu_ly_str):
    # Chuyển chuỗi ngày từ form giao việc thành date/datetime aware.
    ngay_bat_dau = datetime.strptime(ngay_bat_dau_str, "%Y-%m-%d").date()
    naive_han_xu_ly = datetime.strptime(han_xu_ly_str, "%Y-%m-%d").replace(
        hour=23,
        minute=59,
        second=59,
    )
    return ngay_bat_dau, make_aware(naive_han_xu_ly)


def _validate_task_dates(ngay_bat_dau, han_xu_ly, *, allow_past_start=False):
    # Validate ngày bắt đầu và hạn xử lý của công việc.
    today = timezone.now().date()
    if not allow_past_start and ngay_bat_dau < today:
        return "Ngày bắt đầu không được nhỏ hơn ngày hiện tại."
    if han_xu_ly.date() < today:
        return "Hạn xử lý không được nhỏ hơn ngày hiện tại."
    if han_xu_ly.date() < ngay_bat_dau:
        return "Hạn xử lý không được nhỏ hơn ngày bắt đầu."
    return ""


def _create_assignment_files(task, files, *, loai_file, nguon_tai_len, nguoi_tai_len):
    # Lưu các file giao việc/kết quả vào FileCVLienQuan.
    for uploaded_file in files:
        FileCVLienQuan.objects.create(
            cong_viec=task,
            file_van_ban=uploaded_file,
            kich_thuoc=uploaded_file.size,
            loai_file=loai_file,
            nguon_tai_len=nguon_tai_len,
            nguoi_tai_len=nguoi_tai_len,
        )


def _get_collaborator_ids(request, assignee_id):
    # Lấy người phối hợp từ POST và loại bỏ người thực hiện chính.
    ids = []
    seen = set()
    skipped_assignee = False

    for raw_id in request.POST.getlist("nguoi_phoi_hop"):
        raw_id = (raw_id or "").strip()
        if not raw_id or not raw_id.isdigit():
            continue
        if raw_id == str(assignee_id):
            skipped_assignee = True
            continue
        if raw_id in seen:
            continue
        seen.add(raw_id)
        ids.append(raw_id)

    return ids, skipped_assignee


def _replace_task_collaborators(task, collaborator_ids):
    # Thay thế toàn bộ danh sách người phối hợp của công việc.
    PhanCongCongViec.objects.filter(cong_viec=task).delete()
    if not collaborator_ids:
        return

    users_by_id = {
        str(user.pk): user
        for user in NguoiDung.objects.filter(pk__in=collaborator_ids)
    }
    PhanCongCongViec.objects.bulk_create(
        [
            PhanCongCongViec(cong_viec=task, nguoi_phoi_hop=users_by_id[raw_id])
            for raw_id in collaborator_ids
            if raw_id in users_by_id
        ]
    )


def _result_files_queryset(task):
    # Queryset file kết quả do chuyên viên upload.
    return FileCVLienQuan.objects.filter(
        cong_viec=task,
        nguon_tai_len=FileCVLienQuan.NguonTaiLen.KET_QUA_XU_LY,
    ).select_related("nguoi_tai_len")


def _original_files_queryset(task):
    # Queryset file ban đầu của công việc khi lãnh đạo giao.
    return FileCVLienQuan.objects.filter(
        cong_viec=task,
        nguon_tai_len=FileCVLienQuan.NguonTaiLen.GIAO_VIEC,
    )


@login_required
@role_required(Customer.Role.LANH_DAO, Customer.Role.ADMIN)
def giao_viec(request):
    """
    Hiển thị danh sách công việc do lãnh đạo/quản trị quản lý.
    GET chỉ đọc dữ liệu và phân trang.
    """
    tasks = _task_queryset().order_by("-last_activity")

    if request.user.is_lanh_dao:
        tasks = tasks.filter(nguoi_giao=request.user.core_profile)

    paginator = Paginator(tasks, 10)
    page_number = request.GET.get("page")
    tasks = paginator.get_page(page_number)

    context = {
        "tasks": tasks,
        "page_obj": tasks,
        "chuyen_vien_list": NguoiDung.objects.filter(chuc_vu=NguoiDung.ChucVu.CHUYEN_VIEN),
        "all_users": NguoiDung.objects.all(),
        "van_ban_list": VanBan.objects.all().order_by("-ngay_den"),
        "is_lanh_dao": request.user.is_lanh_dao,
        "can_assign_task": request.user.has_role(Customer.Role.LANH_DAO, Customer.Role.ADMIN),
        "status_choices": CongViec.TrangThai.choices,
    }
    return render(request, "quanlycongviec/giao-viec.html", context)


@login_required
@role_required(Customer.Role.CHUYEN_VIEN)
def xu_ly_cong_viec(request):
    """
    Hiển thị danh sách công việc của chuyên viên.
    GET chỉ đọc các công việc được giao cho người dùng hiện tại.
    """
    tasks = _task_queryset().filter(nguoi_thuc_hien=request.user.core_profile).order_by("-last_activity")

    paginator = Paginator(tasks, 10)
    page_number = request.GET.get("page")
    tasks = paginator.get_page(page_number)

    context = {
        "tasks": tasks,
        "page_obj": tasks,
        "status_choices": CongViec.TrangThai.choices,
    }
    return render(request, "quanlycongviec/cong-viec-cua-toi.html", context)


@login_required
@role_required(Customer.Role.LANH_DAO, Customer.Role.ADMIN)
def add_task(request):
    """
    Lãnh đạo/quản trị tạo công việc mới.
    POST validate ngày, người thực hiện, file giao việc và ghi lịch sử.
    """
    if request.method != "POST":
        return redirect("quanlycongviec:giao_viec")

    try:
        ten_cv = (request.POST.get("ten_cv") or "").strip()
        nguoi_thuc_hien_id = request.POST.get("nguoi_thuc_hien")
        nguon_giao = request.POST.get("nguon_giao")
        ngay_bat_dau_str = request.POST.get("ngay_bat_dau")
        han_xu_ly_str = request.POST.get("han_xu_ly")
        noi_dung = (request.POST.get("noi_dung") or "").strip()
        ghi_chu = (request.POST.get("ghi_chu") or "").strip()
        yeu_cau_phe_duyet = request.POST.get("yeu_cau_phe_duyet") == "on"
        van_ban_id = request.POST.get("van_ban_id")
        van_ban_den_id = request.POST.get("van_ban_den_id")

        if not all([ten_cv, nguoi_thuc_hien_id, ngay_bat_dau_str, han_xu_ly_str, noi_dung]):
            messages.error(request, "Vui lòng nhập đầy đủ các trường bắt buộc.")
            return redirect("quanlycongviec:giao_viec")

        nguoi_thuc_hien = get_object_or_404(NguoiDung, pk=nguoi_thuc_hien_id)
        nguoi_phoi_hop_ids, skipped_assignee_collaborator = _get_collaborator_ids(
            request,
            nguoi_thuc_hien_id,
        )

        try:
            ngay_bat_dau, han_xu_ly = _parse_task_dates(ngay_bat_dau_str, han_xu_ly_str)
        except ValueError:
            messages.error(request, "Định dạng ngày tháng không hợp lệ.")
            return redirect("quanlycongviec:giao_viec")

        validation_error = _validate_task_dates(ngay_bat_dau, han_xu_ly)
        if validation_error:
            messages.error(request, validation_error)
            return redirect("quanlycongviec:giao_viec")

        with transaction.atomic():
            task = CongViec.objects.create(
                ten_cong_viec=ten_cv,
                noi_dung_cong_viec=noi_dung,
                nguoi_giao=request.user.core_profile,
                nguoi_thuc_hien=nguoi_thuc_hien,
                nguon_giao=nguon_giao,
                trang_thai=CongViec.TrangThai.CHO_XU_LY,
                ngay_bat_dau=ngay_bat_dau,
                han_xu_ly=han_xu_ly,
                ghi_chu=ghi_chu,
                yeu_cau_phe_duyet=yeu_cau_phe_duyet,
                van_ban_id=van_ban_id if van_ban_id else None,
                van_ban_den_id=van_ban_den_id if van_ban_den_id else None,
            )

            _create_assignment_files(
                task,
                request.FILES.getlist("file_dinh_kem"),
                loai_file=FileCVLienQuan.LoaiFile.CHINH,
                nguon_tai_len=FileCVLienQuan.NguonTaiLen.GIAO_VIEC,
                nguoi_tai_len=request.user.core_profile,
            )
            _create_assignment_files(
                task,
                request.FILES.getlist("tai_lieu_lien_quan"),
                loai_file=FileCVLienQuan.LoaiFile.LIEN_QUAN,
                nguon_tai_len=FileCVLienQuan.NguonTaiLen.GIAO_VIEC,
                nguoi_tai_len=request.user.core_profile,
            )

            _replace_task_collaborators(task, nguoi_phoi_hop_ids)

        ghi_lich_su_cong_viec(
            user=request.user, cong_viec=task, hanh_dong="TAO",
            trang_thai_moi=CongViec.TrangThai.CHO_XU_LY,
        )

        messages.success(request, f"Đã giao việc '{ten_cv}' thành công.")
        if skipped_assignee_collaborator:
            messages.warning(request, "Người phối hợp trùng với người thực hiện chính đã được bỏ qua.")
    except Exception as exc:
        messages.error(request, f"Lỗi hệ thống khi giao việc: {exc}")

    return redirect("quanlycongviec:giao_viec")


@login_required
@role_required(Customer.Role.LANH_DAO, Customer.Role.ADMIN)
def delete_task(request, task_id):
    """
    Xóa công việc theo quyền quản lý.
    POST xóa task và các quan hệ liên quan qua cascade.
    """
    task = _get_task(task_id)

    if not _user_is_task_manager(request, task):
        messages.error(request, "Bạn không có quyền xóa công việc này.")
        return redirect("quanlycongviec:task_detail", task_id=task.pk)

    if task.trang_thai != CongViec.TrangThai.CHO_XU_LY:
        messages.error(request, "Chỉ có thể xóa công việc ở trạng thái Chờ xử lý.")
        return redirect("quanlycongviec:task_detail", task_id=task.pk)

    task.delete()
    ghi_lich_su_cong_viec(user=request.user, cong_viec=task, hanh_dong="XOA")
    messages.success(request, "Đã xóa công việc.")
    return redirect("quanlycongviec:giao_viec")


@login_required
@role_required(Customer.Role.LANH_DAO, Customer.Role.ADMIN)
def edit_task(request, task_id):
    """
    Sửa thông tin công việc.
    GET hiển thị form hiện tại, POST cập nhật nội dung, người thực hiện, file và người phối hợp.
    """
    task = _get_task(task_id)

    if not _user_is_task_manager(request, task):
        messages.error(request, "Bạn không có quyền chỉnh sửa công việc này.")
        return redirect("quanlycongviec:task_detail", task_id=task.pk)

    if task.trang_thai not in {CongViec.TrangThai.CHO_XU_LY, CongViec.TrangThai.HOAN_TRA_LD}:
        messages.error(
            request,
            "Công việc này hiện không thể chỉnh sửa. Chỉ cho phép chỉnh sửa ở trạng thái Chờ xử lý hoặc Hoàn trả_LĐ.",
        )
        return redirect("quanlycongviec:task_detail", task_id=task.pk)

    if request.method != "POST":
        return redirect("quanlycongviec:task_detail", task_id=task.pk)

    try:
        ten_cv = (request.POST.get("ten_cv") or "").strip()
        noi_dung = (request.POST.get("noi_dung") or "").strip()
        ngay_bat_dau_str = request.POST.get("ngay_bat_dau")
        han_xu_ly_str = request.POST.get("han_xu_ly")
        nguoi_thuc_hien_id = request.POST.get("nguoi_thuc_hien")
        nguoi_phoi_hop_ids, skipped_assignee_collaborator = _get_collaborator_ids(
            request,
            nguoi_thuc_hien_id,
        )

        if not all([ten_cv, noi_dung, ngay_bat_dau_str, han_xu_ly_str, nguoi_thuc_hien_id]):
            messages.error(request, "Vui lòng nhập đầy đủ các trường bắt buộc.")
            return redirect("quanlycongviec:task_detail", task_id=task.pk)

        try:
            ngay_bat_dau, han_xu_ly = _parse_task_dates(ngay_bat_dau_str, han_xu_ly_str)
        except ValueError:
            messages.error(request, "Định dạng ngày tháng không hợp lệ.")
            return redirect("quanlycongviec:task_detail", task_id=task.pk)

        validation_error = _validate_task_dates(ngay_bat_dau, han_xu_ly, allow_past_start=True)
        if validation_error:
            messages.error(request, validation_error)
            return redirect("quanlycongviec:task_detail", task_id=task.pk)

        with transaction.atomic():
            task.ten_cong_viec = ten_cv
            task.nguon_giao = request.POST.get("nguon_giao")
            task.noi_dung_cong_viec = noi_dung
            task.ghi_chu = (request.POST.get("ghi_chu") or "").strip()
            task.ngay_bat_dau = ngay_bat_dau
            task.han_xu_ly = han_xu_ly
            task.nguoi_thuc_hien = get_object_or_404(NguoiDung, pk=nguoi_thuc_hien_id)
            task.yeu_cau_phe_duyet = request.POST.get("yeu_cau_phe_duyet") == "on"
            if task.trang_thai == CongViec.TrangThai.HOAN_TRA_LD:
                task.trang_thai = CongViec.TrangThai.CHO_XU_LY
            task.save()

            _replace_task_collaborators(task, nguoi_phoi_hop_ids)

            delete_ids = [item for item in (request.POST.get("delete_files") or "").split(",") if item.strip()]
            if delete_ids:
                original_files = FileCVLienQuan.objects.filter(
                    cong_viec=task,
                    pk__in=delete_ids,
                    nguon_tai_len=FileCVLienQuan.NguonTaiLen.GIAO_VIEC,
                )
                for attachment in original_files:
                    attachment.file_van_ban.delete(save=False)
                    attachment.delete()

            main_files = request.FILES.getlist("file_dinh_kem")
            if main_files:
                for attachment in FileCVLienQuan.objects.filter(
                    cong_viec=task,
                    loai_file=FileCVLienQuan.LoaiFile.CHINH,
                    nguon_tai_len=FileCVLienQuan.NguonTaiLen.GIAO_VIEC,
                ):
                    attachment.file_van_ban.delete(save=False)
                    attachment.delete()

                _create_assignment_files(
                    task,
                    main_files,
                    loai_file=FileCVLienQuan.LoaiFile.CHINH,
                    nguon_tai_len=FileCVLienQuan.NguonTaiLen.GIAO_VIEC,
                    nguoi_tai_len=request.user.core_profile,
                )

            _create_assignment_files(
                task,
                request.FILES.getlist("tai_lieu_lien_quan"),
                loai_file=FileCVLienQuan.LoaiFile.LIEN_QUAN,
                nguon_tai_len=FileCVLienQuan.NguonTaiLen.GIAO_VIEC,
                nguoi_tai_len=request.user.core_profile,
            )

        ghi_lich_su_cong_viec(
            user=request.user, cong_viec=task, hanh_dong="SUA",
        )

        messages.success(request, f"Đã cập nhật công việc '{task.ten_cong_viec}' thành công.")
        if skipped_assignee_collaborator:
            messages.warning(request, "Người phối hợp trùng với người thực hiện chính đã được bỏ qua.")
    except Exception as exc:
        messages.error(request, f"Lỗi khi cập nhật công việc: {exc}")

    return redirect("quanlycongviec:task_detail", task_id=task.pk)


@login_required
@role_required(Customer.Role.CHUYEN_VIEN)
def process_task(request, task_id):
    """
    Chuyên viên gửi kết quả xử lý công việc.
    POST lưu mô tả, file kết quả và chuyển trạng thái chờ duyệt hoặc đã hoàn thành.
    """
    task = _get_task(task_id)

    if not _can_process_task(request, task):
        messages.error(request, "Bạn không có quyền xử lý công việc này.")
        return redirect("quanlycongviec:task_detail", task_id=task.pk)

    if _task_has_result(task):
        messages.info(request, "Công việc này đã có báo cáo xử lý. Hãy dùng chức năng cập nhật xử lý.")
        return redirect("quanlycongviec:update_task_result", task_id=task.pk)

    form = ProcessTaskForm(request.POST or None, request.FILES or None, task=task)

    if request.method == "POST":
        if form.is_valid():
            try:
                with transaction.atomic():
                    task.ket_qua_xu_ly = form.cleaned_data["ket_qua_xu_ly"]
                    task.ghi_chu = form.cleaned_data.get("ghi_chu", "")
                    task.ngay_xu_ly = timezone.now().date()
                    task.trang_thai = (
                        CongViec.TrangThai.CHO_DUYET
                        if task.yeu_cau_phe_duyet
                        else CongViec.TrangThai.DA_HOAN_THANH
                    )
                    task.save()

                    ghi_lich_su_cong_viec(
                        user=request.user, cong_viec=task, hanh_dong="SUA",
                        mo_ta="Xử lý công việc",
                        trang_thai_moi=task.trang_thai,
                    )

                    _create_assignment_files(
                        task,
                        form.get_uploaded_files(),
                        loai_file=FileCVLienQuan.LoaiFile.LIEN_QUAN,
                        nguon_tai_len=FileCVLienQuan.NguonTaiLen.KET_QUA_XU_LY,
                        nguoi_tai_len=request.user.core_profile,
                    )
            except Exception:
                messages.error(request, "Không thể lưu kết quả xử lý")
            else:
                if task.trang_thai == CongViec.TrangThai.CHO_DUYET:
                    messages.success(request, "Lưu xử lý thành công. Công việc đã chuyển sang trạng thái Chờ duyệt.")
                else:
                    messages.success(request, "Lưu xử lý thành công. Công việc đã được hoàn thành.")
                return redirect("quanlycongviec:task_detail", task_id=task.pk)
        else:
            _push_form_errors(request, form)

    context = _build_task_action_context(
        request,
        task,
        form=form,
        template_title="Xử lý công việc",
        submit_label="Lưu xử lý",
    )
    return render(request, "quanlycongviec/xu-ly-cong-viec.html", context)


@login_required
@role_required(Customer.Role.CHUYEN_VIEN)
def update_task_result(request, task_id):
    """
    Chuyên viên cập nhật lại kết quả công việc.
    POST có thể xóa file cũ, thêm file mới và ghi lịch sử.
    """
    task = _get_task(task_id)

    if not _can_process_task(request, task):
        messages.error(request, "Bạn không có quyền cập nhật xử lý công việc này.")
        return redirect("quanlycongviec:task_detail", task_id=task.pk)

    form = UpdateTaskResultForm(
        request.POST or None,
        request.FILES or None,
        task=task,
        initial={
            "ket_qua_xu_ly": task.ket_qua_xu_ly,
            "ghi_chu": task.ghi_chu,
        },
    )

    result_files = _result_files_queryset(task)

    if request.method == "POST":
        if form.is_valid():
            try:
                with transaction.atomic():
                    delete_ids = [
                        item
                        for item in (form.cleaned_data.get("delete_file_ids") or "").split(",")
                        if item.strip()
                    ]
                    if delete_ids:
                        deletable_files = FileCVLienQuan.objects.filter(
                            cong_viec=task,
                            pk__in=delete_ids,
                            nguon_tai_len=FileCVLienQuan.NguonTaiLen.KET_QUA_XU_LY,
                            nguoi_tai_len=request.user.core_profile,
                        )
                        for attachment in deletable_files:
                            attachment.file_van_ban.delete(save=False)
                            attachment.delete()

                    task.ket_qua_xu_ly = form.cleaned_data["ket_qua_xu_ly"]
                    task.ghi_chu = form.cleaned_data.get("ghi_chu", "")
                    task.ngay_xu_ly = timezone.now().date()
                    task.save(update_fields=["ket_qua_xu_ly", "ghi_chu", "ngay_xu_ly", "last_activity"])

                    _create_assignment_files(
                        task,
                        form.get_uploaded_files(),
                        loai_file=FileCVLienQuan.LoaiFile.LIEN_QUAN,
                        nguon_tai_len=FileCVLienQuan.NguonTaiLen.KET_QUA_XU_LY,
                        nguoi_tai_len=request.user.core_profile,
                    )
            except Exception:
                messages.error(request, "Không thể lưu kết quả xử lý")
            else:
                messages.success(request, "Cập nhật báo cáo xử lý thành công")
                return redirect("quanlycongviec:task_detail", task_id=task.pk)
        else:
            _push_form_errors(request, form)

    context = _build_task_action_context(
        request,
        task,
        form=form,
        template_title="Cập nhật báo cáo xử lý công việc",
        submit_label="Lưu cập nhật",
        result_files=result_files,
        can_delete_result_files=True,
    )
    return render(request, "quanlycongviec/cap-nhat-xu-ly-cong-viec.html", context)


@login_required
@role_required(Customer.Role.LANH_DAO, Customer.Role.CHUYEN_VIEN, Customer.Role.ADMIN, Customer.Role.VAN_THU)
def return_task(request, task_id):
    """
    Hoàn trả công việc giữa lãnh đạo và chuyên viên.
    POST lưu lý do hoàn trả, cập nhật trạng thái và ghi lịch sử.
    """
    task = _get_task(task_id)

    if _can_return_to_specialist(request, task):
        return_actor_label = "Chuyên viên nhận lại"
        return_target_name = task.nguoi_thuc_hien.ho_va_ten
        next_status = CongViec.TrangThai.HOAN_TRA_CV
        success_message = "Đã hoàn trả công việc cho chuyên viên."
    elif _can_return_to_leader(request, task):
        return_actor_label = "Lãnh đạo nhận lại"
        return_target_name = task.nguoi_giao.ho_va_ten
        next_status = CongViec.TrangThai.HOAN_TRA_LD
        success_message = "Đã hoàn trả công việc cho lãnh đạo."
    else:
        messages.error(request, "Bạn không có quyền hoàn trả công việc này.")
        return redirect("quanlycongviec:task_detail", task_id=task.pk)

    form = ReturnTaskForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            with transaction.atomic():
                task.trang_thai = next_status
                task.save(update_fields=["trang_thai", "last_activity"])
                HoanTraCongViec.objects.create(
                    cong_viec=task,
                    nguoi_hoan_tra=request.user.core_profile,
                    noi_dung=form.cleaned_data["noi_dung"],
                )
                ghi_lich_su_cong_viec(
                    user=request.user, cong_viec=task, hanh_dong="HOAN_TRA",
                    trang_thai_moi=next_status,
                )
            messages.success(request, success_message)
            return redirect("quanlycongviec:task_detail", task_id=task.pk)

        _push_form_errors(request, form)

    context = {
        "task": task,
        "form": form,
        "receiver_label": return_actor_label,
        "receiver_name": return_target_name,
        "task_list_url": _task_list_route_name(request.user),
    }
    return render(request, "quanlycongviec/hoan-tra-cong-viec.html", context)


@login_required
@role_required(Customer.Role.LANH_DAO, Customer.Role.ADMIN)
def approve_task(request, task_id):
    """
    Lãnh đạo/quản trị duyệt kết quả công việc.
    POST chuyển trạng thái hoàn thành, tạo PheDuyetCongViec và ghi lịch sử.
    """
    task = _get_task(task_id)

    if not _user_is_task_manager(request, task):
        messages.error(request, "Bạn không có quyền duyệt công việc này.")
        return redirect("quanlycongviec:task_detail", task_id=task.pk)

    if task.trang_thai != CongViec.TrangThai.CHO_DUYET:
        messages.error(request, "Chỉ có thể phê duyệt công việc đang ở trạng thái Chờ duyệt.")
        return redirect("quanlycongviec:task_detail", task_id=task.pk)

    task.trang_thai = CongViec.TrangThai.DA_HOAN_THANH
    task.save(update_fields=["trang_thai", "last_activity"])
    PheDuyetCongViec.objects.create(cong_viec=task)
    ghi_lich_su_cong_viec(
        user=request.user, cong_viec=task, hanh_dong="DUYET",
        trang_thai_cu=CongViec.TrangThai.CHO_DUYET,
        trang_thai_moi=CongViec.TrangThai.DA_HOAN_THANH,
    )
    messages.success(request, "Đã duyệt công việc hoàn thành.")
    return redirect("quanlycongviec:task_detail", task_id=task.pk)


@login_required
def get_task_detail(request, task_id):
    # API trả JSON chi tiết công việc cho modal/xử lý nhanh trên frontend.
    task = _get_task(task_id)

    if not _can_view_task(request, task):
        return JsonResponse({"detail": "Forbidden"}, status=403)

    collaborators = PhanCongCongViec.objects.filter(cong_viec=task)
    collab_first = collaborators.first()
    collaborator_ids = [collab.nguoi_phoi_hop_id for collab in collaborators]
    original_files = _original_files_queryset(task)

    attachments = [
        {
            "id": attachment.pk,
            "name": attachment.file_van_ban.name.split("/")[-1],
            "url": attachment.file_van_ban.url,
            "size": f"{attachment.kich_thuoc / 1024:.1f} KB" if attachment.kich_thuoc else "N/A",
            "loai_file": attachment.loai_file,
        }
        for attachment in original_files
    ]

    data = {
        "id": task.cong_viec_id,
        "title": task.ten_cong_viec,
        "content": task.noi_dung_cong_viec,
        "status": task.trang_thai,
        "assigner": task.nguoi_giao.ho_va_ten if task.nguoi_giao else "N/A",
        "assignee": task.nguoi_thuc_hien.ho_va_ten,
        "assignee_id": task.nguoi_thuc_hien.pk,
        "start_date": task.ngay_bat_dau.strftime("%Y-%m-%d"),
        "end_date": task.han_xu_ly.strftime("%Y-%m-%d"),
        "source": task.nguon_giao or "",
        "nguoi_phoi_hop_ids": collaborator_ids,
        "collaborator_id": collab_first.nguoi_phoi_hop.pk if collab_first else "",
        "attachments": attachments,
        "ghi_chu": task.ghi_chu or "",
        "yeu_cau_phe_duyet": task.yeu_cau_phe_duyet,
    }
    return JsonResponse(data)


@login_required
def start_task(request, task_id):
    # Đánh dấu bắt đầu xử lý công việc nếu người dùng có quyền.
    task = _get_task(task_id)
    if not _can_process_task(request, task):
        messages.error(request, "Bạn không có quyền xử lý công việc này.")
        return _redirect_task_list(request)

    if _task_has_result(task):
        return redirect("quanlycongviec:update_task_result", task_id=task.pk)
    return redirect("quanlycongviec:process_task", task_id=task.pk)


def _build_task_action_context(
    request,
    task,
    *,
    form,
    template_title,
    submit_label,
    result_files=None,
    can_delete_result_files=False,
):
    # Gom cờ quyền thao tác để template chi tiết hiển thị nút phù hợp.
    original_files = _original_files_queryset(task)
    context = {
        "task": task,
        "form": form,
        "template_title": template_title,
        "submit_label": submit_label,
        "task_list_url": _task_list_route_name(request.user),
        "main_attachment": original_files.filter(loai_file=FileCVLienQuan.LoaiFile.CHINH).first(),
        "related_files": original_files.filter(loai_file=FileCVLienQuan.LoaiFile.LIEN_QUAN),
        "result_files": result_files or _result_files_queryset(task),
        "can_delete_result_files": can_delete_result_files,
    }
    return context


@login_required
@ensure_csrf_cookie
def task_detail(request, task_id):
    """
    Hiển thị trang chi tiết công việc.
    GET chuẩn bị dữ liệu file, quyền thao tác, lịch sử hoàn trả và form xử lý.
    """
    task = _get_task(task_id)

    if not _can_view_task(request, task):
        messages.error(request, "Bạn không có quyền xem công việc này.")
        return _redirect_task_list(request)

    collaborators = PhanCongCongViec.objects.filter(cong_viec=task)
    original_files = _original_files_queryset(task)
    result_files = _result_files_queryset(task)
    main_attachment = original_files.filter(loai_file=FileCVLienQuan.LoaiFile.CHINH).first()
    related_files = original_files.filter(loai_file=FileCVLienQuan.LoaiFile.LIEN_QUAN)

    history_returns = HoanTraCongViec.objects.filter(cong_viec=task).select_related("nguoi_hoan_tra").order_by(
        "-ngay_hoan_tra",
        "-pk",
    )

    # Kiểm tra điều kiện ký số: lãnh đạo giao việc, task đã xử lý, có file kết quả PDF của chuyên viên
    _can_sign_statuses = {CongViec.TrangThai.CHO_DUYET, CongViec.TrangThai.DA_HOAN_THANH}
    # Lấy file kết quả chuyên viên upload (KET_QUA_XU_LY), uu tiên loại CHINH
    _ket_qua_file_to_sign = (
        FileCVLienQuan.objects.filter(
            cong_viec=task,
            nguon_tai_len=FileCVLienQuan.NguonTaiLen.KET_QUA_XU_LY,
        )
        .order_by(
            # CHINH được xếp trước LIEN_QUAN
            models.Case(
                models.When(loai_file=FileCVLienQuan.LoaiFile.CHINH, then=0),
                default=1,
                output_field=models.IntegerField(),
            )
        )
        .first()
    )
    _has_pdf_result = (
        _ket_qua_file_to_sign is not None
        and _ket_qua_file_to_sign.file_van_ban
        and _ket_qua_file_to_sign.file_van_ban.name.lower().endswith(".pdf")
    )
    can_ky_so = (
        _user_is_task_signer(request, task)
        and task.trang_thai in _can_sign_statuses
        and _has_pdf_result
    )

    # Lịch sử ký số của công việc (nếu có)
    try:
        da_ky_so = LichSuKySo.objects.get(cong_viec=task)
    except LichSuKySo.DoesNotExist:
        da_ky_so = None

    context = {
        "task": task,
        "task_code": f"GV-{task.pk:03d}",
        "collaborators": collaborators,
        "main_attachment": main_attachment,
        "related_files": related_files,
        "result_files": result_files,
        "return_records": history_returns,
        "task_has_result": _task_has_result(task),
        "task_list_url": _task_list_route_name(request.user),
        "can_approve": _user_is_task_manager(request, task) and task.trang_thai == CongViec.TrangThai.CHO_DUYET,
        "can_return": _can_return_to_specialist(request, task) or _can_return_to_leader(request, task),
        "can_process": _can_process_task(request, task) and not _task_has_result(task),
        "can_update_result": _can_process_task(request, task) and _task_has_result(task),
        "can_edit": _user_is_task_manager(request, task)
        and task.trang_thai in {CongViec.TrangThai.CHO_XU_LY, CongViec.TrangThai.HOAN_TRA_LD},
        "can_delete": _user_is_task_manager(request, task) and task.trang_thai == CongViec.TrangThai.CHO_XU_LY,
        "can_ky_so": can_ky_so,
        "da_ky_so": da_ky_so,
        # File kết quả xử lý được dùng để ký số
        "ket_qua_file_to_sign": _ket_qua_file_to_sign,
    }
    return render(request, "quanlycongviec/chi-tiet-cong-viec.html", context)


@require_POST
@login_required
def api_ky_so_cong_viec(request, task_id):
    """
    API ký số công việc.
    POST nhận tọa độ chữ ký, tạo file đã ký/hash và trả JSON cho frontend.
    """
    if not request.user.has_role(Customer.Role.LANH_DAO):
        return JsonResponse({"success": False, "message": "Bạn không có quyền ký số công việc này."}, status=403)

    """Lãnh đạo ký số lên file đính kèm chính của công việc sau khi chuyên viên xử lý xong."""
    import json
    try:
        data = json.loads(request.body)
        x_ratio = float(data.get("x_ratio", 0))
        y_ratio = float(data.get("y_ratio", 0))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"success": False, "message": "Tọa độ không hợp lệ."}, status=400)

    task = _task_queryset().filter(pk=task_id).first()
    if not task:
        return JsonResponse({"success": False, "message": "Không tìm thấy công việc cần ký."}, status=404)
    user = request.user.core_profile

    # Chỉ người giao việc (lãnh đạo) mới được ký
    if not _user_is_task_signer(request, task):
        return JsonResponse({"success": False, "message": "Bạn không phải người giao công việc này."}, status=403)

    # Chỉ ký khi chuyên viên đã xử lý xong (Chờ duyệt hoặc Đã hoàn thành)
    allowed_statuses = {CongViec.TrangThai.CHO_DUYET, CongViec.TrangThai.DA_HOAN_THANH}
    if task.trang_thai not in allowed_statuses:
        return JsonResponse({
            "success": False,
            "message": "Chỉ có thể ký số khi công việc đang ở trạng thái Chờ duyệt hoặc Đã hoàn thành."
        }, status=400)

    # --- Lấy file kết quả chuyên viên đã upload (ưu tiên loại CHINH) ---
    from django.db import models as django_models
    ket_qua_file = (
        FileCVLienQuan.objects.filter(
            cong_viec=task,
            nguon_tai_len=FileCVLienQuan.NguonTaiLen.KET_QUA_XU_LY,
        )
        .order_by(
            django_models.Case(
                django_models.When(loai_file=FileCVLienQuan.LoaiFile.CHINH, then=0),
                default=1,
                output_field=django_models.IntegerField(),
            )
        )
        .first()
    )

    if not ket_qua_file or not ket_qua_file.file_van_ban:
        return JsonResponse(
            {"success": False, "message": "Chuyên viên chưa upload file kết quả xử lý. Không có file nào để ký."},
            status=400
        )

    # Kiểm tra file phải là PDF
    if not ket_qua_file.file_van_ban.name.lower().endswith(".pdf"):
        return JsonResponse({"success": False, "message": "Chỉ hỗ trợ ký số trên file PDF."}, status=400)

    # Lấy thông tin chữ ký số của lãnh đạo
    try:
        chu_ky_so = ChuKySo.objects.get(nguoi_dung=user)
        if not chu_ky_so.anh_chu_ky:
            return JsonResponse({"success": False, "message": "Tài khoản chưa cấu hình ảnh chữ ký."}, status=400)
        signature_image_path = chu_ky_so.anh_chu_ky.path
    except ChuKySo.DoesNotExist:
        return JsonResponse({"success": False, "message": "Tài khoản chưa có thông tin chữ ký số."}, status=400)

    input_pdf_path = ket_qua_file.file_van_ban.path
    if not os.path.exists(input_pdf_path):
        return JsonResponse({"success": False, "message": "Không tìm thấy file PDF kết quả xử lý trên server."}, status=404)
    if not os.path.exists(signature_image_path):
        return JsonResponse({"success": False, "message": "Không tìm thấy file ảnh chữ ký."}, status=404)

    pfx_path = os.path.join(settings.BASE_DIR, 'apps', 'core', 'certs', 'dummy_cert.pfx')
    pfx_password = "123456"

    if not os.path.exists(pfx_path):
        return JsonResponse({"success": False, "message": "Không tìm thấy chứng thư số hệ thống."}, status=500)

    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    output_filename = f"congviec_{task.pk}_signed_{timestamp}.pdf"
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
            pfx_password=pfx_password,
        )
        with open(output_pdf_path, "rb") as f:
            signed_bytes = f.read()

        # --- Ghi đè file kết quả xử lý bằng file đã ký ---
        # Khi bấm vào "File kết quả xử lý" sẽ hiển thị bản đã có chữ ký
        ket_qua_file.file_van_ban.save(
            output_filename,
            ContentFile(signed_bytes),
            save=False,
        )
        ket_qua_file.kich_thuoc = len(signed_bytes)
        ket_qua_file.save(update_fields=["file_van_ban", "kich_thuoc"])

        # Lưu lịch sử ký số
        file_hash = hashlib.sha256(signed_bytes).hexdigest()
        LichSuKySo.objects.update_or_create(
            cong_viec=task,
            defaults={
                'chu_ky_so': chu_ky_so,
                'hash_tai_lieu': file_hash,
                'file_hash': file_hash,
                'file_da_ky': ContentFile(signed_bytes, name=output_filename),
                'van_ban': None,
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Lỗi khi ký số: {str(e)}"}, status=500)
    finally:
        if os.path.exists(output_pdf_path):
            os.remove(output_pdf_path)

    ghi_lich_su_cong_viec(
        user=request.user,
        cong_viec=task,
        hanh_dong="KY_SO",
        mo_ta="Lãnh đạo ký số file đính kèm công việc",
    )

    return JsonResponse({"success": True, "message": "Ký số thành công."})
