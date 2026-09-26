let globalData = null;
let filteredRecords = [];
let currentPage = 1;
const pageSize = 25;

let trendChartInstance = null;
let volumeChartInstance = null;
let currentChartDays = 30;
let currentActiveRegion = 'Pune'; // Pune forefront default

const DIVISION_DISTRICT_MAP = {
  'Pune': ['Pune', 'Satara', 'Solapur', 'Sangli', 'Kolhapur'],
  'Kokan': ['Thane', 'Palghar', 'Raigad', 'Ratnagiri', 'Sindhudurg'],
  'Nashik': ['Nashik', 'Ahmednagar', 'Jalgaon', 'Dhule', 'Nandurbar'],
  'Chhatrapati Sambhajinagar': ['Chhatrapati Sambhajinagar', 'Jalna', 'Beed', 'Latur', 'Dharashiv', 'Nanded', 'Parbhani', 'Hingoli'],
  'Amravati': ['Amravati', 'Akola', 'Buldhana', 'Yavatmal', 'Washim'],
  'Nagpur': ['Nagpur', 'Bhandara', 'Gondia', 'Chandrapur', 'Gadchiroli', 'Wardha']
};

const DAM_COLORS = [
  '#38bdf8', '#818cf8', '#a78bfa', '#f472b6', '#34d399', 
  '#fbbf24', '#f87171', '#2dd4bf', '#fb923c', '#e879f9'
];

document.addEventListener('DOMContentLoaded', () => {
  initDashboard();
});

async function initDashboard() {
  try {
    const resp = await fetch('dam_data.json?v=' + Date.now(), { cache: 'no-store' });
    if (!resp.ok) throw new Error('Failed to load dam_data.json');
    globalData = await resp.json();
    
    populateDropdowns();

    filteredRecords = [...(globalData.all_records || [])];

    if (document.getElementById('totalRecordsBadge')) {
      document.getElementById('totalRecordsBadge').innerText = (globalData.total_records || filteredRecords.length).toLocaleString();
    }
    
    // Default to Pune Region View
    selectRegionTab('Pune');
  } catch (err) {
    console.error('Error initializing dashboard:', err);
    document.getElementById('lastUpdatedText').innerText = 'Offline Mode';
  }
}

function populateDropdowns() {
  if (!globalData) return;

  const districtSelect = document.getElementById('districtSelectFilter');
  const damSelect = document.getElementById('damSelectFilter');
  const chartDamSelect = document.getElementById('chartDamFilter');

  const dams = Object.keys(globalData.latest || {}).sort();

  if (districtSelect && globalData.districts) {
    let distOpts = '<option value="ALL">All Districts</option>';
    globalData.districts.forEach(d => {
      distOpts += `<option value="${d}">${d}</option>`;
    });
    districtSelect.innerHTML = distOpts;
  }

  if (damSelect) {
    let damOpts = '<option value="ALL">All Monitored Dams</option>';
    dams.forEach(d => {
      damOpts += `<option value="${d}">${d}</option>`;
    });
    damSelect.innerHTML = damOpts;
  }

  if (chartDamSelect) {
    let chartOpts = '<option value="ALL">Top Major Dams</option>';
    dams.forEach(d => {
      chartOpts += `<option value="${d}">${d}</option>`;
    });
    chartDamSelect.innerHTML = chartOpts;
  }
}

function selectRegionTab(regionName, btnElem) {
  currentActiveRegion = regionName;

  if (btnElem) {
    const nav = btnElem.parentElement;
    nav.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btnElem.classList.add('active');
  } else {
    const btn = document.querySelector(`.tab-btn[data-region="${regionName}"]`);
    if (btn) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    }
  }

  renderHeroBanner(regionName);
  renderDamCards(regionName);
  renderTrendChart(currentChartDays);
  renderVolumeChart();
  filterTable();
}

function renderHeroBanner(regionName) {
  if (!globalData || !globalData.latest) return;

  const latest = globalData.latest;
  const dams = Object.keys(latest);

  let totalLive = 0;
  let totalDesign = 0;
  let totalPctSum = 0;
  let totalLastYearSum = 0;
  let count = 0;

  dams.forEach(dam => {
    const item = latest[dam];
    if (regionName !== 'ALL' && item.division !== regionName) return;

    totalLive += (item.current_live_mcm || 0);
    totalDesign += (item.design_live_mcm || 0);
    totalPctSum += (item.current_pct || 0);
    totalLastYearSum += (item.last_year_pct || 0);
    count++;
  });

  if (count === 0) count = 1;

  const avgPct = totalDesign > 0 ? ((totalLive / totalDesign) * 100).toFixed(1) : (totalPctSum / count).toFixed(1);
  const avgLastYear = (totalLastYearSum / count).toFixed(1);
  const yoyDiff = (avgPct - avgLastYear).toFixed(1);
  const totalLiveML = Math.round(totalLive * 1000);

  const regionTitleMap = {
    'Pune': 'PUNE & PCMC REGION STORAGE',
    'Kokan': 'KONKAN & MUMBAI LAKES STORAGE',
    'Nashik': 'NASHIK REGION RESERVOIR STORAGE',
    'Chhatrapati Sambhajinagar': 'CHHATRAPATI SAMBHAJINAGAR STORAGE',
    'Amravati': 'AMRAVATI REGION STORAGE',
    'Nagpur': 'NAGPUR REGION STORAGE',
    'ALL': 'MAHARASHTRA STATE-WIDE STORAGE'
  };

  document.getElementById('heroBadgeRegion').innerText = regionTitleMap[regionName] || 'RESERVOIR STORAGE';
  document.getElementById('heroPct').innerText = `${avgPct}%`;
  
  document.getElementById('heroSubtitle').innerText = `Live status as of 26 September 2026 across ${count} monitored dams in ${regionName === 'ALL' ? 'Maharashtra' : regionName + ' Division'}.`;

  document.getElementById('kpiTotalLive').innerText = `${totalLive.toLocaleString('en-US', {maximumFractionDigits:2})} MCM`;
  document.getElementById('kpiTotalLiveML').innerText = `${totalLiveML.toLocaleString('en-US')} Million Litres`;

  document.getElementById('kpiTotalDesign').innerText = `${totalDesign.toLocaleString('en-US', {maximumFractionDigits:2})} MCM`;
  document.getElementById('kpiAvgPct').innerText = `${avgPct}%`;

  const yoyElem = document.getElementById('kpiYoYDiff');
  if (yoyElem) {
    const isPos = yoyDiff >= 0;
    yoyElem.innerHTML = `Last year: ${avgLastYear}% <span class="${isPos ? 'trend-up' : 'trend-down'}">${isPos ? '▲ +' : '▼ '}${yoyDiff}%</span>`;
  }
}

function getTagDetails(pct) {
  if (pct >= 90) return { class: 'tag-full', text: 'Full' };
  if (pct >= 60) return { class: 'tag-optimal', text: 'Optimal' };
  if (pct >= 30) return { class: 'tag-moderate', text: 'Moderate' };
  return { class: 'tag-low', text: 'Low' };
}

function renderDamCards(regionName = currentActiveRegion) {
  const container = document.getElementById('damCardsGrid');
  if (!container || !globalData || !globalData.latest) return;

  const latest = globalData.latest;
  let dams = Object.keys(latest);

  // Priority ordering for Pune dams when in Pune view
  if (regionName === 'Pune') {
    const priorityPune = ['Khadakwasla', 'Panshet', 'Varasgaon', 'Temghar', 'Mulshi', 'Pavana', 'Gunjawani', 'Chaskaman', 'Dimbhe', 'Koyna', 'Ujani', 'Veer'];
    dams.sort((a, b) => {
      const idxA = priorityPune.indexOf(a);
      const idxB = priorityPune.indexOf(b);
      if (idxA !== -1 && idxB !== -1) return idxA - idxB;
      if (idxA !== -1) return -1;
      if (idxB !== -1) return 1;
      return a.localeCompare(b);
    });
  }

  let html = '';
  let renderedCount = 0;

  dams.forEach(dam => {
    const data = latest[dam];
    if (regionName !== 'ALL' && data.division !== regionName) return;

    renderedCount++;
    if (renderedCount > 24) return;

    const liveMcm = data.current_live_mcm || 0;
    const designMcm = data.design_live_mcm || 100;
    const pct = data.current_pct || 0;
    const tag = getTagDetails(pct);
    const liveML = Math.round(liveMcm * 1000);

    const displayNameMR = data.dam_name_mr || dam;

    html += `
      <div class="dam-card">
        <div class="dam-card-header">
          <div class="dam-name-wrapper">
            <h3>${dam}</h3>
            <span class="dam-mr-name">${displayNameMR}</span>
            <span class="dam-location">${data.district || 'Pune'} District</span>
          </div>
          <span class="dam-tag ${tag.class}">${pct}%</span>
        </div>

        <div class="metric-group">
          <div class="metric-item">
            <span class="m-label">Live Storage</span>
            <span class="m-val">${liveMcm.toFixed(2)} MCM</span>
            <span class="m-sub">${liveML.toLocaleString()} ML</span>
          </div>
          <div class="metric-item">
            <span class="m-label">Design Live</span>
            <span class="m-val">${designMcm.toFixed(2)} MCM</span>
            <span class="m-sub">Capacity</span>
          </div>
        </div>

        <div class="progress-bar-container">
          <div class="progress-bar-fill" style="width: ${Math.min(100, Math.max(0, pct))}%;"></div>
        </div>

        <div class="dam-card-footer">
          <span>Last Year: ${data.last_year_pct}%</span>
          <span>Updated: ${data.date}</span>
        </div>
      </div>
    `;
  });

  if (renderedCount === 0) {
    html = `<div style="grid-column: 1/-1; padding: 24px; text-align: center; color: var(--text-muted);">No reservoirs found for selected region.</div>`;
  }

  container.innerHTML = html;

  const title = document.getElementById('cardsGridTitle');
  if (title) {
    title.innerText = regionName === 'Pune' ? 'Pune Primary Supply Reservoirs' : `${regionName} Region Reservoirs`;
  }
}

function setChartDays(days, btnElem) {
  currentChartDays = days;
  if (btnElem) {
    const parent = btnElem.parentElement;
    parent.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
    btnElem.classList.add('active');
  }
  renderTrendChart(days);
}

function renderTrendChart(daysFilter = 30) {
  const ctx = document.getElementById('trendChart').getContext('2d');
  if (!globalData || !globalData.time_series) return;

  const rawTs = globalData.time_series || [];
  let slice = [...rawTs];
  
  if (daysFilter !== 'all' && typeof daysFilter === 'number') {
    slice = slice.slice(-daysFilter);
  }

  const labels = slice.map(s => s.date_fmt || s.date);
  const selectedDam = document.getElementById('chartDamFilter').value;

  let datasets = [];

  if (selectedDam === 'ALL') {
    let focusDams = ['Khadakwasla', 'Panshet', 'Varasgaon', 'Temghar', 'Mulshi', 'Pavana', 'Koyna'];
    if (currentActiveRegion !== 'Pune' && currentActiveRegion !== 'ALL') {
      focusDams = Object.keys(globalData.latest || {}).filter(d => globalData.latest[d].division === currentActiveRegion).slice(0, 6);
    }
    
    datasets = focusDams.map((dam, idx) => {
      const damColor = DAM_COLORS[idx % DAM_COLORS.length];
      return {
        label: dam,
        data: slice.map(s => s[`${dam}_pct`] !== undefined ? s[`${dam}_pct`] : null),
        borderColor: damColor,
        backgroundColor: 'transparent',
        borderWidth: 2,
        tension: 0.25,
        pointRadius: slice.length > 150 ? 0 : 2,
        pointHoverRadius: 5
      };
    });
  } else {
    const damColor = DAM_COLORS[0];
    const gradient = ctx.createLinearGradient(0, 0, 0, 260);
    gradient.addColorStop(0, damColor + '30');
    gradient.addColorStop(1, damColor + '00');

    datasets = [{
      label: `${selectedDam} Storage Level (%)`,
      data: slice.map(s => s[`${selectedDam}_pct`] !== undefined ? s[`${selectedDam}_pct`] : null),
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
          labels: { color: '#9ca3af', font: { family: 'Plus Jakarta Sans', size: 12 }, usePointStyle: true, boxWidth: 6 }
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
  let dams = ['Khadakwasla', 'Panshet', 'Varasgaon', 'Temghar', 'Mulshi', 'Pavana', 'Koyna'].filter(d => latest[d]);
  if (currentActiveRegion !== 'Pune' && currentActiveRegion !== 'ALL') {
    dams = Object.keys(latest).filter(d => latest[d].division === currentActiveRegion).slice(0, 7);
  }

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
          backgroundColor: '#38bdf8',
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
          ticks: { color: '#9ca3af', font: { family: 'Plus Jakarta Sans', size: 11 } }
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
          labels: { color: '#9ca3af', font: { family: 'Plus Jakarta Sans', size: 12 }, usePointStyle: true }
        }
      }
    }
  });
}

function filterTable() {
  const query = document.getElementById('tableSearchInput').value.toLowerCase().trim();
  const districtFilter = document.getElementById('districtSelectFilter').value;
  const damFilter = document.getElementById('damSelectFilter').value;

  if (!globalData || !globalData.all_records) return;

  const all = [...globalData.all_records];

  filteredRecords = all.filter(item => {
    const matchesRegion = (currentActiveRegion === 'ALL') || (item.division === currentActiveRegion);
    const matchesDist = (districtFilter === 'ALL') || (item.district === districtFilter);
    const matchesDam = (damFilter === 'ALL') || (item.dam_name === damFilter);
    
    const matchesSearch = !query || 
      item.date.toLowerCase().includes(query) ||
      item.dam_name.toLowerCase().includes(query) ||
      (item.district && item.district.toLowerCase().includes(query)) ||
      (item.division && item.division.toLowerCase().includes(query)) ||
      item.status.toLowerCase().includes(query) ||
      item.current_pct.toString().includes(query) ||
      item.current_live_mcm.toString().includes(query);

    return matchesRegion && matchesDist && matchesDam && matchesSearch;
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
    html = `<tr><td colspan="11" style="text-align:center; padding:24px; color:var(--text-muted);">No records found matching active filters.</td></tr>`;
  } else {
    currentSlice.forEach(row => {
      const tag = getTagDetails(row.current_pct);
      const liveML = Math.round(row.current_live_mcm * 1000);

      html += `
        <tr>
          <td><strong>${row.date}</strong></td>
          <td>
            <span style="color:var(--text-primary); font-weight:600;">${row.dam_name}</span>
          </td>
          <td style="color:var(--text-secondary);">${row.division || 'Pune'}</td>
          <td style="color:var(--text-secondary);">${row.district || 'Pune'}</td>
          <td style="color:var(--text-secondary);">${row.time || '08:00 AM'}</td>
          <td><strong>${row.current_live_mcm.toFixed(2)}</strong> MCM</td>
          <td style="color:var(--accent-sky); font-weight:500;">${liveML.toLocaleString()} ML</td>
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

  const headers = ['Report Date', 'Dam Name', 'Division', 'District', 'Report Time', 'Live Storage (MCM)', 'Live Storage (ML)', 'Design Live (MCM)', 'Current Storage (%)', 'Last Year (%)', 'Status'];
  const rows = filteredRecords.map(r => [
    `"${r.date}"`,
    `"${r.dam_name}"`,
    `"${r.division || 'Pune'}"`,
    `"${r.district || 'Pune'}"`,
    `"${r.time || '08:00 AM'}"`,
    r.current_live_mcm,
    Math.round(r.current_live_mcm * 1000),
    r.design_live_mcm,
    r.current_pct,
    r.last_year_pct,
    `"${r.status}"`
  ]);

  const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `pune_maharashtra_dam_storage_export_${Date.now()}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
