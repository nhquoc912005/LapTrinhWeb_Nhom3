from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.timezone import make_aware

from apps.accounts.decorators import role_required
from apps.accounts.models import Customer
from apps.core.models import (
    CongViec,
    FileCVLienQuan,
    HoanTraCongViec,
    NguoiDung,
    PheDuyetCongViec,
    PhanCongCongViec,
    VanBan,
)

from .forms import ProcessTaskForm, ReturnTaskForm, UpdateTaskResultForm


def _task_queryset():
    return CongViec.objects.select_related("nguoi_giao", "nguoi_thuc_hien", "van_ban").prefetch_related(
        "filecvlienquan_set",
        "phancongcongviec_set__nguoi_phoi_hop",
        "hoantracongviec_set__nguoi_hoan_tra",
    )


def _get_task(task_id):
    return get_object_or_404(_task_queryset(), pk=task_id)


def _task_list_route_name(user):
    return "quanlycongviec:xu_ly_cong_viec" if user.is_chuyen_vien else "quanlycongviec:giao_viec"


def _redirect_task_list(request):
    return redirect(_task_list_route_name(request.user))


def _push_form_errors(request, form):
    for error in form.non_field_errors():
        messages.error(request, error)

    for field_name, errors in form.errors.items():
        if field_name == "__all__":
            continue
        for error in errors:
            messages.error(request, error)


def _nguoi_dung_la_lanh_dao(nguoi_dung):
    tai_khoan = getattr(nguoi_dung, "tai_khoan", None)
    if tai_khoan:
        return tai_khoan.role == Customer.Role.LANH_DAO
    return nguoi_dung.chuc_vu == NguoiDung.ChucVu.LANH_DAO


def _user_is_task_manager(request, task):
    return request.user.is_lanh_dao and request.user.core_profile.pk == task.nguoi_giao_id


def _user_is_assignee(request, task):
    return request.user.is_chuyen_vien and request.user.core_profile.pk == task.nguoi_thuc_hien_id


def _task_has_result(task):
    return bool(task.ket_qua_xu_ly) or FileCVLienQuan.objects.filter(
        cong_viec=task,
        nguon_tai_len=FileCVLienQuan.NguonTaiLen.KET_QUA_XU_LY,
    ).exists()


def _can_view_task(request, task):
    if request.user.has_role(Customer.Role.ADMIN, Customer.Role.VAN_THU):
        return True
    user_core_id = request.user.core_profile.pk
    return user_core_id in {task.nguoi_giao_id, task.nguoi_thuc_hien_id}


def _can_process_task(request, task):
    return _user_is_assignee(request, task) and task.cho_phep_chuyen_vien_xu_ly


def _can_return_to_leader(request, task):
    return (
        _user_is_assignee(request, task)
        and task.trang_thai in {CongViec.TrangThai.CHO_XU_LY, CongViec.TrangThai.HOAN_TRA_CV}
        and _nguoi_dung_la_lanh_dao(task.nguoi_giao)
    )


def _can_return_to_specialist(request, task):
    return _user_is_task_manager(request, task) and task.trang_thai == CongViec.TrangThai.CHO_DUYET


def _parse_task_dates(ngay_bat_dau_str, han_xu_ly_str):
    ngay_bat_dau = datetime.strptime(ngay_bat_dau_str, "%Y-%m-%d").date()
    naive_han_xu_ly = datetime.strptime(han_xu_ly_str, "%Y-%m-%d").replace(
        hour=23,
        minute=59,
        second=59,
    )
    return ngay_bat_dau, make_aware(naive_han_xu_ly)


def _validate_task_dates(ngay_bat_dau, han_xu_ly, *, allow_past_start=False):
    today = timezone.now().date()
    if not allow_past_start and ngay_bat_dau < today:
        return "Ngày bắt đầu không được nhỏ hơn ngày hiện tại."
    if han_xu_ly.date() < today:
        return "Hạn xử lý không được nhỏ hơn ngày hiện tại."
    if han_xu_ly.date() < ngay_bat_dau:
        return "Hạn xử lý không được nhỏ hơn ngày bắt đầu."
    return ""


def _create_assignment_files(task, files, *, loai_file, nguon_tai_len, nguoi_tai_len):
    for uploaded_file in files:
        FileCVLienQuan.objects.create(
            cong_viec=task,
            file_van_ban=uploaded_file,
            kich_thuoc=uploaded_file.size,
            loai_file=loai_file,
            nguon_tai_len=nguon_tai_len,
            nguoi_tai_len=nguoi_tai_len,
        )


def _result_files_queryset(task):
    return FileCVLienQuan.objects.filter(
        cong_viec=task,
        nguon_tai_len=FileCVLienQuan.NguonTaiLen.KET_QUA_XU_LY,
    ).select_related("nguoi_tai_len")


def _original_files_queryset(task):
    return FileCVLienQuan.objects.filter(
        cong_viec=task,
        nguon_tai_len=FileCVLienQuan.NguonTaiLen.GIAO_VIEC,
    )


@login_required
@role_required(Customer.Role.LANH_DAO, Customer.Role.VAN_THU, Customer.Role.ADMIN)
def giao_viec(request):
    tasks = _task_queryset().order_by("-last_activity")

    if request.user.is_lanh_dao:
        tasks = tasks.filter(nguoi_giao=request.user.core_profile)

    context = {
        "tasks": tasks,
        "chuyen_vien_list": NguoiDung.objects.filter(chuc_vu=NguoiDung.ChucVu.CHUYEN_VIEN),
        "all_users": NguoiDung.objects.all(),
        "van_ban_list": VanBan.objects.all().order_by("-ngay_den"),
        "is_lanh_dao": request.user.is_lanh_dao,
        "status_choices": CongViec.TrangThai.choices,
    }
    return render(request, "quanlycongviec/giao-viec.html", context)


@login_required
@role_required(Customer.Role.CHUYEN_VIEN)
def xu_ly_cong_viec(request):
    tasks = _task_queryset().filter(nguoi_thuc_hien=request.user.core_profile).order_by("-last_activity")
    context = {
        "tasks": tasks,
        "status_choices": CongViec.TrangThai.choices,
    }
    return render(request, "quanlycongviec/cong-viec-cua-toi.html", context)


@login_required
@role_required(Customer.Role.LANH_DAO)
def add_task(request):
    if request.method != "POST":
        return redirect("quanlycongviec:giao_viec")

    try:
        ten_cv = (request.POST.get("ten_cv") or "").strip()
        nguoi_thuc_hien_id = request.POST.get("nguoi_thuc_hien")
        nguoi_phoi_hop_id = request.POST.get("nguoi_phoi_hop")
        nguon_giao = request.POST.get("nguon_giao")
        ngay_bat_dau_str = request.POST.get("ngay_bat_dau")
        han_xu_ly_str = request.POST.get("han_xu_ly")
        noi_dung = (request.POST.get("noi_dung") or "").strip()
        ghi_chu = (request.POST.get("ghi_chu") or "").strip()
        yeu_cau_phe_duyet = request.POST.get("yeu_cau_phe_duyet") == "on"

        if not all([ten_cv, nguoi_thuc_hien_id, ngay_bat_dau_str, han_xu_ly_str, noi_dung]):
            messages.error(request, "Vui lòng nhập đầy đủ các trường bắt buộc.")
            return redirect("quanlycongviec:giao_viec")

        nguoi_thuc_hien = get_object_or_404(NguoiDung, pk=nguoi_thuc_hien_id)

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

            PhanCongCongViec.objects.filter(cong_viec=task).delete()
            if nguoi_phoi_hop_id:
                nguoi_phoi_hop = get_object_or_404(NguoiDung, pk=nguoi_phoi_hop_id)
                PhanCongCongViec.objects.create(cong_viec=task, nguoi_phoi_hop=nguoi_phoi_hop)

        messages.success(request, f"Đã giao việc '{ten_cv}' thành công.")
    except Exception as exc:
        messages.error(request, f"Lỗi hệ thống khi giao việc: {exc}")

    return redirect("quanlycongviec:giao_viec")


@login_required
@role_required(Customer.Role.LANH_DAO)
def delete_task(request, task_id):
    task = _get_task(task_id)

    if not _user_is_task_manager(request, task):
        messages.error(request, "Bạn không có quyền xóa công việc này.")
        return redirect("quanlycongviec:task_detail", task_id=task.pk)

    if task.trang_thai != CongViec.TrangThai.CHO_XU_LY:
        messages.error(request, "Chỉ có thể xóa công việc ở trạng thái Chờ xử lý.")
        return redirect("quanlycongviec:task_detail", task_id=task.pk)

    task.delete()
    messages.success(request, "Đã xóa công việc.")
    return redirect("quanlycongviec:giao_viec")


@login_required
@role_required(Customer.Role.LANH_DAO)
def edit_task(request, task_id):
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
        nguoi_phoi_hop_id = request.POST.get("nguoi_phoi_hop")

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

            PhanCongCongViec.objects.filter(cong_viec=task).delete()
            if nguoi_phoi_hop_id:
                nguoi_phoi_hop = get_object_or_404(NguoiDung, pk=nguoi_phoi_hop_id)
                PhanCongCongViec.objects.create(cong_viec=task, nguoi_phoi_hop=nguoi_phoi_hop)

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

        messages.success(request, f"Đã cập nhật công việc '{task.ten_cong_viec}' thành công.")
    except Exception as exc:
        messages.error(request, f"Lỗi khi cập nhật công việc: {exc}")

    return redirect("quanlycongviec:task_detail", task_id=task.pk)


@login_required
@role_required(Customer.Role.CHUYEN_VIEN)
def process_task(request, task_id):
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
    messages.success(request, "Đã duyệt công việc hoàn thành.")
    return redirect("quanlycongviec:task_detail", task_id=task.pk)


@login_required
def get_task_detail(request, task_id):
    task = _get_task(task_id)

    if not _user_is_task_manager(request, task):
        return JsonResponse({"detail": "Forbidden"}, status=403)

    collaborators = PhanCongCongViec.objects.filter(cong_viec=task)
    collab_first = collaborators.first()
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
        "collaborator_id": collab_first.nguoi_phoi_hop.pk if collab_first else "",
        "attachments": attachments,
        "ghi_chu": task.ghi_chu or "",
        "yeu_cau_phe_duyet": task.yeu_cau_phe_duyet,
    }
    return JsonResponse(data)


@login_required
def start_task(request, task_id):
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
def task_detail(request, task_id):
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
    }
    return render(request, "quanlycongviec/chi-tiet-cong-viec.html", context)
