from django import forms
from .models import VanBanDen


class VanBanDenForm(forms.ModelForm):
    # ===== VĂN THƯ =====
    # Hạn xử lý có thể để trống
    han_xu_ly = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    class Meta:
        model = VanBanDen
        fields = [
            # ===== THÔNG TIN VĂN BẢN =====
            'so_ky_hieu',
            'don_vi_ban_hanh',
            'trich_yeu',
            'loai_van_ban',
            'hinh_thuc_van_ban',
            'ngay_van_ban',
            'ngay_den',
            'han_xu_ly',
            'do_mat',
            'do_khan',

            # ===== VĂN THƯ =====
            # Field này dùng để nhập nội dung trình lên lãnh đạo
            'noi_dung_xu_ly',

            # ===== VĂN THƯ =====
            # Chọn lãnh đạo xử lý
            'lanh_dao_xu_ly',
        ]
        widgets = {
            'so_ky_hieu': forms.TextInput(attrs={'class': 'form-control'}),
            'don_vi_ban_hanh': forms.TextInput(attrs={'class': 'form-control'}),
            'trich_yeu': forms.Textarea(attrs={'class': 'form-control textarea-nice', 'rows': 4}),
            'loai_van_ban': forms.Select(attrs={'class': 'form-control'}),
            'hinh_thuc_van_ban': forms.Select(attrs={'class': 'form-control'}),
            'ngay_van_ban': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ngay_den': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'do_mat': forms.Select(attrs={'class': 'form-control'}),
            'do_khan': forms.Select(attrs={'class': 'form-control'}),
            'noi_dung_xu_ly': forms.Textarea(attrs={
                'class': 'form-control textarea-nice',
                'rows': 5,
                'placeholder': 'Nhập nội dung trình lãnh đạo xem xét...'
            }),
            'lanh_dao_xu_ly': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'so_ky_hieu': 'Số ký hiệu',
            'don_vi_ban_hanh': 'Đơn vị ban hành',
            'trich_yeu': 'Trích yếu',
            'loai_van_ban': 'Loại văn bản',
            'hinh_thuc_van_ban': 'Hình thức văn bản',
            'ngay_van_ban': 'Ngày văn bản',
            'ngay_den': 'Ngày đến',
            'han_xu_ly': 'Hạn xử lý',
            'do_mat': 'Độ mật',
            'do_khan': 'Độ khẩn',

            # ===== VĂN THƯ =====
            'noi_dung_xu_ly': 'Nội dung trình lãnh đạo',

            # ===== VĂN THƯ =====
            'lanh_dao_xu_ly': 'Lãnh đạo xử lý',
        }