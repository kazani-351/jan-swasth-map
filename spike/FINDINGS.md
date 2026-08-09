# T1 spike findings (2026-08-10) — data & backtest feasibility

**Verdict: PASS. Build proceeds. Wedge reframed and empirically confirmed.**

## Data
- Source: EpiClim, Zenodo record 14580510, `Final_data.csv` (1.0 MB, 8,985 rows, md5 a6c961b9…), CC-BY-4.0.
- One file = cases/deaths + climate (precip/temp/LAI), district-week, 2009-2023, sourced from IDSP.
- **Shape gotcha:** rows are outbreak REPORTS, multiple per date (sub-units), and appear only once elevated — NO pre-rise baseline. Data thins sharply after 2019.

## What failed (and why the gate mattered)
- Naive "flag the case-curve rising limb early" backtest FAILED — no pre-rise baseline exists in report data. Building on that assumption would have been an expensive late discovery.

## What holds (numbers)
- Seasonality is strong: **Jul-Aug-Sep carry 73% of all pilot-state dengue cases** (Aug alone 33%).
- Held-out skill (train ≤2015, test 2016-19), case-weighted capture of dengue burden in 3 predicted months:
  - **Model A — fixed monsoon window (Jul-Sep): 85.7%** (chance 25%, 3.4x). WINNER.
  - Model B — per-district top-3 data-fit: 47.6% (overfits sparse districts).
  - Model C — hybrid: 85.1% (no gain over A; simplicity wins).
- Climate corroboration: mean precip in big-outbreak months ≈2x small months (concurrent/explanatory).

## Confirmed wedge
Transparent seasonal (monsoon) model, refined by district history + climate, validated by held-out case-weighted capture (~86%), illustrated on the real 2017 North 24 Parganas dengue epidemic.

## Implications for build
- Forecast subsystem = seasonal risk (monsoon prior + district refinement + climate), NOT case-curve chasing.
- Lead disease = dengue. ADD secondary (dense but less climate-linked). Malaria too sparse in pilot states — flag, don't forecast.
- Backtest/validation view = held-out capture metric + 2017 N24Parganas case study. Report both case-weighted (86%) and unweighted (46%) — honest.
- Snapshot framing is honest (no live 2026 nowcasting from this source); document the path to live IDSP/IHIP feeds.

## Files
`spike/profile.py`, `spike/backtest.py` (the honest failure), `spike/skill_test.py`, `spike/skill_test2.py` (the winning result). Raw data gitignored under `data/raw/`.
