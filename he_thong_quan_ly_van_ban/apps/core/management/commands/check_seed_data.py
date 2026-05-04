# -*- coding: utf-8 -*-
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from apps.core.models import (
    BanHanh,
    ChuyenTiep,
    CongViec,
    FileCVLienQuan,
    HoSoVanBan,
    NguoiDung,
    NguoiXuLyHoSo,
    NoiNhanVanBan,
    PhanCongCongViec,
    PhongBan,
    PhongXemHoSo,
    VanBan,
    VanBanDuyet,
    VanBanLienQuan,
)
from apps.quanlyvanbanden.models import (
    TepVanBanDen,
    VanBanDen,
    VanBanDenChuyenTiep,
)

from ._data_audit import configure_utf8_output, database_kind, safe_database_identity


User = get_user_model()


# Command kiểm tra dữ liệu seed/demo đang có trong database.
class Command(BaseCommand):
    help = "Check role based seed data visibility."

    def handle(self, *args, **options):
        configure_utf8_output()
        db = safe_database_identity()

        self.stdout.write("=== Database hiện tại ===")
        self.stdout.write(f"Loại kết nối: {database_kind()}")
        self.stdout.write(f"Engine: {db['engine']}")
        self.stdout.write(f"Name: {db['name']}")
        self.stdout.write(f"Host: {db['host'] or '(không có)'}")
        self.stdout.write(f"User: {db['user'] or '(không có)'}")
        self.stdout.write("")

        self.print_role_counts()
        self.print_visibility_counts()
        self.print_table_counts()

    def print_role_counts(self):
        self.stdout.write("=== Customer theo role ===")
        role_counts = {
            role: User.objects.filter(role=role).count()
            for role in User.Role.values
        }
        for role, count in role_counts.items():
            self.stdout.write(f"{role}: {count}")

        self.stdout.write("")
        self.stdout.write("=== NguoiDung theo chức vụ ===")
        for row in NguoiDung.objects.values("chuc_vu").annotate(total=Count("pk")).order_by("chuc_vu"):
            self.stdout.write(f"{row['chuc_vu']}: {row['total']}")
        self.stdout.write("")

    def print_visibility_counts(self):
        self.stdout.write("=== Dữ liệu từng role có thể thấy ===")
        usernames = {
            "ADMIN": "admin.demo",
            "LANH_DAO": "lanhdao.demo",
            "VAN_THU": "vanthu.demo",
            "CHUYEN_VIEN": "chuyenvien.demo",
        }

        for role, username in usernames.items():
            user = User.objects.filter(username=username).first()
            if not user:
                self.stdout.write(self.style.WARNING(f"{role}: thiếu user {username}"))
                continue

            profile = NguoiDung.objects.filter(tai_khoan=user).first()
            visible = self.visible_counts(user, profile)
            self.stdout.write(f"{role} ({username}):")
            for key, value in visible.items():
                self.stdout.write(f" - {key}: {value}")
        self.stdout.write("")

    def visible_counts(self, user, profile):
        outgoing = VanBan.objects.filter(
            phan_loai=VanBan.PHAN_LOAI_CHOICES[0][0],
        )
        if user.role == User.Role.VAN_THU:
            outgoing = outgoing.filter(
                trang_thai__in=[
                    VanBan.TRANG_THAI_CHOICES[3][0],
                    VanBan.TRANG_THAI_CHOICES[4][0],
                    VanBan.TRANG_THAI_CHOICES[5][0],
                ]
            )
        elif user.role == User.Role.CHUYEN_VIEN and profile:
            outgoing = outgoing.filter(nguoi_tao=profile)
        elif user.role == User.Role.LANH_DAO and profile:
            outgoing = outgoing.filter(lanh_dao_duyet=profile)

        incoming = VanBan.objects.filter(
            phan_loai=VanBan.PHAN_LOAI_CHOICES[1][0],
        )
        if user.role == User.Role.LANH_DAO and profile:
            incoming = incoming.filter(lanh_dao_duyet=profile)
        elif user.role == User.Role.CHUYEN_VIEN and profile:
            incoming = incoming.filter(
                vanbanduyet__chuyentiep__chuyentiepchitiet__nguoi_dung=profile
            ).distinct()

        tasks = CongViec.objects.all()
        if user.role == User.Role.LANH_DAO and profile:
            tasks = tasks.filter(nguoi_giao=profile)
        elif user.role == User.Role.CHUYEN_VIEN and profile:
            tasks = tasks.filter(nguoi_thuc_hien=profile)

        records = HoSoVanBan.objects.none()
        if profile:
            records = HoSoVanBan.objects.filter(
                Q(nguoi_tao=profile)
                | Q(nguoixulyhoso__nguoi_xu_ly=profile)
                | Q(phongxemhoso__phong_ban=profile.phong_ban)
            ).distinct()

        legacy_incoming = VanBanDen.objects.all()
        if user.role == User.Role.LANH_DAO:
            legacy_incoming = legacy_incoming.filter(lanh_dao_xu_ly=user)
        elif user.role == User.Role.VAN_THU:
            legacy_incoming = legacy_incoming.filter(nguoi_tao=user)
        elif user.role == User.Role.CHUYEN_VIEN:
            legacy_incoming = legacy_incoming.filter(ds_chuyen_tiep__chuyen_vien=user).distinct()

        return {
            "Văn bản đi": outgoing.count(),
            "Văn bản đến core": incoming.count(),
            "Công việc": tasks.count(),
            "Hồ sơ văn bản": records.count(),
            "VanBanDen legacy": legacy_incoming.count(),
        }

    def print_table_counts(self):
        self.stdout.write("=== Tổng record các bảng chính ===")
        model_items = [
            ("ChiNhanh", apps.get_model("core", "ChiNhanh")),
            ("PhongBan", PhongBan),
            ("DonViNgoai", apps.get_model("core", "DonViNgoai")),
            ("Customer", User),
            ("NguoiDung", NguoiDung),
            ("HoSoVanBan", HoSoVanBan),
            ("NguoiXuLyHoSo", NguoiXuLyHoSo),
            ("PhongXemHoSo", PhongXemHoSo),
            ("VanBan", VanBan),
            ("VanBanLienQuan", VanBanLienQuan),
            ("VanBanDuyet", VanBanDuyet),
            ("BanHanh", BanHanh),
            ("NoiNhanVanBan", NoiNhanVanBan),
            ("ChuyenTiep", ChuyenTiep),
            ("CongViec", CongViec),
            ("PhanCongCongViec", PhanCongCongViec),
            ("FileCVLienQuan", FileCVLienQuan),
            ("VanBanDen", VanBanDen),
            ("TepVanBanDen", TepVanBanDen),
            ("VanBanDenChuyenTiep", VanBanDenChuyenTiep),
        ]

        try:
            model_items.append(("BanHanhChiTiep", apps.get_model("core", "BanHanhChiTiep")))
        except LookupError:
            self.stdout.write(
                self.style.WARNING(
                    "BanHanhChiTiep: model không tồn tại trong schema hiện tại; đang dùng NoiNhanVanBan."
                )
            )

        for label, model in model_items:
            count = model.objects.count()
            line = f"{label}: {count}"
            if count == 0:
                self.stdout.write(self.style.WARNING(line + "  <-- CẢNH BÁO: bảng đang bằng 0"))
            else:
                self.stdout.write(line)
