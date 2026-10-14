"""Penyusunan pertanyaan: kata kunci industri -> variasi pertanyaan realistis (PRD 4.1)."""


def build_question_plan(keyword: str, templates: list[dict], variants: int) -> list[str]:
    """Ubah kata kunci menjadi `variants` (3-5) variasi pertanyaan dari templat."""
    texts = [t["text"] for t in sorted(templates, key=lambda x: x.get("id", 0)) if t.get("text")]
    if not texts:
        texts = ["{kw}哪家好"]
    variants = max(3, min(5, variants))
    chosen = [texts[i % len(texts)] for i in range(variants)]
    return [tpl.replace("{kw}", keyword) for tpl in chosen]


def build_question_plan_exact(keywords: list[str], templates: list[dict],
                              total: int = 100) -> list[tuple[str, str, int]]:
    """Rencana pertanyaan MINIMAL `total` (selalu > total), kuota rata ke tiap
    kata kunci dan dibulatkan ke atas ke siklus templat penuh — jadi jumlah
    putaran tiap keyword utuh & merata. Tiap pertanyaan = (keyword, teks, round).

    Contoh (5 templat): 3 keyword -> 35/35/35 = 105; 4 keyword -> 25/25/25/25
    = 100 -> +1 siklus = 105."""
    import math

    texts = [t["text"] for t in sorted(templates, key=lambda x: x.get("id", 0)) if t.get("text")]
    if not texts:
        texts = ["{kw}哪家好"]
    kws = [k for k in keywords if k] or [""]
    n, per = len(kws), len(texts)
    cycles = math.ceil(math.ceil(total / n) / per)
    quota = cycles * per
    bump = per if n * quota <= total else 0  # pastikan hasil SELALU > total

    plan: list[tuple[str, str, int]] = []
    for kw in kws:
        for i in range(quota + bump):
            rnd = i // per + 1
            plan.append((kw, texts[i % per].replace("{kw}", kw), rnd))
        bump = 0
    return plan
