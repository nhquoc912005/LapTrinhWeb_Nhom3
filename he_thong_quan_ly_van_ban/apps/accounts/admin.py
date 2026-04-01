from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Customer
# Register your models here.

@admin.register(Customer)
class CustomerAdmin(UserAdmin):
    model = Customer

    list_display = (
        "username", "email", "ho_va_ten", "role",
        "phong_ban", "is_staff", "is_active",
    )
    list_filter = ("role","is_staff","is_active","groups")

    fieldsets = UserAdmin.fieldsets + (
        ("Thông tin thêm",{
            "fields":(
                "ho_va_ten","chuc_vu","sdt",
                "role","chi_nhanh","phong_ban",
            )
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Thông tin thêm",{
            "classes" : ("wide",),
            "fields":(
                "email","ho_va_ten","chuc_vu",
                "sdt","role","chi_nhanh","phong_ban",),
        }),
    )

    search_fields = ("username","email","ho_va_ten")
    ordering = ("username",)