/**
 * vanbandi.js - Văn bản đi theo vai trò chuyên viên / lãnh đạo
 */
document.addEventListener('DOMContentLoaded', function () {
  const user = requireAuth();
  if (!user) return;

  const VAN_BAN_DI = [
    {
      id: 1,
      soKyHieu: '123/HanhChinh',
      trichYeu: 'Quy chế về quy định công ty 2026',
      ngayVanBan: '03/02/2026',
      donViSoaThan: 'Phòng Kế Toán',
      doKhan: 'BÌNH THƯỜNG',
      trangThai: 'cho-xu-ly',
      hinhThuc: 'Công văn',
      loaiVanBan: 'Quyết định',
      hanXuLy: '09/02/2026',
      lanhDao: 'Phan Thanh Thảo',
      nguoiSoan: 'Phạm Thị Phương',
      noiDungTrinh: 'Kính trình lãnh đạo xem xét.',
      trangThaiVanThu: 'cho-ban-hanh',
      ngayDuyet: '20/02/2026',
      mainFiles: [{ name: 'CV_1735_CT_CS.pdf' }],
      relatedFiles: [{ name: 'CV_1735_CT_CS.pdf' }, { name: 'CV_1735_CT_CS.docx' }]
    },
    {
      id: 2,
      soKyHieu: '123/CuocHop',
      trichYeu: 'Biên bản cuộc họp 01/02/2026',
      ngayVanBan: '03/02/2026',
      donViSoaThan: 'Phòng Kế Toán',
      doKhan: 'KHẨN',
      trangThai: 'da-xu-ly',
      hinhThuc: 'Công văn',
      loaiVanBan: 'Báo cáo',
      hanXuLy: '10/02/2026',
      lanhDao: 'Phan Thanh Thảo',
      nguoiSoan: 'Phạm Thị Phương',
      noiDungTrinh: 'Kính trình lãnh đạo xem xét.',
      ngayXuLy: '10/02/2026',
      trangThaiVanThu: 'cho-ban-hanh',
      ngayDuyet: '20/02/2026',
      mainFiles: [{ name: 'CV_1735_CT_CS.pdf' }],
      relatedFiles: [{ name: 'CV_1735_CT_CS.pdf' }]
    },
    {
      id: 3,
      soKyHieu: '123/KiemToan',
      trichYeu: 'Quy chế về hệ thống kiểm toán công ty',
      ngayVanBan: '03/02/2026',
      donViSoaThan: 'Phòng Kiểm Toán',
      doKhan: 'KHẨN',
      trangThai: 'da-phat-hanh',
      hinhThuc: 'Công văn',
      loaiVanBan: 'Quyết định',
      hanXuLy: '09/02/2026',
      lanhDao: 'Phan Thanh Thảo',
      nguoiSoan: 'Phạm Thị Phương',
      noiDungTrinh: 'Kính trình lãnh đạo xem xét.',
      ngayPhatHanh: '15/02/2026',
      trangThaiVanThu: 'da-ban-hanh',
      ngayDuyet: '20/02/2026',
      nguoiBanHanh: 'Trần Thị Thúy Na',
      ngayBanHanh: '28/02/2026',
      noiBoIds: ['ke-toan', 'kiem-toan', 'ban-giam-doc'],
      donViPhatHanh: ['Phòng Kế Toán', 'Phòng Kiểm Toán', 'Ban Giám Đốc'],
      mainFiles: [{ name: 'CV_1735_CT_CS.pdf' }],
      relatedFiles: [{ name: 'CV_1735_CT_CS.pdf' }, { name: 'CV_1735_CT_CS.docx' }]
    },
    {
      id: 4,
      soKyHieu: '123/PTYC',
      trichYeu: 'SRS phân tích yêu cầu khách hàng',
      ngayVanBan: '03/02/2026',
      donViSoaThan: 'Phòng Kế Toán',
      doKhan: 'KHẨN',
      trangThai: 'hoan-tra',
      hinhThuc: 'Công văn',
      loaiVanBan: 'Quyết định',
      hanXuLy: '09/02/2026',
      lanhDao: 'Phan Thanh Thảo',
      nguoiSoan: 'Phạm Thị Phương',
      noiDungTrinh: 'Kính trình lãnh đạo xem xét.',
      ngayHoanTra: '12/02/2026',
      hanXuLyHoanTra: '20/02/2026',
      yKienHoanTra: 'Cần bổ sung số liệu chi tiết tháng 10',
      trangThaiVanThu: 'da-ban-hanh',
      ngayDuyet: '20/02/2026',
      nguoiBanHanh: 'Trần Thị Thúy Na',
      ngayBanHanh: '28/02/2026',
      noiBoIds: ['ke-toan', 'kiem-toan', 'ban-giam-doc'],
      donViPhatHanh: ['Phòng Kế Toán', 'Phòng Kiểm Toán', 'Ban Giám Đốc'],
      mainFiles: [{ name: 'CV_1735_CT_CS.pdf' }],
      relatedFiles: [{ name: 'CV_1735_CT_CS.pdf' }, { name: 'CV_1735_CT_CS.docx' }]
    }
  ];

  const INTERNAL_UNITS = [
    { id: 'ke-toan', name: 'Phòng Ban Kế Toán', count: 4 },
    { id: 'nhan-su', name: 'Phòng Nhân Sự', count: 3 },
    { id: 'cong-nghe', name: 'Trung Tâm Công Nghệ Thông Tin', count: 5 },
    { id: 'kinh-doanh', name: 'Phòng Kinh Doanh', count: 4 },
    { id: 'kiem-toan', name: 'Phòng Kiểm Toán', count: 4 },
    { id: 'ban-giam-doc', name: 'Ban Giám Đốc', count: 3 }
  ];

  const EXTERNAL_UNITS_SEED = [
    {
      id: 'outside-1',
      name: 'Công ty TNHH Một Ngày Nắng',
      representative: 'Nguyễn Xuân Khánh',
      phone: '0358702592',
      email: 'xuankhanh@gmail.com'
    },
    {
      id: 'outside-2',
      name: 'Công ty TNHH Một Ngày Nắng',
      representative: 'Nguyễn Xuân Khánh',
      phone: '0358702592',
      email: 'xuankhanh@gmail.com'
    },
    {
      id: 'outside-3',
      name: 'Công ty TNHH Một Ngày Nắng',
      representative: 'Nguyễn Xuân Khánh',
      phone: '0358702592',
      email: 'xuankhanh@gmail.com'
    },
    {
      id: 'outside-4',
      name: 'Công ty TNHH Một Ngày Nắng',
      representative: 'Nguyễn Xuân Khánh',
      phone: '0358702592',
      email: 'xuankhanh@gmail.com'
    },
    {
      id: 'outside-5',
      name: 'Công ty TNHH Một Ngày Nắng',
      representative: 'Nguyễn Xuân Khánh',
      phone: '0358702592',
      email: 'xuankhanh@gmail.com'
    }
  ];

  const STATUS_META = {
    'cho-xu-ly': { label: 'Chờ xử lý', bg: '#FEF3C7', color: '#B45309' },
    'da-xu-ly': { label: 'Đã xử lý', bg: '#DBEAFE', color: '#2563EB' },
    'hoan-tra': { label: 'Hoàn trả', bg: '#FCE7F3', color: '#BE185D' },
    'da-phat-hanh': { label: 'Đã phát hành', bg: '#DCFCE7', color: '#15803D' },
    'cho-ban-hanh': { label: 'Chờ ban hành', bg: '#FEF3C7', color: '#B45309' },
    'da-ban-hanh': { label: 'Đã ban hành', bg: '#DCFCE7', color: '#15803D' }
  };

  const ROLE_TAB_CONFIG = {
    default: [
      { label: 'Tất cả', status: 'all' },
      { label: 'Chờ xử lý', status: 'cho-xu-ly' },
      { label: 'Đã xử lý', status: 'da-xu-ly' },
      { label: 'Hoàn trả', status: 'hoan-tra' },
      { label: 'Đã phát hành', status: 'da-phat-hanh' }
    ],
    vanthu: [
      { label: 'Tất cả', status: 'all' },
      { label: 'Chờ ban hành', status: 'cho-ban-hanh' },
      { label: 'Đã ban hành', status: 'da-ban-hanh' }
    ]
  };

  const DEFAULT_APPROVE_DATE = '20/02/2026';
  const DEFAULT_PUBLISH_DATE = '28/02/2026';

  const breadcrumbBar = document.getElementById('breadcrumbBarVBDi');
  const listView = document.getElementById('vbdiListView');
  const formView = document.getElementById('vbdiFormView');
  const detailView = document.getElementById('vbdiDetailView');
  const internalModal = document.getElementById('modalChonDonViNoiBo');
  const externalModal = document.getElementById('modalChonDonViNgoai');
  const addExternalModal = document.getElementById('modalThemDonViNgoai');
  const publishTargetTypeNoiBo = document.getElementById('publishTargetTypeNoiBo');
  const publishTargetTypeNgoai = document.getElementById('publishTargetTypeNgoai');
  const searchNoiBoInput = document.getElementById('searchNoiBo');
  const searchNgoaiInput = document.getElementById('searchNgoai');
  const tbodyNoiBo = document.getElementById('tbodyNoiBo');
  const tbodyNgoai = document.getElementById('tbodyNgoai');
  const chkAllNoiBo = document.getElementById('chkAllNoiBo');
  const chkAllNgoai = document.getElementById('chkAllNgoai');
  const countNoiBo = document.getElementById('countNoiBo');
  const countNgoai = document.getElementById('countNgoai');

  let filteredData = [...VAN_BAN_DI];
  let currentPage = 1;
  let activeStatus = 'all';
  let editingId = null;
  let currentDocId = null;
  let selectedMainFiles = [];
  let selectedRelatedFiles = [];
  let externalUnits = EXTERNAL_UNITS_SEED.map(unit => ({ ...unit }));
  let selectedInternalIds = [];
  let selectedExternalIds = [];
  let editingExternalId = null;

  const perPage = 4;

  function setBreadcrumb(mode) {
    if (!breadcrumbBar) return;

    const home = '<a href="dashboard.html"><svg width="14" height="14" viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>Trang chủ</a>';
    const link = (label, view) => `<a href="#" class="vbdi-breadcrumb-link" data-view="${view}">${label}</a>`;

    let trail = '';
    if (mode === 'form-create') {
      trail = `${link('Văn bản đi', 'list')} <span class="breadcrumb-sep">/</span> <span>Soạn thảo văn bản đi</span>`;
    } else if (mode === 'form-edit') {
      trail = `${link('Văn bản đi', 'list')} <span class="breadcrumb-sep">/</span> <span>Chỉnh sửa văn bản đi</span>`;
    } else if (mode === 'detail') {
      trail = `${link('Văn bản đi', 'list')} <span class="breadcrumb-sep">/</span> <span>Chi tiết văn bản</span>`;
    } else {
      trail = '<span>Văn bản đi</span>';
    }

    breadcrumbBar.innerHTML = `${home}<span class="breadcrumb-sep">›</span>${trail}`;
    breadcrumbBar.querySelectorAll('.vbdi-breadcrumb-link').forEach(linkEl => {
      linkEl.addEventListener('click', function (e) {
        e.preventDefault();
        if (this.dataset.view === 'list') showVBDiListView();
      });
    });
  }

  function showOnly(viewEl) {
    [listView, formView, detailView].forEach(el => {
      if (el) el.style.display = el === viewEl ? 'block' : 'none';
    });
    window.scrollTo(0, 0);
  }

  function showVBDiListView() {
    showOnly(listView);
    setBreadcrumb('list');
    applyFilters();
  }

  function showVBDiFormView(isEdit = false) {
    showOnly(formView);
    setBreadcrumb(isEdit ? 'form-edit' : 'form-create');
    const title = document.getElementById('formViewTitle');
    if (title) title.textContent = isEdit ? 'Chỉnh sửa văn bản đi' : 'Soạn thảo văn bản đi';
    checkFormValidation();
  }

  function showVBDiDetailView() {
    showOnly(detailView);
    setBreadcrumb('detail');
  }

  function toInputDate(dateStr) {
    if (!dateStr) return '';
    const parts = dateStr.split('/');
    if (parts.length === 3) return `${parts[2]}-${parts[1]}-${parts[0]}`;
    return dateStr;
  }

  function fromInputDate(dateStr) {
    if (!dateStr) return '';
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
      const [year, month, day] = dateStr.split('-');
      return `${day}/${month}/${year}`;
    }
    return dateStr;
  }

  function cloneFiles(files) {
    return files.map(file => ({ ...file }));
  }

  function getFileTypeLabel(fileName) {
    const ext = (fileName.split('.').pop() || '').toLowerCase();
    if (ext === 'pdf') return { label: 'PDF', color: '#DC2626' };
    if (ext === 'doc' || ext === 'docx') return { label: 'DOCX', color: '#2563EB' };
    if (ext === 'xls' || ext === 'xlsx') return { label: 'XLS', color: '#15803D' };
    return { label: ext.toUpperCase() || 'FILE', color: '#64748B' };
  }

  function getFileTypeText(fileName) {
    const ext = (fileName.split('.').pop() || '').toLowerCase();
    if (ext === 'pdf') return 'PDF Document';
    if (ext === 'doc' || ext === 'docx') return 'Docx Document';
    if (ext === 'xls' || ext === 'xlsx') return 'Excel Document';
    return 'File Document';
  }

  function renderStatusBadge(statusCode) {
    const meta = STATUS_META[statusCode] || { label: statusCode, bg: '#E5E7EB', color: '#374151' };
    return `<span style="display:inline-block;padding:6px 16px;border-radius:18px;background:${meta.bg};color:${meta.color};font-size:13px;font-weight:600;">${meta.label}</span>`;
  }

  function getDisplayStatus(doc) {
    if (user.role !== 'vanthu') return doc.trangThai;
    if (doc.trangThaiVanThu) return doc.trangThaiVanThu;
    if (doc.trangThai === 'da-phat-hanh') return 'da-ban-hanh';
    if (doc.trangThai === 'da-xu-ly') return 'cho-ban-hanh';
    return null;
  }

  function getRoleDocs() {
    return VAN_BAN_DI.filter(doc => {
      if (user.role !== 'vanthu') return true;
      return !!getDisplayStatus(doc);
    });
  }

  function getRoleTabConfig() {
    return user.role === 'vanthu' ? ROLE_TAB_CONFIG.vanthu : ROLE_TAB_CONFIG.default;
  }

  function configureRoleTabs() {
    const buttons = Array.from(document.querySelectorAll('.tab-filter-btn'));
    const config = getRoleTabConfig();

    buttons.forEach((button, index) => {
      const item = config[index];
      if (!item) {
        button.style.display = 'none';
        button.classList.remove('active');
        return;
      }
      button.style.display = 'inline-flex';
      button.dataset.status = item.status;
      button.textContent = item.label;
      button.classList.toggle('active', index === 0);
    });

    activeStatus = 'all';
  }

  function getPublishedUnits(doc) {
    const names = [];
    const internalNames = INTERNAL_UNITS
      .filter(unit => (doc.noiBoIds || []).includes(unit.id))
      .map(unit => unit.name);
    const externalNames = externalUnits
      .filter(unit => (doc.ngoaiIds || []).includes(unit.id))
      .map(unit => unit.name);

    if (doc.donViPhatHanh?.length) names.push(...doc.donViPhatHanh);
    if (internalNames.length) names.push(...internalNames);
    if (externalNames.length) names.push(...externalNames);

    return [...new Set(names)];
  }

  function getCurrentDoc() {
    return VAN_BAN_DI.find(item => item.id === currentDocId) || null;
  }

  function closeModalById(id) {
    const modal = document.getElementById(id);
    if (modal) modal.style.display = 'none';
  }

  function renderPublishInfoCard(doc) {
    const units = getPublishedUnits(doc);
    if (user.role !== 'vanthu' || getDisplayStatus(doc) !== 'da-ban-hanh' || !units.length) return '';

    return `
      <div class="card" style="padding:24px 32px; border: 1px solid var(--border-color); box-shadow: none; margin-bottom: 24px;">
        <div class="filter-title" style="border-left: 4px solid var(--primary); padding-left: 12px; font-size: 16px; font-weight: 700; color: var(--primary); text-transform: uppercase; margin-bottom: 24px;">DANH SÁCH ĐƠN VỊ ĐÃ PHÁT HÀNH</div>
        <div style="border-left:4px solid var(--primary); padding-left:12px; display:flex; flex-direction:column; gap:8px; color:var(--text-main); font-size:14px;">
          ${units.map(unit => `<div>${unit}</div>`).join('')}
        </div>
      </div>
    `;
  }

  function getVanThuActionButtons(doc, displayStatus) {
    if (displayStatus === 'da-ban-hanh') {
      return `
        <button class="btn btn-primary" style="padding:8px 16px;" onclick="openChonDonViNoiBo(${doc.id})">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="white" style="margin-right:6px;vertical-align:middle;"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zm14.71-9.04c.39-.39.39-1.02 0-1.41l-2.5-2.5a.9959.9959 0 0 0-1.41 0l-1.96 1.96 3.75 3.75 2.12-2.1z"/></svg>Chỉnh sửa ban hành
        </button>
      `;
    }

    return `
      <button class="btn btn-primary" style="padding:8px 16px;" onclick="openChonDonViNoiBo(${doc.id})">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="white" style="margin-right:6px;vertical-align:middle;"><path d="M12 2L4.5 5v6c0 5.25 3.57 10.16 7.5 11 3.93-.84 7.5-5.75 7.5-11V5L12 2zm-1.2 14.2l-3.3-3.3 1.4-1.4 1.9 1.88 4.3-4.3 1.4 1.42-5.7 5.7z"/></svg>Ban hành
      </button>
    `;
  }

  function getLeaderActionButtons(doc) {
    const buttons = [
      `
        <button class="btn btn-primary" style="padding:8px 16px;" onclick="assignVBDiTask(${doc.id})">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="white" style="margin-right:6px;vertical-align:middle;"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>Giao việc
        </button>
      `
    ];

    if (doc.trangThai === 'cho-xu-ly') {
      buttons.push(`
        <button class="btn btn-danger" style="padding:8px 16px; background:#E34F4F; border:none;" onclick="openReturnLeaderVBDi(${doc.id})">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="white" style="margin-right:6px;vertical-align:middle;"><path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.82l1.46 1.46A7.938 7.938 0 0 0 20 13c0-4.42-3.58-8-8-8zm-6.3 1.18L4.24 7.64A7.938 7.938 0 0 0 4 13c0 4.42 3.58 8 8 8v4l5-5-5-5v4c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.82z"/></svg>Hoàn trả
        </button>
      `);
      buttons.push(`
        <button class="btn btn-primary" style="padding:8px 16px;" onclick="openApproveLeaderVBDi(${doc.id})">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="white" style="margin-right:6px;vertical-align:middle;"><path d="M12 2L4.5 5v6c0 5.25 3.57 10.16 7.5 11 3.93-.84 7.5-5.75 7.5-11V5L12 2zm-1.2 14.2l-3.3-3.3 1.4-1.4 1.9 1.88 4.3-4.3 1.4 1.42-5.7 5.7z"/></svg>Phê duyệt
        </button>
      `);
    }

    return buttons.join('');
  }

  function populateLeaderApproveModal(doc) {
    const selectedSpecialist = document.getElementById('returnVBDiSpecialistName');
    if (selectedSpecialist) selectedSpecialist.textContent = `Chuyên viên : ${doc.nguoiSoan || 'Phạm Thị Phương'}`;

    const returnTextarea = document.getElementById('txtHoanTraLyDoDi');
    if (returnTextarea) {
      returnTextarea.value = '';
      returnTextarea.placeholder = 'Nhập lý do / Yêu cầu chỉnh sửa cho chuyên viên...';
    }

    const mainFile = doc.mainFiles?.[0];
    const relatedFile = doc.relatedFiles?.[0];
    const modal = document.getElementById('modalPheDuyetVBDi');
    if (!modal) return;

    const mainCard = document.getElementById('approveVBDiMainFile');
    const relatedCard = document.getElementById('approveVBDiRelatedFile');
    if (mainCard && mainFile) {
      const type = getFileTypeLabel(mainFile.name);
      mainCard.innerHTML = `
        <div style="display:flex; gap:12px; align-items:center;">
          <span style="color:${type.color}; font-weight:bold; font-size:11px;">${type.label}</span>
          <div><div style="font-size:13px; font-weight:700; color:var(--text-main);">${mainFile.name}</div><div style="font-size:12px; color:var(--text-muted);">${getFileTypeText(mainFile.name)}</div></div>
        </div>
        <button style="border:none;background:none;color:#0284C7;cursor:pointer;font-size:16px;">✕</button>
      `;
    }
    if (relatedCard && relatedFile) {
      const type = getFileTypeLabel(relatedFile.name);
      relatedCard.innerHTML = `
        <div style="display:flex; gap:12px; align-items:center;">
          <span style="color:${type.color}; font-weight:bold; font-size:11px;">${type.label}</span>
          <div><div style="font-size:13px; font-weight:700; color:var(--text-main);">${relatedFile.name}</div><div style="font-size:12px; color:var(--text-muted);">${getFileTypeText(relatedFile.name)}</div></div>
        </div>
        <button style="border:none;background:none;color:#0284C7;cursor:pointer;font-size:16px;">✕</button>
      `;
    }

    modal.querySelectorAll('input[name="vanthuRadio"]').forEach(input => {
      input.checked = false;
      const label = input.parentElement?.querySelector('span');
      if (label) label.textContent = 'Lê Văn C (Văn thư)';
    });

    const note = document.getElementById('txtPheDuyetGhiChu');
    if (note) note.value = '';
  }

  function renderFormFileList(targetId, files, kind) {
    const listEl = document.getElementById(targetId);
    if (!listEl) return;

    if (!files.length) {
      listEl.innerHTML = '';
      listEl.style.display = 'none';
      return;
    }

    listEl.style.display = 'flex';
    listEl.innerHTML = files.map((file, index) => {
      const fileType = getFileTypeLabel(file.name);
      return `
        <div style="display:flex; align-items:center; justify-content:space-between; padding:8px 16px; border:1px solid var(--border-color); border-radius:4px; background:#fff;">
          <div style="display:flex; gap:12px; align-items:center;">
            <span style="color:${fileType.color}; font-weight:bold; font-size:10px;">${fileType.label}</span>
            <div>
              <div style="font-size:13px; font-weight:600; color:var(--text-main);">${file.name}</div>
              <div style="font-size:11px; color:var(--text-muted);">${getFileTypeText(file.name)}</div>
            </div>
          </div>
          <button type="button" style="border:none;background:none;color:#0284C7;cursor:pointer;font-size:18px;line-height:1;" onclick="removeVBDiFile('${kind}', ${index})">×</button>
        </div>
      `;
    }).join('');
  }

  function resetForm() {
    editingId = null;
    selectedMainFiles = [];
    selectedRelatedFiles = [];

    const defaults = {
      vbdiSoKyHieu: '',
      vbdiTrichYeu: '',
      vbdiHanXuLy: '',
      vbdiNgayVanBan: '',
      vbdiNoiDungTrinh: ''
    };

    Object.entries(defaults).forEach(([id, value]) => {
      const el = document.getElementById(id);
      if (el) el.value = value;
    });

    const donVi = document.getElementById('vbdiDonViSoaThan');
    const loai = document.getElementById('vbdiLoaiVB');
    const hinhThuc = document.getElementById('vbdiHinhThuc');
    const doKhan = document.getElementById('vbdiDoKhan');
    const lanhDao = document.getElementById('vbdiLanhDao');
    if (donVi) donVi.value = 'Phòng Kế Toán - Phạm Thị P';
    if (loai) loai.value = 'Hành chính';
    if (hinhThuc) hinhThuc.value = 'Công văn';
    if (doKhan) doKhan.value = 'Bình thường';
    if (lanhDao) lanhDao.value = '';

    const fileInput = document.getElementById('vbdiFile');
    const relatedInput = document.getElementById('vbdiFileLienQuan');
    if (fileInput) fileInput.value = '';
    if (relatedInput) relatedInput.value = '';

    renderFormFileList('vbdiFileList', selectedMainFiles, 'main');
    renderFormFileList('vbdiFileLienQuanList', selectedRelatedFiles, 'related');
    checkFormValidation();
  }

  function fillForm(doc) {
    editingId = doc.id;
    currentDocId = doc.id;
    selectedMainFiles = cloneFiles(doc.mainFiles || []);
    selectedRelatedFiles = cloneFiles(doc.relatedFiles || []);

    const values = {
      vbdiSoKyHieu: doc.soKyHieu || '',
      vbdiTrichYeu: doc.trichYeu || '',
      vbdiHanXuLy: toInputDate(doc.hanXuLy),
      vbdiNgayVanBan: toInputDate(doc.ngayVanBan),
      vbdiNoiDungTrinh: doc.noiDungTrinh || ''
    };

    Object.entries(values).forEach(([id, value]) => {
      const el = document.getElementById(id);
      if (el) el.value = value;
    });

    const donVi = document.getElementById('vbdiDonViSoaThan');
    const loai = document.getElementById('vbdiLoaiVB');
    const hinhThuc = document.getElementById('vbdiHinhThuc');
    const doKhan = document.getElementById('vbdiDoKhan');
    const lanhDao = document.getElementById('vbdiLanhDao');
    if (donVi) donVi.value = `${doc.donViSoaThan} - Phạm Thị P`;
    if (loai) loai.value = doc.loaiVanBan || 'Hành chính';
    if (hinhThuc) hinhThuc.value = doc.hinhThuc || 'Công văn';
    if (doKhan) doKhan.value = doc.doKhan === 'BÌNH THƯỜNG' ? 'Bình thường' : 'Khẩn';
    if (lanhDao) lanhDao.value = doc.lanhDao || '';

    renderFormFileList('vbdiFileList', selectedMainFiles, 'main');
    renderFormFileList('vbdiFileLienQuanList', selectedRelatedFiles, 'related');
    checkFormValidation();
  }

  function checkFormValidation() {
    const requiredIds = ['vbdiSoKyHieu', 'vbdiLoaiVB', 'vbdiHinhThuc', 'vbdiTrichYeu', 'vbdiNgayVanBan', 'vbdiDoKhan', 'vbdiLanhDao'];
    const isValid = requiredIds.every(id => document.getElementById(id)?.value.trim()) && selectedMainFiles.length > 0;
    const btnSave = document.getElementById('btnSaveVBDi');
    if (!btnSave) return;

    btnSave.disabled = !isValid;
    btnSave.style.cursor = isValid ? 'pointer' : 'not-allowed';
    btnSave.style.background = isValid ? 'var(--primary)' : '#94A3B8';
  }

  function renderTable() {
    const tbody = document.getElementById('vanBanDiBody');
    const paginationInfo = document.getElementById('paginationInfo');
    if (!tbody) return;

    const total = filteredData.length;
    const start = (currentPage - 1) * perPage;
    const end = Math.min(start + perPage, total);
    const pageData = filteredData.slice(start, end);

    if (paginationInfo) paginationInfo.textContent = `Hiển thị ${total} văn bản`;

    if (!pageData.length) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding:40px;">Không có văn bản phù hợp.</td></tr>`;
      const paginationBtns = document.getElementById('paginationBtns');
      if (paginationBtns) paginationBtns.innerHTML = '';
      return;
    }

    tbody.innerHTML = pageData.map((doc, index) => {
      const fileColor = doc.doKhan === 'KHẨN' ? '#EF4444' : '#EF4444';
      const displayStatus = getDisplayStatus(doc);
      return `
        <tr style="border-bottom: 1px solid var(--border-color);">
          <td class="text-center">${start + index + 1}</td>
          <td><a href="#" style="color:var(--primary);font-weight:700;text-decoration:none;" onclick="viewDetailVBDi(${doc.id}); return false;">${doc.soKyHieu}</a></td>
          <td style="color:var(--text-main);">${doc.trichYeu}</td>
          <td style="color:var(--text-main);">${doc.ngayVanBan}</td>
          <td style="color:var(--text-main);">${doc.donViSoaThan}</td>
          <td style="color:${fileColor};font-weight:700;">${doc.doKhan}</td>
          <td>${renderStatusBadge(displayStatus)}</td>
        </tr>
      `;
    }).join('');

    createPagination('paginationBtns', total, perPage, currentPage, page => {
      currentPage = page;
      renderTable();
    });
  }

  function applyFilters() {
    const keyword = (document.getElementById('searchKeyword')?.value || '').toLowerCase().trim();
    const donVi = document.getElementById('filterDonVi')?.value || '';
    const loai = document.getElementById('filterLoaiVB')?.value || '';
    const hinhThuc = document.getElementById('filterHinhThuc')?.value || '';
    const doKhan = document.getElementById('filterDoKhan')?.value || '';

    filteredData = getRoleDocs().filter(doc => {
      const displayStatus = getDisplayStatus(doc);
      if (!displayStatus) return false;
      if (activeStatus !== 'all' && displayStatus !== activeStatus) return false;
      if (keyword && !doc.soKyHieu.toLowerCase().includes(keyword) && !doc.trichYeu.toLowerCase().includes(keyword)) return false;
      if (donVi && doc.donViSoaThan !== donVi) return false;
      if (loai && doc.loaiVanBan !== loai) return false;
      if (hinhThuc && doc.hinhThuc !== hinhThuc) return false;
      if (doKhan && doc.doKhan !== doKhan.toUpperCase()) return false;
      return true;
    });

    currentPage = 1;
    renderTable();
  }

  function buildDetailHtml(doc) {
    const displayStatus = getDisplayStatus(doc);
    const isLeader = user.role === 'lanhdao';
    const isClerk = user.role === 'vanthu';
    const doKhanStyle = doc.doKhan === 'KHẨN'
      ? 'color:#EF4444;font-weight:700;'
      : 'color:var(--text-main);font-weight:500;';

    const actionButtons = isLeader
      ? getLeaderActionButtons(doc)
      : isClerk
        ? getVanThuActionButtons(doc, displayStatus)
        : [
            `
              <button class="btn btn-primary" style="padding:8px 16px;" onclick="showToast('Đã lưu hồ sơ', 'success')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="white" style="margin-right:6px;vertical-align:middle;"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>Lưu hồ sơ
              </button>
            `,
            `
              <button class="btn btn-primary" style="padding:8px 16px;" onclick="editVBDiCurrent()">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="white" style="margin-right:6px;vertical-align:middle;"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25z"/></svg>Chỉnh sửa
              </button>
            `,
            doc.trangThai !== 'hoan-tra'
              ? `
                <button class="btn btn-danger" style="padding:8px 16px;" onclick="deleteCurrentVBDi()">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="white" style="margin-right:6px;vertical-align:middle;"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>Xóa văn bản
                </button>
              `
              : ''
          ].join('');

    let extraInfo = '';
    if (isClerk && displayStatus === 'cho-ban-hanh') {
      extraInfo = `
        <div class="detail-label" style="margin-top:16px;">Ngày duyệt:</div>
        <div class="detail-value">${doc.ngayDuyet || doc.ngayXuLy || DEFAULT_APPROVE_DATE}</div>
      `;
    } else if (isClerk && displayStatus === 'da-ban-hanh') {
      extraInfo = `
        <div class="detail-label" style="margin-top:16px;">Ngày duyệt:</div>
        <div class="detail-value">${doc.ngayDuyet || doc.ngayXuLy || DEFAULT_APPROVE_DATE}</div>
        <div class="detail-label" style="margin-top:16px;">Người ban hành:</div>
        <div class="detail-value">${doc.nguoiBanHanh || user.name || 'Trần Thị Thúy Na'}</div>
        <div class="detail-label" style="margin-top:16px;">Ngày ban hành:</div>
        <div class="detail-value">${doc.ngayBanHanh || DEFAULT_PUBLISH_DATE}</div>
      `;
    } else if (doc.trangThai === 'hoan-tra') {
      extraInfo = `
        <div class="detail-label" style="margin-top:16px;">Ngày hoàn trả:</div>
        <div class="detail-value">${doc.ngayHoanTra || '—'}</div>
        <div class="detail-label" style="margin-top:16px;">Hạn xử lý hoàn trả:</div>
        <div class="detail-value">${doc.hanXuLyHoanTra || '—'}</div>
      `;
    } else if (doc.trangThai === 'da-xu-ly') {
      extraInfo = `
        <div class="detail-label" style="margin-top:16px;">Ngày xử lý:</div>
        <div class="detail-value">${doc.ngayXuLy || '—'}</div>
      `;
    } else if (doc.trangThai === 'da-phat-hanh') {
      extraInfo = `
        <div class="detail-label" style="margin-top:16px;">Ngày phát hành:</div>
        <div class="detail-value">${doc.ngayPhatHanh || '—'}</div>
      `;
    }

    const mainFile = doc.mainFiles?.[0] || { name: 'CV_1735_CT_CS.pdf' };
    const mainFileType = getFileTypeLabel(mainFile.name);

    const relatedFilesHtml = (doc.relatedFiles || []).map(file => {
      const fileType = getFileTypeLabel(file.name);
      return `
        <div style="display:flex; align-items:center; gap:8px; padding:6px 12px; border:1px solid var(--border-color); border-radius:4px; background:#F8FAFC;">
          <span style="color:${fileType.color}; font-weight:bold; font-size:10px;">${fileType.label}</span>
          <div>
            <div style="font-size:13px; font-weight:600;">${file.name}</div>
            <div style="font-size:11px; color:var(--text-muted);">${getFileTypeText(file.name)}</div>
          </div>
        </div>
      `;
    }).join('');

    const returnBox = !isClerk && doc.trangThai === 'hoan-tra' ? `
      <div class="detail-box detail-box-return" style="background:#FEF2F2; margin-top:24px;">
        <div class="detail-box-title" style="color:#BE123C;">Ý kiến xử lý / hoàn trả</div>
        <div style="color:var(--text-main); font-size:14px;">${doc.yKienHoanTra || '—'}</div>
      </div>
    ` : '';

    return `
      <div class="card" style="padding:24px 32px; border: 1px solid var(--border-color); box-shadow: none; margin-bottom: 24px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:16px;">
          <div class="filter-title" style="border-left: 4px solid var(--primary); padding-left: 12px; font-size: 16px; font-weight: 700; color: var(--primary); text-transform: uppercase;">THÔNG TIN VĂN BẢN ĐI</div>
          <div style="display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end;">${actionButtons}</div>
        </div>
        <hr style="border:none; border-top:1px solid var(--border-color); margin:16px 0 24px 0;">

        <div class="detail-grid">
          <div>
            <div class="detail-label">Trích yếu</div>
            <div class="detail-value">${doc.trichYeu}</div>

            <div class="detail-label" style="margin-top:16px;">Đơn vị soạn thảo:</div>
            <div class="detail-value">${doc.donViSoaThan} - ${doc.nguoiSoan || 'Phạm Thị Phương'}</div>

            <div class="detail-label" style="margin-top:16px;">Hình thức:</div>
            <div class="detail-value">${doc.hinhThuc}</div>

            <div class="detail-label" style="margin-top:16px;">Độ khẩn:</div>
            <div class="detail-value" style="${doKhanStyle}">${doc.doKhan === 'BÌNH THƯỜNG' ? 'Bình thường' : doc.doKhan}</div>
          </div>

          <div>
            <div class="detail-label">Số ký hiệu:</div>
            <div class="detail-value">${doc.soKyHieu}</div>

            <div class="detail-label" style="margin-top:16px;">Loại văn bản:</div>
            <div class="detail-value">${doc.loaiVanBan}</div>

            <div class="detail-label" style="margin-top:16px;">Ngày văn bản:</div>
            <div class="detail-value">${doc.ngayVanBan}</div>

            <div class="detail-label" style="margin-top:16px;">Hạn xử lý:</div>
            <div class="detail-value">${doc.hanXuLy}</div>
          </div>

          <div>
            <div class="detail-label">Lãnh đạo xử lý:</div>
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:16px;">
              <span class="detail-value">${doc.lanhDao}</span>
              ${renderStatusBadge(displayStatus)}
            </div>
            ${extraInfo}
          </div>
        </div>

        <div class="detail-box">
          <div class="detail-box-title">Nội dung trình lãnh đạo:</div>
          <div style="color:var(--text-main); font-size:14px;">${doc.noiDungTrinh || '—'}</div>
        </div>
        ${returnBox}
      </div>

      ${renderPublishInfoCard(doc)}

      <div class="card" style="padding:24px 32px; border: 1px solid var(--border-color); box-shadow: none;">
        <div class="filter-title" style="border-left: 4px solid var(--primary); padding-left: 12px; font-size: 16px; font-weight: 700; color: var(--primary); text-transform: uppercase; margin-bottom: 24px;">DANH SÁCH VĂN BẢN</div>

        <div style="font-size:14px; color:var(--text-secondary); margin-bottom:8px;">File đính kèm:</div>
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:24px;">
          <div style="border: 1px solid var(--border-color); padding: 8px 16px; border-radius: 4px; display: inline-flex; align-items: center; gap: 12px; background: #fff;">
            <span style="color:${mainFileType.color}; font-weight:bold; font-size:12px;">${mainFileType.label}</span>
            <div>
              <div style="font-weight:600; font-size:13px; color:var(--text-main);">${mainFile.name}</div>
              <div style="font-size:11px; color:var(--text-muted);">${getFileTypeText(mainFile.name)}</div>
            </div>
          </div>
        </div>

        <div style="font-size:14px; color:var(--text-secondary); margin-bottom:8px;">Xem trước</div>
        <div style="background:#3f3f46; border-radius:4px; padding:12px; min-height:500px; display:flex; flex-direction:column; margin-bottom:24px;">
          <div style="display:flex; justify-content:space-between; color:#fff; font-size:12px; margin-bottom:12px; padding:0 12px;">
            <span>${mainFile.name}</span>
            <span style="color:#a1a1aa; letter-spacing:2px;">1 / 1 &nbsp;&nbsp;|&nbsp;&nbsp; – &nbsp; + &nbsp;&nbsp;|&nbsp;&nbsp; 🖨️ &nbsp; 📥</span>
          </div>
          <div style="flex:1; background:#fff; margin:0 auto; padding:40px; width:100%; max-width:600px; overflow:hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.3); font-size:13px; line-height:1.5; color:#333;">
            <div style="display:flex; justify-content:space-between; margin-bottom:32px;">
              <div style="text-align:center; font-weight:bold; font-size:13px;">BỘ TÀI CHÍNH<br><span style="text-decoration:underline;">CỤC THUẾ</span><br><br><span style="font-weight:normal; font-size:12px;">Số: 1735/CT-CS</span></div>
              <div style="text-align:center; font-weight:bold; font-size:14px;">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM<br><span style="text-decoration:underline; font-size:13px;">Độc lập - Tự do - Hạnh phúc</span><br><br><span style="font-style:italic; font-weight:normal; font-size:12px;">Hà Nội, ngày 13 tháng 6 năm 2025</span></div>
            </div>
            <div style="margin-bottom:24px; font-weight:500;">V/v giới thiệu nội dung mới tại Nghị định số 117/2025/NĐ-CP của Chính phủ...</div>
            <div style="text-align:center; font-weight:bold; margin-bottom:24px;">Kính gửi: Các Chi cục Thuế khu vực.</div>
            <div>Ngày 09/6/2025, Chính phủ đã ban hành Nghị định số 117/2025/NĐ-CP quy định về quản lý thuế đối với hoạt động kinh doanh trên nền tảng thương mại điện tử...</div>
          </div>
        </div>

        <div style="font-size:14px; color:var(--text-secondary); margin-bottom:8px;">Tài liệu liên quan:</div>
        <div style="display:flex; flex-direction:column; gap:8px;">${relatedFilesHtml}</div>
      </div>
    `;
  }

  document.querySelectorAll('.tab-filter-btn').forEach(button => {
    button.addEventListener('click', function () {
      document.querySelectorAll('.tab-filter-btn').forEach(btn => btn.classList.remove('active'));
      this.classList.add('active');
      activeStatus = this.dataset.status;
      applyFilters();
    });
  });

  ['searchKeyword', 'filterDonVi', 'filterLoaiVB', 'filterHinhThuc', 'filterDoKhan'].forEach(id => {
    const field = document.getElementById(id);
    if (!field) return;
    field.addEventListener(id === 'searchKeyword' ? 'input' : 'change', applyFilters);
  });

  ['vbdiSoKyHieu', 'vbdiLoaiVB', 'vbdiHinhThuc', 'vbdiTrichYeu', 'vbdiNgayVanBan', 'vbdiDoKhan', 'vbdiLanhDao'].forEach(id => {
    const field = document.getElementById(id);
    if (!field) return;
    field.addEventListener('input', checkFormValidation);
    field.addEventListener('change', checkFormValidation);
  });

  document.getElementById('vbdiFile')?.addEventListener('change', function () {
    const file = this.files?.[0];
    if (!file) return;
    selectedMainFiles = [{ name: file.name }];
    renderFormFileList('vbdiFileList', selectedMainFiles, 'main');
    this.value = '';
    checkFormValidation();
  });

  document.getElementById('vbdiFileLienQuan')?.addEventListener('change', function () {
    const files = Array.from(this.files || []).map(file => ({ name: file.name }));
    if (!files.length) return;
    selectedRelatedFiles = [...selectedRelatedFiles, ...files];
    renderFormFileList('vbdiFileLienQuanList', selectedRelatedFiles, 'related');
    this.value = '';
  });

  document.getElementById('btnAddVanBanDi')?.addEventListener('click', () => {
    resetForm();
    showVBDiFormView(false);
  });

  document.getElementById('btnSaveVBDi')?.addEventListener('click', () => {
    const btnSave = document.getElementById('btnSaveVBDi');
    if (!btnSave || btnSave.disabled) return;

    const payload = {
      soKyHieu: document.getElementById('vbdiSoKyHieu')?.value.trim() || '',
      trichYeu: document.getElementById('vbdiTrichYeu')?.value.trim() || '',
      ngayVanBan: fromInputDate(document.getElementById('vbdiNgayVanBan')?.value || ''),
      donViSoaThan: (document.getElementById('vbdiDonViSoaThan')?.value || '').split(' - ')[0],
      doKhan: (document.getElementById('vbdiDoKhan')?.value || '').toUpperCase(),
      hinhThuc: document.getElementById('vbdiHinhThuc')?.value || '',
      loaiVanBan: document.getElementById('vbdiLoaiVB')?.value || '',
      hanXuLy: fromInputDate(document.getElementById('vbdiHanXuLy')?.value || ''),
      lanhDao: document.getElementById('vbdiLanhDao')?.value || '',
      noiDungTrinh: document.getElementById('vbdiNoiDungTrinh')?.value.trim() || '',
      nguoiSoan: 'Phạm Thị Phương',
      mainFiles: cloneFiles(selectedMainFiles),
      relatedFiles: cloneFiles(selectedRelatedFiles)
    };

    if (editingId) {
      const doc = VAN_BAN_DI.find(item => item.id === editingId);
      if (doc) {
        Object.assign(doc, payload);
        showToast('Cập nhật văn bản đi thành công!', 'success');
        applyFilters();
        viewDetailVBDi(doc.id);
      }
      return;
    }

    VAN_BAN_DI.unshift({
      id: Date.now(),
      trangThai: 'cho-xu-ly',
      ...payload
    });
    showToast('Đã lưu văn bản đi!', 'success');
    resetForm();
    showVBDiListView();
  });

  window.showVBDiListView = showVBDiListView;
  window.showVBDiFormView = showVBDiFormView;

  window.assignVBDiTask = function (id) {
    const doc = VAN_BAN_DI.find(item => item.id === id);
    if (!doc) return;
    showToast(`Chuyển sang giao việc cho văn bản ${doc.soKyHieu}.`, 'info');
    window.location.href = 'giao-viec.html';
  };

  window.openReturnLeaderVBDi = function (id) {
    const doc = VAN_BAN_DI.find(item => item.id === id);
    if (!doc) return;
    currentDocId = doc.id;
    populateLeaderApproveModal(doc);
    const modal = document.getElementById('modalHoanTraVBDi');
    if (modal) modal.style.display = 'flex';
    const btn = document.getElementById('btnHoanTraSubmitDi');
    if (btn) {
      btn.disabled = true;
      btn.style.background = '#94A3B8';
      btn.style.cursor = 'not-allowed';
    }
  };

  window.openApproveLeaderVBDi = function (id) {
    const doc = VAN_BAN_DI.find(item => item.id === id);
    if (!doc) return;
    currentDocId = doc.id;
    populateLeaderApproveModal(doc);
    const modal = document.getElementById('modalPheDuyetVBDi');
    if (modal) modal.style.display = 'flex';
    const btn = document.getElementById('btnPheDuyetSubmitDi');
    if (btn) {
      btn.disabled = true;
      btn.style.background = '#94A3B8';
      btn.style.cursor = 'not-allowed';
    }
  };

  window.removeVBDiFile = function (kind, index) {
    if (kind === 'main') {
      selectedMainFiles.splice(index, 1);
      renderFormFileList('vbdiFileList', selectedMainFiles, 'main');
      checkFormValidation();
      return;
    }

    selectedRelatedFiles.splice(index, 1);
    renderFormFileList('vbdiFileLienQuanList', selectedRelatedFiles, 'related');
  };

  window.viewDetailVBDi = function (id) {
    const doc = VAN_BAN_DI.find(item => item.id === id);
    if (!doc) return;
    currentDocId = doc.id;
    detailView.innerHTML = buildDetailHtml(doc);
    showVBDiDetailView();
  };

  window.editVBDiCurrent = function () {
    if (!currentDocId) return;
    const doc = VAN_BAN_DI.find(item => item.id === currentDocId);
    if (!doc) return;
    fillForm(doc);
    showVBDiFormView(true);
  };

  window.deleteCurrentVBDi = function () {
    if (!currentDocId) return;
    showConfirm('Xác nhận xóa', 'Xóa văn bản đi này?', () => {
      const index = VAN_BAN_DI.findIndex(item => item.id === currentDocId);
      if (index !== -1) VAN_BAN_DI.splice(index, 1);
      currentDocId = null;
      showToast('Đã xóa văn bản đi.', 'success');
      applyFilters();
      showVBDiListView();
    });
  };

  const returnReason = document.getElementById('txtHoanTraLyDoDi');
  returnReason?.addEventListener('input', function () {
    const btn = document.getElementById('btnHoanTraSubmitDi');
    if (!btn) return;
    const valid = !!this.value.trim();
    btn.disabled = !valid;
    btn.style.background = valid ? 'var(--primary)' : '#94A3B8';
    btn.style.cursor = valid ? 'pointer' : 'not-allowed';
  });

  document.getElementById('btnHoanTraSubmitDi')?.addEventListener('click', function () {
    if (this.disabled || !currentDocId) return;
    const doc = VAN_BAN_DI.find(item => item.id === currentDocId);
    if (!doc) return;

    const reason = document.getElementById('txtHoanTraLyDoDi')?.value.trim() || '';
    doc.trangThai = 'hoan-tra';
    doc.trangThaiVanThu = null;
    doc.yKienHoanTra = reason;
    doc.ngayHoanTra = '12/02/2026';
    doc.hanXuLyHoanTra = '20/02/2026';
    doc.nguoiBanHanh = '';
    doc.ngayBanHanh = '';
    doc.noiBoIds = [];
    doc.ngoaiIds = [];
    doc.donViPhatHanh = [];
    document.getElementById('modalHoanTraVBDi').style.display = 'none';
    showToast('Đã hoàn trả văn bản cho chuyên viên.', 'success');
    applyFilters();
    viewDetailVBDi(doc.id);
  });

  function validateApproveLeaderModal() {
    const btn = document.getElementById('btnPheDuyetSubmitDi');
    if (!btn) return;
    const selected = document.querySelector('input[name="vanthuRadio"]:checked');
    const valid = !!selected;
    btn.disabled = !valid;
    btn.style.background = valid ? 'var(--primary)' : '#94A3B8';
    btn.style.cursor = valid ? 'pointer' : 'not-allowed';
  }

  document.querySelectorAll('input[name="vanthuRadio"]').forEach(input => {
    input.addEventListener('change', validateApproveLeaderModal);
  });

  document.getElementById('btnPheDuyetSubmitDi')?.addEventListener('click', function () {
    if (this.disabled || !currentDocId) return;
    const doc = VAN_BAN_DI.find(item => item.id === currentDocId);
    if (!doc) return;

    const vanThu = document.querySelector('input[name="vanthuRadio"]:checked')?.parentElement?.querySelector('span')?.textContent || 'Lê Văn C (Văn thư)';
    doc.trangThai = 'da-xu-ly';
    doc.ngayXuLy = '10/02/2026';
    doc.trangThaiVanThu = 'cho-ban-hanh';
    doc.ngayDuyet = DEFAULT_APPROVE_DATE;
    doc.vanThu = vanThu;
    doc.ghiChuChiDao = document.getElementById('txtPheDuyetGhiChu')?.value.trim() || '';
    document.getElementById('modalPheDuyetVBDi').style.display = 'none';
    showToast('Đã phê duyệt văn bản đi.', 'success');
    applyFilters();
    viewDetailVBDi(doc.id);
  });

  function updateExternalSaveButton() {
    const btn = document.getElementById('btnSubmitAddNgoai');
    if (!btn) return;
    const valid = ['addNgoaiTen', 'addNgoaiDaiDien', 'addNgoaiSDT', 'addNgoaiEmail']
      .every(id => document.getElementById(id)?.value.trim());
    btn.disabled = !valid;
    btn.style.background = valid ? 'var(--primary)' : '#94A3B8';
    btn.style.cursor = valid ? 'pointer' : 'not-allowed';
  }

  function updateSelectedCount(type) {
    if (type === 'noibo' && countNoiBo) countNoiBo.textContent = String(selectedInternalIds.length);
    if (type === 'ngoai' && countNgoai) countNgoai.textContent = String(selectedExternalIds.length);
  }

  function renderInternalUnits() {
    if (!tbodyNoiBo) return;
    const keyword = (searchNoiBoInput?.value || '').trim().toLowerCase();
    const rows = INTERNAL_UNITS.filter(unit => unit.name.toLowerCase().includes(keyword));

    tbodyNoiBo.innerHTML = rows.map(unit => `
      <tr style="background:#F8FAFC; border-bottom:1px solid var(--border-color);">
        <td style="padding:16px; width:40px;"><input type="checkbox" data-noibo-id="${unit.id}" style="width:16px; height:16px; cursor:pointer;" ${selectedInternalIds.includes(unit.id) ? 'checked' : ''}></td>
        <td style="padding:16px; font-size:15px; font-weight:600; color:var(--text-main);">${unit.name} (${String(unit.count).padStart(2, '0')})</td>
      </tr>
    `).join('');

    const visibleIds = rows.map(unit => unit.id);
    if (chkAllNoiBo) chkAllNoiBo.checked = !!visibleIds.length && visibleIds.every(id => selectedInternalIds.includes(id));
    updateSelectedCount('noibo');
  }

  function renderExternalUnits() {
    if (!tbodyNgoai) return;
    const keyword = (searchNgoaiInput?.value || '').trim().toLowerCase();
    const rows = externalUnits.filter(unit =>
      [unit.name, unit.representative, unit.phone, unit.email].some(value => value.toLowerCase().includes(keyword))
    );

    tbodyNgoai.innerHTML = rows.map(unit => `
      <tr style="background:#F8FAFC; border-bottom:1px solid var(--border-color);">
        <td style="padding:16px; width:40px;"><input type="checkbox" data-ngoai-id="${unit.id}" style="width:16px; height:16px; cursor:pointer;" ${selectedExternalIds.includes(unit.id) ? 'checked' : ''}></td>
        <td style="padding:16px; font-size:15px; font-weight:600; color:var(--text-main);">${unit.name}</td>
        <td style="padding:16px; font-size:15px; font-weight:600; color:var(--text-main);">${unit.representative}</td>
        <td style="padding:16px; font-size:15px; font-weight:600; color:var(--text-main);">${unit.phone}</td>
        <td style="padding:16px; font-size:15px; font-weight:600; color:var(--text-main);">${unit.email}</td>
        <td style="padding:16px; text-align:center;">
          <button type="button" onclick="editOutsideUnit('${unit.id}')" style="border:none;background:none;color:#64748B;cursor:pointer;font-size:16px;margin-right:12px;">✎</button>
          <button type="button" onclick="deleteOutsideUnit('${unit.id}')" style="border:none;background:none;color:#64748B;cursor:pointer;font-size:16px;">🗑</button>
        </td>
      </tr>
    `).join('');

    const visibleIds = rows.map(unit => unit.id);
    if (chkAllNgoai) chkAllNgoai.checked = !!visibleIds.length && visibleIds.every(id => selectedExternalIds.includes(id));
    updateSelectedCount('ngoai');
  }

  function openPublishModal(id, type) {
    const doc = VAN_BAN_DI.find(item => item.id === id);
    if (!doc) return;

    currentDocId = doc.id;
    selectedInternalIds = [...(doc.noiBoIds || [])];
    selectedExternalIds = [...(doc.ngoaiIds || [])];

    if (type === 'ngoai') {
      renderExternalUnits();
      if (externalModal) externalModal.style.display = 'flex';
      if (publishTargetTypeNgoai) publishTargetTypeNgoai.value = 'ngoai';
      return;
    }

    renderInternalUnits();
    if (internalModal) internalModal.style.display = 'flex';
    if (publishTargetTypeNoiBo) publishTargetTypeNoiBo.value = 'noibo';
  }

  function persistPublishSelection() {
    const doc = getCurrentDoc();
    if (!doc) return false;

    const internalNames = INTERNAL_UNITS
      .filter(unit => selectedInternalIds.includes(unit.id))
      .map(unit => unit.name);
    const externalNames = externalUnits
      .filter(unit => selectedExternalIds.includes(unit.id))
      .map(unit => unit.name);
    const publishedUnits = [...internalNames, ...externalNames];

    if (!publishedUnits.length) {
      showToast('Chọn ít nhất một đơn vị phát hành.', 'error');
      return false;
    }

    doc.noiBoIds = [...selectedInternalIds];
    doc.ngoaiIds = [...selectedExternalIds];
    doc.donViPhatHanh = publishedUnits;
    doc.trangThai = 'da-phat-hanh';
    doc.trangThaiVanThu = 'da-ban-hanh';
    doc.ngayDuyet = doc.ngayDuyet || DEFAULT_APPROVE_DATE;
    doc.nguoiBanHanh = user.name || 'Trần Thị Thúy Na';
    doc.ngayBanHanh = DEFAULT_PUBLISH_DATE;
    return true;
  }

  function resetOutsideUnitForm() {
    editingExternalId = null;
    ['addNgoaiTen', 'addNgoaiDaiDien', 'addNgoaiSDT', 'addNgoaiEmail'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });
    updateExternalSaveButton();
  }

  window.openChonDonViNoiBo = function (id = currentDocId) {
    if (user.role !== 'vanthu') {
      showToast('Chức năng này dành cho luồng văn thư.', 'info');
      return;
    }
    closeModalById('modalChonDonViNgoai');
    openPublishModal(id, 'noibo');
  };

  window.openChonDonViNgoai = function (id = currentDocId) {
    if (user.role !== 'vanthu') {
      showToast('Chức năng này dành cho luồng văn thư.', 'info');
      return;
    }
    closeModalById('modalChonDonViNoiBo');
    openPublishModal(id, 'ngoai');
  };

  window.saveChoosenDonViNoiBo = function () {
    if (!persistPublishSelection()) return;
    closeModalById('modalChonDonViNoiBo');
    showToast('Đã cập nhật phát hành nội bộ.', 'success');
    applyFilters();
    if (currentDocId) viewDetailVBDi(currentDocId);
  };

  window.saveChoosenDonViNgoai = function () {
    if (!persistPublishSelection()) return;
    closeModalById('modalChonDonViNgoai');
    showToast('Đã cập nhật phát hành văn bản.', 'success');
    applyFilters();
    if (currentDocId) viewDetailVBDi(currentDocId);
  };

  window.openModalThemDonViNgoai = function () {
    resetOutsideUnitForm();
    if (addExternalModal) addExternalModal.style.display = 'flex';
  };

  window.editOutsideUnit = function (id) {
    const unit = externalUnits.find(item => item.id === id);
    if (!unit) return;
    editingExternalId = unit.id;
    document.getElementById('addNgoaiTen').value = unit.name;
    document.getElementById('addNgoaiDaiDien').value = unit.representative;
    document.getElementById('addNgoaiSDT').value = unit.phone;
    document.getElementById('addNgoaiEmail').value = unit.email;
    updateExternalSaveButton();
    if (addExternalModal) addExternalModal.style.display = 'flex';
  };

  window.deleteOutsideUnit = function (id) {
    showConfirm('Xác nhận xóa', 'Xóa đơn vị ngoài này?', () => {
      externalUnits = externalUnits.filter(item => item.id !== id);
      selectedExternalIds = selectedExternalIds.filter(item => item !== id);
      renderExternalUnits();
      showToast('Đã xóa đơn vị ngoài.', 'success');
    });
  };

  searchNoiBoInput?.addEventListener('input', renderInternalUnits);
  searchNgoaiInput?.addEventListener('input', renderExternalUnits);

  publishTargetTypeNoiBo?.addEventListener('change', function () {
    if (this.value === 'ngoai') window.openChonDonViNgoai(currentDocId);
  });

  publishTargetTypeNgoai?.addEventListener('change', function () {
    if (this.value === 'noibo') window.openChonDonViNoiBo(currentDocId);
  });

  chkAllNoiBo?.addEventListener('change', function () {
    const keyword = (searchNoiBoInput?.value || '').trim().toLowerCase();
    const visibleIds = INTERNAL_UNITS
      .filter(unit => unit.name.toLowerCase().includes(keyword))
      .map(unit => unit.id);

    if (this.checked) {
      selectedInternalIds = [...new Set([...selectedInternalIds, ...visibleIds])];
    } else {
      selectedInternalIds = selectedInternalIds.filter(id => !visibleIds.includes(id));
    }
    renderInternalUnits();
  });

  chkAllNgoai?.addEventListener('change', function () {
    const keyword = (searchNgoaiInput?.value || '').trim().toLowerCase();
    const visibleIds = externalUnits
      .filter(unit => [unit.name, unit.representative, unit.phone, unit.email].some(value => value.toLowerCase().includes(keyword)))
      .map(unit => unit.id);

    if (this.checked) {
      selectedExternalIds = [...new Set([...selectedExternalIds, ...visibleIds])];
    } else {
      selectedExternalIds = selectedExternalIds.filter(id => !visibleIds.includes(id));
    }
    renderExternalUnits();
  });

  tbodyNoiBo?.addEventListener('change', function (event) {
    const checkbox = event.target.closest('input[data-noibo-id]');
    if (!checkbox) return;
    const id = checkbox.dataset.noiboId;
    if (checkbox.checked) {
      selectedInternalIds = [...new Set([...selectedInternalIds, id])];
    } else {
      selectedInternalIds = selectedInternalIds.filter(item => item !== id);
    }
    renderInternalUnits();
  });

  tbodyNgoai?.addEventListener('change', function (event) {
    const checkbox = event.target.closest('input[data-ngoai-id]');
    if (!checkbox) return;
    const id = checkbox.dataset.ngoaiId;
    if (checkbox.checked) {
      selectedExternalIds = [...new Set([...selectedExternalIds, id])];
    } else {
      selectedExternalIds = selectedExternalIds.filter(item => item !== id);
    }
    renderExternalUnits();
  });

  ['addNgoaiTen', 'addNgoaiDaiDien', 'addNgoaiSDT', 'addNgoaiEmail'].forEach(id => {
    const field = document.getElementById(id);
    field?.addEventListener('input', updateExternalSaveButton);
  });

  document.getElementById('btnSubmitAddNgoai')?.addEventListener('click', function () {
    if (this.disabled) return;

    const payload = {
      name: document.getElementById('addNgoaiTen')?.value.trim() || '',
      representative: document.getElementById('addNgoaiDaiDien')?.value.trim() || '',
      phone: document.getElementById('addNgoaiSDT')?.value.trim() || '',
      email: document.getElementById('addNgoaiEmail')?.value.trim() || ''
    };

    if (editingExternalId) {
      const unit = externalUnits.find(item => item.id === editingExternalId);
      if (unit) Object.assign(unit, payload);
      showToast('Đã cập nhật đơn vị ngoài.', 'success');
    } else {
      externalUnits.unshift({
        id: `outside-${Date.now()}`,
        ...payload
      });
      showToast('Đã thêm đơn vị ngoài.', 'success');
    }

    closeModalById('modalThemDonViNgoai');
    renderExternalUnits();
    resetOutsideUnitForm();
  });

  configureRoleTabs();
  setBreadcrumb('list');
  renderFormFileList('vbdiFileList', selectedMainFiles, 'main');
  renderFormFileList('vbdiFileLienQuanList', selectedRelatedFiles, 'related');
  renderInternalUnits();
  renderExternalUnits();
  updateExternalSaveButton();
  applyFilters();
});
