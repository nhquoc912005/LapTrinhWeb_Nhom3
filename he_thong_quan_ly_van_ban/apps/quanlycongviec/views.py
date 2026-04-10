from django.shortcuts import render

from apps.accounts.decorators import role_required
from apps.accounts.models import Customer


@role_required(*Customer.Role.values)
def giao_viec(request):
    return render(request, "giao-viec.html")


@role_required(*Customer.Role.values)
def xu_ly_cong_viec(request):
    return render(request, "xu-ly-cong-viec.html")
