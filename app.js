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
    const resp = await fetch('dam_data.json');
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
      document.getElementById('lastUpdatedText').innerText = `Last Report: ${d.date} (${d.time})`;
    }
  });

  const avgPct = count > 0 ? (totalPctSum / count).toFixed(1) : 0;
  const avgLastYear = count > 0 ? (totalLastYearSum / count).toFixed(1) : 0;
  const diff = (avgPct - avgLastYear).toFixed(1);

  document.getElementById('kpiTotalLive').innerHTML = `${totalLive.toFixed(1)} <span style="font-size: 16px;">MCM</span>`;
  document.getElementById('kpiTotalDesign').innerHTML = `${totalDesign.toFixed(1)} <span style="font-size: 16px;">MCM</span>`;
  document.getElementById('kpiAvgPct').innerText = `${avgPct}%`;

  const diffEl = document.getElementById('kpiYoYDiff');
  if (diff >= 0) {
    diffEl.innerHTML = `<span class="badge-positive">+${diff}%</span> vs Same Date Last Year (${avgLastYear}%)`;
  } else {
    diffEl.innerHTML = `<span style="color: var(--accent-rose); font-weight:600;">${diff}%</span> vs Same Date Last Year (${avgLastYear}%)`;
  }
}

function getTagDetails(pct) {
  if (pct >= 95) return { text: 'Full Capacity', class: 'tag-full' };
  if (pct >= 70) return { text: 'High Level', class: 'tag-good' };
  if (pct >= 40) return { text: 'Moderate', class: 'tag-moderate' };
  return { text: 'Low Level', class: 'tag-low' };
}

function getProgressColor(pct) {
  if (pct >= 95) return 'linear-gradient(90deg, #10b981, #34d399)';
  if (pct >= 70) return 'linear-gradient(90deg, #0284c7, #38bdf8)';
  if (pct >= 40) return 'linear-gradient(90deg, #d97706, #f59e0b)';
  return 'linear-gradient(90deg, #e11d48, #f43f5e)';
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
    const bgGradient = getProgressColor(d.current_pct);

    html += `
      <div class="dam-card">
        <div class="dam-card-header">
          <div>
            <div class="dam-name">${dam} Dam</div>
            <div style="font-size:12px; color:var(--text-subtle); margin-top:2px;">Live Capacity: ${d.design_live_mcm} MCM</div>
          </div>
          <span class="dam-tag ${tag.class}">${tag.text}</span>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:12px;">
          <div style="font-size:32px; font-weight:800; color:var(--text-main); font-family:'Outfit';">
            ${d.current_pct}%
          </div>
          <div style="font-size:13px; color:var(--text-muted);">
            <strong>${d.current_live_mcm}</strong> / ${d.design_live_mcm} MCM
          </div>
        </div>

        <!-- Gauge Bar -->
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" style="width: ${Math.min(100, d.current_pct)}%; background: ${bgGradient}"></div>
        </div>

        <div style="display:flex; justify-content:space-between; margin-top:12px; font-size:12px; color:var(--text-subtle);">
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
  document.querySelectorAll('.filter-tabs .filter-btn').forEach(b => b.classList.remove('active'));
  if (btnEl) btnEl.classList.add('active');
  renderTrendChart(days);
}

function renderTrendChart(days = 30) {
  const ctx = document.getElementById('trendChart').getContext('2d');
  if (!globalData || !globalData.time_series) return;

  let slice = globalData.time_series;
  if (days !== 'all' && typeof days === 'number') {
    slice = globalData.time_series.slice(-days);
  }

  const labels = slice.map(s => s.date_fmt || s.date);

  const colors = {
    'Khadakwasla': '#38bdf8',
    'Panshet': '#10b981',
    'Mulshi': '#8b5cf6',
    'Gunjawani': '#f59e0b',
    'Temghar': '#f43f5e'
  };

  const datasets = ['Khadakwasla', 'Panshet', 'Mulshi', 'Gunjawani', 'Temghar'].map(dam => {
    return {
      label: dam,
      data: slice.map(s => s[`${dam}_pct`]),
      borderColor: colors[dam],
      backgroundColor: colors[dam] + '15',
      borderWidth: 2,
      tension: 0.3,
      pointRadius: slice.length > 100 ? 0 : 2,
      pointHoverRadius: 6
    };
  });

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
          labels: { color: '#94a3b8', font: { family: 'Outfit', size: 13 }, usePointStyle: true, boxWidth: 8 }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.95)',
          titleColor: '#f8fafc',
          bodyColor: '#cbd5e1',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          padding: 12,
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y !== null && ctx.parsed.y !== undefined ? ctx.parsed.y.toFixed(1) : 'N/A'}%`
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: { color: '#64748b', font: { size: 11 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 10 }
        },
        y: {
          min: 0,
          max: 100,
          grid: { color: 'rgba(255, 255, 255, 0.06)' },
          ticks: { color: '#64748b', font: { size: 11 }, callback: (v) => v + '%' }
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
          label: 'Current Stored (MCM)',
          data: currentLive,
          backgroundColor: '#38bdf8',
          borderRadius: 6
        },
        {
          label: 'Remaining Capacity (MCM)',
          data: remaining,
          backgroundColor: 'rgba(255, 255, 255, 0.08)',
          borderRadius: 6
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
          ticks: { color: '#94a3b8', font: { family: 'Outfit', size: 12 } }
        },
        y: {
          stacked: true,
          grid: { color: 'rgba(255, 255, 255, 0.06)' },
          ticks: { color: '#64748b', font: { size: 11 } }
        }
      },
      plugins: {
        legend: {
          position: 'top',
          labels: { color: '#94a3b8', font: { family: 'Outfit', size: 12 }, usePointStyle: true }
        }
      }
    }
  });
}

function filterTable() {
  const query = document.getElementById('tableSearchInput').value.toLowerCase().trim();
  const damFilter = document.getElementById('damSelectFilter').value;

  if (!globalData || !globalData.all_records) return;

  // Search through all historical records (sorted newest first)
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
    html = `<tr><td colspan="8" style="text-align:center; padding:30px; color:var(--text-muted);">No records found matching your filters.</td></tr>`;
  } else {
    currentSlice.forEach(row => {
      const tag = getTagDetails(row.current_pct);
      html += `
        <tr>
          <td><strong>${row.date}</strong></td>
          <td><span style="color:var(--accent-cyan); font-weight:600;">${row.dam_name}</span></td>
          <td>${row.time || '08:00 स.'}</td>
          <td><strong>${row.current_live_mcm.toFixed(2)}</strong> MCM</td>
          <td>${row.design_live_mcm.toFixed(2)} MCM</td>
          <td><span class="dam-tag ${tag.class}">${row.current_pct}%</span></td>
          <td>${row.last_year_pct}%</td>
          <td><span style="color:${row.status === 'Success' ? 'var(--accent-emerald)' : 'var(--accent-amber)'}; font-weight:500;">${row.status}</span></td>
        </tr>
      `;
    });
  }

  tbody.innerHTML = html;

  // Update Pagination Controls UI
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
