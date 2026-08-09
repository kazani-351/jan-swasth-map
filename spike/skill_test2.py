"""T1 deeper spike v2: test BETTER transparent seasonal models, case-weighted held-out capture. Stdlib.

Model A: fixed regional monsoon window (Jul-Sep) for every district.
Model B: per-district top-3 months by TRAIN-year mean cases.
Metric that matters: what % of held-out dengue CASES fall in predicted high-risk months (chance=3/12=25%).
"""
import csv
from collections import defaultdict

PATH = "data/raw/Final_data.csv"
PILOT = {"Maharashtra", "Tamil Nadu", "West Bengal"}
TRAIN_MAX, TEST = 2015, range(2016, 2020)
MONSOON = {7, 8, 9}

agg = defaultdict(int)  # (state,district,year,mon) -> cases
for r in csv.DictReader(open(PATH, newline="")):
    if r["state_ut"] in PILOT and r["Disease"] == "Dengue":
        try:
            y, m = int(float(r["year"])), int(float(r["mon"]))
            agg[(r["state_ut"], r["district"], y, m)] += int(float(r["Cases"])) if r["Cases"] else 0
        except ValueError:
            pass

# per-district monthly mean cases from TRAIN years -> top-3 months (Model B)
train_mo = defaultdict(lambda: defaultdict(list))
for (s, d, y, m), cs in agg.items():
    if y <= TRAIN_MAX:
        train_mo[(s, d)][m].append(cs)
top3 = {}
for key, md in train_mo.items():
    means = {m: sum(v) / len(v) for m, v in md.items()}
    top3[key] = set(sorted(means, key=means.get, reverse=True)[:3])

# held-out evaluation
def evaluate(predict_months_fn, label):
    hit_cases = tot_cases = hit_n = tot_n = 0
    for (s, d, y, m), cs in agg.items():
        if y in TEST and cs > 0:
            pm = predict_months_fn((s, d))
            if pm is None:  # no training basis
                continue
            tot_cases += cs; tot_n += 1
            if m in pm: hit_cases += cs; hit_n += 1
    print(f"\n{label}")
    print(f"  test district-months: {tot_n}, cases: {tot_cases}")
    if tot_n:
        print(f"  case-weighted capture (big outbreaks in predicted months): {hit_cases/tot_cases:.1%}")
        print(f"  unweighted hit rate:                                       {hit_n/tot_n:.1%}")
        print(f"  chance baseline (|predicted months|/12): ~{ (3/12):.0%} (both models predict 3 months)")

evaluate(lambda k: MONSOON, "Model A: fixed monsoon window Jul-Sep (same for all districts)")
evaluate(lambda k: top3.get(k), "Model B: per-district top-3 training months")
# Hybrid: district top-3 if it has >=3 train years, else monsoon fallback
tyrs = defaultdict(set)
for (s, d, y, m), cs in agg.items():
    if y <= TRAIN_MAX and cs > 0: tyrs[(s, d)].add(y)
evaluate(lambda k: top3.get(k) if len(tyrs.get(k, set())) >= 3 else MONSOON,
         "Model C: district top-3 (if >=3 train yrs) else monsoon fallback")
