from django import forms

from apps.core.models import NguoiDung, VanBan
from apps.core.validation import (
    DUPLICATE_SO_KY_HIEU_TRICH_YEU_MESSAGE,
    document_pair_exists,
    normalize_document_text,
)

# File này chứa form thêm/sửa văn bản đến, dùng model chung VanBan.


class VanBanDenForm(forms.ModelForm):
    """
    Form văn bản đến dùng MODEL CHUNG: apps.core.models.VanBan

    Mapping tên cũ -> tên mới:
    - hinh_thuc_van_ban -> hinh_thuc
    - noi_dung_xu_ly -> noi_dung
    - lanh_dao_xu_ly -> lanh_dao_duyet
    """

    han_xu_ly = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    hinh_thuc_van_ban = forms.ChoiceField(
        choices=VanBan.HINH_THUC_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Hình thức văn bản'
    )

    noi_dung_xu_ly = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control textarea-nice',
            'rows': 5,
            'placeholder': 'Nhập nội dung trình lãnh đạo xem xét...'
        }),
        label='Nội dung trình lãnh đạo'
    )

    lanh_dao_xu_ly = forms.ModelChoiceField(
        queryset=NguoiDung.objects.none(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Lãnh đạo xử lý'
    )

    class Meta:
        model = VanBan
        fields = [
            'so_ky_hieu',
            'don_vi_ban_hanh',
            'trich_yeu',
            'loai_van_ban',
            'ngay_van_ban',
            'ngay_den',
            'han_xu_ly',
            'do_mat',
            'do_khan',
        ]

        widgets = {
            'so_ky_hieu': forms.TextInput(attrs={'class': 'form-control'}),
            'don_vi_ban_hanh': forms.TextInput(attrs={'class': 'form-control'}),
            'trich_yeu': forms.Textarea(attrs={
                'class': 'form-control textarea-nice',
                'rows': 4
            }),
            'loai_van_ban': forms.Select(attrs={'class': 'form-control'}),
            'ngay_van_ban': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'ngay_den': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'do_mat': forms.Select(attrs={'class': 'form-control'}),
            'do_khan': forms.Select(attrs={'class': 'form-control'}),
        }

        labels = {
            'so_ky_hieu': 'Số ký hiệu',
            'trich_yeu': 'Trích yếu',
            'loai_van_ban': 'Loại văn bản',
            'ngay_van_ban': 'Ngày văn bản',
            'ngay_den': 'Ngày đến',
            'han_xu_ly': 'Hạn xử lý',
            'do_mat': 'Độ mật',
            'do_khan': 'Độ khẩn',
        }

    def __init__(self, *args, **kwargs):
        # Chuẩn bị danh sách lãnh đạo xử lý và đổ dữ liệu alias khi sửa văn bản.
        super().__init__(*args, **kwargs)

        # Chỉ lấy người dùng lõi có chức vụ Lãnh Đạo
        self.fields['lanh_dao_xu_ly'].queryset = NguoiDung.objects.filter(
            chuc_vu=NguoiDung.ChucVu.LANH_DAO
        ).order_by('ho_va_ten')

        # Khi sửa dữ liệu cũ, đổ dữ liệu từ field thật sang field alias
        if self.instance and self.instance.pk:
            self.fields['hinh_thuc_van_ban'].initial = self.instance.hinh_thuc
            self.fields['noi_dung_xu_ly'].initial = self.instance.noi_dung
            self.fields['lanh_dao_xu_ly'].initial = self.instance.lanh_dao_duyet

    def clean(self):
        # Validate trùng số ký hiệu + trích yếu trong nhóm văn bản đến.
        cleaned_data = super().clean()
        so_ky_hieu = normalize_document_text(cleaned_data.get('so_ky_hieu'))
        trich_yeu = normalize_document_text(cleaned_data.get('trich_yeu'))

        cleaned_data['so_ky_hieu'] = so_ky_hieu
        cleaned_data['trich_yeu'] = trich_yeu

        if document_pair_exists(
            phan_loai='Văn bản đến',
            so_ky_hieu=so_ky_hieu,
            trich_yeu=trich_yeu,
            exclude_pk=self.instance.pk,
        ):
            raise forms.ValidationError(DUPLICATE_SO_KY_HIEU_TRICH_YEU_MESSAGE)

        return cleaned_data

    def save(self, commit=True):
        # Lưu dữ liệu từ field giao diện vào đúng field của model VanBan dùng chung.
        vb = super().save(commit=False)

        # Map field giao diện cũ sang model chung
        vb.hinh_thuc = self.cleaned_data.get('hinh_thuc_van_ban')
        vb.noi_dung = self.cleaned_data.get('noi_dung_xu_ly')
        vb.lanh_dao_duyet = self.cleaned_data.get('lanh_dao_xu_ly')

        # Văn bản đến luôn phải có phan_loai này
        vb.phan_loai = 'Văn bản đến'

        if commit:
            vb.save()

        return vb
