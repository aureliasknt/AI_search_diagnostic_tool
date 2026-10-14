"""E2E UI: redesign 查询详情 (gaya Xunling) -> list -> modal chat -> highlight brand besar merah."""
import time

from playwright.sync_api import sync_playwright

BASE = "http://localhost:5173"
CODE = "gHpNWeDE8xVu"  # report 105 pertanyaan yang sudah ada
COMPANY = "合肥蓝天污水处理设备有限公司"

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 390, "height": 844})

    pg.goto(f"{BASE}/r/{CODE}?reset=1", wait_until="networkidle")
    pg.wait_for_timeout(1200)
    # nav 5 tab, 查询详情 terkunci dengan judul
    assert pg.locator(".nav-item").count() == 5
    q = pg.locator("#sec-queries")
    assert "查询详情" in q.locator("h2.section-title").inner_text()
    assert q.locator(".lock-wrap .overlay").is_visible()
    pg.screenshot(path="ui_5_queries_locked.png")

    # unlock
    q.locator(".lock-btn").click()
    modal = pg.locator(".modal")
    phone = "139" + str(int(time.time()))[-8:]
    modal.locator("input[placeholder*='手机号']").fill(phone)
    with pg.expect_response(lambda r: "send-code" in r.url) as resp:
        modal.locator("button", has_text="获取验证码").click()
    dev_code = resp.value.json().get("dev_code") or resp.value.json().get("code")
    modal.locator("input[placeholder*='验证码']").fill(dev_code)
    modal.locator(".consent input[type=checkbox]").check()
    with pg.expect_response(lambda r: r.url.endswith("/verify")):
        modal.locator("button.submit").click()
    pg.wait_for_selector("#sec-queries .rpt-tr:not(.rpt-th)", timeout=30000)

    # list: 3 tab, 20 baris, header tabel, chip jumlah
    assert "共 105 条" in q.locator(".rpt-filter").inner_text()
    assert "查询详情" in q.locator(".rpt-title").inner_text()
    assert q.locator(".rpt-tab").count() == 3
    assert "提到品牌" in q.inner_text()
    rows = q.locator(".rpt-tr:not(.rpt-th)")
    assert rows.count() == 20
    assert q.locator(".rpt-th").inner_text().find("训练词") >= 0
    assert rows.first.locator(".op-hand").inner_text() == "👆"
    pg.evaluate("document.getElementById('sec-queries').scrollIntoView()")
    pg.wait_for_timeout(400)
    pg.screenshot(path="ui_6_queries_list.png")

    # pager
    q.locator(".pg-btn").nth(1).click()
    assert "2 / 6" in q.locator(".pg-info").inner_text()
    q.locator(".pg-btn").nth(0).click()

    # filter tab 提到品牌
    q.locator(".rpt-tab", has_text="提到品牌").click()
    assert rows.count() > 0
    q.locator(".rpt-tab", has_text="全部提问").click()

    # buka modal Q&A
    rows.first.click()
    pg.wait_for_selector(".qa-sheet", timeout=10000)
    assert pg.locator(".qa-avatar").inner_text() == "豆"
    assert "豆包" in pg.locator(".qa-name").inner_text()
    assert pg.locator(".qa-user-bubble").is_visible()
    hits = pg.locator(".qa-sheet .brand-big").count()
    print("brand-big hits:", hits)
    assert hits >= 1, "brand tidak di-highlight besar merah"
    assert "和豆包继续聊" in pg.locator(".qa-cta").inner_text()
    pg.screenshot(path="ui_7_qa_modal_v2.png")
    b.close()
print("UI REDESIGN E2E OK")
