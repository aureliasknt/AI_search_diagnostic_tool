"""?reset=1 must re-lock the view even when a token is stored."""
from playwright.sync_api import sync_playwright

BASE = "http://localhost:5173"
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844})
    pg = ctx.new_page()
    # simpan token dummy agar terkunci status "pernah unlock"
    pg.goto(f"{BASE}/r/FnWkWQSqtDEp", wait_until="domcontentloaded")
    pg.evaluate("localStorage.setItem('aidiag_unlock_FnWkWQSqtDEp', JSON.stringify({token:'dummy'}))")
    # buka dengan ?reset=1
    pg.goto(f"{BASE}/r/FnWkWQSqtDEp?reset=1", wait_until="networkidle")
    pg.wait_for_timeout(1200)
    assert pg.locator("#sec-competitor .lock-wrap .overlay").is_visible(), "not re-locked"
    assert pg.locator("#sec-competitor h2.section-title").inner_text().find("竞品分析") >= 0
    assert "竞品分析" in pg.locator("#sec-competitor h2.section-title").inner_text()
    pg.evaluate("document.getElementById('sec-competitor').scrollIntoView()")
    pg.wait_for_timeout(300)
    pg.screenshot(path="check_reset_lock.png")
    b.close()
print("OK: ?reset=1 re-locks the report view")
