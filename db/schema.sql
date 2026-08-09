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

CREATE INDEX IF NOT EXISTS idx_obs_disease_ym ON observations(disease, year, month);
CREATE INDEX IF NOT EXISTS idx_obs_district   ON observations(district_id);
