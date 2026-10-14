"""Pembuatan kartu masalah -> rekomendasi (PRD 5.6, fase MVP: rule-match
atas basis data rekomendasi yang dikelola di panel admin, 2-5 kartu).

Jika rule yang terpenuhi kurang dari 2, kartu pelengkap dibuat otomatis dari
dimensi terlemah brand target (kesenjangan data), sehingga laporan selalu
memuat 2-5 masalah.
"""
import operator

from .scoring import BrandScore, neg_ratio

_OPS = {
    "<": operator.lt, "<=": operator.le,
    ">": operator.gt, ">=": operator.ge,
    "==": operator.eq, "!=": operator.ne,
}

_GAP_TEMPLATES = {
    "mention_rate": {
        "title": "品牌搜索提及覆盖率有提升空间",
        "problem": "在本次{total}条豆包AI回答样本中，品牌被提及的样本占比仍未达到领先水平，部分精准采购场景正被竞品承接。",
        "suggestion": "由企业市场部系统整理品牌介绍、产品线参数与客户案例，优先补齐官网可被AI抓取的知识库内容；完成后复测品牌提及率。",
    },
    "position_score": {
        "title": "品牌在AI回答中的排序仍需前移",
        "problem": "品牌虽进入AI回答，但多数情况下排序不在首位，首位曝光位置仍被竞品占据。",
        "suggestion": "由内容运营团队围绕高频采购问题制作结构化问答内容，布局行业垂直平台与自媒体矩阵，提升AI引用时的排序权重；完成后复测首位提及位置。",
    },
    "sentiment_score": {
        "title": "品牌正向内容积累不足",
        "problem": "AI回答中对品牌的正向描述占比有限，中性表述居多，尚不足以形成强说服力的品牌印象。",
        "suggestion": "由市场团队持续发布客户成功案例、权威检测报告与行业荣誉内容，增加可被AI引用的正向权威素材；完成后复测正向情感占比。",
    },
}


def _metric_value(name: str, target: BrandScore) -> float:
    if name == "neg_ratio":
        return neg_ratio(target)
    return float(getattr(target, name, 0) or 0)


def match_problems(rules: list[dict], scores: list[BrandScore], limit: int = 5) -> list[dict]:
    target = next((s for s in scores if s.is_target), scores[0] if scores else None)
    if target is None:
        return []
    cards, fired_metrics = [], set()
    for rule in rules:
        if not rule.get("enabled", True):
            continue
        op = _OPS.get(rule.get("op", "<"), operator.lt)
        try:
            hit = op(_metric_value(rule.get("metric", ""), target), float(rule.get("value", 0)))
        except (TypeError, ValueError):
            continue
        if hit:
            fired_metrics.add(rule.get("metric", ""))
            cards.append({
                "title": rule.get("title", ""),
                "problem_text": rule.get("problem", ""),
                "suggestion_text": rule.get("suggestion", ""),
            })
        if len(cards) >= limit:
            return cards[:limit]

    # pelengkap dari dimensi terlemah (selalu cukup untuk 2 kartu per PRD)
    weakest = sorted(
        ("mention_rate", "position_score", "sentiment_score"),
        key=lambda m: _metric_value(m, target),
    )
    for metric in weakest:
        if len(cards) >= 2 and len(cards) >= limit:
            break
        if metric in fired_metrics:
            continue
        tpl = _GAP_TEMPLATES[metric]
        cards.append({
            "title": tpl["title"],
            "problem_text": tpl["problem"].format(total=target.total),
            "suggestion_text": tpl["suggestion"],
        })
    return cards[:limit]
