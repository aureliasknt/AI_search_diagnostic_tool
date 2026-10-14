"""Verify AI提问次数 tile + explanatory sub captions on the report."""
from playwright.sync_api import sync_playwright

URL = "http://localhost:5173/r/FnWkWQSqtDEp?reset=1"
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 390, "height": 844})
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(1200)
    # KPI: tile AI提问次数 jadi tile pertama, lebar penuh
    kpis = pg.locator(".kpi-grid .kpi")
    first = kpis.first
    assert "AI提问次数" in first.locator(".kpi-label").inner_text()
    assert first.locator(".kpi-value").inner_text() == "6"
    assert "提问 6 次" in first.locator(".kpi-sub").inner_text()
    assert kpis.count() == 5
    # 数据总览: ada tile AI提问次数 = 6
    ov = pg.locator("#sec-overview .ov")
    labels = [ov.nth(i).locator(".ov-label").inner_text() for i in range(ov.count())]
    assert labels[1] == "AI提问次数", labels
    assert ov.nth(1).locator(".ov-value").inner_text() == "6"
    # 分析说明: label baru
    info = pg.locator("#sec-info").inner_text()
    assert "AI提问次数" in info and "6 次提问 / 6 条回答" in info
    pg.evaluate("window.scrollTo(0, 400)")
    pg.wait_for_timeout(400)
    pg.screenshot(path="check_total_queries.png")
    b.close()
print("OK: AI提问次数 tile added, sub captions visible")
