from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def _build_user_initials(user):
    source = (getattr(user, "ho_va_ten", "") or user.get_full_name() or user.username).strip()
    parts = [part for part in source.split() if part]

    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[-1][0]}".upper()
    if parts:
        return parts[0][:2].upper()
    return user.username[:2].upper()


@login_required
def dashboard(request):
    return render(
        request,
        "dashboard.html",
        {
            "user_display_name": request.user.ho_va_ten or request.user.username,
            "user_role_display": request.user.get_role_display(),
            "user_initials": _build_user_initials(request.user),
        },
    )
