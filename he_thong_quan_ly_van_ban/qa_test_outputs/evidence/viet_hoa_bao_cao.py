import csv
from pathlib import Path


OUT = Path(__file__).resolve().parents[1]

HEADER_MAPS = {
    "testcase_master.csv": {
        "TestCaseID": "Mã testcase",
        "Module": "Phân hệ",
        "Feature": "Chức năng",
        "Role": "Vai trò",
        "Priority": "Mức ưu tiên",
        "Preconditions": "Tiền điều kiện",
        "TestSteps": "Các bước kiểm thử",
        "TestData": "Dữ liệu kiểm thử",
        "ExpectedResult": "Kết quả mong đợi",
        "RouteOrView": "Route hoặc View",
        "ModelOrFormRelated": "Model/Form liên quan",
        "SourceReference": "Tham chiếu source",
    },
    "test_execution_results.csv": {
        "TestCaseID": "Mã testcase",
        "Module": "Phân hệ",
        "Feature": "Chức năng",
        "Role": "Vai trò",
        "Preconditions": "Tiền điều kiện",
        "TestSteps": "Các bước kiểm thử",
        "ExpectedResult": "Kết quả mong đợi",
        "ActualResult": "Kết quả thực tế",
        "Status": "Trạng thái",
        "Severity": "Mức độ nghiêm trọng",
        "Evidence": "Bằng chứng",
        "ErrorMessage": "Thông báo lỗi",
        "Notes": "Ghi chú",
    },
    "bug_list.csv": {
        "BugID": "Mã lỗi",
        "TestCaseID": "Mã testcase",
        "Module": "Phân hệ",
        "Feature": "Chức năng",
        "Title": "Tiêu đề",
        "StepsToReproduce": "Các bước tái hiện",
        "ExpectedResult": "Kết quả mong đợi",
        "ActualResult": "Kết quả thực tế",
        "Severity": "Mức độ nghiêm trọng",
        "SuspectedCause": "Nguyên nhân nghi ngờ",
        "SourceReference": "Tham chiếu source",
        "Evidence": "Bằng chứng",
    },
}

EXACT = {
    # Common values.
    "Authentication": "Xác thực",
    "Role/Permission": "Vai trò/Phân quyền",
    "Dashboard": "Tổng quan",
    "Anonymous": "Chưa đăng nhập",
    "All roles": "Tất cả vai trò",
    "UNKNOWN": "Không xác định",
    "Critical": "Nghiêm trọng",
    "High": "Cao",
    "Medium": "Trung bình",
    "Low": "Thấp",
    "PASS": "ĐẠT",
    "FAIL": "LỖI",
    "BLOCKED": "BỊ CHẶN",
    "NOT_IMPLEMENTED": "CHƯA TRIỂN KHAI",
    "None": "Không",
    "Django test client response; qa_test_outputs/evidence/qa_runtime_tests.log": "Phản hồi Django test client; qa_test_outputs/evidence/qa_runtime_tests.log",

    # Features.
    "Add document to record": "Thêm văn bản vào hồ sơ",
    "Add task": "Tạo công việc",
    "Add task missing required": "Tạo công việc thiếu dữ liệu bắt buộc",
    "Add task past date": "Tạo công việc với ngày quá khứ",
    "Admin top menu": "Menu trên của Admin",
    "Approve": "Phê duyệt",
    "Approve missing clerk": "Phê duyệt thiếu văn thư",
    "Block assignment list": "Chặn truy cập danh sách giao việc",
    "Block incoming create": "Chặn tạo văn bản đến",
    "Block outgoing create": "Chặn tạo văn bản đi",
    "Block specialist task list": "Chặn danh sách công việc của chuyên viên",
    "Branches API": "API chi nhánh/phòng ban",
    "Create Vĩnh viễn retention": "Tạo hồ sơ bảo quản Vĩnh viễn",
    "Create forbidden": "Chặn tạo",
    "Create missing required": "Tạo thiếu dữ liệu bắt buộc",
    "Create valid": "Tạo hợp lệ",
    "Dashboard metrics": "Chỉ số tổng quan",
    "Deadline validation": "Kiểm tra hạn xử lý",
    "Delete": "Xóa",
    "Delete empty": "Xóa hồ sơ rỗng",
    "Delete record with document": "Xóa hồ sơ đang có văn bản",
    "Delete task": "Xóa công việc",
    "Detail": "Chi tiết",
    "Detail creator": "Chi tiết cho người tạo",
    "Detail non-creator": "Chi tiết cho người không tạo",
    "Document detail inside record": "Chi tiết văn bản trong hồ sơ",
    "Duplicate code validation": "Kiểm tra trùng ký hiệu",
    "Dynamic report data": "Dữ liệu báo cáo động",
    "Edit task": "Sửa công việc",
    "Employees API": "API nhân viên theo phòng ban",
    "External next URL": "Next URL bên ngoài",
    "Forward missing specialist": "Chuyển tiếp thiếu chuyên viên",
    "Forward to specialist": "Chuyển tiếp cho chuyên viên",
    "Help menu route": "Route menu hướng dẫn",
    "Invalid main file": "File chính không hợp lệ",
    "Issue requires recipient": "Ban hành cần nơi nhận",
    "Issue valid": "Ban hành hợp lệ",
    "Leader approve task": "Lãnh đạo duyệt công việc",
    "Leader dashboard access": "Lãnh đạo truy cập tổng quan",
    "Leader list scope": "Phạm vi danh sách của lãnh đạo",
    "Leader menu": "Menu của lãnh đạo",
    "Leader return to specialist": "Lãnh đạo hoàn trả cho chuyên viên",
    "Leader task list": "Danh sách giao việc của lãnh đạo",
    "List": "Danh sách",
    "Login invalid password": "Đăng nhập sai mật khẩu",
    "Login page": "Trang đăng nhập",
    "Login success": "Đăng nhập thành công",
    "Logout": "Đăng xuất",
    "Outside unit API": "API đơn vị ngoài",
    "Process invalid file": "Xử lý với file sai loại",
    "Process requires file": "Xử lý bắt buộc có file",
    "Process with approval": "Xử lý có yêu cầu phê duyệt",
    "Process without approval": "Xử lý không yêu cầu phê duyệt",
    "Profile menu route": "Route menu thông tin cá nhân",
    "Protected redirect": "Redirect khi chưa đăng nhập",
    "Reject invalid attachment": "Từ chối file đính kèm không hợp lệ",
    "Remove document from record": "Gỡ văn bản khỏi hồ sơ",
    "Report page access": "Truy cập trang báo cáo",
    "Return": "Hoàn trả",
    "Return requires reason": "Hoàn trả bắt buộc có lý do",
    "Return valid": "Hoàn trả hợp lệ",
    "Safe next URL": "Next URL nội bộ hợp lệ",
    "Save as read-only": "Lưu trạng thái xem để biết",
    "Search": "Tìm kiếm",
    "Specialist detail assigned": "Chuyên viên xem chi tiết đã phân công",
    "Specialist detail unassigned": "Chuyên viên xem chi tiết chưa phân công",
    "Specialist menu": "Menu của chuyên viên",
    "Specialist return to leader": "Chuyên viên hoàn trả cho lãnh đạo",
    "Specialist task list scope": "Phạm vi danh sách công việc của chuyên viên",
    "Start task route": "Route bắt đầu xử lý công việc",
    "Task detail API forbidden": "API chi tiết công việc bị chặn",
    "Task detail API manager": "API chi tiết công việc cho người quản lý",
    "Task detail assignee": "Chi tiết công việc cho người thực hiện",
    "Task detail unauthorized": "Chi tiết công việc không có quyền",
    "Unknown role blocked": "Chặn vai trò không xác định",
    "Update": "Cập nhật",
    "Update result deletes result file only": "Cập nhật kết quả chỉ xóa file kết quả",

    # Preconditions.
    "Project test DB ready": "Cơ sở dữ liệu test của project đã sẵn sàng",
    "User qa_clerk exists": "Có tài khoản qa_clerk",
    "Not logged in": "Chưa đăng nhập",
    "Logged in as specialist": "Đã đăng nhập bằng tài khoản chuyên viên",
    "Logged in as clerk": "Đã đăng nhập bằng tài khoản văn thư",
    "Logged in as leader": "Đã đăng nhập bằng tài khoản lãnh đạo",
    "Logged in as admin": "Đã đăng nhập bằng tài khoản admin",
    "Logged in as qa_clerk": "Đã đăng nhập bằng tài khoản qa_clerk",
    "Menu item exists": "Có mục menu tương ứng",
    "Seeded incoming/task exists": "Có văn bản đến và công việc seed",
    "Seeded incoming document": "Có văn bản đến seed",
    "User role set to UNKNOWN": "Vai trò người dùng được đặt là UNKNOWN",
    "Leader exists": "Có tài khoản lãnh đạo",
    "Leader owns incoming document": "Văn bản đến thuộc quyền xử lý của lãnh đạo",
    "Incoming forwarded to specialist": "Có văn bản đến đã chuyển tiếp cho chuyên viên",
    "Incoming not forwarded to specialist": "Có văn bản đến chưa chuyển tiếp cho chuyên viên",
    "Outgoing document created by specialist": "Có văn bản đi do chuyên viên tạo",
    "Outgoing document created by another specialist": "Có văn bản đi do chuyên viên khác tạo",
    "Outgoing pending document exists": "Có văn bản đi đang chờ xử lý",
    "Leader core profile exists": "Có hồ sơ core của lãnh đạo",
    "Leader is assigned approver": "Lãnh đạo là người được chỉ định duyệt",
    "Document is Chờ ban hành": "Văn bản đang ở trạng thái Chờ ban hành",
    "Branch exists": "Có chi nhánh trong dữ liệu test",
    "Department and users exist": "Có phòng ban và người dùng trong dữ liệu test",
    "Outside unit exists": "Có đơn vị ngoài trong dữ liệu test",
    "PhongBan and NguoiDung exist": "Có PhongBan và NguoiDung trong dữ liệu test",
    "Record QA-HS-001 exists": "Có hồ sơ QA-HS-001",
    "Record exists": "Có hồ sơ văn bản",
    "Record has VanBan": "Hồ sơ có văn bản bên trong",
    "Feature appears in requirements/templates": "Chức năng có dấu vết trong yêu cầu/template",
    "Retention option exists": "Có tùy chọn thời gian bảo quản",
    "Specialist core profile exists": "Có hồ sơ core của chuyên viên",
    "Task status Chờ duyệt": "Công việc ở trạng thái Chờ duyệt",
    "Tasks for two specialists exist": "Có công việc cho hai chuyên viên khác nhau",
    "Leader manages task": "Lãnh đạo là người giao/quản lý công việc",
    "Specialist is not manager": "Chuyên viên không phải người quản lý công việc",
    "Assigned task exists": "Có công việc đã được phân công",
    "Assigned task without result exists": "Có công việc đã phân công chưa có kết quả xử lý",
    "Assigned task yeu_cau_phe_duyet=False": "Có công việc đã phân công với yeu_cau_phe_duyet=False",
    "Assigned task yeu_cau_phe_duyet=True": "Có công việc đã phân công với yeu_cau_phe_duyet=True",
    "Assigned pending task exists": "Có công việc đang chờ xử lý được phân công",
    "Pending task managed by leader exists": "Có công việc chờ xử lý do lãnh đạo quản lý",
    "Returned task has original and result files": "Công việc bị hoàn trả có file gốc và file kết quả",
    "Unassigned task exists": "Có công việc không được giao cho người dùng hiện tại",
    "Empty current record exists": "Có hồ sơ hiện hành rỗng",
    "Report route exists": "Có route báo cáo",
    "Documents assigned to different leaders": "Có văn bản được giao cho các lãnh đạo khác nhau",
    "TepVanBanDen has FileExtensionValidator": "TepVanBanDen có FileExtensionValidator",
    "Incoming document exists": "Có văn bản đến",

    # Test steps and test data.
    "GET /logout/ then GET /dashboard/": "GET /logout/ rồi GET /dashboard/",
    "GET /van-ban-den/ as leader": "GET /van-ban-den/ bằng tài khoản lãnh đạo",
    "GET create record page": "GET trang tạo hồ sơ",
    "GET dashboard and inspect dashboard_metrics": "GET dashboard và kiểm tra dashboard_metrics",
    "GET dashboard and inspect sidebar_menu_items": "GET dashboard và kiểm tra sidebar_menu_items",
    "GET dashboard and inspect top_menu_items": "GET dashboard và kiểm tra top_menu_items",
    "GET report and inspect context": "GET trang báo cáo và kiểm tra context",
    "Inspect TOP_MENU_DEFINITIONS": "Kiểm tra TOP_MENU_DEFINITIONS",
    "POST .exe file": "POST file .exe",
    "POST / with next=/van-ban-den/": "POST / với next=/van-ban-den/",
    "POST / with next=https://example.com/evil": "POST / với next=https://example.com/evil",
    "POST / with valid username/password": "POST / với username/password hợp lệ",
    "POST / with wrong password": "POST / với mật khẩu sai",
    "POST /add/ missing ten_cv": "POST /add/ thiếu ten_cv",
    "POST /add/ with ngay_bat_dau yesterday": "POST /add/ với ngay_bat_dau là ngày hôm qua",
    "POST /task/<id>/xu-ly/ with result file": "POST /task/<id>/xu-ly/ với file kết quả",
    "POST /van-ban-den/them/ with malware.exe": "POST /van-ban-den/them/ với malware.exe",
    "POST /van-ban-den/them/ with required fields and PDF": "POST /van-ban-den/them/ với đủ trường bắt buộc và file PDF",
    "POST /van-ban-di/them/ with PDF": "POST /van-ban-di/them/ với file PDF",
    "POST ban-hanh with phong_ban_ids[]": "POST ban-hanh với phong_ban_ids[]",
    "POST ban-hanh without recipients": "POST ban-hanh không có nơi nhận",
    "POST cap-nhat-xu-ly with delete_file_ids original,result": "POST cap-nhat-xu-ly với delete_file_ids gồm file gốc và file kết quả",
    "POST chuyen-tiep without chuyen_vien_ids": "POST chuyen-tiep không có chuyen_vien_ids",
    "POST create record": "POST tạo hồ sơ",
    "POST create with duplicate ky_hieu_ho_so": "POST tạo hồ sơ với ky_hieu_ho_so trùng",
    "POST create with thoi_gian_bao_quan=Vĩnh viễn": "POST tạo hồ sơ với thoi_gian_bao_quan=Vĩnh viễn",
    "POST delete record": "POST xóa hồ sơ",
    "POST han_xu_ly <= ngay_van_ban": "POST với han_xu_ly <= ngay_van_ban",
    "POST hoan-tra with empty reason": "POST hoan-tra với lý do rỗng",
    "POST hoan-tra with reason": "POST hoan-tra với lý do hợp lệ",
    "POST missing trich_yeu": "POST thiếu trich_yeu",
    "POST phe-duyet without van_thu_id": "POST phe-duyet không có van_thu_id",
    "POST process with bad.txt": "POST xử lý với bad.txt",
    "POST process without tep_ket_qua": "POST xử lý không có tep_ket_qua",
    "POST xoa_van_ban_khoi_ho_so": "POST xoa_van_ban_khoi_ho_so",
    "Reverse add-document route": "Reverse route thêm văn bản vào hồ sơ",
    "Existing VanBan": "Văn bản hiện có",
    "External next URL": "Next URL bên ngoài",
    "Forwarded document": "Văn bản đã chuyển tiếp",
    "No file": "Không có file",
    "No recipient arrays": "Không có danh sách nơi nhận",
    "No specialist selected": "Không chọn chuyên viên",
    "No van_thu_id": "Không có van_thu_id",
    "Past date": "Ngày quá khứ",
    "Safe internal next URL": "Next URL nội bộ hợp lệ",
    "Same date": "Cùng ngày",
    "Seeded VanBanDen/CongViec": "VanBanDen/CongViec seed",
    "Seeded data": "Dữ liệu seed",
    "Seeded docs/tasks": "Văn bản/công việc seed",
    "Seeded outgoing docs": "Văn bản đi seed",
    "Seeded record": "Hồ sơ seed",
    "Seeded task": "Công việc seed",
    "Task assigned to other specialist": "Công việc được giao cho chuyên viên khác",
    "Unassigned document": "Văn bản chưa phân công",
    "Updated tieu_de_ho_so": "Cập nhật tieu_de_ho_so",
    "Updated trich_yeu": "Cập nhật trich_yeu",

    # Expected results.
    "Admin sees enabled management menu": "Admin thấy menu quản lý ở trạng thái khả dụng",
    "Document and attachment created": "Tạo được văn bản và file đính kèm",
    "Document deleted": "Văn bản được xóa",
    "Document updated": "Văn bản được cập nhật",
    "Form rejects and no create": "Form từ chối và không tạo dữ liệu",
    "Form rejects and status unchanged": "Form từ chối và trạng thái không đổi",
    "Form rejects duplicate": "Form từ chối dữ liệu trùng",
    "Forward record created; status DA_XU_LY": "Tạo bản ghi chuyển tiếp; trạng thái DA_XU_LY",
    "HTTP 200 JSON": "HTTP 200 kèm JSON",
    "HTTP 200 with dashboard metrics": "HTTP 200 và có chỉ số tổng quan",
    "HTTP 400 and status unchanged": "HTTP 400 và trạng thái không đổi",
    "Help route should be implemented or marked disabled": "Route hướng dẫn cần được triển khai hoặc đánh dấu chưa khả dụng",
    "Ignore external URL and redirect dashboard": "Bỏ qua URL bên ngoài và redirect về dashboard",
    "Invalid extension rejected and no document created": "Từ chối phần mở rộng không hợp lệ và không tạo văn bản",
    "JSON chi_nhanh list": "JSON danh sách chi_nhanh",
    "JSON don_vi_ngoai list": "JSON danh sách don_vi_ngoai",
    "JSON nhan_vien list": "JSON danh sách nhan_vien",
    "JSON ok; status Đã ban hành; BanHanh created": "JSON ok; trạng thái Đã ban hành; tạo BanHanh",
    "Login page returns 200": "Trang đăng nhập trả HTTP 200",
    "Matching document displayed": "Hiển thị văn bản khớp điều kiện",
    "Metrics include seeded data": "Chỉ số bao gồm dữ liệu seed",
    "No status/forward change": "Không đổi trạng thái/bản ghi chuyển tiếp",
    "No task created": "Không tạo công việc",
    "Only assigned docs visible": "Chỉ hiển thị văn bản được phân công",
    "Only assigned task visible": "Chỉ hiển thị công việc được phân công",
    "Original kept; result file deleted": "Giữ file gốc; xóa file kết quả",
    "Outgoing document created": "Tạo được văn bản đi",
    "Profile route should be implemented or marked disabled": "Route thông tin cá nhân cần được triển khai hoặc đánh dấu chưa khả dụng",
    "Record deleted": "Hồ sơ được xóa",
    "Record not deleted": "Hồ sơ không bị xóa",
    "Record should be created for selectable retention option": "Phải tạo được hồ sơ với tùy chọn bảo quản có trong form",
    "Record updated": "Hồ sơ được cập nhật",
    "Record, PhongXemHoSo, NguoiXuLyHoSo created": "Tạo HoSoVanBan, PhongXemHoSo, NguoiXuLyHoSo",
    "Redirect login and session cleared": "Redirect về đăng nhập và phiên đăng nhập bị xóa",
    "Redirect to dashboard": "Redirect về dashboard",
    "Redirect to list": "Redirect về danh sách",
    "Redirect to login with next": "Redirect về đăng nhập kèm tham số next",
    "Redirect to my task list": "Redirect về danh sách công việc của tôi",
    "Redirect to process form": "Redirect tới form xử lý",
    "Redirect to safe next URL": "Redirect tới next URL nội bộ hợp lệ",
    "Report should have DB-backed statistics context": "Báo cáo cần có context thống kê lấy từ DB",
    "Route/view exists to add document into record": "Có route/view để thêm văn bản vào hồ sơ",
    "Status Chờ ban hành; VanBanDuyet created": "Trạng thái Chờ ban hành; tạo VanBanDuyet",
    "Status HOAN_TRA and date set": "Trạng thái HOAN_TRA và có ngày hoàn trả",
    "Status Hoàn Trả; VanBanHoanTra created": "Trạng thái Hoàn Trả; tạo VanBanHoanTra",
    "Status Hoàn trả_CV": "Trạng thái Hoàn trả_CV",
    "Status Hoàn trả_LĐ; HoanTraCongViec created": "Trạng thái Hoàn trả_LĐ; tạo HoanTraCongViec",
    "Status XEM_DE_BIET": "Trạng thái XEM_DE_BIET",
    "Status unchanged": "Trạng thái không đổi",
    "Status Đã hoàn thành; PheDuyetCongViec created": "Trạng thái Đã hoàn thành; tạo PheDuyetCongViec",
    "Stay on login page with form error": "Ở lại trang đăng nhập và hiển thị lỗi form",
    "Task Chờ duyệt": "Công việc chuyển sang Chờ duyệt",
    "Task created": "Công việc được tạo",
    "Task deleted": "Công việc được xóa",
    "Task menu links to giao_viec": "Menu công việc trỏ tới giao_viec",
    "Task menu links to xu_ly_cong_viec": "Menu công việc trỏ tới xu_ly_cong_viec",
    "Task updated": "Công việc được cập nhật",
    "Task Đã hoàn thành": "Công việc chuyển sang Đã hoàn thành",
    "VanBan.ho_so_van_ban set null": "VanBan.ho_so_van_ban được đặt về null",

    # Actual results and bug text.
    "Admin sees enabled top menu item 'Bộ công cụ quản lý'.": "Admin thấy mục menu trên 'Bộ công cụ quản lý' ở trạng thái khả dụng.",
    "Anonymous dashboard request redirected to login with next parameter.": "Người chưa đăng nhập truy cập dashboard được redirect về đăng nhập kèm tham số next.",
    "Approval without clerk was rejected and status stayed pending.": "Phê duyệt thiếu văn thư bị từ chối và trạng thái vẫn chờ xử lý.",
    "Assigned specialist opened forwarded incoming document detail.": "Chuyên viên được phân công mở được chi tiết văn bản đến đã chuyển tiếp.",
    "Assignee opened task detail.": "Người thực hiện mở được chi tiết công việc.",
    "Branch API returned chi_nhanh JSON list.": "API chi nhánh trả về danh sách chi_nhanh dạng JSON.",
    "CHUYEN_VIEN received HTTP 403 on giao-viec route.": "CHUYEN_VIEN nhận HTTP 403 tại route giao-viec.",
    "CHUYEN_VIEN received HTTP 403 on incoming create route.": "CHUYEN_VIEN nhận HTTP 403 tại route tạo văn bản đến.",
    "Clerk created record with department visibility and handler.": "Văn thư tạo được hồ sơ với phòng ban được xem và người xử lý.",
    "Clerk deleted empty record.": "Văn thư xóa được hồ sơ rỗng.",
    "Clerk issued outgoing document to a department and got JSON ok.": "Văn thư ban hành văn bản đi tới phòng ban và nhận JSON ok.",
    "Clerk removed document from record.": "Văn thư gỡ được văn bản khỏi hồ sơ.",
    "Clerk updated record title.": "Văn thư cập nhật được tiêu đề hồ sơ.",
    "Created incoming document with one attachment and redirected to list.": "Tạo văn bản đến với một file đính kèm và redirect về danh sách.",
    "Creator deleted pending outgoing document.": "Người tạo xóa được văn bản đi đang chờ xử lý.",
    "Creator opened outgoing detail page.": "Người tạo mở được trang chi tiết văn bản đi.",
    "Creator updated outgoing document.": "Người tạo cập nhật được văn bản đi.",
    "Deleted incoming document by POST.": "Đã xóa văn bản đến bằng POST.",
    "Duplicate ky_hieu_ho_so was rejected.": "ky_hieu_ho_so trùng bị từ chối.",
    "Employee API returned users for selected department.": "API nhân viên trả về người dùng thuộc phòng ban đã chọn.",
    "Empty return reason was rejected.": "Lý do hoàn trả rỗng bị từ chối.",
    "External next URL was ignored and redirected to dashboard.": "next URL bên ngoài bị bỏ qua và redirect về dashboard.",
    "GET / returned HTTP 200 and rendered login form.": "GET / trả HTTP 200 và render form đăng nhập.",
    "HTTP 200; created=False; form option 'Vĩnh viễn' did not persist.": "HTTP 200; created=False; tùy chọn form 'Vĩnh viễn' không lưu được.",
    "HTTP 302; created=True; VanBanDen count delta=1.": "HTTP 302; created=True; số lượng VanBanDen tăng 1.",
    "Invalid credentials kept user on login page with form errors.": "Thông tin đăng nhập sai giữ người dùng ở trang đăng nhập và có lỗi form.",
    "Invalid result file extension was rejected.": "Phần mở rộng file kết quả không hợp lệ bị từ chối.",
    "Issue endpoint returned 400 when recipients were missing.": "Endpoint ban hành trả HTTP 400 khi thiếu nơi nhận.",
    "Leader accessed assigned task list.": "Lãnh đạo truy cập được danh sách công việc được giao/quản lý.",
    "Leader approved outgoing document and assigned clerk.": "Lãnh đạo phê duyệt văn bản đi và chỉ định văn thư.",
    "Leader approved waiting-review task.": "Lãnh đạo duyệt công việc đang chờ duyệt.",
    "Leader created task via add_task.": "Lãnh đạo tạo công việc qua add_task.",
    "Leader dashboard rendered with 6 metric cards.": "Dashboard của lãnh đạo render với 6 thẻ chỉ số.",
    "Leader deleted pending task.": "Lãnh đạo xóa được công việc đang chờ xử lý.",
    "Leader edited pending task.": "Lãnh đạo sửa được công việc đang chờ xử lý.",
    "Leader forwarded incoming document to specialist and status changed to DA_XU_LY.": "Lãnh đạo chuyển tiếp văn bản đến cho chuyên viên và trạng thái chuyển thành DA_XU_LY.",
    "Leader list only showed documents assigned to that leader.": "Danh sách của lãnh đạo chỉ hiển thị văn bản được giao cho lãnh đạo đó.",
    "Leader returned incoming document with reason.": "Lãnh đạo hoàn trả văn bản đến kèm lý do.",
    "Leader returned outgoing document with reason.": "Lãnh đạo hoàn trả văn bản đi kèm lý do.",
    "Leader returned waiting-review task to specialist.": "Lãnh đạo hoàn trả công việc đang chờ duyệt cho chuyên viên.",
    "Leader saved incoming document as XEM_DE_BIET.": "Lãnh đạo lưu văn bản đến ở trạng thái XEM_DE_BIET.",
    "Leader sidebar task menu points to giao-viec.": "Menu công việc bên trái của lãnh đạo trỏ tới giao-viec.",
    "Logout redirected to login and protected dashboard required login again.": "Đăng xuất redirect về đăng nhập và dashboard được bảo vệ yêu cầu đăng nhập lại.",
    "Menu item 'Hướng dẫn sử dụng' has url_name=None and no route/view.": "Mục menu 'Hướng dẫn sử dụng' có url_name=None và không có route/view.",
    "Menu item 'Thông tin cá nhân' has url_name=None and no route/view.": "Mục menu 'Thông tin cá nhân' có url_name=None và không có route/view.",
    "Missing required field kept form on page and did not create document.": "Thiếu trường bắt buộc khiến form ở lại trang và không tạo văn bản.",
    "Missing specialist selection did not change incoming document status.": "Thiếu lựa chọn chuyên viên nên trạng thái văn bản đến không thay đổi.",
    "Missing task title was rejected.": "Thiếu tên công việc bị từ chối.",
    "No URL/view exists for adding an existing document into a record.": "Không có URL/view để thêm văn bản hiện có vào hồ sơ.",
    "Non-creator specialist received HTTP 403 on outgoing detail.": "Chuyên viên không phải người tạo nhận HTTP 403 khi xem chi tiết văn bản đi.",
    "Opened document detail inside record.": "Mở được chi tiết văn bản trong hồ sơ.",
    "Outgoing form rejected han_xu_ly <= ngay_van_ban.": "Form văn bản đi từ chối han_xu_ly <= ngay_van_ban.",
    "Outgoing form rejected invalid main attachment extension.": "Form văn bản đi từ chối phần mở rộng file chính không hợp lệ.",
    "Outside unit API search returned matching unit.": "API tìm kiếm đơn vị ngoài trả về đơn vị khớp.",
    "POST / redirected to /dashboard/.": "POST / redirect tới /dashboard/.",
    "Past start date was rejected.": "Ngày bắt đầu trong quá khứ bị từ chối.",
    "ProcessTaskForm required at least one result file.": "ProcessTaskForm yêu cầu ít nhất một file kết quả.",
    "Processing task with approval moved it to CHO_DUYET.": "Xử lý công việc có phê duyệt chuyển trạng thái sang CHO_DUYET.",
    "Processing task without approval marked it completed.": "Xử lý công việc không cần phê duyệt chuyển trạng thái hoàn thành.",
    "Record containing current document was not deleted.": "Hồ sơ đang chứa văn bản hiện hành không bị xóa.",
    "Report view provided dynamic context.": "View báo cáo có cung cấp context động.",
    "Safe next URL honored: /van-ban-den/.": "next URL nội bộ hợp lệ được sử dụng: /van-ban-den/.",
    "Search q filter returned matching incoming document.": "Bộ lọc q trả về văn bản đến khớp điều kiện.",
    "Specialist accessed /bao-cao-thong-ke.html with HTTP 200.": "Chuyên viên truy cập /bao-cao-thong-ke.html với HTTP 200.",
    "Specialist accessed outgoing list.": "Chuyên viên truy cập được danh sách văn bản đi.",
    "Specialist accessed record list.": "Chuyên viên truy cập được danh sách hồ sơ.",
    "Specialist created outgoing document with PDF attachment.": "Chuyên viên tạo được văn bản đi với file PDF đính kèm.",
    "Specialist list only showed assigned tasks.": "Danh sách của chuyên viên chỉ hiển thị công việc được phân công.",
    "Specialist received HTTP 403 on record create route.": "Chuyên viên nhận HTTP 403 tại route tạo hồ sơ.",
    "Specialist returned task to leader.": "Chuyên viên hoàn trả công việc cho lãnh đạo.",
    "Specialist sidebar task menu points to xu-ly-cong-viec.": "Menu công việc bên trái của chuyên viên trỏ tới xu-ly-cong-viec.",
    "Start route redirected assignee to process form.": "Route start redirect người thực hiện tới form xử lý.",
    "Task detail API returned 403 for non-manager.": "API chi tiết công việc trả 403 cho người không phải quản lý.",
    "Task detail API returned JSON for task manager.": "API chi tiết công việc trả JSON cho người quản lý công việc.",
    "Unassigned specialist was redirected from incoming detail to list.": "Chuyên viên chưa được phân công bị redirect từ chi tiết văn bản đến về danh sách.",
    "Unassigned specialist was redirected from task detail.": "Chuyên viên chưa được phân công bị redirect khỏi chi tiết công việc.",
    "Unknown role user received HTTP 403 on dashboard.": "Người dùng có vai trò không xác định nhận HTTP 403 tại dashboard.",
    "Update result deleted only assignee's result file and kept original file.": "Cập nhật kết quả chỉ xóa file kết quả của người thực hiện và giữ file gốc.",
    "Updated incoming document trich_yeu.": "Đã cập nhật trich_yeu của văn bản đến.",
    "VAN_THU received HTTP 403 on outgoing create route.": "VAN_THU nhận HTTP 403 tại route tạo văn bản đi.",
    "VAN_THU received HTTP 403 on xu-ly-cong-viec route.": "VAN_THU nhận HTTP 403 tại route xu-ly-cong-viec.",
    "Văn thư accessed incoming document list.": "Văn thư truy cập được danh sách văn bản đến.",
    "Văn thư opened incoming detail page.": "Văn thư mở được trang chi tiết văn bản đến.",
    "Hồ sơ retention 'Vĩnh viễn' cannot be saved": "Không lưu được hồ sơ có thời gian bảo quản 'Vĩnh viễn'",
    "Văn bản đến accepts invalid attachment extension": "Văn bản đến chấp nhận file đính kèm sai phần mở rộng",
    "Form sets so_nam_luu_tru=None for 'Vĩnh viễn' while HoSoVanBan.so_nam_luu_tru is null=False.": "Form đặt so_nam_luu_tru=None cho 'Vĩnh viễn' trong khi HoSoVanBan.so_nam_luu_tru đang null=False.",
    "TepVanBanDen.tep validator is bypassed because view creates TepVanBanDen.objects.create(...) without form/full_clean validation.": "Validator của TepVanBanDen.tep bị bỏ qua vì view tạo TepVanBanDen.objects.create(...) trực tiếp, không qua form hoặc full_clean.",
}

DO_NOT_TRANSLATE_FIELDS = {
    "TestCaseID",
    "BugID",
    "RouteOrView",
    "ModelOrFormRelated",
    "SourceReference",
    "ErrorMessage",
    "Notes",
}


def translate(value):
    if value is None or value == "":
        return value
    if value in EXACT:
        return EXACT[value]
    if value.startswith("Dashboard metrics include seeded incoming/task data:"):
        return value.replace(
            "Dashboard metrics include seeded incoming/task data:",
            "Chỉ số tổng quan có bao gồm dữ liệu văn bản/công việc seed:",
        )
    return (
        value.replace(" with ", " với ")
        .replace(" without ", " không có ")
        .replace(" missing ", " thiếu ")
        .replace(" and ", " và ")
        .replace(" then ", " rồi ")
    )


def translate_csv(filename):
    path = OUT / filename
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames or []
        rows = []
        for row in reader:
            rows.append(
                {
                    key: (value if key in DO_NOT_TRANSLATE_FIELDS else translate(value))
                    for key, value in row.items()
                }
            )

    header_map = HEADER_MAPS[filename]
    new_fields = [header_map.get(field, field) for field in fields]
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=new_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({header_map.get(key, key): value for key, value in row.items()})


for csv_name in HEADER_MAPS:
    translate_csv(csv_name)

(OUT / "test_summary.md").write_text(
    """# Tóm tắt kết quả kiểm thử QA

## Tổng quan
- Tổng số testcase: 84
- ĐẠT: 79
- LỖI: 2
- BỊ CHẶN: 0
- CHƯA TRIỂN KHAI: 3

## Baseline test tự động sẵn có
- Đã chạy `python manage.py test --verbosity 1`.
- File bằng chứng: `qa_test_outputs/evidence/existing_django_tests_exitcode.log`.
- Kết quả: tìm thấy 23 test, chạy thành công, `OK`, exit code 0.

## Lỗi quan trọng nhất
- BUG-001 / TC-VBDEN-004: Văn bản đến chấp nhận file đính kèm sai phần mở rộng (Cao).
- BUG-002 / TC-HOSO-011: Không lưu được hồ sơ có thời gian bảo quản `Vĩnh viễn` (Trung bình).

## Chức năng chưa test được hoặc chưa triển khai
- TC-ROLE-008: Route menu thông tin cá nhân - mục menu `Thông tin cá nhân` có `url_name=None` và không có route/view.
- TC-ROLE-009: Route menu hướng dẫn - mục menu `Hướng dẫn sử dụng` có `url_name=None` và không có route/view.
- TC-HOSO-010: Thêm văn bản vào hồ sơ - không có URL/view để thêm văn bản hiện có vào hồ sơ.

## Dữ liệu test đã tạo
- Dữ liệu được tạo trong Django test database bằng `qa_test_outputs/evidence/run_qa_runtime_tests.py`; không ghi vào database thật.
- User test: `qa_admin`, `qa_leader`, `qa_leader2`, `qa_clerk`, `qa_specialist`, `qa_specialist2`, `qa_invalid_role`.
- Dữ liệu nghiệp vụ test: chi nhánh/phòng ban QA, văn bản đến, văn bản đi, hồ sơ văn bản, công việc, đơn vị ngoài, file upload giả lập.
- Media runtime được ghi vào `qa_test_outputs/evidence/runtime_media/`.

## Nhận định coverage
- Coverage theo HTTP/Django test client bao phủ xác thực, vai trò/menu, dashboard, văn bản đến, văn bản đi, hồ sơ văn bản, công việc, API JSON, validation, upload file, redirect và workflow trạng thái chính.
- Chưa chạy browser automation/screenshot; các kết quả UI được kiểm ở mức response/template context/DB state.
- Các static template cũ không được nối trong URL hiện tại chỉ được ghi nhận khi có dấu vết menu/route liên quan.
""",
    encoding="utf-8",
)

print("Đã Việt hóa các file báo cáo QA.")
