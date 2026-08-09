# Work order — Jan Swasth Map

Tracer-bullet slices. Work top-to-bottom. Each ticket names its blocking edges. Do NOT start a ticket whose blockers are open.

## GATE

- [x] **T1 — Data & backtest feasibility spike** (blocks: everything) — DONE 2026-08-10, PASS. EpiClim (Zenodo 14580510) downloaded + verified. Case-curve early-warning REJECTED (no pre-rise baseline). Wedge reframed to transparent seasonal model: **86% held-out case-weighted capture** (vs 25% chance), beats per-district fit. Disease set + case study resolved. See `spike/FINDINGS.md`.

## BUILD (unlocked only after T1 passes)

- [ ] **T2 — Ingestion → normalized store** (blocks: T3,T4,T5) — scripts pull IDSP/EpiClim/HMIS for 3 states → normalized district-week tables → `seed.sql`. Snapshot baked in; refresh script wired + fail-loud.
- [ ] **T3 — Seasonal forecast + held-out validation productionized** (needs: T2) — transparent seasonal (monsoon prior + district refinement + climate) written to `forecasts` (district-month tier + drivers + confidence); held-out capture (case-weighted ~86% + unweighted) + 2017 N24Parganas case study written to `validation`. Port `spike/skill_test2.py` logic.
- [ ] **T4 — Coverage-vs-risk gap engine** (needs: T2,T3) — per-capita facility index vs forecast risk → `gaps` rows. (Drug-supply gap = cut-buffer #1.)
- [ ] **T5 — Worker API** (needs: T2) — `/api/districts|forecasts|gaps|backtest|agent` reading from D1.
- [ ] **T6 — Dashboard: risk map + alert rail** (needs: T5) — Leaflet choropleth of MH/TN/WB by risk tier + "act now" rail. Hero screen.
- [ ] **T7 — District detail panel** (needs: T6) — tier + prob/CI + trend + drivers + facility coverage + agent briefing.
- [ ] **T8 — Agent: explain + flag** (needs: T5) — swappable provider (Workers AI default), grounded briefings only.
- [ ] **T9 — Backtest / replay view** (needs: T3,T6) — replay the T1 outbreak, show the early flag. Demo hero moment.
- [ ] **T10 — NL query** (needs: T8) — ask-and-answer over D1. Cut-buffer #2.
- [ ] **T11 — Design polish** (needs: T6,T7) — modern gov-tech clean; unslop-ui/taste pass; responsive (desktop + 375px + short height).

## SHIP

- [ ] **T12 — Deploy** (needs: build core) — Cloudflare Pages + Worker + D1; poll healthy + smoke one real path.
- [ ] **T13 — Narrative writeup** (needs: T3,T9) — FIRST-CLASS. Methodology + the backtest story, reproducible from repo. The conversion lever.
- [ ] **T14 — Demo video + README** (needs: T12) — 2-3 min DHO walkthrough; README = what/run/test.

## Cut-order under time pressure
1. Drug-supply gap (already deferred)  2. T10 NL query  — never cut: T1, T3 backtest, T13 narrative.
