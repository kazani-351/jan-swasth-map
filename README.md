# Jan Swasth Map

Open outbreak early-warning and response tool for India's district health officers. It forecasts seasonal outbreak risk (dengue, acute diarrhoeal disease) for every district, drafts a prioritised response plan, and lets an officer ask a grounded AI agent about any district.

**Live:** https://jan-swasth-map.kazani.workers.dev

Built for Code for India's *Code for a Billion* hackathon (Track 03). Open data only, no personal or health records. Open-source.

## What it does

- **Risk map** of Maharashtra, Tamil Nadu, and West Bengal, coloured by seasonal outbreak risk per district, with an "Act now" rail of the districts to watch this month.
- **Response agent:** click any district for a posture-driven action plan (Mobilise, Prepare, Monitor closely, Routine) with prioritised interventions, resource pre-positioning, and an escalation trigger. A live LLM agent reasons over the same district facts and answers free-form questions, grounded strictly in the data.
- **"How we know it works":** the honest validation. A transparent model captures **85.7% of dengue case-burden on held-out years (2016-2019)**, beating data-driven models that overfit. Full method and limits in [METHODOLOGY.md](METHODOLOGY.md).

## Run it

The dashboard is static; the data is built by a small Python pipeline (standard library only).

```bash
python3 pipeline/refresh.py   # pull EpiClim, verify, and rebuild the forecast + static JSON
                              # (or run ingest.py, forecast.py, export.py individually)
python3 -m http.server 8000 --directory web   # then open http://localhost:8000
```

The live LLM agent runs in a separate Cloudflare Worker (`worker/agent.js`, provider-agnostic, OpenAI-compatible). Without it the app still works fully on the deterministic response plan.

## Test it

Each pipeline stage self-verifies and fails loudly:

```bash
python3 pipeline/ingest.py     # normalises the data, checks integrity
python3 pipeline/forecast.py   # recomputes the held-out numbers, asserts capture >= 70%
python3 pipeline/export.py     # writes web/data/*.json, checks the exports
```

Acceptance criteria and their falsifiers are in [SPEC.md](SPEC.md).

## Architecture

Cloudflare Workers static assets serve `web/` (vanilla JS, Leaflet). The Python pipeline (`pipeline/`) turns the EpiClim dataset into a SQLite/D1 store, computes the seasonal forecast and validation, and exports static JSON. The response agent is a stateless Cloudflare Worker that calls an OpenAI-compatible LLM, grounded on facts sent by the frontend.

## Data and license

- **EpiClim:** weekly district-wise all-India epidemics and climate dataset, Zenodo record 14580510, CC-BY-4.0, sourced from India's Integrated Disease Surveillance Programme (IDSP).
- Code is open-source under the MIT License (see `LICENSE`).
