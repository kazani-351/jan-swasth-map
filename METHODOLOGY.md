# Methodology — Jan Swasth Map

*An open, transparent outbreak early-warning method for Indian district health officers — and an honest account of what it does and doesn't do.*

## The claim, up front

> A deliberately simple, transparent model — dengue risk concentrates in the July–September monsoon window — **captures 85.7% of India's dengue case-burden in held-out years (2016–2019)** using just three predicted months, **3.4× better than chance (25%)**, and it **beats data-driven alternatives that overfit**. Illustrated on the real 2017 North 24 Parganas dengue epidemic, where 100% of the outbreak's 6,480 cases fell inside the predicted window.

Every number here is recomputed from the repo by `pipeline/forecast.py` and written to a `validation` table — nothing is hand-entered.

## Why this is the honest claim (and what we rejected)

We started intending a different, flashier claim: *"our model flags the rising limb of an outbreak weeks before the peak."* **We tested it and it failed** — and that failure is the most important thing we learned.

India's IDSP outbreak data (via the EpiClim dataset) is **outbreak-*report* data**: a district only appears once an outbreak is *already elevated*. There is no quiet pre-rise baseline in the case series, so "detect the rise early" has nothing to detect early. We verified this on the 2017 North 24 Parganas series (the first record is already 387 cases) and rejected the approach rather than fake it. See `spike/backtest.py` — the honest failure is preserved in the repo.

What the data *does* have is strong, stable **seasonality**: 73% of pilot-state dengue cases fall in Jul–Sep, every year. So the honest, defensible claim is a **spatial-temporal skill** claim: does a transparent seasonal model put risk on the right districts in the right months, on years it never saw?

## The model

A **fixed monsoon-climatology prior**, refined per district:

- **Seasonal window** (the prior): dengue peak = Jul–Aug–Sep, shoulder = Jun/Oct. This is domain climatology (India's monsoon), **not fit to the data**. That distinction is load-bearing — see below.
- **District refinement:** a district is `High` in its peak months only if it carries above-median historical burden for that disease; otherwise `Watch`. Districts with no history for a disease get no forecast.
- **Confidence:** qualitative (`high`/`medium`/`low`), driven by how many years of history the district has. We deliberately do **not** publish a numeric probability or confidence interval — on this sparse report data that would be *fake precision*, which the product's own anti-criteria forbid.
- **Trend:** each district-month is marked `rising` / `flat` / `falling` from the seasonal direction (this month's climatological mean vs the previous month's).
- **Diseases:** dengue leads (best signal, climate-linked). Acute Diarrhoeal Disease is secondary. Malaria is too sparse in the pilot states (Tamil Nadu = 6 reports) to forecast — it is flagged, not modelled.

## Validation (the part that matters)

Train on ≤2015, test on 2016–2019. Metric: **case-weighted capture** — what share of the actual dengue *burden* in held-out years fell inside the model's predicted months. (We report the unweighted month-hit rate too, and it's lower on purpose — see limits.)

| Model | Held-out case-weighted capture | vs chance (25%) |
|---|---|---|
| **Fixed monsoon prior (our model)** | **85.7%** | 3.4× |
| Window fit to the training data | 58.1% | worse |
| Per-district data fit | 47.7% | worse |

The headline finding beyond the number itself: **the transparent domain prior beats both data-driven fits.** A window fit to the training years drifts to Aug–Oct and generalises worse (seasonal drift); a per-district fit overfits sparse districts. Domain knowledge won. The pipeline asserts capture ≥ 70% and fails loudly if a future change regresses it.

**Case study (held out):** 2017 North 24 Parganas dengue. The model — window fixed from pre-2016 climatology — marked Jul–Sep as high-risk. In the held-out 2017 season, the outbreak hit Aug (4,258) and Sep (2,222): **100% of its 6,480 cases inside the predicted window.**

## Honest limits

- **Case-weighted 85.7% but unweighted 46%.** The big outbreaks reliably land in monsoon; small, scattered off-season outbreaks are the misses. We optimise for catching the *burden*, and we say so.
- **This is seasonal risk, not live nowcasting.** The source is report data that thins after 2019; the demo proves the *method* on the historical record. A path to live IDSP/IHIP feeds is future work (the `refresh` script is wired to re-pull and rebuild, but the current source stops at 2019/2023).
- **Monthly, per-district grain.** Not weekly, not sub-district.
- **No facility/drug-supply gap layer.** We intended a coverage-vs-risk gap ("high risk meeting thin infrastructure"), but district facility counts exist only inside Rural Health Statistics PDFs; a state-to-district estimate would be circular. Cut honestly rather than faked. The agent still *flags* the highest-risk districts from the forecast.

## Architecture

- **Data pipeline** (Python, stdlib only): `refresh.py` (re-pull EpiClim from Zenodo, md5-verify, atomic replace) → `ingest.py` (normalise to a SQLite/D1 store) → `forecast.py` (seasonal model + held-out validation) → `export.py` (static JSON). Every stage is fail-loud and self-verifying.
- **Frontend** (Cloudflare Pages, vanilla JS + Leaflet): risk map + "Act now" rail, a "How we know it works" validation view, and a grounded district-briefing agent (explain + flag). Read paths are static JSON — no server needed for the dashboard.
- **Agent:** grounded in the forecast data (it only states numbers present in the store). A live LLM adds free-form Q&A at deploy, behind a provider-agnostic interface (Cloudflare Workers AI default).

## Reproduce it

```bash
python3 pipeline/refresh.py   # pull + verify + rebuild everything, or run ingest/forecast/export individually
# then serve web/ statically and open index.html
```

## Data & credits

- **EpiClim** — weekly district-wise all-India epidemics + climate dataset, Zenodo record 14580510, CC-BY-4.0. Sourced from India's Integrated Disease Surveillance Programme (IDSP).
- Built for Code for India's *Code for a Billion* hackathon (Track 03). Open-source.
