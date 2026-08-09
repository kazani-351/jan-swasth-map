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
    for r in cur.execute("SELECT district_id, disease, month, risk_tier, risk_score, confidence, drivers FROM forecasts"):
        fc.setdefault(r["disease"], {}).setdefault(str(r["month"]), {})[r["district_id"]] = {
            "tier": r["risk_tier"], "score": r["risk_score"], "conf": r["confidence"], "drivers": r["drivers"]}

    validation = {r["metric"]: {"value": r["value"], "note": r["note"]}
                  for r in cur.execute("SELECT metric, value, note FROM validation")}

    meta = {
        "diseases": sorted(fc.keys()),
        "states": sorted({d["state"] for d in districts}),
        "n_districts": len(districts),
        "months": [{"n": i, "abbr": a} for i, a in enumerate(
            ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]) if i],
        "source": "EpiClim (Zenodo 14580510), sourced from India IDSP. CC-BY-4.0.",
    }

    out = {"districts.json": districts, "forecasts.json": fc,
           "validation.json": validation, "meta.json": meta}
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
