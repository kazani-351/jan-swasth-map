-- Jan Swasth Map — D1/SQLite schema. Ingestion (T2) fills: districts, observations, climate.
-- forecasts / validation / facilities / gaps land in their own tickets.

CREATE TABLE IF NOT EXISTS districts (
  district_id TEXT PRIMARY KEY,   -- stable slug, e.g. "wb_north_24_parganas"
  name        TEXT NOT NULL,
  state       TEXT NOT NULL,
  lat         REAL,
  lon         REAL,
  population  INTEGER             -- nullable; sourced later (T4 per-capita index)
);

CREATE TABLE IF NOT EXISTS observations (
  district_id TEXT NOT NULL REFERENCES districts(district_id),
  disease     TEXT NOT NULL,      -- Dengue | Malaria | Acute Diarrhoeal Disease
  obs_date    TEXT NOT NULL,      -- ISO yyyy-mm-dd (duplicate same-date reports summed)
  year        INTEGER NOT NULL,
  month       INTEGER NOT NULL,
  cases       INTEGER NOT NULL,
  deaths      INTEGER,            -- nullable (often unreported)
  source      TEXT NOT NULL,      -- provenance
  PRIMARY KEY (district_id, disease, obs_date)
);

CREATE TABLE IF NOT EXISTS climate (
  district_id TEXT NOT NULL REFERENCES districts(district_id),
  obs_date    TEXT NOT NULL,
  year        INTEGER NOT NULL,
  month       INTEGER NOT NULL,
  precip      REAL,               -- mm/day (EpiClim preci)
  temp_k      REAL,               -- Kelvin (EpiClim Temp)
  lai         REAL,               -- Leaf Area Index
  PRIMARY KEY (district_id, obs_date)
);

-- Seasonal risk calendar (T3): one row per district-disease-month (1..12).
CREATE TABLE IF NOT EXISTS forecasts (
  district_id TEXT NOT NULL REFERENCES districts(district_id),
  disease     TEXT NOT NULL,
  month       INTEGER NOT NULL,   -- calendar month 1..12
  risk_tier   TEXT NOT NULL,      -- High | Watch | Low | insufficient_data
  risk_score  REAL,               -- climatological mean cases for that district-disease-month
  confidence  TEXT NOT NULL,      -- high | medium | low
  drivers     TEXT,               -- plain-language explanation
  PRIMARY KEY (district_id, disease, month)
);

-- Held-out validation metrics (T3): the hero-claim numbers, recomputed by the pipeline.
CREATE TABLE IF NOT EXISTS validation (
  metric TEXT PRIMARY KEY,
  value  TEXT NOT NULL,
  note   TEXT
);

CREATE INDEX IF NOT EXISTS idx_obs_disease_ym ON observations(disease, year, month);
CREATE INDEX IF NOT EXISTS idx_obs_district   ON observations(district_id);
CREATE INDEX IF NOT EXISTS idx_fc_disease_mon ON forecasts(disease, month);
