"use strict";

const MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const TIER_COLOR = { High: "#dc2626", Watch: "#d97706", Low: "#94a3b8" };
const state = { disease: "Dengue", month: 8 };
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
let DATA = {};
const markers = {};           // district_id -> leaflet marker
let markerLayer, districtById;

async function boot() {
  const [districts, forecasts, validation, meta] = await Promise.all(
    ["districts", "forecasts", "validation", "meta"].map(n => fetch(`data/${n}.json`).then(r => r.json()))
  );
  DATA = { districts, forecasts, validation, meta };
  districtById = Object.fromEntries(districts.map(d => [d.id, d]));

  // hero stat
  const cap = validation.dengue_capture_caseweighted_pct;
  if (cap) {
    document.getElementById("heroNum").textContent = cap.value + "%";
    const alt = validation.alt_perdistrict_fit_caseweighted_pct, ch = validation.chance_baseline_pct;
    document.getElementById("heroStat").title =
      `Fixed monsoon prior (Jul–Sep). Held-out case-weighted capture ${cap.value}% ` +
      `vs ${ch ? ch.value : "?"}% chance; a per-district data-fit does worse (${alt ? alt.value : "?"}%).`;
  }
  document.getElementById("footSource").textContent = "Data: " + (meta.source || "");

  buildDiseaseToggle(meta.diseases);
  initMap();
  wireControls();
  render();
}

function buildDiseaseToggle(diseases) {
  const el = document.getElementById("diseaseToggle");
  el.innerHTML = "";
  diseases.forEach(d => {
    const b = document.createElement("button");
    b.textContent = d === "Acute Diarrhoeal Disease" ? "Diarrhoeal (ADD)" : d;
    b.setAttribute("aria-pressed", String(d === state.disease));
    b.onclick = () => { state.disease = d; [...el.children].forEach(c => c.setAttribute("aria-pressed", String(c === b))); render(); };
    el.appendChild(b);
  });
}

function initMap() {
  const map = L.map("map", { zoomControl: true, scrollWheelZoom: true }).setView([20.5, 81], 5);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; OpenStreetMap &copy; CARTO', subdomains: "abcd", maxZoom: 12
  }).addTo(map);
  markerLayer = L.layerGroup().addTo(map);
  window._map = map;
}

function radiusFor(score) {
  const s = Math.max(0, score || 0);
  return Math.min(22, 4 + Math.sqrt(s) * 0.9);   // sqrt scale, clamped
}

function render() {
  const fc = (DATA.forecasts[state.disease] || {})[String(state.month)] || {};
  markerLayer.clearLayers();
  for (const k in markers) delete markers[k];

  Object.entries(fc).forEach(([id, f]) => {
    const d = districtById[id];
    if (!d || d.lat == null || d.lon == null) return;
    const m = L.circleMarker([d.lat, d.lon], {
      radius: radiusFor(f.score), color: TIER_COLOR[f.tier] || "#94a3b8",
      weight: 1, fillColor: TIER_COLOR[f.tier] || "#94a3b8",
      fillOpacity: f.tier === "Low" ? 0.28 : 0.62
    }).bindPopup(
      `<span class="pop-name">${esc(d.name)}</span> · ${esc(d.state)}<br>` +
      `<span class="pop-tier" style="color:${TIER_COLOR[f.tier] || "#94a3b8"}">${esc(f.tier)}</span> risk · ` +
      `~${Math.round(f.score)} cases/yr this month<br><small>${esc(f.drivers || "")}</small>`
    );
    m.addTo(markerLayer);
    markers[id] = m;
  });

  renderRail(fc);
}

function renderRail(fc) {
  const rank = { High: 0, Watch: 1, Low: 2 };
  const rows = Object.entries(fc)
    .filter(([, f]) => f.tier === "High" || f.tier === "Watch")
    .sort((a, b) => (rank[a[1].tier] - rank[b[1].tier]) || (b[1].score - a[1].score))
    .slice(0, 20);

  const list = document.getElementById("railList");
  list.innerHTML = "";
  rows.forEach(([id, f], i) => {
    const d = districtById[id] || { name: id, state: "" };
    const li = document.createElement("li");
    li.className = "rail-item";
    const tierClass = f.tier === "High" ? "High" : "Watch";
    li.innerHTML =
      `<span class="rail-rank">${i + 1}</span>` +
      `<span class="rail-name">${esc(d.name)}</span>` +
      `<span class="rail-badge ${tierClass}">${esc(f.tier)}</span>` +
      `<span class="rail-state">${esc(d.state)}</span>` +
      `<span class="rail-score">~${Math.round(f.score)} cases/yr</span>` +
      `<span class="rail-driver">${esc(f.drivers || "")}</span>`;
    li.onclick = () => {
      const m = markers[id];
      if (m) { window._map.setView(m.getLatLng(), 7, { animate: true }); m.openPopup(); }
    };
    list.appendChild(li);
  });

  document.getElementById("railSub").textContent =
    `${state.disease === "Acute Diarrhoeal Disease" ? "Diarrhoeal" : state.disease} · ${MONTHS[state.month]}`;
  document.getElementById("railNote").textContent = rows.length
    ? `${rows.length} districts at High/Watch. Ranked by expected burden this month.`
    : "No elevated-risk districts for this month — off-season.";
}

function wireControls() {
  const slider = document.getElementById("monthSlider"), label = document.getElementById("monthLabel");
  label.textContent = MONTHS[state.month];
  slider.value = state.month;
  slider.oninput = () => { state.month = +slider.value; label.textContent = MONTHS[state.month]; render(); };
}

boot().catch(err => {
  const pre = document.createElement("pre");
  pre.style.cssText = "color:#dc2626;padding:1rem";
  pre.textContent = "Failed to load: " + err;
  document.body.prepend(pre);
  console.error(err);
});
