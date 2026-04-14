import os
from django import forms
from django.utils import timezone
from ..core.models import VanBan, NguoiDung

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx"}

def validate_file_size(file, max_mb=50):
    if file and file.size > max_mb * 1024 * 1024:
        raise forms.ValidationError(
            f'File "{file.name}" không được vượt quá {max_mb}MB.'
        )


def validate_file_extension(file):
    if file:
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                "Chỉ chấp nhận các định dạng: PDF, DOCX, XLSX."
            )


class VanBanDiForm(forms.ModelForm):
    ngay_van_ban = forms.DateField(
        label="Ngày văn bản",
        required=True,
        initial=timezone.now().date,
        widget=forms.DateInput(attrs={
            "class": "vbdi-input",
            "type": "date",
        })
    )

    class Meta:
        model = VanBan
        fields = [
            "so_ky_hieu",
            "don_vi_soan_thao",
            "loai_van_ban",
            "hinh_thuc",
            "trich_yeu",
            "han_xu_ly",
            "do_khan",
            "file_dinh_kem",
            "lanh_dao_duyet",
            "noi_dung",
        ]
        widgets = {
            "so_ky_hieu": forms.TextInput(attrs={
                "class": "vbdi-input",
                "placeholder": "VD: 123/UBND",
            }),
            "don_vi_soan_thao": forms.Select(attrs={"class": "vbdi-select"}),
            "loai_van_ban": forms.Select(attrs={"class": "vbdi-select"}),
            "hinh_thuc": forms.Select(attrs={"class": "vbdi-select"}),
            "trich_yeu": forms.Textarea(attrs={
                "class": "vbdi-textarea",
                "placeholder": "Nội dung tóm tắt văn bản...",
                "rows": 3,
            }),
            "han_xu_ly": forms.DateInput(attrs={
                "class": "vbdi-input",
                "type": "date",
            }),
            "do_khan": forms.Select(attrs={"class": "vbdi-select"}),
            "file_dinh_kem": forms.FileInput(attrs={
                "id": "id_file_dinh_kem",
                "style": "display:none",
                "accept": ".pdf,.docx,.xlsx",
            }),
            "lanh_dao_duyet": forms.Select(attrs={"class": "vbdi-select"}),
            "noi_dung": forms.Textarea(attrs={
                "class": "vbdi-textarea vbdi-textarea-lg",
                "placeholder": "Nhập nội dung xử lý...",
                "rows": 5,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["lanh_dao_duyet"].queryset = NguoiDung.objects.filter(
            chuc_vu="Lãnh Đạo"
        )
        self.fields["lanh_dao_duyet"].empty_label = "-- Chọn lãnh đạo --"

        self.fields["don_vi_soan_thao"].required = False
        self.fields["han_xu_ly"].required = False
        self.fields["do_khan"].required = False
        self.fields["noi_dung"].required = False

        self.fields["don_vi_soan_thao"].choices = [
            ("", "-- Chọn đơn vị soạn thảo --")
        ] + list(VanBan.DON_VI_SOAN_THAO_CHOICES)

        self.fields["loai_van_ban"].choices = [
            ("", "-- Chọn loại văn bản --")
        ] + list(VanBan.LOAI_VAN_BAN_CHOICES)

        self.fields["hinh_thuc"].choices = [
            ("", "-- Chọn hình thức văn bản --")
        ] + list(VanBan.HINH_THUC_CHOICES)

        self.fields["do_khan"].choices = [
            ("", "-- Chọn độ khẩn --")
        ] + list(VanBan.DO_KHAN_CHOICES)

    def clean_file_dinh_kem(self):
        file = self.cleaned_data.get("file_dinh_kem")
        if file and hasattr(file, 'name'):
            validate_file_size(file, 50)
            validate_file_extension(file)
        return file

    def clean(self):
        cleaned_data = super().clean()
        ngay_van_ban = cleaned_data.get("ngay_van_ban")
        han_xu_ly = cleaned_data.get("han_xu_ly")

        if ngay_van_ban and han_xu_ly and han_xu_ly <= ngay_van_ban:
            self.add_error("han_xu_ly", "Hạn xử lý phải lớn hơn ngày văn bản.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.phan_loai = "Văn bản đi"
        instance.trang_thai = "Chờ Xử Lý"
        instance.ngay_den = timezone.now().date()
        
        # Manually assign the date from the form field
        instance.ngay_van_ban = self.cleaned_data['ngay_van_ban']

        if instance.file_dinh_kem:
            instance.kich_thuoc = instance.file_dinh_kem.size
        else:
            instance.kich_thuoc = 0

        if commit:
            instance.save()
        return instance