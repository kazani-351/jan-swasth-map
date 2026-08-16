"""Leading-signal spike, step 2: pull independent monthly climate per district (Open-Meteo/ERA5).

For each study district, fetch daily precip + mean temp 2009-2019, aggregate to monthly.
This climate is INDEPENDENT of the outbreak rows (unlike EpiClim's concurrent climate), so it can
be used as a genuine LAGGED predictor. Writes spike/leading_climate.json. Fail-loud.
"""
import json, sys, time, urllib.parse, urllib.request
from collections import defaultdict

STUDY = json.load(open("spike/leading_targets.json"))
BASE = "https://archive-api.open-meteo.com/v1/archive"


def fetch(lat, lon):
    q = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon,
        "start_date": "2009-01-01", "end_date": "2019-12-31",
        "daily": "precipitation_sum,temperature_2m_mean", "timezone": "Asia/Kolkata"})
    with urllib.request.urlopen(f"{BASE}?{q}", timeout=60) as r:
        return json.load(r)["daily"]


out = {}
for i, x in enumerate(STUDY):
    key = f"{x['state']}|{x['district']}"
    try:
        d = fetch(x["lat"], x["lon"])
    except Exception as e:
        print(f"FATAL: fetch failed for {key}: {e}", file=sys.stderr)
        sys.exit(1)
    psum = defaultdict(float)   # (y,m) -> precip sum
    tvals = defaultdict(list)   # (y,m) -> temps
    for t, p, tm in zip(d["time"], d["precipitation_sum"], d["temperature_2m_mean"]):
        y, m = t[:4], int(t[5:7])
        if p is not None:
            psum[(y, m)] += p
        if tm is not None:
            tvals[(y, m)].append(tm)
    monthly = {}
    for (y, m) in sorted(set(psum) | set(tvals)):
        monthly.setdefault(y, {})[str(m)] = {
            "precip": round(psum[(y, m)], 1),
            "temp": round(sum(tvals[(y, m)]) / len(tvals[(y, m)]), 1) if tvals[(y, m)] else None,
        }
    out[key] = monthly
    print(f"  [{i+1}/{len(STUDY)}] {x['district']} ({x['state'][:2]}) ok")
    time.sleep(1)

json.dump(out, open("spike/leading_climate.json", "w"))
print(f"wrote spike/leading_climate.json for {len(out)} districts")
