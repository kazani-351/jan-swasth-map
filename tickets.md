# Work order — Jan Swasth Map

Tracer-bullet slices. Work top-to-bottom. Each ticket names its blocking edges. Do NOT start a ticket whose blockers are open.

## GATE

- [x] **T1 — Data & backtest feasibility spike** (blocks: everything) — DONE 2026-08-10, PASS. EpiClim (Zenodo 14580510) downloaded + verified. Case-curve early-warning REJECTED (no pre-rise baseline). Wedge reframed to transparent seasonal model: **86% held-out case-weighted capture** (vs 25% chance), beats per-district fit. Disease set + case study resolved. See `spike/FINDINGS.md`.

## BUILD (unlocked only after T1 passes)

- [ ] **T2 — Ingestion → normalized store** (blocks: T3,T4,T5) — scripts pull IDSP/EpiClim/HMIS for 3 states → normalized district-week tables → `seed.sql`. Snapshot baked in; refresh script wired + fail-loud.
- [x] **T3 — Seasonal forecast + held-out validation productionized** (needs: T2) — DONE 2026-08-10. `pipeline/forecast.py`: fixed monsoon prior + district burden/confidence → 2556 `forecasts` rows; `validation` table holds held-out case-weighted 85.7% / unweighted 46.4% + disclosed data-fit alternatives (58%/48%) + chance 25%. Self-verifies; asserts capture ≥70%.
- [~] **T4 — Coverage-vs-risk gap engine** — CUT 2026-08-10 (documented). Sub-spike found district facility counts live only in RHS PDFs (rabbit hole); state-level distribution would be circular. Population (Census 2011) is clean but redundant with case-burden. Cut per the pre-agreed graceful-degradation path. Facility-per-capita = documented future work (RHS PDF parse). The agent still *flags* highest-risk districts from the forecast.
- [x] **T5 — Static JSON export** (needs: T2,T3) — DONE 2026-08-10. Deviation D1: read paths ship as static JSON from Pages (not Worker+D1). `pipeline/export.py` → web/data/{districts,forecasts,validation,meta}.json. Worker reserved for the agent only.
- [x] **T6 — Dashboard: risk map + alert rail** (needs: T5) — DONE 2026-08-10. Leaflet + CartoDB tiles, circle markers (deviation D2, no boundary GeoJSON needed) colored by tier + sized by burden; "Act now" rail w/ plain-language drivers; disease toggle + month slider; hero stat. Verified desktop + mobile, console clean, toggle re-renders.
- [x] **T7+T8 — District briefing panel + explain/flag agent** — CORE DONE 2026-08-10. Click district (marker or rail) → grounded DHO briefing (tier + confidence, season context, historical burden, rank among flagged, recommended action by disease) + 12-month risk calendar + 3 preset data-answered questions (peak/compare/why). Back + auto-close on month/disease change. Verified desktop + mobile, console clean. LLM prose/NL enrichment (Workers AI default / MeshAPI, provider-abstracted) deferred to deploy (T12, wrangler gate). Mobile map-scroll-capture = T11 polish.
- [x] **T9 — Validation / case-study view** (needs: T3,T6) — DONE 2026-08-10. "How we know it works" view: model-comparison bars (monsoon 85.7% vs data-fit 58% vs per-district 48% vs chance 25%) + 2017 N24Parganas held-out case study (100% of 6,480 cases in predicted Jul-Sep window) + honest caveats. Hand-rolled SVG, no chart lib. Verified desktop+mobile; caught+fixed inline-span bar-fill bug.
- [ ] **T10 — NL query** (needs: T8) — ask-and-answer over D1. Cut-buffer #2.
- [ ] **T11 — Design polish** (needs: T6,T7) — modern gov-tech clean; unslop-ui/taste pass; responsive (desktop + 375px + short height).

## SHIP

- [ ] **T12 — Deploy** (needs: build core) — Cloudflare Pages + Worker + D1; poll healthy + smoke one real path.
- [~] **T13 — Narrative writeup** (needs: T3,T9) — FIRST-CLASS. METHODOLOGY.md DONE 2026-08-10 (judge-facing: claim, rejected approaches, model, held-out validation table, honest limits, reproduce steps). BlogChain public piece PENDING — offer outline-architect first (standing preference).
- [ ] **T14 — Demo video + README** (needs: T12) — 2-3 min DHO walkthrough; README = what/run/test.

## EXPANSION — agentic-response system (post-review scope, 2026-08-10)
Leading-signal big bet VALIDATED NO-GO (`spike/FINDINGS.md`: climate doesn't lead outbreaks in this data). Ambition redirected to a genuinely agentic *response* system (engineering-risk, theme-fit) rather than a predictive moonshot.
- [x] **T15 — District Response Agent, deterministic layer** — DONE 2026-08-10. Briefing → full response plan: posture (Mobilise/Prepare/Monitor closely/Routine, from tier+trend) + prioritized actions by disease + burden-scaled resources (honest bands, no fake precision) + timeline (week/month/watch-for) + escalation trigger. Verified desktop; posture branches confirmed across tiers/trends.
- [ ] **T16 — Live LLM agent layer** — CF Worker + Workers AI: multi-step tool-use (forecast/peer-compare/historical-analogue), LLM-reasoned plan + free-form Q&A. Needs wrangler install gate; deploy + curl test (no local workerd on Monterey). The deterministic plan is the graceful fallback.
- [ ] **T17 — xSpan CareHub integration** (bonus award) — investigate a usable population/data endpoint; wire only if it genuinely fits.

## Cut-order under time pressure
1. Drug-supply gap (already deferred)  2. T10 NL query  — never cut: T1, T3 backtest, T13 narrative.
