/**
 * vanbanden.js - Quản lý Văn bản đến
 */
document.addEventListener('DOMContentLoaded', function () {
  const user = requireAuth();
  if (!user) return;

  const pageProfiles = {
    vanthu: { name: 'Ngô Đăng Hà', roleLabel: 'Văn thư', avatar: 'NH' },
    lanhdao: { name: 'Phan Thanh Thảo', roleLabel: 'Giám đốc phòng Hành chính', avatar: 'PT' },
    chuyenvien: { name: 'Phạm Thị Phương', roleLabel: 'Chuyên viên', avatar: 'PP' }
  };

  const statusMeta = {
    'cho-xu-ly': { label: 'Chờ xử lý', className: 'badge-cho-xu-ly' },
    'da-xu-ly': { label: 'Đã xử lý', className: 'badge-da-xu-ly' },
    'hoan-tra': { label: 'Hoàn trả', className: 'badge-hoan-tra' },
    'xem-de-biet': { label: 'Xem để biết', className: 'badge-xem-de-biet' }
  };

  const leaderOptions = [
    { id: 'ld1', name: 'Phan Thanh Thảo', role: 'Giám đốc phòng Hành chính', phone: '0913.256.768', email: 'thao.pt@atax.vn' },
    { id: 'ld2', name: 'Ngô Văn Hà', role: 'Phó giám đốc điều hành', phone: '0914.135.555', email: 'hanv@atax.vn' },
    { id: 'ld3', name: 'Trần Thị Thúy Na', role: 'Trưởng bộ phận văn thư', phone: '0941.223.456', email: 'na.tt@atax.vn' }
  ];

  const staffGroups = [
    {
      id: 'pb1',
      name: 'Phòng Ban Kế Toán',
      staffs: [
        { id: 'nv1', name: 'Nguyễn Hữu Quốc', role: 'Kế toán trưởng', phone: '0913.256.768', email: 'quocnh@vnpt.vn' },
        { id: 'nv2', name: 'Trần Tấn Tú', role: 'Kế toán viên', phone: '0914.135.555', email: 'tutt@vnpt.vn' },
        { id: 'nv3', name: 'Hà Phước Anh', role: 'Kế toán tổng hợp', phone: '0941.223.456', email: 'anhhp@vnpt.vn' },
        { id: 'nv4', name: 'Lê Thị Mai', role: 'Kế toán viên', phone: '0888.123.999', email: 'maitl@vnpt.vn' }
      ]
    },
    {
      id: 'pb2',
      name: 'Phòng Nhân Sự',
      staffs: [
        { id: 'nv5', name: 'Nguyễn Văn An', role: 'Trưởng phòng', phone: '0901.111.111', email: 'an.nv@vnpt.vn' },
        { id: 'nv6', name: 'Trần Thị Bình', role: 'Chuyên viên', phone: '0902.222.222', email: 'binhtt@vnpt.vn' },
        { id: 'nv7', name: 'Lê Văn Cường', role: 'Chuyên viên', phone: '0903.333.333', email: 'cuonglv@vnpt.vn' }
      ]
    },
    {
      id: 'pb3',
      name: 'Trung Tâm Công Nghệ Thông Tin',
      staffs: [
        { id: 'nv8', name: 'Phạm Minh Dũng', role: 'Giám đốc trung tâm', phone: '0904.444.444', email: 'dungpm@vnpt.vn' },
        { id: 'nv9', name: 'Hoàng Thu Hà', role: 'Lập trình viên', phone: '0905.555.555', email: 'haht@vnpt.vn' },
        { id: 'nv10', name: 'Vũ Quốc Khánh', role: 'Phân tích hệ thống', phone: '0906.666.666', email: 'khanhvq@vnpt.vn' },
        { id: 'nv11', name: 'Đinh Thị Giang', role: 'Kiểm thử viên', phone: '0907.777.777', email: 'giangdt@vnpt.vn' },
        { id: 'nv12', name: 'Ngô Thế Hùng', role: 'Quản trị hạ tầng', phone: '0908.888.888', email: 'hungnt@vnpt.vn' }
      ]
    }
  ];

  const initialDocuments = [
    {
      id: 1,
      soKyHieu: '123/UBND',
      donViBanHanh: 'UBND Thành phố',
      trichYeu: 'Về việc triển khai kế hoạch năm 2024',
      loaiVanBan: 'Quyết định',
      hinhThuc: 'Công văn',
      ngayVanBan: '2026-02-03',
      ngayDen: '2026-02-04',
      hanXuLy: '2026-02-09',
      doMat: 'Bình thường',
      doKhan: 'Bình thường',
      trangThai: 'cho-xu-ly',
      nguoiGui: 'Ngô Đăng Hà',
      lanhDaoTiepNhan: 'Phan Thanh Thảo',
      nguoiVanThu: 'Nguyễn Hữu Quốc',
      noiDungTrinh: 'Kính trình lãnh đạo xem xét.',
      yKienHoanTra: '',
      specialistIds: ['nv1', 'nv2', 'nv3'],
      specialistNames: ['Nguyễn Hữu Quốc', 'Trần Tấn Tú', 'Hà Phước Anh'],
      mainFile: { name: 'CV_1735_CT_CS.pdf' },
      relatedFiles: [{ name: 'CV_1735_CT_CS.docx' }, { name: 'CV_1735_CT_CS.pdf' }],
      hoSoId: ''
    },
    {
      id: 2,
      soKyHieu: '123/KT',
      donViBanHanh: 'UBND Thành phố',
      trichYeu: 'V/v sửa đổi hệ thống kiểm toán 2025',
      loaiVanBan: 'Công văn',
      hinhThuc: 'Công văn',
      ngayVanBan: '2026-02-03',
      ngayDen: '2026-02-04',
      hanXuLy: '2026-02-09',
      doMat: 'Mật',
      doKhan: 'Khẩn',
      trangThai: 'da-xu-ly',
      nguoiGui: 'Ngô Đăng Hà',
      lanhDaoTiepNhan: 'Phan Thanh Thảo',
      nguoiVanThu: 'Nguyễn Hữu Quốc',
      noiDungTrinh: 'Kính trình lãnh đạo xem xét.',
      yKienHoanTra: '',
      specialistIds: ['nv1', 'nv2'],
      specialistNames: ['Nguyễn Hữu Quốc', 'Trần Tấn Tú'],
      mainFile: { name: 'CV_1735_CT_CS.pdf' },
      relatedFiles: [{ name: 'CV_1735_CT_CS.docx' }, { name: 'CV_1735_CT_CS.pdf' }],
      hoSoId: ''
    },
    {
      id: 3,
      soKyHieu: '123/SYT',
      donViBanHanh: 'UBND Thành phố',
      trichYeu: 'Báo cáo tình hình dịch bệnh',
      loaiVanBan: 'Báo cáo',
      hinhThuc: 'Công văn',
      ngayVanBan: '2026-02-03',
      ngayDen: '2026-02-04',
      hanXuLy: '2026-02-09',
      doMat: 'Mật',
      doKhan: 'Khẩn',
      trangThai: 'xem-de-biet',
      nguoiGui: 'Ngô Đăng Hà',
      lanhDaoTiepNhan: 'Phan Thanh Thảo',
      nguoiVanThu: 'Nguyễn Hữu Quốc',
      noiDungTrinh: 'Kính trình lãnh đạo xem xét.',
      yKienHoanTra: '',
      specialistIds: [],
      specialistNames: [],
      mainFile: { name: 'CV_1735_CT_CS.pdf' },
      relatedFiles: [{ name: 'CV_1735_CT_CS.docx' }, { name: 'CV_1735_CT_CS.pdf' }],
      hoSoId: ''
    },
    {
      id: 4,
      soKyHieu: '123/UBND',
      donViBanHanh: 'UBND Thành phố',
      trichYeu: 'Quyết định thay đổi thuế',
      loaiVanBan: 'Quyết định',
      hinhThuc: 'Công văn',
      ngayVanBan: '2026-02-03',
      ngayDen: '2026-02-04',
      hanXuLy: '2026-02-09',
      doMat: 'Mật',
      doKhan: 'Khẩn',
      trangThai: 'hoan-tra',
      nguoiGui: 'Ngô Đăng Hà',
      lanhDaoTiepNhan: 'Phan Thanh Thảo',
      nguoiVanThu: 'Nguyễn Hữu Quốc',
      noiDungTrinh: 'Kính trình lãnh đạo xem xét.',
      yKienHoanTra: 'Cần bổ sung số liệu chi tiết tháng 10',
      specialistIds: ['nv1'],
      specialistNames: ['Nguyễn Hữu Quốc'],
      mainFile: { name: 'CV_1735_CT_CS.pdf' },
      relatedFiles: [{ name: 'CV_1735_CT_CS.docx' }, { name: 'CV_1735_CT_CS.pdf' }],
      hoSoId: ''
    }
  ];

  const hoSoOptions = typeof MOCK_HO_SO !== 'undefined'
    ? MOCK_HO_SO.map(function (item) {
        return { id: String(item.id), label: item.tenHoSo };
      })
    : [
        { id: '1', label: 'Tập văn bản gửi đến cơ quan' },
        { id: '2', label: 'Hồ sơ kế hoạch công tác' }
      ];

  const state = {
    documents: initialDocuments,
    filteredDocuments: [],
    activeStatus: 'all',
    currentPage: 1,
    perPage: 4,
    editingId: null,
    currentDetailId: null,
    formFiles: { main: [], related: [] },
    employeeModalMode: 'leader',
    modalSelectedIds: new Set(),
    currentTransferDocId: null,
    returnDocId: null,
    expandedGroupIds: new Set(['pb1'])
  };

  const GIAO_VIEC_PREFILL_KEY = 'giao_viec_prefill_from_vbd';

  const elements = {
    listView: document.getElementById('vbdListView'),
    formView: document.getElementById('vbdFormView'),
    detailView: document.getElementById('vbdDetailView'),
    breadcrumbText: document.getElementById('breadcrumbText'),
    formViewTitle: document.getElementById('formViewTitle'),
    btnAddVanBanDen: document.getElementById('btnAddVanBanDen'),
    btnSaveVBD: document.getElementById('btnSaveVBD'),
    searchKeyword: document.getElementById('searchKeyword'),
    filterLoaiVB: document.getElementById('filterLoaiVB'),
    filterHinhThuc: document.getElementById('filterHinhThuc'),
    filterDoMat: document.getElementById('filterDoMat'),
    filterDoKhan: document.getElementById('filterDoKhan'),
    tableBody: document.getElementById('vanBanDenBody'),
    paginationInfo: document.getElementById('paginationInfo'),
    paginationBtns: document.getElementById('paginationBtns'),
    tabButtons: Array.from(document.querySelectorAll('.tab-filter-btn')),
    dateColumnHeader: document.querySelector('#vanBanDenTable thead th:nth-child(4)'),
    vbdId: document.getElementById('vbdId'),
    vbdSoKyHieu: document.getElementById('vbdSoKyHieu'),
    vbdDonViBanHanh: document.getElementById('vbdDonViBanHanh'),
    vbdLoaiVB: document.getElementById('vbdLoaiVB'),
    vbdHinhThuc: document.getElementById('vbdHinhThuc'),
    vbdTrichYeu: document.getElementById('vbdTrichYeu'),
    vbdNgayVanBan: document.getElementById('vbdNgayVanBan'),
    vbdNgayDen: document.getElementById('vbdNgayDen'),
    vbdHanXuLy: document.getElementById('vbdHanXuLy'),
    vbdDoMat: document.getElementById('vbdDoMat'),
    vbdDoKhan: document.getElementById('vbdDoKhan'),
    vbdFile: document.getElementById('vbdFile'),
    vbdFileList: document.getElementById('vbdFileList'),
    vbdFileUploadArea: document.getElementById('vbdFileUploadArea'),
    vbdFileLienQuan: document.getElementById('vbdFileLienQuan'),
    vbdFileLienQuanList: document.getElementById('vbdFileLienQuanList'),
    vbdFileLienQuanUploadArea: document.getElementById('vbdFileLienQuanUploadArea'),
    vbdLanhDao: document.getElementById('vbdLanhDao'),
    vbdNoiDungTrinh: document.getElementById('vbdNoiDungTrinh'),
    detailHeaderActions: document.getElementById('detailHeaderActions'),
    detailContentBlock: document.getElementById('detailContentBlock'),
    detailRoleBlock: document.getElementById('detailRoleBlock'),
    detailMainFile: document.getElementById('detailMainFile'),
    detailRelatedFiles: document.getElementById('detailRelatedFiles'),
    previewFileName: document.getElementById('previewFileName'),
    selectHoSoVBD: document.getElementById('selectHoSoVBD'),
    btnSaveThemVBHoSo: document.getElementById('btnSaveThemVBHoSo'),
    modalNhanVienUnitFilter: document.getElementById('modalNhanVienUnitFilter'),
    modalNhanVienSearch: document.getElementById('modalNhanVienSearch'),
    treeNhanVienBody: document.getElementById('treeNhanVienBody'),
    chkAllNhanVien: document.getElementById('chkAllNhanVien'),
    lblSelectedCount: document.getElementById('lblSelectedCount'),
    txtLyDoHoanTra: document.getElementById('txtLyDoHoanTra'),
    btnSubmitHoanTra: document.getElementById('btnSubmitHoanTra'),
    returnClerkName: document.getElementById('returnClerkName'),
    headerUserName: document.getElementById('headerUserName'),
    headerUserRole: document.getElementById('headerUserRole'),
    headerAvatar: document.getElementById('headerAvatar')
  };

  normalizeFormSelectDefaults();
  initPageProfile();
  configureRoleLayout();
  initEvents();
  populateHoSoOptions();
  resetForm();
  applyFilters();

  window.showListView = showListView;
  window.showFormView = showFormView;
  window.viewDetail = viewDetail;
  window.editRecord = editRecord;
  window.deleteRecord = deleteRecord;
  window.openNhanVienModal = openNhanVienModal;
  window.toggleTree = toggleTree;
  window.toggleGroup = toggleGroup;
  window.toggleStaff = toggleStaff;
  window.toggleAllNhanVien = toggleAllNhanVien;
  window.saveChonNhanVien = saveChonNhanVien;
  window.validateHoanTra = validateHoanTra;
  window.submitHoanTra = submitHoanTra;
  window.removeFormFile = removeFormFile;

  function isClerk() { return user.role === 'vanthu'; }
  function isLeader() { return user.role === 'lanhdao'; }
  function isSpecialist() { return user.role === 'chuyenvien'; }

  function initPageProfile() {
    const profile = pageProfiles[user.role];
    if (!profile) return;
    if (elements.headerUserName) elements.headerUserName.textContent = profile.name;
    if (elements.headerUserRole) elements.headerUserRole.textContent = profile.roleLabel;
    if (elements.headerAvatar) elements.headerAvatar.textContent = profile.avatar;
  }

  function configureRoleLayout() {
    if (elements.dateColumnHeader) {
      elements.dateColumnHeader.textContent = isSpecialist() ? 'Ngày nhận' : 'Ngày văn bản';
    }

    if (isSpecialist()) {
      elements.tabButtons.forEach(function (button, index) {
        if (index > 0) button.style.display = 'none';
      });
    }
  }

  function normalizeFormSelectDefaults() {
    [elements.vbdLoaiVB, elements.vbdHinhThuc, elements.vbdDoMat, elements.vbdDoKhan].forEach(function (select) {
      if (!select || !select.options.length) return;
      if (!select.options[0].value) select.options[0].value = select.options[0].text;
    });
  }

  function formatDisplayDate(value) {
    if (!value) return '';
    if (value.includes('/')) return value;
    const parts = value.split('-');
    return parts.length === 3 ? parts[2] + '/' + parts[1] + '/' + parts[0] : value;
  }

  function toInputDate(value) {
    if (!value) return '';
    if (value.includes('-')) return value;
    const parts = value.split('/');
    return parts.length === 3 ? parts[2] + '-' + parts[1].padStart(2, '0') + '-' + parts[0].padStart(2, '0') : '';
  }

  function getStatusInfo(status) {
    return statusMeta[status] || statusMeta['cho-xu-ly'];
  }

  function getDisplayStatus(doc) {
    if (isSpecialist()) return 'xem-de-biet';
    return doc.trangThai;
  }

  function renderStatusBadge(status) {
    const info = getStatusInfo(status);
    return '<span class="badge ' + info.className + '">' + info.label + '</span>';
  }

  function getFileTypeLabel(fileName) {
    const name = (fileName || '').toLowerCase();
    if (name.endsWith('.pdf')) return 'PDF';
    if (name.endsWith('.docx')) return 'DOCX';
    if (name.endsWith('.doc')) return 'DOC';
    if (name.endsWith('.xlsx')) return 'XLSX';
    if (name.endsWith('.xls')) return 'XLS';
    return 'FILE';
  }

  function getFileTypeClass(fileName) {
    return getFileTypeLabel(fileName) === 'PDF' ? '' : ' docx';
  }

  function getFileTypeText(fileName) {
    const type = getFileTypeLabel(fileName);
    if (type === 'PDF') return 'PDF Document';
    if (type === 'DOC' || type === 'DOCX') return 'Docx Document';
    if (type === 'XLS' || type === 'XLSX') return 'Excel Document';
    return 'File Document';
  }

  function cloneFile(fileEntry) {
    return fileEntry ? { name: fileEntry.name } : null;
  }

  function buildFileEntries(fileList) {
    return Array.from(fileList || []).map(function (file) {
      return { name: file.name };
    });
  }

  function getDocumentById(id) {
    return state.documents.find(function (item) {
      return item.id === Number(id);
    });
  }

  function getCurrentDetailDocument() {
    return getDocumentById(state.currentDetailId);
  }

  function buildCongViecPrefillFromDocument(doc) {
    return {
      sourceType: 'Văn bản đến',
      sourceDocumentId: doc.id,
      tenLanhDao: doc.lanhDaoTiepNhan || user.name,
      nguonCV: 'Văn bản đến',
      nguonChiTiet: `Văn bản đến số ${doc.soKyHieu}`,
      ngayBatDau: doc.ngayDen || doc.ngayVanBan || '',
      hanXuLy: doc.hanXuLy || doc.ngayDen || doc.ngayVanBan || '',
      tenCongViec: doc.trichYeu || '',
      noiDungCV: [
        `Xử lý văn bản đến số ${doc.soKyHieu || '—'}.`,
        doc.trichYeu ? `Trích yếu: ${doc.trichYeu}` : '',
        doc.donViBanHanh ? `Đơn vị ban hành: ${doc.donViBanHanh}` : '',
        doc.noiDungTrinh ? `Nội dung trình: ${doc.noiDungTrinh}` : ''
      ].filter(Boolean).join('\n'),
      ghiChu: doc.doKhan && doc.doKhan !== 'Bình thường' ? `Độ khẩn: ${doc.doKhan}` : '',
      fileDinhKem: doc.mainFile ? doc.mainFile.name : '',
      taiLieuLienQuan: (doc.relatedFiles || []).map(function (file) { return file.name; })
    };
  }

  function openGiaoViecFromDocument(doc) {
    sessionStorage.setItem(GIAO_VIEC_PREFILL_KEY, JSON.stringify(buildCongViecPrefillFromDocument(doc)));
    window.location.href = 'giao-viec.html?from=van-ban-den';
  }

  function initEvents() {
    elements.tabButtons.forEach(function (button) {
      button.addEventListener('click', function () {
        elements.tabButtons.forEach(function (item) { item.classList.remove('active'); });
        button.classList.add('active');
        state.activeStatus = button.dataset.status || 'all';
        applyFilters();
      });
    });

    [elements.searchKeyword, elements.filterLoaiVB, elements.filterHinhThuc, elements.filterDoMat, elements.filterDoKhan].forEach(function (input) {
      if (!input) return;
      input.addEventListener(input.tagName === 'SELECT' ? 'change' : 'input', applyFilters);
    });

    if (elements.btnAddVanBanDen) {
      elements.btnAddVanBanDen.addEventListener('click', function () {
        state.editingId = null;
        resetForm();
        showFormView(false);
      });
    }

    [elements.vbdSoKyHieu, elements.vbdDonViBanHanh, elements.vbdLoaiVB, elements.vbdHinhThuc, elements.vbdTrichYeu, elements.vbdNgayVanBan, elements.vbdLanhDao].forEach(function (input) {
      if (!input) return;
      input.addEventListener(input.tagName === 'SELECT' ? 'change' : 'input', validateForm);
    });

    if (elements.vbdFile) {
      elements.vbdFile.addEventListener('change', function (event) {
        state.formFiles.main = buildFileEntries(event.target.files).slice(0, 1);
        renderFormFiles('main');
        validateForm();
        elements.vbdFile.value = '';
      });
    }

    if (elements.vbdFileLienQuan) {
      elements.vbdFileLienQuan.addEventListener('change', function (event) {
        state.formFiles.related = state.formFiles.related.concat(buildFileEntries(event.target.files));
        renderFormFiles('related');
        elements.vbdFileLienQuan.value = '';
      });
    }

    if (elements.btnSaveVBD) elements.btnSaveVBD.addEventListener('click', saveForm);
    if (elements.selectHoSoVBD) elements.selectHoSoVBD.addEventListener('change', validateHoSoModalSelection);
    if (elements.btnSaveThemVBHoSo) elements.btnSaveThemVBHoSo.addEventListener('click', saveDocumentToHoSo);
    if (elements.modalNhanVienSearch) elements.modalNhanVienSearch.addEventListener('input', renderEmployeeModal);
    if (elements.modalNhanVienUnitFilter) elements.modalNhanVienUnitFilter.addEventListener('change', renderEmployeeModal);
  }

  function setPrimaryButtonState(button, enabled) {
    if (!button) return;
    button.disabled = !enabled;
    button.style.background = enabled ? 'var(--primary)' : '#94A3B8';
    button.style.borderColor = enabled ? 'var(--primary)' : '#94A3B8';
    button.style.cursor = enabled ? 'pointer' : 'not-allowed';
    button.style.opacity = '1';
  }

  function setDangerButtonState(button, enabled) {
    if (!button) return;
    button.disabled = !enabled;
    button.style.background = enabled ? '#DE5353' : '#94A3B8';
    button.style.borderColor = enabled ? '#DE5353' : '#94A3B8';
    button.style.cursor = enabled ? 'pointer' : 'not-allowed';
    button.style.opacity = enabled ? '1' : '0.6';
  }

  function showOnly(activeElement) {
    [elements.listView, elements.formView, elements.detailView].forEach(function (view) {
      if (!view) return;
      view.style.display = view === activeElement ? 'block' : 'none';
    });
  }

  function showListView() {
    showOnly(elements.listView);
    if (elements.breadcrumbText) elements.breadcrumbText.textContent = 'Văn bản đến';
    window.scrollTo(0, 0);
  }

  function showFormView(isEdit) {
    if (elements.formViewTitle) elements.formViewTitle.textContent = isEdit ? 'Chỉnh sửa văn bản đến' : 'Trình văn bản đến';
    if (elements.btnSaveVBD) elements.btnSaveVBD.textContent = isEdit ? 'Chỉnh sửa' : 'Gửi trình lãnh đạo';
    if (elements.breadcrumbText) {
      elements.breadcrumbText.textContent = isEdit ? 'Văn bản đến / Chỉnh sửa văn bản đến' : 'Văn bản đến / Trình văn bản đến';
    }
    showOnly(elements.formView);
    window.scrollTo(0, 0);
  }

  function showDetailView() {
    if (elements.breadcrumbText) elements.breadcrumbText.textContent = 'Văn bản đến / Chi tiết văn bản';
    showOnly(elements.detailView);
    window.scrollTo(0, 0);
  }

  function applyFilters() {
    const keyword = (elements.searchKeyword ? elements.searchKeyword.value : '').trim().toLowerCase();
    const loai = elements.filterLoaiVB ? elements.filterLoaiVB.value : '';
    const hinhThuc = elements.filterHinhThuc ? elements.filterHinhThuc.value : '';
    const doMat = elements.filterDoMat ? elements.filterDoMat.value : '';
    const doKhan = elements.filterDoKhan ? elements.filterDoKhan.value : '';

    state.filteredDocuments = state.documents.filter(function (doc) {
      const status = getDisplayStatus(doc);
      if (state.activeStatus !== 'all' && status !== state.activeStatus) return false;
      if (keyword) {
        const haystack = [doc.soKyHieu, doc.trichYeu, doc.donViBanHanh].join(' ').toLowerCase();
        if (!haystack.includes(keyword)) return false;
      }
      if (loai && doc.loaiVanBan !== loai) return false;
      if (hinhThuc && doc.hinhThuc !== hinhThuc) return false;
      if (doMat && doc.doMat !== doMat) return false;
      if (doKhan && doc.doKhan !== doKhan) return false;
      return true;
    });

    state.currentPage = 1;
    renderTable();
  }

  function renderTable() {
    const total = state.filteredDocuments.length;
    const start = (state.currentPage - 1) * state.perPage;
    const pageItems = state.filteredDocuments.slice(start, start + state.perPage);

    if (!elements.tableBody) return;

    if (!pageItems.length) {
      elements.tableBody.innerHTML = '<tr><td colspan="7"><div class="empty-state">Không tìm thấy văn bản phù hợp.</div></td></tr>';
    } else {
      elements.tableBody.innerHTML = pageItems.map(function (doc, index) {
        const statusInfo = getStatusInfo(getDisplayStatus(doc));
        const displayDate = isSpecialist() ? formatDisplayDate(doc.ngayDen) : formatDisplayDate(doc.ngayVanBan);
        return '' +
          '<tr>' +
            '<td class="text-center">' + (start + index + 1) + '</td>' +
            '<td><a href="#" style="color:var(--primary);font-weight:600;text-decoration:none;" onclick="viewDetail(' + doc.id + '); return false;">' + doc.soKyHieu + '</a></td>' +
            '<td style="line-height:1.5; color: var(--text-main); font-size: 14px;">' + doc.trichYeu + '</td>' +
            '<td style="color: var(--text-main); font-weight: 500;">' + displayDate + '</td>' +
            '<td style="color: var(--text-main);">' + doc.donViBanHanh + '</td>' +
            '<td><div style="font-size:13px; color:var(--text-main); margin-bottom:2px;">' + doc.doMat + ' /</div><div style="font-weight:700; color:#DC2626;">' + doc.doKhan.toUpperCase() + '</div></td>' +
            '<td><span class="badge ' + statusInfo.className + '">' + statusInfo.label + '</span></td>' +
          '</tr>';
      }).join('');
    }

    if (elements.paginationInfo) elements.paginationInfo.textContent = 'Hiển thị ' + total + ' văn bản';
    renderPagination(total);
  }

  function renderPagination(totalItems) {
    if (!elements.paginationBtns) return;
    const totalPages = Math.max(1, Math.ceil(totalItems / state.perPage));
    if (state.currentPage > totalPages) state.currentPage = totalPages;

    let html = '<button class="page-btn-text" ' + (state.currentPage === 1 ? 'disabled' : '') + ' data-page-action="prev">Trước</button>';
    for (let page = 1; page <= totalPages; page += 1) {
      html += '<button class="page-btn-num' + (page === state.currentPage ? ' active' : '') + '" data-page="' + page + '">' + page + '</button>';
    }
    html += '<button class="page-btn-text" ' + (state.currentPage === totalPages ? 'disabled' : '') + ' data-page-action="next">Sau</button>';
    elements.paginationBtns.innerHTML = html;

    elements.paginationBtns.querySelectorAll('[data-page]').forEach(function (button) {
      button.addEventListener('click', function () {
        state.currentPage = Number(button.dataset.page);
        renderTable();
      });
    });

    const prev = elements.paginationBtns.querySelector('[data-page-action="prev"]');
    const next = elements.paginationBtns.querySelector('[data-page-action="next"]');
    if (prev) prev.addEventListener('click', function () { if (state.currentPage > 1) { state.currentPage -= 1; renderTable(); } });
    if (next) next.addEventListener('click', function () { if (state.currentPage < totalPages) { state.currentPage += 1; renderTable(); } });
  }

  function resetForm() {
    state.editingId = null;
    if (elements.vbdId) elements.vbdId.value = '';
    if (elements.vbdSoKyHieu) elements.vbdSoKyHieu.value = '';
    if (elements.vbdDonViBanHanh) elements.vbdDonViBanHanh.value = '';
    if (elements.vbdLoaiVB) elements.vbdLoaiVB.value = 'Hành chính';
    if (elements.vbdHinhThuc) elements.vbdHinhThuc.value = 'Công văn';
    if (elements.vbdTrichYeu) elements.vbdTrichYeu.value = '';
    if (elements.vbdNgayVanBan) elements.vbdNgayVanBan.value = '';
    if (elements.vbdNgayDen) elements.vbdNgayDen.value = '';
    if (elements.vbdHanXuLy) elements.vbdHanXuLy.value = '';
    if (elements.vbdDoMat) elements.vbdDoMat.value = 'Bình thường';
    if (elements.vbdDoKhan) elements.vbdDoKhan.value = 'Bình thường';
    if (elements.vbdLanhDao) elements.vbdLanhDao.value = '';
    if (elements.vbdNoiDungTrinh) elements.vbdNoiDungTrinh.value = '';
    state.formFiles.main = [];
    state.formFiles.related = [];
    renderFormFiles('main');
    renderFormFiles('related');
    validateForm();
  }

  function fillForm(doc) {
    state.editingId = doc.id;
    if (elements.vbdId) elements.vbdId.value = String(doc.id);
    if (elements.vbdSoKyHieu) elements.vbdSoKyHieu.value = doc.soKyHieu;
    if (elements.vbdDonViBanHanh) elements.vbdDonViBanHanh.value = doc.donViBanHanh;
    if (elements.vbdLoaiVB) elements.vbdLoaiVB.value = doc.loaiVanBan;
    if (elements.vbdHinhThuc) elements.vbdHinhThuc.value = doc.hinhThuc;
    if (elements.vbdTrichYeu) elements.vbdTrichYeu.value = doc.trichYeu;
    if (elements.vbdNgayVanBan) elements.vbdNgayVanBan.value = toInputDate(doc.ngayVanBan);
    if (elements.vbdNgayDen) elements.vbdNgayDen.value = toInputDate(doc.ngayDen);
    if (elements.vbdHanXuLy) elements.vbdHanXuLy.value = toInputDate(doc.hanXuLy);
    if (elements.vbdDoMat) elements.vbdDoMat.value = doc.doMat;
    if (elements.vbdDoKhan) elements.vbdDoKhan.value = doc.doKhan;
    if (elements.vbdLanhDao) elements.vbdLanhDao.value = doc.lanhDaoTiepNhan;
    if (elements.vbdNoiDungTrinh) elements.vbdNoiDungTrinh.value = doc.noiDungTrinh;
    state.formFiles.main = doc.mainFile ? [cloneFile(doc.mainFile)] : [];
    state.formFiles.related = doc.relatedFiles.map(cloneFile);
    renderFormFiles('main');
    renderFormFiles('related');
    validateForm();
  }

  function renderFormFiles(type) {
    const files = type === 'main' ? state.formFiles.main : state.formFiles.related;
    const listElement = type === 'main' ? elements.vbdFileList : elements.vbdFileLienQuanList;
    const uploadArea = type === 'main' ? elements.vbdFileUploadArea : elements.vbdFileLienQuanUploadArea;
    if (!listElement || !uploadArea) return;

    if (!files.length) {
      listElement.innerHTML = '';
      listElement.style.display = 'none';
      uploadArea.style.display = 'block';
      return;
    }

    uploadArea.style.display = 'none';
    listElement.style.display = 'block';
    listElement.innerHTML = files.map(function (file, index) {
      return '' +
        '<div class="file-item-card">' +
          '<div class="file-item-icon' + getFileTypeClass(file.name) + '">' + getFileTypeLabel(file.name) + '</div>' +
          '<div style="flex:1;"><div class="file-item-name">' + file.name + '</div><div class="file-item-type">' + getFileTypeText(file.name) + '</div></div>' +
          '<button class="file-remove-btn" onclick="removeFormFile(\'' + type + '\',' + index + ')">×</button>' +
        '</div>';
    }).join('');
  }

  function removeFormFile(type, index) {
    if (type === 'main') state.formFiles.main.splice(index, 1);
    else state.formFiles.related.splice(index, 1);
    renderFormFiles(type);
    validateForm();
  }

  function validateForm() {
    const valid = Boolean(
      elements.vbdSoKyHieu && elements.vbdSoKyHieu.value.trim() &&
      elements.vbdDonViBanHanh && elements.vbdDonViBanHanh.value.trim() &&
      elements.vbdLoaiVB && elements.vbdLoaiVB.value &&
      elements.vbdHinhThuc && elements.vbdHinhThuc.value &&
      elements.vbdTrichYeu && elements.vbdTrichYeu.value.trim() &&
      elements.vbdNgayVanBan && elements.vbdNgayVanBan.value &&
      elements.vbdLanhDao && elements.vbdLanhDao.value.trim() &&
      state.formFiles.main.length > 0
    );
    setPrimaryButtonState(elements.btnSaveVBD, valid);
    return valid;
  }

  function saveForm() {
    if (!validateForm()) return;
    const data = {
      soKyHieu: elements.vbdSoKyHieu.value.trim(),
      donViBanHanh: elements.vbdDonViBanHanh.value.trim(),
      loaiVanBan: elements.vbdLoaiVB.value,
      hinhThuc: elements.vbdHinhThuc.value,
      trichYeu: elements.vbdTrichYeu.value.trim(),
      ngayVanBan: elements.vbdNgayVanBan.value,
      ngayDen: elements.vbdNgayDen.value || elements.vbdNgayVanBan.value,
      hanXuLy: elements.vbdHanXuLy.value || elements.vbdNgayVanBan.value,
      doMat: elements.vbdDoMat.value || 'Bình thường',
      doKhan: elements.vbdDoKhan.value || 'Bình thường',
      lanhDaoTiepNhan: elements.vbdLanhDao.value.trim(),
      nguoiGui: pageProfiles.vanthu.name,
      nguoiVanThu: 'Nguyễn Hữu Quốc',
      noiDungTrinh: elements.vbdNoiDungTrinh.value.trim() || 'Kính trình lãnh đạo xem xét.',
      mainFile: cloneFile(state.formFiles.main[0]),
      relatedFiles: state.formFiles.related.map(cloneFile)
    };

    if (state.editingId) {
      const current = getDocumentById(state.editingId);
      if (!current) return;
      Object.assign(current, data);
      showToast('Đã cập nhật văn bản đến.', 'success');
    } else {
      state.documents.unshift({
        id: Date.now(),
        trangThai: 'cho-xu-ly',
        yKienHoanTra: '',
        specialistIds: [],
        specialistNames: [],
        hoSoId: '',
        ...data
      });
      showToast('Đã gửi trình lãnh đạo.', 'success');
    }

    applyFilters();
    showListView();
  }

  function viewDetail(id) {
    const doc = getDocumentById(id);
    if (!doc) return;
    state.currentDetailId = doc.id;
    renderDetail(doc);
    showDetailView();
  }

  function editRecord(id) {
    const doc = getDocumentById(id);
    if (!doc) return;
    fillForm(doc);
    showFormView(true);
  }

  function deleteRecord(id) {
    const doc = getDocumentById(id);
    if (!doc) return;
    showConfirm('Xóa văn bản', 'Bạn có chắc chắn muốn xóa văn bản này không?', function () {
      state.documents = state.documents.filter(function (item) { return item.id !== doc.id; });
      if (state.currentDetailId === doc.id) state.currentDetailId = null;
      applyFilters();
      showListView();
      showToast('Đã xóa văn bản thành công.', 'success');
    });
  }

  function renderDetail(doc) {
    if (elements.detailContentBlock) {
      if (isLeader()) elements.detailContentBlock.innerHTML = renderLeaderDetailContent(doc);
      else if (isSpecialist()) elements.detailContentBlock.innerHTML = renderSpecialistDetailContent(doc);
      else elements.detailContentBlock.innerHTML = renderClerkDetailContent(doc);
    }
    renderDetailRoleBlock(doc);
    renderDetailActions(doc);
    renderDetailFiles(doc);
  }

  function renderClerkDetailContent(doc) {
    let html = '' +
      '<hr style="border:none; border-top: 1px solid var(--border-color); margin: 0 0 24px 0;">' +
      '<div class="detail-grid">' +
        '<div><div class="detail-label">Trích yếu</div><div class="detail-value">' + doc.trichYeu + '</div></div>' +
        '<div><div class="detail-label">Số ký hiệu:</div><div class="detail-value" style="font-weight:700;">' + doc.soKyHieu + '</div></div>' +
        '<div><div class="detail-label">Lãnh đạo tiếp nhận:</div><div class="detail-value">' + doc.lanhDaoTiepNhan + '</div><div style="margin-top:8px;">' + renderStatusBadge(getDisplayStatus(doc)) + '</div></div>' +
        '<div><div class="detail-label">Đơn vị ban hành:</div><div class="detail-value">' + doc.donViBanHanh + '</div></div>' +
        '<div><div class="detail-label">Loại văn bản:</div><div class="detail-value">' + doc.loaiVanBan + '</div></div><div></div>' +
        '<div><div class="detail-label">Hình thức:</div><div class="detail-value">' + doc.hinhThuc + '</div></div>' +
        '<div><div class="detail-label">Ngày văn bản:</div><div class="detail-value">' + formatDisplayDate(doc.ngayVanBan) + '</div></div><div></div>' +
        '<div><div class="detail-label">Ngày đến:</div><div class="detail-value">' + formatDisplayDate(doc.ngayDen) + '</div></div>' +
        '<div><div class="detail-label">Hạn xử lý:</div><div class="detail-value">' + formatDisplayDate(doc.hanXuLy) + '</div></div><div></div>' +
        '<div><div class="detail-label">Độ mật:</div><div class="detail-value">' + doc.doMat + '</div></div>' +
        '<div><div class="detail-label">Độ khẩn:</div><div class="detail-value">' + doc.doKhan + '</div></div><div></div>' +
      '</div>' +
      '<div class="detail-box"><div class="detail-box-title">Nội dung trình lãnh đạo:</div><div style="color:var(--text-main); font-size:14px;">' + doc.noiDungTrinh + '</div></div>';
    if (doc.yKienHoanTra) {
      html += '<div class="detail-box detail-box-return"><div class="detail-box-title">Ý kiến xử lý / hoàn trả</div><div style="color:var(--text-main); font-size:14px;">' + doc.yKienHoanTra + '</div></div>';
    }
    return html;
  }

  function renderLeaderDetailContent(doc) {
    let html = '' +
      '<hr style="border:none; border-top: 1px solid var(--border-color); margin: 0 0 24px 0;">' +
      '<div class="detail-grid">' +
        '<div><div class="detail-label">Trích yếu</div><div class="detail-value">' + doc.trichYeu + '</div></div>' +
        '<div><div class="detail-label">Số ký hiệu:</div><div class="detail-value" style="font-weight:700;">' + doc.soKyHieu + '</div></div>' +
        '<div><div class="detail-label">Người gửi:</div><div class="detail-value">' + doc.nguoiGui + '</div><div style="margin-top:8px;">' + renderStatusBadge(getDisplayStatus(doc)) + '</div></div>' +
        '<div><div class="detail-label">Đơn vị ban hành:</div><div class="detail-value">' + doc.donViBanHanh + '</div></div>' +
        '<div><div class="detail-label">Loại văn bản:</div><div class="detail-value">' + doc.loaiVanBan + '</div></div><div></div>' +
        '<div><div class="detail-label">Ngày đến:</div><div class="detail-value">' + formatDisplayDate(doc.ngayDen) + '</div></div>' +
        '<div><div class="detail-label">Hạn xử lý:</div><div class="detail-value">' + formatDisplayDate(doc.hanXuLy) + '</div></div><div></div>' +
        '<div><div class="detail-label">Độ mật:</div><div class="detail-value">' + doc.doMat + '</div></div>' +
        '<div><div class="detail-label">Độ khẩn:</div><div class="detail-value">' + doc.doKhan + '</div></div><div></div>' +
      '</div>' +
      '<div class="detail-box"><div class="detail-box-title">Nội dung trình lãnh đạo:</div><div style="color:var(--text-main); font-size:14px;">' + doc.noiDungTrinh + '</div></div>';
    if (doc.yKienHoanTra) {
      html += '<div class="detail-box detail-box-return"><div class="detail-box-title">Ý kiến xử lý / hoàn trả</div><div style="color:var(--text-main); font-size:14px;">' + doc.yKienHoanTra + '</div></div>';
    }
    return html;
  }

  function renderSpecialistDetailContent(doc) {
    return '' +
      '<hr style="border:none; border-top: 1px solid var(--border-color); margin: 0 0 24px 0;">' +
      '<div class="detail-grid">' +
        '<div><div class="detail-label">Trích yếu</div><div class="detail-value">' + doc.trichYeu + '</div></div>' +
        '<div><div class="detail-label">Số ký hiệu:</div><div class="detail-value" style="font-weight:700;">' + doc.soKyHieu + '</div></div>' +
        '<div><div class="detail-label">Người gửi:</div><div class="detail-value">Phan Thanh Thảo</div><div style="margin-top:8px;">' + renderStatusBadge('xem-de-biet') + '</div></div>' +
        '<div><div class="detail-label">Đơn vị ban hành:</div><div class="detail-value">' + doc.donViBanHanh + '</div></div>' +
        '<div><div class="detail-label">Loại văn bản:</div><div class="detail-value">' + doc.loaiVanBan + '</div></div><div></div>' +
        '<div><div class="detail-label">Ngày nhận:</div><div class="detail-value">' + formatDisplayDate(doc.ngayDen) + '</div></div>' +
        '<div><div class="detail-label">Hạn xử lý:</div><div class="detail-value">' + formatDisplayDate(doc.hanXuLy) + '</div></div><div></div>' +
        '<div><div class="detail-label">Độ mật:</div><div class="detail-value">' + doc.doMat + '</div></div>' +
        '<div><div class="detail-label">Độ khẩn:</div><div class="detail-value">' + doc.doKhan + '</div></div><div></div>' +
      '</div>' +
      '<div class="detail-box"><div class="detail-box-title">Nội dung trình lãnh đạo:</div><div style="color:var(--text-main); font-size:14px;">' + doc.noiDungTrinh + '</div></div>';
  }

  function renderDetailRoleBlock(doc) {
    if (!elements.detailRoleBlock) return;
    if (!isLeader()) {
      elements.detailRoleBlock.style.display = 'none';
      elements.detailRoleBlock.innerHTML = '';
      return;
    }

    const names = doc.specialistNames.length
      ? doc.specialistNames.map(function (name) { return '<div style="padding:4px 0; color:var(--text-main); font-size:14px;">' + name + '</div>'; }).join('')
      : '<div style="padding:4px 0; color:var(--text-secondary); font-size:14px;">Chưa có chuyên viên tiếp nhận.</div>';

    elements.detailRoleBlock.style.display = 'block';
    elements.detailRoleBlock.innerHTML =
      '<div class="filter-title" style="border-left: 4px solid var(--primary); padding-left: 12px; font-size: 16px; font-weight: 700; color: var(--primary); text-transform: uppercase; margin-bottom: 16px;">DANH SÁCH CHUYÊN VIÊN TIẾP NHẬN</div>' +
      '<div style="border-left:4px solid var(--primary); padding-left:12px;">' + names + '</div>';
  }

  function renderDetailActions(doc) {
    if (!elements.detailHeaderActions) return;
    if (isSpecialist()) {
      elements.detailHeaderActions.innerHTML = '';
      return;
    }

    if (isLeader()) {
      if (doc.trangThai === 'cho-xu-ly') {
        elements.detailHeaderActions.innerHTML =
          '<button id="btnLeaderTask" class="btn" style="background:#0284C7; color:white; border:none; font-weight:600;">+ Giao việc</button>' +
          '<button id="btnLeaderAssign" class="btn" style="background:#0284C7; color:white; border:none; font-weight:600;">Chuyển tiếp</button>' +
          '<button id="btnLeaderSave" class="btn" style="background:#64748B; color:white; border:none; font-weight:600;">Lưu</button>' +
          '<button id="btnLeaderReturn" class="btn" style="background:#DE5353; color:white; border:none; font-weight:600;">Hoàn trả</button>';
        document.getElementById('btnLeaderTask').addEventListener('click', function () { openGiaoViecFromDocument(doc); });
        document.getElementById('btnLeaderAssign').addEventListener('click', function () { openNhanVienModal('assign', doc.id); });
        document.getElementById('btnLeaderSave').addEventListener('click', function () { showToast('Đã lưu thông tin xử lý.', 'success'); });
        document.getElementById('btnLeaderReturn').addEventListener('click', function () { openReturnModal(doc); });
      } else {
        elements.detailHeaderActions.innerHTML = '';
      }
      return;
    }

    elements.detailHeaderActions.innerHTML =
      '<button id="btnDetailSaveHoSo" class="btn" style="background:#0284C7; color:white; border:none; font-weight:600;">+ Lưu hồ sơ</button>' +
      '<button id="btnDetailEdit" class="btn" style="background:#0284C7; color:white; border:none; font-weight:600;">Chỉnh sửa</button>' +
      '<button id="btnDetailDelete" class="btn" style="background:#DE5353; color:white; border:none; font-weight:600;">Xóa văn bản</button>';
    document.getElementById('btnDetailSaveHoSo').addEventListener('click', function () { openSaveHoSoModal(doc); });
    document.getElementById('btnDetailEdit').addEventListener('click', function () { editRecord(doc.id); });
    document.getElementById('btnDetailDelete').addEventListener('click', function () { deleteRecord(doc.id); });
  }

  function renderDetailFiles(doc) {
    if (elements.detailMainFile) elements.detailMainFile.innerHTML = renderMainFileCard(doc.mainFile);
    if (elements.detailRelatedFiles) elements.detailRelatedFiles.innerHTML = doc.relatedFiles.map(renderRelatedFileCard).join('');
    if (elements.previewFileName) elements.previewFileName.textContent = doc.mainFile ? doc.mainFile.name : 'Tệp đính kèm';
  }

  function renderMainFileCard(file) {
    if (!file) return '<div style="color: var(--text-secondary);">Chưa có file đính kèm.</div>';
    return '<div style="border:1px solid var(--border-color); padding:8px 16px; border-radius:4px; display:inline-flex; align-items:center; gap:12px; background:#fff;"><span style="color:#DC2626; font-weight:bold; font-size:12px;">' + getFileTypeLabel(file.name) + '</span><div><div style="font-weight:600; font-size:13px; color:var(--text-main);">' + file.name + '</div><div style="font-size:11px; color:var(--text-muted);">' + getFileTypeText(file.name) + '</div></div></div>';
  }

  function renderRelatedFileCard(file) {
    const color = getFileTypeLabel(file.name) === 'PDF' ? '#DC2626' : '#2563EB';
    return '<div style="display:flex; align-items:center; gap:8px; padding:6px 12px; border:1px solid var(--border-color); border-radius:4px; background:#F8FAFC;"><span style="color:' + color + '; font-weight:bold; font-size:10px;">' + getFileTypeLabel(file.name) + '</span><div><div style="font-size:13px; font-weight:600;">' + file.name + '</div><div style="font-size:11px; color:var(--text-muted);">' + getFileTypeText(file.name) + '</div></div></div>';
  }

  function populateHoSoOptions() {
    if (!elements.selectHoSoVBD) return;
    const currentValue = elements.selectHoSoVBD.value;
    elements.selectHoSoVBD.innerHTML = '<option value="">-- Tìm kiếm hoặc chọn tiêu đề hồ sơ --</option>' + hoSoOptions.map(function (item) {
      return '<option value="' + item.id + '">' + item.label + '</option>';
    }).join('');
    elements.selectHoSoVBD.value = currentValue || '';
    validateHoSoModalSelection();
  }

  function openSaveHoSoModal(doc) {
    populateHoSoOptions();
    if (elements.selectHoSoVBD) elements.selectHoSoVBD.value = doc.hoSoId || '';
    validateHoSoModalSelection();
    openModal('modalThemVB');
  }

  function validateHoSoModalSelection() {
    setPrimaryButtonState(elements.btnSaveThemVBHoSo, Boolean(elements.selectHoSoVBD && elements.selectHoSoVBD.value));
  }

  function saveDocumentToHoSo() {
    const doc = getCurrentDetailDocument();
    if (!doc || !elements.selectHoSoVBD || !elements.selectHoSoVBD.value) return;
    doc.hoSoId = elements.selectHoSoVBD.value;
    closeModal('modalThemVB');
    showToast('Đã thêm văn bản vào hồ sơ.', 'success');
  }

  function getAllStaffs() {
    return staffGroups.reduce(function (result, group) {
      return result.concat(group.staffs);
    }, []);
  }

  function getFilteredLeaders() {
    const keyword = (elements.modalNhanVienSearch ? elements.modalNhanVienSearch.value : '').trim().toLowerCase();
    return leaderOptions.filter(function (leader) {
      if (!keyword) return true;
      return [leader.name, leader.role, leader.phone, leader.email].join(' ').toLowerCase().includes(keyword);
    });
  }

  function getFilteredGroups() {
    const keyword = (elements.modalNhanVienSearch ? elements.modalNhanVienSearch.value : '').trim().toLowerCase();
    return staffGroups.reduce(function (result, group) {
      const staffs = group.staffs.filter(function (staff) {
        if (!keyword) return true;
        return [group.name, staff.name, staff.role, staff.phone, staff.email].join(' ').toLowerCase().includes(keyword);
      });
      if (staffs.length) result.push({ id: group.id, name: group.name, staffs: staffs });
      return result;
    }, []);
  }

  function openNhanVienModal(mode, docId) {
    state.employeeModalMode = mode === 'assign' ? 'assign' : 'leader';
    state.currentTransferDocId = docId || state.currentDetailId;
    state.modalSelectedIds = new Set();
    if (elements.modalNhanVienSearch) elements.modalNhanVienSearch.value = '';

    if (state.employeeModalMode === 'leader') {
      if (elements.modalNhanVienUnitFilter) elements.modalNhanVienUnitFilter.innerHTML = '<option>Ban Giám đốc</option>';
      const leader = leaderOptions.find(function (item) {
        return elements.vbdLanhDao && elements.vbdLanhDao.value.trim() === item.name;
      });
      if (leader) state.modalSelectedIds.add(leader.id);
    } else {
      if (elements.modalNhanVienUnitFilter) elements.modalNhanVienUnitFilter.innerHTML = '<option>VNPT Đà Nẵng</option>';
      const doc = getDocumentById(state.currentTransferDocId);
      if (doc && Array.isArray(doc.specialistIds)) state.modalSelectedIds = new Set(doc.specialistIds);
    }

    renderEmployeeModal();
    openModal('modalChonNhanVien');
  }

  function renderEmployeeModal() {
    if (!elements.treeNhanVienBody) return;

    if (state.employeeModalMode === 'leader') {
      const leaders = getFilteredLeaders();
      elements.treeNhanVienBody.innerHTML = leaders.length ? leaders.map(function (leader) {
        return '<div class="tree-node-content"><div style="display:flex; justify-content:center;"><input type="checkbox" class="tree-checkbox" ' + (state.modalSelectedIds.has(leader.id) ? 'checked' : '') + ' onclick="toggleStaff(\'' + leader.id + '\', this.checked)"></div><div class="tree-col-name">' + leader.name + '</div><div class="tree-col-val">' + leader.role + '</div><div class="tree-col-val">' + leader.phone + '</div><div class="tree-col-val">' + leader.email + '</div></div>';
      }).join('') : '<div style="padding:16px; color: var(--text-secondary);">Không tìm thấy lãnh đạo phù hợp.</div>';
      updateEmployeeModalSummary(leaders.length);
      return;
    }

    const groups = getFilteredGroups();
    let html = '';
    groups.forEach(function (group) {
      const isExpanded = state.expandedGroupIds.has(group.id);
      const fullGroup = staffGroups.find(function (item) { return item.id === group.id; });
      const groupChecked = fullGroup && fullGroup.staffs.every(function (staff) { return state.modalSelectedIds.has(staff.id); });
      html += '<div class="tree-node-content tree-node-group"><div style="display:flex; justify-content:center;"><button class="tree-expand-btn" onclick="toggleTree(\'' + group.id + '\')">' + (isExpanded ? '-' : '+') + '</button></div><div class="tree-col-name"><input type="checkbox" class="tree-checkbox" ' + (groupChecked ? 'checked' : '') + ' onclick="toggleGroup(\'' + group.id + '\', this.checked)">' + group.name + ' (' + String(fullGroup ? fullGroup.staffs.length : group.staffs.length).padStart(2, '0') + ')</div><div></div><div></div><div></div></div>';
      if (!isExpanded) return;
      group.staffs.forEach(function (staff) {
        html += '<div class="tree-node-content"><div></div><div class="tree-col-name" style="padding-left: 20px;"><input type="checkbox" class="tree-checkbox" ' + (state.modalSelectedIds.has(staff.id) ? 'checked' : '') + ' onclick="toggleStaff(\'' + staff.id + '\', this.checked)">' + staff.name + '</div><div class="tree-col-val">' + staff.role + '</div><div class="tree-col-val">' + staff.phone + '</div><div class="tree-col-val">' + staff.email + '</div></div>';
      });
    });
    elements.treeNhanVienBody.innerHTML = html || '<div style="padding:16px; color: var(--text-secondary);">Không tìm thấy nhân viên phù hợp.</div>';
    updateEmployeeModalSummary(getAllStaffs().length);
  }

  function updateEmployeeModalSummary(totalCount) {
    if (elements.lblSelectedCount) elements.lblSelectedCount.textContent = String(state.modalSelectedIds.size);
    if (elements.chkAllNhanVien) elements.chkAllNhanVien.checked = totalCount > 0 && state.modalSelectedIds.size === totalCount;
  }

  function toggleTree(groupId) {
    if (state.expandedGroupIds.has(groupId)) state.expandedGroupIds.delete(groupId);
    else state.expandedGroupIds.add(groupId);
    renderEmployeeModal();
  }

  function toggleGroup(groupId, checked) {
    const group = staffGroups.find(function (item) { return item.id === groupId; });
    if (!group) return;
    group.staffs.forEach(function (staff) {
      if (checked) state.modalSelectedIds.add(staff.id);
      else state.modalSelectedIds.delete(staff.id);
    });
    renderEmployeeModal();
  }

  function toggleStaff(staffId, checked) {
    if (checked) state.modalSelectedIds.add(staffId);
    else state.modalSelectedIds.delete(staffId);
    renderEmployeeModal();
  }

  function toggleAllNhanVien(checked) {
    const source = state.employeeModalMode === 'leader' ? leaderOptions : getAllStaffs();
    source.forEach(function (item) {
      if (checked) state.modalSelectedIds.add(item.id);
      else state.modalSelectedIds.delete(item.id);
    });
    renderEmployeeModal();
  }

  function saveChonNhanVien() {
    if (!state.modalSelectedIds.size) {
      showToast(state.employeeModalMode === 'leader' ? 'Vui lòng chọn lãnh đạo xử lý.' : 'Vui lòng chọn chuyên viên tiếp nhận.', 'warning');
      return;
    }

    if (state.employeeModalMode === 'leader') {
      const leader = leaderOptions.find(function (item) { return state.modalSelectedIds.has(item.id); });
      if (leader && elements.vbdLanhDao) elements.vbdLanhDao.value = leader.name;
      validateForm();
      closeModal('modalChonNhanVien');
      return;
    }

    const doc = getDocumentById(state.currentTransferDocId);
    if (!doc) return;
    doc.specialistIds = Array.from(state.modalSelectedIds);
    doc.specialistNames = getAllStaffs().filter(function (staff) { return state.modalSelectedIds.has(staff.id); }).map(function (staff) { return staff.name; });
    closeModal('modalChonNhanVien');
    renderDetail(doc);
    showToast('Đã cập nhật danh sách chuyên viên tiếp nhận.', 'success');
  }

  function openReturnModal(doc) {
    state.returnDocId = doc.id;
    if (elements.returnClerkName) elements.returnClerkName.textContent = 'Văn thư : ' + (doc.nguoiVanThu || 'Nguyễn Hữu Quốc');
    if (elements.txtLyDoHoanTra) elements.txtLyDoHoanTra.value = '';
    validateHoanTra();
    openModal('modalHoanTra');
  }

  function validateHoanTra() {
    setDangerButtonState(elements.btnSubmitHoanTra, Boolean(elements.txtLyDoHoanTra && elements.txtLyDoHoanTra.value.trim()));
  }

  function submitHoanTra() {
    const doc = getDocumentById(state.returnDocId);
    if (!doc || !elements.txtLyDoHoanTra || !elements.txtLyDoHoanTra.value.trim()) return;
    doc.trangThai = 'hoan-tra';
    doc.yKienHoanTra = elements.txtLyDoHoanTra.value.trim();
    closeModal('modalHoanTra');
    applyFilters();
    renderDetail(doc);
    showDetailView();
    showToast('Đã hoàn trả văn bản.', 'success');
  }
});
