# Hệ thống Quản lý Văn bản và Điều hành

Dự án xây dựng bằng **Django** nhằm hỗ trợ quản lý văn bản và điều hành công việc trong cơ quan/doanh nghiệp.  
Hệ thống tập trung vào 4 module chính:

- **Quản lý văn bản đi**
- **Quản lý văn bản đến**
- **Hồ sơ văn bản**
- **Quản lý công việc**

---

## Mục tiêu dự án

Hệ thống được xây dựng để:

- Quản lý tập trung văn bản đi và văn bản đến
- Theo dõi hồ sơ văn bản
- Hỗ trợ giao việc, phân công và xử lý công việc
- Tăng khả năng tra cứu, theo dõi và quản lý tiến độ xử lý văn bản

---

## Chức năng chính

### 1. Quản lý văn bản đi
- Thêm mới văn bản đi
- Cập nhật, chỉnh sửa văn bản đi
- Xem danh sách văn bản đi
- Xem chi tiết văn bản đi
- Tìm kiếm, lọc văn bản đi
- Duyệt và ban hành văn bản

### 2. Quản lý văn bản đến
- Thêm mới văn bản đến
- Cập nhật, chỉnh sửa văn bản đến
- Xem danh sách văn bản đến
- Xem chi tiết văn bản đến
- Chuyển tiếp văn bản
- Hoàn trả văn bản

### 3. Hồ sơ văn bản
- Tạo hồ sơ văn bản
- Quản lý danh sách hồ sơ
- Xem chi tiết hồ sơ
- Thêm/Xóa văn bản vào hồ sơ

### 4. Quản lý công việc
- Tạo công việc
- Phân công công việc
- Phê duyệt công việc
- Hoàn trả công việc

---

## Công nghệ sử dụng

- **Backend:** Django
- **Frontend:** HTML, CSS, JavaScript, Bootstrap
- **Database:** SQLite / MySQL
- **Version Control:** Git, GitHub

---

## Cấu trúc dự án

```bash
he_thong_van_ban/
│
├── manage.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/
│   ├── quanlyvanbandi/
│   ├── quanlyvanbanden/
│   ├── hosovanban/
│   └── quanlycongviec/
│
├── templates/
├── static/
├── media/
└── requirements.txt
