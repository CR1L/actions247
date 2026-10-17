#!/usr/bin/env python3
"""Sanity check after fetch_data.py: refuse to publish a run where key sources failed."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "data", "assets.json")))
c = d["counts"]
print(json.dumps(c, indent=1))
for k, v in d["sources"].items():
    print(("[OK]  " if v["ok"] else "[FAIL]"), k, "-", v["detail"])
problems = []
if c.get("assets", 0) < 1000: problems.append("fewer than 1000 assets")
if c.get("with_token_price", 0) < 100: problems.append("fewer than 100 token prices")
if c.get("on_kraken", 0) < 50: problems.append("Kraken availability missing")
if c.get("on_okx", 0) < 50: problems.append("OKX availability missing")
if problems:
    print("NOT PUBLISHING:", "; ".join(problems)); sys.exit(1)
print("data OK")
