from django.urls import path
from .views import (
    giao_viec, xu_ly_cong_viec, add_task, edit_task,
    delete_task, update_progress, approve_task, return_task, get_task_detail,
    task_detail, start_task
)

app_name = "quanlycongviec"

urlpatterns = [
    path("giao-viec.html", giao_viec, name="giao_viec"),
    path("xu-ly-cong-viec.html", xu_ly_cong_viec, name="xu_ly_cong_viec"),
    path("add/", add_task, name="add_task"),
    path("edit/<int:task_id>/", edit_task, name="edit_task"),
    path("delete/<int:task_id>/", delete_task, name="delete_task"),
    path("update-progress/<int:task_id>/", update_progress, name="update_progress"),
    path("approve/<int:task_id>/", approve_task, name="approve_task"),
    path("return/<int:task_id>/", return_task, name="return_task"),
    path("api/task/<int:task_id>/", get_task_detail, name="get_task_detail"),
    path("task/<int:task_id>/", task_detail, name="task_detail"),
    path("start/<int:task_id>/", start_task, name="start_task"),
]
