from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission


def get_role_permissions(user_model=None):
    User = user_model or get_user_model()
    return {
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


def ensure_role_groups(user_model=None):
    role_permissions = get_role_permissions(user_model)
    groups = {}

    for role_name, permission_codenames in role_permissions.items():
        group, _ = Group.objects.get_or_create(name=role_name)
        permissions = Permission.objects.filter(codename__in=permission_codenames)
        group.permissions.set(permissions)
        groups[role_name] = group

    return groups


def sync_user_role_group(user, role_groups=None):
    role_groups = role_groups or ensure_role_groups(user.__class__)
    role_names = list(role_groups.keys())
    preserved_groups = list(user.groups.exclude(name__in=role_names))
    target_group = role_groups.get(getattr(user, "role", None))

    if target_group:
        user.groups.set([*preserved_groups, target_group])
    else:
        user.groups.set(preserved_groups)

    return target_group
