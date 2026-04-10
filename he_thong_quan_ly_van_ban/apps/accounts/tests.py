from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class LoginViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="vanthu",
            password="StrongPassword123",
            email="vanthu@example.com",
            ho_va_ten="Van Thu",
            role=user_model.Role.VAN_THU,
        )

    def test_login_success_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "vanthu", "password": "StrongPassword123"},
        )

        self.assertRedirects(response, reverse("core:dashboard"))

    def test_external_next_is_ignored(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "vanthu",
                "password": "StrongPassword123",
                "next": "https://example.com/evil",
            },
        )

        self.assertRedirects(response, reverse("core:dashboard"))
