from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.core.context_processors import auth_shell


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


class NavigationMenuTests(TestCase):
    def _build_request_for_role(self, role):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username=f"user_{role.lower()}",
            password="StrongPassword123",
            email=f"{role.lower()}@example.com",
            ho_va_ten=f"User {role}",
            role=role,
        )
        response = self.client.get(reverse("core:dashboard"))
        request = response.wsgi_request
        request.user = user
        return request

    def test_van_thu_sees_bao_cao_thong_ke_in_sidebar(self):
        request = self._build_request_for_role(get_user_model().Role.VAN_THU)

        context = auth_shell(request)
        labels = [item["label"] for item in context["sidebar_menu_items"]]
        report_item = next(
            item for item in context["sidebar_menu_items"] if item["label"] == "Báo cáo thống kê"
        )

        self.assertIn("Báo cáo thống kê", labels)
        self.assertTrue(report_item["is_enabled"])

    def test_chuyen_vien_sees_van_ban_den_and_bao_cao_thong_ke_in_sidebar(self):
        request = self._build_request_for_role(get_user_model().Role.CHUYEN_VIEN)

        context = auth_shell(request)
        labels = [item["label"] for item in context["sidebar_menu_items"]]
        incoming_item = next(
            item for item in context["sidebar_menu_items"] if item["label"] == "Văn bản đến"
        )
        report_item = next(
            item for item in context["sidebar_menu_items"] if item["label"] == "Báo cáo thống kê"
        )

        self.assertIn("Văn bản đến", labels)
        self.assertIn("Báo cáo thống kê", labels)
        self.assertTrue(incoming_item["is_enabled"])
        self.assertTrue(report_item["is_enabled"])
