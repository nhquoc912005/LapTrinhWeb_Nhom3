from django.shortcuts import render

from apps.accounts.decorators import role_required
from apps.accounts.models import Customer

@role_required(*Customer.Role.values)
def dashboard(request):
    return render(request, "dashboard.html")


@role_required(*Customer.Role.values)
def bao_cao_thong_ke(request):
    return render(request, "bao-cao-thong-ke.html")
