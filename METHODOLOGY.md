# Methodology: Jan Swasth Map

*An open, transparent outbreak early-warning method for Indian district health officers, with an honest account of what it does and does not do.*

Live: https://jan-swasth-map.kazani.workers.dev

## The claim, up front

> Dengue risk concentrates in the July to September monsoon window. A transparent model built on just that **captures 85.7% of India's dengue case-burden in held-out years (2016-2019)** using three predicted months. That is about 3.4x better than chance (25%), and it beats data-driven models that overfit. We show it on the real 2017 North 24 Parganas dengue epidemic, where 100% of the outbreak's 6,480 cases fell inside the predicted window.

Every number here is recomputed from the repo by `pipeline/forecast.py` and written to a `validation` table. Nothing is hand-entered.

## Why this is the honest claim (and what we rejected)

We set out to make a flashier claim: *"our model flags the rising limb of an outbreak weeks before the peak."* We tested it, and it failed. That failure taught us the most.

India's IDSP outbreak data (via the EpiClim dataset) is outbreak-*report* data. A district only appears once an outbreak is already elevated. There is no quiet pre-rise baseline in the case series, so "detect the rise early" has nothing to detect. We verified this on the 2017 North 24 Parganas series (the first record is already 387 cases) and rejected the approach instead of faking it. The honest failure is preserved in `spike/backtest.py`.

What the data does have is strong, stable seasonality: 73% of pilot-state dengue cases fall in Jul-Sep, every year. So the honest, defensible claim is about spatial-temporal skill. Does a transparent seasonal model put risk on the right districts in the right months, on years it never saw?

## The model

A fixed monsoon-climatology prior, refined per district:

- **Seasonal window** (the prior): dengue peak = Jul, Aug, Sep; shoulder = Jun, Oct. This comes from India's monsoon climatology, not from fitting the data. That distinction carries the result (see validation).
- **District refinement:** a district is `High` in its peak months only if it carries above-median historical burden for that disease, otherwise `Watch`. Districts with no history for a disease get no forecast.
- **Confidence:** qualitative (`high`, `medium`, `low`), driven by how many years of history the district has. We do not publish a numeric probability or confidence interval. On this sparse report data that would be fake precision, which the product's own anti-criteria forbid.
- **Trend:** each district-month is marked `rising`, `flat`, or `falling` from the seasonal direction (this month's climatological mean against the previous month's).
- **Diseases:** dengue leads, since it has the best signal and is climate-linked. Acute Diarrhoeal Disease is secondary. Malaria is too sparse in the pilot states (Tamil Nadu has 6 reports) to forecast, so it is flagged rather than modelled.

## Validation (the part that matters)

Train on 2015 and earlier, test on 2016-2019. The metric is case-weighted capture: what share of the actual dengue *burden* in held-out years fell inside the model's predicted months. We report the unweighted month-hit rate too, and it is lower on purpose (see limits).

| Model | Held-out case-weighted capture | vs chance (25%) |
|---|---|---|
| **Fixed monsoon prior (our model)** | **85.7%** | 3.4x |
| Window fit to the training data | 58.1% | worse |
| Per-district data fit | 47.7% | worse |

The finding under the number: the transparent domain prior beats both data-driven fits. A window fit to the training years drifts to Aug-Oct and generalises worse (seasonal drift), and a per-district fit overfits sparse districts. Domain knowledge won. The pipeline asserts capture at or above 70% and fails loudly if a future change regresses it.

**Case study (held out):** 2017 North 24 Parganas dengue. The model, with its window fixed from pre-2016 climatology, marked Jul-Sep as high-risk. In the held-out 2017 season the outbreak hit Aug (4,258) and Sep (2,222): **100% of its 6,480 cases inside the predicted window.**

## Honest limits

- **Case-weighted 85.7%, but unweighted 46%.** The big outbreaks reliably land in monsoon. The misses are small, scattered off-season outbreaks. We optimise for catching the *burden*, and we say so.
- **This is seasonal risk, not live nowcasting.** The source is report data that thins after 2019, so the demo proves the *method* on the historical record. Live IDSP/IHIP feeds are future work. The `refresh` script is wired to re-pull and rebuild, but the current source stops in 2019/2023.
- **Monthly, per-district grain.** Not weekly, not sub-district.
- **No facility or drug-supply gap layer.** We intended a coverage-vs-risk gap ("high risk meeting thin infrastructure"), but district facility counts live only inside Rural Health Statistics PDFs, and a state-to-district estimate would be circular. We cut it honestly rather than fake it. The agent still flags the highest-risk districts from the forecast.

## Architecture

- **Data pipeline** (Python, stdlib only): `refresh.py` (re-pull EpiClim from Zenodo, md5-verify, atomic replace), then `ingest.py` (normalise to a SQLite/D1 store), then `forecast.py` (seasonal model plus held-out validation), then `export.py` (static JSON). Every stage is fail-loud and self-verifying.
- **Frontend** (Cloudflare Workers static assets, vanilla JS and Leaflet): a risk map with an "Act now" rail, a "How we know it works" validation view, and a district response agent. Read paths are static JSON, so the dashboard needs no server.
- **Response agent:** for any district it drafts a posture-driven response plan (Mobilise, Prepare, Monitor closely, Routine) with prioritised actions, resource pre-positioning, and an escalation trigger. A live LLM (a Cloudflare Worker calling MeshAPI, model `openai/gpt-4o-mini`) reasons over the same district facts and answers free-form questions. It is grounded strictly in the provided facts and cannot invent numbers, and it falls back to the deterministic plan if the LLM is unavailable.

## Reproduce it

```bash
python3 pipeline/refresh.py   # pull, verify, and rebuild everything (or run ingest/forecast/export individually)
# then serve web/ statically and open index.html
```

## Data and credits

- **EpiClim**: weekly district-wise all-India epidemics and climate dataset, Zenodo record 14580510, CC-BY-4.0. Sourced from India's Integrated Disease Surveillance Programme (IDSP).
- Built for Code for India's *Code for a Billion* hackathon (Track 03). Open-source.
