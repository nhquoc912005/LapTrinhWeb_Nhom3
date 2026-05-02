# Báo cáo kiểm tra lỗi Project

Thời điểm kiểm tra: 01/05/2026. Phạm vi: chỉ đọc, phân tích và chạy các lệnh kiểm tra an toàn/dry-run; không sửa code nghiệp vụ, không xóa file, không reset database, không commit.

## 1. Tổng quan project

- Framework: Django 6.0.3.
- Project: `he_thong_quan_ly_van_ban`.
- AUTH_USER_MODEL: `accounts.Customer`.
- App chính: `accounts`, `core`, `quanlyvanbanden`, `quanlyvanbandi`, `quanlycongviec`, `hosovanban`.
- Database hiện tại: PostgreSQL/Supabase qua host pooler `aws-1-ap-south-1.pooler.supabase.com`.
- Role chính: `ADMIN`, `LANH_DAO`, `VAN_THU`, `CHUYEN_VIEN`.
- Nhận xét tổng quan: project chạy được ở mức smoke test, có dữ liệu Supabase thật, nhưng đang có một migration chữ ký số chưa apply, một số chức năng bị tắt hoặc chưa hoàn thiện, và có rủi ro bảo mật/upload/seed data cần xử lý trước khi demo chính thức.

Số liệu DB đọc được:

| Bảng/model | Số lượng |
|---|---:|
| `accounts.Customer` | 76 |
| `core.NguoiDung` | 76 |
| `core.VanBan` | 172 |
| `quanlyvanbanden.VanBanDen` legacy | 38 |
| `core.CongViec` | 77 |
| `core.HoSoVanBan` | 126 |
| `core.ChuKySo` | 76 |
| `core.LichSuKySo` | 120 |

Số user theo role:

| Role | Số lượng |
|---|---:|
| ADMIN | 2 |
| LANH_DAO | 8 |
| VAN_THU | 13 |
| CHUYEN_VIEN | 53 |

## 2. Lỗi nghiêm trọng cần sửa ngay

### Lỗi 1: Migration chữ ký số chưa được apply lên Supabase

- Mức độ: Critical.
- File liên quan: `apps/core/models.py:715-730`, `apps/core/migrations/0021_lichsukyso_sha256_integrity.py`.
- Bằng chứng: `python manage.py migrate --plan` còn pending `core.0021_lichsukyso_sha256_integrity`.
- Lỗi runtime đã tái hiện:
  - `python manage.py check_digital_signature_integrity` lỗi `column LichSuKySo.file_hash does not exist`.
  - `python manage.py check_chu_ky_so` in được thống kê ban đầu rồi lỗi cùng nguyên nhân.
- Nguyên nhân: code model đã thêm `file_hash`, `hash_algorithm`, `signature_image`, `verified`, nhưng DB Supabase chưa có cột tương ứng.
- Ảnh hưởng: màn hình hồ sơ cá nhân/chữ ký số hoặc command verify có thể lỗi 500 khi query `LichSuKySo`.
- Cách sửa đề xuất: chạy `python manage.py migrate`, sau đó chạy lại `check_chu_ky_so` và `check_digital_signature_integrity`.

### Lỗi 2: Chức năng ban hành văn bản đi đang bị tắt

- Mức độ: High.
- File liên quan: `apps/quanlyvanbandi/urls.py:14`, `apps/quanlyvanbandi/views.py:465-514`, `apps/templates/vanbandi/popup-ban-hanh.html:432`.
- Mô tả lỗi: route `ban_hanh_van_ban` và view ban hành đang bị comment. Template popup vẫn dùng biến `ban_hanh_url`.
- Nguyên nhân: code chức năng ban hành bị vô hiệu hóa nhưng giao diện vẫn còn phần popup/JS liên quan.
- Ảnh hưởng: văn thư có thể thấy UI ban hành nhưng thao tác ban hành văn bản đi không hoạt động đúng từ màn hình chi tiết.
- Cách sửa đề xuất: khôi phục route/view ban hành hoặc ẩn hoàn toàn popup/nút ban hành nếu chưa dùng.

### Lỗi 3: Upload văn bản đến thiếu kiểm tra phần mở rộng file ở luồng hiện tại

- Mức độ: High.
- File liên quan: `apps/quanlyvanbanden/forms.py`, `apps/quanlyvanbanden/views.py:466-516`, `apps/quanlyvanbanden/views.py:533-616`.
- Bằng chứng bổ sung: `qa_test_outputs/bug_list.csv` ghi `TC-VBDEN-004` lỗi nhận file `malware.exe`.
- Nguyên nhân: form văn bản đến không validate file upload; view lấy `request.FILES` rồi gán `file_dinh_kem`/tạo `VanBanLienQuan` trực tiếp. Validator model legacy `TepVanBanDen.tep` không bảo vệ được luồng đang dùng `core.VanBan`.
- Ảnh hưởng: có thể upload file không mong muốn như `.exe`, rủi ro bảo mật và rủi ro khi serve media.
- Cách sửa đề xuất: thêm validate extension/size ở form hoặc view cho cả file chính và file liên quan; không chỉ dựa vào HTML `accept`.

### Lỗi 4: `seed_demo_data` không import được

- Mức độ: High.
- File liên quan: `apps/core/management/commands/seed_demo_data.py:47-52`.
- Bằng chứng: `python manage.py help seed_demo_data` lỗi `AttributeError: type object 'VanBan' has no attribute 'DON_VI_SOAN_THAO_CHOICES'`.
- Nguyên nhân: command còn tham chiếu choice cũ đã không còn trong `core.VanBan`.
- Ảnh hưởng: không chạy được command seed demo này; sinh viên dễ bị lỗi ngay cả khi chỉ gọi `help`.
- Cách sửa đề xuất: cập nhật command theo field/choices hiện tại hoặc loại command khỏi hướng dẫn nếu không dùng.

### Lỗi 5: SECRET_KEY hard-code và DEBUG=True

- Mức độ: High.
- File liên quan: `he_thong_quan_ly_van_ban/settings.py:24`, `he_thong_quan_ly_van_ban/settings.py:27`.
- Mô tả lỗi: `SECRET_KEY` đang hard-code trong source và `DEBUG=True`.
- Ảnh hưởng: không an toàn nếu deploy hoặc public repo; lỗi debug có thể lộ thông tin nội bộ.
- Cách sửa đề xuất: đọc `SECRET_KEY` và `DEBUG` từ `.env`, bắt buộc production phải `DEBUG=False`.

### Lỗi 6: Git đang tracking nhiều file runtime/media

- Mức độ: High.
- Bằng chứng: `git ls-files` phát hiện 580 artifact được tracking, gồm 73 file `.pyc`, 453 file trong `media`, 54 file `qa_test_outputs/evidence/runtime_media`; `.env` và `db.sqlite3` không bị tracking.
- Ảnh hưởng: repo phình to, dễ lộ tài liệu upload thật, khó review, dễ merge conflict.
- Cách sửa đề xuất: không xóa file ngay; cần lập kế hoạch `git rm --cached` cho `.pyc`, media runtime, staticfiles/evidence runtime sau khi xác nhận với nhóm.

## 3. Lỗi database và migration

- Supabase/PostgreSQL đang được dùng đúng khi `.env` có `DATABASE_URL`.
- `settings.py:106-119` đã dùng `dj_database_url`, `CONN_MAX_AGE=0`, `DISABLE_SERVER_SIDE_CURSORS=True`, và `sslmode=require`. Đây là cấu hình phù hợp hơn cho Supabase transaction pooler.
- Có fallback SQLite ở `settings.py:121-126`. Đây là tốt cho dev, nhưng nếu máy demo thiếu `.env`, app sẽ âm thầm chạy SQLite và sinh viên tưởng đang dùng Supabase.
- Migration hiện tại không conflict theo `showmigrations`, nhưng graph `core` có nhiều nhánh số trùng (`0003`, `0004`, `0005`, `0006`, `0014`) và merge migration. Đây là rủi ro bảo trì, không nên xóa bừa.
- App `hosovanban`, `quanlycongviec`, `quanlyvanbandi` không có migrations vì models hiện trống; logic đang dùng model trong `core`.
- `makemigrations --check --dry-run`: `No changes detected`.
- `migrate --plan`: còn pending `core.0021_lichsukyso_sha256_integrity`.
- Lệnh `migrate` thật chưa chạy trong audit này để tuân thủ yêu cầu không ghi DB.

## 4. Lỗi models và quan hệ dữ liệu

- `core.NguoiDung` liên kết `Customer` bằng `OneToOneField` tại `apps/core/models.py:65-72`. Cơ chế `Customer.sync_core_profile()` tồn tại và DB hiện có 76 `Customer` khớp 76 `NguoiDung`, điểm này tốt.
- `core.ChuKySo` dùng `OneToOneField` tới `NguoiDung` tại `apps/core/models.py:662-668`. Mỗi người dùng có tối đa một chữ ký số, phù hợp yêu cầu cơ bản.
- `core.LichSuKySo` dùng `OneToOneField` tới `VanBan` và `CongViec` tại `apps/core/models.py:696-712`. Điều này làm mỗi văn bản/công việc chỉ có một lịch sử ký. Nếu nghiệp vụ cần nhiều lần ký/nhiều người ký cùng một văn bản, thiết kế này sẽ bị giới hạn.
- `LichSuKySo` có `CheckConstraint` đúng một trong hai đối tượng `van_ban` hoặc `cong_viec`, tốt. DB hiện có `van_ban=65`, `cong_viec=55`, `both=0`, `none=0`.
- `NoiNhanVanBan` có `phong_ban` và `don_vi_ngoai` đều nullable (`apps/core/models.py:320-335`) nhưng chưa có constraint bắt buộc đúng một nơi nhận. Có thể sinh record vừa không có nơi nhận, hoặc vừa có cả hai.
- `VanBan.file_dinh_kem`, `VanBanLienQuan.file_van_ban`, `FileCVLienQuan.file_van_ban` là `FileField` nhưng model `core` chưa có validator extension/size. Một số form có kiểm tra, nhưng model không bảo vệ khi view/seed tạo trực tiếp.
- Tồn tại song song `core.VanBan` dùng cho văn bản đến và model legacy `quanlyvanbanden.VanBanDen`. Điều này có thể gây nhầm giữa dữ liệu mới và dữ liệu cũ.
- `CongViec.van_ban_den` hiện là FK tới `core.VanBan`, tên field dễ gây hiểu nhầm với `quanlyvanbanden.VanBanDen`.

## 5. Lỗi views và phân quyền

### A. Đăng nhập / phân quyền

- Login/logout có cấu trúc tốt: `accounts.views.login_view` dùng `CustomerLoginForm`, `url_has_allowed_host_and_scheme`, `ensure_csrf_cookie`; logout có `login_required`.
- Test hiện có cho login/dashboard chạy pass.
- Redirect sau login đang về `core:dashboard`, không tách riêng trang theo role. Nếu yêu cầu giảng viên là mỗi role vào trang riêng, đây là thiếu chức năng; nếu dashboard role-aware là chủ ý, hiện chấp nhận được.
- `role_required` đang được dùng rộng ở các view chính.

### B. Quản lý người dùng

- Chưa thấy màn hình quản lý user riêng cho ADMIN trong templates/urls. Có Django admin và command seed role/permission.
- Đồng bộ `Customer` và `NguoiDung` hiện ổn theo số lượng DB, nhưng cần kiểm tra khi thêm/sửa user từ Django admin để đảm bảo signal/sync chạy đúng.

### C. Văn bản đi

- Danh sách/tạo/sửa/duyệt/hoàn trả có view và route.
- Ban hành văn bản đi đang bị comment, đây là lỗi chức năng chính.
- Upload file chính văn bản đi có validate extension ở `apps/quanlyvanbandi/forms.py`, điểm này tốt hơn văn bản đến.
- View chi tiết có lọc theo role, nhưng cần test UI thực tế cho từng role sau khi sửa ban hành.

### D. Văn bản đến

- Danh sách/chi tiết/thêm/sửa/xóa/chuyển tiếp/hoàn trả có view.
- Phân quyền xem chi tiết có kiểm tra lãnh đạo/chuyên viên được giao.
- Rủi ro lớn nhất là validate upload file chưa đủ ở luồng tạo/sửa văn bản đến.
- View hiện dùng `core.VanBan` cho văn bản đến, trong khi app vẫn còn model legacy `VanBanDen`; cần thống nhất cách gọi trong tài liệu/seed.

### E. Công việc

- Lãnh đạo giao việc, chuyên viên xử lý, cập nhật kết quả, hoàn trả, duyệt công việc đều có route/view.
- `get_task_detail`, `start_task`, `task_detail` chỉ có `login_required` nhưng có kiểm tra quyền nội bộ; hiện chấp nhận được.
- Form kết quả công việc có validate extension/size cho file kết quả.
- `giao_viec` cho phép `LANH_DAO`, `VAN_THU`, `ADMIN` vào trang, nhưng `add_task` chỉ cho `LANH_DAO`. Nếu UI cho ADMIN/VAN_THU thấy chức năng thêm, sẽ gây nhầm quyền.

### F. Hồ sơ văn bản

- Tạo/sửa/xóa/chi tiết hồ sơ có view và phân quyền.
- `danh_sach` có lọc theo người tạo/người xử lý/phòng ban cho user không phải ADMIN/VAN_THU.
- Dashboard lại dùng `HoSoVanBan.objects.all()` để tính tổng hồ sơ cho mọi role (`apps/core/views.py:662`), có thể làm lộ số liệu tổng nếu muốn phân quyền nghiêm.

### G. Hồ sơ cá nhân

- Đã có route `accounts:profile` và template `apps/templates/accounts/profile.html`.
- View hồ sơ cá nhân gọi `verify_signed_file(history)` khi render. Hàm này mặc định `persist=True` và có thể ghi `verified` vào DB trong request GET. Nên chuyển sang `persist=False` khi chỉ hiển thị, hoặc tách verify ghi DB sang command.
- Trước khi apply migration 0021, trang hồ sơ có nguy cơ lỗi nếu query lịch sử ký số.

## 6. Lỗi template/url

- `python manage.py check` không phát hiện lỗi URL config.
- URL chính include nhiều app ở root path nhưng có namespace, chưa thấy trùng name gây lỗi ngay.
- `he_thong_quan_ly_van_ban/urls.py:20` serve media bằng `static()` không bọc `if settings.DEBUG`. Nên chỉ serve media kiểu này khi DEBUG=True.
- `popup-ban-hanh.html` dùng `BAN_HANH_URL="{{ ban_hanh_url }}"` trong khi context `ban_hanh_url` bị comment ở `quanlyvanbandi.views`. Đây là lỗi UI ban hành.
- `accounts/profile.html` dùng `item.file_hash`, `item.file_da_ky.url`, `signature.anh_chu_ky.url`. Template có guard cơ bản cho file, nhưng DB thiếu cột `file_hash` trước migration.
- Các form POST chính đã thấy có `csrf_token`. Chưa phát hiện form POST rõ ràng thiếu CSRF trong lần quét này.
- Một số template wrapper cấp root như `van-ban-den.html`, `giao-viec.html`, `xu-ly-cong-viec.html`, `ho-so-van-ban.html` chỉ chuyển hướng/mở màn hình chính; không lỗi, nhưng nên dọn hoặc ghi rõ nếu không dùng.

## 7. Lỗi media/file upload

- `MEDIA_URL=/media/`, `MEDIA_ROOT=<project>/media` đúng.
- DB file path kiểm tra 610 record: không thấy đường dẫn tuyệt đối `D:\...`, không thấy file thiếu.
- File trong DB hiện đang tồn tại trong media: tốt.
- Rủi ro: nhiều file media đang bị Git tracking, không nên đưa vào repo lâu dài.
- Rủi ro upload:
  - Văn bản đi: có validate extension `.pdf`, `.docx`, `.xlsx`.
  - Công việc: có validate extension `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`.
  - Văn bản đến: chưa validate đầy đủ file chính/file liên quan trong view/form hiện tại.
- Không nên serve file upload trực tiếp trong production bằng `static(settings.MEDIA_URL, ...)`; nên dùng web server/storage riêng.

## 8. Lỗi seed data

| Command | Trạng thái kiểm tra | Nhận xét |
|---|---|---|
| `seed_roles_permissions` | `help` chạy được | Tạo/sync group/permission và gán group cho user. Có ghi DB nên không chạy thật trong audit. |
| `seed_accounts` | `help` chạy được | Tạo/cập nhật tài khoản mẫu nhưng dùng `DEFAULT_PASSWORD = "123"`; có nhánh xóa user/profile ngoài spec, cần cẩn trọng khi chạy Supabase thật. |
| `seed_demo_data` | Lỗi ngay khi import/help | Gọi `VanBan.DON_VI_SOAN_THAO_CHOICES` không còn tồn tại. |
| `seed_data` | `help` chạy được | Có option `--clear`; code có đoạn xóa `NguoiDung`, `PhongBan`, `DonViNgoai`, `ChiNhanh`, user không superuser. Không dùng trên DB thật nếu không muốn reset. |
| `seed_role_based_data` | `help` chạy được | ORM/upsert tốt hơn, nhưng default password là `"123"` nếu thiếu `ROLE_SEED_PASSWORD`. |
| `seed_chu_ky_so` | `help` chạy được | Có transaction/upsert, nhưng phải chạy sau `migrate` vì DB đang thiếu cột SHA-256. |
| `check_database_status` | Chạy được | In đúng DB PostgreSQL/Supabase, số record và media. |
| `check_seed_data` | Chạy được | In được số liệu theo role và bảng chính. |
| `check_chu_ky_so` | Lỗi một phần | Thống kê được số lượng chữ ký nhưng crash khi query field `file_hash` chưa có trong DB. |
| `check_digital_signature_integrity` | Lỗi | Crash vì DB thiếu cột `LichSuKySo.file_hash`. |
| `import_old_data_safe` | `help` chạy được | Không chạy thật vì có ghi DB. `old_data.json` chỉ có user/phòng ban/chi nhánh, thiếu văn bản/file/công việc. |
| `rebuild_media_records` | `help` chạy được | Có thể tạo record từ media, không chạy thật trong audit. |

Ghi chú: `old_data.json` đang tồn tại local, có 156 object gồm `accounts.customer`, `core.nguoidung`, `core.chinhanh`, `core.phongban`; không có dữ liệu văn bản/file/công việc. File này không thấy Git tracking, nhưng vẫn là artifact nhạy cảm cần quản lý.

## 9. Lỗi chữ ký số

- `ChuKySo`: DB hiện có 76 bản ghi, khớp số user/profile.
- `LichSuKySo`: DB hiện có 120 bản ghi, theo role:
  - ADMIN: 30
  - LANH_DAO: 30
  - VAN_THU: 30
  - CHUYEN_VIEN: 30
- Lịch sử ký gắn `VanBan`: 65; gắn `CongViec`: 55; không có bản ghi vừa gắn cả hai hoặc để cả hai null.
- Constraint model hiện đúng theo yêu cầu “một bản ghi chỉ ký một loại đối tượng”.
- Lỗi chính: code SHA-256 đã có nhưng migration chưa apply, làm command/profile lỗi.
- `verify_signed_file()` hiện cập nhật `verified` vào DB nếu khác trạng thái cũ. Việc gọi hàm này trong `profile_view` khi GET làm view vừa đọc vừa ghi.
- `LichSuKySo` dùng `OneToOneField` tới văn bản/công việc. Nếu sau này cần nhiều lần ký cùng tài liệu, cần đổi sang `ForeignKey` và thêm logic phân biệt lần ký/người ký.

## 10. Rủi ro bảo mật

- `SECRET_KEY` hard-code trong source.
- `DEBUG=True`.
- Demo password hard-code `"123"` ở `seed_accounts.py`, `seed_demo_data.py`, và fallback của `seed_role_based_data.py`.
- Template OTP demo hard-code mã `123456` tại `apps/templates/core/otp.html:156` và JS kiểm tra `123456` tại dòng 258.
- Upload văn bản đến chưa chặn file độc hại ở server side.
- Media được serve trực tiếp bởi Django URL config không phân biệt DEBUG.
- `.env` không bị Git tracking theo kiểm tra hiện tại, đây là điểm tốt.
- `db.sqlite3` không bị Git tracking theo kiểm tra hiện tại, đây là điểm tốt.
- Có nhiều file media/runtime đang bị Git tracking, có thể chứa tài liệu upload hoặc evidence test.

## 11. Chức năng đang hoạt động tốt

- `python manage.py check`: không có lỗi.
- `python manage.py makemigrations --check --dry-run`: không phát hiện model change chưa tạo migration.
- Test suite hiện có: 24 test pass khi chạy bằng SQLite in-memory.
- `runserver` smoke test: login page trả HTTP 200, dashboard chưa login redirect 302 về login.
- Kết nối Supabase/PostgreSQL đang dùng đúng engine và host pooler.
- Cấu hình Supabase có `CONN_MAX_AGE=0`, `DISABLE_SERVER_SIDE_CURSORS=True`, `sslmode=require`.
- `Customer` và `NguoiDung` đang đồng bộ số lượng 76/76.
- Media record kiểm tra mẫu không có file thiếu hoặc path tuyệt đối.
- Constraint `LichSuKySo` hiện không có dữ liệu sai.
- Văn bản đi và công việc có validate file upload ở form.

## 12. Thứ tự ưu tiên sửa lỗi

| STT | Lỗi | Mức độ | File | Cách sửa ngắn gọn | Ưu tiên |
|---:|---|---|---|---|---|
| 1 | DB thiếu cột SHA-256 chữ ký số | Critical | `apps/core/migrations/0021_lichsukyso_sha256_integrity.py` | Chạy `migrate`, sau đó chạy lại check chữ ký | P0 |
| 2 | Command verify/check chữ ký số crash | Critical | `check_digital_signature_integrity.py`, `check_chu_ky_so.py` | Sau migrate, bổ sung guard schema hoặc thông báo thân thiện | P0 |
| 3 | Ban hành văn bản đi bị comment | High | `quanlyvanbandi/urls.py`, `views.py`, `popup-ban-hanh.html` | Khôi phục view/route hoặc ẩn UI | P1 |
| 4 | Upload văn bản đến nhận file sai loại | High | `quanlyvanbanden/forms.py`, `views.py` | Validate extension/size cho file chính và liên quan | P1 |
| 5 | `seed_demo_data` lỗi import | High | `seed_demo_data.py` | Cập nhật theo model hiện tại hoặc loại khỏi hướng dẫn | P1 |
| 6 | `SECRET_KEY`, `DEBUG`, password demo hard-code | High | `settings.py`, seed commands | Đưa vào `.env`, đổi default password | P1 |
| 7 | File media/pyc đang bị Git tracking | High | Git index | Lập kế hoạch `git rm --cached`, cập nhật `.gitignore` | P2 |
| 8 | Dashboard đếm tất cả hồ sơ cho mọi role | Medium | `apps/core/views.py` | Dùng queryset hồ sơ theo quyền user | P2 |
| 9 | `verify_signed_file` ghi DB trong GET profile | Medium | `accounts/views.py`, `digital_signature.py` | Dùng `persist=False` khi render | P2 |
| 10 | `NoiNhanVanBan` thiếu constraint nơi nhận | Medium | `apps/core/models.py` | Thêm `CheckConstraint` đúng một nơi nhận | P3 |
| 11 | `LichSuKySo` chỉ cho một lần ký mỗi đối tượng | Medium | `apps/core/models.py` | Đánh giá nghiệp vụ, đổi `ForeignKey` nếu cần nhiều chữ ký | P3 |

## 13. Các lệnh nên chạy để kiểm tra

Chạy trong PowerShell:

```powershell
cd D:\LapTrinhWeb_Nhom3\he_thong_quan_ly_van_ban

# Kiểm tra cấu hình/model không ghi DB
py -3 manage.py check
py -3 manage.py makemigrations --check --dry-run
py -3 manage.py showmigrations
py -3 manage.py migrate --plan

# Apply migration còn thiếu trước khi kiểm chữ ký số
py -3 manage.py migrate

# Kiểm tra dữ liệu và chữ ký số
py -3 manage.py check_database_status
py -3 manage.py check_seed_data
py -3 manage.py check_chu_ky_so
py -3 manage.py check_digital_signature_integrity

# Test hiện có
$env:DATABASE_URL='sqlite:///:memory:'
py -3 manage.py test --verbosity 1
Remove-Item Env:\DATABASE_URL

# Chạy server demo
py -3 manage.py runserver
```

Nếu cần seed lại dữ liệu demo, nên đặt password demo qua env trước:

```powershell
$env:ROLE_SEED_PASSWORD='MatKhauDemoManhHon'
py -3 manage.py seed_roles_permissions
py -3 manage.py seed_role_based_data --per-role 25
py -3 manage.py seed_chu_ky_so --per-role 25
```

Không nên chạy trên Supabase thật nếu chưa hiểu tác động:

```powershell
py -3 manage.py seed_data --clear
py -3 manage.py seed_demo_data
```

## 14. Kết luận

Project hiện không bị lỗi startup cơ bản: `check`, `makemigrations --check`, test suite và runserver smoke test đều ổn. Vấn đề lớn nhất là code chữ ký số đã đi trước schema Supabase: migration `core.0021` chưa apply nên các command và màn hình liên quan chữ ký số sẽ lỗi khi chạm `file_hash`.

Sau lỗi migration, nhóm nên ưu tiên sửa luồng ban hành văn bản đi, validate upload văn bản đến, và dọn command seed bị lỗi hoặc có nguy cơ reset dữ liệu. Về bảo mật, cần đưa `SECRET_KEY`/`DEBUG`/password demo ra `.env` và xử lý Git tracking media/runtime trước khi nộp hoặc demo với dữ liệu thật.
