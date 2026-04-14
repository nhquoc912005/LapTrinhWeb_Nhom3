from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.models import CongViec, FileCVLienQuan, HoanTraCongViec


class QuanLyCongViecWorkflowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.leader = user_model.objects.create_user(
            username="leader",
            password="StrongPassword123",
            email="leader@example.com",
            ho_va_ten="Lãnh đạo A",
            role=user_model.Role.LANH_DAO,
        )
        self.specialist = user_model.objects.create_user(
            username="specialist",
            password="StrongPassword123",
            email="specialist@example.com",
            ho_va_ten="Chuyên viên A",
            role=user_model.Role.CHUYEN_VIEN,
        )
        self.other_specialist = user_model.objects.create_user(
            username="specialist2",
            password="StrongPassword123",
            email="specialist2@example.com",
            ho_va_ten="Chuyên viên B",
            role=user_model.Role.CHUYEN_VIEN,
        )

        self.leader_core = self.leader.sync_core_profile()
        self.specialist_core = self.specialist.sync_core_profile()
        self.other_specialist_core = self.other_specialist.sync_core_profile()

    def _create_task(self, **overrides):
        defaults = {
            "ten_cong_viec": "Soạn báo cáo thuế",
            "noi_dung_cong_viec": "Thực hiện và nộp báo cáo thuế tháng.",
            "nguoi_giao": self.leader_core,
            "nguoi_thuc_hien": self.specialist_core,
            "ngay_bat_dau": timezone.now().date(),
            "han_xu_ly": timezone.now() + timedelta(days=3),
            "trang_thai": CongViec.TrangThai.CHO_XU_LY,
            "yeu_cau_phe_duyet": True,
        }
        defaults.update(overrides)
        return CongViec.objects.create(**defaults)

    def test_specialist_list_only_shows_assigned_tasks(self):
        own_task = self._create_task(ten_cong_viec="Công việc của tôi")
        self._create_task(
            ten_cong_viec="Công việc người khác",
            nguoi_thuc_hien=self.other_specialist_core,
        )

        self.client.force_login(self.specialist)
        response = self.client.get(reverse("quanlycongviec:xu_ly_cong_viec"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, own_task.ten_cong_viec)
        self.assertNotContains(response, "Công việc người khác")

    def test_giao_viec_renders_for_leader(self):
        task = self._create_task(ten_cong_viec="Nhiệm vụ lãnh đạo theo dõi")

        self.client.force_login(self.leader)
        response = self.client.get(reverse("quanlycongviec:giao_viec"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, task.ten_cong_viec)

    def test_task_detail_renders_for_assignee(self):
        task = self._create_task()

        self.client.force_login(self.specialist)
        response = self.client.get(reverse("quanlycongviec:task_detail", args=[task.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, task.ten_cong_viec)

    def test_process_task_without_approval_marks_completed(self):
        task = self._create_task(yeu_cau_phe_duyet=False)

        self.client.force_login(self.specialist)
        response = self.client.post(
            reverse("quanlycongviec:process_task", args=[task.pk]),
            data={
                "ket_qua_xu_ly": "Đã xử lý xong và gửi kết quả.",
                "ghi_chu": "Không có ghi chú thêm.",
                "tep_ket_qua": SimpleUploadedFile(
                    "ket-qua.docx",
                    b"dummy-content",
                    content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ),
            },
            follow=True,
        )

        task.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(task.trang_thai, CongViec.TrangThai.DA_HOAN_THANH)
        self.assertTrue(
            FileCVLienQuan.objects.filter(
                cong_viec=task,
                nguon_tai_len=FileCVLienQuan.NguonTaiLen.KET_QUA_XU_LY,
                nguoi_tai_len=self.specialist_core,
            ).exists()
        )

    def test_process_task_with_approval_moves_to_waiting_review(self):
        task = self._create_task(yeu_cau_phe_duyet=True)

        self.client.force_login(self.specialist)
        self.client.post(
            reverse("quanlycongviec:process_task", args=[task.pk]),
            data={
                "ket_qua_xu_ly": "Đã hoàn thành hồ sơ.",
                "ghi_chu": "",
                "tep_ket_qua": SimpleUploadedFile(
                    "ket-qua.pdf",
                    b"%PDF-1.4 test",
                    content_type="application/pdf",
                ),
            },
        )

        task.refresh_from_db()
        self.assertEqual(task.trang_thai, CongViec.TrangThai.CHO_DUYET)

    def test_update_task_result_keeps_status_and_cannot_delete_original_file(self):
        task = self._create_task(
            trang_thai=CongViec.TrangThai.HOAN_TRA_CV,
            ket_qua_xu_ly="Bản nháp ban đầu.",
        )
        original_file = FileCVLienQuan.objects.create(
            cong_viec=task,
            file_van_ban=SimpleUploadedFile("goc.pdf", b"%PDF-1.4 original", content_type="application/pdf"),
            loai_file=FileCVLienQuan.LoaiFile.CHINH,
            nguon_tai_len=FileCVLienQuan.NguonTaiLen.GIAO_VIEC,
            nguoi_tai_len=self.leader_core,
        )
        result_file = FileCVLienQuan.objects.create(
            cong_viec=task,
            file_van_ban=SimpleUploadedFile(
                "bao-cao.xlsx",
                b"excel-result",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
            loai_file=FileCVLienQuan.LoaiFile.LIEN_QUAN,
            nguon_tai_len=FileCVLienQuan.NguonTaiLen.KET_QUA_XU_LY,
            nguoi_tai_len=self.specialist_core,
        )

        self.client.force_login(self.specialist)
        self.client.post(
            reverse("quanlycongviec:update_task_result", args=[task.pk]),
            data={
                "ket_qua_xu_ly": "Đã cập nhật theo yêu cầu.",
                "ghi_chu": "Đã bổ sung thêm số liệu.",
                "delete_file_ids": f"{original_file.pk},{result_file.pk}",
            },
        )

        task.refresh_from_db()
        self.assertEqual(task.trang_thai, CongViec.TrangThai.HOAN_TRA_CV)
        self.assertTrue(FileCVLienQuan.objects.filter(pk=original_file.pk).exists())
        self.assertFalse(FileCVLienQuan.objects.filter(pk=result_file.pk).exists())

    def test_specialist_can_return_task_to_leader(self):
        task = self._create_task()

        self.client.force_login(self.specialist)
        self.client.post(
            reverse("quanlycongviec:return_task", args=[task.pk]),
            data={"noi_dung": "Thiếu chứng từ đầu vào, đề nghị lãnh đạo bổ sung."},
        )

        task.refresh_from_db()
        self.assertEqual(task.trang_thai, CongViec.TrangThai.HOAN_TRA_LD)
        self.assertTrue(
            HoanTraCongViec.objects.filter(cong_viec=task, nguoi_hoan_tra=self.specialist_core).exists()
        )

    def test_leader_can_return_waiting_task_to_specialist(self):
        task = self._create_task(
            trang_thai=CongViec.TrangThai.CHO_DUYET,
            ket_qua_xu_ly="Đã nộp báo cáo để lãnh đạo duyệt.",
        )

        self.client.force_login(self.leader)
        self.client.post(
            reverse("quanlycongviec:return_task", args=[task.pk]),
            data={"noi_dung": "Bổ sung thêm bảng đối chiếu chứng từ."},
        )

        task.refresh_from_db()
        self.assertEqual(task.trang_thai, CongViec.TrangThai.HOAN_TRA_CV)
