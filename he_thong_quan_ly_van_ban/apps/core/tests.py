from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class DashboardViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.valid_user = user_model.objects.create_user(
            username="adminrole",
            password="StrongPassword123",
            email="adminrole@example.com",
            ho_va_ten="Admin Role",
            role=user_model.Role.ADMIN,
        )
        self.invalid_user = user_model.objects.create_user(
            username="invalidrole",
            password="StrongPassword123",
            email="invalidrole@example.com",
            ho_va_ten="Invalid Role",
            role=user_model.Role.CHUYEN_VIEN,
        )
        self.invalid_user.role = "UNKNOWN"
        self.invalid_user.save(update_fields=["role"])

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("core:dashboard"))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('core:dashboard')}",
        )

    def test_dashboard_renders_for_valid_role(self):
        self.client.force_login(self.valid_user)
        response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TỔNG QUAN HỆ THỐNG")
        self.assertContains(response, 'aria-disabled="true"', html=False)

    def test_dashboard_returns_forbidden_for_unknown_role(self):
        self.client.force_login(self.invalid_user)
        response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(response.status_code, 403)
