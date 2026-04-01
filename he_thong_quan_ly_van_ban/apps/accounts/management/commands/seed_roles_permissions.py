from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group,Permission
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Tạo group và gán quyền cho hệ thống"

    def handle(self, *args, **options):
        User = get_user_model()
        role_permissions = {
            User.Role.ADMIN: [
                "access_admin_area",
                "manage_users",
                "manage_departments",
                "view_reports",
                "add_customer",
                "change_customer",
                "delete_customer",
                "view_customer",
            ],
            User.Role.LANH_DAO: [
                "access_lanh_dao_area",
                "view_reports",
                "forward_document",
                "approve_outgoing_document",
                "return_outgoing_document",
                "assign_task",
                "edit_task",
                "delete_task",
                "approve_task",
                "return_task",
                "manage_records",
                "add_document_to_record",
            ],
            User.Role.VAN_THU: [
                "access_van_thu_area",
                "present_incoming_document",
                "edit_incoming_document",
                "delete_incoming_document",
                "issue_outgoing_document",
                "manage_records",
                "add_document_to_record",
                "remove_document_from_record",
            ],
            User.Role.CHUYEN_VIEN: [
                "access_chuyen_vien_area",
                "draft_outgoing_document",
                "edit_outgoing_document",
                "delete_outgoing_document",
                "process_task",
                "update_task_result",
                "manage_records",
                "add_document_to_record",
                "remove_document_from_record",
            ],
        }
        for role_name,permission_codenames in role_permissions.items():
            group, _ = Group.objects.get_or_create(name=role_name)

            permission = Permission.objects.filter(codename__in=permission_codenames)
            group.permissions.set(permission)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Đã tạo/cập nhật group '{role_name}' với {permission.count()} quyền."
                )
            )
        #Đồng bộ các group cho các
        for user in User.objects.all():
            if user.role:
                group = Group.objects.filter(name=user.role).first()
                if group:
                    user.groups.clear()
                    user.groups.add(group)
        self.stdout.write(self.style.SUCCESS("Hoàn tất seed group và quyền."))