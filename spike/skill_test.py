"""T1 deeper spike: does a TRANSPARENT seasonal model have held-out skill? Dengue, pilot states. Stdlib.

Task: learn each district's dengue peak-months from TRAIN years only, then on held-out years measure
how often actual outbreaks land in predicted peak-months vs a chance baseline. Also quantify how
concentrated dengue seasonality is (transferability), and climate association (explanatory only).
"""
import csv, statistics
from collections import defaultdict, Counter

PATH = "data/raw/Final_data.csv"
PILOT = {"Maharashtra", "Tamil Nadu", "West Bengal"}
DISEASE = "Dengue"
TRAIN_MAX = 2015
TEST = range(2016, 2020)  # 2016-2019 (skip sparse 2020-22)

# aggregate duplicate reports -> (state,district,year,mon) summed cases + mean climate
agg = defaultdict(lambda: [0, [], []])  # cases, preci list, temp list
for r in csv.DictReader(open(PATH, newline="")):
    if r["state_ut"] in PILOT and r["Disease"] == DISEASE:
        try:
            y, m = int(float(r["year"])), int(float(r["mon"]))
            c = int(float(r["Cases"])) if r["Cases"] else 0
        except ValueError:
            continue
        k = (r["state_ut"], r["district"], y, m)
        agg[k][0] += c
        if r["preci"]: agg[k][1].append(float(r["preci"]))
        if r["Temp"]: agg[k][2].append(float(r["Temp"]))

records = [(s, d, y, m, cs) for (s, d, y, m), (cs, _, _) in agg.items()]
print(f"aggregated dengue district-month records (pilot states): {len(records)}")

# --- seasonality concentration: share of cases by calendar month (all years) ---
by_month = Counter()
for s, d, y, m, cs in records:
    by_month[m] += cs
tot = sum(by_month.values())
top3 = sorted(by_month, key=by_month.get, reverse=True)[:3]
top3_share = sum(by_month[m] for m in top3) / tot if tot else 0
print("\ncases by month (share):")
for m in range(1, 13):
    if by_month.get(m): print(f"  m{m:02d}: {by_month[m]:6d}  ({by_month[m]/tot:.1%})")
print(f"top-3 months {sorted(top3)} carry {top3_share:.1%} of all dengue cases  <-- seasonality strength")

# --- per-district held-out skill test ---
train_months = defaultdict(set)      # district -> set of months seen in TRAIN years
train_years = defaultdict(set)
test_recs = defaultdict(list)        # district -> [(year,mon,cases)] in TEST years
for s, d, y, m, cs in records:
    if cs <= 0: continue
    if y <= TRAIN_MAX:
        train_months[(s, d)].add(m); train_years[(s, d)].add(y)
    elif y in TEST:
        test_recs[(s, d)].append((y, m, cs))

# qualify: districts with >=2 train years of history AND >=1 held-out outbreak
hits = misses = 0
cw_hit = cw_tot = 0
chance_sum = n_dist = 0
per_district = []
for key, tr in test_recs.items():
    pm = train_months.get(key, set())
    if len(train_years.get(key, set())) < 2 or not pm:
        continue
    n_dist += 1
    chance = len(pm) / 12.0
    chance_sum += chance
    d_hit = d_miss = 0
    for (y, m, cs) in tr:
        if m in pm: hits += 1; d_hit += 1; cw_hit += cs
        else:       misses += 1; d_miss += 1
        cw_tot += cs
    per_district.append((key[1], d_hit, d_hit + d_miss, sorted(pm)))

n = hits + misses
print(f"\nheld-out skill (districts qualifying: {n_dist}, test outbreak-months: {n}):")
if n:
    print(f"  seasonal hit rate (outbreak lands in predicted peak-month): {hits/n:.1%}")
    print(f"  chance baseline (avg predicted-months/12):                 {chance_sum/max(n_dist,1):.1%}")
    print(f"  case-weighted hit rate (do BIG outbreaks land in-season):  {cw_hit/cw_tot:.1%}" if cw_tot else "  (no cases)")
print("\n  per-district (held-out hits / total, predicted peak-months):")
for name, h, t, pm in sorted(per_district, key=lambda x: -x[2]):
    print(f"    {name:20s} {h}/{t}   peak-months={pm}")

# --- climate association (explanatory only; climate here is concurrent, not lagged) ---
hi = [statistics.mean(p) for (s,d,y,m),(cs,p,t) in agg.items() if cs>=100 and p]
lo = [statistics.mean(p) for (s,d,y,m),(cs,p,t) in agg.items() if 0<cs<100 and p]
if hi and lo:
    print(f"\nclimate (concurrent, explanatory): mean precip in big months (>=100 cases)={statistics.mean(hi):.3f} "
          f"vs small (<100)={statistics.mean(lo):.3f}")
