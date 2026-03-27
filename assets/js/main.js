/**
 * main.js - Shared Layout, Navigation, Utilities
 * Hệ Thống Quản Lý Văn Bản và Điều Hành
 */

/* ============================================================
   MOCK DATA - Shared across all modules
   ============================================================ */
const MOCK_VAN_BAN_DEN = [
  { id: 1, soKyHieu: '123/UBND', donViBanHanh: 'UBND Thành phố', trichYeu: 'Về việc triển khai kế hoạch năm 2024', loaiVanBan: 'Quyết định', hinhThuc: 'Công văn', ngayVanBan: '2026-02-03', ngayDen: '2026-02-04', hanXuLy: '2026-02-09', doMat: 'Bình thường', doKhan: 'Bình thường', nguoiXuLy: 'Nguyễn Văn A', trangThai: 'cho-xu-ly', fileUrl: 'CV_1735_CT_CS.pdf' },
  { id: 2, soKyHieu: '123/KT', donViBanHanh: 'UBND Thành phố', trichYeu: 'V/v sửa đổi hệ thống kiểm toán 2025', loaiVanBan: 'Công văn', hinhThuc: 'Công văn', ngayVanBan: '2026-02-03', ngayDen: '2026-02-04', hanXuLy: '2026-02-10', doMat: 'Mật', doKhan: 'Khẩn', nguoiXuLy: 'Trần Thị B', trangThai: 'da-xu-ly', fileUrl: 'CV_1735_CT_CS.pdf' },
  { id: 3, soKyHieu: '123/SYT', donViBanHanh: 'Sở Y tế', trichYeu: 'Báo cáo tình hình dịch bệnh tháng 2/2026', loaiVanBan: 'Báo cáo', hinhThuc: 'Công văn', ngayVanBan: '2026-02-05', ngayDen: '2026-02-06', hanXuLy: '2026-02-12', doMat: 'Mật', doKhan: 'Khẩn', nguoiXuLy: 'Lê Văn C', trangThai: 'xem-de-biet', fileUrl: 'CV_1735_CT_CS.pdf' },
  { id: 4, soKyHieu: '125/UBND', donViBanHanh: 'UBND Tỉnh', trichYeu: 'Quyết định thay đổi thuế suất VAT', loaiVanBan: 'Quyết định', hinhThuc: 'Quyết định', ngayVanBan: '2026-02-08', ngayDen: '2026-02-09', hanXuLy: '2026-02-15', doMat: 'Mật', doKhan: 'Khẩn', nguoiXuLy: 'Phạm Thị D', trangThai: 'hoan-tra', fileUrl: 'CV_1735_CT_CS.pdf' },
  { id: 5, soKyHieu: '200/BTC', donViBanHanh: 'Bộ Tài chính', trichYeu: 'Hướng dẫn thực hiện Nghị định 117/2025/NĐ-CP', loaiVanBan: 'Thông tư', hinhThuc: 'Thông tư', ngayVanBan: '2026-02-10', ngayDen: '2026-02-11', hanXuLy: '2026-02-20', doMat: 'Bình thường', doKhan: 'Bình thường', nguoiXuLy: 'Hoàng Văn E', trangThai: 'cho-xu-ly', fileUrl: 'CV_1735_CT_CS.pdf' },
  { id: 6, soKyHieu: '305/BGDDT', donViBanHanh: 'Bộ Giáo dục', trichYeu: 'Kế hoạch triển khai chương trình giáo dục mới', loaiVanBan: 'Kế hoạch', hinhThuc: 'Kế hoạch', ngayVanBan: '2026-02-12', ngayDen: '2026-02-13', hanXuLy: '2026-02-25', doMat: 'Bình thường', doKhan: 'Bình thường', nguoiXuLy: 'Vũ Thị F', trangThai: 'da-chuyen-tiep', fileUrl: 'CV_1735_CT_CS.pdf' },
  { id: 7, soKyHieu: '089/BLDTBXH', donViBanHanh: 'Bộ Lao động', trichYeu: 'Thông báo về chính sách bảo hiểm xã hội năm 2026', loaiVanBan: 'Thông báo', hinhThuc: 'Thông báo', ngayVanBan: '2026-02-15', ngayDen: '2026-02-16', hanXuLy: '2026-02-28', doMat: 'Bình thường', doKhan: 'Thường', nguoiXuLy: 'Nguyễn Thị G', trangThai: 'cho-xu-ly', fileUrl: 'CV_1735_CT_CS.pdf' },
];

const MOCK_VAN_BAN_DI = [
  { id: 1, soKyHieu: '01/2026/CV-ĐV', trichYeu: 'V/v triển khai kế hoạch quản lý văn bản năm 2026', hinhThuc: 'Công văn', loaiVanBan: 'Hành chính', doKhan: 'Thường', donViSoaThan: 'Phòng Hành chính', hanXuLy: '2026-02-15', nguoiDuyet: 'Nguyễn Văn Lãnh Đạo', trangThai: 'da-ban-hanh', fileUrl: 'draft_01.docx' },
  { id: 2, soKyHieu: '02/2026/TB-ĐV', trichYeu: 'Thông báo về lịch họp định kỳ tháng 3/2026', hinhThuc: 'Thông báo', loaiVanBan: 'Hành chính', doKhan: 'Thường', donViSoaThan: 'Phòng Hành chính', hanXuLy: '2026-02-20', nguoiDuyet: 'Nguyễn Văn Lãnh Đạo', trangThai: 'cho-xu-ly', fileUrl: 'draft_02.docx' },
  { id: 3, soKyHieu: '03/2026/BC-ĐV', trichYeu: 'Báo cáo tình hình hoạt động quý I/2026', hinhThuc: 'Báo cáo', loaiVanBan: 'Báo cáo', doKhan: 'Khẩn', donViSoaThan: 'Phòng Nghiệp vụ', hanXuLy: '2026-02-25', nguoiDuyet: 'Nguyễn Văn Lãnh Đạo', trangThai: 'da-xu-ly', fileUrl: 'draft_03.docx' },
  { id: 4, soKyHieu: '', trichYeu: 'V/v triển khai dự án phần mềm mới', hinhThuc: 'Công văn', loaiVanBan: 'Hành chính', doKhan: 'Thường', donViSoaThan: 'Phòng CNTT', hanXuLy: '2026-03-05', nguoiDuyet: 'Nguyễn Văn Lãnh Đạo', trangThai: 'hoan-tra', fileUrl: 'draft_04.docx' },
  { id: 5, soKyHieu: '05/2026/QD-ĐV', trichYeu: 'Quyết định bổ nhiệm cán bộ phòng Kế toán', hinhThuc: 'Quyết định', loaiVanBan: 'Nhân sự', doKhan: 'Khẩn', donViSoaThan: 'Phòng Nhân sự', hanXuLy: '2026-03-10', nguoiDuyet: 'Nguyễn Văn Lãnh Đạo', trangThai: 'cho-ban-hanh', fileUrl: 'draft_05.docx' },
  { id: 6, soKyHieu: '', trichYeu: 'Tờ trình xin phê duyệt ngân sách quý II', hinhThuc: 'Tờ trình', loaiVanBan: 'Tài chính', doKhan: 'Thường', donViSoaThan: 'Phòng Kế toán', hanXuLy: '2026-03-15', nguoiDuyet: 'Nguyễn Văn Lãnh Đạo', trangThai: 'cho-xu-ly', fileUrl: 'draft_06.docx' },
];

const MOCK_CONG_VIEC = [
  { id: 1, tenCongViec: 'Thu thập yêu cầu khách hàng 1', noiDungCV: 'Yêu cầu các phòng ban tổng hợp số liệu và gửi về phòng Kế toán trước ngày 25/03.', ngayBatDau: '01/01/2026', hanXuLy: '05/02/2026', nguoiThucHien: 'Trần Thị Thúy Na', nguoiPhoiHop: 'Phòng KT-TC', trangThai: 'Chờ xử lý', tenLanhDao: 'Ngô Văn Hà', nguonCV: 'Văn bản đến', ghiChu: 'Khẩn', maGiaoViec: 'GV-001', fileDinhKem: 'CV_1735_CT_CS.pdf' },
  { id: 2, tenCongViec: 'Thu thập yêu cầu khách hàng 2', noiDungCV: 'Cập nhật lại quy trình nghiệp vụ', ngayBatDau: '01/01/2026', hanXuLy: '05/02/2026', nguoiThucHien: 'Phạm Thị Phương', nguoiPhoiHop: '', trangThai: 'Đã hoàn thành', tenLanhDao: 'Ngô Văn Hà', nguonCV: 'Văn bản đi', ghiChu: '', maGiaoViec: 'GV-002', fileDinhKem: '' },
  { id: 3, tenCongViec: 'Thu thập yêu cầu khách hàng 3', noiDungCV: 'Xây dựng kế hoạch truyền thông', ngayBatDau: '01/01/2026', hanXuLy: '05/02/2026', nguoiThucHien: 'Trần Tấn Tú', nguoiPhoiHop: '', trangThai: 'Hoàn trả', tenLanhDao: 'Ngô Văn Hà', nguonCV: 'Văn bản đi', ghiChu: '', maGiaoViec: 'GV-003', fileDinhKem: '', ngayHoanTra: '09/02/2025' },
  { id: 4, tenCongViec: 'Thu thập yêu cầu khách hàng 3', noiDungCV: 'Triển khai công cụ mới', ngayBatDau: '01/01/2026', hanXuLy: '05/02/2026', nguoiThucHien: 'Trần Tấn Tú', nguoiPhoiHop: '', trangThai: 'Chờ duyệt', tenLanhDao: 'Ngô Văn Hà', nguonCV: 'Văn bản đi', ghiChu: '', maGiaoViec: 'GV-004', fileDinhKem: '', ngayDuyet: '10/02/2026' },
  // Data matched to specific detail mockups
  { id: 101, tenCongViec: 'Báo cáo tài chính Quý I/2026', noiDungCV: 'Yêu cầu các phòng ban tổng hợp số liệu và gửi về phòng Kế toán trước ngày 25/03.', ngayBatDau: '03/01/2026', hanXuLy: '03/10/2026', nguoiThucHien: 'Nguyễn Văn A', nguoiPhoiHop: 'Phòng KT-TC', trangThai: 'Chờ xử lý', tenLanhDao: 'Ngô Văn Hà', nguonCV: 'Văn bản đến', ghiChu: 'Khẩn', maGiaoViec: 'GV-001', fileDinhKem: 'CV_1735_CT_CS.pdf'},
  { id: 102, tenCongViec: 'Kiểm toán báo cáo tài chính công ty TNHH ABC', noiDungCV: 'Thực hiện kiểm toán báo cáo tài chính năm 2025 của công ty TNHH ABC theo chuẩn mực kiểm toán Việt Nam', ngayBatDau: '01/02/2026', hanXuLy: '15/02/2026', nguoiThucHien: 'Ngô Đăng Hà', nguoiPhoiHop: '', trangThai: 'Đang xử lý', tenLanhDao: 'Nguyễn Văn C', nguonCV: 'VB001/2026 - Hợp đồng kiểm toán', ghiChu: '', maGiaoViec: 'GV-102', fileDinhKem: 'VB001_2026_Hop_dong.pdf'},
  { id: 103, tenCongViec: 'Tư vấn thuế GTGT cho doanh nghiệp XYZ', noiDungCV: 'Tư vấn quy trình kê khai và hoàn thuế GTGT cho doanh nghiệp XYZ', ngayBatDau: '29/01/2026', hanXuLy: '10/02/2026', nguoiThucHien: 'Ngô Đăng Hà', nguoiPhoiHop: '', trangThai: 'Đang xử lý', tenLanhDao: 'Nguyễn Văn C', nguonCV: 'Văn bản đi', ghiChu: '', maGiaoViec: 'GV-103', fileDinhKem: 'Phan_tich_thue_XYZ.xlsx'},
  { id: 104, tenCongViec: 'Báo cáo tài chính Quý I/2026', noiDungCV: 'Yêu cầu các phòng ban tổng hợp số liệu và gửi về phòng Kế toán trước ngày 25/03.', ngayBatDau: '03/01/2026', hanXuLy: '03/10/2026', nguoiThucHien: 'Nguyễn Văn A', nguoiPhoiHop: 'Phòng KT-TC', trangThai: 'Chờ duyệt', tenLanhDao: 'Ngô Văn Hà', nguonCV: 'Văn bản đến', ghiChu: 'Khẩn', maGiaoViec: 'GV-001', fileDinhKem: 'CV_1735_CT_CS.pdf', ngayDuyet: '10/02/2026'},
];

const MOCK_HO_SO = [
  { id: 1, maHoSo: '1.VHKHTT', tenHoSo: 'Tập văn bản gửi đến cơ quan', moTa: 'Tập hợp các văn bản được gửi đến các cơ quan bên ngoài', namHinhThanh: '2025', thoiGianBaoQuan: 'Vĩnh viễn', donVi: 'Phòng hành chính', trangThai: 'Hiện hành', quyenXuLy: 'Phạm Thị Phương, Trần Thị Thúy Na', ngayTao: '03/04/2025' },
  { id: 2, maHoSo: '2.KHCT', tenHoSo: 'Hồ sơ kế hoạch công tác', moTa: 'Hồ sơ liên quan đến công việc chuyên môn', namHinhThanh: '2024', thoiGianBaoQuan: 'Theo quy định - 5 năm', donVi: 'Phòng kế hoạch', trangThai: 'Hiện hành', quyenXuLy: 'Trần Thị Thúy Na', ngayTao: '10/06/2024' },
  { id: 3, maHoSo: '3.QDNS', tenHoSo: 'Các quyết định nhân sự', moTa: 'Văn bản quyết định về mặt nhân sự', namHinhThanh: '2024', thoiGianBaoQuan: 'Theo quy định - 2 năm', donVi: 'Phòng nhân sự', trangThai: 'Hiện hành', quyenXuLy: 'Nguyễn Văn A', ngayTao: '15/08/2024' },
  { id: 4, maHoSo: '4.QDLLV', tenHoSo: 'Hồ sơ các quyết định thông báo lịch làm', moTa: 'Tập hợp các văn bản liên quan tới lịch làm việc', namHinhThanh: '2023', thoiGianBaoQuan: 'Theo quy định - 2 năm', donVi: 'Phòng nhân sự', trangThai: 'Lưu trữ', quyenXuLy: 'Phạm Thị Phương, Trần Thị Thúy Na', ngayTao: '02/03/2023', soNamLuuTru: '2' }
];

/* ============================================================
   SHARED UI INITIALIZATION
   ============================================================ */

/**
 * Initialize the authenticated layout (header user info, sidebar)
 */
function initLayout() {
  const user = getCurrentUser();
  if (!user) return;

  initHeaderNav();

  // Set header user info
  const elName = document.getElementById('headerUserName');
  const elRole = document.getElementById('headerUserRole');
  const elAvatar = document.getElementById('headerAvatar');

  if (elName) elName.textContent = user.name;
  if (elRole) elRole.textContent = user.roleLabel;
  if (elAvatar) elAvatar.textContent = user.avatar;

  // Role-based visibility
  applyRoleVisibility(user.role);

  // Set active sidebar link
  setActiveSidebarLink();

  // Init user dropdown
  initUserDropdown();

  // Init sidebar submenus
  initSidebarSubmenus();
}

/**
 * Apply role-based show/hide on elements
 */
function applyRoleVisibility(role) {
  // Hide elements not allowed for the current role
  document.querySelectorAll('[data-roles]').forEach(el => {
    const allowed = el.dataset.roles.split(',').map(r => r.trim());
    if (!allowed.includes(role)) {
      el.style.display = 'none';
    }
  });

  // Show elements only for specific roles
  document.querySelectorAll('[data-role-show]').forEach(el => {
    const allowed = el.dataset.roleShow.split(',').map(r => r.trim());
    if (allowed.includes(role)) {
      el.style.display = '';
    }
  });
}

/**
 * Highlight the active sidebar link based on current page
 */
function setActiveSidebarLink() {
  const currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';
  document.querySelectorAll('.sidebar-nav-link[href], .sidebar-submenu a[href]').forEach(link => {
    const href = link.getAttribute('href');
    if (href && href === currentPage) {
      link.classList.add('active');
      // Open parent submenu if exists
      const submenu = link.closest('.sidebar-submenu');
      if (submenu) {
        submenu.classList.add('open');
        const parentLink = submenu.previousElementSibling;
        if (parentLink) parentLink.classList.add('active', 'open');
      }
    }
  });
}

/**
 * Initialize sidebar accordion submenus
 */
function initSidebarSubmenus() {
  document.querySelectorAll('.sidebar-nav-link[data-toggle="submenu"]').forEach(link => {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      const targetId = this.dataset.target;
      const submenu = document.getElementById(targetId);
      if (!submenu) return;

      const isOpen = submenu.classList.contains('open');
      submenu.classList.toggle('open', !isOpen);
      this.classList.toggle('open', !isOpen);
    });
  });
}

function initHeaderNav() {
  if (document.querySelector('.header-nav')) return;

  const header = document.querySelector('.app-header');
  if (!header) return;

  const currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';
  const navItems = [
    {
      href: 'dashboard.html',
      label: 'Trang chủ',
      activePages: ['dashboard.html'],
      icon: '<svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>'
    },
    {
      href: '#',
      label: 'Thông tin cá nhân',
      disabled: true,
      icon: '<svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>'
    },
    {
      href: '#',
      label: 'Bộ công cụ quản lý',
      disabled: true,
      icon: '<svg viewBox="0 0 24 24"><path d="M7 4h10a2 2 0 0 1 2 2v2h1a2 2 0 0 1 2 2v3h-2v-3h-4v3H8v-3H4v8a2 2 0 0 0 2 2h5v-4h2v4h5a2 2 0 0 0 2-2v-3h2v3a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4v-8a4 4 0 0 1 4-4h1V6a2 2 0 0 1 2-2zm0 4h10V6H7v2z"/></svg>'
    },
    {
      href: '#',
      label: 'Hướng dẫn sử dụng',
      disabled: true,
      icon: '<svg viewBox="0 0 24 24"><path d="M18 2H8a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2zm0 14H8V4h10v12zM6 6H4v14a2 2 0 0 0 2 2h12v-2H6V6zm3 1h8v2H9V7zm0 4h8v2H9v-2z"/></svg>'
    }
  ];

  const nav = document.createElement('nav');
  nav.className = 'header-nav';
  nav.setAttribute('aria-label', 'Điều hướng chính');
  nav.innerHTML = `
    <div class="header-nav-list">
      ${navItems.map(item => `
        <a href="${item.href}" class="header-nav-link${(item.activePages || []).includes(currentPage) ? ' active' : ''}"${item.disabled ? ' data-disabled="true"' : ''}>
          ${item.icon}
          <span>${item.label}</span>
        </a>
      `).join('')}
    </div>
  `;

  header.insertAdjacentElement('afterend', nav);

  nav.querySelectorAll('[data-disabled="true"]').forEach(link => {
    link.addEventListener('click', function (e) {
      e.preventDefault();
    });
  });
}

/**
 * Initialize user dropdown in header
 */
function initUserDropdown() {
  const userBtn = document.getElementById('headerUserBtn');
  const dropdown = document.getElementById('userDropdown');

  if (!userBtn || !dropdown) return;

  userBtn.addEventListener('click', function (e) {
    e.stopPropagation();
    dropdown.classList.toggle('open');
  });

  document.addEventListener('click', function () {
    dropdown.classList.remove('open');
  });

  // Logout
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', function (e) {
      e.preventDefault();
      showConfirm('Xác nhận đăng xuất', 'Bạn có chắc chắn muốn đăng xuất khỏi hệ thống?', function () {
        logout();
      });
    });
  }
}

/* ============================================================
   TOAST NOTIFICATIONS
   ============================================================ */
function showToast(message, type = 'success', duration = 3500) {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = {
    success: '<svg width="20" height="20" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg>',
    error:   '<svg width="20" height="20" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/></svg>',
    warning: '<svg width="20" height="20" viewBox="0 0 24 24"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>',
    info:    '<svg width="20" height="20" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>'
  };

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span class="toast-icon">${icons[type] || icons.info}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/* ============================================================
   CONFIRM DIALOG
   ============================================================ */
function showConfirm(title, message, onConfirm) {
  let overlay = document.getElementById('confirmOverlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'confirmOverlay';
    overlay.className = 'confirm-overlay';
    overlay.innerHTML = `
      <div class="confirm-dialog">
        <div class="confirm-icon">
          <svg width="28" height="28" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
        </div>
        <div class="confirm-title" id="confirmTitle"></div>
        <div class="confirm-message" id="confirmMessage"></div>
        <div class="confirm-actions">
          <button class="btn btn-secondary" id="confirmCancel">Hủy bỏ</button>
          <button class="btn btn-danger" id="confirmOk">Xác nhận</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);
  }

  document.getElementById('confirmTitle').textContent = title;
  document.getElementById('confirmMessage').textContent = message;
  overlay.classList.add('open');

  const ok = document.getElementById('confirmOk');
  const cancel = document.getElementById('confirmCancel');

  const close = () => overlay.classList.remove('open');

  const newOk = ok.cloneNode(true);
  ok.replaceWith(newOk);
  newOk.addEventListener('click', () => { close(); onConfirm && onConfirm(); });
  cancel.addEventListener('click', close);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
}

/* ============================================================
   MODAL HELPERS
   ============================================================ */
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('open');
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('open');
}

function initModals() {
  // Close when clicking overlay background
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', function (e) {
      if (e.target === this) this.classList.remove('open');
    });
  });

  // Close buttons
  document.querySelectorAll('[data-dismiss="modal"]').forEach(btn => {
    btn.addEventListener('click', function () {
      this.closest('.modal-overlay').classList.remove('open');
    });
  });
}

/* ============================================================
   STATUS BADGE HELPER
   ============================================================ */
const STATUS_MAP = {
  'cho-xu-ly':      { label: 'Chờ xử lý',       cls: 'badge-cho-xu-ly' },
  'hoan-tra':       { label: 'Hoàn trả',          cls: 'badge-hoan-tra' },
  'da-xu-ly':       { label: 'Đã xử lý',          cls: 'badge-da-xu-ly' },
  'da-chuyen-tiep': { label: 'Đã chuyển tiếp',    cls: 'badge-da-chuyen-tiep' },
  'xem-de-biet':    { label: 'Xem để biết',        cls: 'badge-xem-de-biet' },
  'cho-ban-hanh':   { label: 'Chờ ban hành',       cls: 'badge-cho-ban-hanh' },
  'da-ban-hanh':    { label: 'Đã ban hành',         cls: 'badge-da-ban-hanh' },
  'dang-xu-ly':     { label: 'Đang thực hiện',     cls: 'badge-dang-xu-ly' },
  'cho-duyet':      { label: 'Chờ duyệt',           cls: 'badge-cho-duyet' },
  'da-hoan-thanh':  { label: 'Đã hoàn thành',       cls: 'badge-hoan-thanh' },
  'qua-han':        { label: 'Quá hạn',              cls: 'badge-qua-han' },
  'yeu-cau-bo-sung':{ label: 'Y/c bổ sung',          cls: 'badge-hoan-tra' },
};

function renderBadge(status) {
  const s = STATUS_MAP[status] || { label: status, cls: '' };
  return `<span class="badge ${s.cls}">${s.label}</span>`;
}

/**
 * Compute deadline badge
 */
function deadlineBadge(hanXuLyStr) {
  if (!hanXuLyStr) return '';
  const deadline = new Date(hanXuLyStr);
  const now = new Date();
  const diffDays = Math.ceil((deadline - now) / (1000 * 60 * 60 * 24));
  if (diffDays < 0) return '<span class="deadline-badge" style="background:#FEE2E2;color:#991B1B;">Quá hạn</span>';
  if (diffDays <= 3) return '<span class="deadline-badge" style="background:#FEF3C7;color:#B45309;">Sắp đến hạn</span>';
  return '';
}

/* ============================================================
   PAGINATION HELPER
   ============================================================ */
function createPagination(containerId, total, perPage, currentPage, onPageChange) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const totalPages = Math.ceil(total / perPage);
  let html = '';

  for (let i = 1; i <= totalPages; i++) {
    html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
  }

  container.innerHTML = `
    <button class="page-btn" data-page="${currentPage - 1}" ${currentPage === 1 ? 'disabled' : ''}>
      <svg width="16" height="16" viewBox="0 0 24 24"><path d="M15.41 16.59L10.83 12l4.58-4.59L14 6l-6 6 6 6z"/></svg>
    </button>
    ${html}
    <button class="page-btn" data-page="${currentPage + 1}" ${currentPage === totalPages ? 'disabled' : ''}>
      <svg width="16" height="16" viewBox="0 0 24 24"><path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6z"/></svg>
    </button>`;

  container.querySelectorAll('.page-btn:not([disabled])').forEach(btn => {
    btn.addEventListener('click', () => onPageChange(parseInt(btn.dataset.page)));
  });
}

/* ============================================================
   DATE FORMATTING
   ============================================================ */
function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function formatDateInput(dateStr) {
  if (!dateStr) return '';
  return dateStr; // Already YYYY-MM-DD for input[type=date]
}

/* ============================================================
   FORM VALIDATION
   ============================================================ */
function validateRequired(fieldId, errorId) {
  const field = document.getElementById(fieldId);
  const error = document.getElementById(errorId);
  if (!field) return true;
  const val = field.value ? field.value.trim() : '';
  if (!val) {
    field.classList.add('error');
    if (error) error.classList.add('show');
    return false;
  }
  field.classList.remove('error');
  if (error) error.classList.remove('show');
  return true;
}

/* ============================================================
   INIT ON DOM READY
   ============================================================ */
document.addEventListener('DOMContentLoaded', function () {
  // Initialize layout if we're on an authenticated page
  if (document.getElementById('headerUserName') || document.querySelector('.app-header')) {
    initLayout();
    initModals();
  }
});
