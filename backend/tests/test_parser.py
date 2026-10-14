"""Unit test parser: exact match, fuzzy alias, posisi, jumlah."""
from app.engine.parser import parse_answer

BRANDS = ["安徽绿清水处理设备有限公司", "蓝天环保", "华净水务"]


def test_exact_mention_and_position():
    text = ("市场上比较知名的有：1. 蓝天环保，实力强；"
            "2. 安徽绿清水处理设备有限公司，口碑不错。")
    parsed = parse_answer(text, BRANDS)
    assert parsed["蓝天环保"]["mentioned"] is True
    assert parsed["蓝天环保"]["order"] == 1
    assert parsed["安徽绿清水处理设备有限公司"]["order"] == 2


def test_fuzzy_alias_match():
    alias_map = {"蓝天环保": ["蓝天环保科技"]}
    text = "安徽蓝天环保科技有限公司也是常见选择之一。"
    parsed = parse_answer(text, BRANDS, alias_map)
    assert parsed["蓝天环保"]["mentioned"] is True
    assert parsed["蓝天环保"]["count"] == 1


def test_short_alias_substring():
    alias_map = {"蓝天环保": ["蓝天"]}
    text = "蓝天和绿清都做得不错。"
    parsed = parse_answer(text, BRANDS, alias_map)
    assert parsed["蓝天环保"]["mentioned"] is True
    assert parsed["安徽绿清水处理设备有限公司"]["mentioned"] is False


def test_mention_count_and_absence():
    text = "蓝天环保口碑不错，蓝天环保案例也多。华净水务中规中矩。"
    parsed = parse_answer(text, BRANDS)
    assert parsed["蓝天环保"]["count"] == 2
    assert parsed["安徽绿清水处理设备有限公司"]["mentioned"] is False


def test_punctuation_and_case_normalization():
    text = "蓝 天 环 保（合肥）——实力强。"
    parsed = parse_answer(text, BRANDS)
    assert parsed["蓝天环保"]["mentioned"] is True
