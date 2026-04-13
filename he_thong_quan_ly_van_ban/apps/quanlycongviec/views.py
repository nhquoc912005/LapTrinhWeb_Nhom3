from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.utils.timezone import make_aware
from apps.accounts.decorators import role_required
from apps.accounts.models import Customer
from apps.core.models import CongViec, NguoiDung, HoanTraCongViec, PheDuyetCongViec, VanBan, PhanCongCongViec, FileCVLienQuan
import json
from datetime import datetime

@login_required
@role_required(Customer.Role.LANH_DAO, Customer.Role.VAN_THU, Customer.Role.CHUYEN_VIEN, Customer.Role.ADMIN)
def giao_viec(request):
    """
    Trang Quản lý công việc chung (Tất cả các role đều xem được tất cả công việc)
    """
    user_core = request.user.core_profile
    is_lanh_dao = request.user.is_lanh_dao
    is_van_thu = request.user.is_van_thu
    
    # Hiển thị tất cả công việc cho tất cả các role, ưu tiên hoạt động mới nhất
    tasks = CongViec.objects.all().order_by('-last_activity')
    
    # Lấy danh sách chuyên viên và tất cả người dùng
    chuyen_vien_list = NguoiDung.objects.filter(chuc_vu=NguoiDung.ChucVu.CHUYEN_VIEN)
    all_users = NguoiDung.objects.all()

    # Lấy danh sách văn bản để liên quan
    van_ban_list = VanBan.objects.all().order_by('-ngay_den')
    
    context = {
        'tasks': tasks,
        'chuyen_vien_list': chuyen_vien_list,
        'all_users': all_users,
        'van_ban_list': van_ban_list,
        'is_lanh_dao': is_lanh_dao,
    }
    return render(request, "quanlycongviec/giao-viec.html", context)

@login_required
@role_required(Customer.Role.CHUYEN_VIEN)
def xu_ly_cong_viec(request):
    """
    Trang dành riêng cho Chuyên viên để xử lý công việc (Hiển thị tất cả công việc)
    """
    user_core = request.user.core_profile
    # Hiển thị tất cả công việc, ưu tiên hoạt động mới nhất
    tasks = CongViec.objects.all().order_by('-last_activity')
    
    context = {
        'tasks': tasks,
    }
    return render(request, "quanlycongviec/xu-ly-cong-viec.html", context)

@login_required
@role_required(Customer.Role.LANH_DAO)
def add_task(request):
    if request.method == "POST":
        try:
            ten_cv = request.POST.get('ten_cv')
            nguoi_thuc_hien_id = request.POST.get('nguoi_thuc_hien')
            nguoi_phoi_hop_id = request.POST.get('nguoi_phoi_hop')
            nguon_giao = request.POST.get('nguon_giao')
            ngay_bat_dau_str = request.POST.get('ngay_bat_dau')
            han_xu_ly_str = request.POST.get('han_xu_ly')
            noi_dung = request.POST.get('noi_dung')
            ghi_chu = request.POST.get('ghi_chu')
            
            if not all([ten_cv, nguoi_thuc_hien_id, ngay_bat_dau_str, han_xu_ly_str]):
                messages.error(request, "Vui lòng nhập đầy đủ các trường bắt buộc.")
                return redirect('quanlycongviec:giao_viec')

            nguoi_thuc_hien = get_object_or_404(NguoiDung, pk=nguoi_thuc_hien_id)
            
            # Xử lý định dạng ngày tháng
            try:
                naive_han_xu_ly = datetime.strptime(han_xu_ly_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                han_xu_ly = make_aware(naive_han_xu_ly)
                ngay_bat_dau = datetime.strptime(ngay_bat_dau_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, "Định dạng ngày tháng không hợp lệ.")
                return redirect('quanlycongviec:giao_viec')

            # Kiểm tra ngày bắt đầu không được trong quá khứ
            today = timezone.now().date()
            if ngay_bat_dau < today:
                messages.error(request, "Ngày bắt đầu không được nhỏ hơn ngày hiện tại.")
                return redirect('quanlycongviec:giao_viec')
            
            if han_xu_ly.date() < today:
                messages.error(request, "Hạn xử lý không được nhỏ hơn ngày hiện tại.")
                return redirect('quanlycongviec:giao_viec')
                
            if han_xu_ly.date() < ngay_bat_dau:
                messages.error(request, "Hạn xử lý không được nhỏ hơn ngày bắt đầu.")
                return redirect('quanlycongviec:giao_viec')

            # Tạo công việc
            task = CongViec.objects.create(
                ten_cong_viec=ten_cv,
                noi_dung_cong_viec=noi_dung,
                nguoi_giao=request.user.core_profile,
                nguoi_thuc_hien=nguoi_thuc_hien,
                nguon_giao=nguon_giao,
                trang_thai="Chờ xử lý",
                ngay_bat_dau=ngay_bat_dau,
                han_xu_ly=han_xu_ly,
                ghi_chu=ghi_chu
            )

            # Xử lý file đính kèm chính
            main_files = request.FILES.getlist('file_dinh_kem')
            for f in main_files:
                # Mặc dù input không có multiple, getlist/for loop vẫn an toàn
                FileCVLienQuan.objects.create(cong_viec=task, file_van_ban=f, kich_thuoc=f.size, loai_file='CHINH')
            
            # Xử lý tài liệu liên quan
            ref_files = request.FILES.getlist('tai_lieu_lien_quan')
            for f in ref_files:
                FileCVLienQuan.objects.create(cong_viec=task, file_van_ban=f, kich_thuoc=f.size, loai_file='LIEN_QUAN')

            # Người phối hợp
            if nguoi_phoi_hop_id:
                try:
                    nguoi_phoi_hop = NguoiDung.objects.get(pk=nguoi_phoi_hop_id)
                    PhanCongCongViec.objects.create(cong_viec=task, nguoi_phoi_hop=nguoi_phoi_hop)
                except NguoiDung.DoesNotExist:
                    pass

            messages.success(request, f"Đã giao việc '{ten_cv}' thành công.")
        except Exception as e:
            messages.error(request, f"Lỗi hệ thống khi giao việc: {str(e)}")
            
    return redirect('quanlycongviec:giao_viec')

@login_required
@role_required(Customer.Role.LANH_DAO)
def delete_task(request, task_id):
    task = get_object_or_404(CongViec, pk=task_id)
    if task.trang_thai != "Chờ xử lý":
        messages.error(request, "Chỉ có thể xóa công việc ở trạng thái Chờ xử lý.")
        return redirect('quanlycongviec:giao_viec')
        
    task.delete()
    messages.success(request, "Đã xóa công việc.")
    return redirect('quanlycongviec:giao_viec')

@login_required
@role_required(Customer.Role.LANH_DAO)
def edit_task(request, task_id):
    task = get_object_or_404(CongViec, pk=task_id)
    
    if task.trang_thai not in ["Chờ xử lý", "Hoàn trả"]:
        messages.error(request, "Công việc này hiện không thể chỉnh sửa (chỉ cho phép chỉnh sửa ở trạng thái Chờ xử lý hoặc Hoàn trả).")
        return redirect('quanlycongviec:task_detail', task_id=task.pk)

    if request.method == "POST":
        try:
            task.ten_cong_viec = request.POST.get('ten_cv')
            task.nguon_giao = request.POST.get('nguon_giao')
            task.noi_dung_cong_viec = request.POST.get('noi_dung')
            task.ghi_chu = request.POST.get('ghi_chu')
            
            nguoi_thuc_hien_id = request.POST.get('nguoi_thuc_hien')
            nguoi_phoi_hop_id = request.POST.get('nguoi_phoi_hop')
            ngay_bat_dau_str = request.POST.get('ngay_bat_dau')
            han_xu_ly_str = request.POST.get('han_xu_ly')

            if nguoi_thuc_hien_id:
                task.nguoi_thuc_hien = get_object_or_404(NguoiDung, pk=nguoi_thuc_hien_id)
            if ngay_bat_dau_str:
                task.ngay_bat_dau = datetime.strptime(ngay_bat_dau_str, '%Y-%m-%d').date()
            if han_xu_ly_str:
                naive_han_xu_ly = datetime.strptime(han_xu_ly_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                task.han_xu_ly = make_aware(naive_han_xu_ly)

            # Khi chỉnh sửa, không bắt buộc ngày bắt đầu phải >= hôm nay 
            # (vì công việc có thể đã bắt đầu từ trước đó)
            # Chỉ cần đảm bảo logic: Hạn xử lý >= Ngày bắt đầu
            
            today = timezone.now().date()
            if task.han_xu_ly.date() < today:
                messages.error(request, "Hạn xử lý không được nhỏ hơn ngày hiện tại.")
                return redirect('quanlycongviec:giao_viec')

            if task.han_xu_ly.date() < task.ngay_bat_dau:
                messages.error(request, "Hạn xử lý không được nhỏ hơn ngày bắt đầu.")
                return redirect('quanlycongviec:giao_viec')

            task.save()
            
            # Cập nhật người phối hợp
            PhanCongCongViec.objects.filter(cong_viec=task).delete()
            if nguoi_phoi_hop_id:
                nguoi_phoi_hop = get_object_or_404(NguoiDung, pk=nguoi_phoi_hop_id)
                PhanCongCongViec.objects.create(cong_viec=task, nguoi_phoi_hop=nguoi_phoi_hop)

            # Xử lý xóa file cũ theo đánh dấu từ UI
            deleted_ids = request.POST.get('delete_files', '').split(',')
            for fid in deleted_ids:
                if fid.strip():
                    try:
                        FileCVLienQuan.objects.filter(pk=fid, cong_viec=task).delete()
                    except (ValueError, FileCVLienQuan.DoesNotExist):
                        pass

            # Xử lý file đính kèm chính (Thay thế nếu có file mới)
            main_files = request.FILES.getlist('file_dinh_kem')
            if main_files:
                # Xóa file chính cũ trước khi lưu file mới (Đảm bảo chỉ có 1)
                FileCVLienQuan.objects.filter(cong_viec=task, loai_file='CHINH').delete()
                for f in main_files:
                    FileCVLienQuan.objects.create(cong_viec=task, file_van_ban=f, kich_thuoc=f.size, loai_file='CHINH')

            # Xử lý tài liệu liên quan (Thêm mới)
            ref_files = request.FILES.getlist('tai_lieu_lien_quan')
            for f in ref_files:
                FileCVLienQuan.objects.create(cong_viec=task, file_van_ban=f, kich_thuoc=f.size, loai_file='LIEN_QUAN')

            messages.success(request, f"Đã cập nhật công việc '{task.ten_cong_viec}' thành công.")
            return redirect('quanlycongviec:task_detail', task_id=task.pk)
        except Exception as e:
            messages.error(request, f"Lỗi khi cập nhật công việc: {str(e)}")
            
    return redirect('quanlycongviec:giao_viec')

@login_required
def update_progress(request, task_id):
    task = get_object_or_404(CongViec, pk=task_id)
    if request.method == "POST":
        ket_qua = request.POST.get('ket_qua')
        task.ket_qua_xu_ly = ket_qua
        task.trang_thai = "Chờ duyệt"
        task.ngay_xu_ly = timezone.now()
        task.save()
        messages.success(request, "Đã gửi kết quả xử lý. Đang chờ lãnh đạo duyệt.")
    return redirect('quanlycongviec:xu_ly_cong_viec')

@login_required
def approve_task(request, task_id):
    if not request.user.is_lanh_dao:
        messages.error(request, "Bạn không có quyền duyệt công việc.")
        return redirect('core:dashboard')
    task = get_object_or_404(CongViec, pk=task_id)
    task.trang_thai = "Đã hoàn thành"
    task.save()
    PheDuyetCongViec.objects.create(cong_viec=task)
    messages.success(request, "Đã duyệt công việc hoàn thành.")
    return redirect('quanlycongviec:giao_viec')

@login_required
def return_task(request, task_id):
    task = get_object_or_404(CongViec, pk=task_id)
    if request.method == "POST":
        noi_dung = request.POST.get('noi_dung')
        task.trang_thai = "Hoàn trả"
        task.save()
        HoanTraCongViec.objects.create(cong_viec=task, noi_dung=noi_dung)
        messages.warning(request, "Đã hoàn trả công việc.")
        if request.user.is_chuyen_vien:
            return redirect('quanlycongviec:xu_ly_cong_viec')
        return redirect('quanlycongviec:giao_viec')
    
    # Handle GET
    context = {
        'task': task,
    }
    return render(request, "quanlycongviec/hoan-tra-cong-viec.html", context)

@login_required
def get_task_detail(request, task_id):
    task = get_object_or_404(CongViec, pk=task_id)
    collaborators = PhanCongCongViec.objects.filter(cong_viec=task)
    collab_list = [c.nguoi_phoi_hop.ho_va_ten for c in collaborators]
    collab_first = collaborators.first()
    
    attachments = FileCVLienQuan.objects.filter(cong_viec=task)
    file_list = []
    for f in attachments:
        file_list.append({
            'id': f.pk,
            'name': f.file_van_ban.name.split('/')[-1],
            'url': f.file_van_ban.url,
            'size': f"{f.kich_thuoc / 1024:.1f} KB" if f.kich_thuoc else "N/A",
            'loai_file': f.loai_file
        })

    data = {
        'id': task.cong_viec_id,
        'title': task.ten_cong_viec,
        'content': task.noi_dung_cong_viec,
        'status': task.trang_thai,
        'assigner': task.nguoi_giao.ho_va_ten if task.nguoi_giao else "N/A",
        'assignee': task.nguoi_thuc_hien.ho_va_ten,
        'assignee_id': task.nguoi_thuc_hien.pk,
        'start_date': task.ngay_bat_dau.strftime('%Y-%m-%d'),
        'end_date': task.han_xu_ly.strftime('%Y-%m-%d'),
        'source': task.nguon_giao or "",
        'collaborator_id': collab_first.nguoi_phoi_hop.pk if collab_first else "",
        'collaborators': collab_list,
        'attachments': file_list,
        'ghi_chu': task.ghi_chu or "",
        'can_approve': request.user.is_lanh_dao and task.trang_thai == "Chờ duyệt",
        'can_delete': request.user.is_lanh_dao and task.trang_thai == "Chờ xử lý",
        'can_edit': request.user.is_lanh_dao,
    }
    return JsonResponse(data)

@login_required
def start_task(request, task_id):
    task = get_object_or_404(CongViec, pk=task_id)
    # Cho phép bất kỳ chuyên viên nào cũng có thể nhận việc (Pick up)
    if not request.user.is_chuyen_vien:
        messages.error(request, "Bạn không có quyền thực hiện công việc này.")
        return redirect('quanlycongviec:xu_ly_cong_viec')
    
    # Nếu người thực hiện hiện tại khác với người đang click, cập nhật lại người thực hiện
    if task.nguoi_thuc_hien != request.user.core_profile:
        task.nguoi_thuc_hien = request.user.core_profile
        messages.info(request, f"Bạn đã tiếp nhận công việc này từ {task.nguoi_thuc_hien.ho_va_ten if task.nguoi_thuc_hien else 'người khác'}.")
    else:
        messages.info(request, "Đã tiếp nhận công việc. Bắt đầu xử lý.")
        
    # task.trang_thai = "Đang xử lý" # Removed
    task.save()
    return redirect('quanlycongviec:task_detail', task_id=task.pk)

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(CongViec, pk=task_id)
    collaborators = PhanCongCongViec.objects.filter(cong_viec=task)
    
    # Tách biệt file chính và tài liệu liên quan
    main_attachment = FileCVLienQuan.objects.filter(cong_viec=task, loai_file='CHINH').first()
    related_files = FileCVLienQuan.objects.filter(cong_viec=task, loai_file='LIEN_QUAN')
    
    attachments = FileCVLienQuan.objects.filter(cong_viec=task)
    task_code = f"GV-{task.pk:03d}"
    
    first_pdf = None
    # Ưu tiên xem trước file chính nếu là PDF
    if main_attachment and main_attachment.file_van_ban.name.lower().endswith('.pdf'):
        first_pdf = main_attachment
    else:
        for att in attachments:
            if att.file_van_ban.name.lower().endswith('.pdf'):
                first_pdf = att
                break

    context = {
        'task': task,
        'task_code': task_code,
        'collaborators': collaborators,
        'main_attachment': main_attachment,
        'related_files': related_files,
        'attachments': attachments,
        'first_pdf': first_pdf,
        'can_approve': request.user.is_lanh_dao and task.trang_thai == "Chờ duyệt",
        'can_return': (request.user.is_lanh_dao and task.trang_thai in ["Chờ duyệt", "Hoàn trả"]) or \
                      (request.user.is_chuyen_vien and task.trang_thai in ["Chờ xử lý", "Hoàn trả"]),
        'can_start': request.user.is_chuyen_vien and task.trang_thai in ["Chờ xử lý", "Hoàn trả"],
        'can_edit': request.user.is_lanh_dao and task.trang_thai in ["Chờ xử lý", "Hoàn trả"],
        'can_delete': request.user.is_lanh_dao and task.trang_thai in ["Chờ xử lý", "Hoàn trả"],
    }
    return render(request, "quanlycongviec/chi-tiet-cong-viec.html", context)
