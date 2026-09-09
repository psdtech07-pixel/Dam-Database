let globalData = null;
let filteredRecords = [];
let currentPage = 1;
const pageSize = 20;

let trendChartInstance = null;
let volumeChartInstance = null;
let currentChartDays = 30;

document.addEventListener('DOMContentLoaded', () => {
  initDashboard();
});

async function initDashboard() {
  try {
    const resp = await fetch('dam_data.json?v=' + Date.now(), { cache: 'no-store' });
    if (!resp.ok) throw new Error('Failed to load dam_data.json');
    globalData = await resp.json();
    
    // Sort all records descending (newest dates first for log table)
    filteredRecords = [...(globalData.all_records || [])].reverse();

    if (document.getElementById('totalRecordsBadge')) {
      document.getElementById('totalRecordsBadge').innerText = (globalData.total_records || filteredRecords.length).toLocaleString();
    }
    
    renderKPIs();
    renderDamCards();
    renderTrendChart(currentChartDays);
    renderVolumeChart();
    renderTable();
  } catch (err) {
    console.error('Error initializing dashboard:', err);
    document.getElementById('lastUpdatedText').innerText = 'Offline Mode';
  }
}

function renderKPIs() {
  if (!globalData || !globalData.latest) return;
  
  let totalLive = 0;
  let totalDesign = 0;
  let totalPctSum = 0;
  let totalLastYearSum = 0;
  let count = 0;

  const latest = globalData.latest;
  const dams = Object.keys(latest);

  dams.forEach(dam => {
    const d = latest[dam];
    totalLive += d.current_live_mcm || 0;
    totalDesign += d.design_live_mcm || 0;
    totalPctSum += d.current_pct || 0;
    totalLastYearSum += d.last_year_pct || 0;
    count++;

    // Update Header Date
    if (d.date) {
      document.getElementById('lastUpdatedText').innerText = `Report Date: ${d.date}`;
    }
  });

  const avgPct = count > 0 ? (totalPctSum / count).toFixed(1) : 0;
  const avgLastYear = count > 0 ? (totalLastYearSum / count).toFixed(1) : 0;
  const diff = (avgPct - avgLastYear).toFixed(1);

  document.getElementById('kpiTotalLive').innerHTML = `${totalLive.toFixed(1)} <span class="unit">MCM</span>`;
  document.getElementById('kpiTotalDesign').innerHTML = `${totalDesign.toFixed(1)} <span class="unit">MCM</span>`;
  document.getElementById('kpiAvgPct').innerText = `${avgPct}%`;

  const diffEl = document.getElementById('kpiYoYDiff');
  if (diff >= 0) {
    diffEl.innerHTML = `<span class="badge-positive">+${diff}%</span> vs Same Date Last Year (${avgLastYear}%)`;
  } else {
    diffEl.innerHTML = `<span style="color: var(--accent-rose); font-weight:600;">${diff}%</span> vs Same Date Last Year (${avgLastYear}%)`;
  }
}

function getTagDetails(pct) {
  if (pct >= 95) return { text: 'Full', class: 'tag-full' };
  if (pct >= 70) return { text: 'High', class: 'tag-good' };
  if (pct >= 40) return { text: 'Moderate', class: 'tag-moderate' };
  return { text: 'Low', class: 'tag-low' };
}

function getProgressColor(pct) {
  if (pct >= 95) return '#10b981';
  if (pct >= 70) return '#0284c7';
  if (pct >= 40) return '#f59e0b';
  return '#f43f5e';
}

function renderDamCards() {
  const grid = document.getElementById('damCardsGrid');
  if (!globalData || !globalData.latest) return;

  const latest = globalData.latest;
  const dams = ['Khadakwasla', 'Panshet', 'Mulshi', 'Gunjawani', 'Temghar'];

  let html = '';
  dams.forEach(dam => {
    const d = latest[dam];
    if (!d) return;

    const tag = getTagDetails(d.current_pct);
    const barColor = getProgressColor(d.current_pct);

    html += `
      <div class="dam-card">
        <div class="dam-header">
          <div>
            <div class="dam-name">${dam} Dam</div>
            <div class="dam-capacity-sub">Capacity: ${d.design_live_mcm} MCM</div>
          </div>
          <span class="dam-tag ${tag.class}">${tag.text}</span>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:4px;">
          <div style="font-size:28px; font-weight:700; color:var(--text-primary); letter-spacing:-0.02em;">
            ${d.current_pct}%
          </div>
          <div style="font-size:13px; color:var(--text-secondary);">
            <strong style="color:var(--text-primary);">${d.current_live_mcm}</strong> / ${d.design_live_mcm} MCM
          </div>
        </div>

        <div class="progress-bar-bg">
          <div class="progress-bar-fill" style="width: ${Math.min(100, d.current_pct)}%; background: ${barColor}"></div>
        </div>

        <div class="dam-footer-metrics">
          <span>Gross: ${d.current_gross_mcm} MCM</span>
          <span>Last Year: ${d.last_year_pct}%</span>
        </div>
      </div>
    `;
  });

  grid.innerHTML = html;
}

function setChartDays(days, btnEl) {
  currentChartDays = days;
  document.querySelectorAll('.pill-nav .pill-btn').forEach(b => b.classList.remove('active'));
  if (btnEl) btnEl.classList.add('active');
  renderTrendChart(days);
}

function renderTrendChart(days = currentChartDays) {
  const ctx = document.getElementById('trendChart').getContext('2d');
  if (!globalData || !globalData.time_series) return;

  const damFilterEl = document.getElementById('chartDamFilter');
  const selectedDam = damFilterEl ? damFilterEl.value : 'ALL';

  let slice = globalData.time_series;
  if (days !== 'all' && typeof days === 'number') {
    slice = globalData.time_series.slice(-days);
  }

  const labels = slice.map(s => s.date_fmt || s.date);

  const colors = {
    'Khadakwasla': '#38bdf8',
    'Panshet': '#10b981',
    'Mulshi': '#a855f7',
    'Gunjawani': '#f59e0b',
    'Temghar': '#f43f5e'
  };

  let datasets = [];

  if (selectedDam === 'ALL') {
    datasets = ['Khadakwasla', 'Panshet', 'Mulshi', 'Gunjawani', 'Temghar'].map(dam => {
      return {
        label: dam,
        data: slice.map(s => s[`${dam}_pct`]),
        borderColor: colors[dam],
        backgroundColor: 'transparent',
        borderWidth: 2,
        tension: 0.25,
        pointRadius: slice.length > 150 ? 0 : 2,
        pointHoverRadius: 5
      };
    });
  } else {
    const damColor = colors[selectedDam] || '#38bdf8';
    
    const gradient = ctx.createLinearGradient(0, 0, 0, 260);
    gradient.addColorStop(0, damColor + '30');
    gradient.addColorStop(1, damColor + '00');

    datasets = [{
      label: `${selectedDam} Storage Level (%)`,
      data: slice.map(s => s[`${selectedDam}_pct`]),
      borderColor: damColor,
      backgroundColor: gradient,
      fill: true,
      borderWidth: 2.5,
      tension: 0.25,
      pointRadius: slice.length > 150 ? 0 : 3,
      pointHoverRadius: 6
    }];
  }

  if (trendChartInstance) {
    trendChartInstance.destroy();
  }

  trendChartInstance = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'top',
          labels: { color: '#9ca3af', font: { family: 'Inter', size: 12 }, usePointStyle: true, boxWidth: 6 }
        },
        tooltip: {
          backgroundColor: '#111827',
          titleColor: '#f9fafb',
          bodyColor: '#d1d5db',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y !== null && ctx.parsed.y !== undefined ? ctx.parsed.y.toFixed(1) : 'N/A'}%`
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: { color: '#6b7280', font: { size: 11 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 8 }
        },
        y: {
          min: 0,
          max: 100,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#6b7280', font: { size: 11 }, callback: (v) => v + '%' }
        }
      }
    }
  });
}

function renderVolumeChart() {
  const ctx = document.getElementById('volumeChart').getContext('2d');
  if (!globalData || !globalData.latest) return;

  const latest = globalData.latest;
  const dams = ['Khadakwasla', 'Panshet', 'Mulshi', 'Gunjawani', 'Temghar'];

  const currentLive = dams.map(d => latest[d] ? latest[d].current_live_mcm : 0);
  const remaining = dams.map(d => latest[d] ? Math.max(0, latest[d].design_live_mcm - latest[d].current_live_mcm) : 0);

  if (volumeChartInstance) {
    volumeChartInstance.destroy();
  }

  volumeChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: dams,
      datasets: [
        {
          label: 'Stored (MCM)',
          data: currentLive,
          backgroundColor: '#0284c7',
          borderRadius: 4
        },
        {
          label: 'Remaining (MCM)',
          data: remaining,
          backgroundColor: 'rgba(255, 255, 255, 0.08)',
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          stacked: true,
          grid: { display: false },
          ticks: { color: '#9ca3af', font: { family: 'Inter', size: 11 } }
        },
        y: {
          stacked: true,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#6b7280', font: { size: 11 } }
        }
      },
      plugins: {
        legend: {
          position: 'top',
          labels: { color: '#9ca3af', font: { family: 'Inter', size: 12 }, usePointStyle: true }
        }
      }
    }
  });
}

function filterTable() {
  const query = document.getElementById('tableSearchInput').value.toLowerCase().trim();
  const damFilter = document.getElementById('damSelectFilter').value;

  if (!globalData || !globalData.all_records) return;

  const all = [...globalData.all_records].reverse();

  filteredRecords = all.filter(item => {
    const matchesDam = (damFilter === 'ALL') || (item.dam_name === damFilter);
    const matchesSearch = !query || 
      item.date.toLowerCase().includes(query) ||
      item.dam_name.toLowerCase().includes(query) ||
      item.status.toLowerCase().includes(query) ||
      item.current_pct.toString().includes(query) ||
      item.current_live_mcm.toString().includes(query);

    return matchesDam && matchesSearch;
  });

  currentPage = 1;
  renderTable();
}

function renderTable() {
  const tbody = document.getElementById('tableBody');
  if (!tbody) return;

  const totalRecords = filteredRecords.length;
  const totalPages = Math.max(1, Math.ceil(totalRecords / pageSize));

  if (currentPage > totalPages) currentPage = totalPages;

  const startIdx = (currentPage - 1) * pageSize;
  const endIdx = Math.min(startIdx + pageSize, totalRecords);
  const currentSlice = filteredRecords.slice(startIdx, endIdx);

  let html = '';
  if (currentSlice.length === 0) {
    html = `<tr><td colspan="8" style="text-align:center; padding:24px; color:var(--text-muted);">No records found matching filters.</td></tr>`;
  } else {
    currentSlice.forEach(row => {
      const tag = getTagDetails(row.current_pct);
      html += `
        <tr>
          <td><strong>${row.date}</strong></td>
          <td><span style="color:var(--text-primary); font-weight:500;">${row.dam_name}</span></td>
          <td style="color:var(--text-secondary);">${row.time || '08:00 AM'}</td>
          <td><strong>${row.current_live_mcm.toFixed(2)}</strong> MCM</td>
          <td style="color:var(--text-secondary);">${row.design_live_mcm.toFixed(2)} MCM</td>
          <td><span class="dam-tag ${tag.class}">${row.current_pct}%</span></td>
          <td style="color:var(--text-secondary);">${row.last_year_pct}%</td>
          <td><span style="color:${row.status === 'Success' ? 'var(--accent-emerald)' : 'var(--accent-amber)'}; font-weight:500;">${row.status}</span></td>
        </tr>
      `;
    });
  }

  tbody.innerHTML = html;

  const countText = document.getElementById('recordsCountText');
  if (countText) {
    if (totalRecords === 0) {
      countText.innerText = `Showing 0 of 0 records`;
    } else {
      countText.innerText = `Showing ${(startIdx + 1).toLocaleString()} - ${endIdx.toLocaleString()} of ${totalRecords.toLocaleString()} database records`;
    }
  }

  const pageIndicator = document.getElementById('pageIndicator');
  if (pageIndicator) {
    pageIndicator.innerText = `Page ${currentPage} of ${totalPages}`;
  }

  const prevBtn = document.getElementById('prevPageBtn');
  const nextBtn = document.getElementById('nextPageBtn');
  if (prevBtn) prevBtn.disabled = (currentPage <= 1);
  if (nextBtn) nextBtn.disabled = (currentPage >= totalPages);
}

function changePage(delta) {
  currentPage += delta;
  renderTable();
}

function exportTableToCSV() {
  if (!filteredRecords || filteredRecords.length === 0) {
    alert('No records available to export.');
    return;
  }

  const headers = ['Report Date', 'Dam Name', 'Report Time', 'Live Storage (MCM)', 'Design Live (MCM)', 'Current Storage (%)', 'Last Year (%)', 'Status'];
  const csvRows = [headers.join(',')];

  filteredRecords.forEach(r => {
    csvRows.push([
      `"${r.date}"`,
      `"${r.dam_name}"`,
      `"${r.time || ''}"`,
      r.current_live_mcm,
      r.design_live_mcm,
      r.current_pct,
      r.last_year_pct,
      `"${r.status}"`
    ].join(','));
  });

  const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `Pune_5_Dams_Database_Records_${new Date().toISOString().slice(0,10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}
