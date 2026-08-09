"""T1 spike: minimal honest backtest on WB/North 24 Parganas/Dengue/2017. Stdlib only. Throwaway.

Question: would a TRANSPARENT rule have flagged this outbreak >=1 week before the peak,
using signal available AT the time (not peeking ahead)? Measure lead_weeks.
"""
import csv, datetime

PATH = "data/raw/Final_data.csv"
TARGET = ("West Bengal", "North 24 Parganas", "Dengue")

recs = []
with open(PATH, newline="") as f:
    for r in csv.DictReader(f):
        if (r["state_ut"], r["district"], r["Disease"]) == TARGET:
            try:
                dt = datetime.date(int(float(r["year"])), int(float(r["mon"])), int(float(r["day"])))
                recs.append((dt, int(float(r["Cases"])) if r["Cases"] else 0,
                             float(r["preci"] or 0), float(r["Temp"] or 0)))
            except ValueError:
                pass
recs.sort()

print("All-years Dengue records for WB/North 24 Parganas (date, cases, preci, tempK):")
for dt, c, p, t in recs:
    print(f"  {dt}  cases={c:5d}  preci={p:.3f}  temp={t:.1f}")

# 2017 series only
s = [(dt, c, p, t) for dt, c, p, t in recs if dt.year == 2017]
print(f"\n2017 series: {len(s)} weekly records")
if not s:
    raise SystemExit("no 2017 data")

cases = [c for _, c, _, _ in s]
peak_i = cases.index(max(cases))
peak_dt = s[peak_i][0]
print(f"peak: week {peak_i+1}/{len(s)} on {peak_dt}, cases={cases[peak_i]}")

# Transparent rule, causal (only uses weeks up to & including current):
#   baseline = median of prior weeks (expanding, min 2 priors)
#   Watch if cases > 2x baseline AND rising vs last week
#   High  if cases > 4x baseline AND rising
# No peeking ahead. Report first Watch and first High week and lead vs peak.
def tier(i):
    if i < 2:  # need >=2 priors for a baseline
        return "n/a"
    prior = sorted(cases[:i])
    base = prior[len(prior)//2] or 1  # median, floor 1
    rising = cases[i] > cases[i-1]
    if cases[i] > 4*base and rising: return "High"
    if cases[i] > 2*base and rising: return "Watch"
    return "Low"

print("\nweek-by-week causal tiers:")
first_watch = first_high = None
for i, (dt, c, p, t) in enumerate(s):
    tg = tier(i)
    print(f"  w{i+1} {dt} cases={c:5d} -> {tg}")
    if tg == "Watch" and first_watch is None: first_watch = i
    if tg == "High" and first_high is None: first_high = i

def lead(i):
    return None if i is None else (peak_i - i)

print(f"\npeak at week index {peak_i}")
print(f"first Watch at week index {first_watch}  -> lead = {lead(first_watch)} weeks before peak")
print(f"first High  at week index {first_high}   -> lead = {lead(first_high)} weeks before peak")

lw = lead(first_watch)
verdict = "PASS" if (lw is not None and lw >= 1) else "WEAK/FAIL"
print(f"\nT1 backtest verdict: {verdict} (need a Watch/High flag >=1 week before peak)")
