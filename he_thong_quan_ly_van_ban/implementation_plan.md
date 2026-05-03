# Điều chỉnh luồng Ban Hành và Phê Duyệt Văn bản đi

Theo yêu cầu mới của bạn, luồng "Ban hành" văn bản đi sẽ được thay đổi hoàn toàn: không còn tạo ra các bản sao (Văn bản đến) để gửi cho từng cá nhân nữa. Thay vào đó, văn bản đi sẽ đóng vai trò như một bảng tin dùng chung cho những người được phép tiếp cận.

## User Review Required
- **Trạng thái hiển thị ở màn hình Danh sách**: Với người nhận (các nhân viên thuộc phòng ban có trong danh sách nơi nhận nội bộ), văn bản đi này sẽ hiển thị trạng thái là **"Xem để biết"** trên màn hình danh sách, dù trạng thái thực sự lưu trong cơ sở dữ liệu của văn bản là **"Đã ban hành"**. Bạn có đồng ý với cách hiển thị này không?
- **Danh sách văn bản đến**: Vì không còn nhân bản thành Văn bản đến nữa, những văn bản nội bộ này sẽ **không xuất hiện ở màn hình Văn bản đến** của người nhận, mà họ phải vào màn hình **Văn bản đi** (hoặc Trang chủ) để xem. Bạn xác nhận điều này đúng không?

## Proposed Changes

### `quanlyvanbandi` (Backend)

#### [MODIFY] [views.py](file:///g:/DUE/MonHoc/LapTrinhWeb/LapTrinhWeb_Nhom3/he_thong_quan_ly_van_ban/apps/quanlyvanbandi/views.py)
- **Hàm `ban_hanh_van_ban`**: 
  - **[XÓA]** Bỏ hoàn toàn vòng lặp tạo mới `Văn bản đến` (`VanBan.objects.create(phan_loai='Văn bản đến')`) và logic tạo `ChuyenTiep`, copy `VanBanLienQuan`, `LichSuKySo`.
  - **[GIỮ LẠI]** Chỉ cập nhật `trang_thai` của văn bản gốc thành `"Đã ban hành"`, tạo bản ghi `BanHanh` và ghi log lịch sử hoạt động.
- **Hàm `chi_tiet_van_ban_di`**:
  - Điều chỉnh biến `hien_thi_trang_thai`: Nếu người dùng hiện tại thuộc phòng ban nhận (`is_in_receiving_dept` = True) và KHÔNG PHẢI là người tạo/người duyệt/văn thư xử lý, thì `hien_thi_trang_thai` sẽ ép hiển thị thành `"Xem Để Biết"` (thay vì "Đã Xử Lý" hay "Đã ban hành").
- **Hàm `van_ban_di` (Danh sách)**:
  - Cập nhật logic để truyền thêm thông tin nhận biết văn bản nào người dùng đang xem dưới tư cách là "người nhận" (thuộc phòng ban nhận) để giao diện hiển thị trạng thái "Xem để biết".

### `quanlyvanbandi` (Frontend)

#### [MODIFY] [van-ban-di.html](file:///g:/DUE/MonHoc/LapTrinhWeb/LapTrinhWeb_Nhom3/he_thong_quan_ly_van_ban/apps/templates/vanbandi/van-ban-di.html)
- Ở cột "Trạng thái", bổ sung logic Jinja: Nếu văn bản này người dùng đang xem dưới tư cách là "người nhận", thì render badge có chữ **"Xem để biết"** (màu xám/xanh dương) thay vì in ra trạng thái gốc ("Đã ban hành").

## Verification Plan

### Manual Verification
1. Dùng tài khoản Chuyên viên tạo 1 văn bản đi, chọn Nơi nhận là "Phòng Kế toán". Trình cho Lãnh đạo.
2. Dùng tài khoản Lãnh đạo để **Phê duyệt**, chuyển cho Văn thư.
3. Dùng tài khoản Văn thư để **Ban hành**. Xác minh không có bản ghi Văn bản đến nào được tạo ra trong hệ thống.
4. Dùng tài khoản Chuyên viên thuộc "Phòng Kế toán" đăng nhập:
   - Vào màn hình **Văn bản đi**, thấy văn bản vừa ban hành xuất hiện.
   - Trạng thái hiển thị ở danh sách và chi tiết đều là **Xem để biết**.
   - Cố gắng thao tác các nút khác (sẽ không có, chỉ được xem).
