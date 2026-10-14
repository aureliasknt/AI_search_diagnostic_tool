"""Quick visual check: locked report shows section titles."""
from playwright.sync_api import sync_playwright

URL = "http://localhost:5173/r/FnWkWQSqtDEp"
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 390, "height": 844})
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(1200)
    for sid, title in [("sec-competitor", "竞品分析"), ("sec-sentiment", "舆情分析"), ("sec-problems", "报告总结")]:
        el = pg.locator(f"#{sid}")
        assert el.count() == 1, f"{sid} missing"
        t = el.locator("h2.section-title")
        assert t.count() == 1 and title in (t.inner_text() or ""), f"{sid} title wrong: {t.inner_text()!r}"
        assert t.is_visible(), f"{sid} title not visible"
        chip = el.locator(".lock-chip")
        assert chip.is_visible(), f"{sid} lock chip not visible"
        # konten placeholder tetap ada & terkunci
        assert el.locator(".lock-wrap .overlay").is_visible(), f"{sid} lock overlay missing"
    # scroll ke section terkunci lalu screenshot
    pg.evaluate("document.getElementById('sec-competitor').scrollIntoView()")
    pg.wait_for_timeout(400)
    pg.screenshot(path="check_locked_titles.png")
    b.close()
print("OK: titles visible before unlock, content still locked")
