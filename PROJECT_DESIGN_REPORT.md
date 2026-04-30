# Báo cáo lỗi thiết kế UI/UX Project

Thời điểm kiểm tra: 01/05/2026. Phạm vi: rà soát template, CSS, JavaScript giao diện và smoke test trang login/static. Báo cáo này chỉ đánh giá thiết kế, trải nghiệm người dùng, khả năng responsive và khả năng bảo trì giao diện; không sửa code.

## 1. Tổng quan giao diện

- Tổng template HTML: 46 file.
- Tổng CSS chính: 2 file (`style.css`, `them-ho-so-van-ban.css`).
- `apps/static/assets/css/style.css`: khoảng 3229 dòng, 721 giá trị `px`, 244 literal màu, 6 `@media`.
- `apps/static/assets/css/them-ho-so-van-ban.css`: khoảng 380 dòng, 91 giá trị `px`, 42 literal màu.
- Trang login và file CSS global trả HTTP 200 khi chạy server tạm.
- Nhận xét tổng quan: giao diện có bố cục nghiệp vụ đầy đủ, nhưng đang thiếu một design system nhất quán. Nhiều màn hình dùng CSS inline và style riêng từng template, dẫn đến các màn hình giống cùng một hệ thống nhưng cảm giác không đồng bộ.

## 2. Lỗi nghiêm trọng về thiết kế cần ưu tiên

### 2.1. Giao diện thiếu design system thống nhất

- Mức độ: High.
- File liên quan:
  - `apps/static/assets/css/style.css`
  - `apps/templates/van_ban_den/*/chi_tiet.html`
  - `apps/templates/vanbandi/chi-tiet-van-ban-di.html`
  - `apps/templates/quanlycongviec/chi-tiet-cong-viec.html`
  - `apps/templates/hosovanban/chi-tiet-*.html`
- Bằng chứng:
  - Có nhiều loại component trùng chức năng: `card`, `filter-card`, `surface-card`, `profile-panel`, `btn`, `btn-local`, `popup`, `modal`, `delete-modal`.
  - Nhiều template tự khai báo `<style>` riêng thay vì dùng class chung.
- Ảnh hưởng: người dùng cảm giác mỗi module là một giao diện khác nhau; khi sửa theme hoặc responsive phải sửa nhiều nơi.
- Đề xuất: chuẩn hóa bộ component chung: button, card, table, badge, modal, form, file-preview, toolbar.

### 2.2. Quá nhiều inline CSS trong template

- Mức độ: High.
- File có nhiều inline style nhất:

| File | Số dòng | `style=` |
|---|---:|---:|
| `apps/templates/hosovanban/chi-tiet-van-ban.html` | 206 | 72 |
| `apps/templates/hosovanban/chi-tiet-ho-so-van-ban.html` | 177 | 64 |
| `apps/templates/vanbandi/chi-tiet-van-ban-di.html` | 925 | 48 |
| `apps/templates/vanbandi/popup-ban-hanh.html` | 858 | 13 |
| `apps/templates/van_ban_den/vanthu/chi_tiet.html` | 1033 | 11 |

- Ảnh hưởng: khó responsive, khó đổi màu/theme, khó test giao diện, dễ có style lệch giữa màn hình.
- Đề xuất: chuyển style inline sang class trong CSS chung hoặc CSS theo module có quy ước.

### 2.3. Template quá dài, trộn HTML/CSS/JS trong cùng file

- Mức độ: High.
- File dài nhất:

| File | Số dòng | Vấn đề |
|---|---:|---|
| `apps/templates/van_ban_den/vanthu/chi_tiet.html` | 1033 | HTML + CSS + JS preview file cùng file |
| `apps/templates/vanbandi/chi-tiet-van-ban-di.html` | 925 | nhiều popup/preview/script trong một template |
| `apps/templates/vanbandi/popup-ban-hanh.html` | 858 | popup quá lớn, không extend layout |
| `apps/templates/van_ban_den/chuyenvien/chi_tiet.html` | 764 | lặp logic preview |
| `apps/templates/van_ban_den/lanhdao/chi_tiet.html` | 712 | lặp logic preview |

- Ảnh hưởng: khó review, khó tìm lỗi visual, dễ sửa một role nhưng quên role khác.
- Đề xuất: tách partial/template component: `file_preview.html`, `document_info_panel.html`, `action_toolbar.html`, `delete_modal.html`; đưa JS preview ra file static.

### 2.4. Responsive mobile chưa tốt

- Mức độ: High.
- File liên quan: `apps/static/assets/css/style.css:1455-1478`, `apps/static/assets/css/style.css:3179-3230`.
- Mô tả:
  - Ở màn hình dưới 768px, `.app-sidebar` bị `display: none`, nhưng không có hamburger/menu thay thế.
  - Top nav chỉ scroll ngang; người dùng mobile có thể không biết còn menu bên phải.
  - Nhiều bảng dùng `min-width: 900px`, modal có width lớn, preview có `min-height` lớn.
- Ảnh hưởng: người dùng điện thoại khó điều hướng giữa văn bản đến, văn bản đi, công việc, hồ sơ.
- Đề xuất: thêm mobile drawer hoặc bottom navigation; giữ nút menu rõ ràng trên header; tối ưu bảng thành card list trên mobile.

### 2.5. Màn hình dashboard có phong cách lệch so với app nghiệp vụ

- Mức độ: Medium.
- File liên quan: `apps/templates/core/dashboard.html`.
- Bằng chứng:
  - Số liệu dùng font `54px`, card bo góc `18px`, shadow lớn.
  - Trong khi global radius là `4px` và các màn hình nghiệp vụ khác dùng style utilitarian hơn.
- Ảnh hưởng: dashboard nhìn hiện đại nhưng lệch khỏi các module còn lại; cảm giác sản phẩm thiếu thống nhất.
- Đề xuất: giảm bo góc/card shadow, dùng cùng token radius, spacing, typography với module văn bản/công việc.

## 3. Lỗi điều hướng và bố cục

### 3.1. Có các trang wrapper không còn là màn hình thật

- Mức độ: Medium.
- File liên quan:
  - `apps/templates/van-ban-den.html`
  - `apps/templates/giao-viec.html`
  - `apps/templates/xu-ly-cong-viec.html`
  - `apps/templates/ho-so-van-ban.html`
- Mô tả: các trang này chỉ hiển thị thông báo “chức năng đang sử dụng giao diện danh sách mới” và nút mở trang khác.
- Ảnh hưởng: nếu user đi nhầm route sẽ thấy màn hình trung gian không cần thiết, làm trải nghiệm giống bản demo chưa hoàn thiện.
- Đề xuất: redirect thẳng ở view/URL hoặc bỏ khỏi menu nếu không dùng.

### 3.2. Sidebar biến mất trên mobile

- Mức độ: High.
- File liên quan: `apps/static/assets/css/style.css:1471`.
- Mô tả: `.app-sidebar { display: none; }` nhưng không có menu thay thế.
- Ảnh hưởng: user mobile mất điều hướng phụ.
- Đề xuất: dùng drawer mở từ nút menu trên header.

### 3.3. Header có nguy cơ bị chật trên màn hình nhỏ

- Mức độ: Medium.
- File liên quan: `apps/templates/base.html`, `apps/static/assets/css/style.css`.
- Mô tả: brand title dài, user dropdown, top nav cùng chiếm chiều ngang. Header có ellipsis nhưng không giải quyết được việc top nav phải scroll ngang.
- Đề xuất: trên mobile chỉ hiển thị logo ngắn + nút menu + avatar; chuyển top nav vào drawer.

### 3.4. Có nút nhìn giống thao tác nhưng chưa rõ hành động

- Mức độ: Medium.
- File liên quan: `apps/templates/van_ban_den/vanthu/chi_tiet.html`.
- Ví dụ: nút “Lưu hồ sơ” là `<button type="button">` nhưng không thấy action/form/onClick trực tiếp trong đoạn template.
- Ảnh hưởng: user bấm nhưng không có phản hồi sẽ tưởng hệ thống lỗi.
- Đề xuất: nếu chưa có chức năng thì ẩn nút; nếu có thì gắn action rõ ràng và trạng thái loading/thành công.

## 4. Lỗi màu sắc, typography và spacing

### 4.1. Màu sắc bị phân mảnh

- Mức độ: Medium.
- Bằng chứng: toàn bộ template/CSS có nhiều literal màu lặp lại: `#fff`, `#64748b`, `#0076A2`, `#D1D5DC`, `#0f172a`, `#334155`, `#0284C7`, `#ef4444`, `#EF4444`, `#CBD5E1`, ...
- Vấn đề: cùng màu/ý nghĩa nhưng viết nhiều biến thể hoa-thường hoặc gần giống nhau.
- Ảnh hưởng: khó đảm bảo contrast và khó đổi theme.
- Đề xuất: gom vào CSS variables: primary, success, danger, warning, border, text, muted, surface.

### 4.2. Typography không đồng đều giữa các màn hình

- Mức độ: Medium.
- Ví dụ:
  - Dashboard dùng số liệu rất lớn.
  - Màn chi tiết văn bản/công việc dùng nhiều cỡ chữ 13/14/15/16/18 lẫn inline.
  - Một số nút dùng chữ thường, một số dùng in hoa.
- Ảnh hưởng: người dùng khó quét thông tin nhất quán.
- Đề xuất: định nghĩa scale: page title, section title, label, body, table cell, badge, helper text.

### 4.3. Bo góc và shadow không thống nhất

- Mức độ: Low/Medium.
- Ví dụ:
  - Global `--radius: 4px`.
  - Dashboard card `border-radius: 18px`.
  - Profile avatar/card/pill dùng style khác.
- Ảnh hưởng: giao diện nhìn pha nhiều style.
- Đề xuất: dùng 4px hoặc 6px cho app nghiệp vụ; chỉ dùng radius lớn cho avatar hoặc element đặc biệt.

## 5. Lỗi table/list và khả năng đọc dữ liệu

### 5.1. Bảng có xu hướng phụ thuộc horizontal scroll

- Mức độ: Medium.
- File liên quan: `style.css` có `table.data-table { min-width: 900px; }`.
- Ảnh hưởng: trên laptop nhỏ/mobile user phải kéo ngang, dễ mất cột thao tác.
- Đề xuất: thêm sticky action column, hoặc chuyển danh sách mobile thành card rows.

### 5.2. Text dài có thể bị cắt quá sớm

- Mức độ: Medium.
- File liên quan: `.table-text-truncate`, các field `trich_yeu`, tên file, tiêu đề công việc.
- Ảnh hưởng: hệ thống quản lý văn bản cần đọc trích yếu rõ; cắt quá nhiều làm giảm khả năng xử lý.
- Đề xuất: dùng 2-line clamp cho trích yếu; tooltip hoặc expand inline.

### 5.3. Trạng thái/badge chưa chuẩn hóa toàn hệ thống

- Mức độ: Medium.
- Mô tả: trạng thái văn bản đi, văn bản đến, công việc, hồ sơ có nhiều class/badge riêng.
- Ảnh hưởng: cùng ý nghĩa “Chờ xử lý”, “Hoàn trả”, “Đã xử lý” có thể khác màu hoặc khác chữ.
- Đề xuất: tạo mapping trạng thái chung: pending, approved, returned, issued, overdue, completed.

## 6. Lỗi modal, popup và preview file

### 6.1. Modal/popup có nhiều hệ riêng

- Mức độ: High.
- File liên quan:
  - `style.css`: `.modal-overlay`, `.app-confirm-overlay`, `.popup-overlay`
  - `apps/static/assets/css/them-ho-so-van-ban.css`
  - `apps/templates/vanbandi/popup-*.html`
  - `apps/templates/van_ban_den/*/_modal_*.html`
- Bằng chứng: z-index khác nhau như 500, 600, 9999; class và cấu trúc modal không thống nhất.
- Ảnh hưởng: dễ lỗi popup nằm sau overlay, không scroll được, hoặc đóng/mở không đồng nhất.
- Đề xuất: chỉ dùng một modal system chung với size `sm/md/lg/full`, header/body/footer chuẩn.

### 6.2. Preview file bị lặp ở nhiều role

- Mức độ: High.
- File liên quan:
  - `van_ban_den/vanthu/chi_tiet.html`
  - `van_ban_den/lanhdao/chi_tiet.html`
  - `van_ban_den/chuyenvien/chi_tiet.html`
  - `vanbandi/chi-tiet-van-ban-di.html`
  - `quanlycongviec/chi-tiet-cong-viec.html`
- Mô tả: PDF/DOCX/XLSX preview được viết lại ở nhiều template.
- Ảnh hưởng: sửa lỗi preview ở một nơi không áp dụng cho nơi khác; giao diện preview không nhất quán.
- Đề xuất: tạo component preview chung và một file JS chung.

### 6.3. Có phụ thuộc CDN ngoài trong màn hình preview

- Mức độ: Medium.
- File liên quan:
  - `van_ban_den/vanthu/chi_tiet.html`
  - `van_ban_den/lanhdao/chi_tiet.html`
  - `van_ban_den/chuyenvien/chi_tiet.html`
  - `style.css` import Google Fonts
  - `quanlycongviec/chi-tiet-cong-viec.html` dùng icon từ Wikimedia
- Ảnh hưởng: nếu phòng lab mất internet hoặc CDN chậm, font/icon/preview có thể hỏng.
- Đề xuất: dùng vendor local đã có trong `apps/static/vendor` và icon inline/local nhất quán.

## 7. Lỗi accessibility

### 7.1. Nhiều nút icon thiếu nhãn truy cập

- Mức độ: Medium.
- Ví dụ:
  - Nút `×`, `◀`, `▶` trong popup/preview.
  - `apps/templates/quanlycongviec/chi-tiet-cong-viec.html` có button chỉ chứa SVG.
- Ảnh hưởng: screen reader không đọc được ý nghĩa nút; người dùng keyboard khó hiểu.
- Đề xuất: thêm `aria-label`, `title`, hoặc text ẩn `.sr-only`.

### 7.2. Một số iframe thiếu `title`

- Mức độ: Medium.
- File có dấu hiệu:
  - `apps/templates/hosovanban/chi-tiet-van-ban.html`
  - `apps/templates/quanlycongviec/chi-tiet-cong-viec.html`
  - `apps/templates/quanlycongviec/giao-viec.html`
- Ảnh hưởng: không đạt accessibility cơ bản.
- Đề xuất: thêm `title="Xem trước tài liệu"` hoặc title cụ thể.

### 7.3. Clickable row dùng `onclick` không thân thiện keyboard

- Mức độ: Medium.
- File liên quan:
  - `apps/templates/hosovanban/ho-so-van-ban.html`
  - `apps/templates/hosovanban/chi-tiet-ho-so-van-ban.html`
  - `apps/templates/vanbandi/van-ban-di.html`
- Ảnh hưởng: user dùng bàn phím không mở được row như người dùng chuột.
- Đề xuất: dùng thẻ `<a>` trong cell chính, hoặc thêm `tabindex="0"` và handler Enter/Space.

### 7.4. Link disabled bằng `onclick="return false"`

- Mức độ: Low/Medium.
- File liên quan: `apps/templates/base.html`.
- Mô tả: menu disabled vẫn là thẻ `<a>`, dùng `aria-disabled` và `onclick`.
- Ảnh hưởng: screen reader/keyboard có thể vẫn focus vào mục không dùng được.
- Đề xuất: render `<span>`/`button disabled` cho item không có quyền, hoặc bỏ khỏi DOM nếu không cần hiển thị.

## 8. Lỗi UX theo chức năng

### 8.1. Chức năng chữ ký số trong profile còn thiên về dữ liệu, chưa đủ thao tác

- Mức độ: Medium.
- File liên quan: `apps/templates/accounts/profile.html`, CSS `.profile-*`.
- Mô tả: profile hiển thị chữ ký số và 5 lịch sử gần nhất, nhưng chưa có CTA rõ: cập nhật ảnh chữ ký, xem toàn bộ lịch sử, lọc lịch sử ký, kiểm tra toàn vẹn.
- Ảnh hưởng: user khó hiểu đây là màn thông tin hay màn quản lý chữ ký.
- Đề xuất: thêm tab “Thông tin cá nhân / Chữ ký số / Lịch sử ký”; thêm nút “Xem tất cả lịch sử ký”.

### 8.2. Hồ sơ cá nhân dùng role code thay vì nhãn đẹp

- Mức độ: Low.
- File liên quan: `apps/templates/accounts/profile.html`.
- Mô tả: pill hiển thị `{{ profile_user.role }}` như `LANH_DAO`, `VAN_THU`.
- Ảnh hưởng: chưa thân thiện với người dùng cuối.
- Đề xuất: dùng `{{ profile_user.get_role_display }}` hoặc `display_role`.

### 8.3. Thông báo trạng thái chưa có pattern thống nhất

- Mức độ: Medium.
- File liên quan: `base.html`, các template có modal/toast riêng.
- Mô tả: có Django messages, toast JS, confirm modal, delete modal riêng.
- Ảnh hưởng: sau thao tác, user có lúc thấy message auto-hide, có lúc modal, có lúc redirect không rõ.
- Đề xuất: thống nhất feedback: success toast, error banner, destructive confirm modal.

### 8.4. File preview chiếm nhiều chiều cao

- Mức độ: Medium.
- File liên quan: các màn chi tiết văn bản/công việc.
- Mô tả: preview có `min-height` lớn, canvas/iframe lớn. Với màn hình nhỏ, thông tin chính và thao tác có thể bị đẩy xuống xa.
- Đề xuất: dùng layout split có panel thông tin cố định, preview có chiều cao theo viewport; thêm nút collapse preview.

## 9. Lỗi bảo trì giao diện

### 9.1. CSS global quá lớn và chứa cả style module cụ thể

- Mức độ: High.
- File liên quan: `apps/static/assets/css/style.css`.
- Mô tả: `style.css` vừa là reset/layout/base, vừa chứa dashboard, profile, table, modal, form, chức năng riêng.
- Ảnh hưởng: sửa CSS dễ ảnh hưởng ngoài ý muốn.
- Đề xuất cấu trúc lại:
  - `base.css`
  - `layout.css`
  - `components/buttons.css`
  - `components/forms.css`
  - `components/tables.css`
  - `components/modals.css`
  - `pages/dashboard.css`
  - `pages/profile.css`

### 9.2. JavaScript inline trong template nhiều

- Mức độ: Medium.
- File liên quan: các template chi tiết và popup.
- Ảnh hưởng: khó cache, khó test, khó tái sử dụng.
- Đề xuất: chuyển JS preview/modal/form dynamic ra `apps/static/assets/js/`.

### 9.3. Trộn nhiều nguồn icon

- Mức độ: Medium.
- Mô tả: có inline SVG, ký tự Unicode `×`, `◀`, `▶`, icon Wikimedia, icon trong CSS data-uri.
- Ảnh hưởng: icon không đồng bộ về nét, kích thước, màu.
- Đề xuất: thống nhất một bộ icon local/inline.

## 10. Điểm thiết kế đang ổn

- Login page có bố cục rõ, form đơn giản, có CSRF, CSS global serve được.
- Layout app đã có header, top nav, sidebar, content, breadcrumb; đây là nền tốt để chuẩn hóa.
- Có CSS variables cho màu chính, border, background, text, radius.
- Dashboard có dữ liệu phân nhóm rõ: metric, biểu đồ, trạng thái, tài liệu gần đây, công việc gấp.
- Profile page đã có cấu trúc thông tin cá nhân, thống kê, chữ ký số.
- Một số màn hình đã có responsive breakpoint riêng, ví dụ dashboard và chi tiết văn bản đi.
- File upload/preview có ý tưởng tốt cho nghiệp vụ quản lý văn bản, chỉ cần chuẩn hóa lại.

## 11. Thứ tự ưu tiên sửa design

| STT | Vấn đề | Mức độ | File chính | Cách sửa ngắn gọn | Ưu tiên |
|---:|---|---|---|---|---|
| 1 | Thiếu navigation mobile khi ẩn sidebar | High | `style.css`, `base.html` | Thêm hamburger drawer/mobile menu | P0 |
| 2 | Ban hành/preview/modal nhiều hệ khác nhau | High | `popup-*.html`, `style.css` | Tạo modal component chung | P0 |
| 3 | Inline CSS quá nhiều | High | nhiều template | Chuyển sang class/component CSS | P1 |
| 4 | Template chi tiết quá dài | High | `vanthu/chi_tiet.html`, `chi-tiet-van-ban-di.html` | Tách partial + JS static | P1 |
| 5 | Preview file lặp ở nhiều role | High | `van_ban_den/*/chi_tiet.html` | Tạo `file_preview` dùng chung | P1 |
| 6 | Dashboard lệch style so với module nghiệp vụ | Medium | `core/dashboard.html` | Giảm radius/shadow/font quá lớn | P2 |
| 7 | Màu/typography phân mảnh | Medium | `style.css`, templates | Chuẩn hóa design token | P2 |
| 8 | Accessibility nút icon/iframe/clickable row | Medium | nhiều template | Thêm `aria-label`, `title`, keyboard support | P2 |
| 9 | Wrapper pages gây cảm giác chưa hoàn thiện | Medium | `van-ban-den.html`, `giao-viec.html` | Redirect hoặc bỏ khỏi navigation | P3 |
| 10 | CDN ngoài cho preview/icon/font | Medium | chi tiết văn bản, `style.css` | Dùng asset local | P3 |

## 12. Gợi ý hướng refactor giao diện

1. Giữ `base.html` làm shell duy nhất.
2. Tạo component chung:
   - `components/page_header.html`
   - `components/action_toolbar.html`
   - `components/status_badge.html`
   - `components/data_table.html`
   - `components/modal.html`
   - `components/file_preview.html`
3. Chuyển CSS inline sang class, ưu tiên 5 template có nhiều inline style nhất.
4. Chuẩn hóa màu/trạng thái trước khi sửa từng màn hình.
5. Làm mobile navigation trước, vì hiện mobile mất sidebar.
6. Sau mỗi đợt sửa, kiểm tra các viewport: 1366px, 1024px, 768px, 390px.

## 13. Kết luận

Lỗi design lớn nhất không phải là một màn hình xấu đơn lẻ, mà là thiếu hệ thống giao diện chung. Project đã có nền layout và dữ liệu tốt, nhưng mỗi module đang tự giải quyết card, button, modal, preview, table và responsive theo cách riêng. Nếu cần demo với giảng viên, nên ưu tiên sửa mobile navigation, thống nhất modal/preview file, và giảm inline CSS ở các màn hình chi tiết trước.
