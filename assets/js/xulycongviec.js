/**
 * xulycongviec.js - Xử lý Công việc
 */
document.addEventListener('DOMContentLoaded', function () {
  const user = requireAuth();
  if (!user) return;

  let currentPage = 1;
  const perPage = 10;
  let filteredData = [...MOCK_CONG_VIEC];
  let pendingCvId = null;
  let pendingAction = null;

  function normalizeStatus(status) {
    const value = String(status || '').trim().toLowerCase();
    if (value === 'cho-xu-ly' || value === 'chờ xử lý') return 'cho-xu-ly';
    if (value === 'dang-xu-ly' || value === 'đang xử lý' || value === 'đang thực hiện') return 'dang-xu-ly';
    if (value === 'cho-duyet' || value === 'chờ duyệt') return 'cho-duyet';
    if (value === 'da-hoan-thanh' || value === 'đã hoàn thành') return 'da-hoan-thanh';
    if (value === 'hoan-tra' || value === 'hoàn trả' || value === 'yeu-cau-bo-sung' || value === 'yêu cầu bổ sung') return 'hoan-tra';
    return value;
  }

  function setTaskStatus(cv, statusCode) {
    const labels = {
      'cho-xu-ly': 'Chờ xử lý',
      'dang-xu-ly': 'Đang xử lý',
      'cho-duyet': 'Chờ duyệt',
      'da-hoan-thanh': 'Đã hoàn thành',
      'hoan-tra': 'Hoàn trả'
    };
    cv.trangThai = labels[statusCode] || statusCode;
  }

  function getTodayDisplay() {
    const now = new Date();
    const day = String(now.getDate()).padStart(2, '0');
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const year = now.getFullYear();
    return `${day}/${month}/${year}`;
  }

  function formatTaskDate(value) {
    if (!value) return '—';
    if (/^\d{2}\/\d{2}\/\d{4}$/.test(value)) return value;
    return formatDate(value);
  }

  function renderTable() {
    const tbody = document.getElementById('xuLyCVBody');
    const tableInfo = document.getElementById('tableInfo');
    const paginationInfo = document.getElementById('paginationInfo');

    const total = filteredData.length;
    const start = (currentPage - 1) * perPage;
    const end = Math.min(start + perPage, total);
    const pageData = filteredData.slice(start, end);

    if (tableInfo) tableInfo.textContent = `Tổng cộng: ${total} công việc`;
    if (paginationInfo) paginationInfo.textContent = `Hiển thị ${total > 0 ? start + 1 : 0}–${end} trong ${total} công việc`;

    if (!pageData.length) {
      tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><svg width="48" height="48" viewBox="0 0 24 24"><path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"/></svg><h3>Không có công việc nào</h3></div></td></tr>`;
      return;
    }

    tbody.innerHTML = pageData.map((cv, idx) => {
      const globalIdx = start + idx + 1;
      const isChuyenVien = user.role === 'chuyenvien';
      const isLanhDao = user.role === 'lanhdao';
      const statusCode = normalizeStatus(cv.trangThai);

      let actionBtns = '';

      if (isChuyenVien) {
        if (statusCode === 'cho-xu-ly') {
          actionBtns += `<button class="btn btn-primary btn-sm" onclick="startCV(${cv.id})">Bắt đầu thực hiện</button>`;
        }
        if (statusCode === 'dang-xu-ly') {
          actionBtns += `
            <button class="btn btn-success btn-sm" onclick="openXuLyModal(${cv.id},'hoan-tat')">Hoàn tất</button>
            <button class="btn btn-warning btn-sm" onclick="openXuLyModal(${cv.id},'cap-nhat')">Cập nhật</button>
            <button class="btn btn-danger btn-sm" onclick="openXuLyModal(${cv.id},'hoan-tra')">Hoàn trả</button>`;
        }
        if (statusCode === 'cho-duyet') {
          actionBtns += `<span style="font-size:12px;color:var(--text-secondary);">Đang chờ lãnh đạo duyệt</span>`;
        }
      }

      if (isLanhDao) {
        actionBtns += `<button class="btn btn-outline btn-sm" onclick="xemKetQua(${cv.id})">Xem kết quả</button>`;
        if (statusCode === 'cho-duyet') {
          actionBtns += `<button class="btn btn-danger btn-sm" onclick="duyet(${cv.id})">Duyệt hoàn thành</button>`;
        }
      }

      if (user.role === 'vanthu') {
        actionBtns = `<span style="font-size:12px;color:var(--text-muted);">Chỉ xem</span>`;
      }

      return `
        <tr>
          <td class="text-center">${globalIdx}</td>
          <td style="font-weight:600;">${cv.tenCongViec}</td>
          <td>${cv.tenLanhDao}</td>
          <td>${formatTaskDate(cv.ngayBatDau)}</td>
          <td>${formatTaskDate(cv.hanXuLy)}</td>
          <td>${renderBadge(statusCode)}</td>
          <td class="text-center" style="white-space:nowrap;">${actionBtns || '—'}</td>
        </tr>`;
    }).join('');

    createPagination('paginationBtns', total, perPage, currentPage, (p) => { currentPage = p; renderTable(); });
  }

  function applyFilters() {
    const keyword = (document.getElementById('searchKeyword')?.value || '').toLowerCase();
    const status = document.getElementById('filterStatus')?.value || '';

    filteredData = MOCK_CONG_VIEC.filter(cv => {
      if (keyword && !cv.tenCongViec.toLowerCase().includes(keyword) && !cv.tenLanhDao.toLowerCase().includes(keyword)) return false;
      if (status && normalizeStatus(cv.trangThai) !== status) return false;
      return true;
    });
    currentPage = 1;
    renderTable();
  }

  document.getElementById('btnSearch')?.addEventListener('click', applyFilters);
  document.getElementById('searchKeyword')?.addEventListener('keydown', e => { if (e.key === 'Enter') applyFilters(); });

  window.startCV = function (id) {
    const cv = MOCK_CONG_VIEC.find(c => c.id === id);
    if (cv) { setTaskStatus(cv, 'dang-xu-ly'); applyFilters(); }
    showToast('Đã bắt đầu thực hiện công việc!', 'success');
  };

  window.openXuLyModal = function (id, action) {
    pendingCvId = id;
    pendingAction = action;
    const titles = { 'hoan-tat': 'Hoàn tất công việc', 'cap-nhat': 'Cập nhật tiến độ', 'hoan-tra': 'Hoàn trả công việc' };
    document.getElementById('modalXLTitle').textContent = titles[action] || 'Cập nhật';
    document.getElementById('xlKetQua').value = '';
    document.getElementById('xlLyDo').value = '';

    // Show/hide lý do hoàn trả
    const lyDoWrap = document.getElementById('lyDoHoanTraWrap');
    if (lyDoWrap) lyDoWrap.style.display = action === 'hoan-tra' ? 'block' : 'none';

    openModal('modalXuLyCV');
  };

  document.getElementById('btnSaveXuLy')?.addEventListener('click', () => {
    const ketQua = document.getElementById('xlKetQua')?.value.trim();
    if (!ketQua) { showToast('Vui lòng nhập nội dung kết quả xử lý.', 'error'); return; }

    if (pendingAction === 'hoan-tra') {
      const lyDo = document.getElementById('xlLyDo')?.value.trim();
      if (!lyDo) { showToast('Vui lòng nhập lý do hoàn trả.', 'error'); return; }
    }

    const cv = MOCK_CONG_VIEC.find(c => c.id === pendingCvId);
    if (cv) {
      cv.ketQuaXuLy = ketQua;
      if (pendingAction === 'hoan-tat') {
        cv.ngayDuyet = getTodayDisplay();
        cv.lyDoHoanTra = '';
        setTaskStatus(cv, 'cho-duyet');
        showToast('Đã gửi kết quả, chờ lãnh đạo duyệt!', 'success');
      } else if (pendingAction === 'cap-nhat') {
        showToast('Đã cập nhật tiến độ công việc!', 'success');
      } else if (pendingAction === 'hoan-tra') {
        cv.lyDoHoanTra = document.getElementById('xlLyDo')?.value.trim() || '';
        cv.ngayHoanTra = getTodayDisplay();
        setTaskStatus(cv, 'hoan-tra');
        showToast('Đã hoàn trả công việc.', 'warning');
      }
      applyFilters();
    }
    closeModal('modalXuLyCV');
  });

  window.xemKetQua = function (id) {
    const cv = MOCK_CONG_VIEC.find(c => c.id === id);
    if (cv) alert(`Kết quả xử lý: ${cv.tenCongViec}\nTrạng thái: ${STATUS_MAP[normalizeStatus(cv.trangThai)]?.label || cv.trangThai}`);
  };

  window.duyet = function (id) {
    if (user.role !== 'lanhdao') {
      showToast('Chỉ lãnh đạo mới có quyền duyệt.', 'error');
      return;
    }
    showConfirm('Duyệt hoàn thành', 'Xác nhận công việc này đã hoàn thành?', () => {
      const cv = MOCK_CONG_VIEC.find(c => c.id === id);
      if (cv) {
        cv.ngayPheDuyet = getTodayDisplay();
        cv.ngayDuyet = cv.ngayDuyet || cv.ngayPheDuyet;
        setTaskStatus(cv, 'da-hoan-thanh');
        applyFilters();
      }
      showToast('Đã duyệt hoàn thành công việc!', 'success');
    });
  };

  renderTable();
});
