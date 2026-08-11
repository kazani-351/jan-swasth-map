#!/usr/bin/env python3
"""Refresh the snapshot from source, end to end. PROVABLY WIRED, not load-bearing for the demo.

Re-pulls EpiClim from Zenodo, verifies integrity, then rebuilds seed -> forecast -> export.
Fail-loud (house rule): any step failing exits non-zero and does NOT clobber the existing good
snapshot — the download lands in a temp file and only atomically replaces the snapshot after md5
passes. No silent stale-success.

Run:  python3 pipeline/refresh.py     (from repo root)
"""
import hashlib, os, subprocess, sys, tempfile, urllib.request

ZENODO_URL = "https://zenodo.org/records/14580510/files/Final_data.csv?download=1"
EXPECTED_MD5 = "a6c961b95a454226e4720ae1745f9f16"  # pinned; a mismatch means the source changed -> human review
RAW = "data/raw/Final_data.csv"
STEPS = ["pipeline/ingest.py", "pipeline/forecast.py", "pipeline/export.py"]


def die(m):
    print(f"FATAL: {m}", file=sys.stderr)
    sys.exit(1)


def main():
    os.makedirs(os.path.dirname(RAW), exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        print("pulling EpiClim from Zenodo ...")
        try:
            urllib.request.urlretrieve(ZENODO_URL, tmp)
        except Exception as e:
            die(f"download failed: {e} (existing snapshot left intact)")
        got = hashlib.md5(open(tmp, "rb").read()).hexdigest()
        if got != EXPECTED_MD5:
            die(f"md5 mismatch: got {got}, expected {EXPECTED_MD5} (source changed — review before accepting; snapshot left intact)")
        os.replace(tmp, RAW)
        print(f"snapshot refreshed + verified (md5 {got})")
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

    for step in STEPS:
        print(f"running {step} ...")
        if subprocess.run([sys.executable, step]).returncode != 0:
            die(f"{step} failed — pipeline aborted (partial outputs may exist; re-run to fix)")
    print("refresh complete.")


if __name__ == "__main__":
    main()
