"""Leading-signal spike, step 3: does PRE-SEASON climate predict interannual dengue deviation,
held-out, beyond the per-district seasonal baseline? Stdlib. This is the gate for the big bet.

Design (no leakage):
- Target per district-year = log1p(Jul-Sep dengue cases).
- Baseline model = each district's TRAINING-year mean log-peak (pure seasonality; no year info).
- Leading signal = pre-monsoon (Apr-Jun) precip & temp ANOMALY vs the district's training climatology.
- Test: on held-out 2016-19 district-years, does climate anomaly track the dengue anomaly
  (target minus baseline)? Rank correlation + does a train-fit climate model cut held-out MAE?
"""
import json, math
from collections import defaultdict

targets = json.load(open("spike/leading_targets.json"))
clim = json.load(open("spike/leading_climate.json"))
TRAIN_MAX = 2015
PRE = [4, 5, 6]  # pre-monsoon months leading the Jul-Sep peak


def pre_season(key, year):
    ym = clim.get(key, {}).get(str(year))
    if not ym:
        return None, None
    ps = [ym[str(m)]["precip"] for m in PRE if str(m) in ym and ym[str(m)]["precip"] is not None]
    ts = [ym[str(m)]["temp"] for m in PRE if str(m) in ym and ym[str(m)]["temp"] is not None]
    if len(ps) < len(PRE) or len(ts) < len(PRE):
        return None, None
    return sum(ps), sum(ts) / len(ts)


# assemble per district-year records
recs = []  # (key, year, logpeak, precip, temp)
for x in targets:
    key = f"{x['state']}|{x['district']}"
    for ys, peak in x["peak_by_year"].items():
        y = int(ys)
        pr, tp = pre_season(key, y)
        if pr is None:
            continue
        recs.append((key, y, math.log1p(peak), pr, tp))

# per-district training climatology (baseline + anomaly reference)
tr = defaultdict(lambda: {"peak": [], "precip": [], "temp": []})
for key, y, lp, pr, tp in recs:
    if y <= TRAIN_MAX:
        tr[key]["peak"].append(lp); tr[key]["precip"].append(pr); tr[key]["temp"].append(tp)
mean = lambda xs: sum(xs) / len(xs) if xs else None

# build anomaly rows for districts with >=2 training years
train_rows, test_rows = [], []
for key, y, lp, pr, tp in recs:
    t = tr[key]
    if len(t["peak"]) < 2:
        continue
    row = (lp - mean(t["peak"]), pr - mean(t["precip"]), tp - mean(t["temp"]))  # (peak_anom, precip_anom, temp_anom)
    (train_rows if y <= TRAIN_MAX else test_rows).append(row)


def pearson(a, b):
    n = len(a)
    if n < 3:
        return float("nan")
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    va = math.sqrt(sum((x - ma) ** 2 for x in a)); vb = math.sqrt(sum((y - mb) ** 2 for y in b))
    return cov / (va * vb) if va and vb else float("nan")


def spearman(a, b):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        rk = [0] * len(v)
        for r, i in enumerate(order):
            rk[i] = r
        return rk
    return pearson(ranks(a), ranks(b))


def report(rows, label):
    pa = [r[0] for r in rows]; pp = [r[1] for r in rows]; tt = [r[2] for r in rows]
    print(f"\n{label} (n={len(rows)} district-years):")
    print(f"  precip-anom vs dengue-anom : Spearman {spearman(pp, pa):+.2f}   Pearson {pearson(pp, pa):+.2f}")
    print(f"  temp-anom   vs dengue-anom : Spearman {spearman(tt, pa):+.2f}   Pearson {pearson(tt, pa):+.2f}")
    return pa, pp, tt


tr_pa, tr_pp, tr_tt = report(train_rows, "TRAIN (in-sample)")
te_pa, te_pp, te_tt = report(test_rows, "TEST (held-out 2016-19)")

# held-out MAE: does a train-fit univariate climate model (dengue_anom ~ precip_anom) beat baseline (predict 0)?
def slope(x, y):
    n = len(x); mx, my = sum(x) / n, sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)); den = sum((xi - mx) ** 2 for xi in x)
    return (num / den if den else 0.0), (my - (num / den if den else 0.0) * mx)
b1, b0 = slope(tr_pp, tr_pa)
mae_base = sum(abs(a) for a in te_pa) / len(te_pa)                       # baseline predicts 0 anomaly
mae_clim = sum(abs(a - (b0 + b1 * p)) for a, p in zip(te_pa, te_pp)) / len(te_pa)
sign_agree = sum(1 for a, p in zip(te_pa, te_pp) if (a > 0) == (p > 0)) / len(te_pa)

print(f"\nheld-out MAE (log-cases anomaly):  baseline(seasonal)={mae_base:.3f}   +precip model={mae_clim:.3f}   "
      f"improvement={100*(mae_base-mae_clim)/mae_base:+.1f}%")
print(f"held-out sign agreement (wet pre-season -> bigger outbreak): {sign_agree:.0%}")

te_sp = spearman(te_pp, te_pa)
verdict = ("SIGNAL" if (te_sp > 0.25 and mae_clim < mae_base) else
           "WEAK" if (te_sp > 0.1 or mae_clim < mae_base) else "NO SIGNAL")
print(f"\nLEADING-SIGNAL VERDICT: {verdict}  (held-out precip Spearman {te_sp:+.2f}, "
      f"MAE {'better' if mae_clim < mae_base else 'not better'} than seasonal baseline)")
