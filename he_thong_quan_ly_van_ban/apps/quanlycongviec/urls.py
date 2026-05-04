from django.urls import path
from .views import (
    add_task,
    api_ky_so_cong_viec,
    approve_task,
    delete_task,
    edit_task,
    giao_viec,
    get_task_detail,
    process_task,
    return_task,
    start_task,
    task_detail,
    update_task_result,
    xu_ly_cong_viec,
)

app_name = "quanlycongviec"

# URL quản lý công việc: giao việc, xử lý, duyệt, hoàn trả, chi tiết và ký số.
urlpatterns = [
    # Màn danh sách theo vai trò lãnh đạo/chuyên viên.
    path("giao-viec.html", giao_viec, name="giao_viec"),
    path("xu-ly-cong-viec.html", xu_ly_cong_viec, name="xu_ly_cong_viec"),
    # CRUD công việc do lãnh đạo/quản trị thao tác.
    path("add/", add_task, name="add_task"),
    path("edit/<int:task_id>/", edit_task, name="edit_task"),
    path("delete/<int:task_id>/", delete_task, name="delete_task"),
    # Luồng chuyên viên xử lý/cập nhật kết quả và lãnh đạo duyệt/hoàn trả.
    path("task/<int:task_id>/xu-ly/", process_task, name="process_task"),
    path("task/<int:task_id>/cap-nhat-xu-ly/", update_task_result, name="update_task_result"),
    path("update-progress/<int:task_id>/", process_task, name="update_progress"),
    path("task/<int:task_id>/approve/", approve_task, name="approve_task"),
    path("task/<int:task_id>/hoan-tra/", return_task, name="return_task"),
    # API và trang chi tiết công việc.
    path("api/task/<int:task_id>/", get_task_detail, name="get_task_detail"),
    path("task/<int:task_id>/", task_detail, name="task_detail"),
    path("start/<int:task_id>/", start_task, name="start_task"),
    # API ký số công việc.
    path("task/<int:task_id>/ky-so/", api_ky_so_cong_viec, name="api_ky_so_cong_viec"),
]
