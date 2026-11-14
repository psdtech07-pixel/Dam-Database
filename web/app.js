/**
 * Maharashtra & Pune Dam Water Levels Dashboard
 * Clean Editorial Civic-Tech UI (mumbailakewaterlevel.in Style)
 * Supports Light/Dark Mode, Circular Ring Gauge, YoY Vertical Bar Comparison,
 * Dedicated Dam Detail Pages with Encyclopedic Specs, Photos & District Navigation
 */

let latestSnapshot = null;
let originalLatestSnapshot = null;
let currentSyncedDate = null;
let filteredRecords = [];
let currentPage = 1;
const pageSize = 20;

let trendChartInstance = null;
let volumeChartInstance = null;
let damDetailChartInstance = null;

let currentChartDays = 30;
let currentDamDetailChartDays = 30;
let currentActiveRegion = 'Pune'; // Default to Pune Region
let currentDamSlug = null;
let historyCache = {}; // Cache for decoupled time-series JSON files (dam_slug -> points array)

// Curated palette for multi-dam comparison
const DAM_COLORS = [
  '#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#06b6d4', '#f97316', '#6366f1', '#14b8a6', '#ec4899'
];

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initDashboard();

  // Handle URL hash routing e.g. #/dam/khadakwasla
  window.addEventListener('hashchange', handleHashRouting);
});

/* ----------------------------------------------------------------------------
   THEME TOGGLE (LIGHT / DARK MODE)
   ---------------------------------------------------------------------------- */
function initTheme() {
  const saved = localStorage.getItem('theme');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = saved || (prefersDark ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', theme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);

  // Re-render active charts with updated theme colors
  if (trendChartInstance) renderTrendChart(currentChartDays);
  if (volumeChartInstance) renderVolumeChart();
  if (damDetailChartInstance && currentDamSlug) renderDamDetailTrendChart(currentDamSlug, currentDamDetailChartDays);
}

function getThemeColors() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  return {
    isDark,
    gridColor: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)',
    textColor: isDark ? '#94a3b8' : '#64748b',
    tooltipBg: isDark ? '#1e293b' : '#ffffff',
    tooltipText: isDark ? '#f8fafc' : '#0f172a',
    tooltipBorder: isDark ? '#334155' : '#e2e8f0'
  };
}

const SLUG_ALIASES = {
  "tillari-kokan-sindhudurg": "tillari",
  "ujani": "bhima-ujjani",
  "siddheshwar": "siddeshwar",
  "dhalegaon-hlb": "dhalegaon-h-l-b",
  "dhanegaon-hlb": "dhanegaon-high-level",
  "dongargaon-hlb": "dongargaon-h-l-b",
  "ghod-chinchani": "ghod",
  "jayakwadi-paithan": "jayakwadi",
  "kawdas-weir": "kawdas-p-u-weir",
  "mulshi-tata": "mulshi",
  "pujaritola": "pujaritola-p-u-weir",
  "walwhan-tata": "walwan-tata"
};

/* ----------------------------------------------------------------------------
   ROUTING: OVERVIEW <-> DEDICATED DAM DETAIL PAGE <-> ABOUT PAGE
   ---------------------------------------------------------------------------- */
function handleHashRouting() {
  const hash = window.location.hash || '';
  if (hash.startsWith('#/dam/')) {
    let slug = hash.replace('#/dam/', '').trim().toLowerCase();
    if (SLUG_ALIASES[slug]) {
      slug = SLUG_ALIASES[slug];
      window.location.replace(`#/dam/${slug}`);
      return;
    }
    if (slug) {
      openDamPage(slug, false);
      return;
    }
  } else if (hash === '#/about' || hash === '#/about-project') {
    openAboutPage('project', false);
    return;
  } else if (hash === '#/about-us' || hash === '#/about-developer') {
    openAboutPage('developer', false);
    return;
  }
  navigateToOverview(false);
}

function navigateToOverview(updateHash = true) {
  if (updateHash) {
    history.pushState(null, '', window.location.pathname + window.location.search);
  }
  currentDamSlug = null;

  const overview = document.getElementById('overviewView');
  const damDetail = document.getElementById('damDetailView');
  const about = document.getElementById('aboutView');

  if (damDetail) { damDetail.classList.remove('active'); damDetail.style.display = 'none'; }
  if (about) { about.classList.remove('active'); about.style.display = 'none'; }
  if (overview) { overview.style.display = 'block'; overview.classList.add('active'); }

  window.scrollTo({ top: 0, behavior: 'smooth' });
  if (trendChartInstance) renderTrendChart(currentChartDays);
  if (volumeChartInstance) renderVolumeChart();
}

function openDamPage(slug, updateHash = true) {
  const allDams = getDamList();
  const dam = allDams.find(d => d.slug === slug);
  if (!dam) return;

  currentDamSlug = slug;
  if (updateHash) {
    window.location.hash = `#/dam/${slug}`;
  }

  const overview = document.getElementById('overviewView');
  const damDetail = document.getElementById('damDetailView');
  const about = document.getElementById('aboutView');

  if (overview) { overview.classList.remove('active'); overview.style.display = 'none'; }
  if (about) { about.classList.remove('active'); about.style.display = 'none'; }
  if (damDetail) { damDetail.style.display = 'block'; damDetail.classList.add('active'); }

  renderDamDetailPage(dam);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function openAboutPage(targetSection = 'project', updateHash = true) {
  if (updateHash) {
    window.location.hash = targetSection === 'developer' ? '#/about-us' : '#/about';
  }
  currentDamSlug = null;

  const overview = document.getElementById('overviewView');
  const damDetail = document.getElementById('damDetailView');
  const about = document.getElementById('aboutView');

  if (overview) { overview.classList.remove('active'); overview.style.display = 'none'; }
  if (damDetail) { damDetail.classList.remove('active'); damDetail.style.display = 'none'; }
  if (about) { about.style.display = 'block'; about.classList.add('active'); }

  if (targetSection === 'developer') {
    const devSection = document.getElementById('aboutDeveloperSection');
    if (devSection) {
      setTimeout(() => devSection.scrollIntoView({ behavior: 'smooth' }), 50);
      return;
    }
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function filterByBreadcrumbDistrict() {
  if (!currentDamSlug) return;
  const allDams = getDamList();
  const dam = allDams.find(d => d.slug === currentDamSlug);
  navigateToOverview();
  if (dam && dam.district) {
    const distSelect = document.getElementById('districtSelectFilter');
    if (distSelect) {
      distSelect.value = dam.district;
      filterTable();
      const tableSection = document.querySelector('.table-panel');
      if (tableSection) tableSection.scrollIntoView({ behavior: 'smooth' });
    }
  }
}

/* ----------------------------------------------------------------------------
   DASHBOARD INITIALIZATION & DATA FETCHING
   ---------------------------------------------------------------------------- */
async function initDashboard() {
  try {
    let resp = await fetch('data/latest.json?v=' + Date.now(), { cache: 'no-store' });
    if (!resp.ok) throw new Error('Failed to load latest dam metrics');
    latestSnapshot = await resp.json();
    originalLatestSnapshot = JSON.parse(JSON.stringify(latestSnapshot));

    // Update Header Date Badge
    if (document.getElementById('lastUpdatedText')) {
      const dateFormatted = formatDateDisplay(latestSnapshot.batch_date);
      document.getElementById('lastUpdatedText').innerText = `${dateFormatted} (Live)`;
      document.getElementById('navbarSubtitle').innerText = `Report as of ${dateFormatted} • Maharashtra WRD`;
    }

    if (document.getElementById('totalRecordsBadge')) {
      document.getElementById('totalRecordsBadge').innerText = (latestSnapshot.total_dams || Object.keys(latestSnapshot.dams || {}).length).toLocaleString();
    }

    // Load dynamic platform metadata for About page KPIs (B08)
    fetch('data/meta.json?v=' + Date.now()).then(r => r.json()).then(meta => {
      if (meta) {
        if (document.getElementById('aboutStatsDams') && meta.dams_count) {
          document.getElementById('aboutStatsDams').innerText = meta.dams_count.toLocaleString();
        }
        if (document.getElementById('aboutStatsDivisions') && meta.divisions_count) {
          document.getElementById('aboutStatsDivisions').innerText = meta.divisions_count.toLocaleString();
        }
        if (document.getElementById('aboutStatsRecords') && meta.records_count) {
          document.getElementById('aboutStatsRecords').innerText = meta.records_count.toLocaleString();
        }
        if (document.getElementById('aboutStatsDays') && meta.days_count) {
          document.getElementById('aboutStatsDays').innerText = meta.days_count.toLocaleString();
        }
      }
    }).catch(() => {});

    // Set Date Picker bounds from dates.json
    fetch('data/dates.json?v=' + Date.now()).then(r => r.json()).then(dates => {
      if (Array.isArray(dates) && dates.length > 0) {
        const picker = document.getElementById('syncDatePicker');
        if (picker) {
          picker.max = dates[0];
          picker.min = dates[dates.length - 1];
          picker.value = dates[0];
        }
      }
    }).catch(() => {});

    populateDropdowns();

    // Check if initial URL points to a specific dam or about page
    const hash = window.location.hash || '';
    if (hash.startsWith('#/dam/') || hash.startsWith('#/about')) {
      handleHashRouting();
    } else {
      selectRegionTab('Pune');
    }
  } catch (err) {
    console.error('Error initializing dashboard:', err);
    if (document.getElementById('lastUpdatedText')) {
      document.getElementById('lastUpdatedText').innerText = 'Offline Mode';
    }
  }
}

function formatDateDisplay(isoDateStr) {
  if (!isoDateStr) return 'Latest';
  try {
    const parts = isoDateStr.split('-');
    if (parts.length === 3) {
      const date = new Date(parts[0], parts[1] - 1, parts[2]);
      return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
    }
  } catch (e) {}
  return isoDateStr;
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
  const chartDamSelect = document.getElementById('chartDamFilter');

  // Populate Basins
  if (basinSelect) {
    const basins = [...new Set(dams.map(d => d.basin).filter(Boolean))].sort();
    let basinOpts = '<option value="ALL">All River Basins</option>';
    basins.forEach(b => {
      basinOpts += `<option value="${escapeHtml(b)}">${escapeHtml(b)} Basin</option>`;
    });
    basinSelect.innerHTML = basinOpts;
  }

  // Populate Districts
  if (districtSelect) {
    const districts = [...new Set(dams.map(d => d.district).filter(Boolean))].sort();
    let distOpts = '<option value="ALL">All Districts</option>';
    districts.forEach(d => {
      distOpts += `<option value="${escapeHtml(d)}">${escapeHtml(d)}</option>`;
    });
    districtSelect.innerHTML = distOpts;
  }

  // Populate Chart Dam Selector
  if (chartDamSelect) {
    const sortedDams = [...dams].sort((a, b) => a.name_en.localeCompare(b.name_en));
    let chartOpts = '<option value="ALL">Top Regional Reservoirs</option>';
    sortedDams.forEach(d => {
      chartOpts += `<option value="${escapeHtml(d.slug)}">${escapeHtml(d.name_en)} (${escapeHtml(d.district)})</option>`;
    });
    chartDamSelect.innerHTML = chartOpts;
  }
}

/* ----------------------------------------------------------------------------
   REGION TAB SELECTION & HERO SUMMARY (IMAGE 1 EXACT CLONE)
   ---------------------------------------------------------------------------- */
function selectRegionTab(regionName, btnElem) {
  currentActiveRegion = regionName;

  // Update Tab Active Styling
  const tabs = document.querySelectorAll('.region-tab');
  tabs.forEach(t => t.classList.remove('active'));
  if (btnElem) {
    btnElem.classList.add('active');
  } else {
    const match = Array.from(tabs).find(t => t.getAttribute('data-region') === regionName);
    if (match) match.classList.add('active');
  }

  // Update Headlines
  const headlines = {
    'Pune': 'How full are Pune’s dams today?',
    'Kokan': 'How full are Mumbai & Konkan lakes today?',
    'Nashik': 'How full are Nashik’s reservoirs today?',
    'Chhatrapati Sambhajinagar': 'How full are Marathwada’s reservoirs today?',
    'Amravati': 'How full are Amravati’s reservoirs today?',
    'Nagpur': 'How full are Vidarbha’s reservoirs today?',
    'ALL': 'How full are Maharashtra’s reservoirs today?'
  };

  const gridTitles = {
    'Pune': 'Pune Primary Reservoirs',
    'Kokan': 'Konkan & Mumbai Major Reservoirs',
    'Nashik': 'Nashik Major Reservoirs',
    'Chhatrapati Sambhajinagar': 'Marathwada Major Reservoirs',
    'Amravati': 'Amravati Major Reservoirs',
    'Nagpur': 'Vidarbha Major Reservoirs',
    'ALL': 'All Maharashtra Major Reservoirs'
  };

  if (document.getElementById('heroHeadlineQuestion')) {
    document.getElementById('heroHeadlineQuestion').innerText = headlines[regionName] || 'How full are our dams today?';
  }
  if (document.getElementById('cardsGridTitle')) {
    document.getElementById('cardsGridTitle').innerText = gridTitles[regionName] || 'Monitored Reservoirs';
  }

  updateHeroAnalytics(regionName);
  renderDamCards(regionName);
  renderTrendChart(currentChartDays);
  renderVolumeChart();
  filterTable();
}

function getRegionDams(regionName) {
  const allDams = getDamList();
  if (regionName === 'ALL') return allDams;
  return allDams.filter(d => d.division === regionName);
}

function getStatusDetails(pct) {
  if (pct >= 50) return { key: 'healthy', label: 'Healthy', color: '#10b981', textClass: 'healthy' };
  if (pct >= 25) return { key: 'moderate', label: 'Moderate', color: '#f59e0b', textClass: 'moderate' };
  if (pct >= 10) return { key: 'low', label: 'Low', color: '#ea580c', textClass: 'low' };
  return { key: 'critical', label: 'Critical', color: '#ef4444', textClass: 'critical' };
}

function updateHeroAnalytics(regionName) {
  const regionDams = getRegionDams(regionName);
  if (!regionDams || regionDams.length === 0) return;

  let totalLive = 0;
  let totalDesign = 0;
  let lyNum = 0;
  let lyDen = 0;
  let yoyCount = 0;

  regionDams.forEach(d => {
    const live = Number(d.live_mcm) || 0;
    const design = Number(d.design_live_mcm) || 0;
    totalLive += live;
    totalDesign += design;

    if (d.last_year_pct != null && d.last_year_pct !== '' && Number(d.last_year_pct) > 0 && design > 0) {
      lyNum += Number(d.last_year_pct) * design;
      lyDen += design;
      yoyCount++;
    }
  });

  const overallPct = totalDesign > 0 ? (totalLive / totalDesign) * 100 : 0;
  const lastYearPct = lyDen > 0 ? (lyNum / lyDen) : null;
  const status = getStatusDetails(overallPct);

  // Format Large Numbers
  const totalLiveML = totalLive * 1000;
  const totalDesignML = totalDesign * 1000;
  const totalLiveTMC = totalLive * 0.035315;
  const totalDesignTMC = totalDesign * 0.035315;

  // 1. UPDATE CIRCULAR RING GAUGE (Image 1 Left Card)
  const ringProgress = document.getElementById('heroRingProgress');
  const pctNumber = document.getElementById('heroPctNumber');
  const statusPill = document.getElementById('heroStatusPill');

  if (pctNumber) pctNumber.innerText = `${overallPct.toFixed(1)}%`;
  if (statusPill) {
    statusPill.innerText = status.label;
    statusPill.className = `ring-status-pill ${status.textClass}`;
  }

  if (ringProgress) {
    const radius = 62;
    const circumference = 2 * Math.PI * radius; // 389.55
    const offset = circumference * (1 - Math.min(100, Math.max(0, overallPct)) / 100);
    ringProgress.style.strokeDasharray = `${circumference}`;
    ringProgress.style.strokeDashoffset = `${offset}`;
    ringProgress.style.stroke = status.color;
  }

  // Real Delta comparison calculation
  const deltaText = document.getElementById('heroDeltaText');
  if (deltaText) {
    const delta = computeRegionDelta(regionDams);
    if (!delta) {
      deltaText.innerText = '—';
    } else {
      const arrow = delta.pp > 0.005 ? '↗' : (delta.pp < -0.005 ? '↘' : '→');
      const sign = delta.pp > 0.005 ? '+' : '';
      const ppStr = `${sign}${delta.pp.toFixed(2)}%`;
      const mlStr = `${sign}${Math.round(delta.ml).toLocaleString('en-IN')} ML`;
      const dateStr = formatDateDisplay(delta.prevDate);
      let text = `${arrow} ${ppStr} · ${mlStr} · since ${dateStr}`;
      if (delta.n < delta.total) {
        text += ` (${delta.n} of ${delta.total} dams)`;
      }
      deltaText.innerText = text;
    }
  }

  // Stored vs Capacity numbers
  if (document.getElementById('heroStoredML')) {
    document.getElementById('heroStoredML').innerText = `${Math.round(totalLiveML).toLocaleString('en-IN')} ML`;
  }
  if (document.getElementById('heroStoredMCM')) {
    document.getElementById('heroStoredMCM').innerText = `${totalLive.toLocaleString('en-IN', { maximumFractionDigits: 1 })} MCM · ${totalLiveTMC.toFixed(1)} TMC`;
  }

  if (document.getElementById('heroCapacityML')) {
    document.getElementById('heroCapacityML').innerText = `${Math.round(totalDesignML).toLocaleString('en-IN')} ML`;
  }
  if (document.getElementById('heroCapacityMCM')) {
    document.getElementById('heroCapacityMCM').innerText = `${totalDesign.toLocaleString('en-IN', { maximumFractionDigits: 1 })} MCM · ${totalDesignTMC.toFixed(1)} TMC`;
  }

  // 2. UPDATE YEAR-ON-YEAR VERTICAL BARS (Image 1 Right Card)
  const bar2025 = document.getElementById('bar2025Fill');
  const bar2026 = document.getElementById('bar2026Fill');
  const yoy2025Num = document.getElementById('yoy2025Num');
  const yoy2026Num = document.getElementById('yoy2026Num');
  const yoyDateLabel = document.getElementById('yoyCurrentDateLabel');
  const yoyFootnote = document.getElementById('yoyFootnoteText');

  // Dynamic years from data
  const curBatchDate = latestSnapshot.batch_date;
  const curYear = curBatchDate ? new Date(curBatchDate).getFullYear() : new Date().getFullYear();
  const prevYear = curYear - 1;

  const bar2025Label = document.getElementById('bar2025YearLabel');
  const bar2026Label = document.getElementById('bar2026YearLabel');
  const yoy2025Label = document.getElementById('yoy2025Label');
  if (bar2025Label) bar2025Label.innerText = prevYear;
  if (bar2026Label) bar2026Label.innerText = curYear;
  if (yoy2025Label) yoy2025Label.innerText = prevYear;

  if (lastYearPct != null) {
    if (bar2025) {
      bar2025.style.height = `${Math.min(100, lastYearPct)}%`;
      if (bar2025.parentElement && bar2025.parentElement.parentElement) {
        bar2025.parentElement.parentElement.style.opacity = '1';
      }
    }
    if (yoy2025Num) yoy2025Num.innerText = `${lastYearPct.toFixed(1)}%`;
  } else {
    if (bar2025) {
      bar2025.style.height = '0%';
      if (bar2025.parentElement && bar2025.parentElement.parentElement) {
        bar2025.parentElement.parentElement.style.opacity = '0.35';
      }
    }
    if (yoy2025Num) yoy2025Num.innerText = '—';
  }

  if (bar2026) bar2026.style.height = `${Math.min(100, overallPct)}%`;
  if (yoy2026Num) yoy2026Num.innerText = `${overallPct.toFixed(1)}%`;

  if (yoyDateLabel) {
    const dateFormatted = formatDateDisplay(curBatchDate).toUpperCase();
    yoyDateLabel.innerText = dateFormatted;
  }
  if (yoyFootnote) {
    let note = `Capacity-weighted YoY from WRD for ${regionDams.length} major reservoirs in ${regionName} region.`;
    if (yoyCount < regionDams.length) {
      note = `Capacity-weighted YoY from WRD (based on ${yoyCount} of ${regionDams.length} dams reporting prior year data).`;
    }
    yoyFootnote.innerText = note;
  }

  // 3. UPDATE ADVISORY CALLOUT ("What it means today")
  const advisoryMain = document.getElementById('advisoryMainText');
  const advisorySub = document.getElementById('advisorySubText');
  const calloutBox = document.getElementById('advisoryCallout');

  if (advisoryMain) {
    const regionNamePretty = regionName === 'ALL' ? "Maharashtra" : regionName;
    let yoyPart = '';
    if (lastYearPct != null) {
      yoyPart = ` Last year on this date: <strong>${lastYearPct.toFixed(2)}%</strong>.`;
    }
    advisoryMain.innerHTML = `${regionNamePretty}’s reservoirs are <strong>${overallPct.toFixed(2)}% full</strong>, ${status.label.toLowerCase()} levels.${yoyPart}`;
  }
  if (advisorySub) {
    let advice = 'Storage levels are healthy across major reservoirs. Practice responsible water use.';
    if (overallPct < 25) advice = 'Storage levels are low compared with capacity. Follow water conservation guidance from local municipal and irrigation authorities.';
    else if (overallPct < 50) advice = 'Storage is moderate. Monitor local municipal water updates and seasonal irrigation rotations.';
    advisorySub.innerText = advice;
  }
}

function computeRegionDelta(dams) {
  let cur = 0, prev = 0, cap = 0, n = 0;
  const dates = {};
  for (const d of dams) {
    if (d.prev_live_mcm == null || d.live_mcm == null || d.design_live_mcm == null) continue;
    cur += Number(d.live_mcm);
    prev += Number(d.prev_live_mcm);
    cap += Number(d.design_live_mcm);
    n++;
    if (d.prev_date) {
      dates[d.prev_date] = (dates[d.prev_date] || 0) + 1;
    }
  }
  if (!n || !cap) return null;
  const dateEntries = Object.entries(dates);
  const prevDate = dateEntries.length > 0 ? dateEntries.sort((a, b) => b[1] - a[1])[0][0] : null;
  return {
    pp: ((cur - prev) / cap) * 100,
    ml: (cur - prev) * 1000,
    prevDate,
    n,
    total: dams.length
  };
}

/* ----------------------------------------------------------------------------
   RESERVOIR CARDS GRID (CLICK OPENS DEDICATED DAM PAGE)
   ---------------------------------------------------------------------------- */
function renderDamCards(regionName) {
  const container = document.getElementById('damCardsGrid');
  if (!container) return;

  let dams = getRegionDams(regionName);

  // Priority ordering for Pune region
  if (regionName === 'Pune') {
    const priorityOrder = [
      'khadakwasla', 'panshet', 'varasgaon', 'temghar', 'pavana',
      'mulshi', 'bhatghar', 'dimbhe', 'bhama-askhed',
      'chaskaman', 'koyna', 'bhima-ujjani', 'warna'
    ];
    dams.sort((a, b) => {
      const idxA = priorityOrder.indexOf(a.slug);
      const idxB = priorityOrder.indexOf(b.slug);
      if (idxA !== -1 && idxB !== -1) return idxA - idxB;
      if (idxA !== -1) return -1;
      if (idxB !== -1) return 1;
      return (Number(b.live_mcm) || 0) - (Number(a.live_mcm) || 0);
    });
  } else {
    dams.sort((a, b) => (Number(b.live_mcm) || 0) - (Number(a.live_mcm) || 0));
  }

  if (dams.length === 0) {
    container.innerHTML = '<div style="grid-column: 1/-1; padding: 40px; text-align: center; color: var(--text-muted);">No reservoirs found for this region.</div>';
    return;
  }

  let html = '';
  dams.forEach(dam => {
    const pct = Number(dam.pct) || 0;
    const liveMCM = Number(dam.live_mcm) || 0;
    const designMCM = Number(dam.design_live_mcm) || 0;
    const lastYearPct = Number(dam.last_year_pct) || 0;
    const remainingMCM = Math.max(0, designMCM - liveMCM);
    const liveTMC = liveMCM * 0.035315;
    const liveML = liveMCM * 1000;

    const status = getStatusDetails(pct);

    // YoY difference
    let yoyDiff = pct - lastYearPct;
    let yoyClass = 'yoy-neutral';
    let yoyText = `${lastYearPct.toFixed(1)}% Last Year`;
    if (lastYearPct > 0) {
      if (yoyDiff > 0) {
        yoyClass = 'yoy-up';
        yoyText = `↑ +${yoyDiff.toFixed(1)}% vs Last Year`;
      } else if (yoyDiff < 0) {
        yoyClass = 'yoy-down';
        yoyText = `↓ ${yoyDiff.toFixed(1)}% vs Last Year`;
      } else {
        yoyText = `= Same as Last Year`;
      }
    }

    const mrTitle = dam.name_mr && dam.name_mr !== dam.name_en ? `<span class="dam-title-mr">${escapeHtml(dam.name_mr)}</span>` : '';

    html += `
      <div class="reservoir-card" onclick="openDamPage('${escapeHtml(dam.slug)}')" title="Click to open dedicated reservoir page">
        <div class="card-top">
          <div class="dam-title-group">
            <h3>${escapeHtml(dam.name_en)}</h3>
            ${mrTitle}
          </div>
          <div class="card-badges">
            <span class="badge-tag">${escapeHtml(dam.district)}</span>
          </div>
        </div>

        <div class="card-storage-stat">
          <span class="card-pct ${status.textClass}">${pct.toFixed(1)}%</span>
          <span class="card-yoy-tag ${yoyClass}">${escapeHtml(yoyText)}</span>
        </div>

        <div class="card-progress-bar">
          <div class="card-progress-fill ${status.textClass}" style="width: ${Math.min(100, pct)}%;"></div>
        </div>

        <div class="card-details-grid">
          <div class="detail-cell">
            <span class="cell-label">Live Storage</span>
            <span class="cell-val">${liveMCM.toFixed(1)} MCM</span>
            <span class="cell-sub">${liveTMC.toFixed(2)} TMC (${liveML.toLocaleString()} ML)</span>
          </div>

          <div class="detail-cell">
            <span class="cell-label">Useful Capacity</span>
            <span class="cell-val">${designMCM.toFixed(1)} MCM</span>
            <span class="cell-sub">${remainingMCM.toFixed(1)} MCM to fill</span>
          </div>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

/* ----------------------------------------------------------------------------
   VIEW 2: DEDICATED DAM DETAIL PAGE (IMAGE 3 EXACT CLONE)
   ---------------------------------------------------------------------------- */
function renderDamDetailPage(dam) {
  const pct = Number(dam.pct) || 0;
  const liveMCM = Number(dam.live_mcm) || 0;
  const designMCM = Number(dam.design_live_mcm) || 0;
  const lastYearPct = Number(dam.last_year_pct) || 0;
  const remainingMCM = Math.max(0, designMCM - liveMCM);
  const liveTMC = liveMCM * 0.035315;
  const designTMC = designMCM * 0.035315;
  const liveML = liveMCM * 1000;
  const designML = designMCM * 1000;
  const status = getStatusDetails(pct);

  // Breadcrumbs
  document.getElementById('breadDistrictLink').innerText = dam.district;
  document.getElementById('breadDamName').innerText = dam.name_en;

  // Title Banner
  document.getElementById('dpTitle').innerText = dam.name_en;
  const talukaText = dam.taluka || dam.district;
  document.getElementById('dpSubtitle').innerText = `${talukaText} · ${dam.type || 'Major'} · Maharashtra WRD live storage`;

  // Primary Storage Card
  document.getElementById('dpCardDamName').innerText = dam.name_en;
  const pctElem = document.getElementById('dpCardPct');
  pctElem.innerText = `${pct.toFixed(2)}%`;
  pctElem.style.color = status.color;

  const fillBar = document.getElementById('dpCardProgressFill');
  fillBar.style.width = `${Math.min(100, pct)}%`;
  fillBar.style.backgroundColor = status.color;

  document.getElementById('dpCardStoredML').innerText = `${Math.round(liveML).toLocaleString('en-IN')} ML`;
  document.getElementById('dpCardStoredMCM').innerText = `${liveMCM.toFixed(1)} MCM · ${liveTMC.toFixed(2)} TMC`;

  document.getElementById('dpCardCapacityML').innerText = `${Math.round(designML).toLocaleString('en-IN')} ML`;
  document.getElementById('dpCardCapacityMCM').innerText = `${designMCM.toFixed(3)} MCM · ${designTMC.toFixed(2)} TMC`;

  document.getElementById('dpCardTodayPct').innerText = `${pct.toFixed(2)}%`;
  document.getElementById('dpCardRemainingMCM').innerText = `${remainingMCM.toFixed(1)} MCM to fill`;

  document.getElementById('dpCardLastYearPct').innerText = lastYearPct > 0 ? `${lastYearPct.toFixed(2)}%` : '—';
  
  const yoyDiffPP = pct - lastYearPct;
  const yoyPPElem = document.getElementById('dpCardYoYpp');
  if (lastYearPct > 0) {
    const sign = yoyDiffPP >= 0 ? '+' : '';
    const desc = yoyDiffPP >= 0 ? 'Higher YoY' : 'Lower YoY';
    yoyPPElem.innerText = `${sign}${yoyDiffPP.toFixed(2)} pp (${desc})`;
    yoyPPElem.style.color = yoyDiffPP >= 0 ? '#10b981' : '#ef4444';
  } else {
    yoyPPElem.innerText = 'Same-date comparison unavailable';
    yoyPPElem.style.color = 'var(--text-muted)';
  }

  const statusTag = document.getElementById('dpCardStatusTag');
  statusTag.innerText = status.label.toUpperCase();
  statusTag.style.color = status.color;

  const dateFormatted = formatDateDisplay(dam.date || latestSnapshot.batch_date);
  document.getElementById('dpCardDateStamp').innerText = `Data as of ${dateFormatted}`;

  document.getElementById('dpViewDistrictLink').innerText = `View all ${dam.district} district dams >`;

  // Dam Encyclopedia & Specifications
  const photo = document.getElementById('dpImage');
  const svgPlaceholder = "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22800%22%20height%3D%22500%22%20viewBox%3D%220%200%20800%20500%22%3E%3Crect%20width%3D%22100%25%22%20height%3D%22100%25%22%20fill%3D%22%23e2e8f0%22%2F%3E%3Cpath%20d%3D%22M360%20210h80v80h-80z%22%20fill%3D%22%2394a3b8%22%2F%3E%3Cpolygon%20points%3D%22400%2C170%20340%2C210%20460%2C210%22%20fill%3D%22%2364748b%22%2F%3E%3Ctext%20x%3D%22400%22%20y%3D%22320%22%20font-family%3D%22system-ui%2C%20sans-serif%22%20font-size%3D%2218%22%20font-weight%3D%22500%22%20fill%3D%22%23475569%22%20text-anchor%3D%22middle%22%3EPhoto%20not%20available%3C%2Ftext%3E%3Ctext%20x%3D%22400%22%20y%3D%22345%22%20font-family%3D%22system-ui%2C%20sans-serif%22%20font-size%3D%2213%22%20fill%3D%22%2394a3b8%22%20text-anchor%3D%22middle%22%3EAwaiting%20verified%20reservoir%20photography%3C%2Ftext%3E%3C%2Fsvg%3E";
  
  if (dam.image_url && dam.image_url.trim().length > 0) {
    photo.src = dam.image_url.trim();
    photo.alt = `${dam.name_en} Reservoir in ${dam.district} district, Maharashtra`;
    document.getElementById('dpPhotoCaption').innerText = `${dam.name_en} Reservoir (${dam.name_mr || dam.name_en}), ${dam.district}, Maharashtra`;
  } else {
    photo.src = svgPlaceholder;
    photo.alt = `Photo not available for ${dam.name_en}`;
    document.getElementById('dpPhotoCaption').innerText = `Photo not available · ${dam.name_en} (${dam.district})`;
  }

  const descElem = document.getElementById('dpDescription');
  if (dam.description && dam.description.trim().length > 0) {
    descElem.innerText = dam.description.trim();
    descElem.style.display = 'block';
  } else {
    descElem.innerText = '';
    descElem.style.display = 'none';
  }

  document.getElementById('dpSpecLocation').innerText = dam.taluka ? `${dam.district} / ${dam.taluka}` : (dam.district || '—');
  document.getElementById('dpSpecCity').innerText = dam.nearest_city || '—';
  document.getElementById('dpSpecRiver').innerText = dam.river ? (dam.river.toLowerCase().includes('river') ? dam.river : `${dam.river} River`) : '—';
  document.getElementById('dpSpecBasin').innerText = dam.basin ? (dam.basin.toLowerCase().includes('basin') ? dam.basin : `${dam.basin} River Basin`) : '—';
  document.getElementById('dpSpecYear').innerText = dam.year ? String(dam.year) : '—';
  
  if (dam.height_m && dam.length_m) {
    document.getElementById('dpSpecDimensions').innerText = `${dam.height_m} m / ${Number(dam.length_m).toLocaleString('en-IN')} m`;
  } else if (dam.height_m) {
    document.getElementById('dpSpecDimensions').innerText = `${dam.height_m} m`;
  } else if (dam.length_m) {
    document.getElementById('dpSpecDimensions').innerText = `${Number(dam.length_m).toLocaleString('en-IN')} m`;
  } else {
    document.getElementById('dpSpecDimensions').innerText = '—';
  }

  document.getElementById('dpSpecDead').innerText = dam.dead_mcm != null ? `${dam.dead_mcm} MCM` : '—';
  document.getElementById('dpSpecGross').innerText = dam.design_gross_mcm != null ? `${dam.design_gross_mcm} MCM` : (designMCM > 0 ? `${designMCM.toFixed(2)} MCM (Live)` : '—');
  document.getElementById('dpSpecPurpose').innerText = dam.purpose || '—';

  // Wikipedia Supplementary Reference Link
  const wikiWrap = document.getElementById('dpWikiLinkWrap');
  const wikiLink = document.getElementById('dpWikiLink');
  if (wikiWrap && wikiLink) {
    if (dam.wikipedia_url && dam.wikipedia_url.trim().length > 0) {
      wikiLink.href = dam.wikipedia_url.trim();
      wikiWrap.style.display = 'block';
    } else {
      wikiWrap.style.display = 'none';
    }
  }

  // Dedicated Historical Trend Chart for this Dam
  document.getElementById('dpChartDamName').innerText = dam.name_en;
  renderDamDetailTrendChart(dam.slug, currentDamDetailChartDays);

  // Render "Other Major Dams in {District}" Grid (Image 3 bottom)
  renderOtherDamsGrid(dam);
}

function renderOtherDamsGrid(activeDam) {
  const container = document.getElementById('dpOtherDamsGrid');
  const title = document.getElementById('dpOtherDamsTitle');
  if (!container || !title) return;

  title.innerText = `Other major dams in ${activeDam.district}`;

  const allDams = getDamList();
  // Filter other dams in same district
  let others = allDams.filter(d => d.district === activeDam.district && d.slug !== activeDam.slug);
  
  // If fewer than 4 in district, supplement with other dams from same division
  if (others.length < 4) {
    const divOthers = allDams.filter(d => d.division === activeDam.division && d.slug !== activeDam.slug && !others.includes(d));
    others = [...others, ...divOthers];
  }

  // Sort by highest percentage / capacity
  others.sort((a, b) => (Number(b.live_mcm) || 0) - (Number(a.live_mcm) || 0));

  if (others.length === 0) {
    container.innerHTML = '<div style="grid-column: 1/-1; color: var(--text-muted);">No other major dams in this district.</div>';
    return;
  }

  let html = '';
  others.forEach(d => {
    const pct = Number(d.pct) || 0;
    const status = getStatusDetails(pct);
    const mrSpan = d.name_mr && d.name_mr !== d.name_en ? `<span class="other-dam-mr">${escapeHtml(d.name_mr)}</span>` : '';

    html += `
      <div class="other-dam-pill" onclick="openDamPage('${escapeHtml(d.slug)}')">
        <div>
          <span class="other-dam-name">${escapeHtml(d.name_en)}</span>
          ${mrSpan}
        </div>
        <span class="other-dam-pct ${status.textClass}">${pct.toFixed(2)}%</span>
      </div>
    `;
  });

  container.innerHTML = html;
}

function setDamDetailChartDays(days, btnElem) {
  currentDamDetailChartDays = days;
  const buttons = document.querySelectorAll('.dam-chart-header .range-btn');
  buttons.forEach(b => b.classList.remove('active'));
  if (btnElem) btnElem.classList.add('active');

  if (currentDamSlug) {
    renderDamDetailTrendChart(currentDamSlug, days);
  }
}

async function renderDamDetailTrendChart(slug, days) {
  const canvas = document.getElementById('damDetailTrendChart');
  if (!canvas) return;

  const history = await loadDamHistory(slug);
  const colors = getThemeColors();

  let filtered = [...history];
  if (days !== 'all' && typeof days === 'number') {
    filtered = filtered.slice(-days);
  }

  const labels = filtered.map(pt => {
    const dt = pt.d || pt.date;
    const parts = dt.split('-');
    return parts.length === 3 ? `${parts[2]}/${parts[1]}` : dt;
  });

  const dataPoints = filtered.map(pt => pt.p !== undefined ? pt.p : pt.pct);

  if (damDetailChartInstance) {
    damDetailChartInstance.destroy();
  }

  const ctx = canvas.getContext('2d');
  damDetailChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Storage Level (%)',
        data: dataPoints,
        borderColor: '#10b981',
        backgroundColor: colors.isDark ? 'rgba(16, 185, 129, 0.15)' : 'rgba(16, 185, 129, 0.08)',
        fill: true,
        borderWidth: 2.5,
        pointRadius: filtered.length > 60 ? 0 : 2.5,
        tension: 0.2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { color: colors.gridColor, drawBorder: false },
          ticks: {
            color: colors.textColor,
            font: { family: 'Inter', size: 10 },
            maxTicksLimit: 12
          }
        },
        y: {
          min: 0,
          max: 100,
          grid: { color: colors.gridColor, drawBorder: false },
          ticks: {
            color: colors.textColor,
            font: { family: 'Inter', size: 10 },
            callback: function(v) { return v + '%'; }
          }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: colors.tooltipBg,
          titleColor: colors.tooltipText,
          bodyColor: colors.tooltipText,
          borderColor: colors.tooltipBorder,
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: function(ctx) { return ` Storage: ${ctx.parsed.y.toFixed(2)}%`; }
          }
        }
      }
    }
  });
}

/* ----------------------------------------------------------------------------
   OVERVIEW CHARTS (TRENDS & VOLUME BAR)
   ---------------------------------------------------------------------------- */
function setChartDays(days, btnElem) {
  currentChartDays = days;
  const buttons = document.querySelectorAll('.chart-controls .range-btn');
  buttons.forEach(b => b.classList.remove('active'));
  if (btnElem) btnElem.classList.add('active');
  renderTrendChart(days);
}

async function loadDamHistory(slug) {
  if (historyCache[slug]) return historyCache[slug];
  try {
    const resp = await fetch(`data/history/${slug}.json?v=` + Date.now());
    if (resp.ok) {
      const data = await resp.json();
      historyCache[slug] = data;
      return data;
    }
  } catch (err) {}
  return [];
}

async function renderTrendChart(days) {
  const canvas = document.getElementById('trendChart');
  if (!canvas) return;

  const chartFilter = document.getElementById('chartDamFilter');
  const selectedSlug = chartFilter ? chartFilter.value : 'ALL';
  const colors = getThemeColors();

  let targetDams = [];
  if (selectedSlug === 'ALL') {
    const regionDams = getRegionDams(currentActiveRegion);
    targetDams = [...regionDams]
      .sort((a, b) => (Number(b.design_live_mcm) || 0) - (Number(a.design_live_mcm) || 0))
      .slice(0, 5);
  } else {
    const allDams = getDamList();
    const found = allDams.find(d => d.slug === selectedSlug);
    if (found) targetDams = [found];
  }

  if (targetDams.length === 0) return;

  const histories = await Promise.all(targetDams.map(d => loadDamHistory(d.slug)));

  let dateSet = new Set();
  histories.forEach(h => {
    if (Array.isArray(h)) {
      h.forEach(pt => {
        if (pt.d || pt.date) dateSet.add(pt.d || pt.date);
      });
    }
  });

  let sortedDates = Array.from(dateSet).sort();
  if (days !== 'all' && typeof days === 'number') {
    sortedDates = sortedDates.slice(-days);
  }

  const datasets = targetDams.map((dam, idx) => {
    const history = histories[idx] || [];
    const valMap = {};
    history.forEach(pt => {
      const dt = pt.d || pt.date;
      const pct = pt.p !== undefined ? pt.p : pt.pct;
      if (dt) valMap[dt] = Number(pct) || 0;
    });

    const dataPoints = sortedDates.map(dt => valMap[dt] !== undefined ? valMap[dt] : null);
    const color = DAM_COLORS[idx % DAM_COLORS.length];

    return {
      label: `${dam.name_en} (%)`,
      data: dataPoints,
      borderColor: color,
      backgroundColor: color,
      borderWidth: 2,
      pointRadius: sortedDates.length > 60 ? 0 : 2,
      tension: 0.2,
      fill: false,
      spanGaps: true
    };
  });

  if (trendChartInstance) {
    trendChartInstance.destroy();
  }

  const ctx = canvas.getContext('2d');
  trendChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: sortedDates.map(d => {
        const parts = d.split('-');
        return parts.length === 3 ? `${parts[2]}/${parts[1]}` : d;
      }),
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            boxWidth: 10,
            usePointStyle: true,
            color: colors.textColor,
            font: { family: 'Inter', size: 11, weight: '500' }
          }
        },
        tooltip: {
          backgroundColor: colors.tooltipBg,
          titleColor: colors.tooltipText,
          bodyColor: colors.tooltipText,
          borderColor: colors.tooltipBorder,
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: function(context) {
              return ` ${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: colors.gridColor, drawBorder: false },
          ticks: { color: colors.textColor, font: { family: 'Inter', size: 10 }, maxTicksLimit: 12 }
        },
        y: {
          min: 0,
          max: 100,
          grid: { color: colors.gridColor, drawBorder: false },
          ticks: { color: colors.textColor, font: { family: 'Inter', size: 10 }, callback: function(v) { return v + '%'; } }
        }
      }
    }
  });
}

function renderVolumeChart() {
  const canvas = document.getElementById('volumeChart');
  if (!canvas) return;

  const regionDams = getRegionDams(currentActiveRegion);
  const colors = getThemeColors();

  const sorted = [...regionDams]
    .sort((a, b) => (Number(b.design_live_mcm) || 0) - (Number(a.design_live_mcm) || 0))
    .slice(0, 7);

  if (sorted.length === 0) return;

  const labels = sorted.map(d => d.name_en);
  const storedData = sorted.map(d => Number(d.live_mcm) || 0);
  const remainingData = sorted.map(d => Math.max(0, (Number(d.design_live_mcm) || 0) - (Number(d.live_mcm) || 0)));

  if (volumeChartInstance) {
    volumeChartInstance.destroy();
  }

  const ctx = canvas.getContext('2d');
  volumeChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Stored Water (MCM)',
          data: storedData,
          backgroundColor: '#2563eb',
          borderRadius: 4
        },
        {
          label: 'Remaining Capacity (MCM)',
          data: remainingData,
          backgroundColor: colors.isDark ? '#334155' : '#cbd5e1',
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
          ticks: { color: colors.textColor, font: { family: 'Inter', size: 10 }, maxRotation: 30 }
        },
        y: {
          stacked: true,
          grid: { color: colors.gridColor, drawBorder: false },
          ticks: { color: colors.textColor, font: { family: 'Inter', size: 10 }, callback: function(v) { return v + ' M'; } }
        }
      },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: { boxWidth: 10, color: colors.textColor, font: { family: 'Inter', size: 11, weight: '500' } }
        },
        tooltip: {
          backgroundColor: colors.tooltipBg,
          titleColor: colors.tooltipText,
          bodyColor: colors.tooltipText,
          borderColor: colors.tooltipBorder,
          borderWidth: 1,
          padding: 10
        }
      }
    }
  });
}

/* ----------------------------------------------------------------------------
   SEARCH & FILTER DATA TABLE
   ---------------------------------------------------------------------------- */
function filterTable() {
  const allDams = getDamList();
  const basinFilter = document.getElementById('basinSelectFilter')?.value || 'ALL';
  const districtFilter = document.getElementById('districtSelectFilter')?.value || 'ALL';
  const statusFilter = document.getElementById('statusSelectFilter')?.value || 'ALL';
  const searchTxt = (document.getElementById('tableSearchInput')?.value || '').trim().toLowerCase();

  filteredRecords = allDams.filter(dam => {
    if (basinFilter !== 'ALL' && dam.basin !== basinFilter) return false;
    if (districtFilter !== 'ALL' && dam.district !== districtFilter) return false;

    const pct = Number(dam.pct) || 0;
    if (statusFilter === 'HEALTHY' && pct < 50) return false;
    if (statusFilter === 'MODERATE' && (pct < 25 || pct >= 50)) return false;
    if (statusFilter === 'LOW' && (pct < 10 || pct >= 25)) return false;
    if (statusFilter === 'CRITICAL' && pct >= 10) return false;

    if (searchTxt) {
      const matchEn = dam.name_en && dam.name_en.toLowerCase().includes(searchTxt);
      const matchMr = dam.name_mr && dam.name_mr.toLowerCase().includes(searchTxt);
      const matchDist = dam.district && dam.district.toLowerCase().includes(searchTxt);
      const matchDiv = dam.division && dam.division.toLowerCase().includes(searchTxt);
      const matchBasin = dam.basin && dam.basin.toLowerCase().includes(searchTxt);
      if (!matchEn && !matchMr && !matchDist && !matchDiv && !matchBasin) return false;
    }

    return true;
  });

  filteredRecords.sort((a, b) => a.name_en.localeCompare(b.name_en));
  currentPage = 1;
  renderTable();
}

function renderTable() {
  const tbody = document.getElementById('tableBody');
  const countText = document.getElementById('recordsCountText');
  const pageIndicator = document.getElementById('pageIndicator');
  const prevBtn = document.getElementById('prevPageBtn');
  const nextBtn = document.getElementById('nextPageBtn');

  if (!tbody) return;

  const total = filteredRecords.length;
  const totalPages = Math.ceil(total / pageSize) || 1;
  currentPage = Math.min(currentPage, totalPages);

  const startIdx = (currentPage - 1) * pageSize;
  const endIdx = Math.min(startIdx + pageSize, total);
  const pageRecords = filteredRecords.slice(startIdx, endIdx);

  if (countText) countText.innerText = total > 0 ? `Showing ${startIdx + 1}–${endIdx} of ${total} reservoirs` : '0 records found';
  if (pageIndicator) pageIndicator.innerText = `Page ${currentPage} of ${totalPages}`;
  if (prevBtn) prevBtn.disabled = currentPage <= 1;
  if (nextBtn) nextBtn.disabled = currentPage >= totalPages;

  if (pageRecords.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 32px; color: var(--text-muted);">No reservoirs match the active search criteria.</td></tr>`;
    return;
  }

  let html = '';
  pageRecords.forEach(d => {
    const liveMCM = Number(d.live_mcm) || 0;
    const designMCM = Number(d.design_live_mcm) || 0;
    const liveTMC = liveMCM * 0.035315;
    const pct = Number(d.pct) || 0;
    const lastYearPct = Number(d.last_year_pct) || 0;
    const status = getStatusDetails(pct);

    const mrSpan = d.name_mr && d.name_mr !== d.name_en ? `<span class="table-dam-mr">${escapeHtml(d.name_mr)}</span>` : '';

    html += `
      <tr>
        <td>
          <span class="table-dam-name" onclick="openDamPage('${escapeHtml(d.slug)}')">${escapeHtml(d.name_en)}</span>
          ${mrSpan}
        </td>
        <td>${escapeHtml(d.division)}</td>
        <td>${escapeHtml(d.district)}</td>
        <td>${escapeHtml(d.basin || 'Krishna')}</td>
        <td class="text-right"><strong>${liveMCM.toFixed(1)}</strong></td>
        <td class="text-right">${liveTMC.toFixed(2)}</td>
        <td class="text-right">${designMCM.toFixed(1)}</td>
        <td class="text-center">
          <span class="table-pct-badge" style="background-color: var(--accent-green-bg); color: ${status.color};">${pct.toFixed(1)}%</span>
        </td>
        <td class="text-right">${lastYearPct > 0 ? lastYearPct.toFixed(1) + '%' : '—'}</td>
        <td class="text-center">
          <button class="btn-ghost" style="padding: 2px 8px; font-size: 0.72rem;" onclick="openDamPage('${escapeHtml(d.slug)}')">View &gt;</button>
        </td>
      </tr>
    `;
  });

  tbody.innerHTML = html;
}

function changePage(delta) {
  currentPage += delta;
  renderTable();
}

function exportTableToCSV() {
  if (filteredRecords.length === 0) {
    alert('No data records available to export.');
    return;
  }

  const headers = [
    'Dam Name', 'Marathi Name', 'Division', 'District', 'River Basin',
    'Live Storage (MCM)', 'Live Storage (TMC)', 'Design Live Capacity (MCM)',
    'Storage Percentage (%)', 'Last Year Percentage (%)', 'Status'
  ];

  const rows = filteredRecords.map(d => {
    const liveMCM = Number(d.live_mcm) || 0;
    const designMCM = Number(d.design_live_mcm) || 0;
    const liveTMC = (liveMCM * 0.035315).toFixed(2);
    const pct = Number(d.pct) || 0;
    const lastPct = Number(d.last_year_pct) || 0;
    const status = getStatusDetails(pct).label;

    return [
      `"${d.name_en}"`,
      `"${d.name_mr || d.name_en}"`,
      `"${d.division}"`,
      `"${d.district}"`,
      `"${d.basin || 'Krishna'}"`,
      liveMCM.toFixed(2),
      liveTMC,
      designMCM.toFixed(2),
      pct.toFixed(2),
      lastPct.toFixed(2),
      status
    ].join(',');
  });

  const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows].join('\n');
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `maharashtra_dam_storage_${latestSnapshot?.batch_date || 'data'}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/* ----------------------------------------------------------------------------
   HISTORICAL DATE TIME MACHINE (SYNC PICKER)
   ---------------------------------------------------------------------------- */
async function onDateSyncSelected(isoDate) {
  if (!isoDate) return;
  currentSyncedDate = isoDate;

  const resetBtn = document.getElementById('resetDateSyncBtn');
  if (resetBtn) resetBtn.style.display = 'inline-flex';

  const dateText = document.getElementById('lastUpdatedText');
  if (dateText) dateText.innerText = `${formatDateDisplay(isoDate)} (Historical)`;

  const allDams = getDamList();
  const updatedDams = {};

  await Promise.all(allDams.map(async dam => {
    const history = await loadDamHistory(dam.slug);
    const point = (history || []).find(pt => (pt.d || pt.date) === isoDate);
    if (point) {
      updatedDams[dam.slug] = {
        ...dam,
        live_mcm: point.m !== undefined ? point.m : point.mcm,
        pct: point.p !== undefined ? point.p : point.pct,
        date: isoDate
      };
    } else {
      updatedDams[dam.slug] = dam;
    }
  }));

  latestSnapshot = {
    ...latestSnapshot,
    batch_date: isoDate,
    dams: updatedDams
  };

  updateHeroAnalytics(currentActiveRegion);
  renderDamCards(currentActiveRegion);
  filterTable();

  if (currentDamSlug && latestSnapshot.dams[currentDamSlug]) {
    renderDamDetailPage(latestSnapshot.dams[currentDamSlug]);
  }
}





function resetDateSync() {
  currentSyncedDate = null;
  latestSnapshot = JSON.parse(JSON.stringify(originalLatestSnapshot));

  const resetBtn = document.getElementById('resetDateSyncBtn');
  if (resetBtn) resetBtn.style.display = 'none';

  if (document.getElementById('lastUpdatedText')) {
    const dateFormatted = formatDateDisplay(latestSnapshot.batch_date);
    document.getElementById('lastUpdatedText').innerText = `${dateFormatted} (Live)`;
  }

  const picker = document.getElementById('syncDatePicker');
  if (picker && latestSnapshot.batch_date) {
    picker.value = latestSnapshot.batch_date;
  }

  updateHeroAnalytics(currentActiveRegion);
  renderDamCards(currentActiveRegion);
  filterTable();

  if (currentDamSlug && latestSnapshot.dams[currentDamSlug]) {
    renderDamDetailPage(latestSnapshot.dams[currentDamSlug]);
  }
}

/* ----------------------------------------------------------------------------
   QUICK SEARCH MODAL & GLOBAL COMMAND PALETTE (CTRL+K / CMD+K)
   ---------------------------------------------------------------------------- */
let quickSearchResults = [];
let quickSearchSelectedIndex = 0;

function openQuickSearchModal() {
  const modal = document.getElementById('quickSearchModal');
  const input = document.getElementById('quickSearchModalInput');
  if (!modal || !input) return;

  modal.style.display = 'flex';
  input.value = '';
  quickSearchSelectedIndex = 0;
  onQuickSearchInput('');
  setTimeout(() => input.focus(), 60);
}

function closeQuickSearchModal() {
  const modal = document.getElementById('quickSearchModal');
  if (modal) modal.style.display = 'none';
}

function closeQuickSearchOnBackdrop(event) {
  if (event.target && event.target.id === 'quickSearchModal') {
    closeQuickSearchModal();
  }
}

function onQuickSearchInput(query) {
  const container = document.getElementById('quickSearchResultsList');
  if (!container) return;

  const allDams = getDamList();
  const q = (query || '').trim().toLowerCase();

  let matches = allDams;
  if (q) {
    matches = allDams.filter(d => {
      const matchEn = d.name_en && d.name_en.toLowerCase().includes(q);
      const matchMr = d.name_mr && d.name_mr.toLowerCase().includes(q);
      const matchDist = d.district && d.district.toLowerCase().includes(q);
      const matchDiv = d.division && d.division.toLowerCase().includes(q);
      const matchBasin = d.basin && d.basin.toLowerCase().includes(q);
      const matchRiver = d.river && d.river.toLowerCase().includes(q);
      return matchEn || matchMr || matchDist || matchDiv || matchBasin || matchRiver;
    });
  }

  // Sort by highest capacity / relevance
  matches.sort((a, b) => (Number(b.live_mcm) || 0) - (Number(a.live_mcm) || 0));
  quickSearchResults = matches.slice(0, 20);
  quickSearchSelectedIndex = 0;

  if (quickSearchResults.length === 0) {
    container.innerHTML = `<div class="quick-search-empty">No reservoirs found matching "<strong>${escapeHtml(query)}</strong>". Try searching by district (e.g. Pune, Satara, Nashik).</div>`;
    return;
  }

  renderQuickSearchResults();
}

function renderQuickSearchResults() {
  const container = document.getElementById('quickSearchResultsList');
  if (!container) return;

  let html = '';
  quickSearchResults.forEach((dam, idx) => {
    const pct = Number(dam.pct) || 0;
    const status = getStatusDetails(pct);
    const selectedClass = idx === quickSearchSelectedIndex ? 'selected' : '';
    const mrSpan = dam.name_mr && dam.name_mr !== dam.name_en ? `<span class="qs-name-mr">${escapeHtml(dam.name_mr)}</span>` : '';
    const riverOrBasin = dam.river || dam.basin || 'Krishna';

    html += `
      <div class="quick-search-item ${selectedClass}" onclick="selectQuickSearchResult('${escapeHtml(dam.slug)}')" onmouseenter="setQuickSearchHover(${idx})">
        <div class="qs-left">
          <div class="qs-title-row">
            <span class="qs-name-en">${escapeHtml(dam.name_en)}</span>
            ${mrSpan}
          </div>
          <div class="qs-meta">${escapeHtml(dam.district)} · ${escapeHtml(dam.division)} · ${escapeHtml(riverOrBasin)}</div>
        </div>
        <div class="qs-right">
          <span class="qs-pct-tag" style="background-color: var(--accent-green-bg); color: ${status.color};">${pct.toFixed(1)}%</span>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

function setQuickSearchHover(idx) {
  quickSearchSelectedIndex = idx;
  const items = document.querySelectorAll('.quick-search-item');
  items.forEach((it, i) => {
    if (i === idx) it.classList.add('selected');
    else it.classList.remove('selected');
  });
}

function selectQuickSearchResult(slug) {
  closeQuickSearchModal();
  openDamPage(slug);
}

function onQuickSearchKeydown(event) {
  if (event.key === 'Escape') {
    closeQuickSearchModal();
    return;
  }
  if (event.key === 'ArrowDown') {
    event.preventDefault();
    if (quickSearchResults.length > 0) {
      quickSearchSelectedIndex = (quickSearchSelectedIndex + 1) % quickSearchResults.length;
      renderQuickSearchResults();
      scrollSelectedQuickSearchIntoView();
    }
    return;
  }
  if (event.key === 'ArrowUp') {
    event.preventDefault();
    if (quickSearchResults.length > 0) {
      quickSearchSelectedIndex = (quickSearchSelectedIndex - 1 + quickSearchResults.length) % quickSearchResults.length;
      renderQuickSearchResults();
      scrollSelectedQuickSearchIntoView();
    }
    return;
  }
  if (event.key === 'Enter') {
    event.preventDefault();
    if (quickSearchResults[quickSearchSelectedIndex]) {
      selectQuickSearchResult(quickSearchResults[quickSearchSelectedIndex].slug);
    }
  }
}

function scrollSelectedQuickSearchIntoView() {
  const container = document.getElementById('quickSearchResultsList');
  const selected = container ? container.querySelector('.quick-search-item.selected') : null;
  if (selected) {
    selected.scrollIntoView({ block: 'nearest' });
  }
}

function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/* ----------------------------------------------------------------------------
   SCROLL TO TOP ("UP") BUTTON
   ---------------------------------------------------------------------------- */
function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

window.addEventListener('scroll', () => {
  const topBtn = document.getElementById('scrollToTopBtn');
  if (topBtn) {
    if (window.scrollY > 300) {
      topBtn.classList.add('visible');
    } else {
      topBtn.classList.remove('visible');
    }
  }
});

// Global Keyboard Shortcut listener (Cmd+K / Ctrl+K / '/' key)
document.addEventListener('keydown', (e) => {
  if ((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K')) {
    e.preventDefault();
    const modal = document.getElementById('quickSearchModal');
    if (modal && modal.style.display === 'flex') {
      closeQuickSearchModal();
    } else {
      openQuickSearchModal();
    }
    return;
  }

  if (e.key === 'Escape') {
    closeQuickSearchModal();
  }
});
