from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class QuanLyVanBanDenViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="vanbanden",
            password="StrongPassword123",
            email="vanbanden@example.com",
            ho_va_ten="Van Ban Den",
            role=user_model.Role.VAN_THU,
        )

    def test_danh_sach_requires_login(self):
        response = self.client.get(reverse("quanlyvanbanden:danh_sach"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('quanlyvanbanden:danh_sach')}",
        )

    def test_danh_sach_renders_for_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("quanlyvanbanden:danh_sach"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Văn bản đến", html=False)
