"""E2E UI: halaman input -> AI推测行业 -> 开始诊断 -> report -> unlock -> 查询详情 modal."""
import time

from playwright.sync_api import sync_playwright

BASE = "http://localhost:5173"
COMPANY = "合肥金泉环保科技有限公司"
PHONE = "139" + str(int(time.time()))[-8:]

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 390, "height": 844})

    # 1) halaman start
    pg.goto(BASE + "/", wait_until="networkidle")
    assert pg.locator(".intro-title").is_visible()
    pg.fill(".fld-input", COMPANY)
    pg.click("text=✨ AI推测行业")
    pg.wait_for_selector(".chip", timeout=30000)
    n_kw = pg.locator(".chip:not(.gray)").count()
    assert n_kw >= 1, "keywords kosong"
    assert pg.locator(".fld").nth(1).locator("input").input_value() != ""  # industry terisi
    pg.screenshot(path="ui_1_start_filled.png")

    # 2) 开始诊断 -> redirect ke /r/:code
    pg.click("button.btn.primary")
    pg.wait_for_url(lambda u: "/r/" in u, timeout=30000)
    code = pg.url.split("/r/")[1]
    print("report code:", code)

    # 3) tunggu selesai (progress polling otomatis)
    pg.wait_for_selector(".gauge-card", timeout=180000)
    pg.wait_for_timeout(1500)
    assert pg.locator(".nav-item").count() == 5
    # tab 查询详情 terkunci: judul tampil, konten blur
    q = pg.locator("#sec-queries")
    assert "查询详情" in q.locator("h2.section-title").inner_text()
    assert q.locator(".lock-wrap .overlay").is_visible()
    pg.screenshot(path="ui_2_report_locked.png")

    # 4) unlock lewat gate modal (tangkap dev_code dari response)
    q.locator(".lock-btn").click()
    modal = pg.locator(".modal")
    modal.locator("input[placeholder*='手机号']").fill(PHONE)
    with pg.expect_response(lambda r: "send-code" in r.url) as resp:
        modal.locator("button", has_text="获取验证码").click()
    dev_code = resp.value.json().get("dev_code") or resp.value.json().get("code")
    modal.locator("input[placeholder*='验证码']").fill(dev_code)
    modal.locator(".consent input[type=checkbox]").check()
    with pg.expect_response(lambda r: r.url.endswith("/verify")):
        modal.locator("button.submit").click()
    pg.wait_for_selector("#sec-queries .q-row", timeout=30000)
    print("unlocked")

    # 5) tab 查询详情: 20 baris per halaman, pager, buka modal
    assert pg.locator("#sec-queries .q-row").count() == 20
    pg.locator("#sec-queries .q-row").first.click()
    pg.wait_for_selector(".qa-modal", timeout=10000)
    hits = pg.locator(".qa-modal .brand-hit").count()
    print("brand hits in modal:", hits)
    assert hits >= 1, "tidak ada brand yang di-highlight"
    answer = pg.locator(".qa-modal .qa-sec-text.answer").inner_text()
    assert COMPANY[:4] in answer or "环保" in answer
    pg.screenshot(path="ui_3_qa_modal.png")

    # 6) pager next
    pg.locator(".qa-close").click()
    pg.locator("#sec-queries .pg-btn", has_text="下一页").click()
    assert "2 / 5" in pg.locator("#sec-queries .pg-info").inner_text()
    pg.screenshot(path="ui_4_queries_page2.png")
    b.close()
print("UI E2E OK")
