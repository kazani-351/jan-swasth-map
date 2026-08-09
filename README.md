# Jan Swasth Map

Open population-health early-warning dashboard for Indian District Health Officers. Forecasts outbreak risk (dengue, malaria, acute-diarrheal) per district for ~4 weeks, explains why, and flags where rising risk meets thin health infrastructure. Pilot states: Maharashtra, Tamil Nadu, West Bengal.

Built for the Code for India "Code for a Billion" hackathon (Track 03). Open data only — no personal/health records. Open-source (Apache-2.0/MIT).

> Status: scaffolding. See [SPEC.md](SPEC.md) for the full plan and [tickets.md](tickets.md) for the build order.

## Stack
Cloudflare Pages (Leaflet frontend) + Worker API + D1 (SQLite). Forecasts/gaps/backtest precomputed by an offline Python/Node pipeline into `seed.sql`.

## Run
_TBD once T2–T6 land. Will be: install, build seed, `wrangler dev`._

## Test
_TBD. Acceptance criteria + falsifiers are in [SPEC.md](SPEC.md) §15–16._

## Data sources
IDSP weekly outbreak reports · EpiClim (district climate + epidemics) · HMIS (facility/capacity). All open. Full provenance in the methodology writeup.
