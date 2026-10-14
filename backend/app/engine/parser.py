"""Parsing jawaban AI (PRD 4.2): deteksi penyebutan brand (exact + fuzzy alias),
posisi penyebutan pertama, dan jumlah penyebutan."""
import re

_PUNCT = re.compile(r"[\s，。、；：！？（）()【】\[\]《》<>\"'\"'.,;:!?\-—_·~|/\\]+")


def normalize(text: str) -> str:
    return _PUNCT.sub("", (text or "").lower())


def _aliases_of(brand: str, alias_map: dict[str, list[str]]) -> list[str]:
    aliases = [brand]
    for a in alias_map.get(brand, []):
        if a and a not in aliases:
            aliases.append(a)
    # alias terpanjang dulu agar "讯灵AI" tidak dipotong oleh "讯灵"
    return sorted(aliases, key=len, reverse=True)


def parse_answer(text: str, brands: list[str], alias_map: dict[str, list[str]] | None = None) -> dict:
    """Kembalikan {brand: {mentioned, first_index, count, order}}.
    order = urutan kemunculan pertama di antara brand yang disebut (1 = paling awal)."""
    alias_map = alias_map or {}
    norm_text = normalize(text)
    result: dict[str, dict] = {}
    hits: list[tuple[int, str]] = []

    for brand in brands:
        spans = []
        for alias in _aliases_of(brand, alias_map):
            needle = normalize(alias)
            if not needle:
                continue
            start = 0
            while True:
                idx = norm_text.find(needle, start)
                if idx < 0:
                    break
                spans.append((idx, idx + len(needle)))
                start = idx + len(needle)
        # gabungkan span yang tumpang tindih (alias "蓝天环保" & "蓝天环保科技"
        # keduanya cocok di teks yang sama — hitung sebagai 1 penyebutan)
        spans.sort()
        merged: list[tuple[int, int]] = []
        for s, e in spans:
            if merged and s < merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], e))
            else:
                merged.append((s, e))
        first_index = merged[0][0] if merged else -1
        mentioned = first_index >= 0
        result[brand] = {"mentioned": mentioned, "first_index": first_index,
                         "count": len(merged), "order": None}
        if mentioned:
            hits.append((first_index, brand))

    hits.sort()
    for order, (_, brand) in enumerate(hits, start=1):
        result[brand]["order"] = order
    return result


def mentioned_brand_count(parsed: dict) -> int:
    return sum(1 for v in parsed.values() if v["mentioned"])
