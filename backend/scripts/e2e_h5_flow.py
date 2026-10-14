"""E2E fitur baru: guess -> start (100 pertanyaan) -> report full dengan queries."""
import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://localhost:8000/api"
COMPANY = "合肥蓝天污水处理设备有限公司"

s = requests.Session()

# 1) AI推测行业
r = s.post(f"{BASE}/diagnose/guess", json={"company_name": COMPANY}, timeout=60)
assert r.status_code == 200, r.text
g = r.json()
print("guess:", g)
assert g["industry"] and len(g["keywords"]) >= 1

# 2) 开始诊断
r = s.post(f"{BASE}/diagnose", json={
    "company_name": COMPANY,
    "industry": g["industry"],
    "products": g["products"],
    "keywords": g["keywords"],
    "competitors": g["competitors"],
    "website": "",
}, timeout=60)
assert r.status_code == 200, r.text
code = r.json()["code"]
print("diagnosis code:", code)

# 3) tunggu selesai
for i in range(90):
    d = s.get(f"{BASE}/r/{code}", timeout=30).json()
    if d["status"] == "done":
        break
    if d["status"] == "failed":
        print("FAILED:", d.get("error")); sys.exit(1)
    time.sleep(2)
else:
    print("TIMEOUT"); sys.exit(1)

assert d["total_samples"] > 100, d["total_samples"]
assert d["industry"] == g["industry"]
print("done: score=", d["score"], "samples=", d["total_samples"])

# 4) full payload: queries 100 + alias_map + Q&A lengkap
full = s.get(f"{BASE}/r/{code}/full", params={"token": "x"}, timeout=30)
# tanpa token valid -> 401; kita test endpoint queries lewat verify cepat tidak perlu.
# Gunakan verify flow: minta kode (mock mengembalikan dev_code)
ph = "139" + str(int(time.time()))[-8:]
r = s.post(f"{BASE}/r/{code}/send-code", json={"phone": ph}, timeout=30)
assert r.status_code == 200, r.text
dev = r.json().get("dev_code") or r.json().get("code")
r = s.post(f"{BASE}/r/{code}/verify", json={"phone": ph, "code": dev, "consent": True}, timeout=30)
tok = r.json()["unlock_token"]
full = s.get(f"{BASE}/r/{code}/full", params={"token": tok}, timeout=30).json()
qs = full["queries"]
assert len(qs) == d["total_samples"] and len(qs) > 100, len(qs)
assert all(q["question"] and q["answer"] for q in qs)
assert "alias_map" in full
answers_with_brand = [q for q in qs if q["mentioned"]]
print(f"queries=100, dengan-brand={len(answers_with_brand)}, alias_brands={list(full['alias_map'].keys())}")
print("sample Q:", qs[0]["question"])
print("sample A:", qs[0]["answer"][:80])
print("E2E OK")
