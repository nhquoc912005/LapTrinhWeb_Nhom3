from django.shortcuts import render

from apps.accounts.decorators import role_required
from apps.accounts.models import Customer


@role_required(*Customer.Role.values)
def danh_sach(request):
    return render(request, "ho-so-van-ban.html")
