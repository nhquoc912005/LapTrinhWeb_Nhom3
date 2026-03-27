/**
 * dashboard.js - Dashboard page logic
 */
document.addEventListener('DOMContentLoaded', function () {
  // Auth check
  const user = requireAuth();
  if (!user) return;

  renderStatsCards(user.role);
  renderRecentDocs();
  renderUrgentTasks();
  initBarChart();
  initDoughnutChart();
});

/* ============================================================
   STATS CARDS - Role-based display
   ============================================================ */
function renderStatsCards(role) {
  const container = document.getElementById('statsGrid');
  if (!container) return;

  // Common stats
  const allStats = [
    { icon: 'blue',   svg: '<path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>', label: 'Tổng văn bản đến', value: 371, sub: 'Trong tháng', trend: '+12.5%', up: true },
    { icon: 'teal',   svg: '<path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>', label: 'Tổng văn bản đi', value: 309, sub: 'Trong tháng', trend: '+8.3%', up: true },
    { icon: 'yellow', svg: '<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v4z"/>', label: 'Văn bản chờ xử lý', value: 73, sub: 'Cần xử lý gấp', trend: '+15.8%', up: false },
    { icon: 'red',    svg: '<path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>', label: 'Văn bản hoàn trả', value: 18, sub: 'Cần chỉnh sửa', trend: '-3.2%', up: true },
    { icon: 'green',  svg: '<path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>', label: 'Văn bản đã ban hành', value: 45, sub: 'Trong tháng', trend: '+5.7%', up: true },
    { icon: 'indigo', svg: '<path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>', label: 'Công việc đang xử lý', value: 68, sub: 'Đang thực hiện', trend: '+18.4%', up: true },
    { icon: 'green',  svg: '<path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>', label: 'Công việc hoàn thành', value: 531, sub: 'Tỷ lệ: 82.5%', trend: '+18.4%', up: true },
    { icon: 'orange', svg: '<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v4z"/>', label: 'Công việc trễ hạn', value: 12, sub: 'Cần xử lý ngay', trend: '-5.1%', up: true },
  ];

  // Role-specific order
  let statsToShow = [];
  if (role === 'lanhdao') {
    statsToShow = [allStats[0], allStats[1], allStats[2], allStats[3], allStats[5], allStats[6], allStats[7], allStats[4]];
  } else if (role === 'vanthu') {
    statsToShow = [allStats[0], allStats[1], allStats[2], allStats[4], allStats[3], allStats[5], allStats[6], allStats[7]];
  } else {
    // chuyenvien
    statsToShow = [allStats[5], allStats[6], allStats[7], allStats[2], allStats[0], allStats[1], allStats[3], allStats[4]];
  }

  container.innerHTML = statsToShow.map(s => `
    <div class="stat-card">
      <div class="stat-icon stat-icon-${s.icon}">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="white">${s.svg}</svg>
      </div>
      <div class="stat-info">
        <div class="stat-label">${s.label}</div>
        <div class="stat-value">${s.value.toLocaleString('vi-VN')}</div>
        <div class="stat-sub">${s.sub}</div>
      </div>
      <div class="stat-trend ${s.up ? 'up' : 'down'}">${s.trend}</div>
    </div>
  `).join('');
}

/* ============================================================
   RECENT DOCUMENTS
   ============================================================ */
function renderRecentDocs() {
  const container = document.getElementById('recentDocsList');
  if (!container) return;

  const recentDocs = MOCK_VAN_BAN_DEN.slice(0, 5);
  container.innerHTML = recentDocs.map(doc => `
    <div class="widget-list-item">
      <div>
        <div class="widget-item-title">
          <a href="van-ban-den.html" style="color:var(--primary);">${doc.soKyHieu}</a>
          — ${doc.trichYeu.length > 50 ? doc.trichYeu.slice(0, 50) + '...' : doc.trichYeu}
        </div>
        <div class="widget-item-sub">${formatDate(doc.ngayDen)} · ${doc.donViBanHanh}</div>
      </div>
      <div class="widget-item-meta">
        ${renderBadge(doc.trangThai)}
      </div>
    </div>
  `).join('');
}

/* ============================================================
   URGENT TASKS
   ============================================================ */
function renderUrgentTasks() {
  const container = document.getElementById('urgentTasksList');
  if (!container) return;

  const urgent = MOCK_CONG_VIEC
    .filter(cv => cv.trangThai !== 'da-hoan-thanh')
    .slice(0, 4);

  const priorityMap = { 'qua-han': 'Cao', 'dang-xu-ly': 'Cao', 'cho-xu-ly': 'Trung bình' };
  const priorityColor = { 'Cao': '#EF4444', 'Trung bình': '#F59E0B' };

  container.innerHTML = urgent.map(cv => {
    const p = priorityMap[cv.trangThai] || 'Trung bình';
    return `
    <div class="widget-list-item">
      <div>
        <div class="widget-item-title">${cv.tenCongViec}</div>
        <div class="widget-item-sub">Người thực hiện: ${cv.nguoiThucHien}</div>
        <div class="widget-item-sub">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="var(--text-muted)" style="vertical-align:middle;"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67V7z"/></svg>
          Hạn: ${formatDate(cv.hanXuLy)} ${deadlineBadge(cv.hanXuLy)}
        </div>
      </div>
      <div class="widget-item-meta">
        <span class="badge" style="background:${priorityColor[p]}20;color:${priorityColor[p]};">${p}</span>
      </div>
    </div>`;
  }).join('');
}

/* ============================================================
   BAR CHART - Chart.js
   ============================================================ */
function initBarChart() {
  const ctx = document.getElementById('barChart');
  if (!ctx) return;

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'],
      datasets: [
        { label: 'Công việc',   data: [14, 18, 12, 20, 15, 8, 5],  backgroundColor: '#F59E0B', borderRadius: 4 },
        { label: 'Văn bản đi',  data: [8,  11, 10, 13, 14, 4, 5],  backgroundColor: '#10B981', borderRadius: 4 },
        { label: 'Văn bản đến', data: [15, 15, 12, 16, 15, 8, 6],  backgroundColor: '#0076A2', borderRadius: 4 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { font: { family: 'Arimo', size: 12 }, padding: 16 } }
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { family: 'Arimo' } } },
        y: { beginAtZero: true, grid: { color: '#f1f3f5' }, ticks: { font: { family: 'Arimo' } } }
      }
    }
  });
}

/* ============================================================
   DOUGHNUT CHART - Chart.js
   ============================================================ */
function initDoughnutChart() {
  const ctx = document.getElementById('doughnutChart');
  if (!ctx) return;

  const data = { labels: ['Chờ xử lý', 'Đã duyệt', 'Hoàn trả', 'Đã hoàn thành'], values: [73, 531, 18, 45] };
  const colors = ['#F59E0B', '#10B981', '#EF4444', '#0076A2'];

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.labels,
      datasets: [{ data: data.values, backgroundColor: colors, borderWidth: 2, borderColor: 'white', hoverOffset: 6 }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.raw}` } }
      },
      cutout: '65%'
    }
  });

  // Custom legend
  const legend = document.getElementById('doughnutLegend');
  if (legend) {
    const total = data.values.reduce((a, b) => a + b, 0);
    legend.innerHTML = data.labels.map((label, i) => `
      <div style="display:flex;align-items:center;justify-content:space-between;padding:4px 0;font-size:13px;">
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="width:12px;height:12px;border-radius:3px;background:${colors[i]};flex-shrink:0;display:inline-block;"></span>
          ${label}
        </div>
        <span style="font-weight:700;color:var(--text-main);">${data.values[i]}</span>
      </div>`).join('');
  }
}
