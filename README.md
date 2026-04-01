# Hệ thống Quản lý Văn bản và Điều hành

Dự án xây dựng bằng **Django** nhằm hỗ trợ quản lý văn bản và điều hành công việc trong cơ quan/doanh nghiệp.  
Hệ thống được phát triển từ giao diện frontend tĩnh và đang được chuyển đổi sang mô hình **Django Backend + Template Rendering**.

## Mục tiêu dự án

- Quản lý tập trung văn bản đi và văn bản đến
- Quản lý hồ sơ văn bản
- Hỗ trợ giao việc, phân công và theo dõi xử lý công việc
- Tăng khả năng tra cứu, theo dõi trạng thái và điều hành công việc
- Chuẩn hóa luồng xử lý văn bản trong hệ thống

## Module chính

### 1. Quản lý văn bản đi
- Thêm mới văn bản đi
- Cập nhật, chỉnh sửa văn bản đi
- Xem danh sách văn bản đi
- Xem chi tiết văn bản đi
- Duyệt và ban hành văn bản
- Theo dõi trạng thái xử lý văn bản đi

### 2. Quản lý văn bản đến
- Tiếp nhận văn bản đến
- Cập nhật, chỉnh sửa văn bản đến
- Xem danh sách văn bản đến
- Xem chi tiết văn bản đến
- Chuyển tiếp văn bản
- Hoàn trả văn bản
- Theo dõi tiến độ xử lý

### 3. Hồ sơ văn bản
- Tạo hồ sơ văn bản
- Quản lý danh sách hồ sơ
- Liên kết văn bản với hồ sơ
- Xem chi tiết hồ sơ
- Xử lý hồ sơ văn bản

### 4. Quản lý công việc
- Tạo công việc
- Giao việc
- Phân công công việc
- Theo dõi trạng thái xử lý
- Phê duyệt công việc
- Hoàn trả công việc
- Quản lý file liên quan đến công việc

## Công nghệ sử dụng

- **Backend:** Django 4.2.8
- **Frontend:** HTML, CSS
- **Database:** SQLite
- **Template Engine:** Django Templates
- **Quản lý file tĩnh:** Django Static Files
- **Quản lý media:** Django Media Files
- **Version Control:** Git, GitHub

## Cấu trúc dự án

```bash
he_thong_quan_ly_van_ban/
│
├── manage.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/
│   ├── core/
│   ├── accounts/
│   ├── quanlyvanbandi/
│   ├── quanlyvanbanden/
│   ├── hosovanban/
│   └── quanlycongviec/
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── index.html
│   ├── otp.html
│   ├── registration/
│   ├── quanlyvanbandi/
│   ├── quanlyvanbanden/
│   ├── hosovanban/
│   └── quanlycongviec/
│
├── static/
│   └── assets/
│       ├── css/
│       ├── js/
│       ├── img/
│       └── fonts/
│
├── media/
│   ├── van_ban_di/
│   ├── van_ban_den/
│   ├── ho_so_van_ban/
│   └── cong_viec/
│
└── requirements.txt
