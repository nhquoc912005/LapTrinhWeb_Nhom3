from django import forms
from django.contrib.auth.forms import AuthenticationForm


class CustomerLoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Tên đăng nhập hoặc mật khẩu không đúng.",
        "inactive": "Tài khoản này hiện đang bị vô hiệu hóa.",
    }

    username = forms.CharField(
        label="Tên đăng nhập",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nhập tên đăng nhập",
                "autocomplete": "username",
                "autofocus": True,
            }
        ),
    )

    password = forms.CharField(
        label="Mật khẩu",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control has-right-icon",
                "placeholder": "Nhập mật khẩu",
                "autocomplete": "current-password",
            }
        ),
    )
