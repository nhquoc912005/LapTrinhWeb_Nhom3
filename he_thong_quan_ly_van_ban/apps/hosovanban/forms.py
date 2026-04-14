from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.models import HoSoVanBan, PhongBan, NguoiDung


class HoSoVanBanCreateForm(forms.ModelForm):
    phong_ban = forms.ModelMultipleChoiceField(
        queryset=PhongBan.objects.all().order_by("ten_phong_ban"),
        required=True,
        widget=forms.CheckboxSelectMultiple,
        label="Phòng ban được xem",
    )

    nguoi_xu_ly = forms.ModelMultipleChoiceField(
        queryset=NguoiDung.objects.select_related("phong_ban").all().order_by("ho_va_ten"),
        required=True,
        widget=forms.MultipleHiddenInput,
        label="Người xử lý",
    )

    class Meta:
        model = HoSoVanBan
        fields = [
            "tieu_de_ho_so",
            "ky_hieu_ho_so",
            "thoi_gian_bao_quan",
            "so_nam_luu_tru",
            "mo_ta",
        ]

    def clean_ky_hieu_ho_so(self):
        ky_hieu = self.cleaned_data.get("ky_hieu_ho_so", "").strip()
        if HoSoVanBan.objects.filter(ky_hieu_ho_so__iexact=ky_hieu).exists():
            raise ValidationError("Số ký hiệu đã tồn tại trong hệ thống.")
        return ky_hieu

    def clean(self):
        cleaned_data = super().clean()
        thoi_gian_bao_quan = cleaned_data.get("thoi_gian_bao_quan")
        so_nam_luu_tru = cleaned_data.get("so_nam_luu_tru")

        mapping = {
            "Theo quy định - 2 năm": 2,
            "Theo quy định - 5 năm": 5,
            "Theo quy định - 10 năm": 10,
        }

        if thoi_gian_bao_quan in mapping:
            cleaned_data["so_nam_luu_tru"] = mapping[thoi_gian_bao_quan]
        elif thoi_gian_bao_quan == "Vĩnh viễn":
            cleaned_data["so_nam_luu_tru"] = None
        elif thoi_gian_bao_quan == "Tạm thời":
            if so_nam_luu_tru in (None, ""):
                self.add_error("so_nam_luu_tru", "Vui lòng nhập số năm lưu trữ.")
            else:
                try:
                    so_nam = int(so_nam_luu_tru)
                    if so_nam <= 0:
                        raise ValueError
                    cleaned_data["so_nam_luu_tru"] = so_nam
                except (TypeError, ValueError):
                    self.add_error("so_nam_luu_tru", "Số năm bảo quản phải là định dạng số nguyên dương.")

        return cleaned_data

class HoSoVanBanUpdateForm(HoSoVanBanCreateForm):
    def clean_ky_hieu_ho_so(self):
        ky_hieu = self.cleaned_data.get("ky_hieu_ho_so", "").strip()
        qs = HoSoVanBan.objects.filter(ky_hieu_ho_so__iexact=ky_hieu)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Số ký hiệu đã tồn tại trong hệ thống.")
        return ky_hieu