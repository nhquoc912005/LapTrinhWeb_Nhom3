"""
ASGI config for he_thong_quan_ly_van_ban project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'he_thong_quan_ly_van_ban.settings')

application = get_asgi_application()
