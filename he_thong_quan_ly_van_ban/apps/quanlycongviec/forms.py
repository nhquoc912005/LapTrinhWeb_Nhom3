from pathlib import Path

from django import forms


ALLOWED_RESULT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx"}
MAX_RESULT_FILE_SIZE = 50 * 1024 * 1024


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(item, initial) for item in data]
        if not data:
            return []
        return [single_file_clean(data, initial)]


class BaseTaskResultForm(forms.Form):
    ket_qua_xu_ly = forms.CharField(
        label="Mô tả kết quả xử lý",
        required=True,
        error_messages={"required": "Kết quả xử lý là bắt buộc."},
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "class": "form-control",
                "placeholder": "Nhập mô tả kết quả xử lý công việc...",
            }
        ),
    )
    ghi_chu = forms.CharField(
        label="Ghi chú",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "class": "form-control",
                "placeholder": "Nhập ghi chú (nếu có)...",
            }
        ),
    )
    tep_ket_qua = MultipleFileField(
        label="File kết quả",
        required=False,
        widget=MultipleFileInput(
            attrs={
                "class": "form-control",
                "accept": ".pdf,.doc,.docx,.xls,.xlsx",
                "multiple": True,
            }
        ),
    )

    require_result_file = False

    def __init__(self, *args, **kwargs):
        self.task = kwargs.pop("task", None)
        super().__init__(*args, **kwargs)

    def get_uploaded_files(self):
        return self.files.getlist("tep_ket_qua")

    def clean(self):
        cleaned_data = super().clean()
        uploaded_files = self.get_uploaded_files()

        if self.require_result_file and not uploaded_files:
            raise forms.ValidationError("Vui lòng đính kèm ít nhất một file kết quả.")

        for uploaded_file in uploaded_files:
            extension = Path(uploaded_file.name).suffix.lower()
            if extension not in ALLOWED_RESULT_EXTENSIONS:
                raise forms.ValidationError("File không hợp lệ!")
            if uploaded_file.size > MAX_RESULT_FILE_SIZE:
                raise forms.ValidationError("File vượt quá dung lượng cho phép.")

        return cleaned_data


class ProcessTaskForm(BaseTaskResultForm):
    require_result_file = True


class UpdateTaskResultForm(BaseTaskResultForm):
    delete_file_ids = forms.CharField(required=False, widget=forms.HiddenInput())


class ReturnTaskForm(forms.Form):
    noi_dung = forms.CharField(
        label="Lý do hoàn trả",
        required=True,
        error_messages={"required": "Lý do hoàn trả là bắt buộc."},
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "class": "form-control",
                "placeholder": "Nhập chi tiết lý do hoàn trả, nội dung cần chỉnh sửa hoặc bổ sung...",
            }
        ),
    )
