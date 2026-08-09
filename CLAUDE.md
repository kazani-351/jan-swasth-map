# CLAUDE.md — Jan Swasth Map

Full spec: @SPEC.md · Work order: @tickets.md

## What this is
Open population-health early-warning dashboard for Indian District Health Officers (pilot: Maharashtra, Tamil Nadu, West Bengal). Forecasts outbreak risk (dengue, malaria, acute-diarrheal), explains it, and flags where rising risk meets thin infrastructure. Hackathon: Code for India "Code for a Billion" Track 03. Deploy + open-source by 15 Nov 2026.

## The wedge (build everything to prove this)
Lead with the **backtest**: "on real IDSP data, a transparent model would have flagged outbreak X in district Y, N weeks before the peak." The dashboard showcases it. If the backtest doesn't honestly hold, we change the positioning — we do NOT fake it.

## Stack
- Frontend: Cloudflare Pages, Leaflet + TopoJSON, lightweight vanilla JS (no heavy framework — 4GB-friendly machine).
- API: Cloudflare Worker (`/api/districts|forecasts|gaps|backtest|agent`).
- Storage: Cloudflare D1 (SQLite). Forecasts/gaps/backtest are precomputed offline and served from D1 (deterministic demo).
- Pipeline: offline Python (forecast/backtest) + Node scripts (normalize → `seed.sql`). Reproducible from a clean checkout.
- Agent: provider-swappable, default Cloudflare Workers AI (no key), MeshAPI optional.

## Hard constraints (non-negotiable)
- **No PII / no ABHA-ABDM / no individual records.** Open aggregated/anonymized data only.
- **No auth.** Public read-only.
- **English-only UI** for V1.
- **Snapshot data + wired refresh.** Demo must not depend on a live source at request time.
- **Fail loud, never silent-stale.** A failed data refresh logs + non-zero exits; it never reports success.
- **Forecast is always tiered + CI.** Never display a single "exact case count next week" as certainty.
- **Agent answers only from stored rows.** No fabricated numbers, no individual medical advice.

## Workflow
- Research → Plan → Execute → Review → Ship. The data/backtest spike (ticket #1) GATES all build work — no dashboard code until the backtest is confirmed achievable on real data.
- Small vertical slices, each verified. Keep `implementation-notes.md` with a Deviations log.
- Verify against SPEC.md acceptance criteria (each has a falsifier). Run the anti-criteria too.
- Review (`/code-review` + `/simplify`) before declaring done. `/security-audit-static` if any input/auth/data-handling surface grows.

## Secrets
Agent keys go in `.dev.vars` (local) or `wrangler secret put` (deployed) — both gitignored. Never commit `.dev.vars`, `.env`, or `.mcp.json`.

## Gotchas
- **EpiClim rows are outbreak REPORTS, not a weekly panel.** Multiple rows share a date (sub-units of a district); the data appears only once an outbreak is already elevated — there is NO pre-rise baseline in the case series. So do NOT model "detect the rising limb of the case curve" (fails — verified in T1 spike). Model **seasonality + climate**, validated spatially on held-out years. Aggregate duplicate dates (sum cases) before any time-series work.
- Data thins sharply after 2019 (2020-22 sparse). Use 2009-2019 for training/backtest; snapshot framing is honest, live 2026 nowcasting is not supported by this source.
- Malaria is too sparse in the pilot states (TN=6, WB=21 reports). Lead with **dengue** (best signal + climate-linked), ADD secondary (dense but less climate-linked), malaria flagged-but-thin.
- **Dengue seasonal window is a FIXED monsoon domain prior {7,8,9}, NOT fit to data.** Fitting it to training years drifts to {8,9,10} and REGRESSES held-out case-weighted capture 86%→58% (seasonal drift); per-district fit → 48%. Do NOT "improve" the model by data-fitting the window. `pipeline/forecast.py` asserts case-weighted capture ≥70% and fails loud if it regresses. The validation table stores the (worse) data-fit alternatives for honest disclosure.
