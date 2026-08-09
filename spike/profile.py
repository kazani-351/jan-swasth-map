"""T1 spike: profile EpiClim to decide if the backtest is feasible. Stdlib only. Throwaway."""
import csv, datetime
from collections import defaultdict, Counter

PATH = "data/raw/Final_data.csv"
STATES = {"Maharashtra", "Tamil Nadu", "West Bengal"}
DISEASES = {"Dengue", "Malaria", "Acute Diarrhoeal Disease"}

rows = []
with open(PATH, newline="") as f:
    for r in csv.DictReader(f):
        try:
            r["_cases"] = int(float(r["Cases"])) if r["Cases"] else 0
            r["_year"] = int(float(r["year"])) if r["year"] else None
            r["_mon"] = int(float(r["mon"])) if r["mon"] else None
            r["_day"] = int(float(r["day"])) if r["day"] else None
        except ValueError:
            r["_cases"] = r["_year"] = r["_mon"] = r["_day"] = None
        rows.append(r)

print(f"total rows: {len(rows)}")

# year coverage
yr = Counter(r["_year"] for r in rows if r["_year"])
print("\nyear -> row count:")
for y in sorted(yr): print(f"  {y}: {yr[y]}")

# disease distribution
dis = Counter(r["Disease"] for r in rows)
print("\ntop diseases:")
for d, c in dis.most_common(8): print(f"  {d}: {c}")

# per pilot state: events per disease
print("\npilot-state event counts (rows) by disease:")
for s in STATES:
    sub = [r for r in rows if r["state_ut"] == s]
    dd = Counter(r["Disease"] for r in sub if r["Disease"] in DISEASES)
    print(f"  {s}: total={len(sub)}  " + "  ".join(f"{k}={v}" for k, v in dd.items()))

# backtest candidates: (state, district, disease, year) with many weekly records + a clear peak
print("\nbacktest candidates (pilot states + target diseases, >=6 weekly records):")
grp = defaultdict(list)  # key -> list of (date, cases)
for r in rows:
    if r["state_ut"] in STATES and r["Disease"] in DISEASES and r["_year"] and r["_mon"] and r["_day"]:
        try:
            dt = datetime.date(r["_year"], r["_mon"], r["_day"])
        except ValueError:
            continue
        grp[(r["state_ut"], r["district"], r["Disease"], r["_year"])].append((dt, r["_cases"]))

cands = []
for key, pts in grp.items():
    pts.sort()
    nweeks = len(pts)
    total = sum(c for _, c in pts)
    peak = max(c for _, c in pts)
    span = (pts[-1][0] - pts[0][0]).days
    cands.append((nweeks, total, peak, span, key))

cands.sort(reverse=True)  # by nweeks, then total
for nweeks, total, peak, span, key in cands[:20]:
    if nweeks >= 6:
        st, dist, dis_, yr_ = key
        print(f"  {st}/{dist} {dis_} {yr_}: weeks={nweeks} total={total} peak={peak} span={span}d")

print(f"\ncandidates with >=6 weekly records: {sum(1 for c in cands if c[0] >= 6)}")
print(f"candidates with >=10 weekly records: {sum(1 for c in cands if c[0] >= 10)}")
