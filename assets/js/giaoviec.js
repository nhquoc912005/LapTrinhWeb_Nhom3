/**
 * giaoviec.js - Quản lý Giao Việc (Refactored for 5 Screens)
 */
document.addEventListener('DOMContentLoaded', function () {
  const user = requireAuth();
  if (!user) return;

  const views = ['congViecListView', 'congViecFormView', 'congViecDetailView', 'congViecXulyView', 'congViecCapNhatView'];
  
  function switchView(viewId, breadcrumbs = []) {
    views.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.style.display = (id === viewId) ? 'block' : 'none';
      if (id === 'congViecListView' && viewId === 'congViecListView') renderTable();
    });
    updateBreadcrumbs(breadcrumbs);
    window.scrollTo(0, 0);
  }

  function updateBreadcrumbs(items) {
    const bar = document.getElementById('breadcrumbBar');
    if (!bar) return;
    let html = `<a href="dashboard.html"><svg width="14" height="14" viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>Trang chủ</a>`;
    items.forEach((item, idx) => {
      html += ` <span class="breadcrumb-sep">›</span>`;
      if (item.link) {
        html += `<a href="#" class="breadcrumb-link" data-view="${item.view}" data-id="${item.id || ''}">${item.text}</a>`;
      } else {
        html += `<span>${item.text}</span>`;
      }
    });
    bar.innerHTML = html;

    bar.querySelectorAll('.breadcrumb-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const v = link.getAttribute('data-view');
        const id = link.getAttribute('data-id');
        if (v === 'congViecListView') switchView('congViecListView', [{text: 'Quản lý công việc'}]);
        else if (v === 'congViecDetailView') viewCongViecDetail(parseInt(id));
      });
    });
  }

  let activeTab = 'all';
  let filteredData = [...MOCK_CONG_VIEC];

  const GV_STATUS = {
    'cho-xu-ly': { label: 'Chờ xử lý', bg: '#FEF3C7', color: '#D97706' },
    'dang-xu-ly': { label: 'Đang xử lý', bg: '#DBEAFE', color: '#2563EB' },
    'cho-duyet': { label: 'Chờ duyệt', bg: '#EDE9FE', color: '#7C3AED' },
    'da-hoan-thanh': { label: 'Đã hoàn thành', bg: '#D1FAE5', color: '#059669' },
    'hoan-tra': { label: 'Hoàn trả', bg: '#FCE7F3', color: '#DB2777' }
  };

  function normalizeGVStatus(status) {
    const value = String(status || '').trim().toLowerCase();
    if (value === 'cho-xu-ly' || value === 'chờ xử lý') return 'cho-xu-ly';
    if (value === 'dang-xu-ly' || value === 'đang xử lý' || value === 'đang thực hiện') return 'dang-xu-ly';
    if (value === 'cho-duyet' || value === 'chờ duyệt') return 'cho-duyet';
    if (value === 'da-hoan-thanh' || value === 'đã hoàn thành') return 'da-hoan-thanh';
    if (value === 'hoan-tra' || value === 'hoàn trả' || value === 'yeu-cau-bo-sung' || value === 'yêu cầu bổ sung') return 'hoan-tra';
    return value;
  }

  function getGVStatusLabel(status) {
    return GV_STATUS[normalizeGVStatus(status)]?.label || status || '—';
  }

  function setGVStatus(cv, statusCode) {
    cv.trangThai = GV_STATUS[statusCode]?.label || statusCode;
  }

  function formatDateForDisplay(dateStr) {
    if (!dateStr) return '';
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
      const [year, month, day] = dateStr.split('-');
      return `${day}/${month}/${year}`;
    }
    return dateStr;
  }

  function getTodayDisplay() {
    const now = new Date();
    const day = String(now.getDate()).padStart(2, '0');
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const year = now.getFullYear();
    return `${day}/${month}/${year}`;
  }

  function getCongViecById(id) {
    return MOCK_CONG_VIEC.find(cv => cv.id === id);
  }

  function goToListView() {
    switchView('congViecListView', [{ text: 'Quản lý công việc' }]);
  }

  window.goToCongViecList = goToListView;

  function renderBadgeGV(st) {
    const meta = GV_STATUS[normalizeGVStatus(st)] || { label: st, bg: '#E5E7EB', color: '#374151' };
    return `<span style="display:inline-block;padding:6px 16px;border-radius:16px;font-size:12px;font-weight:600;background:${meta.bg};color:${meta.color};">${meta.label}</span>`;
  }

  function renderTable() {
    const tbody = document.getElementById('congViecBody');
    if (!tbody) return;

    if (!filteredData.length) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding:40px;">Không tìm thấy kết quả phù hợp.</td></tr>`;
      return;
    }

    tbody.innerHTML = filteredData.map((cv, idx) => `
      <tr style="border-bottom: 1px solid var(--border-color);">
        <td class="text-center" style="padding:12px;">${idx + 1}</td>
        <td style="padding:12px;"><a href="#" class="cv-link" data-id="${cv.id}" style="color:var(--primary); font-weight:600; text-decoration:none;">${cv.tenCongViec}</a></td>
        <td style="padding:12px;">${cv.nguoiThucHien}</td>
        <td style="padding:12px;">${cv.ngayBatDau}</td>
        <td style="padding:12px;">${cv.hanXuLy}</td>
        <td style="padding:12px;">${cv.nguonCV}</td>
        <td style="padding:12px;">${renderBadgeGV(cv.trangThai)}</td>
      </tr>
    `).join('');

    const paginateInfo = document.getElementById('paginationInfo');
    if (paginateInfo) paginateInfo.textContent = `Hiển thị ${filteredData.length} công việc`;

    document.querySelectorAll('.cv-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const id = parseInt(e.target.getAttribute('data-id'));
        viewCongViecDetail(id);
      });
    });
  }

  function applyFilters() {
    const kw = (document.getElementById('searchKeyword')?.value || '').toLowerCase().trim();
    const source = document.getElementById('filterNguonCV')?.value || '';
    const activeStatus = activeTab === 'all' ? 'all' : normalizeGVStatus(activeTab);

    filteredData = MOCK_CONG_VIEC.filter(cv => {
      if (activeStatus !== 'all' && normalizeGVStatus(cv.trangThai) !== activeStatus) return false;
      if (kw && !cv.tenCongViec.toLowerCase().includes(kw)) return false;
      if (source && cv.nguonCV !== source) return false;
      return true;
    });
    renderTable();
  }

  // --- FORM VIEW (MÀN 1 & 2) ---
  window.renderForm = function(cvId = null) {
    const cv = cvId ? MOCK_CONG_VIEC.find(c => c.id === cvId) : null;
    const isEdit = !!cv;
    const title = isEdit ? 'CHỈNH SỬA CÔNG VIỆC' : 'GIAO CÔNG VIỆC MỚI';
    const breadcrumbs = isEdit ? 
      [{text: 'Quản lý công việc', link: true, view: 'congViecListView'}, {text: 'Thông tin chi tiết công việc', link: true, view: 'congViecDetailView', id: cvId}, {text: 'Chỉnh sửa công việc'}] :
      [{text: 'Quản lý công việc', link: true, view: 'congViecListView'}, {text: 'Giao việc'}];

    const html = `
      <div class="card" style="background:#fff; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.1); padding:24px;">
        <h3 style="color:var(--text-color); font-size:16px; font-weight:700; border-left:4px solid var(--primary); padding-left:12px; margin:0 0 24px 0; text-transform:uppercase;">
          ${title}
        </h3>
        
        <div style="border-top: 1px solid var(--border-color); padding-top:24px;">
          <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:20px; margin-bottom:20px;">
            <div class="form-group">
              <label class="form-label" style="font-size:13px; color:var(--text-muted);">Lãnh đạo giao việc</label>
              <input type="text" class="form-control" value="${cv?.tenLanhDao || user.name}" readonly style="background:#E5E7EB; border-color:#D1D5DB;">
            </div>
            <div class="form-group">
              <label class="form-label" style="font-size:13px;">Nguồn giao <span style="color:#EF4444;">*</span></label>
              <select id="formNguonGiao" class="form-control" style="font-size:14px; height:40px;">
                <option value="">Chọn nguồn văn bản</option>
                <option value="Văn bản đến" ${cv?.nguonCV === 'Văn bản đến' ? 'selected' : ''}>Văn bản đến</option>
                <option value="Văn bản đi" ${cv?.nguonCV === 'Văn bản đi' ? 'selected' : ''}>Văn bản đi</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label" style="font-size:13px;">Ngày bắt đầu <span style="color:#EF4444;">*</span></label>
              <input type="date" id="formNgayBatDau" class="form-control" value="${cv?.ngayBatDau ? formatDateForInput(cv.ngayBatDau) : ''}">
            </div>
            <div class="form-group">
              <label class="form-label" style="font-size:13px;">Hạn xử lý <span style="color:#EF4444;">*</span></label>
              <input type="date" id="formHanXuLy" class="form-control" value="${cv?.hanXuLy ? formatDateForInput(cv.hanXuLy) : ''}">
            </div>
          </div>

          <div class="form-group" style="margin-bottom:20px;">
            <label class="form-label" style="font-size:13px;">Tên công việc <span style="color:#EF4444;">*</span></label>
            <input type="text" id="formTenCV" class="form-control" placeholder="Nhập tên công việc..." value="${cv?.tenCongViec || ''}">
          </div>

          <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; margin-bottom:20px;">
            <div class="form-group">
              <label class="form-label" style="font-size:13px;">Chuyên viên thực hiện <span style="color:#EF4444;">*</span></label>
              <select id="formChuyenVien" class="form-control" style="font-size:14px; height:40px;">
                <option value="">-- Chọn chuyên viên --</option>
                <option value="Trần Tấn Tú" ${cv?.nguoiThucHien === 'Trần Tấn Tú' ? 'selected' : ''}>Trần Tấn Tú</option>
                <option value="Nguyễn Văn A" ${cv?.nguoiThucHien === 'Nguyễn Văn A' ? 'selected' : ''}>Nguyễn Văn A</option>
                <option value="Trần Thị Thúy Na" ${cv?.nguoiThucHien === 'Trần Thị Thúy Na' ? 'selected' : ''}>Trần Thị Thúy Na</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label" style="font-size:13px;">Người phối hợp</label>
              <select id="formNguoiPhoiHop" class="form-control" style="font-size:14px; height:40px;">
                <option value="">-- Chọn người phối hợp --</option>
                <option value="Trần Thị Thúy Na" ${cv?.nguoiPhoiHop === 'Trần Thị Thúy Na' ? 'selected' : ''}>Trần Thị Thúy Na</option>
                <option value="Phòng KT-TC" ${cv?.nguoiPhoiHop === 'Phòng KT-TC' ? 'selected' : ''}>Phòng KT-TC</option>
              </select>
            </div>
          </div>

          <div class="form-group" style="margin-bottom:20px;">
            <label class="form-label" style="font-size:13px;">Nội dung công việc <span style="color:#EF4444;">*</span></label>
            <textarea id="formNoiDung" class="form-control" rows="6" placeholder="Nhập nội dung công việc...">${cv?.noiDungCV || ''}</textarea>
          </div>

          <div class="form-group" style="margin-bottom:20px;">
            <label class="form-label" style="font-size:13px;">Ghi chú</label>
            <textarea id="formGhiChu" class="form-control" rows="2" placeholder="Nhập ghi chú (nếu có)...">${cv?.ghiChu || ''}</textarea>
          </div>

          <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; margin-bottom:32px;">
            <div class="form-group">
              <label class="form-label" style="font-size:13px;">File đính kèm</label>
              <div class="upload-zone" style="border:1px dashed #D1D5DB; border-radius:4px; padding:20px; text-align:center; background:#F9FAFB; cursor:pointer;">
                ${cv?.fileDinhKem ? `
                  <div style="display:flex; align-items:center; justify-content:center;">
                    <div style="background:#FEF2F2; color:#EF4444; border:1px solid #FECACA; border-radius:4px; padding:4px 8px; font-size:10px; font-weight:700; margin-right:12px;">PDF</div>
                    <div style="text-align:left;">
                      <div style="font-size:14px; font-weight:600; color:var(--text-color);">${cv.fileDinhKem}</div>
                      <div style="font-size:12px; color:var(--text-muted);">PDF Document</div>
                    </div>
                  </div>
                ` : `
                  <div style="font-size:14px; color:var(--text-color); margin-bottom:4px;">Kéo thả file hoặc <span style="color:var(--primary); font-weight:600;">chọn file</span></div>
                  <div style="font-size:11px; color:var(--text-muted);">PDF, DOC, DOCX, XLS, XLSX (Tối đa 50MB/1 file)</div>
                `}
              </div>
            </div>
            <div class="form-group">
              <label class="form-label" style="font-size:13px;">Tài liệu liên quan</label>
              <div class="upload-zone" style="border:1px dashed #D1D5DB; border-radius:4px; padding:20px; text-align:center; background:#F9FAFB; cursor:pointer;">
                <div style="font-size:14px; color:var(--text-color); margin-bottom:4px;">Kéo thả file hoặc <span style="color:var(--primary); font-weight:600;">chọn file</span></div>
                <div style="font-size:11px; color:var(--text-muted);">PDF, DOC, DOCX, XLS, XLSX (Tối đa 50MB/1 file)</div>
              </div>
            </div>
          </div>

          <div style="display:flex; justify-content:flex-end; gap:12px; border-top: 1px solid var(--border-color); padding-top:24px;">
            <button class="btn btn-secondary" id="btnCancelFormCongViec" style="padding:8px 32px; background:#F1F5F9; border:none; color:var(--text-color);">Hủy</button>
            <button class="btn btn-primary" id="btnSaveForm" style="padding:8px 32px; opacity:0.6; cursor:not-allowed;" disabled>Lưu</button>
          </div>
        </div>
      </div>
    `;

    document.getElementById('congViecFormView').innerHTML = html;
    switchView('congViecFormView', breadcrumbs);

    // Validation
    const reqFields = ['formNguonGiao', 'formNgayBatDau', 'formHanXuLy', 'formTenCV', 'formChuyenVien', 'formNoiDung'];
    const validate = () => {
      let valid = true;
      reqFields.forEach(id => {
        if (!document.getElementById(id).value) valid = false;
      });
      const btn = document.getElementById('btnSaveForm');
      btn.disabled = !valid;
      btn.style.opacity = valid ? '1' : '0.6';
      btn.style.cursor = valid ? 'pointer' : 'not-allowed';
    };
    reqFields.forEach(id => document.getElementById(id).addEventListener('input', validate));
    reqFields.forEach(id => document.getElementById(id).addEventListener('change', validate));
    validate(); // initial check

    document.getElementById('btnCancelFormCongViec')?.addEventListener('click', () => {
      if (isEdit) viewCongViecDetail(cvId);
      else goToListView();
    });

    document.getElementById('btnSaveForm')?.addEventListener('click', () => {
      const payload = {
        tenLanhDao: cv?.tenLanhDao || user.name,
        nguonCV: document.getElementById('formNguonGiao')?.value || '',
        ngayBatDau: formatDateForDisplay(document.getElementById('formNgayBatDau')?.value || ''),
        hanXuLy: formatDateForDisplay(document.getElementById('formHanXuLy')?.value || ''),
        tenCongViec: document.getElementById('formTenCV')?.value.trim() || '',
        nguoiThucHien: document.getElementById('formChuyenVien')?.value || '',
        nguoiPhoiHop: document.getElementById('formNguoiPhoiHop')?.value || '',
        noiDungCV: document.getElementById('formNoiDung')?.value.trim() || '',
        ghiChu: document.getElementById('formGhiChu')?.value.trim() || '',
        fileDinhKem: cv?.fileDinhKem || 'CV_1735_CT_CS.pdf'
      };

      if (isEdit) {
        Object.assign(cv, payload);
        filteredData = [...MOCK_CONG_VIEC];
        applyFilters();
        showToast('Đã cập nhật công việc.', 'success');
        viewCongViecDetail(cv.id);
        return;
      }

      const newCv = {
        id: Date.now(),
        maGiaoViec: `GV-${String(MOCK_CONG_VIEC.length + 1).padStart(3, '0')}`,
        trangThai: getGVStatusLabel('cho-xu-ly'),
        ...payload
      };

      MOCK_CONG_VIEC.unshift(newCv);
      filteredData = [...MOCK_CONG_VIEC];
      applyFilters();
      showToast('Đã tạo công việc mới.', 'success');
      viewCongViecDetail(newCv.id);
    });
  };

  function formatDateForInput(dStr) {
    if (!dStr) return '';
    const parts = dStr.split('/');
    if (parts.length === 3) return `${parts[2]}-${parts[1]}-${parts[0]}`;
    return dStr;
  }

  function getDetailButtons(cv) {
    const status = normalizeGVStatus(cv.trangThai);
    const editBtn = `<button class="btn btn-primary" style="padding:8px 16px;font-weight:500;" onclick="renderForm(${cv.id})"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="vertical-align:middle;margin-right:6px;"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25z"/></svg>Chỉnh sửa</button>`;
    const deleteBtn = `<button class="btn" style="background:#E85D4F;color:#fff;border:none;border-radius:4px;padding:8px 16px;font-weight:500;" onclick="deleteCongViec(${cv.id})"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="vertical-align:middle;margin-right:6px;"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>Xoá văn bản</button>`;
    const processBtn = `<button class="btn btn-primary" style="padding:8px 16px;font-weight:500;" onclick="handleXuLyCV(${cv.id})"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="vertical-align:middle;margin-right:6px;"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25z"/></svg>Xử lý</button>`;
    const returnToLeaderBtn = `<button class="btn" style="background:#E63946;color:#fff;border:none;border-radius:4px;padding:8px 16px;font-weight:500;" onclick="openReturnCongViec(${cv.id}, 'specialist')">Hoàn trả giao việc</button>`;
    const returnToSpecialistBtn = `<button class="btn" style="background:#E63946;color:#fff;border:none;border-radius:4px;padding:8px 16px;font-weight:500;" onclick="openReturnCongViec(${cv.id}, 'leader')">Hoàn trả công việc</button>`;
    const approveBtn = `<button class="btn btn-primary" style="padding:8px 16px;font-weight:500;" onclick="approveCongViec(${cv.id})">Phê duyệt</button>`;

    if (user.role === 'lanhdao') {
      if (status === 'cho-duyet') return `${editBtn}${approveBtn}${returnToSpecialistBtn}${deleteBtn}`;
      return `${editBtn}${deleteBtn}`;
    }

    if (user.role === 'chuyenvien') {
      if (status === 'cho-xu-ly' || status === 'dang-xu-ly') return `${returnToLeaderBtn}${processBtn}`;
      return `${editBtn}${deleteBtn}`;
    }

    return `<span style="font-size:13px;color:var(--text-muted);">Chỉ xem</span>`;
  }

  function getDetailExtraField(cv) {
    const status = normalizeGVStatus(cv.trangThai);
    if (status === 'hoan-tra') return { label: 'Ngày hoàn trả', value: cv.ngayHoanTra || '09/02/2025' };
    if (status === 'cho-duyet') return { label: 'Ngày duyệt', value: cv.ngayDuyet || '10/02/2026' };
    if (status === 'da-hoan-thanh') return { label: 'Ngày phê duyệt', value: cv.ngayPheDuyet || cv.ngayDuyet || '10/02/2026' };
    return null;
  }

  // --- DETAIL VIEW (MÀN 3, 4, 5) ---
  window.viewCongViecDetail = function(id) {
    const cv = getCongViecById(id);
    if (!cv) return;

    const extraField = getDetailExtraField(cv);
    const extraFieldHtml = extraField ? `
      <div style="margin-bottom:16px;">
        <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">${extraField.label}</div>
        <div style="font-size:15px; color:var(--text-color); font-weight:600;">${extraField.value}</div>
      </div>
    ` : '';

    const html = `
      <div class="card" style="background:#fff; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.1); padding:24px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:16px; margin-bottom:24px;">
          <h3 style="color:var(--text-color); font-size:16px; font-weight:700; border-left:4px solid var(--primary); padding-left:12px; margin:0; text-transform:uppercase;">
            THÔNG TIN CHI TIẾT CÔNG VIỆC
          </h3>
          <div style="display:flex; flex-direction:column; align-items:flex-end; gap:12px;">
            <div style="display:flex; flex-wrap:wrap; justify-content:flex-end; gap:8px;">${getDetailButtons(cv)}</div>
            ${renderBadgeGV(cv.trangThai)}
          </div>
        </div>
        
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:32px; margin-bottom:32px;">
          <div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Lãnh đạo giao việc</div>
              <div style="font-size:15px; color:var(--text-color); font-weight:600;">${cv.tenLanhDao || '—'}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Nguồn giao</div>
              <div style="font-size:15px; color:var(--text-color); font-weight:600;">${cv.nguonCV || '—'}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Chuyên viên thực hiện</div>
              <div style="font-size:15px; color:var(--text-color); font-weight:600;">${cv.nguoiThucHien || '—'}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Ngày bắt đầu</div>
              <div style="font-size:15px; color:var(--text-color); font-weight:600;">${cv.ngayBatDau || '—'}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Nội dung công việc</div>
              <div style="font-size:15px; color:var(--text-color); line-height:1.5;">${cv.noiDungCV || '—'}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Ghi chú</div>
              <div style="font-size:15px; color:var(--text-color); font-weight:600;">${cv.ghiChu || '—'}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:8px;">File đính kèm</div>
              <div style="display:flex; align-items:center;">
                <div style="background:#FEF2F2; color:#EF4444; border:1px solid #FECACA; border-radius:4px; padding:4px 8px; font-size:10px; font-weight:700; margin-right:12px;">PDF</div>
                <div>
                  <div style="font-size:14px; font-weight:600; color:var(--text-color);">${cv.fileDinhKem || 'CV_1735_CT_CS.pdf'}</div>
                  <div style="font-size:12px; color:var(--text-muted);">PDF Document</div>
                </div>
              </div>
            </div>
          </div>
          <div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Mã giao việc</div>
              <div style="font-size:15px; color:var(--text-color); font-weight:600;">${cv.maGiaoViec || '—'}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Tên công việc</div>
              <div style="font-size:15px; color:var(--text-color); font-weight:600;">${cv.tenCongViec || '—'}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Người phối hợp</div>
              <div style="font-size:15px; color:var(--text-color); font-weight:600;">${cv.nguoiPhoiHop || '—'}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Hạn xử lý</div>
              <div style="font-size:15px; color:var(--text-color); font-weight:600;">${cv.hanXuLy || '—'}</div>
            </div>
            ${extraFieldHtml}
          </div>
        </div>

        <div style="margin-top:40px; border-top:1px solid var(--border-color); padding-top:24px;">
          <div style="font-size:14px; font-weight:700; color:var(--text-muted); margin-bottom:16px; text-transform:uppercase;">Xem trước</div>
          <div style="background:#52525B; border-radius:4px; overflow:hidden; display:flex; flex-direction:column; align-items:center; padding-bottom:40px;">
            <div style="width:100%; background:#3F3F46; padding:8px 16px; display:flex; justify-content:space-between; align-items:center; color:#fff;">
              <div style="font-size:13px;">${cv.fileDinhKem || 'CV_1735_CT_CS.pdf'}</div>
              <div style="display:flex; align-items:center; gap:20px;">
                <span style="font-size:13px; opacity:0.8;">1 / 1</span>
                <span style="font-size:18px; cursor:pointer;">—</span>
                <span style="font-size:18px; cursor:pointer;">+</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="cursor:pointer;"><path d="M19 8H5c-1.66 0-3 1.34-3 3v6h4v4h12v-4h4v-6c0-1.66-1.34-3-3-3zm-3 11H8v-5h8v5zm3-7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm-1-9H6v4h12V3z"/></svg>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="cursor:pointer;"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
              </div>
            </div>
            <div style="background:#fff; width:700px; min-height:900px; margin-top:24px; padding:60px; box-shadow:0 10px 15px -3px rgba(0,0,0,0.3);">
              <div style="display:flex; justify-content:space-between; margin-bottom:50px;">
                <div style="text-align:center;">
                  <p style="font-weight:bold; font-size:13px; margin:0;">BỘ TÀI CHÍNH</p>
                  <p style="font-weight:bold; font-size:13px; margin:0; text-decoration:underline;">CỤC THUẾ</p>
                  <p style="font-size:12px; margin-top:10px;">Số: 1735/CT-CS</p>
                </div>
                <div style="text-align:center;">
                  <p style="font-weight:bold; font-size:13px; margin:0;">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</p>
                  <p style="font-weight:bold; font-size:13px; margin:0; text-decoration:underline;">Độc lập - Tự do - Hạnh phúc</p>
                  <p style="font-size:12px; margin-top:10px; font-style:italic;">Hà Nội, ngày 13 tháng 6 năm 2025</p>
                </div>
              </div>
              <p style="font-size:13px;">V/v giới thiệu nội dung mới tại Nghị định số 117/2025/NĐ-CP của Chính phủ...</p>
              <p style="text-align:center; font-weight:bold; margin:30px 0; font-size:14px;">Kính gửi: Các Chi cục Thuế khu vực.</p>
              <p style="font-size:13px; line-height:1.7; text-align:justify;">
                Ngày 09/6/2025, Chính phủ đã ban hành Nghị định số 117/2025/NĐ-CP quy định về quản lý thuế đối với hoạt động kinh doanh trên nền tảng thương mại điện tử...
              </p>
            </div>
          </div>
        </div>
      </div>
    `;

    document.getElementById('congViecDetailView').innerHTML = html;
    switchView('congViecDetailView', [{text: 'Quản lý công việc', link: true, view: 'congViecListView'}, {text: 'Thông tin chi tiết công việc'}]);
  };

  window.openReturnCongViec = function(id, mode = 'specialist') {
    const cv = getCongViecById(id);
    if (!cv) return;

    const isLeaderReturn = mode === 'leader';
    const personLabel = isLeaderReturn ? 'Chuyên viên' : 'Lãnh đạo';
    const personName = isLeaderReturn ? (cv.nguoiThucHien || '—') : (cv.tenLanhDao || '—');
    const placeholder = isLeaderReturn
      ? 'Nhập chi tiết lý do hoàn trả, nội dung cần chỉnh sửa để chuyên viên tiếp tục xử lý...'
      : 'Nhập chi tiết lý do, nội dung sai sót hoặc đề xuất chỉnh sửa để Lãnh đạo nắm thông tin...';

    document.getElementById('congViecCapNhatView').innerHTML = `
      <div class="card" style="background:#fff; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.1); padding:40px 32px;">
        <h1 style="font-size:28px; color:#0F7AA8; margin:0 0 32px 0; font-weight:700;">Hoàn trả công việc</h1>
        <div style="font-size:20px; font-weight:700; color:#2F343B; margin-bottom:28px;">${personLabel} : ${personName}</div>
        <div style="font-size:18px; font-weight:700; color:#2F343B; margin-bottom:16px;">Lý do hoàn trả</div>
        <textarea id="formLyDoHoanTra" class="form-control" rows="5" placeholder="${placeholder}" style="font-size:16px; padding:18px;">${cv.lyDoHoanTra || ''}</textarea>
        <div style="display:flex; justify-content:flex-end; gap:16px; margin-top:24px;">
          <button class="btn btn-secondary" id="btnCancelHoanTraCongViec" style="padding:12px 40px; background:#F3F4F6; color:#374151; border:none;">Hủy</button>
          <button class="btn btn-primary" id="btnSaveHoanTraCongViec" style="padding:12px 40px;">Lưu</button>
        </div>
      </div>
    `;

    switchView('congViecCapNhatView', [{text: 'Quản lý công việc', link: true, view: 'congViecListView'}, {text: 'Thông tin chi tiết công việc', link: true, view: 'congViecDetailView', id: id}, {text: 'Hoàn trả công việc'}]);

    document.getElementById('btnCancelHoanTraCongViec')?.addEventListener('click', () => viewCongViecDetail(id));
    document.getElementById('btnSaveHoanTraCongViec')?.addEventListener('click', () => {
      const reason = document.getElementById('formLyDoHoanTra')?.value.trim();
      if (!reason) {
        showToast('Vui lòng nhập lý do hoàn trả.', 'error');
        return;
      }

      cv.lyDoHoanTra = reason;
      cv.ngayHoanTra = getTodayDisplay();
      setGVStatus(cv, 'hoan-tra');
      filteredData = [...MOCK_CONG_VIEC];
      applyFilters();
      showToast(isLeaderReturn ? 'Đã hoàn trả công việc về chuyên viên.' : 'Đã hoàn trả giao việc cho lãnh đạo.', 'success');
      viewCongViecDetail(id);
    });
  };

  window.approveCongViec = function(id) {
    if (user.role !== 'lanhdao') {
      showToast('Chỉ lãnh đạo mới có quyền phê duyệt.', 'error');
      return;
    }

    const cv = getCongViecById(id);
    if (!cv) return;

    showConfirm('Phê duyệt công việc', 'Xác nhận phê duyệt hoàn thành công việc này?', () => {
      cv.ngayPheDuyet = getTodayDisplay();
      cv.ngayDuyet = cv.ngayDuyet || cv.ngayPheDuyet;
      setGVStatus(cv, 'da-hoan-thanh');
      filteredData = [...MOCK_CONG_VIEC];
      applyFilters();
      showToast('Đã phê duyệt công việc.', 'success');
      viewCongViecDetail(id);
    });
  };

  window.deleteCongViec = function(id) {
    showConfirm('Xoá công việc', 'Bạn có chắc chắn muốn xoá công việc này?', () => {
      const index = MOCK_CONG_VIEC.findIndex(cv => cv.id === id);
      if (index !== -1) MOCK_CONG_VIEC.splice(index, 1);
      filteredData = [...MOCK_CONG_VIEC];
      applyFilters();
      showToast('Đã xoá công việc.', 'success');
      goToListView();
    });
  };

  // --- XỬ LÝ CÔNG VIỆC (MÀN 3 -> FORM) ---
  window.handleXuLyCV = function(id) {
    const cv = getCongViecById(id);
    if (!cv) return;

    document.getElementById('congViecXulyView').innerHTML = `
      <div class="card" style="background:#fff; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.1); padding:24px;">
        <h3 style="color:var(--text-color); font-size:16px; font-weight:700; border-left:4px solid var(--primary); padding-left:12px; margin:0 0 24px 0; text-transform:uppercase;">
          XỬ LÝ CÔNG VIỆC
        </h3>
        
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:32px; margin-bottom:32px; border-bottom:1px solid var(--border-color); padding-bottom:32px;">
          <div>
            <div style="margin-bottom:16px;"><div style="font-size:12px; color:var(--text-muted); margin-bottom:4px;">Tên công việc</div><div style="font-size:14px; font-weight:600;">${cv.tenCongViec}</div></div>
            <div style="margin-bottom:16px;"><div style="font-size:12px; color:var(--text-muted); margin-bottom:4px;">Nội dung công việc (Yêu cầu xử lý)</div><div style="font-size:14px; line-height:1.6;">${cv.noiDungCV}</div></div>
            <div style="margin-bottom:16px;">
              <div style="font-size:12px; color:var(--text-muted); margin-bottom:8px;">Tài liệu liên quan</div>
              <div style="display:flex; align-items:center;">
                <div style="background:#FEF2F2; color:#EF4444; border:1px solid #FECACA; border-radius:4px; padding:4px 8px; font-size:10px; font-weight:700; margin-right:12px;">PDF</div>
                <div><div style="font-size:13px; font-weight:600;">CV_1735_CT_CS.pdf</div><div style="font-size:11px; color:var(--text-muted);">PDF Document</div></div>
              </div>
            </div>
          </div>
          <div><div style="font-size:12px; color:var(--text-muted); margin-bottom:4px;">Hạn hoàn thành</div><div style="font-size:14px; font-weight:600;">${cv.hanXuLy}</div></div>
        </div>

        <div style="margin-bottom:24px;">
          <h4 style="font-size:13px; font-weight:700; color:var(--text-color); margin-bottom:12px; text-transform:uppercase;">KẾT QUẢ XỬ LÝ</h4>
          <div class="form-group"><label class="form-label" style="font-size:12px;">Mô tả kết quả xử lý <span style="color:#EF4444;">*</span></label><textarea id="formKetQuaXuLy" class="form-control" rows="4" placeholder="Nhập mô tả kết quả xử lý...">${cv.ketQuaXuLy || ''}</textarea></div>
        </div>

        <div style="margin-bottom:32px;">
          <h4 style="font-size:13px; font-weight:700; color:var(--text-color); margin-bottom:12px; text-transform:uppercase;">GHI CHÚ</h4>
          <div class="form-group"><textarea id="formGhiChuXuLy" class="form-control" rows="2" placeholder="Nhập ghi chú...">${cv.ghiChuXuLy || ''}</textarea></div>
        </div>

        <div style="display:flex; justify-content:flex-end; gap:12px;">
          <button class="btn btn-secondary" id="btnCancelXuLyCongViec" style="padding:8px 32px; background:#F1F5F9; border:none; color:var(--text-color);">Hủy</button>
          <button class="btn btn-primary" id="btnSaveXuLyCongViec" style="padding:8px 32px;">Lưu xử lý</button>
        </div>
      </div>
    `;

    switchView('congViecXulyView', [{text: 'Quản lý công việc', link: true, view: 'congViecListView'}, {text: 'Thông tin chi tiết công việc', link: true, view: 'congViecDetailView', id: id}, {text: 'Xử lý công việc'}]);

    document.getElementById('btnCancelXuLyCongViec')?.addEventListener('click', () => viewCongViecDetail(id));
    document.getElementById('btnSaveXuLyCongViec')?.addEventListener('click', () => {
      const result = document.getElementById('formKetQuaXuLy')?.value.trim();
      if (!result) {
        showToast('Vui lòng nhập kết quả xử lý.', 'error');
        return;
      }

      cv.ketQuaXuLy = result;
      cv.ghiChuXuLy = document.getElementById('formGhiChuXuLy')?.value.trim() || '';
      cv.ngayDuyet = getTodayDisplay();
      setGVStatus(cv, 'cho-duyet');
      filteredData = [...MOCK_CONG_VIEC];
      applyFilters();
      showToast('Đã gửi công việc chờ lãnh đạo duyệt.', 'success');
      viewCongViecDetail(id);
    });
  };

  // Event Listeners for Filter Tabs
  document.querySelectorAll('.filter-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeTab = btn.getAttribute('data-tab');
      applyFilters();
    });
  });

  const searchInput = document.getElementById('searchKeyword');
  if (searchInput) searchInput.addEventListener('input', applyFilters);
  const sourceSelect = document.getElementById('filterNguonCV');
  if (sourceSelect) sourceSelect.addEventListener('change', applyFilters);

  const btnThem = document.getElementById('btnThemCongViec');
  if (btnThem) btnThem.addEventListener('click', () => renderForm());

  applyFilters();
  goToListView();
});
