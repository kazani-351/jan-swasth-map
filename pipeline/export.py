#!/usr/bin/env python3
"""T5 — Export the store to static JSON for the Pages frontend. Stdlib. Fail-loud + self-check.

Run:  python3 pipeline/ingest.py && python3 pipeline/forecast.py && python3 pipeline/export.py
"""
import json, os, sqlite3, sys

SCHEMA, SEED, FC = "db/schema.sql", "db/seed.sql", "db/forecast.sql"
OUTDIR = "web/data"


def die(m):
    print(f"FATAL: {m}", file=sys.stderr); sys.exit(1)


def main():
    for p in (SEED, FC):
        if not os.path.exists(p): die(f"{p} missing — run ingest.py then forecast.py")
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    for p in (SCHEMA, SEED, FC):
        con.executescript(open(p).read())
    cur = con.cursor()
    os.makedirs(OUTDIR, exist_ok=True)

    districts = [dict(r) for r in cur.execute(
        "SELECT district_id AS id, name, state, lat, lon FROM districts ORDER BY id")]

    # forecasts nested: disease -> month -> district_id -> {tier,score,conf,drivers}
    fc = {}
    for r in cur.execute("SELECT district_id, disease, month, risk_tier, risk_score, trend, confidence, drivers FROM forecasts"):
        fc.setdefault(r["disease"], {}).setdefault(str(r["month"]), {})[r["district_id"]] = {
            "tier": r["risk_tier"], "score": r["risk_score"], "trend": r["trend"],
            "conf": r["confidence"], "drivers": r["drivers"]}

    validation = {r["metric"]: {"value": r["value"], "note": r["note"]}
                  for r in cur.execute("SELECT metric, value, note FROM validation")}

    # case study: 2017 North 24 Parganas dengue (held out) vs the model's predicted window (train <=2015)
    CASE_ID, CASE_DIS, CASE_YEAR = "wb_north_24_parganas", "Dengue", 2017
    crow = cur.execute("SELECT name, state FROM districts WHERE district_id=?", (CASE_ID,)).fetchone()
    by_ym = {}
    for r in cur.execute("SELECT year, month, SUM(cases) c FROM observations WHERE district_id=? AND disease=? "
                         "GROUP BY year, month", (CASE_ID, CASE_DIS)):
        by_ym[(r["year"], r["month"])] = r["c"]
    years = sorted({y for (y, _) in by_ym})
    series_2017 = [by_ym.get((CASE_YEAR, m), 0) for m in range(1, 13)]
    climatology = [round(sum(by_ym.get((y, m), 0) for y in years) / max(len(years), 1), 1) for m in range(1, 13)]
    case_study = {
        "district": crow["name"] if crow else CASE_ID, "state": crow["state"] if crow else "",
        "disease": CASE_DIS, "year": CASE_YEAR,
        "model_peak_months": [7, 8, 9], "model_shoulder_months": [6, 10],
        "train_note": "Model window fixed from monsoon climatology (trained on ≤2015); 2017 was held out.",
        "series_2017": series_2017, "climatology": climatology,
        "peak_month": max(range(1, 13), key=lambda m: series_2017[m - 1]),
        "total_2017": sum(series_2017),
    }

    meta = {
        "diseases": sorted(fc.keys()),
        "states": sorted({d["state"] for d in districts}),
        "n_districts": len(districts),
        "months": [{"n": i, "abbr": a} for i, a in enumerate(
            ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]) if i],
        "source": "EpiClim (Zenodo 14580510), sourced from India IDSP. CC-BY-4.0.",
    }

    out = {"districts.json": districts, "forecasts.json": fc,
           "validation.json": validation, "case_study.json": case_study, "meta.json": meta}
    for name, obj in out.items():
        with open(os.path.join(OUTDIR, name), "w") as f:
            json.dump(obj, f, separators=(",", ":"))

    # self-check: dengue must exist and have High-tier districts in Aug (month 8)
    if "Dengue" not in fc: die("no Dengue forecasts to export")
    aug_high = sum(1 for v in fc["Dengue"].get("8", {}).values() if v["tier"] == "High")
    if aug_high == 0: die("no High-tier dengue districts in Aug — export looks wrong")
    if not validation.get("dengue_capture_caseweighted_pct"): die("validation metrics missing")

    print("exported:")
    for name, obj in out.items():
        sz = os.path.getsize(os.path.join(OUTDIR, name))
        n = len(obj) if isinstance(obj, (list, dict)) else "?"
        print(f"  {OUTDIR}/{name:18s} {sz/1024:6.1f} KB  ({n} keys)")
    print(f"[check] dengue Aug High-tier districts: {aug_high}")
    print(f"[check] hero metric present: {validation['dengue_capture_caseweighted_pct']['value']}%")
    print("[check] PASS")
    con.close()


if __name__ == "__main__":
    main()
