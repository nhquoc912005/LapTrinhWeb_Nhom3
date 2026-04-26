import csv
import os
import sys
import traceback
from datetime import timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "qa_test_outputs"
EVIDENCE_DIR = OUTPUT_DIR / "evidence"
LOG_FILE = EVIDENCE_DIR / "qa_runtime_tests.log"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "he_thong_quan_ly_van_ban.settings")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.test import Client  # noqa: E402
from django.test.utils import setup_databases, setup_test_environment, teardown_databases  # noqa: E402
from django.urls import NoReverseMatch, reverse  # noqa: E402
from django.utils import timezone  # noqa: E402

from apps.core.context_processors import TOP_MENU_DEFINITIONS, auth_shell  # noqa: E402
from apps.core.models import (  # noqa: E402
    BanHanh,
    ChiNhanh,
    CongViec,
    DonViNgoai,
    FileCVLienQuan,
    HoSoVanBan,
    HoanTraCongViec,
    NguoiDung,
    NguoiXuLyHoSo,
    PheDuyetCongViec,
    PhanCongCongViec,
    PhongBan,
    PhongXemHoSo,
    VanBan,
    VanBanDuyet,
    VanBanHoanTra,
    VanBanLienQuan,
)
from apps.quanlyvanbanden.models import (  # noqa: E402
    TepVanBanDen,
    VanBanDen,
    VanBanDenChuyenTiep,
)


OUTPUT_DIR.mkdir(exist_ok=True)
EVIDENCE_DIR.mkdir(exist_ok=True)
settings.MEDIA_ROOT = str(EVIDENCE_DIR / "runtime_media")
Path(settings.MEDIA_ROOT).mkdir(exist_ok=True)


TESTCASES = []
RESULTS = []
BUGS = []
CONTEXT = {}


def log(message):
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(f"{timezone.now().isoformat()} {message}\n")


def add_case(
    test_id,
    module,
    feature,
    role,
    priority,
    preconditions,
    steps,
    test_data,
    expected,
    route_or_view,
    model_or_form,
    source_ref,
    runner=None,
    bug_title="",
    suspected_cause="",
):
    case = {
        "TestCaseID": test_id,
        "Module": module,
        "Feature": feature,
        "Role": role,
        "Priority": priority,
        "Preconditions": preconditions,
        "TestSteps": steps,
        "TestData": test_data,
        "ExpectedResult": expected,
        "RouteOrView": route_or_view,
        "ModelOrFormRelated": model_or_form,
        "SourceReference": source_ref,
        "_runner": runner,
        "_bug_title": bug_title,
        "_suspected_cause": suspected_cause,
    }
    TESTCASES.append(case)
    return case


def record(case, actual, status, severity="None", evidence="Django test client response", error="", notes=""):
    result = {
        "TestCaseID": case["TestCaseID"],
        "Module": case["Module"],
        "Feature": case["Feature"],
        "Role": case["Role"],
        "Preconditions": case["Preconditions"],
        "TestSteps": case["TestSteps"],
        "ExpectedResult": case["ExpectedResult"],
        "ActualResult": actual,
        "Status": status,
        "Severity": severity,
        "Evidence": evidence,
        "ErrorMessage": error,
        "Notes": notes,
    }
    RESULTS.append(result)
    if status == "FAIL":
        BUGS.append(
            {
                "BugID": f"BUG-{len(BUGS) + 1:03d}",
                "TestCaseID": case["TestCaseID"],
                "Module": case["Module"],
                "Feature": case["Feature"],
                "Title": case.get("_bug_title") or f"{case['Feature']} failed",
                "StepsToReproduce": case["TestSteps"],
                "ExpectedResult": case["ExpectedResult"],
                "ActualResult": actual,
                "Severity": severity,
                "SuspectedCause": case.get("_suspected_cause") or "Cần phân tích thêm từ source/runtime evidence.",
                "SourceReference": case["SourceReference"],
                "Evidence": evidence,
            }
        )
    return result


def pass_result(actual):
    return actual, "PASS", "None", ""


def fail_result(actual, severity="Medium", error=""):
    return actual, "FAIL", severity, error


def not_impl_result(actual):
    return actual, "NOT_IMPLEMENTED", "None", ""


def blocked_result(actual, error=""):
    return actual, "BLOCKED", "None", error


def upload(name, content=b"qa-file", content_type="application/pdf"):
    return SimpleUploadedFile(name, content, content_type=content_type)


def response_text(response):
    return response.content.decode("utf-8", errors="replace")


def redirect_location(response):
    return response.headers.get("Location", "")


def login_as(user):
    client = Client(raise_request_exception=False)
    client.force_login(user)
    return client


def get_ctx(response, key, default=None):
    try:
        if response.context is None:
            return default
        return response.context.get(key, default)
    except AttributeError:
        try:
            return response.context[key]
        except Exception:
            return default


def assert_status(response, expected_status, detail=""):
    if response.status_code != expected_status:
        raise AssertionError(f"Expected HTTP {expected_status}, got {response.status_code}. {detail}")


def assert_redirect_to(response, expected):
    location = redirect_location(response)
    if response.status_code not in (301, 302, 303, 307, 308):
        raise AssertionError(f"Expected redirect to {expected}, got HTTP {response.status_code}.")
    if location != expected:
        raise AssertionError(f"Expected redirect to {expected}, got {location}.")


def create_user(username, role, full_name, email, *, branch=None, department=None, is_staff=False, is_superuser=False):
    User = get_user_model()
    user = User.objects.create_user(
        username=username,
        password="StrongPassword123",
        email=email,
        ho_va_ten=full_name,
        role=role,
        is_staff=is_staff,
        is_superuser=is_superuser,
    )
    if branch:
        user.chi_nhanh = branch
    if department:
        user.phong_ban = department
    if branch or department:
        user.save()
    user.refresh_from_db()
    return user


def seed_context():
    User = get_user_model()
    today = timezone.localdate()
    branch = ChiNhanh.objects.create(ten_chi_nhanh="QA Branch")
    dept_admin = PhongBan.objects.create(chi_nhanh=branch, ten_phong_ban="Ban Giám đốc")
    dept_vanthu = PhongBan.objects.create(chi_nhanh=branch, ten_phong_ban="Văn thư")
    dept_chuyenvien = PhongBan.objects.create(chi_nhanh=branch, ten_phong_ban="Chuyên viên")
    dept_other = PhongBan.objects.create(chi_nhanh=branch, ten_phong_ban="Phòng khác")
    outside = DonViNgoai.objects.create(
        ten_don_vi="Đơn vị QA ngoài",
        email="qa.outside@example.com",
        so_dien_thoai="0900000000",
        dia_chi="QA Street",
    )

    admin = create_user(
        "qa_admin",
        User.Role.ADMIN,
        "QA Admin",
        "qa_admin@example.com",
        branch=branch,
        department=dept_admin,
        is_staff=True,
    )
    leader = create_user(
        "qa_leader",
        User.Role.LANH_DAO,
        "QA Lãnh đạo",
        "qa_leader@example.com",
        branch=branch,
        department=dept_admin,
    )
    leader_2 = create_user(
        "qa_leader2",
        User.Role.LANH_DAO,
        "QA Lãnh đạo 2",
        "qa_leader2@example.com",
        branch=branch,
        department=dept_other,
    )
    clerk = create_user(
        "qa_clerk",
        User.Role.VAN_THU,
        "QA Văn thư",
        "qa_clerk@example.com",
        branch=branch,
        department=dept_vanthu,
    )
    specialist = create_user(
        "qa_specialist",
        User.Role.CHUYEN_VIEN,
        "QA Chuyên viên",
        "qa_specialist@example.com",
        branch=branch,
        department=dept_chuyenvien,
    )
    specialist_2 = create_user(
        "qa_specialist2",
        User.Role.CHUYEN_VIEN,
        "QA Chuyên viên 2",
        "qa_specialist2@example.com",
        branch=branch,
        department=dept_other,
    )
    invalid_role_user = create_user(
        "qa_invalid_role",
        User.Role.CHUYEN_VIEN,
        "QA Invalid Role",
        "qa_invalid_role@example.com",
        branch=branch,
        department=dept_other,
    )
    invalid_role_user.role = "UNKNOWN"
    invalid_role_user.save(update_fields=["role"])

    incoming = VanBanDen.objects.create(
        so_ky_hieu="QA-VBD-001",
        don_vi_ban_hanh="Đơn vị gửi QA",
        trich_yeu="Văn bản đến kiểm thử",
        loai_van_ban=VanBanDen.LoaiVanBan.CONG_VAN,
        hinh_thuc_van_ban=VanBanDen.HinhThucVanBan.CONG_VAN,
        ngay_van_ban=today,
        ngay_den=today,
        han_xu_ly=today + timedelta(days=5),
        do_mat=VanBanDen.DoMat.BINH_THUONG,
        do_khan=VanBanDen.DoKhan.BINH_THUONG,
        noi_dung_xu_ly="Trình lãnh đạo xử lý.",
        nguoi_tao=clerk,
        lanh_dao_xu_ly=leader,
        trang_thai=VanBanDen.TrangThai.CHO_XU_LY,
    )
    TepVanBanDen.objects.create(van_ban_den=incoming, loai=TepVanBanDen.LoaiTep.DINH_KEM, tep=upload("incoming.pdf"))

    incoming_other_leader = VanBanDen.objects.create(
        so_ky_hieu="QA-VBD-OTHER",
        don_vi_ban_hanh="Đơn vị gửi QA 2",
        trich_yeu="Văn bản đến của lãnh đạo khác",
        loai_van_ban=VanBanDen.LoaiVanBan.CONG_VAN,
        hinh_thuc_van_ban=VanBanDen.HinhThucVanBan.CONG_VAN,
        ngay_van_ban=today,
        ngay_den=today,
        han_xu_ly=today + timedelta(days=4),
        do_mat=VanBanDen.DoMat.BINH_THUONG,
        do_khan=VanBanDen.DoKhan.BINH_THUONG,
        noi_dung_xu_ly="Không thuộc leader chính.",
        nguoi_tao=clerk,
        lanh_dao_xu_ly=leader_2,
        trang_thai=VanBanDen.TrangThai.CHO_XU_LY,
    )

    outgoing = create_outgoing(
        "QA-VBDI-001",
        "Văn bản đi kiểm thử",
        specialist.core_profile,
        leader.core_profile,
        status=VanBan.TRANG_THAI_CHOICES[0][0],
    )
    outgoing_waiting_issue = create_outgoing(
        "QA-VBDI-ISSUE",
        "Văn bản chờ ban hành kiểm thử",
        specialist.core_profile,
        leader.core_profile,
        status=VanBan.TRANG_THAI_CHOICES[4][0],
    )
    outgoing_other_creator = create_outgoing(
        "QA-VBDI-OTHER",
        "Văn bản của chuyên viên khác",
        specialist_2.core_profile,
        leader.core_profile,
        status=VanBan.TRANG_THAI_CHOICES[0][0],
    )

    record = HoSoVanBan.objects.create(
        tieu_de_ho_so="Hồ sơ kiểm thử",
        ky_hieu_ho_so="QA-HS-001",
        nguoi_tao=clerk.core_profile,
        thoi_gian_bao_quan=HoSoVanBan.THOI_GIAN_BAO_QUAN_CHOICES[1][0],
        so_nam_luu_tru=5,
        trang_thai=HoSoVanBan.TRANG_THAI_CHOICES[0][0],
        mo_ta="Hồ sơ seed cho QA.",
    )
    PhongXemHoSo.objects.create(ho_so_van_ban=record, phong_ban=dept_chuyenvien)
    NguoiXuLyHoSo.objects.create(ho_so_van_ban=record, nguoi_xu_ly=specialist.core_profile)
    outgoing.ho_so_van_ban = record
    outgoing.save(update_fields=["ho_so_van_ban"])

    task = create_task("QA Công việc seed", leader.core_profile, specialist.core_profile)
    other_task = create_task("QA Công việc người khác", leader.core_profile, specialist_2.core_profile)

    CONTEXT.update(
        {
            "today": today,
            "branch": branch,
            "dept_admin": dept_admin,
            "dept_vanthu": dept_vanthu,
            "dept_chuyenvien": dept_chuyenvien,
            "dept_other": dept_other,
            "outside": outside,
            "admin": admin,
            "leader": leader,
            "leader_2": leader_2,
            "clerk": clerk,
            "specialist": specialist,
            "specialist_2": specialist_2,
            "invalid_role_user": invalid_role_user,
            "incoming": incoming,
            "incoming_other_leader": incoming_other_leader,
            "outgoing": outgoing,
            "outgoing_waiting_issue": outgoing_waiting_issue,
            "outgoing_other_creator": outgoing_other_creator,
            "record": record,
            "task": task,
            "other_task": other_task,
        }
    )


def create_outgoing(code, title, creator, approver, *, status=None, record=None):
    today = timezone.localdate()
    return VanBan.objects.create(
        lanh_dao_duyet=approver,
        nguoi_tao=creator,
        ho_so_van_ban=record,
        so_ky_hieu=code,
        trich_yeu=title,
        hinh_thuc=VanBan.HINH_THUC_CHOICES[0][0],
        loai_van_ban=VanBan.LOAI_VAN_BAN_CHOICES[0][0],
        don_vi_soan_thao=VanBan.DON_VI_SOAN_THAO_CHOICES[0][0],
        ngay_van_ban=today,
        ngay_den=today,
        han_xu_ly=today + timedelta(days=7),
        do_khan=VanBan.DO_KHAN_CHOICES[2][0],
        do_mat=VanBan.DO_MAT_CHOICES[0][0],
        file_dinh_kem=upload(f"{code}.pdf"),
        kich_thuoc=7,
        trang_thai=status or VanBan.TRANG_THAI_CHOICES[0][0],
        noi_dung="Nội dung kiểm thử.",
        phan_loai=VanBan.PHAN_LOAI_CHOICES[0][0],
    )


def create_task(name, assigner, assignee, *, status=None, approval=True, result=""):
    now = timezone.now()
    return CongViec.objects.create(
        ten_cong_viec=name,
        noi_dung_cong_viec=f"Nội dung {name}",
        nguon_giao=CongViec.NguonGiao.VAN_BAN_DEN,
        trang_thai=status or CongViec.TrangThai.CHO_XU_LY,
        ngay_bat_dau=timezone.localdate(),
        han_xu_ly=now + timedelta(days=3),
        ket_qua_xu_ly=result,
        ghi_chu="",
        yeu_cau_phe_duyet=approval,
        nguoi_giao=assigner,
        nguoi_thuc_hien=assignee,
    )


def run_existing_test_note():
    path = EVIDENCE_DIR / "existing_django_tests_exitcode.log"
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace").strip()
    return "Baseline test command log not found."


def tc_login_page():
    response = Client(raise_request_exception=False).get(reverse("accounts:login"))
    assert_status(response, 200)
    return pass_result("GET / returned HTTP 200 and rendered login form.")


def tc_login_success():
    response = Client(raise_request_exception=False).post(
        reverse("accounts:login"),
        {"username": "qa_clerk", "password": "StrongPassword123"},
    )
    assert_redirect_to(response, reverse("core:dashboard"))
    return pass_result("POST / redirected to /dashboard/.")


def tc_login_invalid():
    response = Client(raise_request_exception=False).post(
        reverse("accounts:login"),
        {"username": "qa_clerk", "password": "WrongPassword"},
    )
    assert_status(response, 200)
    if response.context and response.context["form"].is_valid():
        raise AssertionError("Login form unexpectedly valid with wrong password.")
    return pass_result("Invalid credentials kept user on login page with form errors.")


def tc_login_external_next_ignored():
    response = Client(raise_request_exception=False).post(
        reverse("accounts:login"),
        {"username": "qa_clerk", "password": "StrongPassword123", "next": "https://example.com/evil"},
    )
    assert_redirect_to(response, reverse("core:dashboard"))
    return pass_result("External next URL was ignored and redirected to dashboard.")


def tc_login_safe_next_honored():
    target = reverse("quanlyvanbanden:danh_sach")
    response = Client(raise_request_exception=False).post(
        reverse("accounts:login"),
        {"username": "qa_clerk", "password": "StrongPassword123", "next": target},
    )
    assert_redirect_to(response, target)
    return pass_result(f"Safe next URL honored: {target}.")


def tc_logout():
    client = login_as(CONTEXT["clerk"])
    response = client.get(reverse("accounts:logout"))
    assert_redirect_to(response, reverse("accounts:login"))
    response_after = client.get(reverse("core:dashboard"))
    expected = f"{reverse('accounts:login')}?next={reverse('core:dashboard')}"
    assert_redirect_to(response_after, expected)
    return pass_result("Logout redirected to login and protected dashboard required login again.")


def tc_dashboard_requires_login():
    response = Client(raise_request_exception=False).get(reverse("core:dashboard"))
    assert_redirect_to(response, f"{reverse('accounts:login')}?next={reverse('core:dashboard')}")
    return pass_result("Anonymous dashboard request redirected to login with next parameter.")


def tc_role_chuyenvien_denied_incoming_create():
    response = login_as(CONTEXT["specialist"]).get(reverse("quanlyvanbanden:them"))
    assert_status(response, 403)
    return pass_result("CHUYEN_VIEN received HTTP 403 on incoming create route.")


def tc_role_clerk_denied_outgoing_create():
    response = login_as(CONTEXT["clerk"]).get(reverse("quanlyvanbandi:them_van_ban_di"))
    assert_status(response, 403)
    return pass_result("VAN_THU received HTTP 403 on outgoing create route.")


def tc_role_specialist_denied_assignment_list():
    response = login_as(CONTEXT["specialist"]).get(reverse("quanlycongviec:giao_viec"))
    assert_status(response, 403)
    return pass_result("CHUYEN_VIEN received HTTP 403 on giao-viec route.")


def tc_role_clerk_denied_my_tasks():
    response = login_as(CONTEXT["clerk"]).get(reverse("quanlycongviec:xu_ly_cong_viec"))
    assert_status(response, 403)
    return pass_result("VAN_THU received HTTP 403 on xu-ly-cong-viec route.")


def tc_role_menu_specialist_task_link():
    response = login_as(CONTEXT["specialist"]).get(reverse("core:dashboard"))
    assert_status(response, 200)
    items = get_ctx(response, "sidebar_menu_items", [])
    task_items = [item for item in items if item["label"] == "Quản lý công việc"]
    if not task_items or task_items[0]["href"] != reverse("quanlycongviec:xu_ly_cong_viec"):
        raise AssertionError(f"Unexpected specialist task menu: {task_items}")
    return pass_result("Specialist sidebar task menu points to xu-ly-cong-viec.")


def tc_role_menu_leader_task_link():
    response = login_as(CONTEXT["leader"]).get(reverse("core:dashboard"))
    assert_status(response, 200)
    items = get_ctx(response, "sidebar_menu_items", [])
    task_items = [item for item in items if item["label"] == "Quản lý công việc"]
    if not task_items or task_items[0]["href"] != reverse("quanlycongviec:giao_viec"):
        raise AssertionError(f"Unexpected leader task menu: {task_items}")
    return pass_result("Leader sidebar task menu points to giao-viec.")


def tc_role_admin_top_management_menu():
    response = login_as(CONTEXT["admin"]).get(reverse("core:dashboard"))
    assert_status(response, 200)
    items = get_ctx(response, "top_menu_items", [])
    found = [item for item in items if item["label"] == "Bộ công cụ quản lý"]
    if not found or not found[0]["is_enabled"]:
        raise AssertionError(f"Admin management top menu not enabled: {items}")
    return pass_result("Admin sees enabled top menu item 'Bộ công cụ quản lý'.")


def tc_profile_menu_not_implemented():
    profile_items = [item for item in TOP_MENU_DEFINITIONS if item["label"] == "Thông tin cá nhân"]
    if profile_items and profile_items[0]["url_name"] is None:
        return not_impl_result("Menu item 'Thông tin cá nhân' has url_name=None and no route/view.")
    return fail_result("Profile menu unexpectedly has a route; testcase needs update.", "Low")


def tc_help_menu_not_implemented():
    help_items = [item for item in TOP_MENU_DEFINITIONS if item["label"] == "Hướng dẫn sử dụng"]
    if help_items and help_items[0]["url_name"] is None:
        return not_impl_result("Menu item 'Hướng dẫn sử dụng' has url_name=None and no route/view.")
    return fail_result("Help menu unexpectedly has a route; testcase needs update.", "Low")


def tc_dashboard_leader_access():
    response = login_as(CONTEXT["leader"]).get(reverse("core:dashboard"))
    assert_status(response, 200)
    metrics = get_ctx(response, "dashboard_metrics", [])
    if not metrics:
        raise AssertionError("dashboard_metrics context is empty.")
    return pass_result(f"Leader dashboard rendered with {len(metrics)} metric cards.")


def tc_dashboard_metrics_include_seed_data():
    response = login_as(CONTEXT["leader"]).get(reverse("core:dashboard"))
    assert_status(response, 200)
    metrics = get_ctx(response, "dashboard_metrics", [])
    labels = {item["label"]: item["value"] for item in metrics}
    if labels.get("Văn bản đến", 0) < 1 or labels.get("Công việc", 0) < 1:
        raise AssertionError(f"Metrics did not include seeded data: {labels}")
    return pass_result(f"Dashboard metrics include seeded incoming/task data: {labels}.")


def tc_report_page_access():
    response = login_as(CONTEXT["specialist"]).get(reverse("core:bao_cao_thong_ke"))
    assert_status(response, 200)
    return pass_result("Specialist accessed /bao-cao-thong-ke.html with HTTP 200.")


def tc_report_dynamic_data_not_implemented():
    response = login_as(CONTEXT["leader"]).get(reverse("core:bao_cao_thong_ke"))
    assert_status(response, 200)
    if not response.context or len(response.context.flatten()) <= 5:
        return not_impl_result("Report view renders static template without DB-backed statistics context.")
    return pass_result("Report view provided dynamic context.")


def tc_dashboard_unknown_role_forbidden():
    response = login_as(CONTEXT["invalid_role_user"]).get(reverse("core:dashboard"))
    assert_status(response, 403)
    return pass_result("Unknown role user received HTTP 403 on dashboard.")


def tc_incoming_clerk_list():
    response = login_as(CONTEXT["clerk"]).get(reverse("quanlyvanbanden:danh_sach"))
    assert_status(response, 200)
    return pass_result("Văn thư accessed incoming document list.")


def incoming_post_data(code="QA-VBD-CREATE", **overrides):
    today = CONTEXT["today"]
    data = {
        "so_ky_hieu": code,
        "don_vi_ban_hanh": "Đơn vị tạo mới QA",
        "trich_yeu": "Tạo văn bản đến qua QA",
        "loai_van_ban": VanBanDen.LoaiVanBan.CONG_VAN,
        "hinh_thuc_van_ban": VanBanDen.HinhThucVanBan.CONG_VAN,
        "ngay_van_ban": today.isoformat(),
        "ngay_den": today.isoformat(),
        "han_xu_ly": (today + timedelta(days=5)).isoformat(),
        "do_mat": VanBanDen.DoMat.BINH_THUONG,
        "do_khan": VanBanDen.DoKhan.BINH_THUONG,
        "noi_dung_xu_ly": "Nội dung xử lý QA",
        "lanh_dao_xu_ly": CONTEXT["leader"].pk,
    }
    data.update(overrides)
    return data


def tc_incoming_create_valid_with_file():
    before = VanBanDen.objects.count()
    response = login_as(CONTEXT["clerk"]).post(
        reverse("quanlyvanbanden:them"),
        data={
            **incoming_post_data("QA-VBD-CREATE"),
            "file_dinh_kem_files": [upload("incoming-create.pdf")],
        },
    )
    assert_redirect_to(response, reverse("quanlyvanbanden:danh_sach"))
    created = VanBanDen.objects.get(so_ky_hieu="QA-VBD-CREATE")
    if VanBanDen.objects.count() != before + 1 or created.tep_tin.count() != 1:
        raise AssertionError("Incoming document or attachment was not created.")
    return pass_result("Created incoming document with one attachment and redirected to list.")


def tc_incoming_create_missing_required():
    before = VanBanDen.objects.count()
    data = incoming_post_data("QA-VBD-MISSING")
    data["trich_yeu"] = ""
    response = login_as(CONTEXT["clerk"]).post(reverse("quanlyvanbanden:them"), data=data)
    assert_status(response, 200)
    if VanBanDen.objects.count() != before:
        raise AssertionError("Incoming document was created despite missing trich_yeu.")
    return pass_result("Missing required field kept form on page and did not create document.")


def tc_incoming_invalid_attachment_rejected():
    before = VanBanDen.objects.count()
    response = login_as(CONTEXT["clerk"]).post(
        reverse("quanlyvanbanden:them"),
        data={
            **incoming_post_data("QA-VBD-BADFILE"),
            "file_dinh_kem_files": [upload("malware.exe", b"MZ", "application/octet-stream")],
        },
    )
    created = VanBanDen.objects.filter(so_ky_hieu="QA-VBD-BADFILE").exists()
    if response.status_code == 200 and not created and VanBanDen.objects.count() == before:
        return pass_result("Invalid incoming attachment was rejected.")
    return fail_result(
        f"HTTP {response.status_code}; created={created}; VanBanDen count delta={VanBanDen.objects.count() - before}.",
        "High",
        "Invalid .exe attachment was accepted by incoming create flow.",
    )


def tc_incoming_detail_clerk():
    response = login_as(CONTEXT["clerk"]).get(reverse("quanlyvanbanden:chi_tiet", args=[CONTEXT["incoming"].pk]))
    assert_status(response, 200)
    return pass_result("Văn thư opened incoming detail page.")


def tc_incoming_search_filter():
    response = login_as(CONTEXT["clerk"]).get(reverse("quanlyvanbanden:danh_sach"), {"q": "QA-VBD-001"})
    assert_status(response, 200)
    text = response_text(response)
    if "QA-VBD-001" not in text:
        raise AssertionError("Filtered incoming list did not contain QA-VBD-001.")
    return pass_result("Search q filter returned matching incoming document.")


def tc_incoming_update_valid():
    vb = VanBanDen.objects.create(**incoming_model_kwargs("QA-VBD-EDIT", "Trước khi sửa"))
    response = login_as(CONTEXT["clerk"]).post(
        reverse("quanlyvanbanden:sua", args=[vb.pk]),
        data=incoming_post_data("QA-VBD-EDIT", trich_yeu="Sau khi sửa"),
    )
    assert_redirect_to(response, reverse("quanlyvanbanden:chi_tiet", args=[vb.pk]))
    vb.refresh_from_db()
    if vb.trich_yeu != "Sau khi sửa":
        raise AssertionError(f"trich_yeu not updated: {vb.trich_yeu}")
    return pass_result("Updated incoming document trich_yeu.")


def incoming_model_kwargs(code, title, leader=None):
    today = CONTEXT["today"]
    return {
        "so_ky_hieu": code,
        "don_vi_ban_hanh": "Đơn vị QA",
        "trich_yeu": title,
        "loai_van_ban": VanBanDen.LoaiVanBan.CONG_VAN,
        "hinh_thuc_van_ban": VanBanDen.HinhThucVanBan.CONG_VAN,
        "ngay_van_ban": today,
        "ngay_den": today,
        "han_xu_ly": today + timedelta(days=5),
        "do_mat": VanBanDen.DoMat.BINH_THUONG,
        "do_khan": VanBanDen.DoKhan.BINH_THUONG,
        "noi_dung_xu_ly": "Nội dung QA",
        "nguoi_tao": CONTEXT["clerk"],
        "lanh_dao_xu_ly": leader or CONTEXT["leader"],
        "trang_thai": VanBanDen.TrangThai.CHO_XU_LY,
    }


def tc_incoming_delete_valid():
    vb = VanBanDen.objects.create(**incoming_model_kwargs("QA-VBD-DELETE", "Văn bản để xóa"))
    response = login_as(CONTEXT["clerk"]).post(reverse("quanlyvanbanden:xoa", args=[vb.pk]))
    assert_redirect_to(response, reverse("quanlyvanbanden:danh_sach"))
    if VanBanDen.objects.filter(pk=vb.pk).exists():
        raise AssertionError("Incoming document still exists after delete.")
    return pass_result("Deleted incoming document by POST.")


def tc_incoming_leader_list_scope():
    response = login_as(CONTEXT["leader"]).get(reverse("quanlyvanbanden:danh_sach"))
    assert_status(response, 200)
    text = response_text(response)
    if "QA-VBD-001" not in text or "QA-VBD-OTHER" in text:
        raise AssertionError("Leader list did not respect lanh_dao_xu_ly scope.")
    return pass_result("Leader list only showed documents assigned to that leader.")


def tc_incoming_leader_forward():
    vb = VanBanDen.objects.create(**incoming_model_kwargs("QA-VBD-FWD", "Văn bản chuyển tiếp"))
    response = login_as(CONTEXT["leader"]).post(
        reverse("quanlyvanbanden:lanh_dao_chuyen_tiep", args=[vb.pk]),
        data={"chuyen_vien_ids": [str(CONTEXT["specialist"].pk)]},
    )
    assert_redirect_to(response, reverse("quanlyvanbanden:chi_tiet", args=[vb.pk]))
    vb.refresh_from_db()
    if vb.trang_thai != VanBanDen.TrangThai.DA_XU_LY:
        raise AssertionError(f"Unexpected status after forward: {vb.trang_thai}")
    if not VanBanDenChuyenTiep.objects.filter(van_ban_den=vb, chuyen_vien=CONTEXT["specialist"]).exists():
        raise AssertionError("Forward record was not created.")
    CONTEXT["incoming_forwarded"] = vb
    return pass_result("Leader forwarded incoming document to specialist and status changed to DA_XU_LY.")


def tc_incoming_leader_forward_without_specialist():
    vb = VanBanDen.objects.create(**incoming_model_kwargs("QA-VBD-FWD-NONE", "Văn bản thiếu chuyên viên"))
    response = login_as(CONTEXT["leader"]).post(
        reverse("quanlyvanbanden:lanh_dao_chuyen_tiep", args=[vb.pk]),
        data={},
    )
    assert_redirect_to(response, reverse("quanlyvanbanden:chi_tiet", args=[vb.pk]))
    vb.refresh_from_db()
    if vb.trang_thai != VanBanDen.TrangThai.CHO_XU_LY or vb.ds_chuyen_tiep.exists():
        raise AssertionError("Document changed despite missing chuyen_vien_ids.")
    return pass_result("Missing specialist selection did not change incoming document status.")


def tc_incoming_leader_save_readonly():
    vb = VanBanDen.objects.create(**incoming_model_kwargs("QA-VBD-SAVE", "Văn bản lưu xem để biết"))
    response = login_as(CONTEXT["leader"]).post(reverse("quanlyvanbanden:lanh_dao_luu", args=[vb.pk]))
    assert_redirect_to(response, reverse("quanlyvanbanden:chi_tiet", args=[vb.pk]))
    vb.refresh_from_db()
    if vb.trang_thai != VanBanDen.TrangThai.XEM_DE_BIET:
        raise AssertionError(f"Unexpected status: {vb.trang_thai}")
    return pass_result("Leader saved incoming document as XEM_DE_BIET.")


def tc_incoming_leader_return_requires_reason():
    vb = VanBanDen.objects.create(**incoming_model_kwargs("QA-VBD-RET-EMPTY", "Văn bản hoàn trả thiếu lý do"))
    response = login_as(CONTEXT["leader"]).post(
        reverse("quanlyvanbanden:lanh_dao_hoan_tra", args=[vb.pk]),
        data={"ly_do_hoan_tra": ""},
    )
    assert_redirect_to(response, reverse("quanlyvanbanden:chi_tiet", args=[vb.pk]))
    vb.refresh_from_db()
    if vb.trang_thai != VanBanDen.TrangThai.CHO_XU_LY:
        raise AssertionError("Empty return reason changed incoming status.")
    return pass_result("Empty return reason was rejected.")


def tc_incoming_leader_return_valid():
    vb = VanBanDen.objects.create(**incoming_model_kwargs("QA-VBD-RET", "Văn bản hoàn trả"))
    response = login_as(CONTEXT["leader"]).post(
        reverse("quanlyvanbanden:lanh_dao_hoan_tra", args=[vb.pk]),
        data={"ly_do_hoan_tra": "Cần bổ sung thông tin."},
    )
    assert_redirect_to(response, reverse("quanlyvanbanden:chi_tiet", args=[vb.pk]))
    vb.refresh_from_db()
    if vb.trang_thai != VanBanDen.TrangThai.HOAN_TRA or not vb.ngay_hoan_tra:
        raise AssertionError("Valid return did not set HOAN_TRA/ngay_hoan_tra.")
    return pass_result("Leader returned incoming document with reason.")


def tc_incoming_specialist_forwarded_detail():
    vb = CONTEXT.get("incoming_forwarded")
    if not vb:
        vb = VanBanDen.objects.create(**incoming_model_kwargs("QA-VBD-FWD-LATE", "Văn bản chuyển tiếp muộn"))
        VanBanDenChuyenTiep.objects.create(van_ban_den=vb, chuyen_vien=CONTEXT["specialist"], nguoi_chuyen=CONTEXT["leader"])
    response = login_as(CONTEXT["specialist"]).get(reverse("quanlyvanbanden:chi_tiet", args=[vb.pk]))
    assert_status(response, 200)
    return pass_result("Assigned specialist opened forwarded incoming document detail.")


def tc_incoming_specialist_unassigned_redirected():
    response = login_as(CONTEXT["specialist"]).get(reverse("quanlyvanbanden:chi_tiet", args=[CONTEXT["incoming"].pk]))
    assert_redirect_to(response, reverse("quanlyvanbanden:danh_sach"))
    return pass_result("Unassigned specialist was redirected from incoming detail to list.")


def tc_outgoing_specialist_list():
    response = login_as(CONTEXT["specialist"]).get(reverse("quanlyvanbandi:van_ban_di"))
    assert_status(response, 200)
    return pass_result("Specialist accessed outgoing list.")


def outgoing_post_data(code="QA-VBDI-CREATE", **overrides):
    today = CONTEXT["today"]
    data = {
        "so_ky_hieu": code,
        "don_vi_soan_thao": VanBan.DON_VI_SOAN_THAO_CHOICES[0][0],
        "loai_van_ban": VanBan.LOAI_VAN_BAN_CHOICES[0][0],
        "hinh_thuc": VanBan.HINH_THUC_CHOICES[0][0],
        "trich_yeu": "Tạo văn bản đi qua QA",
        "ngay_van_ban": today.isoformat(),
        "han_xu_ly": (today + timedelta(days=3)).isoformat(),
        "do_khan": VanBan.DO_KHAN_CHOICES[2][0],
        "lanh_dao_duyet": CONTEXT["leader"].core_profile.pk,
        "noi_dung": "Nội dung xử lý QA",
    }
    data.update(overrides)
    return data


def tc_outgoing_create_valid():
    before = VanBan.objects.filter(phan_loai=VanBan.PHAN_LOAI_CHOICES[0][0]).count()
    response = login_as(CONTEXT["specialist"]).post(
        reverse("quanlyvanbandi:them_van_ban_di"),
        data={**outgoing_post_data("QA-VBDI-CREATE"), "file_dinh_kem": upload("outgoing-create.pdf")},
    )
    assert_redirect_to(response, reverse("quanlyvanbandi:van_ban_di"))
    created = VanBan.objects.get(so_ky_hieu="QA-VBDI-CREATE")
    if VanBan.objects.filter(phan_loai=VanBan.PHAN_LOAI_CHOICES[0][0]).count() != before + 1:
        raise AssertionError("Outgoing document count did not increase.")
    if created.trang_thai != VanBan.TRANG_THAI_CHOICES[0][0]:
        raise AssertionError(f"Unexpected status: {created.trang_thai}")
    return pass_result("Specialist created outgoing document with PDF attachment.")


def tc_outgoing_create_deadline_validation():
    before = VanBan.objects.filter(so_ky_hieu="QA-VBDI-BAD-DATE").count()
    today = CONTEXT["today"]
    response = login_as(CONTEXT["specialist"]).post(
        reverse("quanlyvanbandi:them_van_ban_di"),
        data={
            **outgoing_post_data(
                "QA-VBDI-BAD-DATE",
                ngay_van_ban=today.isoformat(),
                han_xu_ly=today.isoformat(),
            ),
            "file_dinh_kem": upload("outgoing-bad-date.pdf"),
        },
    )
    assert_status(response, 200)
    if VanBan.objects.filter(so_ky_hieu="QA-VBDI-BAD-DATE").count() != before:
        raise AssertionError("Outgoing document was created despite invalid deadline.")
    return pass_result("Outgoing form rejected han_xu_ly <= ngay_van_ban.")


def tc_outgoing_invalid_main_file_rejected():
    before = VanBan.objects.filter(so_ky_hieu="QA-VBDI-BADFILE").count()
    response = login_as(CONTEXT["specialist"]).post(
        reverse("quanlyvanbandi:them_van_ban_di"),
        data={
            **outgoing_post_data("QA-VBDI-BADFILE"),
            "file_dinh_kem": upload("bad.exe", b"MZ", "application/octet-stream"),
        },
    )
    assert_status(response, 200)
    if VanBan.objects.filter(so_ky_hieu="QA-VBDI-BADFILE").count() != before:
        raise AssertionError("Outgoing document was created with invalid file extension.")
    return pass_result("Outgoing form rejected invalid main attachment extension.")


def tc_outgoing_detail_creator():
    response = login_as(CONTEXT["specialist"]).get(reverse("quanlyvanbandi:chi_tiet_van_ban_di", args=[CONTEXT["outgoing"].pk]))
    assert_status(response, 200)
    return pass_result("Creator opened outgoing detail page.")


def tc_outgoing_detail_non_creator_forbidden():
    response = login_as(CONTEXT["specialist"]).get(reverse("quanlyvanbandi:chi_tiet_van_ban_di", args=[CONTEXT["outgoing_other_creator"].pk]))
    assert_status(response, 403)
    return pass_result("Non-creator specialist received HTTP 403 on outgoing detail.")


def tc_outgoing_update_creator():
    vb = create_outgoing("QA-VBDI-EDIT", "Văn bản đi trước sửa", CONTEXT["specialist"].core_profile, CONTEXT["leader"].core_profile)
    response = login_as(CONTEXT["specialist"]).post(
        reverse("quanlyvanbandi:sua_van_ban_di", args=[vb.pk]),
        data=outgoing_post_data("QA-VBDI-EDIT", trich_yeu="Văn bản đi sau sửa"),
    )
    assert_redirect_to(response, reverse("quanlyvanbandi:van_ban_di"))
    vb.refresh_from_db()
    if vb.trich_yeu != "Văn bản đi sau sửa":
        raise AssertionError("Outgoing trich_yeu not updated.")
    return pass_result("Creator updated outgoing document.")


def tc_outgoing_delete_pending_by_creator():
    vb = create_outgoing("QA-VBDI-DELETE", "Văn bản đi để xóa", CONTEXT["specialist"].core_profile, CONTEXT["leader"].core_profile)
    response = login_as(CONTEXT["specialist"]).post(reverse("quanlyvanbandi:xoa_van_ban_di", args=[vb.pk]))
    assert_redirect_to(response, reverse("quanlyvanbandi:van_ban_di"))
    if VanBan.objects.filter(pk=vb.pk).exists():
        raise AssertionError("Outgoing document still exists after delete.")
    return pass_result("Creator deleted pending outgoing document.")


def tc_outgoing_leader_approve_valid():
    vb = create_outgoing("QA-VBDI-APPROVE", "Văn bản đi phê duyệt", CONTEXT["specialist"].core_profile, CONTEXT["leader"].core_profile)
    response = login_as(CONTEXT["leader"]).post(
        reverse("quanlyvanbandi:phe_duyet_van_ban_di", args=[vb.pk]),
        data={"van_thu_id": CONTEXT["clerk"].core_profile.pk, "ghi_chu": "Đồng ý."},
    )
    assert_redirect_to(response, reverse("quanlyvanbandi:chi_tiet_van_ban_di", args=[vb.pk]))
    vb.refresh_from_db()
    if vb.trang_thai != VanBan.TRANG_THAI_CHOICES[4][0]:
        raise AssertionError(f"Unexpected status after approval: {vb.trang_thai}")
    if not VanBanDuyet.objects.filter(van_ban=vb, van_thu=CONTEXT["clerk"].core_profile).exists():
        raise AssertionError("Approval record was not created.")
    return pass_result("Leader approved outgoing document and assigned clerk.")


def tc_outgoing_leader_approve_missing_clerk():
    vb = create_outgoing("QA-VBDI-APPROVE-NOCLERK", "Văn bản đi thiếu văn thư", CONTEXT["specialist"].core_profile, CONTEXT["leader"].core_profile)
    response = login_as(CONTEXT["leader"]).post(
        reverse("quanlyvanbandi:phe_duyet_van_ban_di", args=[vb.pk]),
        data={"ghi_chu": "Thiếu văn thư."},
    )
    assert_redirect_to(response, reverse("quanlyvanbandi:chi_tiet_van_ban_di", args=[vb.pk]))
    vb.refresh_from_db()
    if vb.trang_thai != VanBan.TRANG_THAI_CHOICES[0][0]:
        raise AssertionError("Approval without clerk changed status.")
    return pass_result("Approval without clerk was rejected and status stayed pending.")


def tc_outgoing_leader_return_valid():
    vb = create_outgoing("QA-VBDI-RETURN", "Văn bản đi hoàn trả", CONTEXT["specialist"].core_profile, CONTEXT["leader"].core_profile)
    response = login_as(CONTEXT["leader"]).post(
        reverse("quanlyvanbandi:hoan_tra_van_ban_di", args=[vb.pk]),
        data={"ly_do": "Cần sửa thể thức."},
    )
    assert_redirect_to(response, reverse("quanlyvanbandi:chi_tiet_van_ban_di", args=[vb.pk]))
    vb.refresh_from_db()
    if vb.trang_thai != VanBan.TRANG_THAI_CHOICES[2][0]:
        raise AssertionError(f"Unexpected return status: {vb.trang_thai}")
    if not VanBanHoanTra.objects.filter(van_ban=vb).exists():
        raise AssertionError("Return record was not created.")
    return pass_result("Leader returned outgoing document with reason.")


def tc_outgoing_issue_requires_recipient():
    vb = create_outgoing(
        "QA-VBDI-ISSUE-NORECIP",
        "Văn bản đi ban hành thiếu nơi nhận",
        CONTEXT["specialist"].core_profile,
        CONTEXT["leader"].core_profile,
        status=VanBan.TRANG_THAI_CHOICES[4][0],
    )
    response = login_as(CONTEXT["clerk"]).post(reverse("quanlyvanbandi:ban_hanh_van_ban", args=[vb.pk]), data={})
    assert_status(response, 400)
    vb.refresh_from_db()
    if vb.trang_thai != VanBan.TRANG_THAI_CHOICES[4][0]:
        raise AssertionError("Issue without recipients changed status.")
    return pass_result("Issue endpoint returned 400 when recipients were missing.")


def tc_outgoing_issue_valid_department():
    vb = create_outgoing(
        "QA-VBDI-ISSUE-VALID",
        "Văn bản đi ban hành hợp lệ",
        CONTEXT["specialist"].core_profile,
        CONTEXT["leader"].core_profile,
        status=VanBan.TRANG_THAI_CHOICES[4][0],
    )
    response = login_as(CONTEXT["clerk"]).post(
        reverse("quanlyvanbandi:ban_hanh_van_ban", args=[vb.pk]),
        data={"phong_ban_ids[]": [str(CONTEXT["dept_chuyenvien"].pk)]},
    )
    assert_status(response, 200)
    vb.refresh_from_db()
    if vb.trang_thai != VanBan.TRANG_THAI_CHOICES[5][0] or not BanHanh.objects.filter(van_ban=vb).exists():
        raise AssertionError("Valid issue did not set status/create BanHanh.")
    return pass_result("Clerk issued outgoing document to a department and got JSON ok.")


def tc_api_branches():
    response = login_as(CONTEXT["admin"]).get(reverse("quanlyvanbandi:api_chi_nhanh_phong_ban"))
    assert_status(response, 200)
    data = response.json()
    if "chi_nhanh" not in data or not data["chi_nhanh"]:
        raise AssertionError(f"Unexpected API payload: {data}")
    return pass_result("Branch API returned chi_nhanh JSON list.")


def tc_api_employees_by_department():
    response = login_as(CONTEXT["admin"]).get(
        reverse("quanlyvanbandi:api_nhan_vien_phong_ban"),
        {"phong_ban_id": CONTEXT["dept_chuyenvien"].pk},
    )
    assert_status(response, 200)
    data = response.json()
    if not any(item["email"] == CONTEXT["specialist"].email for item in data.get("nhan_vien", [])):
        raise AssertionError(f"Specialist not found in API payload: {data}")
    return pass_result("Employee API returned users for selected department.")


def tc_api_outside_unit_search():
    response = login_as(CONTEXT["admin"]).get(reverse("quanlyvanbandi:api_don_vi_ngoai"), {"q": "QA"})
    assert_status(response, 200)
    data = response.json()
    if not any(item["email"] == "qa.outside@example.com" for item in data.get("don_vi_ngoai", [])):
        raise AssertionError(f"Outside unit not found in API payload: {data}")
    return pass_result("Outside unit API search returned matching unit.")


def tc_record_list():
    response = login_as(CONTEXT["specialist"]).get(reverse("hosovanban:danh_sach"))
    assert_status(response, 200)
    return pass_result("Specialist accessed record list.")


def record_post_data(code="QA-HS-CREATE", **overrides):
    data = {
        "tieu_de_ho_so": "Hồ sơ tạo qua QA",
        "ky_hieu_ho_so": code,
        "thoi_gian_bao_quan": HoSoVanBan.THOI_GIAN_BAO_QUAN_CHOICES[1][0],
        "so_nam_luu_tru": "5",
        "mo_ta": "Mô tả hồ sơ QA",
        "phong_ban": [str(CONTEXT["dept_chuyenvien"].pk)],
        "nguoi_xu_ly": [str(CONTEXT["specialist"].core_profile.pk)],
    }
    data.update(overrides)
    return data


def tc_record_create_valid():
    before = HoSoVanBan.objects.count()
    response = login_as(CONTEXT["clerk"]).post(
        reverse("hosovanban:them_ho_so_van_ban"),
        data=record_post_data("QA-HS-CREATE"),
    )
    assert_redirect_to(response, reverse("hosovanban:danh_sach"))
    record_obj = HoSoVanBan.objects.get(ky_hieu_ho_so="QA-HS-CREATE")
    if HoSoVanBan.objects.count() != before + 1:
        raise AssertionError("Record count did not increase.")
    if not PhongXemHoSo.objects.filter(ho_so_van_ban=record_obj).exists():
        raise AssertionError("PhongXemHoSo was not created.")
    if not NguoiXuLyHoSo.objects.filter(ho_so_van_ban=record_obj).exists():
        raise AssertionError("NguoiXuLyHoSo was not created.")
    return pass_result("Clerk created record with department visibility and handler.")


def tc_record_create_non_clerk_forbidden():
    response = login_as(CONTEXT["specialist"]).get(reverse("hosovanban:them_ho_so_van_ban"))
    assert_status(response, 403)
    return pass_result("Specialist received HTTP 403 on record create route.")


def tc_record_duplicate_code_rejected():
    before = HoSoVanBan.objects.filter(ky_hieu_ho_so__iexact=CONTEXT["record"].ky_hieu_ho_so).count()
    response = login_as(CONTEXT["clerk"]).post(
        reverse("hosovanban:them_ho_so_van_ban"),
        data=record_post_data(CONTEXT["record"].ky_hieu_ho_so),
    )
    assert_status(response, 200)
    after = HoSoVanBan.objects.filter(ky_hieu_ho_so__iexact=CONTEXT["record"].ky_hieu_ho_so).count()
    if after != before:
        raise AssertionError("Duplicate record code was created.")
    return pass_result("Duplicate ky_hieu_ho_so was rejected.")


def tc_record_update_valid():
    rec = HoSoVanBan.objects.create(
        tieu_de_ho_so="Hồ sơ trước sửa",
        ky_hieu_ho_so="QA-HS-EDIT",
        nguoi_tao=CONTEXT["clerk"].core_profile,
        thoi_gian_bao_quan=HoSoVanBan.THOI_GIAN_BAO_QUAN_CHOICES[1][0],
        so_nam_luu_tru=5,
        trang_thai=HoSoVanBan.TRANG_THAI_CHOICES[0][0],
    )
    response = login_as(CONTEXT["clerk"]).post(
        reverse("hosovanban:sua", args=[rec.pk]),
        data=record_post_data("QA-HS-EDIT", tieu_de_ho_so="Hồ sơ sau sửa"),
    )
    assert_redirect_to(response, reverse("hosovanban:chi_tiet", args=[rec.pk]))
    rec.refresh_from_db()
    if rec.tieu_de_ho_so != "Hồ sơ sau sửa":
        raise AssertionError("Record title not updated.")
    return pass_result("Clerk updated record title.")


def tc_record_delete_empty_valid():
    rec = HoSoVanBan.objects.create(
        tieu_de_ho_so="Hồ sơ để xóa",
        ky_hieu_ho_so="QA-HS-DELETE",
        nguoi_tao=CONTEXT["clerk"].core_profile,
        thoi_gian_bao_quan=HoSoVanBan.THOI_GIAN_BAO_QUAN_CHOICES[1][0],
        so_nam_luu_tru=5,
        trang_thai=HoSoVanBan.TRANG_THAI_CHOICES[0][0],
    )
    response = login_as(CONTEXT["clerk"]).post(reverse("hosovanban:xoa", args=[rec.pk]))
    assert_redirect_to(response, reverse("hosovanban:danh_sach"))
    if HoSoVanBan.objects.filter(pk=rec.pk).exists():
        raise AssertionError("Empty record still exists after delete.")
    return pass_result("Clerk deleted empty record.")


def tc_record_delete_with_document_blocked():
    rec = CONTEXT["record"]
    response = login_as(CONTEXT["clerk"]).post(reverse("hosovanban:xoa", args=[rec.pk]))
    assert_redirect_to(response, reverse("hosovanban:danh_sach"))
    if not HoSoVanBan.objects.filter(pk=rec.pk).exists():
        raise AssertionError("Record with attached document was deleted.")
    return pass_result("Record containing current document was not deleted.")


def tc_record_detail_document():
    response = login_as(CONTEXT["specialist"]).get(
        reverse("hosovanban:chi_tiet_van_ban", args=[CONTEXT["record"].pk, CONTEXT["outgoing"].pk])
    )
    assert_status(response, 200)
    return pass_result("Opened document detail inside record.")


def tc_record_remove_document():
    rec = HoSoVanBan.objects.create(
        tieu_de_ho_so="Hồ sơ gỡ văn bản",
        ky_hieu_ho_so="QA-HS-REMOVE",
        nguoi_tao=CONTEXT["clerk"].core_profile,
        thoi_gian_bao_quan=HoSoVanBan.THOI_GIAN_BAO_QUAN_CHOICES[1][0],
        so_nam_luu_tru=5,
        trang_thai=HoSoVanBan.TRANG_THAI_CHOICES[0][0],
    )
    vb = create_outgoing("QA-VBDI-REMOVE-HS", "Văn bản cần gỡ khỏi hồ sơ", CONTEXT["specialist"].core_profile, CONTEXT["leader"].core_profile, record=rec)
    response = login_as(CONTEXT["clerk"]).post(reverse("hosovanban:xoa_van_ban_khoi_ho_so", args=[rec.pk, vb.pk]))
    assert_redirect_to(response, reverse("hosovanban:chi_tiet", args=[rec.pk]))
    vb.refresh_from_db()
    if vb.ho_so_van_ban_id is not None:
        raise AssertionError("Document still belongs to record after removal.")
    return pass_result("Clerk removed document from record.")


def tc_record_add_document_not_implemented():
    try:
        reverse("hosovanban:them_van_ban_vao_ho_so", args=[CONTEXT["record"].pk])
        return fail_result("Unexpected add-document-to-record URL exists; testcase needs update.", "Low")
    except NoReverseMatch:
        return not_impl_result("No URL/view exists for adding an existing document into a record.")


def tc_record_vinh_vien_storage_bug():
    before = HoSoVanBan.objects.filter(ky_hieu_ho_so="QA-HS-VINHVIEN").count()
    response = login_as(CONTEXT["clerk"]).post(
        reverse("hosovanban:them_ho_so_van_ban"),
        data=record_post_data(
            "QA-HS-VINHVIEN",
            thoi_gian_bao_quan=HoSoVanBan.THOI_GIAN_BAO_QUAN_CHOICES[3][0],
            so_nam_luu_tru="1",
        ),
    )
    created = HoSoVanBan.objects.filter(ky_hieu_ho_so="QA-HS-VINHVIEN").count() > before
    if created and response.status_code in (301, 302):
        return pass_result("Vĩnh viễn record created successfully.")
    return fail_result(
        f"HTTP {response.status_code}; created={created}; form option 'Vĩnh viễn' did not persist.",
        "Medium",
        "Record option 'Vĩnh viễn' appears selectable but create flow did not create the record.",
    )


def tc_task_leader_list():
    response = login_as(CONTEXT["leader"]).get(reverse("quanlycongviec:giao_viec"))
    assert_status(response, 200)
    return pass_result("Leader accessed assigned task list.")


def tc_task_specialist_list_scope():
    response = login_as(CONTEXT["specialist"]).get(reverse("quanlycongviec:xu_ly_cong_viec"))
    assert_status(response, 200)
    text = response_text(response)
    if "QA Công việc seed" not in text or "QA Công việc người khác" in text:
        raise AssertionError("Specialist task list did not respect assignee scope.")
    return pass_result("Specialist list only showed assigned tasks.")


def task_post_data(name="QA Công việc tạo mới", **overrides):
    today = CONTEXT["today"]
    data = {
        "ten_cv": name,
        "nguoi_thuc_hien": str(CONTEXT["specialist"].core_profile.pk),
        "nguoi_phoi_hop": "",
        "nguon_giao": CongViec.NguonGiao.VAN_BAN_DEN,
        "ngay_bat_dau": today.isoformat(),
        "han_xu_ly": (today + timedelta(days=3)).isoformat(),
        "noi_dung": "Nội dung công việc QA",
        "ghi_chu": "Ghi chú QA",
        "yeu_cau_phe_duyet": "on",
    }
    data.update(overrides)
    return data


def tc_task_add_valid():
    before = CongViec.objects.filter(ten_cong_viec="QA Công việc tạo mới").count()
    response = login_as(CONTEXT["leader"]).post(reverse("quanlycongviec:add_task"), data=task_post_data())
    assert_redirect_to(response, reverse("quanlycongviec:giao_viec"))
    after = CongViec.objects.filter(ten_cong_viec="QA Công việc tạo mới").count()
    if after != before + 1:
        raise AssertionError("Task was not created.")
    return pass_result("Leader created task via add_task.")


def tc_task_add_missing_required():
    before = CongViec.objects.count()
    response = login_as(CONTEXT["leader"]).post(
        reverse("quanlycongviec:add_task"),
        data=task_post_data("QA Công việc thiếu dữ liệu", ten_cv=""),
    )
    assert_redirect_to(response, reverse("quanlycongviec:giao_viec"))
    if CongViec.objects.count() != before:
        raise AssertionError("Task was created despite missing required title.")
    return pass_result("Missing task title was rejected.")


def tc_task_add_past_date_rejected():
    before = CongViec.objects.count()
    yesterday = CONTEXT["today"] - timedelta(days=1)
    response = login_as(CONTEXT["leader"]).post(
        reverse("quanlycongviec:add_task"),
        data=task_post_data("QA Công việc ngày quá khứ", ngay_bat_dau=yesterday.isoformat()),
    )
    assert_redirect_to(response, reverse("quanlycongviec:giao_viec"))
    if CongViec.objects.count() != before:
        raise AssertionError("Task was created with past start date.")
    return pass_result("Past start date was rejected.")


def tc_task_detail_assignee():
    response = login_as(CONTEXT["specialist"]).get(reverse("quanlycongviec:task_detail", args=[CONTEXT["task"].pk]))
    assert_status(response, 200)
    return pass_result("Assignee opened task detail.")


def tc_task_detail_unauthorized_redirect():
    response = login_as(CONTEXT["specialist_2"]).get(reverse("quanlycongviec:task_detail", args=[CONTEXT["task"].pk]))
    assert_redirect_to(response, reverse("quanlycongviec:xu_ly_cong_viec"))
    return pass_result("Unassigned specialist was redirected from task detail.")


def tc_task_edit_valid():
    task = create_task("QA Công việc trước sửa", CONTEXT["leader"].core_profile, CONTEXT["specialist"].core_profile)
    response = login_as(CONTEXT["leader"]).post(
        reverse("quanlycongviec:edit_task", args=[task.pk]),
        data=task_post_data("QA Công việc sau sửa"),
    )
    assert_redirect_to(response, reverse("quanlycongviec:task_detail", args=[task.pk]))
    task.refresh_from_db()
    if task.ten_cong_viec != "QA Công việc sau sửa":
        raise AssertionError("Task title not updated.")
    return pass_result("Leader edited pending task.")


def tc_task_delete_valid():
    task = create_task("QA Công việc để xóa", CONTEXT["leader"].core_profile, CONTEXT["specialist"].core_profile)
    response = login_as(CONTEXT["leader"]).post(reverse("quanlycongviec:delete_task", args=[task.pk]))
    assert_redirect_to(response, reverse("quanlycongviec:giao_viec"))
    if CongViec.objects.filter(pk=task.pk).exists():
        raise AssertionError("Task still exists after delete.")
    return pass_result("Leader deleted pending task.")


def tc_task_process_without_approval_completed():
    task = create_task(
        "QA Công việc không cần duyệt",
        CONTEXT["leader"].core_profile,
        CONTEXT["specialist"].core_profile,
        approval=False,
    )
    response = login_as(CONTEXT["specialist"]).post(
        reverse("quanlycongviec:process_task", args=[task.pk]),
        data={
            "ket_qua_xu_ly": "Đã xử lý xong.",
            "ghi_chu": "OK",
            "tep_ket_qua": upload("ket-qua.docx", b"docx"),
        },
    )
    assert_redirect_to(response, reverse("quanlycongviec:task_detail", args=[task.pk]))
    task.refresh_from_db()
    if task.trang_thai != CongViec.TrangThai.DA_HOAN_THANH:
        raise AssertionError(f"Unexpected task status: {task.trang_thai}")
    return pass_result("Processing task without approval marked it completed.")


def tc_task_process_with_approval_waiting():
    task = create_task("QA Công việc chờ duyệt", CONTEXT["leader"].core_profile, CONTEXT["specialist"].core_profile, approval=True)
    response = login_as(CONTEXT["specialist"]).post(
        reverse("quanlycongviec:process_task", args=[task.pk]),
        data={
            "ket_qua_xu_ly": "Đã xử lý chờ duyệt.",
            "ghi_chu": "",
            "tep_ket_qua": upload("ket-qua.pdf", b"%PDF-1.4"),
        },
    )
    assert_redirect_to(response, reverse("quanlycongviec:task_detail", args=[task.pk]))
    task.refresh_from_db()
    if task.trang_thai != CongViec.TrangThai.CHO_DUYET:
        raise AssertionError(f"Unexpected task status: {task.trang_thai}")
    return pass_result("Processing task with approval moved it to CHO_DUYET.")


def tc_task_process_requires_result_file():
    task = create_task("QA Công việc thiếu file", CONTEXT["leader"].core_profile, CONTEXT["specialist"].core_profile)
    response = login_as(CONTEXT["specialist"]).post(
        reverse("quanlycongviec:process_task", args=[task.pk]),
        data={"ket_qua_xu_ly": "Có mô tả nhưng thiếu file.", "ghi_chu": ""},
    )
    assert_status(response, 200)
    task.refresh_from_db()
    if task.trang_thai != CongViec.TrangThai.CHO_XU_LY:
        raise AssertionError("Task status changed despite missing result file.")
    return pass_result("ProcessTaskForm required at least one result file.")


def tc_task_process_invalid_result_file():
    task = create_task("QA Công việc file sai loại", CONTEXT["leader"].core_profile, CONTEXT["specialist"].core_profile)
    response = login_as(CONTEXT["specialist"]).post(
        reverse("quanlycongviec:process_task", args=[task.pk]),
        data={"ket_qua_xu_ly": "Có file sai loại.", "ghi_chu": "", "tep_ket_qua": upload("bad.txt", b"bad", "text/plain")},
    )
    assert_status(response, 200)
    task.refresh_from_db()
    if task.trang_thai != CongViec.TrangThai.CHO_XU_LY:
        raise AssertionError("Task status changed despite invalid result file.")
    return pass_result("Invalid result file extension was rejected.")


def tc_task_update_result_deletes_only_result_file():
    task = create_task(
        "QA Công việc cập nhật kết quả",
        CONTEXT["leader"].core_profile,
        CONTEXT["specialist"].core_profile,
        status=CongViec.TrangThai.HOAN_TRA_CV,
        result="Kết quả ban đầu.",
    )
    original = FileCVLienQuan.objects.create(
        cong_viec=task,
        file_van_ban=upload("original.pdf", b"%PDF-1.4"),
        kich_thuoc=8,
        loai_file=FileCVLienQuan.LoaiFile.CHINH,
        nguon_tai_len=FileCVLienQuan.NguonTaiLen.GIAO_VIEC,
        nguoi_tai_len=CONTEXT["leader"].core_profile,
    )
    result_file = FileCVLienQuan.objects.create(
        cong_viec=task,
        file_van_ban=upload("result.xlsx", b"xlsx"),
        kich_thuoc=4,
        loai_file=FileCVLienQuan.LoaiFile.LIEN_QUAN,
        nguon_tai_len=FileCVLienQuan.NguonTaiLen.KET_QUA_XU_LY,
        nguoi_tai_len=CONTEXT["specialist"].core_profile,
    )
    response = login_as(CONTEXT["specialist"]).post(
        reverse("quanlycongviec:update_task_result", args=[task.pk]),
        data={
            "ket_qua_xu_ly": "Kết quả cập nhật.",
            "ghi_chu": "Đã sửa.",
            "delete_file_ids": f"{original.pk},{result_file.pk}",
        },
    )
    assert_redirect_to(response, reverse("quanlycongviec:task_detail", args=[task.pk]))
    if not FileCVLienQuan.objects.filter(pk=original.pk).exists():
        raise AssertionError("Original assignment file was deleted.")
    if FileCVLienQuan.objects.filter(pk=result_file.pk).exists():
        raise AssertionError("Result file was not deleted.")
    return pass_result("Update result deleted only assignee's result file and kept original file.")


def tc_task_specialist_return_to_leader():
    task = create_task("QA Công việc trả lãnh đạo", CONTEXT["leader"].core_profile, CONTEXT["specialist"].core_profile)
    response = login_as(CONTEXT["specialist"]).post(
        reverse("quanlycongviec:return_task", args=[task.pk]),
        data={"noi_dung": "Thiếu dữ liệu đầu vào."},
    )
    assert_redirect_to(response, reverse("quanlycongviec:task_detail", args=[task.pk]))
    task.refresh_from_db()
    if task.trang_thai != CongViec.TrangThai.HOAN_TRA_LD:
        raise AssertionError(f"Unexpected task status: {task.trang_thai}")
    if not HoanTraCongViec.objects.filter(cong_viec=task, nguoi_hoan_tra=CONTEXT["specialist"].core_profile).exists():
        raise AssertionError("Return record was not created.")
    return pass_result("Specialist returned task to leader.")


def tc_task_leader_return_to_specialist():
    task = create_task(
        "QA Công việc trả chuyên viên",
        CONTEXT["leader"].core_profile,
        CONTEXT["specialist"].core_profile,
        status=CongViec.TrangThai.CHO_DUYET,
        result="Đã nộp kết quả.",
    )
    response = login_as(CONTEXT["leader"]).post(
        reverse("quanlycongviec:return_task", args=[task.pk]),
        data={"noi_dung": "Bổ sung số liệu."},
    )
    assert_redirect_to(response, reverse("quanlycongviec:task_detail", args=[task.pk]))
    task.refresh_from_db()
    if task.trang_thai != CongViec.TrangThai.HOAN_TRA_CV:
        raise AssertionError(f"Unexpected task status: {task.trang_thai}")
    return pass_result("Leader returned waiting-review task to specialist.")


def tc_task_leader_approve_waiting():
    task = create_task(
        "QA Công việc duyệt hoàn thành",
        CONTEXT["leader"].core_profile,
        CONTEXT["specialist"].core_profile,
        status=CongViec.TrangThai.CHO_DUYET,
        result="Đã hoàn tất.",
    )
    response = login_as(CONTEXT["leader"]).post(reverse("quanlycongviec:approve_task", args=[task.pk]))
    assert_redirect_to(response, reverse("quanlycongviec:task_detail", args=[task.pk]))
    task.refresh_from_db()
    if task.trang_thai != CongViec.TrangThai.DA_HOAN_THANH:
        raise AssertionError(f"Unexpected task status: {task.trang_thai}")
    if not PheDuyetCongViec.objects.filter(cong_viec=task).exists():
        raise AssertionError("Approval record was not created.")
    return pass_result("Leader approved waiting-review task.")


def tc_task_api_manager_json():
    response = login_as(CONTEXT["leader"]).get(reverse("quanlycongviec:get_task_detail", args=[CONTEXT["task"].pk]))
    assert_status(response, 200)
    data = response.json()
    if data.get("id") != CONTEXT["task"].pk:
        raise AssertionError(f"Unexpected task API payload: {data}")
    return pass_result("Task detail API returned JSON for task manager.")


def tc_task_api_not_manager_forbidden():
    response = login_as(CONTEXT["specialist"]).get(reverse("quanlycongviec:get_task_detail", args=[CONTEXT["task"].pk]))
    assert_status(response, 403)
    return pass_result("Task detail API returned 403 for non-manager.")


def tc_task_start_redirects_to_process():
    task = create_task("QA Công việc start route", CONTEXT["leader"].core_profile, CONTEXT["specialist"].core_profile)
    response = login_as(CONTEXT["specialist"]).get(reverse("quanlycongviec:start_task", args=[task.pk]))
    assert_redirect_to(response, reverse("quanlycongviec:process_task", args=[task.pk]))
    return pass_result("Start route redirected assignee to process form.")


def register_cases():
    add_case("TC-AUTH-001", "Authentication", "Login page", "Anonymous", "High", "Project test DB ready", "GET /", "None", "Login page returns 200", "/", "CustomerLoginForm", "apps/accounts/views.py:login_view; apps/accounts/urls.py", tc_login_page)
    add_case("TC-AUTH-002", "Authentication", "Login success", "Văn thư", "Critical", "User qa_clerk exists", "POST / with valid username/password", "qa_clerk / StrongPassword123", "Redirect to dashboard", "/", "CustomerLoginForm, Customer", "apps/accounts/views.py:login_view", tc_login_success)
    add_case("TC-AUTH-003", "Authentication", "Login invalid password", "Văn thư", "High", "User qa_clerk exists", "POST / with wrong password", "qa_clerk / WrongPassword", "Stay on login page with form error", "/", "CustomerLoginForm", "apps/accounts/forms.py:CustomerLoginForm", tc_login_invalid)
    add_case("TC-AUTH-004", "Authentication", "External next URL", "Văn thư", "High", "User qa_clerk exists", "POST / with next=https://example.com/evil", "External next URL", "Ignore external URL and redirect dashboard", "/", "CustomerLoginForm", "apps/accounts/views.py:_get_safe_redirect_url", tc_login_external_next_ignored)
    add_case("TC-AUTH-005", "Authentication", "Safe next URL", "Văn thư", "High", "User qa_clerk exists", "POST / with next=/van-ban-den/", "Safe internal next URL", "Redirect to safe next URL", "/", "CustomerLoginForm", "apps/accounts/views.py:_get_safe_redirect_url", tc_login_safe_next_honored)
    add_case("TC-AUTH-006", "Authentication", "Logout", "Văn thư", "High", "Logged in as qa_clerk", "GET /logout/ then GET /dashboard/", "None", "Redirect login and session cleared", "/logout/", "Customer", "apps/accounts/views.py:logout_view", tc_logout)
    add_case("TC-AUTH-007", "Authentication", "Protected redirect", "Anonymous", "Critical", "Not logged in", "GET /dashboard/", "None", "Redirect to login with next", "/dashboard/", "Customer", "apps/core/views.py:dashboard; apps/accounts/decorators.py:role_required", tc_dashboard_requires_login)

    add_case("TC-ROLE-001", "Role/Permission", "Block incoming create", "Chuyên viên", "High", "Logged in as specialist", "GET /van-ban-den/them/", "None", "HTTP 403", "/van-ban-den/them/", "VanBanDenForm", "apps/quanlyvanbanden/views.py:them_van_ban_den", tc_role_chuyenvien_denied_incoming_create)
    add_case("TC-ROLE-002", "Role/Permission", "Block outgoing create", "Văn thư", "High", "Logged in as clerk", "GET /van-ban-di/them/", "None", "HTTP 403", "/van-ban-di/them/", "VanBanDiForm", "apps/quanlyvanbandi/views.py:van_ban_di_edit", tc_role_clerk_denied_outgoing_create)
    add_case("TC-ROLE-003", "Role/Permission", "Block assignment list", "Chuyên viên", "High", "Logged in as specialist", "GET /giao-viec.html", "None", "HTTP 403", "/giao-viec.html", "CongViec", "apps/quanlycongviec/views.py:giao_viec", tc_role_specialist_denied_assignment_list)
    add_case("TC-ROLE-004", "Role/Permission", "Block specialist task list", "Văn thư", "High", "Logged in as clerk", "GET /xu-ly-cong-viec.html", "None", "HTTP 403", "/xu-ly-cong-viec.html", "CongViec", "apps/quanlycongviec/views.py:xu_ly_cong_viec", tc_role_clerk_denied_my_tasks)
    add_case("TC-ROLE-005", "Role/Permission", "Specialist menu", "Chuyên viên", "Medium", "Logged in as specialist", "GET dashboard and inspect sidebar_menu_items", "None", "Task menu links to xu_ly_cong_viec", "core:dashboard", "auth_shell context", "apps/core/context_processors.py:SIDEBAR_MENU_DEFINITIONS", tc_role_menu_specialist_task_link)
    add_case("TC-ROLE-006", "Role/Permission", "Leader menu", "Lãnh đạo", "Medium", "Logged in as leader", "GET dashboard and inspect sidebar_menu_items", "None", "Task menu links to giao_viec", "core:dashboard", "auth_shell context", "apps/core/context_processors.py:SIDEBAR_MENU_DEFINITIONS", tc_role_menu_leader_task_link)
    add_case("TC-ROLE-007", "Role/Permission", "Admin top menu", "Admin", "Low", "Logged in as admin", "GET dashboard and inspect top_menu_items", "None", "Admin sees enabled management menu", "core:dashboard", "auth_shell context", "apps/core/context_processors.py:TOP_MENU_DEFINITIONS", tc_role_admin_top_management_menu)
    add_case("TC-ROLE-008", "Role/Permission", "Profile menu route", "All roles", "Low", "Menu item exists", "Inspect TOP_MENU_DEFINITIONS", "None", "Profile route should be implemented or marked disabled", "url_name=None", "auth_shell context", "apps/core/context_processors.py:TOP_MENU_DEFINITIONS", tc_profile_menu_not_implemented)
    add_case("TC-ROLE-009", "Role/Permission", "Help menu route", "All roles", "Low", "Menu item exists", "Inspect TOP_MENU_DEFINITIONS", "None", "Help route should be implemented or marked disabled", "url_name=None", "auth_shell context", "apps/core/context_processors.py:TOP_MENU_DEFINITIONS", tc_help_menu_not_implemented)

    add_case("TC-DASH-001", "Dashboard", "Leader dashboard access", "Lãnh đạo", "High", "Logged in as leader", "GET /dashboard/", "Seeded docs/tasks", "HTTP 200 with dashboard metrics", "/dashboard/", "VanBanDen, VanBan, CongViec, HoSoVanBan", "apps/core/views.py:dashboard", tc_dashboard_leader_access)
    add_case("TC-DASH-002", "Dashboard", "Dashboard metrics", "Lãnh đạo", "Medium", "Seeded incoming/task exists", "GET dashboard and inspect dashboard_metrics", "Seeded VanBanDen/CongViec", "Metrics include seeded data", "/dashboard/", "VanBanDen, CongViec", "apps/core/views.py:_dashboard_metrics", tc_dashboard_metrics_include_seed_data)
    add_case("TC-DASH-003", "Báo cáo thống kê", "Report page access", "Chuyên viên", "Medium", "Logged in as specialist", "GET /bao-cao-thong-ke.html", "None", "HTTP 200", "/bao-cao-thong-ke.html", "Template bao-cao-thong-ke.html", "apps/core/views.py:bao_cao_thong_ke", tc_report_page_access)
    add_case("TC-DASH-004", "Báo cáo thống kê", "Dynamic report data", "Lãnh đạo", "Low", "Report route exists", "GET report and inspect context", "Seeded data", "Report should have DB-backed statistics context", "/bao-cao-thong-ke.html", "VanBanDen, VanBan, CongViec", "apps/core/views.py:bao_cao_thong_ke", tc_report_dynamic_data_not_implemented)
    add_case("TC-DASH-005", "Dashboard", "Unknown role blocked", "UNKNOWN", "High", "User role set to UNKNOWN", "GET /dashboard/", "qa_invalid_role", "HTTP 403", "/dashboard/", "Customer.role", "apps/accounts/decorators.py:role_required", tc_dashboard_unknown_role_forbidden)

    add_case("TC-VBDEN-001", "Văn bản đến", "List", "Văn thư", "High", "Logged in as clerk", "GET /van-ban-den/", "Seeded incoming document", "HTTP 200", "/van-ban-den/", "VanBanDen", "apps/quanlyvanbanden/views.py:danh_sach_van_ban_den", tc_incoming_clerk_list)
    add_case("TC-VBDEN-002", "Văn bản đến", "Create valid", "Văn thư", "Critical", "Leader exists", "POST /van-ban-den/them/ with required fields and PDF", "QA-VBD-CREATE + incoming-create.pdf", "Document and attachment created", "/van-ban-den/them/", "VanBanDenForm, TepVanBanDen", "apps/quanlyvanbanden/views.py:them_van_ban_den", tc_incoming_create_valid_with_file)
    add_case("TC-VBDEN-003", "Văn bản đến", "Create missing required", "Văn thư", "High", "Leader exists", "POST missing trich_yeu", "trich_yeu=''", "Form rejects and no create", "/van-ban-den/them/", "VanBanDenForm", "apps/quanlyvanbanden/forms.py:VanBanDenForm", tc_incoming_create_missing_required)
    add_case("TC-VBDEN-004", "Văn bản đến", "Reject invalid attachment", "Văn thư", "High", "TepVanBanDen has FileExtensionValidator", "POST /van-ban-den/them/ with malware.exe", "malware.exe", "Invalid extension rejected and no document created", "/van-ban-den/them/", "TepVanBanDen.tep", "apps/quanlyvanbanden/models.py:TepVanBanDen; apps/quanlyvanbanden/views.py:them_van_ban_den", tc_incoming_invalid_attachment_rejected, "Văn bản đến accepts invalid attachment extension", "TepVanBanDen.tep validator is bypassed because view creates TepVanBanDen.objects.create(...) without form/full_clean validation.")
    add_case("TC-VBDEN-005", "Văn bản đến", "Detail", "Văn thư", "High", "Seeded incoming document", "GET /van-ban-den/<pk>/", "QA-VBD-001", "HTTP 200", "/van-ban-den/<pk>/", "VanBanDen, TepVanBanDen", "apps/quanlyvanbanden/views.py:chi_tiet_van_ban_den", tc_incoming_detail_clerk)
    add_case("TC-VBDEN-006", "Văn bản đến", "Search", "Văn thư", "Medium", "Seeded incoming document", "GET /van-ban-den/?q=QA-VBD-001", "q=QA-VBD-001", "Matching document displayed", "/van-ban-den/?q=", "VanBanDen", "apps/quanlyvanbanden/views.py:danh_sach_van_ban_den", tc_incoming_search_filter)
    add_case("TC-VBDEN-007", "Văn bản đến", "Update", "Văn thư", "High", "Incoming document exists", "POST /van-ban-den/<pk>/sua/", "Updated trich_yeu", "Document updated", "/van-ban-den/<pk>/sua/", "VanBanDenForm", "apps/quanlyvanbanden/views.py:sua_van_ban_den", tc_incoming_update_valid)
    add_case("TC-VBDEN-008", "Văn bản đến", "Delete", "Văn thư", "High", "Incoming document exists", "POST /van-ban-den/<pk>/xoa/", "QA-VBD-DELETE", "Document deleted", "/van-ban-den/<pk>/xoa/", "VanBanDen", "apps/quanlyvanbanden/views.py:xoa_van_ban_den", tc_incoming_delete_valid)
    add_case("TC-VBDEN-009", "Văn bản đến", "Leader list scope", "Lãnh đạo", "High", "Documents assigned to different leaders", "GET /van-ban-den/ as leader", "QA-VBD-001 and QA-VBD-OTHER", "Only assigned docs visible", "/van-ban-den/", "VanBanDen.lanh_dao_xu_ly", "apps/quanlyvanbanden/views.py:danh_sach_van_ban_den", tc_incoming_leader_list_scope)
    add_case("TC-VBDEN-010", "Văn bản đến", "Forward to specialist", "Lãnh đạo", "Critical", "Leader owns incoming document", "POST /van-ban-den/<pk>/chuyen-tiep/", "chuyen_vien_ids=[specialist]", "Forward record created; status DA_XU_LY", "/van-ban-den/<pk>/chuyen-tiep/", "VanBanDenChuyenTiep", "apps/quanlyvanbanden/views.py:lanh_dao_chuyen_tiep_van_ban_den", tc_incoming_leader_forward)
    add_case("TC-VBDEN-011", "Văn bản đến", "Forward missing specialist", "Lãnh đạo", "Medium", "Leader owns incoming document", "POST chuyen-tiep without chuyen_vien_ids", "No specialist selected", "No status/forward change", "/van-ban-den/<pk>/chuyen-tiep/", "VanBanDenChuyenTiep", "apps/quanlyvanbanden/views.py:lanh_dao_chuyen_tiep_van_ban_den", tc_incoming_leader_forward_without_specialist)
    add_case("TC-VBDEN-012", "Văn bản đến", "Save as read-only", "Lãnh đạo", "Medium", "Leader owns incoming document", "POST /van-ban-den/<pk>/luu/", "None", "Status XEM_DE_BIET", "/van-ban-den/<pk>/luu/", "VanBanDen.trang_thai", "apps/quanlyvanbanden/views.py:lanh_dao_luu_van_ban_den", tc_incoming_leader_save_readonly)
    add_case("TC-VBDEN-013", "Văn bản đến", "Return requires reason", "Lãnh đạo", "High", "Leader owns incoming document", "POST hoan-tra with empty reason", "ly_do_hoan_tra=''", "Status unchanged", "/van-ban-den/<pk>/hoan-tra/", "VanBanDen.ly_do_hoan_tra", "apps/quanlyvanbanden/views.py:lanh_dao_hoan_tra_van_ban_den", tc_incoming_leader_return_requires_reason)
    add_case("TC-VBDEN-014", "Văn bản đến", "Return valid", "Lãnh đạo", "High", "Leader owns incoming document", "POST hoan-tra with reason", "Cần bổ sung thông tin", "Status HOAN_TRA and date set", "/van-ban-den/<pk>/hoan-tra/", "VanBanDen.trang_thai", "apps/quanlyvanbanden/views.py:lanh_dao_hoan_tra_van_ban_den", tc_incoming_leader_return_valid)
    add_case("TC-VBDEN-015", "Văn bản đến", "Specialist detail assigned", "Chuyên viên", "High", "Incoming forwarded to specialist", "GET /van-ban-den/<pk>/", "Forwarded document", "HTTP 200", "/van-ban-den/<pk>/", "VanBanDenChuyenTiep", "apps/quanlyvanbanden/views.py:chi_tiet_van_ban_den", tc_incoming_specialist_forwarded_detail)
    add_case("TC-VBDEN-016", "Văn bản đến", "Specialist detail unassigned", "Chuyên viên", "High", "Incoming not forwarded to specialist", "GET /van-ban-den/<pk>/", "Unassigned document", "Redirect to list", "/van-ban-den/<pk>/", "VanBanDenChuyenTiep", "apps/quanlyvanbanden/views.py:chi_tiet_van_ban_den", tc_incoming_specialist_unassigned_redirected)

    add_case("TC-VBDI-001", "Văn bản đi", "List", "Chuyên viên", "High", "Logged in as specialist", "GET /van-ban-di/", "Seeded outgoing docs", "HTTP 200", "/van-ban-di/", "VanBan", "apps/quanlyvanbandi/views.py:van_ban_di", tc_outgoing_specialist_list)
    add_case("TC-VBDI-002", "Văn bản đi", "Create valid", "Chuyên viên", "Critical", "Leader core profile exists", "POST /van-ban-di/them/ with PDF", "QA-VBDI-CREATE", "Outgoing document created", "/van-ban-di/them/", "VanBanDiForm, VanBan", "apps/quanlyvanbandi/views.py:van_ban_di_edit", tc_outgoing_create_valid)
    add_case("TC-VBDI-003", "Văn bản đi", "Deadline validation", "Chuyên viên", "High", "Leader core profile exists", "POST han_xu_ly <= ngay_van_ban", "Same date", "Form rejects and no create", "/van-ban-di/them/", "VanBanDiForm.clean", "apps/quanlyvanbandi/forms.py:VanBanDiForm.clean", tc_outgoing_create_deadline_validation)
    add_case("TC-VBDI-004", "Văn bản đi", "Invalid main file", "Chuyên viên", "High", "Leader core profile exists", "POST .exe file", "bad.exe", "Form rejects and no create", "/van-ban-di/them/", "VanBanDiForm.clean_file_dinh_kem", "apps/quanlyvanbandi/forms.py:validate_file_extension", tc_outgoing_invalid_main_file_rejected)
    add_case("TC-VBDI-005", "Văn bản đi", "Detail creator", "Chuyên viên", "High", "Outgoing document created by specialist", "GET /van-ban-di/<id>/", "QA-VBDI-001", "HTTP 200", "/van-ban-di/<id>/", "VanBan", "apps/quanlyvanbandi/views.py:chi_tiet_van_ban_di", tc_outgoing_detail_creator)
    add_case("TC-VBDI-006", "Văn bản đi", "Detail non-creator", "Chuyên viên", "High", "Outgoing document created by another specialist", "GET /van-ban-di/<id>/", "QA-VBDI-OTHER", "HTTP 403", "/van-ban-di/<id>/", "VanBan.nguoi_tao", "apps/quanlyvanbandi/views.py:chi_tiet_van_ban_di", tc_outgoing_detail_non_creator_forbidden)
    add_case("TC-VBDI-007", "Văn bản đi", "Update", "Chuyên viên", "High", "Outgoing pending document exists", "POST /van-ban-di/<pk>/sua/", "Updated trich_yeu", "Document updated", "/van-ban-di/<pk>/sua/", "VanBanDiForm", "apps/quanlyvanbandi/views.py:van_ban_di_edit", tc_outgoing_update_creator)
    add_case("TC-VBDI-008", "Văn bản đi", "Delete", "Chuyên viên", "High", "Outgoing pending document exists", "POST /van-ban-di/<pk>/xoa/", "QA-VBDI-DELETE", "Document deleted", "/van-ban-di/<pk>/xoa/", "VanBan", "apps/quanlyvanbandi/views.py:xoa_van_ban_di", tc_outgoing_delete_pending_by_creator)
    add_case("TC-VBDI-009", "Văn bản đi", "Approve", "Lãnh đạo", "Critical", "Leader is assigned approver", "POST /van-ban-di/<pk>/phe-duyet/", "van_thu_id + ghi_chu", "Status Chờ ban hành; VanBanDuyet created", "/van-ban-di/<pk>/phe-duyet/", "VanBanDuyet", "apps/quanlyvanbandi/views.py:phe_duyet_van_ban_di", tc_outgoing_leader_approve_valid)
    add_case("TC-VBDI-010", "Văn bản đi", "Approve missing clerk", "Lãnh đạo", "High", "Leader is assigned approver", "POST phe-duyet without van_thu_id", "No van_thu_id", "Status unchanged", "/van-ban-di/<pk>/phe-duyet/", "VanBanDuyet", "apps/quanlyvanbandi/views.py:phe_duyet_van_ban_di", tc_outgoing_leader_approve_missing_clerk)
    add_case("TC-VBDI-011", "Văn bản đi", "Return", "Lãnh đạo", "High", "Leader is assigned approver", "POST /van-ban-di/<pk>/hoan-tra/", "ly_do", "Status Hoàn Trả; VanBanHoanTra created", "/van-ban-di/<pk>/hoan-tra/", "VanBanHoanTra", "apps/quanlyvanbandi/views.py:hoan_tra_van_ban_di", tc_outgoing_leader_return_valid)
    add_case("TC-VBDI-012", "Văn bản đi", "Issue requires recipient", "Văn thư", "High", "Document is Chờ ban hành", "POST ban-hanh without recipients", "No recipient arrays", "HTTP 400 and status unchanged", "/van-ban-di/<pk>/ban-hanh/", "BanHanh", "apps/quanlyvanbandi/views.py:ban_hanh_van_ban", tc_outgoing_issue_requires_recipient)
    add_case("TC-VBDI-013", "Văn bản đi", "Issue valid", "Văn thư", "Critical", "Document is Chờ ban hành", "POST ban-hanh with phong_ban_ids[]", "dept_chuyenvien", "JSON ok; status Đã ban hành; BanHanh created", "/van-ban-di/<pk>/ban-hanh/", "BanHanh, BanHanhChiTiep", "apps/quanlyvanbandi/views.py:ban_hanh_van_ban", tc_outgoing_issue_valid_department)
    add_case("TC-API-001", "API", "Branches API", "Admin", "Medium", "Branch exists", "GET /api/chi-nhanh-phong-ban/", "None", "JSON chi_nhanh list", "/api/chi-nhanh-phong-ban/", "ChiNhanh, PhongBan", "apps/quanlyvanbandi/views.py:api_chi_nhanh_phong_ban", tc_api_branches)
    add_case("TC-API-002", "API", "Employees API", "Admin", "Medium", "Department and users exist", "GET /api/nhan-vien/?phong_ban_id=<id>", "dept_chuyenvien", "JSON nhan_vien list", "/api/nhan-vien/", "NguoiDung", "apps/quanlyvanbandi/views.py:api_nhan_vien_phong_ban", tc_api_employees_by_department)
    add_case("TC-API-003", "API", "Outside unit API", "Admin", "Medium", "Outside unit exists", "GET /api/don-vi-ngoai/?q=QA", "q=QA", "JSON don_vi_ngoai list", "/api/don-vi-ngoai/", "DonViNgoai", "apps/quanlyvanbandi/views.py:api_don_vi_ngoai", tc_api_outside_unit_search)

    add_case("TC-HOSO-001", "Hồ sơ văn bản", "List", "Chuyên viên", "High", "Logged in as specialist", "GET /hosovanban/ho-so-van-ban.html", "Seeded record", "HTTP 200", "/hosovanban/ho-so-van-ban.html", "HoSoVanBan", "apps/hosovanban/views.py:danh_sach", tc_record_list)
    add_case("TC-HOSO-002", "Hồ sơ văn bản", "Create valid", "Văn thư", "Critical", "PhongBan and NguoiDung exist", "POST create record", "QA-HS-CREATE", "Record, PhongXemHoSo, NguoiXuLyHoSo created", "/hosovanban/them-ho-so-van-ban.html", "HoSoVanBanCreateForm", "apps/hosovanban/views.py:them_ho_so_van_ban", tc_record_create_valid)
    add_case("TC-HOSO-003", "Hồ sơ văn bản", "Create forbidden", "Chuyên viên", "High", "Logged in as specialist", "GET create record page", "None", "HTTP 403", "/hosovanban/them-ho-so-van-ban.html", "HoSoVanBanCreateForm", "apps/hosovanban/views.py:them_ho_so_van_ban", tc_record_create_non_clerk_forbidden)
    add_case("TC-HOSO-004", "Hồ sơ văn bản", "Duplicate code validation", "Văn thư", "High", "Record QA-HS-001 exists", "POST create with duplicate ky_hieu_ho_so", "QA-HS-001", "Form rejects duplicate", "/hosovanban/them-ho-so-van-ban.html", "HoSoVanBanCreateForm.clean_ky_hieu_ho_so", "apps/hosovanban/forms.py:HoSoVanBanCreateForm", tc_record_duplicate_code_rejected)
    add_case("TC-HOSO-005", "Hồ sơ văn bản", "Update", "Văn thư", "High", "Record exists", "POST /hosovanban/sua/<pk>/", "Updated tieu_de_ho_so", "Record updated", "/hosovanban/sua/<pk>/", "HoSoVanBanUpdateForm", "apps/hosovanban/views.py:sua_ho_so_van_ban", tc_record_update_valid)
    add_case("TC-HOSO-006", "Hồ sơ văn bản", "Delete empty", "Văn thư", "High", "Empty current record exists", "POST /hosovanban/xoa/<pk>/", "QA-HS-DELETE", "Record deleted", "/hosovanban/xoa/<pk>/", "HoSoVanBan", "apps/hosovanban/views.py:xoa_ho_so_van_ban", tc_record_delete_empty_valid)
    add_case("TC-HOSO-007", "Hồ sơ văn bản", "Delete record with document", "Văn thư", "High", "Record has VanBan", "POST delete record", "QA-HS-001 contains QA-VBDI-001", "Record not deleted", "/hosovanban/xoa/<pk>/", "HoSoVanBan, VanBan", "apps/hosovanban/views.py:xoa_ho_so_van_ban", tc_record_delete_with_document_blocked)
    add_case("TC-HOSO-008", "Hồ sơ văn bản", "Document detail inside record", "Chuyên viên", "Medium", "Record has VanBan", "GET /hosovanban/chi-tiet/<ho_so>/van-ban/<vb>/", "QA-HS-001 + QA-VBDI-001", "HTTP 200", "/hosovanban/chi-tiet/<ho_so>/van-ban/<vb>/", "VanBan, VanBanLienQuan", "apps/hosovanban/views.py:chi_tiet_van_ban_trong_ho_so", tc_record_detail_document)
    add_case("TC-HOSO-009", "Hồ sơ văn bản", "Remove document from record", "Văn thư", "High", "Record has VanBan", "POST xoa_van_ban_khoi_ho_so", "QA-VBDI-REMOVE-HS", "VanBan.ho_so_van_ban set null", "/hosovanban/chi-tiet/<ho_so>/van-ban/<vb>/xoa/", "VanBan.ho_so_van_ban", "apps/hosovanban/views.py:xoa_van_ban_khoi_ho_so", tc_record_remove_document)
    add_case("TC-HOSO-010", "Hồ sơ văn bản", "Add document to record", "Văn thư", "Medium", "Feature appears in requirements/templates", "Reverse add-document route", "Existing VanBan", "Route/view exists to add document into record", "No route found", "HoSoVanBan, VanBan", "apps/hosovanban/urls.py; apps/templates/hosovanban/them-van-ban-popup.html", tc_record_add_document_not_implemented)
    add_case("TC-HOSO-011", "Hồ sơ văn bản", "Create Vĩnh viễn retention", "Văn thư", "Medium", "Retention option exists", "POST create with thoi_gian_bao_quan=Vĩnh viễn", "QA-HS-VINHVIEN", "Record should be created for selectable retention option", "/hosovanban/them-ho-so-van-ban.html", "HoSoVanBanCreateForm, HoSoVanBan.so_nam_luu_tru", "apps/hosovanban/forms.py:HoSoVanBanCreateForm.clean; apps/core/models.py:HoSoVanBan", tc_record_vinh_vien_storage_bug, "Hồ sơ retention 'Vĩnh viễn' cannot be saved", "Form sets so_nam_luu_tru=None for 'Vĩnh viễn' while HoSoVanBan.so_nam_luu_tru is null=False.")

    add_case("TC-CV-001", "Công việc", "Leader task list", "Lãnh đạo", "High", "Logged in as leader", "GET /giao-viec.html", "Seeded task", "HTTP 200", "/giao-viec.html", "CongViec", "apps/quanlycongviec/views.py:giao_viec", tc_task_leader_list)
    add_case("TC-CV-002", "Công việc", "Specialist task list scope", "Chuyên viên", "High", "Tasks for two specialists exist", "GET /xu-ly-cong-viec.html", "QA Công việc seed / người khác", "Only assigned task visible", "/xu-ly-cong-viec.html", "CongViec.nguoi_thuc_hien", "apps/quanlycongviec/views.py:xu_ly_cong_viec", tc_task_specialist_list_scope)
    add_case("TC-CV-003", "Công việc", "Add task", "Lãnh đạo", "Critical", "Specialist core profile exists", "POST /add/", "QA Công việc tạo mới", "Task created", "/add/", "CongViec, PhanCongCongViec", "apps/quanlycongviec/views.py:add_task", tc_task_add_valid)
    add_case("TC-CV-004", "Công việc", "Add task missing required", "Lãnh đạo", "High", "Logged in as leader", "POST /add/ missing ten_cv", "ten_cv=''", "No task created", "/add/", "CongViec", "apps/quanlycongviec/views.py:add_task", tc_task_add_missing_required)
    add_case("TC-CV-005", "Công việc", "Add task past date", "Lãnh đạo", "High", "Logged in as leader", "POST /add/ with ngay_bat_dau yesterday", "Past date", "No task created", "/add/", "CongViec", "apps/quanlycongviec/views.py:_validate_task_dates", tc_task_add_past_date_rejected)
    add_case("TC-CV-006", "Công việc", "Task detail assignee", "Chuyên viên", "High", "Assigned task exists", "GET /task/<id>/", "QA Công việc seed", "HTTP 200", "/task/<id>/", "CongViec", "apps/quanlycongviec/views.py:task_detail", tc_task_detail_assignee)
    add_case("TC-CV-007", "Công việc", "Task detail unauthorized", "Chuyên viên", "High", "Unassigned task exists", "GET /task/<id>/", "Task assigned to other specialist", "Redirect to my task list", "/task/<id>/", "CongViec", "apps/quanlycongviec/views.py:task_detail", tc_task_detail_unauthorized_redirect)
    add_case("TC-CV-008", "Công việc", "Edit task", "Lãnh đạo", "High", "Pending task managed by leader exists", "POST /edit/<id>/", "QA Công việc sau sửa", "Task updated", "/edit/<id>/", "CongViec", "apps/quanlycongviec/views.py:edit_task", tc_task_edit_valid)
    add_case("TC-CV-009", "Công việc", "Delete task", "Lãnh đạo", "High", "Pending task managed by leader exists", "POST /delete/<id>/", "QA Công việc để xóa", "Task deleted", "/delete/<id>/", "CongViec", "apps/quanlycongviec/views.py:delete_task", tc_task_delete_valid)
    add_case("TC-CV-010", "Công việc", "Process without approval", "Chuyên viên", "Critical", "Assigned task yeu_cau_phe_duyet=False", "POST /task/<id>/xu-ly/ with result file", "ket-qua.docx", "Task Đã hoàn thành", "/task/<id>/xu-ly/", "ProcessTaskForm, FileCVLienQuan", "apps/quanlycongviec/views.py:process_task", tc_task_process_without_approval_completed)
    add_case("TC-CV-011", "Công việc", "Process with approval", "Chuyên viên", "Critical", "Assigned task yeu_cau_phe_duyet=True", "POST /task/<id>/xu-ly/ with result file", "ket-qua.pdf", "Task Chờ duyệt", "/task/<id>/xu-ly/", "ProcessTaskForm", "apps/quanlycongviec/views.py:process_task", tc_task_process_with_approval_waiting)
    add_case("TC-CV-012", "Công việc", "Process requires file", "Chuyên viên", "High", "Assigned task exists", "POST process without tep_ket_qua", "No file", "Form rejects and status unchanged", "/task/<id>/xu-ly/", "ProcessTaskForm.require_result_file", "apps/quanlycongviec/forms.py:ProcessTaskForm", tc_task_process_requires_result_file)
    add_case("TC-CV-013", "Công việc", "Process invalid file", "Chuyên viên", "High", "Assigned task exists", "POST process with bad.txt", "bad.txt", "Form rejects and status unchanged", "/task/<id>/xu-ly/", "ProcessTaskForm.clean", "apps/quanlycongviec/forms.py:BaseTaskResultForm.clean", tc_task_process_invalid_result_file)
    add_case("TC-CV-014", "Công việc", "Update result deletes result file only", "Chuyên viên", "High", "Returned task has original and result files", "POST cap-nhat-xu-ly with delete_file_ids original,result", "delete_file_ids", "Original kept; result file deleted", "/task/<id>/cap-nhat-xu-ly/", "UpdateTaskResultForm, FileCVLienQuan", "apps/quanlycongviec/views.py:update_task_result", tc_task_update_result_deletes_only_result_file)
    add_case("TC-CV-015", "Công việc", "Specialist return to leader", "Chuyên viên", "High", "Assigned pending task exists", "POST /task/<id>/hoan-tra/", "noi_dung", "Status Hoàn trả_LĐ; HoanTraCongViec created", "/task/<id>/hoan-tra/", "ReturnTaskForm, HoanTraCongViec", "apps/quanlycongviec/views.py:return_task", tc_task_specialist_return_to_leader)
    add_case("TC-CV-016", "Công việc", "Leader return to specialist", "Lãnh đạo", "High", "Task status Chờ duyệt", "POST /task/<id>/hoan-tra/", "noi_dung", "Status Hoàn trả_CV", "/task/<id>/hoan-tra/", "ReturnTaskForm", "apps/quanlycongviec/views.py:return_task", tc_task_leader_return_to_specialist)
    add_case("TC-CV-017", "Công việc", "Leader approve task", "Lãnh đạo", "Critical", "Task status Chờ duyệt", "POST /task/<id>/approve/", "None", "Status Đã hoàn thành; PheDuyetCongViec created", "/task/<id>/approve/", "PheDuyetCongViec", "apps/quanlycongviec/views.py:approve_task", tc_task_leader_approve_waiting)
    add_case("TC-CV-018", "Công việc", "Task detail API manager", "Lãnh đạo", "Medium", "Leader manages task", "GET /api/task/<id>/", "QA Công việc seed", "HTTP 200 JSON", "/api/task/<id>/", "CongViec, FileCVLienQuan", "apps/quanlycongviec/views.py:get_task_detail", tc_task_api_manager_json)
    add_case("TC-CV-019", "Công việc", "Task detail API forbidden", "Chuyên viên", "Medium", "Specialist is not manager", "GET /api/task/<id>/", "QA Công việc seed", "HTTP 403", "/api/task/<id>/", "CongViec", "apps/quanlycongviec/views.py:get_task_detail", tc_task_api_not_manager_forbidden)
    add_case("TC-CV-020", "Công việc", "Start task route", "Chuyên viên", "Medium", "Assigned task without result exists", "GET /start/<id>/", "QA Công việc start route", "Redirect to process form", "/start/<id>/", "CongViec", "apps/quanlycongviec/views.py:start_task", tc_task_start_redirects_to_process)


def write_csv(path, fieldnames, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_outputs():
    master_fields = [
        "TestCaseID",
        "Module",
        "Feature",
        "Role",
        "Priority",
        "Preconditions",
        "TestSteps",
        "TestData",
        "ExpectedResult",
        "RouteOrView",
        "ModelOrFormRelated",
        "SourceReference",
    ]
    execution_fields = [
        "TestCaseID",
        "Module",
        "Feature",
        "Role",
        "Preconditions",
        "TestSteps",
        "ExpectedResult",
        "ActualResult",
        "Status",
        "Severity",
        "Evidence",
        "ErrorMessage",
        "Notes",
    ]
    bug_fields = [
        "BugID",
        "TestCaseID",
        "Module",
        "Feature",
        "Title",
        "StepsToReproduce",
        "ExpectedResult",
        "ActualResult",
        "Severity",
        "SuspectedCause",
        "SourceReference",
        "Evidence",
    ]
    write_csv(OUTPUT_DIR / "testcase_master.csv", master_fields, TESTCASES)
    write_csv(OUTPUT_DIR / "test_execution_results.csv", execution_fields, RESULTS)
    write_csv(OUTPUT_DIR / "bug_list.csv", bug_fields, BUGS)

    counts = {status: 0 for status in ["PASS", "FAIL", "BLOCKED", "NOT_IMPLEMENTED"]}
    for result in RESULTS:
        counts[result["Status"]] += 1

    important_bugs = "\n".join(
        f"- {bug['BugID']} / {bug['TestCaseID']}: {bug['Title']} ({bug['Severity']})"
        for bug in BUGS[:10]
    ) or "- Không có FAIL runtime."

    not_tested = []
    for result in RESULTS:
        if result["Status"] in {"BLOCKED", "NOT_IMPLEMENTED"}:
            not_tested.append(f"- {result['TestCaseID']}: {result['Feature']} - {result['ActualResult']}")
    not_tested_text = "\n".join(not_tested) or "- Không có testcase bị BLOCKED/NOT_IMPLEMENTED."

    baseline_note = run_existing_test_note()

    summary = f"""# QA Test Summary

## Tổng quan
- Tổng số testcase: {len(TESTCASES)}
- PASS: {counts['PASS']}
- FAIL: {counts['FAIL']}
- BLOCKED: {counts['BLOCKED']}
- NOT_IMPLEMENTED: {counts['NOT_IMPLEMENTED']}

## Baseline test tự động sẵn có
- Đã chạy `python manage.py test --verbosity 1`.
- Kết quả evidence: `qa_test_outputs/evidence/existing_django_tests_exitcode.log`
- Ghi nhận: {baseline_note}

## Lỗi quan trọng nhất
{important_bugs}

## Chức năng chưa test được hoặc chưa triển khai
{not_tested_text}

## Dữ liệu test đã tạo
- Dữ liệu được tạo trong Django test database bằng `qa_test_outputs/evidence/run_qa_runtime_tests.py`; không ghi vào database thật.
- User test: `qa_admin`, `qa_leader`, `qa_leader2`, `qa_clerk`, `qa_specialist`, `qa_specialist2`, `qa_invalid_role`.
- Dữ liệu nghiệp vụ test: chi nhánh/phòng ban QA, văn bản đến, văn bản đi, hồ sơ văn bản, công việc, đơn vị ngoài, file upload giả lập.
- Media runtime được ghi vào `qa_test_outputs/evidence/runtime_media/`.

## Nhận định coverage
- Coverage theo HTTP/Django test client bao phủ authentication, role/menu, dashboard, văn bản đến, văn bản đi, hồ sơ văn bản, công việc, API JSON, validation, upload file, redirect và workflow trạng thái chính.
- Chưa chạy browser automation/screenshot; các kết quả UI được kiểm ở mức response/template context/DB state.
- Các static template cũ không được nối trong URL hiện tại chỉ được ghi nhận khi có dấu vết menu/route liên quan.
"""
    (OUTPUT_DIR / "test_summary.md").write_text(summary, encoding="utf-8")


def execute_cases():
    evidence = "Django test client response; qa_test_outputs/evidence/qa_runtime_tests.log"
    for case in TESTCASES:
        runner = case.get("_runner")
        if runner is None:
            record(case, "No runner defined.", "BLOCKED", "None", evidence, "Missing runner.")
            continue
        try:
            actual, status, severity, error = runner()
            record(case, actual, status, severity, evidence, error)
            log(f"{case['TestCaseID']} {status}: {actual}")
        except Exception as exc:
            tb = traceback.format_exc()
            log(f"{case['TestCaseID']} FAIL_EXCEPTION: {exc}\n{tb}")
            record(
                case,
                f"Unhandled exception: {exc}",
                "FAIL",
                "High",
                evidence,
                tb,
            )


def main():
    LOG_FILE.write_text("QA runtime test execution log\n", encoding="utf-8")
    setup_test_environment()
    old_config = None
    try:
        old_config = setup_databases(verbosity=0, interactive=False)
        seed_context()
        register_cases()
        execute_cases()
        write_outputs()
        counts = {status: 0 for status in ["PASS", "FAIL", "BLOCKED", "NOT_IMPLEMENTED"]}
        for result in RESULTS:
            counts[result["Status"]] += 1
        print(
            "QA_RUNTIME_DONE "
            f"total={len(TESTCASES)} pass={counts['PASS']} fail={counts['FAIL']} "
            f"blocked={counts['BLOCKED']} not_implemented={counts['NOT_IMPLEMENTED']}"
        )
    finally:
        if old_config is not None:
            teardown_databases(old_config, verbosity=0)


if __name__ == "__main__":
    sys.exit(main() or 0)
