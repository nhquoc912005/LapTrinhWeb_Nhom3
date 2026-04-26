# Tóm tắt kết quả kiểm thử QA

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
