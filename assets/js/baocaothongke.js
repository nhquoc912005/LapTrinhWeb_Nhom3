/**
 * baocaothongke.js - Bao cao thong ke
 */
document.addEventListener('DOMContentLoaded', function () {
  const user = requireAuth();
  if (!user) return;

  initReportPage();
});

const REPORT_DATA = {
  documents: {
    breadcrumb: 'Thống kê tình hình xử lý văn bản',
    leftChartTitle: 'Thống kê tổng hợp',
    rightChartTitle: 'Tỷ lệ trạng thái xử lý',
    filters: [
      { label: 'Từ ngày', required: true, type: 'date', value: '2026-01-31' },
      { label: 'Đến ngày', required: true, type: 'date', value: '2026-02-23' },
      { label: 'Loại văn bản', type: 'select', value: 'Tất cả', options: ['Tất cả', 'Quyết định', 'Công văn', 'Thông báo', 'Tờ trình'] },
      { label: 'Đơn vị ban hành', type: 'select', value: 'Tất cả', options: ['Tất cả', 'UBND Thành phố', 'Sở Tài chính', 'Bộ Tài chính'] },
      { label: 'Trạng thái xử lý', type: 'select', value: 'Tất cả', options: ['Tất cả', 'Đã hoàn thành', 'Chờ xử lý', 'Chờ duyệt'] },
      { label: 'Tiêu chí phân loại', type: 'select', value: 'Tổng hợp', options: ['Tổng hợp', 'Theo loại văn bản', 'Theo đơn vị'] }
    ],
    stats: [
      {
        label: 'Tổng số văn bản',
        value: '275',
        valueColor: '#0076A2',
        sub: '',
        iconBg: '#E0F2FE',
        iconColor: '#C2E3F3',
        icon: '<path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-6zm-1 2.5L17.5 10H13V4.5zM8 20V4h3v8h7v8H8z"/>' 
      },
      {
        label: 'Đúng hạn',
        value: '230',
        valueColor: '#16A34A',
        sub: '83.6%',
        iconBg: '#DBEAFE',
        iconColor: '#111827',
        icon: '<path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>'
      },
      {
        label: 'Trễ hạn',
        value: '22',
        valueColor: '#DC2626',
        sub: '8.0%',
        iconBg: '#FEE2E2',
        iconColor: '#EAB308',
        icon: '<path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>'
      }
    ],
    barChart: {
      labels: ['Quyết định', 'Công văn', 'Thông báo', 'Tờ trình'],
      datasets: [
        { label: 'Chờ duyệt', data: [5, 10, 5, 2], color: '#E63946' },
        { label: 'Chờ xử lý', data: [5, 10, 5, 3], color: '#FFB703' },
        { label: 'Đã hoàn thành', data: [35, 100, 70, 25], color: '#2EAD45' }
      ],
      suggestedMax: 100
    },
    pieChart: {
      values: [84, 8, 8],
      colors: ['#2EAD45', '#FFB703', '#E63946'],
      leftLegend: [
        { text: 'Đã hoàn thành: 84%', color: '#2EAD45' }
      ],
      rightLegend: [
        { text: 'Chờ xử lý: 8%', color: '#FFB703' },
        { text: 'Chờ duyệt: 8%', color: '#E63946' }
      ]
    },
    table: {
      headers: ['Loại văn bản', 'Tổng số', 'Đúng hạn', 'Trễ hạn', 'Chờ xử lý'],
      rows: [
        ['Quyết định', '45', { text: '35', color: '#16A34A' }, { text: '5', color: '#DC2626' }, { text: '5', color: '#D97706' }],
        ['Công văn', '120', { text: '100', color: '#16A34A' }, { text: '10', color: '#DC2626' }, { text: '10', color: '#D97706' }],
        ['Thông báo', '80', { text: '70', color: '#16A34A' }, { text: '5', color: '#DC2626' }, { text: '5', color: '#D97706' }],
        ['Tờ trình', '30', { text: '25', color: '#16A34A' }, { text: '2', color: '#DC2626' }, { text: '3', color: '#D97706' }]
      ]
    }
  },
  tasks: {
    breadcrumb: 'Thống kê kết quả thực hiện công việc',
    leftChartTitle: 'Thống kê theo cá nhân',
    rightChartTitle: 'Tỷ lệ trạng thái công việc',
    filters: [
      { label: 'Từ ngày', required: true, type: 'date', value: '2026-02-06' },
      { label: 'Đến ngày', required: true, type: 'date', value: '2026-02-27' },
      { label: 'Đối tượng thống kê', type: 'select', value: 'Đơn vị', options: ['Đơn vị', 'Cá nhân'] },
      { label: 'Phòng ban', type: 'select', value: 'Tất cả', options: ['Tất cả', 'Phòng Kế toán', 'Phòng Kiểm toán', 'Phòng Hành chính'] },
      { label: 'Trạng thái công việc', type: 'select', value: 'Tất cả', options: ['Tất cả', 'Đã hoàn thành', 'Đang thực hiện', 'Chờ xử lý', 'Hoàn trả'], spanTwo: true }
    ],
    stats: [
      {
        label: 'Tổng số công việc',
        value: '107',
        valueColor: '#0076A2',
        sub: '',
        iconBg: '#E0F2FE',
        iconColor: '#C2E3F3',
        icon: '<path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2zm0 2 1.4 2H20v10H4V6h6z"/>' 
      },
      {
        label: 'Đã hoàn thành',
        value: '82',
        valueColor: '#16A34A',
        sub: '76.6%',
        iconBg: '#DBEAFE',
        iconColor: '#111827',
        icon: '<path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>'
      },
      {
        label: 'Đang xử lý',
        value: '21',
        valueColor: '#F59E0B',
        sub: '19.6%',
        iconBg: '#FEF3C7',
        iconColor: '#64748B',
        icon: '<path d="M15.07 1 14 2.07 16.93 5 18 3.93 15.07 1zM11 8h2v6h-2zm1-6C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18a8 8 0 1 1 0-16 8 8 0 0 1 0 16z"/>'
      }
    ],
    barChart: {
      labels: [
        'Kiểm toán báo cáo tài chính Công ty ABC',
        'Tư vấn thuế TNCN cho khách hàng DEF',
        'Lập báo cáo thuế TNDN quý 4/2025',
        'Soát xét hồ sơ khai thuế Công ty GHI'
      ],
      datasets: [
        { label: 'Chờ xử lý', data: [2, 1, 2, 2], color: '#FFB703' },
        { label: 'Đang thực hiện', data: [3, 4, 3, 4], color: '#0076A2' },
        { label: 'Đã hoàn thành', data: [20, 25, 15, 22], color: '#2EAD45' }
      ],
      suggestedMax: 28
    },
    pieChart: {
      values: [77, 13, 7, 4],
      colors: ['#2EAD45', '#0076A2', '#FFB703', '#E63946'],
      leftLegend: [
        { text: 'Đã hoàn thành: 77%', color: '#2EAD45' }
      ],
      rightLegend: [
        { text: 'Đang thực hiện: 13%', color: '#0076A2' },
        { text: 'Chờ xử lý: 7%', color: '#FFB703' },
        { text: 'Hoàn trả: 4%', color: '#E63946' }
      ]
    },
    table: {
      headers: ['STT', 'Tên công việc', 'Tổng số', 'Đã hoàn thành', 'Đúng hạn', 'Trễ hạn', 'Tỷ lệ hoàn thành'],
      rows: [
        ['1', 'Kiểm toán báo cáo tài chính Công ty ABC', '25', { text: '20', color: '#16A34A' }, { text: '18', color: '#16A34A' }, { text: '2', color: '#DC2626' }, '80.0%'],
        ['2', 'Tư vấn thuế TNCN cho khách hàng DEF', '30', { text: '25', color: '#16A34A' }, { text: '23', color: '#16A34A' }, { text: '2', color: '#DC2626' }, '83.3%'],
        ['3', 'Lập báo cáo thuế TNDN quý 4/2025', '20', { text: '15', color: '#16A34A' }, { text: '13', color: '#16A34A' }, { text: '2', color: '#DC2626' }, '75.0%'],
        ['4', 'Soát xét hồ sơ khai thuế Công ty GHI', '28', { text: '22', color: '#16A34A' }, { text: '20', color: '#16A34A' }, { text: '2', color: '#DC2626' }, '78.6%']
      ]
    }
  }
};

let currentReportKey = 'documents';
let reportBarChartInstance = null;
let reportPieChartInstance = null;

function initReportPage() {
  const tabVanBan = document.getElementById('tabVanBan');
  const tabCongViec = document.getElementById('tabCongViec');
  const btnViewReport = document.getElementById('btnViewReport');

  tabVanBan?.addEventListener('click', function () {
    setReportMode('documents');
  });

  tabCongViec?.addEventListener('click', function () {
    setReportMode('tasks');
  });

  btnViewReport?.addEventListener('click', function () {
    renderCurrentReport();
    showToast('Đã cập nhật thống kê theo bộ lọc hiện tại.', 'success');
  });

  renderCurrentReport();
}

function setReportMode(mode) {
  if (currentReportKey === mode) return;
  currentReportKey = mode;
  renderCurrentReport();
}

function renderCurrentReport() {
  const config = REPORT_DATA[currentReportKey];
  if (!config) return;

  updateTabs();
  renderBreadcrumb(config);
  renderFilters(config);
  renderStats(config);
  renderCharts(config);
  renderTable(config);
}

function updateTabs() {
  const tabVanBan = document.getElementById('tabVanBan');
  const tabCongViec = document.getElementById('tabCongViec');

  updateTabButton(tabVanBan, currentReportKey === 'documents');
  updateTabButton(tabCongViec, currentReportKey === 'tasks');
}

function updateTabButton(button, active) {
  if (!button) return;
  button.classList.toggle('active', active);
  button.style.background = active ? '#fff' : 'transparent';
  button.style.color = active ? 'var(--primary)' : 'var(--text-muted)';
  button.style.boxShadow = active ? '0 1px 3px rgba(0,0,0,0.1)' : 'none';
  button.style.fontWeight = active ? '600' : '500';
}

function renderBreadcrumb(config) {
  const title = document.getElementById('reportBreadcrumbTitle');
  if (title) title.textContent = config.breadcrumb;
}

function renderFilters(config) {
  const grid = document.getElementById('reportFilterGrid');
  if (!grid) return;

  grid.innerHTML = `
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:22px 26px;">
      ${config.filters.map(renderFilterField).join('')}
    </div>
  `;
}

function renderFilterField(field) {
  const label = `${field.label}${field.required ? ' <span style="color:#DC2626">*</span>' : ''}`;
  const style = field.spanTwo ? 'grid-column:1 / -1;' : '';

  if (field.type === 'date') {
    return `
      <div style="${style}">
        <label style="display:block; font-size:13px; color:var(--text-secondary); margin-bottom:8px;">${label}</label>
        <input type="date" class="form-control" value="${field.value}" style="height:44px;">
      </div>
    `;
  }

  return `
    <div style="${style}">
      <label style="display:block; font-size:13px; color:var(--text-secondary); margin-bottom:8px;">${label}</label>
      <select class="form-control" style="height:44px;">
        ${field.options.map(function (option) {
          return `<option${option === field.value ? ' selected' : ''}>${option}</option>`;
        }).join('')}
      </select>
    </div>
  `;
}

function renderStats(config) {
  const container = document.getElementById('reportStatsGrid');
  if (!container) return;

  container.innerHTML = config.stats.map(function (item) {
    return `
      <div class="stat-card" style="padding:22px 24px; justify-content:space-between; min-height:128px;">
        <div class="stat-info">
          <div class="stat-label" style="font-size:13px; margin-bottom:10px;">${item.label}</div>
          <div class="stat-value" style="font-size:30px; color:${item.valueColor};">${item.value}</div>
          <div class="stat-sub" style="font-size:13px; margin-top:6px; color:#64748B;">${item.sub || '&nbsp;'}</div>
        </div>
        <div style="width:54px; height:54px; border-radius:50%; background:${item.iconBg}; color:${item.iconColor}; display:flex; align-items:center; justify-content:center; flex-shrink:0;">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">${item.icon}</svg>
        </div>
      </div>
    `;
  }).join('');
}

function renderCharts(config) {
  const leftTitle = document.getElementById('leftChartTitle');
  const rightTitle = document.getElementById('rightChartTitle');
  const pieLegendLeft = document.getElementById('pieLegendLeft');
  const pieLegendRight = document.getElementById('pieLegendRight');

  if (leftTitle) leftTitle.textContent = config.leftChartTitle;
  if (rightTitle) rightTitle.textContent = config.rightChartTitle;
  if (pieLegendLeft) pieLegendLeft.innerHTML = buildPieLegend(config.pieChart.leftLegend);
  if (pieLegendRight) pieLegendRight.innerHTML = buildPieLegend(config.pieChart.rightLegend);

  renderBarChart(config.barChart);
  renderPieChart(config.pieChart);
}

function buildPieLegend(items) {
  return items.map(function (item) {
    return `<div style="font-size:18px; line-height:1.7; color:${item.color}; white-space:nowrap;">${item.text}</div>`;
  }).join('');
}

function renderBarChart(config) {
  const canvas = document.getElementById('reportBarChart');
  if (!canvas || typeof Chart === 'undefined') return;

  if (reportBarChartInstance) {
    reportBarChartInstance.destroy();
  }

  reportBarChartInstance = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: config.labels,
      datasets: config.datasets.map(function (dataset) {
        return {
          label: dataset.label,
          data: dataset.data,
          backgroundColor: dataset.color,
          borderRadius: 0,
          maxBarThickness: 28
        };
      })
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            boxWidth: 16,
            boxHeight: 10,
            padding: 18,
            font: { family: 'Arimo', size: 12 }
          }
        }
      },
      scales: {
        x: {
          stacked: false,
          ticks: {
            color: '#4B5563',
            font: { family: 'Arimo', size: currentReportKey === 'tasks' ? 11 : 12 },
            maxRotation: 0,
            autoSkip: false
          },
          grid: { display: false }
        },
        y: {
          beginAtZero: true,
          suggestedMax: config.suggestedMax,
          ticks: {
            color: '#6B7280',
            font: { family: 'Arimo', size: 12 },
            stepSize: currentReportKey === 'documents' ? 25 : 7
          },
          grid: {
            color: '#D1D5DB',
            borderDash: [4, 4]
          }
        }
      }
    }
  });
}

function renderPieChart(config) {
  const canvas = document.getElementById('reportPieChart');
  if (!canvas || typeof Chart === 'undefined') return;

  if (reportPieChartInstance) {
    reportPieChartInstance.destroy();
  }

  reportPieChartInstance = new Chart(canvas, {
    type: 'pie',
    data: {
      labels: config.values.map(function (_, index) { return `Mục ${index + 1}`; }),
      datasets: [{
        data: config.values,
        backgroundColor: config.colors,
        borderColor: '#ffffff',
        borderWidth: 1,
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      }
    }
  });
}

function renderTable(config) {
  const thead = document.getElementById('reportTableHead');
  const tbody = document.getElementById('reportTableBody');
  if (!thead || !tbody) return;

  thead.innerHTML = `
    <tr>
      ${config.table.headers.map(function (header) {
        return `<th>${header}</th>`;
      }).join('')}
    </tr>
  `;

  tbody.innerHTML = config.table.rows.map(function (row) {
    return `
      <tr>
        ${row.map(renderTableCell).join('')}
      </tr>
    `;
  }).join('');
}

function renderTableCell(cell) {
  if (typeof cell === 'object' && cell !== null) {
    return `<td style="color:${cell.color}; font-weight:500;">${cell.text}</td>`;
  }
  return `<td>${cell}</td>`;
}
