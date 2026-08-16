"""Robustness: is the null a wrong-lag artifact, or is the dengue anomaly just climate-independent?
Test several precip windows incl. CONCURRENT (Jul-Sep). If even concurrent is flat, it's a true null.
"""
import json, math
from collections import defaultdict

targets = json.load(open("spike/leading_targets.json"))
clim = json.load(open("spike/leading_climate.json"))
TRAIN_MAX = 2015
WINDOWS = {"Apr-Jun(pre)": [4, 5, 6], "Jun-Jul(early)": [6, 7], "Jul-Sep(concurrent)": [7, 8, 9],
           "Jan-Jun(long pre)": [1, 2, 3, 4, 5, 6], "prevOct-Dec(lag)": [10, 11, 12]}


def wsum(key, year, months):
    ym = clim.get(key, {}).get(str(year), {})
    ps = [ym[str(m)]["precip"] for m in months if str(m) in ym and ym[str(m)]["precip"] is not None]
    return sum(ps) if len(ps) == len(months) else None


def pearson(a, b):
    n = len(a)
    if n < 3: return float("nan")
    ma, mb = sum(a)/n, sum(b)/n
    cov = sum((x-ma)*(y-mb) for x, y in zip(a, b))
    va = math.sqrt(sum((x-ma)**2 for x in a)); vb = math.sqrt(sum((y-mb)**2 for y in b))
    return cov/(va*vb) if va and vb else float("nan")


def spearman(a, b):
    rk = lambda v: [sorted(range(len(v)), key=lambda i: v[i]).index(i) for i in range(len(v))]
    return pearson(rk(a), rk(b))


logpeak = {}
for x in targets:
    key = f"{x['state']}|{x['district']}"
    for ys, peak in x["peak_by_year"].items():
        logpeak[(key, int(ys))] = math.log1p(peak)

print(f"{'window':20s} {'train Spearman':>14s} {'test Spearman':>14s}")
for name, months in WINDOWS.items():
    tr = defaultdict(lambda: {"p": [], "y": []})
    rows = []
    for (key, y), lp in logpeak.items():
        p = wsum(key, y, months)
        if p is None: continue
        rows.append((key, y, lp, p))
        if y <= TRAIN_MAX:
            tr[key]["p"].append(p); tr[key]["y"].append(lp)
    tr_rows, te_rows = [], []
    for key, y, lp, p in rows:
        t = tr[key]
        if len(t["y"]) < 2: continue
        anom = (lp - sum(t["y"])/len(t["y"]), p - sum(t["p"])/len(t["p"]))
        (tr_rows if y <= TRAIN_MAX else te_rows).append(anom)
    trs = spearman([r[1] for r in tr_rows], [r[0] for r in tr_rows])
    tes = spearman([r[1] for r in te_rows], [r[0] for r in te_rows])
    print(f"{name:20s} {trs:>+14.2f} {tes:>+14.2f}")
