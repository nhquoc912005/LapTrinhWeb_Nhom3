from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class HoSoVanBanViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="hosovanban",
            password="StrongPassword123",
            email="hosovanban@example.com",
            ho_va_ten="Ho So Van Ban",
            role=user_model.Role.CHUYEN_VIEN,
        )

    def test_danh_sach_renders_for_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("hosovanban:danh_sach"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hồ sơ Văn bản", html=False)
