from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class QuanLyVanBanDiViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="vanbandi",
            password="StrongPassword123",
            email="vanbandi@example.com",
            ho_va_ten="Van Ban Di",
            role=user_model.Role.CHUYEN_VIEN,
        )

    def test_danh_sach_renders_for_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("quanlyvanbandi:danh_sach"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Văn bản đi", html=False)
