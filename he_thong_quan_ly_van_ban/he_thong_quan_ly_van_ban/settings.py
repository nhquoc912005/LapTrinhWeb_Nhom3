import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# File cấu hình chính của project Django quản lý văn bản.
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Nạp biến môi trường từ .env để cấu hình database, host và CSRF khi chạy thực tế.
load_dotenv(BASE_DIR / ".env")


def _get_csv_env(name, default=None):
    # Đọc các biến môi trường dạng danh sách phân tách bằng dấu phẩy.
    value = os.getenv(name, "")
    if not value:
        return list(default or [])
    return [item.strip() for item in value.split(",") if item.strip()]


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-^ex&97v6!agmhn7!0(&(9*=9a6iuwreaeg3r&2zj!fvlzwp19!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Các host và origin tin cậy được lấy từ môi trường để hỗ trợ chạy local và deploy.
ALLOWED_HOSTS = _get_csv_env(
    "DJANGO_ALLOWED_HOSTS",
    ["localhost", "127.0.0.1", "[::1]"],
)
CSRF_TRUSTED_ORIGINS = _get_csv_env(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    ["http://localhost:8000", "http://127.0.0.1:8000"],
)
CSRF_COOKIE_NAME = os.getenv("DJANGO_CSRF_COOKIE_NAME", "qlvb_csrftoken")
SESSION_COOKIE_NAME = os.getenv("DJANGO_SESSION_COOKIE_NAME", "qlvb_sessionid")


# Application definition

# Khai báo các app nghiệp vụ chính: tài khoản, văn bản đi/đến, công việc và hồ sơ.
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'apps.core.apps.CoreConfig',
    'apps.accounts.apps.AccountsConfig',
    'apps.quanlyvanbandi.apps.QuanlyvanbandiConfig',
    'apps.quanlyvanbanden.apps.QuanlyvanbandenConfig',
    'apps.hosovanban.apps.HosovanbanConfig',
    'apps.quanlycongviec.apps.QuanlycongviecConfig',
]
# Dùng model người dùng tùy chỉnh để gắn vai trò nghiệp vụ vào tài khoản đăng nhập.
AUTH_USER_MODEL = "accounts.Customer"

# Điều hướng mặc định cho các luồng đăng nhập, đăng xuất và sau đăng nhập.
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

# Static files
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "apps" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@example.com"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'he_thong_quan_ly_van_ban.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'apps' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Cung cấp dữ liệu menu/sidebar và trạng thái active cho layout chung.
                'apps.core.context_processors.auth_shell',
            ],
        },
    },
]

WSGI_APPLICATION = 'he_thong_quan_ly_van_ban.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Khi có DATABASE_URL, ưu tiên kết nối database bên ngoài như PostgreSQL.
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0,
        )
    }
    DATABASES["default"]["CONN_MAX_AGE"] = 0
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
    if "postgresql" in DATABASES["default"].get("ENGINE", ""):
        DATABASES["default"].setdefault("OPTIONS", {})
        DATABASES["default"]["OPTIONS"]["sslmode"] = "require"
else:
    # Mặc định local dùng SQLite để dễ chạy demo trên máy phát triển.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"

USE_I18N = True

USE_TZ = True


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Lưu file upload như văn bản, chữ ký số và file đã ký trong thư mục media.
# Thêm vào file vào thư mục media
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
