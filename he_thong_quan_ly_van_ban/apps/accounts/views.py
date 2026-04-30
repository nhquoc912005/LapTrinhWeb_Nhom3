from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from apps.core.utils.digital_signature import verify_signed_file

from .forms import CustomerLoginForm


def _get_safe_redirect_url(request):
    redirect_to = request.POST.get("next") or request.GET.get("next")
    if redirect_to and url_has_allowed_host_and_scheme(
        redirect_to,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect_to
    return settings.LOGIN_REDIRECT_URL


@require_http_methods(["GET", "POST"])
@never_cache
@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        return redirect(_get_safe_redirect_url(request))

    form = CustomerLoginForm(request=request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        user.sync_access_context()
        login(request, user)
        return redirect(_get_safe_redirect_url(request))

    next_url = request.POST.get("next") or request.GET.get("next") or ""
    return render(request, "core/index.html", {"form": form, "next_url": next_url})


@login_required
@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)


@login_required
def profile_view(request):
    user = request.user
    core_profile = user.sync_access_context()

    from apps.core.models import ChuKySo, CongViec, HoSoVanBan, LichSuKySo, VanBan
    from apps.quanlyvanbanden.models import VanBanDen

    outgoing = VanBan.objects.filter(phan_loai=VanBan.PHAN_LOAI_CHOICES[0][0])
    if user.is_van_thu:
        outgoing = outgoing.filter(
            trang_thai__in=[
                VanBan.TRANG_THAI_CHOICES[3][0],
                VanBan.TRANG_THAI_CHOICES[4][0],
                VanBan.TRANG_THAI_CHOICES[5][0],
            ]
        )
    elif user.is_chuyen_vien:
        outgoing = outgoing.filter(nguoi_tao=core_profile)
    elif user.is_lanh_dao:
        outgoing = outgoing.filter(lanh_dao_duyet=core_profile)

    incoming = VanBan.objects.filter(phan_loai=VanBan.PHAN_LOAI_CHOICES[1][0])
    if user.is_lanh_dao:
        incoming = incoming.filter(lanh_dao_duyet=core_profile)
    elif user.is_chuyen_vien:
        incoming = incoming.filter(
            vanbanduyet__chuyentiep__chuyentiepchitiet__nguoi_dung=core_profile
        ).distinct()

    tasks = CongViec.objects.all()
    if user.is_lanh_dao:
        tasks = tasks.filter(nguoi_giao=core_profile)
    elif user.is_chuyen_vien:
        tasks = tasks.filter(nguoi_thuc_hien=core_profile)

    records = HoSoVanBan.objects.filter(
        Q(nguoi_tao=core_profile)
        | Q(nguoixulyhoso__nguoi_xu_ly=core_profile)
        | Q(phongxemhoso__phong_ban=core_profile.phong_ban)
    ).distinct()

    legacy_incoming = VanBanDen.objects.all()
    if user.is_lanh_dao:
        legacy_incoming = legacy_incoming.filter(lanh_dao_xu_ly=user)
    elif user.is_van_thu:
        legacy_incoming = legacy_incoming.filter(nguoi_tao=user)
    elif user.is_chuyen_vien:
        legacy_incoming = legacy_incoming.filter(ds_chuyen_tiep__chuyen_vien=user).distinct()

    signature = ChuKySo.objects.filter(nguoi_dung=core_profile).first()
    signature_history = LichSuKySo.objects.filter(
        chu_ky_so__nguoi_dung=core_profile
    ).select_related("van_ban", "cong_viec").order_by("-thoi_gian_ky")
    recent_signatures = list(signature_history[:5])
    for history in recent_signatures:
        history.integrity = verify_signed_file(history)

    context = {
        "profile_user": user,
        "core_profile": core_profile,
        "signature": signature,
        "recent_signatures": recent_signatures,
        "stats": {
            "outgoing_documents": outgoing.count(),
            "incoming_documents": incoming.count(),
            "legacy_incoming_documents": legacy_incoming.count(),
            "tasks": tasks.count(),
            "records": records.count(),
            "signature_history": signature_history.count(),
        },
    }
    return render(request, "accounts/profile.html", context)
