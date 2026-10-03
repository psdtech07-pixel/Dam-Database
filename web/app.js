let latestSnapshot = null;
let originalLatestSnapshot = null;
let currentSyncedDate = null;
let filteredRecords = [];
let currentPage = 1;
const pageSize = 25;

let trendChartInstance = null;
let volumeChartInstance = null;
let currentChartDays = 30;
let currentActiveRegion = 'Pune'; // Pune forefront default
let currentActiveBasin = 'ALL';
let historyCache = {}; // Cache for decoupled time-series JSON files (dam_slug -> points array)

const DAM_COLORS = [
  '#38bdf8', '#818cf8', '#a78bfa', '#f472b6', '#34d399', 
  '#fbbf24', '#f87171', '#2dd4bf', '#fb923c', '#e879f9'
];

document.addEventListener('DOMContentLoaded', () => {
  initDashboard();
});

async function initDashboard() {
  try {
    let resp = await fetch('data/latest.json?v=' + Date.now(), { cache: 'no-store' });
    if (!resp.ok) {
      resp = await fetch('data/latest_snapshot.json?v=' + Date.now(), { cache: 'no-store' });
    }
    if (!resp.ok) throw new Error('Failed to load latest dam metrics');
    latestSnapshot = await resp.json();
    originalLatestSnapshot = JSON.parse(JSON.stringify(latestSnapshot));
    
    if (document.getElementById('lastUpdatedText')) {
      document.getElementById('lastUpdatedText').innerText = `Sync: ${latestSnapshot.batch_date || 'Live'}`;
    }

    if (document.getElementById('totalRecordsBadge')) {
      document.getElementById('totalRecordsBadge').innerText = (latestSnapshot.total_dams || Object.keys(latestSnapshot.dams || {}).length).toLocaleString();
    }

    // Set Date Picker bounds dynamically from dates.json
    fetch('data/dates.json?v=' + Date.now()).then(r => r.json()).then(dates => {
      if (Array.isArray(dates) && dates.length > 0) {
        const picker = document.getElementById('syncDatePicker');
        if (picker) {
          picker.max = dates[0];
          picker.min = dates[dates.length - 1];
        }
      }
    }).catch(() => {});

    populateDropdowns();
    selectRegionTab('Pune');
  } catch (err) {
    console.error('Error initializing dashboard:', err);
    if (document.getElementById('lastUpdatedText')) {
      document.getElementById('lastUpdatedText').innerText = 'Offline Mode';
    }
  }
}

function getDamList() {
  if (!latestSnapshot || !latestSnapshot.dams) return [];
  return Object.values(latestSnapshot.dams);
}

function populateDropdowns() {
  if (!latestSnapshot || !latestSnapshot.dams) return;

  const dams = getDamList();
  const basinSelect = document.getElementById('basinSelectFilter');
  const districtSelect = document.getElementById('districtSelectFilter');
  const damSelect = document.getElementById('damSelectFilter');
  const chartDamSelect = document.getElementById('chartDamFilter');

  // Populate Basins
  if (basinSelect) {
    const basins = [...new Set(dams.map(d => d.basin).filter(Boolean))].sort();
    let basinOpts = '<option value="ALL">All River Basins</option>';
    basins.forEach(b => {
      basinOpts += `<option value="${b}">${b} Basin</option>`;
    });
    basinSelect.innerHTML = basinOpts;
  }

  // Populate Districts
  if (districtSelect) {
    const districts = [...new Set(dams.map(d => d.district).filter(Boolean))].sort();
    let distOpts = '<option value="ALL">All Districts</option>';
    districts.forEach(d => {
      distOpts += `<option value="${d}">${d}</option>`;
    });
    districtSelect.innerHTML = distOpts;
  }

  // Populate Dams
  if (damSelect) {
    const sortedDams = [...dams].sort((a, b) => a.name_en.localeCompare(b.name_en));
    let damOpts = '<option value="ALL">All Monitored Dams</option>';
    sortedDams.forEach(d => {
      damOpts += `<option value="${d.slug}">${d.name_en} (${d.name_mr})</option>`;
    });
    damSelect.innerHTML = damOpts;
  }

  // Populate Chart Dam Selector
  if (chartDamSelect) {
    const sortedDams = [...dams].sort((a, b) => a.name_en.localeCompare(b.name_en));
    let chartOpts = '<option value="ALL">Top Major Dams</option>';
    sortedDams.forEach(d => {
      chartOpts += `<option value="${d.slug}">${d.name_en}</option>`;
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
  if (!latestSnapshot || !latestSnapshot.dams) return;

  const basinFilter = document.getElementById('basinSelectFilter') ? document.getElementById('basinSelectFilter').value : 'ALL';
  const dams = getDamList();

  let totalLive = 0;
  let totalDesign = 0;
  let totalPctSum = 0;
  let totalLastYearSum = 0;
  let count = 0;

  dams.forEach(item => {
    if (regionName !== 'ALL' && item.division !== regionName) return;
    if (basinFilter !== 'ALL' && item.basin !== basinFilter) return;

    totalLive += (item.live_mcm || 0);
    totalDesign += (item.design_live_mcm || 0);
    totalPctSum += (item.pct || 0);
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

  const batchDate = latestSnapshot.batch_date || 'Current Date';

  document.getElementById('heroBadgeRegion').innerText = regionTitleMap[regionName] || 'RESERVOIR STORAGE';
  document.getElementById('heroPct').innerText = `${avgPct}%`;
  
  document.getElementById('heroSubtitle').innerText = `Live status as of ${batchDate} across ${count} monitored dams in ${regionName === 'ALL' ? 'Maharashtra' : regionName + ' Division'}.`;

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
  if (!container || !latestSnapshot || !latestSnapshot.dams) return;

  const basinFilter = document.getElementById('basinSelectFilter') ? document.getElementById('basinSelectFilter').value : 'ALL';
  let dams = getDamList();

  // Priority ordering for Pune dams when in Pune view
  if (regionName === 'Pune') {
    const priorityPune = ['khadakwasla', 'panshet', 'varasgaon', 'temghar', 'mulshi', 'pawana', 'gunjawani', 'chaskaman', 'dimbhe', 'koyna', 'ujani', 'veer'];
    dams.sort((a, b) => {
      const idxA = priorityPune.indexOf(a.slug);
      const idxB = priorityPune.indexOf(b.slug);
      if (idxA !== -1 && idxB !== -1) return idxA - idxB;
      if (idxA !== -1) return -1;
      if (idxB !== -1) return 1;
      return a.name_en.localeCompare(b.name_en);
    });
  } else {
    dams.sort((a, b) => a.name_en.localeCompare(b.name_en));
  }

  let html = '';
  let renderedCount = 0;

  dams.forEach(data => {
    if (regionName !== 'ALL' && data.division !== regionName) return;
    if (basinFilter !== 'ALL' && data.basin !== basinFilter) return;

    renderedCount++;

    const liveMcm = data.live_mcm || 0;
    const designMcm = data.design_live_mcm || 100;
    const pct = data.pct || 0;
    const tag = getTagDetails(pct);
    const liveML = Math.round(liveMcm * 1000);
    const displayNameMR = data.name_mr || data.name_en;

    html += `
      <div class="dam-card" ondblclick="openDamTrend('${data.slug}')" title="Double-click to view water storage trend chart for ${data.name_en}">
        <div class="dam-card-header">
          <div class="dam-name-wrapper">
            <h3>${data.name_en}</h3>
            <span class="dam-mr-name">${displayNameMR}</span>
            <span class="dam-location">${data.district || 'Pune'} • ${data.basin || 'Krishna'} Basin</span>
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
          <span>Updated: ${data.date || latestSnapshot.batch_date}</span>
        </div>
      </div>
    `;
  });

  if (renderedCount === 0) {
    html = `<div style="grid-column: 1/-1; padding: 24px; text-align: center; color: var(--text-muted);">No reservoirs found for selected region/basin filters.</div>`;
  }

  container.innerHTML = html;

  const title = document.getElementById('cardsGridTitle');
  if (title) {
    const regionText = regionName === 'ALL' ? 'All Maharashtra State' : (regionName === 'Pune' ? 'Pune Primary' : `${regionName} Region`);
    title.innerText = `${regionText} Monitored Reservoirs (${renderedCount} Dams)`;
  }
}

async function openDamTrend(slug) {
  const chartDamSelect = document.getElementById('chartDamFilter');
  if (chartDamSelect) {
    chartDamSelect.value = slug;
  }
  await renderTrendChart(currentChartDays);
  
  const chartCard = document.querySelector('.chart-card');
  if (chartCard) {
    chartCard.classList.remove('chart-card-highlight');
    void chartCard.offsetWidth; // trigger reflow
    chartCard.classList.add('chart-card-highlight');
    chartCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

async function onDateSyncSelected(selectedDate) {
  if (!selectedDate) return;

  const textElem = document.getElementById('lastUpdatedText');
  const pulseElem = document.getElementById('syncPulse');
  const resetBtn = document.getElementById('resetDateSyncBtn');

  if (textElem) textElem.innerText = `Syncing ${selectedDate}...`;

  if (!originalLatestSnapshot && latestSnapshot) {
    originalLatestSnapshot = JSON.parse(JSON.stringify(latestSnapshot));
  }

  const allDams = getDamList();
  
  // Load histories concurrently
  const historyPromises = allDams.map(d => fetchDamHistory(d.slug));
  const histories = await Promise.all(historyPromises);

  const updatedDamsMap = {};

  allDams.forEach((dam, idx) => {
    const history = histories[idx] || [];
    let match = history.find(p => (p.d || p.date) === selectedDate);
    if (!match) {
      const preceding = history.filter(p => (p.d || p.date) <= selectedDate);
      if (preceding.length > 0) {
        match = preceding[preceding.length - 1];
      }
    }

    const liveMcm = match ? (match.m !== undefined ? match.m : match.mcm || 0) : (dam.live_mcm || 0);
    const pct = match ? (match.p !== undefined ? match.p : match.pct || 0) : (dam.pct || 0);
    const readingDate = match ? (match.d || match.date) : selectedDate;

    updatedDamsMap[dam.slug] = {
      ...dam,
      date: readingDate,
      live_mcm: liveMcm,
      gross_mcm: liveMcm + (dam.dead_mcm || 0),
      pct: pct,
      remaining_mcm: Math.max(0, (dam.design_live_mcm || 0) - liveMcm)
    };
  });

  latestSnapshot = {
    batch_date: selectedDate,
    total_dams: Object.keys(updatedDamsMap).length,
    dams: updatedDamsMap
  };

  currentSyncedDate = selectedDate;

  if (textElem) textElem.innerText = `📅 Date: ${selectedDate}`;
  if (pulseElem) pulseElem.classList.add('historical');
  if (resetBtn) resetBtn.style.display = 'inline-block';

  renderHeroBanner(currentActiveRegion);
  renderDamCards(currentActiveRegion);
  renderTrendChart(currentChartDays);
  renderVolumeChart();
  filterTable();
}

function resetDateSync() {
  if (originalLatestSnapshot) {
    latestSnapshot = JSON.parse(JSON.stringify(originalLatestSnapshot));
  }
  currentSyncedDate = null;
  const picker = document.getElementById('syncDatePicker');
  if (picker) picker.value = '';

  const textElem = document.getElementById('lastUpdatedText');
  const pulseElem = document.getElementById('syncPulse');
  const resetBtn = document.getElementById('resetDateSyncBtn');

  if (textElem) textElem.innerText = `Sync: ${latestSnapshot.batch_date || 'Live'}`;
  if (pulseElem) pulseElem.classList.remove('historical');
  if (resetBtn) resetBtn.style.display = 'none';

  renderHeroBanner(currentActiveRegion);
  renderDamCards(currentActiveRegion);
  renderTrendChart(currentChartDays);
  renderVolumeChart();
  filterTable();
}
}

async function fetchDamHistory(slug) {
  if (historyCache[slug]) return historyCache[slug];
  try {
    const resp = await fetch(`data/history/${slug}.json?v=` + Date.now());
    if (!resp.ok) return [];
    const data = await resp.json();
    historyCache[slug] = data;
    return data;
  } catch (err) {
    console.warn(`Failed to fetch history for ${slug}:`, err);
    return [];
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

async function renderTrendChart(daysFilter = 30) {
  const canvas = document.getElementById('trendChart');
  if (!canvas || !latestSnapshot) return;
  const ctx = canvas.getContext('2d');

  const selectedDamSlug = document.getElementById('chartDamFilter').value;
  const basinFilter = document.getElementById('basinSelectFilter') ? document.getElementById('basinSelectFilter').value : 'ALL';

  let focusDams = [];

  if (selectedDamSlug === 'ALL') {
    let candidateDams = getDamList().filter(d => {
      const matchRegion = (currentActiveRegion === 'ALL') || (d.division === currentActiveRegion);
      const matchBasin = (basinFilter === 'ALL') || (d.basin === basinFilter);
      return matchRegion && matchBasin;
    });

    if (currentActiveRegion === 'Pune') {
      const priorityPune = ['khadakwasla', 'panshet', 'varasgaon', 'temghar', 'mulshi', 'pawana', 'koyna', 'ujani'];
      candidateDams.sort((a, b) => {
        const idxA = priorityPune.indexOf(a.slug);
        const idxB = priorityPune.indexOf(b.slug);
        if (idxA !== -1 && idxB !== -1) return idxA - idxB;
        if (idxA !== -1) return -1;
        if (idxB !== -1) return 1;
        return b.design_live_mcm - a.design_live_mcm;
      });
    } else {
      candidateDams.sort((a, b) => b.design_live_mcm - a.design_live_mcm);
    }
    focusDams = candidateDams.slice(0, 6);
  } else {
    const match = latestSnapshot.dams[selectedDamSlug];
    if (match) focusDams = [match];
  }

  if (focusDams.length === 0) return;

  // Load history files concurrently
  const historyPromises = focusDams.map(d => fetchDamHistory(d.slug));
  const histories = await Promise.all(historyPromises);

  // Determine common date timeline
  let allDatesSet = new Set();
  histories.forEach(h => {
    if (Array.isArray(h)) {
      h.forEach(pt => {
        const dStr = pt.d || pt.date;
        if (dStr && dStr >= '2024-01-01' && dStr <= '2026-12-31') {
          allDatesSet.add(dStr);
        }
      });
    }
  });

  let sortedDates = Array.from(allDatesSet).sort();
  if (daysFilter !== 'all' && typeof daysFilter === 'number') {
    sortedDates = sortedDates.slice(-daysFilter);
  }

  const dateMap = new Map();
  sortedDates.forEach((d, idx) => dateMap.set(d, idx));

  let datasets = focusDams.map((dam, idx) => {
    const damColor = DAM_COLORS[idx % DAM_COLORS.length];
    const history = histories[idx] || [];
    const ptMap = new Map(history.map(p => [p.d || p.date, p.p !== undefined ? p.p : p.pct]));

    const dataPoints = sortedDates.map(d => ptMap.has(d) ? ptMap.get(d) : null);

    return {
      label: `${dam.name_en} (%)`,
      data: dataPoints,
      borderColor: damColor,
      backgroundColor: selectedDamSlug === 'ALL' ? 'transparent' : (() => {
        const grad = ctx.createLinearGradient(0, 0, 0, 260);
        grad.addColorStop(0, damColor + '35');
        grad.addColorStop(1, damColor + '00');
        return grad;
      })(),
      fill: selectedDamSlug !== 'ALL',
      borderWidth: 2.2,
      spanGaps: true, // Seamless line interpolation over missing report dates
      tension: 0.25,
      pointRadius: sortedDates.length > 150 ? 0 : 2,
      pointHoverRadius: 5
    };
  });

  if (trendChartInstance) {
    trendChartInstance.destroy();
  }

  trendChartInstance = new Chart(ctx, {
    type: 'line',
    data: { labels: sortedDates, datasets },
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
  const canvas = document.getElementById('volumeChart');
  if (!canvas || !latestSnapshot || !latestSnapshot.dams) return;
  const ctx = canvas.getContext('2d');

  const basinFilter = document.getElementById('basinSelectFilter') ? document.getElementById('basinSelectFilter').value : 'ALL';
  let dams = getDamList().filter(d => {
    const matchRegion = (currentActiveRegion === 'ALL') || (d.division === currentActiveRegion);
    const matchBasin = (basinFilter === 'ALL') || (d.basin === basinFilter);
    return matchRegion && matchBasin;
  });

  if (currentActiveRegion === 'Pune') {
    const priorityPune = ['khadakwasla', 'panshet', 'varasgaon', 'temghar', 'mulshi', 'pawana', 'koyna', 'ujani'];
    dams.sort((a, b) => {
      const idxA = priorityPune.indexOf(a.slug);
      const idxB = priorityPune.indexOf(b.slug);
      if (idxA !== -1 && idxB !== -1) return idxA - idxB;
      if (idxA !== -1) return -1;
      if (idxB !== -1) return 1;
      return b.design_live_mcm - a.design_live_mcm;
    });
  } else {
    dams.sort((a, b) => b.design_live_mcm - a.design_live_mcm);
  }

  const displayDams = dams.slice(0, 7);
  const labels = displayDams.map(d => d.name_en);
  const currentLive = displayDams.map(d => d.live_mcm || 0);
  const remaining = displayDams.map(d => Math.max(0, (d.design_live_mcm || 0) - (d.live_mcm || 0)));

  if (volumeChartInstance) {
    volumeChartInstance.destroy();
  }

  volumeChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
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
  const basinFilter = document.getElementById('basinSelectFilter') ? document.getElementById('basinSelectFilter').value : 'ALL';
  const districtFilter = document.getElementById('districtSelectFilter').value;
  const damFilter = document.getElementById('damSelectFilter').value;

  if (!latestSnapshot || !latestSnapshot.dams) return;

  const all = getDamList();

  filteredRecords = all.filter(item => {
    const matchesRegion = (currentActiveRegion === 'ALL') || (item.division === currentActiveRegion);
    const matchesBasin = (basinFilter === 'ALL') || (item.basin === basinFilter);
    const matchesDist = (districtFilter === 'ALL') || (item.district === districtFilter);
    const matchesDam = (damFilter === 'ALL') || (item.slug === damFilter);
    
    const matchesSearch = !query || 
      item.name_en.toLowerCase().includes(query) ||
      (item.name_mr && item.name_mr.toLowerCase().includes(query)) ||
      (item.district && item.district.toLowerCase().includes(query)) ||
      (item.division && item.division.toLowerCase().includes(query)) ||
      (item.basin && item.basin.toLowerCase().includes(query)) ||
      (item.pct && item.pct.toString().includes(query)) ||
      (item.live_mcm && item.live_mcm.toString().includes(query));

    return matchesRegion && matchesBasin && matchesDist && matchesDam && matchesSearch;
  });

  // Also trigger cards & banner update if basin changed
  renderHeroBanner(currentActiveRegion);
  renderDamCards(currentActiveRegion);

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
      const tag = getTagDetails(row.pct || 0);
      const liveML = Math.round((row.live_mcm || 0) * 1000);

      html += `
        <tr>
          <td><strong>${row.date || latestSnapshot.batch_date}</strong></td>
          <td>
            <span style="color:var(--text-primary); font-weight:600;">${row.name_en}</span>
            <div style="font-size:0.75rem; color:var(--text-muted);">${row.name_mr || ''}</div>
          </td>
          <td style="color:var(--text-secondary);">${row.division || 'Pune'}</td>
          <td style="color:var(--text-secondary);">${row.district || 'Pune'}</td>
          <td style="color:var(--text-secondary);">${row.time || '08:00 AM'}</td>
          <td><strong>${(row.live_mcm || 0).toFixed(2)}</strong> MCM</td>
          <td style="color:var(--accent-sky); font-weight:500;">${liveML.toLocaleString()} ML</td>
          <td style="color:var(--text-secondary);">${(row.design_live_mcm || 0).toFixed(2)} MCM</td>
          <td><span class="dam-tag ${tag.class}">${(row.pct || 0).toFixed(1)}%</span></td>
          <td style="color:var(--text-secondary);">${(row.last_year_pct || 0).toFixed(1)}%</td>
          <td><span style="color:var(--accent-emerald); font-weight:500;">Success</span></td>
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
      countText.innerText = `Showing ${(startIdx + 1).toLocaleString()} - ${endIdx.toLocaleString()} of ${totalRecords.toLocaleString()} database dams`;
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

  const headers = ['Report Date', 'Dam Name (EN)', 'Dam Name (MR)', 'Division', 'District', 'Basin', 'Report Time', 'Live Storage (MCM)', 'Live Storage (ML)', 'Design Live (MCM)', 'Current Storage (%)', 'Last Year (%)', 'Status'];
  const rows = filteredRecords.map(r => [
    `"${r.date || latestSnapshot.batch_date}"`,
    `"${r.name_en}"`,
    `"${r.name_mr || ''}"`,
    `"${r.division || 'Pune'}"`,
    `"${r.district || 'Pune'}"`,
    `"${r.basin || 'Krishna'}"`,
    `"${r.time || '08:00 AM'}"`,
    r.live_mcm || 0,
    Math.round((r.live_mcm || 0) * 1000),
    r.design_live_mcm || 0,
    r.pct || 0,
    r.last_year_pct || 0,
    `"Success"`
  ]);

  const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `maharashtra_dam_storage_snapshot_${Date.now()}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
