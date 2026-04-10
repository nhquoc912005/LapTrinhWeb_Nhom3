from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class QuanLyCongViecViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="congviec",
            password="StrongPassword123",
            email="congviec@example.com",
            ho_va_ten="Cong Viec",
            role=user_model.Role.LANH_DAO,
        )

    def test_giao_viec_renders_for_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("quanlycongviec:giao_viec"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Giao Việc", html=False)

    def test_xu_ly_cong_viec_renders_for_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("quanlycongviec:xu_ly_cong_viec"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Công việc", html=False)
