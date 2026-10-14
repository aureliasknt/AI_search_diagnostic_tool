"""Unit test model penilaian (PRD 4.3)."""
from app.engine.scoring import category_of, compute_brand_scores, rank_scores

BRANDS = ["目标公司", "竞品A", "竞品B"]
WEIGHTS = {"mention": 40, "position": 30, "sentiment": 30}


def _samples(target_mentioned=8, total=10, pos=6, neu=2, neg=0):
    parsed, sents = [], []
    for i in range(total):
        mentioned = i < target_mentioned
        parsed.append({
            "目标公司": {"mentioned": mentioned, "count": 1 if mentioned else 0,
                        "order": 1 if mentioned else None},
            "竞品A": {"mentioned": False, "count": 0, "order": None},
            "竞品B": {"mentioned": False, "count": 0, "order": None},
        })
        s = "neutral"
        if mentioned:
            if i < pos:
                s = "positive"
            elif i < pos + neu:
                s = "neutral"
            else:
                s = "negative"
        sents.append({"目标公司": s})
    return parsed, sents


def test_mention_rate_and_category():
    parsed, sents = _samples(target_mentioned=8, total=10, pos=6, neu=2)
    scores = compute_brand_scores(parsed, sents, BRANDS, "目标公司", WEIGHTS)
    target = next(s for s in scores if s.is_target)
    assert target.mention_rate == 80.0
    # posisi selalu 1 dari 1 brand disebut -> 100; sentimen (6+2*0.5)/10=70
    assert target.position_score == 100.0
    assert target.sentiment_score == 70.0
    assert target.composite == 80 * 0.4 + 100 * 0.3 + 70 * 0.3
    assert category_of(target.composite) == "良好"


def test_weights_change_result():
    parsed, sents = _samples()
    w = {"mention": 100, "position": 0, "sentiment": 0}
    scores = compute_brand_scores(parsed, sents, BRANDS, "目标公司", w)
    target = next(s for s in scores if s.is_target)
    assert target.composite == 80.0


def test_category_thresholds():
    assert category_of(80) == "良好"
    assert category_of(79.9) == "一般"
    assert category_of(60) == "一般"
    assert category_of(59.9) == "较差"
    assert category_of(0) == "较差"


def test_ranking_descending():
    parsed = [{
        "目标公司": {"mentioned": True, "count": 1, "order": 1},
        "竞品A": {"mentioned": True, "count": 1, "order": 2},
        "竞品B": {"mentioned": False, "count": 0, "order": None},
    }]
    sents = [{"目标公司": "positive", "竞品A": "neutral"}]
    scores = compute_brand_scores(parsed * 10, sents * 10, BRANDS, "目标公司", WEIGHTS)
    ranks = rank_scores(scores)
    assert ranks["目标公司"] == 1
    assert ranks["竞品A"] == 2
    assert ranks["竞品B"] == 3
