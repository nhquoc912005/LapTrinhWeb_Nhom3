from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

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
    return render(request, "index.html", {"form": form, "next_url": next_url})


@login_required
@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)
