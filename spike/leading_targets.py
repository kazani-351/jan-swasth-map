"""Leading-signal spike, step 1: build dengue targets per district-year + district coords. Stdlib.

Target = peak-season (Jul-Sep) dengue cases per district-year, for pilot districts with >=4 years
of dengue history (enough for a held-out interannual test). Coords for the Open-Meteo pull.
Writes spike/leading_targets.json.
"""
import csv, json
from collections import defaultdict

RAW = "data/raw/Final_data.csv"
PILOT = {"Maharashtra", "Tamil Nadu", "West Bengal"}
PEAK = {7, 8, 9}

by_dm = defaultdict(int)          # (state,district,year,month) -> cases
coords = {}                       # (state,district) -> [lats, lons]
for r in csv.DictReader(open(RAW, newline="")):
    if r["state_ut"] in PILOT and r["Disease"] == "Dengue":
        try:
            y, m = int(float(r["year"])), int(float(r["mon"]))
            c = int(float(r["Cases"])) if r["Cases"] else 0
        except ValueError:
            continue
        by_dm[(r["state_ut"], r["district"], y, m)] += c
        cc = coords.setdefault((r["state_ut"], r["district"]), [[], []])
        for i, col in enumerate(("Latitude", "Longitude")):
            try:
                cc[i].append(float(r[col]))
            except (ValueError, KeyError, TypeError):
                pass

# peak-season magnitude per district-year
peak_mag = defaultdict(int)       # (state,district) -> {year: jul-sep cases}
years_seen = defaultdict(set)
for (s, d, y, m), c in by_dm.items():
    if m in PEAK and c > 0:
        peak_mag[(s, d)]
        years_seen[(s, d)].add(y)
peak_by_dy = defaultdict(dict)
for (s, d, y, m), c in by_dm.items():
    if m in PEAK:
        peak_by_dy[(s, d)][y] = peak_by_dy[(s, d)].get(y, 0) + c

study = []
for key, ymap in peak_by_dy.items():
    yrs = [y for y, v in ymap.items() if v > 0]
    if len(yrs) >= 4:
        s, d = key
        la, lo = coords[key]
        study.append({
            "state": s, "district": d,
            "lat": round(sum(la) / len(la), 4), "lon": round(sum(lo) / len(lo), 4),
            "peak_by_year": {str(y): ymap.get(y, 0) for y in range(2009, 2020)},
        })

study.sort(key=lambda x: -sum(x["peak_by_year"].values()))
json.dump(study, open("spike/leading_targets.json", "w"), indent=1)
print(f"study districts (dengue peak in >=4 years): {len(study)}")
print("top by total peak-season dengue:")
for x in study[:12]:
    tot = sum(x["peak_by_year"].values())
    nyr = sum(1 for v in x["peak_by_year"].values() if v > 0)
    print(f"  {x['district']:22s} {x['state'][:2].upper()}  total={tot:6d}  years={nyr}  ({x['lat']},{x['lon']})")
print(f"\ntotal district-years with peak dengue: "
      f"{sum(1 for x in study for v in x['peak_by_year'].values() if v > 0)}")
