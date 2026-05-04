from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied


# File này gom logic kiểm tra role để dùng lại cho view function và class-based view.


def user_has_role(user, *allowed_roles):
    # Trả về True nếu user đã đăng nhập và có một trong các vai trò được phép.
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return getattr(user, "role", None) in allowed_roles


def role_required(*allowed_roles):
    # Decorator dùng trên view để chặn người không đúng vai trò trước khi vào xử lý.
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not user_has_role(request.user, *allowed_roles):
                raise PermissionDenied("Ban khong co quyen truy cap chuc nang nay.")
            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator


class RoleRequiredMixin(AccessMixin):
    # Mixin tương đương role_required dành cho class-based view nếu cần mở rộng sau này.
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not user_has_role(request.user, *self.allowed_roles):
            raise PermissionDenied("Ban khong co quyen truy cap chuc nang nay.")
        return super().dispatch(request, *args, **kwargs)
