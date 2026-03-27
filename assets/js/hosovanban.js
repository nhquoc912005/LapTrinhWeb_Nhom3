/**
 * hosovanban.js - Quản lý Hồ sơ Văn bản
 */
document.addEventListener('DOMContentLoaded', function () {
  const user = requireAuth();
  if (!user) return;

  let currentPage = 1;
  const perPage = 10;
  let filteredData = [...MOCK_HO_SO];
  let editingId = null;

  // Populate dropdown for add document to file
  function populateVBSelects() {
    const selDen = document.getElementById('selectVBDen');
    const selDi = document.getElementById('selectVBDi');
    if (selDen) {
      MOCK_VAN_BAN_DEN.forEach(vb => {
        const opt = document.createElement('option');
        opt.value = vb.id; opt.textContent = `${vb.soKyHieu} - ${vb.trichYeu.slice(0, 40)}`;
        selDen.appendChild(opt);
      });
    }
    if (selDi) {
      MOCK_VAN_BAN_DI.forEach(vb => {
        const opt = document.createElement('option');
        opt.value = vb.id; opt.textContent = `${vb.soKyHieu || 'Chưa có số'} - ${vb.trichYeu.slice(0, 40)}`;
        selDi.appendChild(opt);
      });
    }
  }

  let currentTab = 'all'; // all, hien-hanh, luu-tru

  function renderTable() {
    const tbody = document.getElementById('hoSoBody');
    const paginationInfo = document.getElementById('paginationInfo');

    const total = filteredData.length;
    // Just mock pagination display since data is small
    const start = 0;
    const end = total;
    const pageData = filteredData.slice(start, end);

    if (paginationInfo) paginationInfo.textContent = `Hiển thị ${total} văn bản`;

    if (!pageData.length) {
      tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><svg width="48" height="48" viewBox="0 0 24 24"><path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg><h3>Chưa có hồ sơ nào</h3></div></td></tr>`;
      return;
    }

    tbody.innerHTML = pageData.map((hs, idx) => {
      const statusColor = hs.trangThai === 'Hiện hành' ? '#166534' : '#475569';
      const statusBg = hs.trangThai === 'Hiện hành' ? '#DCFCE7' : '#E2E8F0';

      return `
        <tr style="border-bottom: 1px solid var(--border-color); background: #fff;">
          <td style="font-weight:700; color:#0284C7; cursor:pointer;" onclick="window.viewHoSoDetail(${hs.id})">${hs.tenHoSo}</td>
          <td style="color:var(--text-main);">${hs.maHoSo}</td>
          <td style="color:var(--text-main);">${hs.namHinhThanh}</td>
          <td style="color:var(--text-main);">${hs.thoiGianBaoQuan}</td>
          <td style="color:var(--text-main);">${hs.donVi}</td>
          <td><span style="background:${statusBg}; color:${statusColor}; padding:4px 12px; border-radius:20px; font-size:13px; font-weight:600;">${hs.trangThai}</span></td>
        </tr>`;
    }).join('');
  }

  function renderFilterChips() {
    const keyword = (document.getElementById('searchKeyword')?.value || '').trim();
    const status = document.getElementById('filterStatus')?.value || '';
    const donVi = document.getElementById('filterDonVi')?.value || '';
    const nam = document.getElementById('filterNam')?.value || '';

    const chips = [];
    if (status) chips.push({ type: 'status', label: `Trạng thái: ${status}` });
    if (donVi) chips.push({ type: 'donVu', label: `Đơn vị: ${donVi}` });
    if (nam) chips.push({ type: 'nam', label: `Năm: ${nam}` });

    const container = document.getElementById('filterChipsContainer');
    const chipsDiv = document.getElementById('filterChips');
    if (!container || !chipsDiv) return;

    if (chips.length > 0) {
      container.style.display = 'flex';
      chipsDiv.innerHTML = chips.map(c => `
        <div style="background:#E0F2FE; color:#0369A1; padding:4px 10px; border-radius:16px; font-size:12px; font-weight:600; display:flex; align-items:center; gap:6px;">
          ${c.label}
          <span style="cursor:pointer; font-weight:bold; color:#0284C7;" onclick="removeFilter('${c.type}')">&times;</span>
        </div>
      `).join('');
    } else {
      container.style.display = 'none';
      chipsDiv.innerHTML = '';
    }
  }

  window.removeFilter = function(type) {
    if (type === 'status') document.getElementById('filterStatus').value = '';
    if (type === 'donVu') document.getElementById('filterDonVi').value = '';
    if (type === 'nam') document.getElementById('filterNam').value = '';
    applyFilters();
  };

  function applyFilters() {
    const keyword = (document.getElementById('searchKeyword')?.value || '').toLowerCase();
    const status = document.getElementById('filterStatus')?.value || '';
    const donVi = document.getElementById('filterDonVi')?.value || '';
    const nam = document.getElementById('filterNam')?.value || '';

    filteredData = MOCK_HO_SO.filter(hs => {
      // Tab filter
      if (currentTab === 'hien-hanh' && hs.trangThai !== 'Hiện hành') return false;
      if (currentTab === 'luu-tru' && hs.trangThai !== 'Lưu trữ') return false;

      // Dropdown filters
      if (status && hs.trangThai !== status) return false;
      if (donVi && hs.donVi !== donVi) return false;
      if (nam && hs.namHinhThanh !== nam) return false;

      // Keyword filter
      if (keyword && !hs.maHoSo.toLowerCase().includes(keyword) && !hs.tenHoSo.toLowerCase().includes(keyword)) return false;

      return true;
    });

    renderFilterChips();
    renderTable();
  }

  // Filter Event Listeners
  document.getElementById('searchKeyword')?.addEventListener('input', applyFilters);
  document.getElementById('filterStatus')?.addEventListener('change', applyFilters);
  document.getElementById('filterDonVi')?.addEventListener('change', applyFilters);
  document.getElementById('filterNam')?.addEventListener('change', applyFilters);

  // Tab Listeners
  document.querySelectorAll('.filter-tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
      document.querySelectorAll('.filter-tab').forEach(t => {
        t.style.background = 'transparent';
        t.style.color = 'var(--text-muted)';
        t.classList.remove('active');
        t.style.boxShadow = 'none';
        t.style.fontWeight = '500';
      });
      const el = e.target;
      el.style.background = '#fff';
      el.style.color = 'var(--primary)';
      el.classList.add('active');
      el.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
      el.style.fontWeight = '600';

      currentTab = el.getAttribute('data-tab');
      applyFilters();
    });
  });

  // Navigation functions for Mockups
  window.viewHoSoDetail = function(id) {
    const hs = MOCK_HO_SO.find(h => h.id === id);
    if (!hs) return;
    
    document.getElementById('hoSoListView').style.display = 'none';
    document.getElementById('vanBanDetailView').style.display = 'none';
    const detailView = document.getElementById('hoSoDetailView');
    detailView.style.display = 'block';

    const statusBg = hs.trangThai === 'Hiện hành' ? '#DCFCE7' : '#E2E8F0';
    const statusColor = hs.trangThai === 'Hiện hành' ? '#166534' : '#475569';

    detailView.innerHTML = `
      <div class="breadcrumb-bar" style="margin-bottom:24px;">
        <a href="#" onclick="window.backToList()" style="text-decoration:none; color:var(--text-muted);"><svg width="14" height="14" viewBox="0 0 24 24" style="vertical-align:middle;margin-right:4px;"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>Hồ sơ văn bản</a>
        <span class="breadcrumb-sep" style="margin:0 8px; color:var(--text-muted);">›</span><span style="color:var(--text-main); font-weight:500;">Chi tiết hồ sơ văn bản</span>
      </div>

      <div style="background:#fff; border:1px solid var(--border-color); border-radius:4px; padding:24px; box-shadow:0 1px 3px rgba(0,0,0,0.05); margin-bottom:24px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
          <h3 style="color:var(--primary); font-size:16px; font-weight:700; border-left:4px solid var(--primary); padding-left:12px; margin:0; text-transform:uppercase;">THÔNG TIN HỒ SƠ VĂN BẢN</h3>
          <span style="background:${statusBg}; color:${statusColor}; padding:6px 16px; border-radius:20px; font-size:13px; font-weight:600;">${hs.trangThai}</span>
        </div>
        
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-bottom:24px;">
          <div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Tiêu đề hồ sơ</div>
              <div style="font-size:15px; color:var(--text-main); font-weight:500;">${hs.tenHoSo}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Ngày tạo hồ sơ</div>
              <div style="font-size:15px; color:var(--text-main);">${hs.ngayTao}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Đơn vị / Phòng ban</div>
              <div style="font-size:15px; color:var(--text-main);">${hs.donVi}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Mô tả</div>
              <div style="font-size:15px; color:var(--text-main);">${hs.moTa}</div>
            </div>
          </div>
          <div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Ký hiệu hồ sơ</div>
              <div style="font-size:15px; color:var(--text-main);">${hs.maHoSo}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Thời gian bảo quản</div>
              <div style="font-size:15px; color:var(--text-main);">${hs.thoiGianBaoQuan}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Quyền xử lý văn bản</div>
              <div style="font-size:15px; color:var(--text-main);">${hs.quyenXuLy}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Số năm lưu trữ</div>
              <div style="font-size:15px; color:var(--text-main);">${hs.soNamLuuTru || '—'}</div>
            </div>
          </div>
        </div>
        <hr style="border:none; border-top:1px solid var(--border-color); margin:24px 0;">
        <div style="font-size:14px; color:var(--text-main);">Văn thư: <span style="font-weight:700;">Phan Thanh Thảo</span></div>
      </div>

      <div style="background:#fff; border:1px solid var(--border-color); border-radius:4px; box-shadow:0 1px 3px rgba(0,0,0,0.05); overflow:hidden;">
        <h3 style="color:var(--primary); font-size:14px; font-weight:700; border-left:4px solid var(--primary); padding-left:12px; margin:24px 24px 16px 24px; text-transform:uppercase;">DANH SÁCH HỒ SƠ (2)</h3>
        <table class="data-table" style="border-top:1px solid var(--border-color);">
          <thead style="background:#F8FAFC;">
            <tr>
              <th class="text-center" style="width:60px;">STT</th>
              <th>Số ký hiệu</th>
              <th>Trích yếu</th>
              <th>Đơn vị ban hành</th>
              <th>Ngày văn bản</th>
              <th class="text-center">Thao tác</th>
            </tr>
          </thead>
          <tbody>
            <tr style="border-bottom:1px solid var(--border-color);">
              <td class="text-center">1</td>
              <td style="color:#0284C7; font-weight:600; cursor:pointer;" onclick="window.viewVanBanDetail(1, ${hs.id})">123/UBND</td>
              <td>Về việc triển khai kế hoạch năm 2024</td>
              <td>UBND Thành phố</td>
              <td>03/02/2025</td>
              <td class="text-center"><button class="btn btn-icon btn-sm" style="color:var(--text-muted); border:1px solid var(--border-color);"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg></button></td>
            </tr>
            <tr>
              <td class="text-center">2</td>
              <td style="color:#0284C7; font-weight:600; cursor:pointer;" onclick="window.viewVanBanDetail(2, ${hs.id})">VB.002/2026</td>
              <td>Báo cáo kết quả hoạt động quý I</td>
              <td>Phòng Hành chính</td>
              <td>2026-03-20</td>
              <td class="text-center"><button class="btn btn-icon btn-sm" style="color:var(--text-muted); border:1px solid var(--border-color);"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg></button></td>
            </tr>
          </tbody>
        </table>
      </div>
    `;
    window.scrollTo(0,0);
  };

  window.backToList = function() {
    document.getElementById('hoSoDetailView').style.display = 'none';
    document.getElementById('vanBanDetailView').style.display = 'none';
    document.getElementById('hoSoListView').style.display = 'block';
  };

  window.viewVanBanDetail = function(vbId, hsId) {
    const hs = MOCK_HO_SO.find(h => h.id === hsId);
    if (!hs) return;

    document.getElementById('hoSoDetailView').style.display = 'none';
    const vbView = document.getElementById('vanBanDetailView');
    vbView.style.display = 'block';

    const vbData = vbId === 1 
      ? { trchYeu: 'Về việc triển khai kế hoạch năm 2024', soKyHieu: '123/UBND', loai: 'Quyết định', donVi: 'UBND Thành phố', ngayVB: '03/02/2025', hinhThuc: 'Công văn', hanXL: '09/02/2026', ngayDen: '04/02/2026', doKhan: 'Bình thường', doMat: 'Bình thường' }
      : { trchYeu: 'Báo cáo kết quả hoạt động quý I', soKyHieu: 'VB.002/2026', loai: 'Báo cáo', donVi: 'Phòng Hành chính', ngayVB: '2026-03-20', hinhThuc: 'Công văn', hanXL: '2026-04-20', ngayDen: '2026-03-22', doKhan: 'Bình thường', doMat: 'Bình thường' };

    vbView.innerHTML = `
      <div class="breadcrumb-bar" style="margin-bottom:24px;">
        <a href="#" onclick="window.backToList()" style="text-decoration:none; color:var(--text-muted);"><svg width="14" height="14" viewBox="0 0 24 24" style="vertical-align:middle;margin-right:4px;"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>Hồ sơ văn bản</a>
        <span class="breadcrumb-sep" style="margin:0 8px; color:var(--text-muted);">›</span>
        <a href="#" onclick="window.viewHoSoDetail(${hsId})" style="text-decoration:none; color:var(--text-muted);">Chi tiết hồ sơ văn bản</a>
        <span class="breadcrumb-sep" style="margin:0 8px; color:var(--text-muted);">›</span>
        <span style="color:var(--text-main); font-weight:500;">Văn bản</span>
      </div>

      <div style="margin-bottom:24px;">
        <h1 style="font-size:24px; font-weight:700; color:var(--text-main); margin:0 0 8px 0;">Hồ sơ văn bản</h1>
        <div style="font-size:15px; color:var(--text-muted);">${hs.tenHoSo}</div>
      </div>

      <div style="background:#fff; border:1px solid var(--border-color); border-radius:4px; padding:24px; box-shadow:0 1px 3px rgba(0,0,0,0.05); margin-bottom:24px;">
        <h3 style="color:var(--primary); font-size:16px; font-weight:700; border-left:4px solid var(--primary); padding-left:12px; margin:0 0 24px 0; text-transform:uppercase;">THÔNG TIN VĂN BẢN</h3>
        
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:24px; margin-bottom:32px;">
          <div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Trích yếu</div>
              <div style="font-size:14px; color:var(--text-main); font-weight:500;">${vbData.trchYeu}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Đơn vị ban hành:</div>
              <div style="font-size:14px; color:var(--text-main);">${vbData.donVi}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Hình thức:</div>
              <div style="font-size:14px; color:var(--text-main);">${vbData.hinhThuc}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Ngày đến:</div>
              <div style="font-size:14px; color:var(--text-main);">${vbData.ngayDen}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Độ mật:</div>
              <div style="font-size:14px; color:var(--text-main);">${vbData.doMat}</div>
            </div>
          </div>
          <div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Số ký hiệu:</div>
              <div style="font-size:14px; color:var(--text-main);">${vbData.soKyHieu}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Loại văn bản:</div>
              <div style="font-size:14px; color:var(--text-main);">${vbData.loai}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Ngày văn bản:</div>
              <div style="font-size:14px; color:var(--text-main);">${vbData.ngayVB}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Hạn xử lý:</div>
              <div style="font-size:14px; color:var(--text-main);">${vbData.hanXL}</div>
            </div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Độ khẩn:</div>
              <div style="font-size:14px; color:var(--text-main);">${vbData.doKhan}</div>
            </div>
          </div>
          <div>
            <div style="margin-bottom:16px;">
              <div style="font-size:13px; color:var(--text-muted); margin-bottom:4px;">Lãnh đạo tiếp nhận:</div>
              <div style="font-size:14px; color:var(--text-main);">Phan Thanh Thảo</div>
            </div>
          </div>
        </div>

        <div style="background:#F1F5F9; border-radius:4px; padding:16px;">
          <div style="font-size:14px; font-weight:700; color:var(--primary); margin-bottom:8px;">Nội dung trình lãnh đạo:</div>
          <div style="font-size:14px; color:var(--text-main);">Kính trình lãnh đạo xem xét.</div>
        </div>
      </div>

      <div style="background:#fff; border:1px solid var(--border-color); border-radius:4px; box-shadow:0 1px 3px rgba(0,0,0,0.05); padding:24px;">
        <h3 style="color:var(--primary); font-size:16px; font-weight:700; border-left:4px solid var(--primary); padding-left:12px; margin:0 0 24px 0; text-transform:uppercase;">DANH SÁCH VĂN BẢN</h3>
        
        <div style="margin-bottom:24px;">
          <div style="font-size:13px; color:var(--text-muted); margin-bottom:8px;">File đính kèm:</div>
          <div style="display:inline-flex; align-items:center; gap:12px; padding:12px 16px; border:1px solid var(--border-color); border-radius:4px;">
             <div style="background:#FEE2E2; color:#DC2626; font-size:12px; font-weight:bold; padding:4px 8px; border-radius:4px;">PDF</div>
             <div>
                <div style="font-size:14px; font-weight:600; color:var(--text-main);">CV_1735_CT_CS.pdf</div>
                <div style="font-size:12px; color:var(--text-muted);">PDF Document</div>
             </div>
          </div>
        </div>

        <div style="margin-bottom:24px;">
          <div style="font-size:13px; color:var(--text-muted); margin-bottom:8px;">Xem trước</div>
          <!-- Mock PDF Viewer -->
          <div style="border:1px solid #333; background:#475569; border-radius:4px; overflow:hidden;">
            <div style="background:#334155; color:#fff; padding:8px 16px; display:flex; justify-content:space-between; align-items:center; font-size:13px;">
              <span>CV_1735_CT_CS.pdf</span>
              <div style="display:flex; align-items:center; gap:16px;">
                <span>1 / 1</span>
                <span>- +</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M19 8H5c-1.66 0-3 1.34-3 3v6h4v4h12v-4h4v-6c0-1.66-1.34-3-3-3zm-3 11H8v-5h8v5zm3-7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm-1-9H6v4h12V3z"/></svg>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
              </div>
            </div>
            <div style="padding:40px; text-align:center; height:400px; display:flex; justify-content:center; overflow-y:auto;">
               <div style="background:#fff; width:100%; max-width:600px; height:600px; box-shadow:0 4px 12px rgba(0,0,0,0.1); padding:40px; text-align:left; color:#000;">
                  <h2 style="font-size:14px;text-align:center;margin-bottom:20px;">BỘ TÀI CHÍNH<br>CỤC THUẾ</h2>
                  <p style="font-size:12px;text-align:justify;">Kính gửi: Các chỉ cục Thuế khu vực.<br><br>Ghi chú nội dung xem trước giả lập...</p>
               </div>
            </div>
          </div>
        </div>

        <div>
          <div style="font-size:13px; color:var(--text-muted); margin-bottom:8px;">Tài liệu liên quan:</div>
          <div style="font-size:14px; color:var(--text-main); font-style:italic;">Không có tài liệu liên quan.</div>
        </div>
      </div>
    `;
    window.scrollTo(0,0);
  };

  document.getElementById('btnThemHoSo')?.addEventListener('click', () => {
    editingId = null;
    document.getElementById('modalHSTitle').textContent = 'Thêm hồ sơ mới';
    ['hsMaHoSo','hsTenHoSo','hsMoTa'].forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
    document.getElementById('hsTrangThai').selectedIndex = 0;
    openModal('modalHoSo');
  });

  document.getElementById('btnSaveHoSo')?.addEventListener('click', () => {
    const maHS = document.getElementById('hsMaHoSo')?.value.trim();
    const tenHS = document.getElementById('hsTenHoSo')?.value.trim();
    if (!maHS || !tenHS) { showToast('Vui lòng điền mã và tên hồ sơ.', 'error'); return; }

    if (editingId) {
      const idx = MOCK_HO_SO.findIndex(h => h.id === editingId);
      if (idx !== -1) { MOCK_HO_SO[idx].maHoSo = maHS; MOCK_HO_SO[idx].tenHoSo = tenHS; MOCK_HO_SO[idx].moTa = document.getElementById('hsMoTa')?.value || ''; }
      showToast('Cập nhật hồ sơ thành công!', 'success');
    } else {
      MOCK_HO_SO.unshift({ id: MOCK_HO_SO.length + 1, maHoSo: maHS, tenHoSo: tenHS, moTa: document.getElementById('hsMoTa')?.value || '', ngayTao: '2026-03-25', nguoiTao: user.name, trangThai: document.getElementById('hsTrangThai')?.value || 'Đang mở', soVanBan: 0 });
      showToast('Thêm hồ sơ thành công!', 'success');
    }
    closeModal('modalHoSo');
    filteredData = [...MOCK_HO_SO];
    renderTable();
  });

  window.viewHoSo = function (id) {
    const hs = MOCK_HO_SO.find(h => h.id === id);
    if (hs) alert(`Hồ sơ: ${hs.maHoSo}\nTên: ${hs.tenHoSo}\nSố VB: ${hs.soVanBan}\nNgày tạo: ${formatDate(hs.ngayTao)}`);
  };

  window.editHoSo = function (id) {
    const hs = MOCK_HO_SO.find(h => h.id === id);
    if (!hs) return;
    editingId = id;
    document.getElementById('modalHSTitle').textContent = 'Chỉnh sửa hồ sơ';
    document.getElementById('hsMaHoSo').value = hs.maHoSo;
    document.getElementById('hsTenHoSo').value = hs.tenHoSo;
    document.getElementById('hsMoTa').value = hs.moTa;
    openModal('modalHoSo');
  };

  window.deleteHoSo = function (id) {
    showConfirm('Xác nhận xóa hồ sơ', 'Bạn có chắc chắn muốn xóa hồ sơ này?', () => {
      const idx = MOCK_HO_SO.findIndex(h => h.id === id);
      if (idx !== -1) MOCK_HO_SO.splice(idx, 1);
      filteredData = filteredData.filter(h => h.id !== id);
      renderTable();
      showToast('Đã xóa hồ sơ.', 'success');
    });
  };

  window.openThemVBModal = function (hoSoId) {
    document.getElementById('themVbHoSoId').value = hoSoId;
    openModal('modalThemVB');
  };

  document.getElementById('btnThemVBVaoHS')?.addEventListener('click', () => {
    const hoSoId = parseInt(document.getElementById('themVbHoSoId')?.value);
    const selDen = document.getElementById('selectVBDen')?.value;
    const selDi = document.getElementById('selectVBDi')?.value;
    if (!selDen && !selDi) { showToast('Vui lòng chọn văn bản để thêm vào hồ sơ.', 'error'); return; }
    const hs = MOCK_HO_SO.find(h => h.id === hoSoId);
    if (hs) { hs.soVanBan += 1; filteredData = [...MOCK_HO_SO]; renderTable(); }
    closeModal('modalThemVB');
    showToast('Đã thêm văn bản vào hồ sơ thành công!', 'success');
  });

  // ==========================================
  // CUSTOM POPUP 1: CHỌN PHÒNG BAN
  // ==========================================
  const phongBanTrigger = document.getElementById('phongBanTrigger');
  const popupPhongBan = document.getElementById('popupPhongBan');
  const phongBanText = document.getElementById('phongBanText');
  const chkAllPhongBan = document.getElementById('chkAllPhongBan');
  const chkPhongBanItems = document.querySelectorAll('.chkPhongBanItem');

  if (phongBanTrigger && popupPhongBan) {
    phongBanTrigger.addEventListener('click', (e) => {
      e.stopPropagation();
      popupPhongBan.style.display = popupPhongBan.style.display === 'none' ? 'block' : 'none';
    });

    document.addEventListener('click', (e) => {
      if (!phongBanTrigger.contains(e.target) && !popupPhongBan.contains(e.target)) {
        popupPhongBan.style.display = 'none';
      }
    });

    const updatePhongBanText = () => {
      const checkedVals = Array.from(chkPhongBanItems).filter(c => c.checked).map(c => c.value);
      if (checkedVals.length === 0) {
        phongBanText.textContent = '-- Chọn đơn vị --';
        phongBanText.style.color = 'var(--text-muted)';
      } else {
        phongBanText.textContent = checkedVals.join(', ');
        phongBanText.style.color = 'var(--text-main)';
      }
      chkAllPhongBan.checked = checkedVals.length === chkPhongBanItems.length;
    };

    chkAllPhongBan?.addEventListener('change', (e) => {
      chkPhongBanItems.forEach(c => c.checked = e.target.checked);
      updatePhongBanText();
    });

    chkPhongBanItems.forEach(c => c.addEventListener('change', updatePhongBanText));
  }

  // ==========================================
  // CUSTOM POPUP 2: CHỌN NGƯỜI XỬ LÝ (TREE DATA)
  // ==========================================
  const treeData = [
    {
      id: "pkd", name: "Phòng Ban Kế Toán (04)", isOpen: true,
      members: [
        { id: "m1", name: "Trần Danh Việt", role: "Kế toán trưởng", phone: "0913.256.768", email: "viettd@vnpt.vn" },
        { id: "m2", name: "Phạm Thị Phương Thảo", role: "Kế toán viên", phone: "0914.135.555", email: "thaoptp@vnpt.vn" },
        { id: "m3", name: "Nguyễn Hoàng Nam", role: "Kế toán tổng hợp", phone: "0941.223.456", email: "namnh@vnpt.vn" },
        { id: "m4", name: "Lê Thị Mai", role: "Văn thư", phone: "0888.123.999", email: "maitp@vnpt.vn" }
      ]
    },
    {
      id: "pns", name: "Phòng Nhân Sự (03)", isOpen: false,
      members: [
        { id: "m5", name: "Nguyễn Văn A", role: "Trưởng phòng", phone: "0901.123.123", email: "vana@vnpt.vn" },
        { id: "m6", name: "Trần Thị B", role: "Chuyên viên", phone: "0902.234.234", email: "thib@vnpt.vn" }
      ]
    },
    {
      id: "cntt", name: "Trung Tâm Công Nghệ Thông Tin (05)", isOpen: false,
      members: [
        { id: "m7", name: "Lê Văn C", role: "Kỹ sư", phone: "0903.345.345", email: "vanc@vnpt.vn" }
      ]
    }
  ];

  let modalSelectedMembers = new Set();
  let globalSelectedMembers = new Map(); // Store full member obj for chips

  const tbodyNguoiXuLy = document.getElementById('tbodyNguoiXuLy');
  const chkAllNguoiXuLy = document.getElementById('chkAllNguoiXuLy');
  const searchInputNguoiXuLy = document.getElementById('searchInputNguoiXuLy');
  const countNguoiXuLy = document.getElementById('countNguoiXuLy');

  function renderNguoiXuLyTable() {
    if (!tbodyNguoiXuLy) return;
    const keyword = searchInputNguoiXuLy.value.toLowerCase();
    
    let html = '';
    let totalVisibleMembers = 0;
    let selectedVisibleCount = 0;

    treeData.forEach(group => {
      // Filter members
      const filteredMembers = group.members.filter(m => 
        m.name.toLowerCase().includes(keyword) || 
        m.email.toLowerCase().includes(keyword) || 
        m.phone.includes(keyword)
      );
      
      if (filteredMembers.length === 0 && keyword !== "") return; // Hide group if no match during search

      const isGroupExpanded = keyword !== "" ? true : group.isOpen;
      const groupMembersSelected = filteredMembers.filter(m => modalSelectedMembers.has(m.id)).length;
      const isGroupAllSelected = filteredMembers.length > 0 && groupMembersSelected === filteredMembers.length;
      
      // Group Row
      html += `
        <tr style="background:#F1F5F9; border-bottom:1px solid var(--border-color);">
          <td style="padding:12px 16px; text-align:center;">
             <button onclick="toggleTreeGroup('${group.id}')" style="background:#fff; border:1px solid #CBD5E1; color:#333; width:20px; height:20px; font-weight:bold; cursor:pointer; line-height:16px;">${isGroupExpanded ? '-' : '+'}</button>
          </td>
          <td colspan="4" style="padding:12px 16px;">
             <label style="font-weight:700; font-size:14px; display:flex; align-items:center; gap:12px; cursor:pointer; margin:0;">
               <input type="checkbox" style="width:16px;height:16px;" ${isGroupAllSelected ? 'checked' : ''} onchange="toggleGroupSelection('${group.id}', this.checked)">
               ${group.name}
             </label>
          </td>
        </tr>
      `;

      if (isGroupExpanded) {
        filteredMembers.forEach(m => {
          totalVisibleMembers++;
          const isSelected = modalSelectedMembers.has(m.id);
          if (isSelected) selectedVisibleCount++;

          html += `
            <tr style="border-bottom:1px solid var(--border-color); background:#fff;">
              <td style="padding:12px 16px; text-align:center;"></td>
              <td style="padding:12px 16px;">
                <label style="display:flex; align-items:center; gap:12px; cursor:pointer; margin:0; font-size:14px;">
                  <input type="checkbox" style="width:16px;height:16px;" ${isSelected ? 'checked' : ''} onchange="toggleMemberSelection('${m.id}', this.checked)">
                  ${m.name}
                </label>
              </td>
              <td style="padding:12px 16px; font-size:14px; color:var(--text-main);">${m.role}</td>
              <td style="padding:12px 16px; font-size:14px; color:var(--text-main);">${m.phone}</td>
              <td style="padding:12px 16px; font-size:14px; color:var(--text-main);">${m.email}</td>
            </tr>
          `;
        });
      }
    });

    tbodyNguoiXuLy.innerHTML = html;
    countNguoiXuLy.textContent = modalSelectedMembers.size;
    chkAllNguoiXuLy.checked = totalVisibleMembers > 0 && selectedVisibleCount === totalVisibleMembers;
  }

  window.toggleTreeGroup = function(groupId) {
    const group = treeData.find(g => g.id === groupId);
    if (group) { group.isOpen = !group.isOpen; renderNguoiXuLyTable(); }
  };

  window.toggleGroupSelection = function(groupId, isChecked) {
    const keyword = searchInputNguoiXuLy.value.toLowerCase();
    const group = treeData.find(g => g.id === groupId);
    if (group) {
      group.members.forEach(m => {
        if (keyword && !m.name.toLowerCase().includes(keyword) && !m.email.toLowerCase().includes(keyword) && !m.phone.includes(keyword)) return;
        if (isChecked) modalSelectedMembers.add(m.id);
        else modalSelectedMembers.delete(m.id);
      });
      renderNguoiXuLyTable();
    }
  };

  window.toggleMemberSelection = function(memberId, isChecked) {
    if (isChecked) modalSelectedMembers.add(memberId);
    else modalSelectedMembers.delete(memberId);
    renderNguoiXuLyTable();
  };

  chkAllNguoiXuLy?.addEventListener('change', (e) => {
    const isChecked = e.target.checked;
    const keyword = searchInputNguoiXuLy.value.toLowerCase();
    treeData.forEach(group => {
      group.members.forEach(m => {
        if (keyword && !m.name.toLowerCase().includes(keyword) && !m.email.toLowerCase().includes(keyword) && !m.phone.includes(keyword)) return;
        if (isChecked) modalSelectedMembers.add(m.id);
        else modalSelectedMembers.delete(m.id);
      });
    });
    renderNguoiXuLyTable();
  });

  searchInputNguoiXuLy?.addEventListener('input', renderNguoiXuLyTable);

  const nguoiXuLyTrigger = document.getElementById('nguoiXuLyTrigger');
  const modalChonNguoiXuLy = document.getElementById('modalChonNguoiXuLy');
  const nguoiXuLyChipsContainer = document.getElementById('nguoiXuLyChipsContainer');

  nguoiXuLyTrigger?.addEventListener('click', (e) => {
    // Cannot open if clicking a remove chip
    if (e.target.tagName.toLowerCase() === 'svg' || e.target.closest('span')) return;
    
    // reset modal state to match global
    modalSelectedMembers = new Set(globalSelectedMembers.keys());
    searchInputNguoiXuLy.value = '';
    
    modalChonNguoiXuLy.style.display = 'flex';
    renderNguoiXuLyTable();
  });

  window.closeModalNguoiXuLy = function() {
    modalChonNguoiXuLy.style.display = 'none';
  };
  
  // Close on outside click
  modalChonNguoiXuLy?.addEventListener('click', (e) => {
      if (e.target === modalChonNguoiXuLy) closeModalNguoiXuLy();
  });

  document.getElementById('btnSaveNguoiXuLy')?.addEventListener('click', () => {
    globalSelectedMembers.clear();
    treeData.forEach(group => {
      group.members.forEach(m => {
        if (modalSelectedMembers.has(m.id)) {
          globalSelectedMembers.set(m.id, m);
        }
      });
    });
    renderChips();
    closeModalNguoiXuLy();
  });

  function renderChips() {
    if (globalSelectedMembers.size === 0) {
      nguoiXuLyChipsContainer.innerHTML = '<span style="color:var(--text-muted);">-- Chọn danh sách --</span>';
      return;
    }
    
    let chipsHtml = '';
    globalSelectedMembers.forEach(m => {
      chipsHtml += `
        <div style="background:#E2ECF7; border:1px solid #CBD5E1; color:#334155; border-radius:16px; padding:2px 10px; font-size:13px; font-weight:500; display:inline-flex; align-items:center; gap:6px;">
          ${m.name}
          <span style="cursor:pointer; font-size:14px; font-weight:bold; color:#64748B;" onclick="removeChip('${m.id}', event)">&times;</span>
        </div>
      `;
    });
    nguoiXuLyChipsContainer.innerHTML = chipsHtml;
  }

  window.removeChip = function(memberId, event) {
    event.stopPropagation();
    globalSelectedMembers.delete(memberId);
    renderChips();
  };

  // Initial page render
  populateVBSelects();
  applyFilters();
  renderChips();

});
