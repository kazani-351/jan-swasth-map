"use strict";

const MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
// single source of truth for tier colors = the CSS custom properties (--high/--watch/--low)
const cssVar = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim() || "#94a3b8";
const TIER_COLOR = { High: cssVar("--high"), Watch: cssVar("--watch"), Low: cssVar("--low") };
const TREND = { rising: "↑ rising", falling: "↓ easing", flat: "→ steady" };
// Set to your deployed Response Agent Worker URL to activate the live LLM agent (empty = deterministic only).
const AGENT_ENDPOINT = "https://jan-swasth-agent.kazani.workers.dev";

async function askAgent(context, question) {
  if (!AGENT_ENDPOINT) return null;
  try {
    const r = await fetch(AGENT_ENDPOINT, {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ context, question }),
    });
    const d = await r.json();
    return d && d.text ? d.text : null;   // {fallback:true} or error -> null -> client falls back
  } catch {
    return null;
  }
}
const state = { disease: "Dengue", month: 8 };
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
let DATA = {};
const markers = {};           // district_id -> leaflet marker
let markerLayer, districtById;

async function boot() {
  const [districts, forecasts, validation, caseStudy, meta] = await Promise.all(
    ["districts", "forecasts", "validation", "case_study", "meta"].map(n => fetch(`data/${n}.json`).then(r => r.json()))
  );
  DATA = { districts, forecasts, validation, caseStudy, meta };
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
  wireViewNav();
  render();
  renderValidation();
}

function wireViewNav() {
  const nav = document.getElementById("viewNav");
  const mapView = document.getElementById("mapView");
  const valView = document.getElementById("validationView");
  nav.querySelectorAll("button").forEach(b => {
    b.onclick = () => {
      const isMap = b.dataset.view === "map";
      nav.querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
      mapView.hidden = !isMap;
      valView.hidden = isMap;
      if (isMap && window._map) setTimeout(() => window._map.invalidateSize(), 0);
    };
  });
}

function renderValidation() {
  const v = DATA.validation, cs = DATA.caseStudy;
  const cap = v.dengue_capture_caseweighted_pct.value, uw = v.dengue_capture_unweighted_pct.value;
  document.getElementById("vlede").textContent =
    `A deliberately simple, transparent model — dengue risk concentrates in the Jul–Sep monsoon — ` +
    `captures ${cap}% of the dengue case-burden in years it was never fit to (2016–19), ~3.4× better than chance, ` +
    `and it beats data-driven alternatives that overfit.`;

  const rows = [
    { label: "Monsoon prior (our model)", val: +v.dengue_capture_caseweighted_pct.value, hi: true },
    { label: "Window fit to training data", val: +v.alt_trainfit_window_caseweighted_pct.value },
    { label: "Per-district data fit", val: +v.alt_perdistrict_fit_caseweighted_pct.value },
    { label: "Chance", val: +v.chance_baseline_pct.value, chance: true },
  ];
  document.getElementById("modelBars").innerHTML = rows.map(r =>
    `<div class="mb-row ${r.hi ? "hi" : ""} ${r.chance ? "mb-chance" : ""}">` +
    `<span class="mb-label">${esc(r.label)}</span>` +
    `<span class="mb-track"><span class="mb-fill" style="width:${Math.max(0, Math.min(100, r.val))}%"></span></span>` +
    `<span class="mb-val">${r.val.toFixed(1)}%</span></div>`).join("");

  document.getElementById("csTitle").textContent = `Held out: the ${cs.year} ${cs.district} dengue epidemic`;
  const inWin = cs.series_2017.reduce((a, c, i) => a + (cs.model_peak_months.includes(i + 1) ? c : 0), 0);
  const pct = cs.total_2017 ? Math.round(inWin / cs.total_2017 * 100) : 0;
  document.getElementById("csSub").textContent =
    `${cs.train_note} In the held-out ${cs.year} season, ${pct}% of the outbreak's ${cs.total_2017.toLocaleString()} cases fell inside the predicted Jul–Sep window.`;
  document.getElementById("caseChart").innerHTML = caseChartSVG(cs) + caseLegend();

  const caveats = [
    `Case-weighted capture is ${cap}%; the unweighted month-hit rate is ${uw}% — small, scattered off-season outbreaks are the honest misses. We optimise for catching the burden, not every event.`,
    "The source is IDSP outbreak-report data (via EpiClim, 2009–2019): outbreaks appear only once already elevated, so this is seasonal risk, not live case-curve nowcasting.",
    "Grain is monthly and per-district; malaria is too sparse in these states to forecast (kept as data-only).",
    "The window is a fixed monsoon-climatology prior, not tuned to the test years — a window fit to the data does worse (shown above).",
  ];
  document.getElementById("caveats").innerHTML = caveats.map(c => `<li>${esc(c)}</li>`).join("");
}

function caseChartSVG(cs) {
  const W = 680, H = 210, padL = 30, padB = 24, padT = 14, padR = 8;
  const gw = (W - padL - padR) / 12;
  const max = Math.max(...cs.series_2017, ...cs.climatology, 1);
  const y = val => padT + (H - padT - padB) * (1 - val / max);
  const mlab = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];
  let s = `<svg viewBox="0 0 ${W} ${H}" class="cc-svg" preserveAspectRatio="xMidYMid meet" role="img" aria-label="${cs.year} monthly dengue cases; predicted high-risk window shaded">`;
  cs.model_peak_months.forEach(m => {
    s += `<rect class="cc-band" x="${(padL + (m - 1) * gw).toFixed(1)}" y="${padT}" width="${gw.toFixed(1)}" height="${H - padT - padB}"/>`;
  });
  const clim = cs.climatology.map((val, i) => `${(padL + i * gw + gw / 2).toFixed(1)},${y(val).toFixed(1)}`).join(" ");
  s += `<polyline class="cc-clim" points="${clim}"/>`;
  cs.series_2017.forEach((val, i) => {
    if (val <= 0) return;
    const x = padL + i * gw + gw * 0.2, bw = gw * 0.6, yy = y(val);
    s += `<rect class="cc-bar" x="${x.toFixed(1)}" y="${yy.toFixed(1)}" width="${bw.toFixed(1)}" height="${(H - padB - yy).toFixed(1)}" rx="1.5"/>`;
    s += `<text class="cc-val" x="${(x + bw / 2).toFixed(1)}" y="${(yy - 3).toFixed(1)}" text-anchor="middle">${val.toLocaleString()}</text>`;
  });
  mlab.forEach((m, i) => {
    s += `<text class="cc-axis" x="${(padL + i * gw + gw / 2).toFixed(1)}" y="${H - 8}" text-anchor="middle">${m}</text>`;
  });
  return s + `</svg>`;
}

function caseLegend() {
  return `<div class="cc-legend"><span class="l-band">Predicted High-risk window (Jul–Sep)</span>` +
    `<span class="l-bar">${DATA.caseStudy.year} cases</span>` +
    `<span style="border-bottom:1px dashed var(--muted)">Typical seasonal shape</span></div>`;
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
  closeBriefing();
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
    });
    m.on("click", () => openBriefing(id));
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
      if (m) window._map.setView(m.getLatLng(), 7, { animate: true });
      openBriefing(id);
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

// ---- Response agent (explain + flag + plan), grounded in the forecast data ----
const SHORT = { "Acute Diarrhoeal Disease": "diarrhoeal disease" };
const shortDisease = d => SHORT[d] || d.toLowerCase();

function railParts(show) {
  ["rail-head", "rail-list", "rail-note"].forEach((cls, i) => {
    const el = document.querySelector(i === 0 ? ".rail-head" : i === 1 ? "#railList" : "#railNote");
    if (el) el.hidden = !show;
  });
}
function closeBriefing() {
  const b = document.getElementById("briefing");
  if (b) b.hidden = true;
  railParts(true);
}

// Deterministic, grounded response plan (the LLM layer will reason a richer version at deploy).
const ACTION_LIB = {
  "Dengue": [
    "Vector control: fogging + source reduction in affected wards",
    "Stock rapid diagnostic tests (NS1/IgM) and IV fluids at PHCs/CHCs",
    "Activate fever surveillance; alert PHCs and urban local bodies",
    "Community messaging: remove standing water, use bed nets",
  ],
  "Acute Diarrhoeal Disease": [
    "Test water quality; ensure chlorination of affected supplies",
    "Pre-position ORS and IV fluids at PHCs",
    "Brief PHCs on case management and reporting",
    "Sanitation & hand-hygiene messaging in affected areas",
  ],
};

function buildResponsePlan(cur, disease) {
  const tier = cur.tier, trend = cur.trend || "flat";
  let posture, postureClass;
  if (tier === "High") { posture = trend === "falling" ? "Sustain & de-escalate" : "Mobilise"; postureClass = "Mobilise"; }
  else if (tier === "Watch") { posture = trend === "rising" ? "Prepare" : "Monitor closely"; postureClass = "Prepare"; }
  else { posture = "Routine surveillance"; postureClass = "Routine"; }

  const lib = ACTION_LIB[disease] || ["Alert district health staff", "Pre-position supplies", "Monitor reporting"];
  const n = postureClass === "Mobilise" ? lib.length : postureClass === "Prepare" ? 3 : 1;
  const actions = lib.slice(0, n);

  const s = Math.round(cur.score || 0);
  const resources = (tier === "Low" || s < 5)
    ? "Routine stock levels; no surge pre-positioning indicated."
    : `Indicative: pre-position rapid tests and fluids for ~${s}–${Math.round(s * 1.5)} presentations this month (scaled to expected burden — refine with local stock).`;

  const timeline = tier === "Low"
    ? { week: "Continue routine reporting.", month: "Watch for the seasonal ramp (see calendar).", watch: "Any case cluster → open a line-list." }
    : {
        week: postureClass === "Mobilise" ? actions[0] : "Confirm supply readiness and PHC contacts.",
        month: postureClass === "Mobilise" ? "Sustain vector control / case management; daily line-listing." : "Complete pre-positioning before peak; brief field staff.",
        watch: `Escalate to Mobilise / request state support if cases exceed ~${Math.round((s || 10) * 1.5)} or spread to adjacent blocks.`,
      };
  return { posture, postureClass, actions, resources, timeline };
}

function openBriefing(id) {
  const d = districtById[id];
  const disease = state.disease, month = state.month;
  const monthFc = (DATA.forecasts[disease] || {})[String(month)] || {};
  const cur = monthFc[id];
  if (!d || !cur) return;

  const flagged = Object.entries(monthFc)
    .filter(([, f]) => f.tier === "High" || f.tier === "Watch")
    .sort((a, b) => b[1].score - a[1].score);
  const rank = flagged.findIndex(([k]) => k === id) + 1;

  const cal = [];
  for (let m = 1; m <= 12; m++) {
    const f = ((DATA.forecasts[disease] || {})[String(m)] || {})[id];
    cal.push({ m, tier: f ? f.tier : "Low" });
  }
  const highMonths = cal.filter(c => c.tier === "High").map(c => MONTHS[c.m]);
  const watchMonths = cal.filter(c => c.tier === "Watch").map(c => MONTHS[c.m]);

  const dn = shortDisease(disease), mn = MONTHS[month];
  let text;
  if (cur.tier === "Low") {
    text = `In ${mn}, ${d.name} is at low ${dn} risk — off-season here. Historical ${mn} caseload is minimal.`;
  } else {
    const sev = cur.tier === "High" ? "HIGH" : "elevated (Watch)";
    text = `In ${mn}, ${d.name} is at ${sev} ${dn} risk — the seasonal peak window. ` +
      `The district historically records ~${Math.round(cur.score)} cases in ${mn} (${cur.conf} confidence). ` +
      (rank ? `It ranks #${rank} of ${flagged.length} flagged districts across the pilot this month.` : "");
  }
  const answers = {
    peak: highMonths.length
      ? `High ${dn} risk in ${highMonths.join(", ")}${watchMonths.length ? `; watch in ${watchMonths.join(", ")}` : ""}.`
      : `No High-risk months on record for ${dn} here.`,
    compare: cur.tier === "Low"
      ? `${d.name} isn't among this month's flagged districts.`
      : `#${rank} of ${flagged.length} flagged districts this month by expected ${dn} burden (~${Math.round(cur.score)} cases).`,
    why: cur.drivers || `${mn} seasonal pattern for ${dn} in ${d.name}.`,
  };

  const calHtml = cal.map(c =>
    `<div class="bf-cal-cell ${c.m === month ? "now" : ""}"><div class="bf-cal-bar ${c.tier}"></div>${MONTHS[c.m][0]}</div>`).join("");
  const plan = buildResponsePlan(cur, disease);
  const planHtml =
    `<div class="bf-plan">` +
    `<div class="bf-plan-head">Response plan <span class="bf-posture ${plan.postureClass}">${esc(plan.posture)}</span></div>` +
    `<ol class="bf-actions">${plan.actions.map(a => `<li>${esc(a)}</li>`).join("")}</ol>` +
    `<div class="bf-res"><strong>Resources:</strong> ${esc(plan.resources)}</div>` +
    `<div class="bf-timeline">` +
      `<div><span class="bf-tl-k">This week</span>${esc(plan.timeline.week)}</div>` +
      `<div><span class="bf-tl-k">This month</span>${esc(plan.timeline.month)}</div>` +
      `<div><span class="bf-tl-k">Watch-for</span>${esc(plan.timeline.watch)}</div>` +
    `</div></div>`;

  const context = {
    district: d.name, state: d.state, disease, month: mn,
    tier: cur.tier, trend: cur.trend, confidence: cur.conf,
    expected_cases_this_month: Math.round(cur.score),
    rank: cur.tier === "Low" ? "not flagged this month" : `${rank} of ${flagged.length} flagged`,
    seasonal_high_months: highMonths,
    deterministic_plan: { posture: plan.posture, actions: plan.actions, resources: plan.resources },
  };

  const b = document.getElementById("briefing");
  b.innerHTML =
    `<button class="bf-back" id="bfBack">← All districts</button>` +
    `<p class="bf-name">${esc(d.name)}</p><p class="bf-state">${esc(d.state)} · ${esc(disease)} · ${esc(mn)}</p>` +
    `<span class="bf-tier ${cur.tier}">${esc(cur.tier)}</span>` +
    (cur.trend ? `<span class="bf-trend ${cur.trend}">${TREND[cur.trend] || ""}</span>` : "") +
    `<span class="bf-conf">${esc(cur.conf)} confidence</span>` +
    `<p class="bf-text">${esc(text)}</p>` +
    planHtml +
    `<p class="bf-cal-label">Seasonal risk calendar (${esc(disease)})</p><div class="bf-cal">${calHtml}</div>` +
    `<div class="bf-asks"><p class="bf-asks-label">Ask about this district</p>` +
    `<button class="bf-ask" data-a="peak">When does risk peak here?</button>` +
    `<button class="bf-ask" data-a="compare">How does it compare?</button>` +
    `<button class="bf-ask" data-a="why">Why this risk level?</button>` +
    (AGENT_ENDPOINT ? `<div class="bf-ask-row"><input class="bf-input" id="bfInput" placeholder="Ask the agent anything…" maxlength="500" /><button class="bf-send" id="bfSend">Ask</button></div>` : "") +
    `<div class="bf-answer" id="bfAnswer" hidden></div></div>` +
    `<p class="bf-llm-note">${AGENT_ENDPOINT ? "Live agent, grounded strictly in the facts above (deterministic plan is the fallback)." : "Deterministic plan, grounded in the forecast data. The live agent adds free-form Q&A once deployed."}</p>`;
  b.hidden = false;
  railParts(false);

  document.getElementById("bfBack").onclick = closeBriefing;
  const ans = document.getElementById("bfAnswer");
  b.querySelectorAll(".bf-ask").forEach(btn => {
    btn.onclick = () => { ans.textContent = answers[btn.dataset.a]; ans.hidden = false; };
  });

  const sendBtn = document.getElementById("bfSend"), input = document.getElementById("bfInput");
  if (sendBtn && input) {
    const go = async () => {
      const q = input.value.trim();
      if (!q) return;
      ans.hidden = false; ans.textContent = "Thinking…"; sendBtn.disabled = true;
      const text = await askAgent(context, q);
      ans.textContent = text || "The live agent is unavailable right now — see the response plan above.";
      sendBtn.disabled = false;
    };
    sendBtn.onclick = go;
    input.addEventListener("keydown", e => { if (e.key === "Enter") go(); });
  }
}

boot().catch(err => {
  const pre = document.createElement("pre");
  pre.style.cssText = "color:#dc2626;padding:1rem";
  pre.textContent = "Failed to load: " + err;
  document.body.prepend(pre);
  console.error(err);
});
