import os
from django import forms
from django.utils import timezone
from apps.core.validation import (
    DUPLICATE_SO_KY_HIEU_TRICH_YEU_MESSAGE,
    document_pair_exists,
    normalize_document_text,
)
from ..core.models import VanBan, NguoiDung

# File này chứa form soạn thảo/sửa văn bản đi và validate file đính kèm.

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx"}

def validate_file_size(file, max_mb=50):
    # Giới hạn dung lượng file upload để tránh lưu file quá lớn.
    if file and file.size > max_mb * 1024 * 1024:
        raise forms.ValidationError(
            f'File "{file.name}" không được vượt quá {max_mb}MB.'
        )


def validate_file_extension(file):
    # Chỉ cho phép các định dạng văn bản/bảng tính đang được hệ thống hỗ trợ.
    if file:
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                "Chỉ chấp nhận các định dạng: PDF, DOCX, XLSX."
            )


class VanBanDiForm(forms.ModelForm):
    # Form dùng cho màn thêm/sửa văn bản đi của chuyên viên/lãnh đạo.
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
            "loai_van_ban",
            "hinh_thuc",
            "trich_yeu",
            "ngay_van_ban",
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
        # Thiết lập choices và danh sách lãnh đạo duyệt cho form văn bản đi.
        super().__init__(*args, **kwargs)

        self.fields["lanh_dao_duyet"].queryset = NguoiDung.objects.filter(
            chuc_vu=NguoiDung.ChucVu.LANH_DAO
        )
        self.fields["lanh_dao_duyet"].empty_label = "-- Chọn lãnh đạo --"

        if self.instance and self.instance.pk and self.instance.ngay_van_ban:
            self.fields["ngay_van_ban"].initial = self.instance.ngay_van_ban

        self.fields["han_xu_ly"].required = False
        self.fields["do_khan"].required = False
        self.fields["noi_dung"].required = False

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
        # Validate file chính được upload cho văn bản đi.
        file = self.cleaned_data.get("file_dinh_kem")
        if file and hasattr(file, 'name'):
            validate_file_size(file, 50)
            validate_file_extension(file)
        return file

    def clean(self):
        # Kiểm tra ngày xử lý và trùng số ký hiệu + trích yếu trong văn bản đi.
        cleaned_data = super().clean()
        ngay_van_ban = cleaned_data.get("ngay_van_ban")
        han_xu_ly = cleaned_data.get("han_xu_ly")
        so_ky_hieu = normalize_document_text(cleaned_data.get("so_ky_hieu"))
        trich_yeu = normalize_document_text(cleaned_data.get("trich_yeu"))

        cleaned_data["so_ky_hieu"] = so_ky_hieu
        cleaned_data["trich_yeu"] = trich_yeu

        if ngay_van_ban and han_xu_ly and han_xu_ly <= ngay_van_ban:
            self.add_error("han_xu_ly", "Hạn xử lý phải lớn hơn ngày văn bản.")

        if document_pair_exists(
            phan_loai="Văn bản đi",
            so_ky_hieu=so_ky_hieu,
            trich_yeu=trich_yeu,
            exclude_pk=self.instance.pk,
        ):
            raise forms.ValidationError(DUPLICATE_SO_KY_HIEU_TRICH_YEU_MESSAGE)

        return cleaned_data

    def save(self, commit=True):
        # Gán phan_loai/trạng thái mặc định và kích thước file trước khi lưu.
        instance = super().save(commit=False)
        instance.phan_loai = "Văn bản đi"
        if not instance.pk:
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
