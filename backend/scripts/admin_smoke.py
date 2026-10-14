# -*- coding: utf-8 -*-
"""Smoke test panel admin: login -> diagnosa -> detail -> share/QR -> prospek -> konfig."""
import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "http://localhost:5174"

steps = []
def ok(name, cond, extra=""):
    steps.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""))

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_context(viewport={"width": 1440, "height": 900}).new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    # login
    page.goto(BASE + "/login", wait_until="networkidle")
    ok("halaman login tampil", page.locator("text=AI搜索诊断系统").count() > 0)
    page.fill("input[placeholder*=用户名], input[type=text]", "admin")
    page.fill("input[type=password]", "admin123")
    page.locator("button:has-text('登')").first.click()
    page.wait_for_url("**/diagnoses", timeout=10000)
    page.wait_for_timeout(1200)
    ok("login -> redirect /diagnoses", "/diagnoses" in page.url)

    # daftar diagnosa
    body = page.inner_text("body")
    ok("tabel diagnosa berisi contoh", "安徽绿清水处理" in body)
    ok("status 已完成", "已完成" in body)
    page.screenshot(path="admin_1_list.png")

    # share dialog (QR)
    page.locator("button:has-text('分享')").first.click()
    page.wait_for_timeout(900)
    ok("dialog share + QR svg", page.locator(".share-body svg, .qr svg").count() > 0)
    ok("url share localhost:5173", "5173/r/" in (page.inner_text("body") + str(page.locator(".share-body input").input_value() if page.locator(".share-body input").count() else "")))
    page.screenshot(path="admin_2_share.png")
    page.keyboard.press("Escape")

    # detail
    page.locator("button:has-text('详情')").first.click()
    page.wait_for_timeout(1200)
    body = page.inner_text("body")
    ok("detail: metrik brand tampil", "品牌" in body and "提及率" in body)
    page.locator(".el-tabs__item:has-text('问题与建议')").click()
    page.wait_for_timeout(600)
    ok("detail: kartu masalah tampil", "优化建议" in page.inner_text("body"))
    page.locator(".el-tabs__item:has-text('GEO营销对比')").click()
    page.wait_for_timeout(600)
    ok("detail: editor GEO tampil", "GEO布局阶段" in page.inner_text("body"))
    page.screenshot(path="admin_3_detail.png")

    # prospek
    page.goto(BASE + "/prospects", wait_until="networkidle")
    page.wait_for_timeout(1000)
    body = page.inner_text("body")
    ok("prospek ter-mask tampil", "****" in body)
    page.screenshot(path="admin_4_prospects.png")

    # konfigurasi
    page.goto(BASE + "/config", wait_until="networkidle")
    page.wait_for_timeout(1000)
    ok("tab bobot tampil", page.locator(".el-slider").count() >= 3)
    page.locator(".el-tabs__item:has-text('提问模板')").click(); page.wait_for_timeout(700)
    ok("tab templat: {kw} tampil", "{kw}" in page.inner_text("body"))
    page.locator(".el-tabs__item:has-text('平台配置')").click(); page.wait_for_timeout(700)
    ok("tab platform: radio doubao", page.locator("text=豆包").count() > 0)
    page.screenshot(path="admin_5_config.png")

    # guard: sales tak boleh ke /config
    page.goto(BASE + "/login", wait_until="networkidle"); page.wait_for_timeout(600)
    page.fill("input[placeholder*=用户名], input[type=text]", "sales01")
    page.fill("input[type=password]", "sales123")
    page.locator("button:has-text('登')").first.click()
    page.wait_for_url("**/diagnoses", timeout=10000)
    page.goto(BASE + "/config", wait_until="networkidle"); page.wait_for_timeout(800)
    ok("guard: sales diarahkan dari /config", "/config" not in page.url, page.url)

    browser.close()
    ok("tidak ada JS error", len(errors) == 0, "; ".join(errors[:3]))

print()
failed = [n for n, c in steps if not c]
print(f"HASIL: {len(steps)-len(failed)}/{len(steps)} PASS" + (f"  GAGAL: {failed}" if failed else ""))
sys.exit(1 if failed else 0)
