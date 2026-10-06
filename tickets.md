# Work order — Jan Swasth Map

Tracer-bullet slices. Work top-to-bottom. Each ticket names its blocking edges. Do NOT start a ticket whose blockers are open.

## GATE

- [x] **T1 — Data & backtest feasibility spike** (blocks: everything) — DONE 2026-08-10, PASS. EpiClim (Zenodo 14580510) downloaded + verified. Case-curve early-warning REJECTED (no pre-rise baseline). Wedge reframed to transparent seasonal model: **86% held-out case-weighted capture** (vs 25% chance), beats per-district fit. Disease set + case study resolved. See `spike/FINDINGS.md`.

## BUILD (unlocked only after T1 passes)

- [ ] **T2 — Ingestion → normalized store** (blocks: T3,T4,T5) — scripts pull IDSP/EpiClim/HMIS for 3 states → normalized district-week tables → `seed.sql`. Snapshot baked in; refresh script wired + fail-loud.
- [x] **T3 — Seasonal forecast + held-out validation productionized** (needs: T2) — DONE 2026-08-10. `pipeline/forecast.py`: fixed monsoon prior + district burden/confidence → 2556 `forecasts` rows; `validation` table holds held-out case-weighted 85.7% / unweighted 46.4% + disclosed data-fit alternatives (58%/48%) + chance 25%. Self-verifies; asserts capture ≥70%.
- [~] **T4 — Coverage-vs-risk gap engine** — CUT 2026-08-10 (documented). Sub-spike found district facility counts live only in RHS PDFs (rabbit hole); state-level distribution would be circular. Population (Census 2011) is clean but redundant with case-burden. Cut per the pre-agreed graceful-degradation path. Facility-per-capita = documented future work (RHS PDF parse). The agent still *flags* highest-risk districts from the forecast.
- [x] **T5 — Static JSON export** (needs: T2,T3) — DONE 2026-08-10. Deviation D1: read paths ship as static JSON from Pages (not Worker+D1). `pipeline/export.py` → web/data/{districts,forecasts,validation,meta}.json. Worker reserved for the agent only.
- [x] **T6 — Dashboard: risk map + alert rail** (needs: T5) — DONE 2026-08-10. Leaflet + OSM tiles (greyed; CARTO switched to API-key-only 2026-10), circle markers (deviation D2, no boundary GeoJSON needed) colored by tier + sized by burden; "Act now" rail w/ plain-language drivers; disease toggle + month slider; hero stat. Verified desktop + mobile, console clean, toggle re-renders.
- [x] **T7+T8 — District briefing panel + explain/flag agent** — CORE DONE 2026-08-10. Click district (marker or rail) → grounded DHO briefing (tier + confidence, season context, historical burden, rank among flagged, recommended action by disease) + 12-month risk calendar + 3 preset data-answered questions (peak/compare/why). Back + auto-close on month/disease change. Verified desktop + mobile, console clean. LLM prose/NL enrichment (Workers AI default / MeshAPI, provider-abstracted) deferred to deploy (T12, wrangler gate). Mobile map-scroll-capture = T11 polish.
- [x] **T9 — Validation / case-study view** (needs: T3,T6) — DONE 2026-08-10. "How we know it works" view: model-comparison bars (monsoon 85.7% vs data-fit 58% vs per-district 48% vs chance 25%) + 2017 N24Parganas held-out case study (100% of 6,480 cases in predicted Jul-Sep window) + honest caveats. Hand-rolled SVG, no chart lib. Verified desktop+mobile; caught+fixed inline-span bar-fill bug.
- [ ] **T10 — NL query** (needs: T8) — ask-and-answer over D1. Cut-buffer #2.
- [ ] **T11 — Design polish** (needs: T6,T7) — modern gov-tech clean; unslop-ui/taste pass; responsive (desktop + 375px + short height).

## SHIP

- [x] **T12 — Deploy** — DONE + VERIFIED LIVE 2026-08-10. Frontend deploy = drag & drop the `web/` folder in the Cloudflare dashboard (no wrangler on Monterey). Frontend on Cloudflare Workers static-assets at **https://jan-swasth-map.kazani.workers.dev** (not Pages/D1 — static-JSON deviation D1). Agent Worker at https://jan-swasth-agent.kazani.workers.dev. Production smoke: live site renders (no console errors) + agent answers from the deployed origin (grounded, correct numbers). TODO: set Worker ALLOWED_ORIGIN to the site URL + Mesh spend cap.
- [~] **T13 — Narrative writeup** (needs: T3,T9) — FIRST-CLASS. METHODOLOGY.md DONE 2026-08-10 (judge-facing: claim, rejected approaches, model, held-out validation table, honest limits, reproduce steps). BlogChain public piece PENDING — offer outline-architect first (standing preference).
- [ ] **T14 — Demo video + README** (needs: T12) — 2-3 min DHO walkthrough; README = what/run/test.

## EXPANSION — agentic-response system (post-review scope, 2026-08-10)
Leading-signal big bet VALIDATED NO-GO (`spike/FINDINGS.md`: climate doesn't lead outbreaks in this data). Ambition redirected to a genuinely agentic *response* system (engineering-risk, theme-fit) rather than a predictive moonshot.
- [x] **T15 — District Response Agent, deterministic layer** — DONE 2026-08-10. Briefing → full response plan: posture (Mobilise/Prepare/Monitor closely/Routine, from tier+trend) + prioritized actions by disease + burden-scaled resources (honest bands, no fake precision) + timeline (week/month/watch-for) + escalation trigger. Verified desktop; posture branches confirmed across tiers/trends.
- [x] **T16 — Live LLM agent layer** — DONE + VERIFIED LIVE 2026-08-10. Worker deployed at https://jan-swasth-agent.kazani.workers.dev (MeshAPI / openai/gpt-4o-mini). curl-verified end-to-end (grounded briefing, numbers correct, no hallucination); browser-verified (ask box → live grounded answer). AGENT_ENDPOINT wired in app.js. TODO before ship: set ALLOWED_ORIGIN to Pages URL + confirm Mesh spend cap.
  (earlier) CODE DONE + FRONTEND VERIFIED 2026-08-10. `worker/agent.js`: stateless, grounded-by-input, OpenAI-compatible (provider = MeshAPI via env; swappable), CORS, 20s timeout, returns `{fallback:true}` on any error. Frontend: free-form "Ask the agent" box (shows only when AGENT_ENDPOINT set) + graceful fallback to the deterministic plan — verified (box appears, Thinking state, failed call degrades cleanly). PENDING: user deploys Worker via CF dashboard (paste `worker/agent.js`, set LLM_BASE_URL/LLM_API_KEY/LLM_MODEL), curl-test with `worker/sample.json`, then set `AGENT_ENDPOINT` in web/app.js. Worker code itself UNVERIFIED until that deploy (no local workerd on Monterey).
- [~] **T17 — xSpan CareHub integration** — NO-GO 2026-08-10 (investigated). xSpan's developer surface (github.com/karlmehta/XSpan-HealthAI-Agent) is an individual-health, local-desktop data aggregator (personal Oura/WHOOP/EHR/genomics → local SQLite biomarker synthesis); "no accounts, no servers, no API keys." No population/district/outbreak API to integrate. Its only overlap (ABDM/ABHA individual records) is the PII we deliberately exclude (AN2). Forgo the bonus award rather than contort the product / break the no-PII principle. Same validate-before-build discipline as the satellite NO-GO.

## Cut-order under time pressure
1. Drug-supply gap (already deferred)  2. T10 NL query  — never cut: T1, T3 backtest, T13 narrative.
