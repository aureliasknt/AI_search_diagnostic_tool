# -*- coding: utf-8 -*-
"""E2E UAT (PRD Bab 9) terhadap stack lokal: H5 -> gerbang SMS -> unlock -> PDF."""
import sys, json, time, random, urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_H5 = "http://localhost:5173"
BASE_API = "http://localhost:8000/api"
PHONE = f"139{random.randint(10000000, 99999999)}"  # unik per run, hindari cooldown 60s

from playwright.sync_api import sync_playwright

def api(path, payload=None, headers=None):
    req = urllib.request.Request(BASE_API + path, data=json.dumps(payload).encode() if payload else None,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))

steps = []
def ok(name, cond, extra=""):
    steps.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""))

admin = api("/auth/login", {"username": "admin", "password": "admin123"})
AUTH = {"Authorization": f"Bearer {admin['token']}"}
diag_list = api("/diagnoses", headers=AUTH)
CODE = next(d["share_code"] for d in diag_list["items"] if d["status"] == "done")
print(f"laporan uji: code={CODE}")

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True)
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    # 1) Buka ringkasan tanpa isi data
    summary = api(f"/r/{CODE}")
    expect_score = f"{summary['score']:.2f}"
    page.goto(f"{BASE_H5}/r/{CODE}", wait_until="networkidle")
    page.wait_for_timeout(1200)
    body = page.inner_text("body")
    ok("halaman terbuka & ada judul perusahaan", "安徽绿清水处理" in body)
    ok("skor tampil (API=halaman)", expect_score in body or expect_score.rstrip("0").rstrip(".") in body,
       f"score={expect_score}")
    ok("section terkunci tampil (gembok/blur)", page.locator(".lock-overlay, .locked, [class*=lock]").count() > 0,
       f"lock-els={page.locator('.lock-overlay, .locked, [class*=lock]').count()}")
    ok("TIDAK ada indikator 信源/来源分析", ("信源" not in body and "来源平台" not in body))
    page.screenshot(path="shot_1_locked.png", full_page=False)

    # 2) Klik area terkunci -> GateModal
    page.locator(".lock-overlay, .locked, [class*=lock]").first.click()
    page.wait_for_timeout(600)
    ok("GateModal muncul (input hp)", page.locator("input[type=tel], input[placeholder*=手机], input[placeholder*=号]").count() > 0)
    page.screenshot(path="shot_2_gate.png", full_page=False)

    # 3) Minta kode (mock -> dev_code di response); tangkap response browser
    page.fill("input[type=tel], input[placeholder*=手机], input[placeholder*=号]", PHONE)
    with page.expect_response(lambda r: "send-code" in r.url) as resp_info:
        page.locator("button:has-text('获取验证码'), button:has-text('获取')").first.click()
    sent = resp_info.value.json()
    page.wait_for_timeout(900)
    dev_code = sent.get("dev_code", "")
    ok("send-code mengembalikan dev_code (mock)", bool(dev_code), f"dev_code={dev_code}")

    # isi kode + consent
    page.fill(".modal input[placeholder*='验证码']", dev_code)
    consent = page.locator(".modal .consent input[type=checkbox]")
    consent.check(force=True)
    page.screenshot(path="shot_3_filled.png", full_page=False)
    page.locator(".modal button.submit").click()
    page.wait_for_timeout(1500)

    # 4) Section terbuka
    body2 = page.inner_text("body")
    ok("setelah verifikasi section terbuka (竞品/舆情/总结 muncul)",
       ("竞品" in body2 and "舆情" in body2 and ("优化建议" in body2 or "分析问题" in body2)))
    ok("tombol ekspor PDF muncul", page.locator("button:has-text('PDF'), a:has-text('PDF')").count() > 0)
    leak = [t for t in ("信源", "来源平台") if t in body2]
    for t in leak:
        i = body2.find(t)
        print(f"  -> kebocokan '{t}': ...{body2[max(0,i-30):i+30]}...")
    ok("TIDAK ada indikator 信源 setelah unlock", not leak)
    page.screenshot(path="shot_4_unlocked.png", full_page=True)

    token = page.evaluate("localStorage.getItem('unlock:" + CODE + "') || localStorage.getItem('unlock:" + CODE + "')")
    ok("unlock token tersimpan di localStorage", bool(token))

    # 5) PDF endpoint
    req = urllib.request.Request(f"{BASE_API}/r/{CODE}/pdf?token={token}")
    with urllib.request.urlopen(req, timeout=120) as r:
        pdf = r.read()
        ctype = r.headers.get("Content-Type")
    ok("PDF dihasilkan backend", pdf[:5] == b"%PDF-" and "pdf" in ctype, f"{len(pdf)} bytes, {ctype}")

    browser.close()
    ok("tidak ada JS error", len(errors) == 0, "; ".join(errors[:3]))

# 6) Prospek masuk (mask) + status + Excel (pakai token admin di atas)
pros = api("/prospects", headers=AUTH)
found = [p for p in pros["items"] if p["phone_mask"].startswith("139")]
ok("prospek realtime tampil (mask)", bool(found), json.dumps(found[0]["phone_mask"] if found else "", ensure_ascii=False))
if found:
    upd = urllib.request.Request(f"{BASE_API}/prospects/{found[0]['id']}", data=json.dumps({"status": "contacted"}).encode(),
                                 headers={"Content-Type": "application/json", **AUTH}, method="PATCH")
    urllib.request.urlopen(upd)
    ok("PATCH status prospek", True)
req = urllib.request.Request(f"{BASE_API}/prospects/export", headers=AUTH)
with urllib.request.urlopen(req) as r:
    xls = r.read()
ok("Excel diekspor", xls[:2] == b"PK" and len(xls) > 1000, f"{len(xls)} bytes")

print()
failed = [n for n, c in steps if not c]
print(f"HASIL: {len(steps)-len(failed)}/{len(steps)} PASS" + (f"  GAGAL: {failed}" if failed else ""))
sys.exit(1 if failed else 0)
