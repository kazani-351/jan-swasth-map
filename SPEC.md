# SPEC — Jan Swasth Map

**Project:** Jan Swasth Map (working name) — open population-health early-warning dashboard for India
**Hackathon:** Code for India — "Code for a Billion" (Bharat Agentic-AI Hackathon 2026), Track 03 (tracks later became open impact areas; this is the Health area)
**Deadline:** Deployed to cloud + open-sourced by **15 Nov 2026**. Winners 5 Dec 2026.
**Builder:** kazani (solo). Attribution retained; code open-sourced (Apache-2.0/MIT) to CFI GitHub org.
**Date locked:** 2026-08-09.

---

## 1. One-liner

An open early-warning + resource-gap map for **District Health Officers**: it forecasts outbreak risk (dengue, malaria, acute-diarrheal) per district for the next ~4 weeks, explains *why* in plain language, and flags districts where **rising risk meets thin health infrastructure** — so a DHO knows where to pre-position resources before an outbreak lands.

## 2. Goal & success criteria

**"Done" =** a live, deployed, open-sourced multi-subsystem app that, for 3 pilot states, ingests real open data, produces defensible weekly district forecasts, flags coverage-vs-risk gaps, renders a DHO-facing map + alert rail, and lets the agent explain any district and answer plain-language questions — plus a 2-3 min demo video and a methodology README.

**"Good" (winning-grade) =** reads as *real public-health infrastructure*, not a hackathon toy. Depth over polish-on-one-page (the explicit Samjha Do lesson). Judges can interrogate the method and it holds up.

**Judging axes we build toward:** impact (DHO acts earlier), openness (100% OSS, open data, documented method), technical quality (honest, reproducible forecast + backtest).

## 2b. Positioning & wedge (grill outcome, 2026-08-10)

**Lead with held-out seasonal skill, not the dashboard.** The claim we build everything to prove (CONFIRMED empirically in the T1 spike, 2026-08-10): *"A transparent seasonal model captures **~86% of India's dengue case burden** in held-out years (2016-19) with just 3 predicted months — 3.4x better than chance — and beats an overfit per-district data-fit. Illustrated on the real 2017 North 24 Parganas dengue epidemic."* Verifiable, honest, memorable, and it doubles as the methodology story (domain-knowledge model beat the black-box fit). The dashboard is the vehicle that showcases it, not the headline.

> Why not the original "flag the case-curve peak early" claim: IDSP data is outbreak-REPORT data that only appears once elevated — no pre-rise baseline exists, so case-curve early-warning is not supported. Verified and rejected in the T1 spike. See `spike/FINDINGS.md`.

**The narrative is a first-class deliverable, not optional.** A methodology + story writeup (BlogChain / public) ships alongside the app. It is the conversion lever (the real bottleneck per strategy), the judge-memorability vehicle, and where the "Best xSpan/AgentFoundry integration" recognition angle is argued. Success = a defensible, backtest-proven, well-narrated slice that wins *visibility*, not just a shipped repo.

**User grounding without a real DHO:** we cannot access a District Health Officer. Mitigation = anchor every design decision in **published IDSP/IHIP surveillance workflow + DHO-role documents, cited in the methodology.** Cheap credibility, defensible under judging, closes the "never talked to the user" criticism at low cost.

**Scope stance:** full V1 (all 6 subsystems + NL query + backtest) is the target. **Cut-order under time pressure (graceful degradation, not silent drop):** (1) drug-supply gap, (2) NL query. Core that must ship regardless: ingestion + forecast + **backtest** + coverage-gap + dashboard + narrative.

## 3. Scope

### IN (V1)
1. **Ingestion** — normalize IDSP/EpiClim/HMIS into one district-week store for MH + TN + WB.
2. **Forecast** — transparent seasonal risk per district-disease, monthly grain, 3 tiers + trend + qualitative confidence (no numeric CI — see D5).
3. **Gap detection** — coverage-vs-risk mismatch flag (facility density/capacity vs forecast risk).
4. **Dashboard** — choropleth risk map + "act now" alert rail; district detail panel.
5. **Agent** — plain-language district briefing (explain + flag) AND a thin natural-language query over the data.
6. **Backtest/replay** — show the baseline flagged a real past outbreak weeks early.
7. **Deliverables** — live URL, demo video, methodology README, **and a first-class narrative writeup (BlogChain/public) leading with the backtest claim**.

### OUT (V1) — forced cuts
- **User accounts / auth** — public read-only. (Anti-criterion below.)
- **Real personal health data / PII / ABHA-ABDM records** — open aggregated/anonymized data only. (Anti-criterion.)
- **Native mobile app** — responsive web only.
- **Multi-language UI** — English-only UI (data may carry local place names). Vernacular = later.
- **Drug-supply-stock gap** — designated **first-to-cut buffer** if time runs short (HMIS stock granularity is the riskiest data). Facility-coverage gap stays IN.

## 4. Users & context

- **Primary (hero):** District Health Officer / district surveillance unit — decides where limited resources (kits, staff, vector control) go next month. Uses it on a desktop/laptop in an office; glanceable, decision-first.
- **Secondary:** state surveillance cell, press, NGOs, researchers (benefit from the same public view; not designed-for in V1).

## 5. Architecture (subsystems + data flow)

```
[Offline pipeline (Python/Node scripts)]
  IDSP/EpiClim/HMIS raw  ->  normalize  ->  forecast (baseline model)  ->  gap calc  ->  backtest
        |                                                                                   |
        v                                                                                   v
                      seed.sql  ------------------->  [Cloudflare D1]  <---- read ---- [Cloudflare Worker API]
                                                                                              |
   [Cloudflare Pages static frontend]  <--- JSON --->  /api/*  (districts, forecasts, gaps, agent) 
        (Leaflet choropleth + alert rail + detail panel + NL query box)                       |
                                                                             [Agent provider: Workers AI default | MeshAPI opt]
```

- **Forecasts + gaps + backtest are computed offline** in the pipeline and stored in D1. The Worker serves precomputed rows (deterministic demo, no live-source dependency at request time).
- **Snapshot + wired refresh:** curated recent data baked into `seed.sql`; a documented `refresh` script rebuilds it. Refresh is provably wired, not load-bearing for the demo.

### Data model (D1 / SQLite)
- `districts(district_id, name, state, population, lat, lon)`
- `observations(district_id, disease, week, cases, deaths, source)`
- `climate(district_id, week, rainfall_mm, temp_avg, humidity)`
- `forecasts(district_id, disease, month, risk_tier, risk_score, trend, confidence, drivers)`  — actual shipped schema (D5: qualitative confidence, no numeric prob/CI)
- `facilities(district_id, phc_count, chc_count, beds, capacity_index, per_capita_index)`
- `gaps(district_id, disease, target_week, gap_flag, gap_reason, coverage_index, risk_tier)`
- `backtest(district_id, disease, window, predicted_tier, actual_cases, lead_weeks)`

## 6. Data sources (with accessibility status)

| Source | Use | Status |
|---|---|---|
| IDSP weekly outbreak reports (idsp.mohfw.gov.in) | case/death observations | Real; official but PDF-based. Lean on cleaned mirror below. |
| dataful.in #18514 (cleaned IDSP outbreaks) | structured observations | Verified exists; primary observation source. |
| EpiClim (arxiv 2501.18602) | weekly district climate + epidemics (dengue/malaria/ADD) | Verified paper exists; **must confirm data files are downloadable** (fog). Forecast-feature unlock. |
| HMIS (hmis.mohfw.gov.in) | facility counts + capacity | Real; **district bulk-export granularity to confirm** (fog). |
| District boundary GeoJSON (MH/TN/WB) | choropleth map | Public sources exist; **confirm an open-licensed set** (fog). |

## 7. Forecast method (transparent seasonal model — decided by T1 evidence)

**Per district-disease, monthly grain, seasonal risk.** (Grain is monthly, not weekly: EpiClim is outbreak-report data with no dense weekly panel — see §14/gotchas.)
- **Core model = seasonal monsoon prior** refined by district history. Dengue risk concentrates Jul-Sep (73% of pilot-state cases); the shared monsoon prior generalizes far better on held-out years than a per-district month-fit (86% vs 48% case-weighted capture — the fit overfits sparse districts).
- **Climate features** (precip/temp/LAI from EpiClim) refine and *explain* risk (precip in big-outbreak months ≈2x baseline). Note: EpiClim climate is concurrent with reports, so it is explanatory/refining, not a proven *leading* signal; a lagged-climate leading model is a documented future upgrade.
- Output: risk **tiers** (Low / Watch / High) per district-month; **drivers** in plain language (season + climate + recent history); an honest **confidence** flag (wider/low-confidence for sparse-history districts).
- **Lead disease = dengue** (best signal, climate-linked). ADD secondary (dense but less climate-linked). **Malaria too sparse in pilot states — flagged, not forecast.**
- **Rejected:** case-curve rising-limb detection (no pre-rise baseline — verified fail, T1); per-district data-fit (overfits — 48% vs 86%); trained ML/LLM-reasoned risk (weaker explainability, and the transparent model already wins). All notable as future work behind the same interface.

### 7b. Validation (replaces "backtest lead-weeks")
- **Held-out capture:** train on ≤2015, test 2016-19; report **case-weighted capture** (~86%: does the model concentrate risk where the burden actually landed) AND **unweighted hit rate** (~46%: small scattered off-season outbreaks are the honest misses). Both reported.
- **Illustrative case study:** the 2017 North 24 Parganas dengue epidemic (Jul-Sep) sits squarely in the predicted high-risk window — the narrative anchor.
- Probe: `spike/skill_test2.py` reproduces the numbers; production pipeline recomputes them into a `validation` table.

## 8. Gap metric (defensible)

**Coverage-vs-risk mismatch:** flag districts where forecast `risk_tier = High/Watch` AND `per_capita_index` (facilities/beds per 100k vs pilot-set median) is low. Gap = "high risk meeting thin infrastructure." Ties forecast + facility subsystems together.
- **Rejected:** raw facility density (a low-risk, low-facility district isn't urgent); IPHS-normed shortfall (cleanest normatively, hardest to source per-district — noted as upgrade).

## 9. Agent (swappable)

- **Interface:** `explain(district, disease)` → plain-language DHO briefing; `ask(question)` → NL query answered from D1 (parameterized/guarded retrieval, not free SQL).
- **Provider:** default **Cloudflare Workers AI** (no external key, free tier, in-stack). **MeshAPI** as a config-swap provider if cheap. Interface stays provider-agnostic.
- **Optional sponsor adapter:** if xSpan CareHub exposes a usable population/data endpoint, wire it as one optional adapter for the "Best xSpan CareHub Integration" bonus award — do not contort the product around it.
- **Guardrails:** agent answers only from the stored data; refuses individual medical advice; every briefing is grounded in specific rows (no free-floating claims).

## 10. UI / UX

- **Direction:** modern gov-tech clean — data-dense but credible; restrained palette, clear choropleth, tabular numbers, readable at a glance. (Anti-slop: no purple-gradient default; will run unslop-ui/taste at build.)
- **Hero screen:** choropleth district map of MH/TN/WB colored by risk tier + right-hand **alert rail** of top-N "act now" districts (rising risk + gap flag).
- **District detail panel:** forecast tier + qualitative confidence + trend + drivers + agent briefing. (No numeric CI — D5. Facility coverage — cut, D3.)
- **NL query box:** ask-and-answer over the data (demo feature).
- **Backtest view:** replay a past outbreak, show early flag.
- **Responsive web**, desktop-first (DHO office use); verify mobile + short-height per house rules.

## 11. Tech stack

- **Frontend:** static site on **Cloudflare Pages**; **Leaflet** choropleth (+ TopoJSON to keep boundary size small); vanilla/lightweight JS (no heavy framework — 4GB-friendly). MapLibre noted as alt.
- **API:** **Cloudflare Worker**, endpoints `/api/districts|forecasts|gaps|backtest|agent`.
- **Storage:** **Cloudflare D1** (SQLite) — fits the ~tens-of-thousands-of-rows scale and the NL-query retrieval.
- **Pipeline:** offline Python (forecast/backtest) + Node/scripts (normalize → `seed.sql`); committed, reproducible, documented.
- **Deploy:** Cloudflare (Pages + Worker + D1). Free tier covers it. `{project}.workers.dev` / Pages URL; custom domain optional.

## 12. Key flows, states, edge cases, failure modes

- **Cold load:** map renders from precomputed D1 rows; no live fetch. If agent provider is down, dashboard + forecasts still fully work; agent panel degrades to a static templated briefing.
- **Missing data district:** rendered in a neutral "no data" state, never a fake forecast. Explicitly distinguished from Low risk.
- **Sparse-history district:** forecast falls back to seasonal baseline only; flagged as lower-confidence (wider CI).
- **Backtest miss:** shown honestly (the tool must not only cherry-pick wins).
- **NL query out-of-scope:** agent declines and suggests what it *can* answer; never fabricates numbers.
- **Source outage on refresh:** refresh script fails loud + logs; app keeps serving last snapshot (fail-loud, no silent stale success — house rule).

## 13. Tradeoffs recorded

- Pilot 3 states (depth) over all-India (breadth) — accepted weaker national-coverage optics for a demo that actually works.
- Interpretable baseline over ML — accepted lower headline accuracy for explainability + reproducibility.
- Snapshot over live pipeline — accepted "less real-time" for zero judging-day fragility.
- Workers AI over Claude BYOK — accepted plainer prose for zero external dependency/cost.
- Self-built over CodeNow-centric — accepted forgoing the token perk + one bonus award to protect credentials/RAM and keep the owned workflow.

## 14. Risks & unknowns

- **EpiClim data files may not be cleanly downloadable** → fallback: derive climate from other open sources (IMD-adjacent) or drop to trend+seasonality only (forecast still valid, weaker).
- **HMIS district facility granularity** → fallback: Rural Health Statistics CSV/PDF, or coarser state-normalized per-capita index.
- **District GeoJSON licensing** → confirm an open set before committing map layer.
- **MeshAPI fit/pricing** → default Workers AI de-risks this entirely.
- **Organizer entry rule** (CodeNow-mandatory?) → email drafted; build-in-own-stack is robust to either answer since judging is on the deployed artifact.
- **Solo time vs 6 subsystems** → drug-supply gap is the pre-agreed cut.

## 15. Acceptance criteria (each names its falsifier)

- **A1 — Real data, 3 states.** Falsifier: any pilot district's cases are not traceable to IDSP/dataful/EpiClim, OR MH/TN/WB not all present in `observations`. Probe: query D1, spot-check 5 districts against source.
- **A2 — Forecast produced + tiered.** Falsifier: any active district-disease lacks a `forecasts` row with tier+trend+confidence for each month. Probe: `SELECT` coverage count = active districts × diseases × 12.
- **A3 — Held-out seasonal skill holds (THE HERO CLAIM).** Falsifier: the transparent model's case-weighted capture of dengue burden on held-out years (2016-19) drops to near the 25% chance baseline, OR it does not beat the per-district data-fit. Probe: `spike/skill_test2.py` / production `validation` table (target ~86% vs 25%). Confirmed 2026-08-10. If it ever fails honestly, the positioning changes — we do not fake it.
- **A9 — Narrative exists and is backed.** Falsifier: no methodology writeup shipped, OR the writeup's headline backtest claim is not reproducible from the repo. Probe: open the writeup, run the cited backtest, confirm the numbers match.
- **A4 — Gap flag ties risk+coverage.** Falsifier: a flagged gap district is not both (risk High/Watch) and (per_capita_index below median). Probe: verify each `gaps.gap_flag=1` row against its inputs.
- **A5 — Agent grounded.** Falsifier: agent briefing states a number absent from the district's stored rows, or gives individual medical advice. Probe: 10 scripted prompts, check every claim maps to data.
- **A6 — Deployed + demo-robust.** Falsifier: live URL down, OR dashboard/forecast breaks when the agent provider is disabled. Probe: load prod URL with agent env unset.
- **A7 — Open + reproducible.** Falsifier: repo missing, non-OSS license, OR pipeline can't rebuild `seed.sql` from documented steps on a clean checkout. Probe: fresh clone, run refresh, diff schema.
- **A8 — Responsive.** Falsifier: hero map/rail unusable at 375px width or ~375x400 height. Probe: Claude_Preview at those viewports.

## 16. Anti-criteria (testable must-not-happens)

- **AN1:** No auth. `/login`, `/signup`, or any account creation returns 404 / does not exist in V1.
- **AN2:** No PII. No individual-level or ABHA/ABDM record appears anywhere in the data store, API, or UI. Probe: schema + sample scan for person-level fields.
- **AN3:** No live-source hard dependency. Demo does not break if IDSP/HMIS are offline (serves baked snapshot). Probe: block outbound to those hosts, load app.
- **AN4:** No fabricated precision. UI never shows a single "exact case count next week" as a certainty; risk is always **tiered with qualitative confidence** (never a fake-precise number or numeric CI — D5). Probe: inspect forecast rendering.
- **AN5:** No silent stale-success. A failed refresh logs loudly and does not report success. Probe: force a source 404, run refresh, check exit code + log.

## 17. Not yet specified (fog — stated, not invented)

- Exact EpiClim access path + whether its climate coverage spans all MH/TN/WB districts.
- Exact HMIS facility fields available at district level (bed counts vs facility counts vs both).
- ~~Which past outbreak window~~ RESOLVED: 2017 North 24 Parganas dengue (illustrative case study).
- ~~Final disease set~~ RESOLVED: dengue (lead) + acute-diarrheal (secondary); malaria too sparse in pilot states → flag-only, not forecast.
- District `population` for the per-capita facility index (T4) — not in EpiClim; source separately (Census/HMIS) or fog.
- HMIS facility data granularity at district level (T4) — still to confirm.
- Exact risk-score → tier thresholds and probability calibration (set empirically during build).
- Product name (working name "Jan Swasth Map"; may run product-name at ship).
- Organizer answer on CodeNow-as-entry requirement.
- Custom domain (default: Cloudflare-namespace URL).
