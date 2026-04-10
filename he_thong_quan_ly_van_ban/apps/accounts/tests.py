from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.core.models import NguoiDung


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

    def test_customer_creation_syncs_core_profile(self):
        core_profile = self.user.nguoi_dung_core

        self.assertEqual(core_profile.tai_khoan, self.user)
        self.assertEqual(core_profile.email, self.user.email)
        self.assertEqual(core_profile.ho_va_ten, self.user.ho_va_ten)
        self.assertEqual(core_profile.chuc_vu, NguoiDung.ChucVu.VAN_THU)
        self.assertIsNone(core_profile.phong_ban)

    def test_customer_creation_syncs_permission_group(self):
        self.assertQuerySetEqual(
            self.user.groups.order_by("name").values_list("name", flat=True),
            [self.user.role],
            transform=lambda value: value,
        )
        self.assertTrue(self.user.groups.filter(name=self.user.role).exists())
        self.assertTrue(self.user.has_perm("accounts.access_van_thu_area"))

    def test_login_recreates_missing_core_profile(self):
        self.user.nguoi_dung_core.delete()

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "vanthu", "password": "StrongPassword123"},
        )

        self.assertRedirects(response, reverse("core:dashboard"))
        self.user.refresh_from_db()
        self.assertTrue(
            NguoiDung.objects.filter(tai_khoan=self.user, email=self.user.email).exists()
        )

    def test_role_change_updates_permission_group(self):
        user_model = get_user_model()
        self.user.role = user_model.Role.LANH_DAO
        self.user.save(update_fields=["role"])
        self.user.refresh_from_db()

        self.assertQuerySetEqual(
            self.user.groups.order_by("name").values_list("name", flat=True),
            [user_model.Role.LANH_DAO],
            transform=lambda value: value,
        )
        self.assertTrue(self.user.has_perm("accounts.access_lanh_dao_area"))
