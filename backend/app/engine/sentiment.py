"""Klasifikasi sentimen deskripsi brand di jawaban AI (PRD 4.2).

Implementasi nyata = panggilan kedua ke LLM dengan output JSON terstruktur;
mock = heuristik frasa kunci (untuk dev tanpa API key)."""
import json
import re

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

_PROMPT = (
    "请判断以下AI回答中，关于品牌「{brand}」的描述情感倾向。"
    "只输出JSON：{{\"sentiment\": \"positive\"}}，取值 positive / neutral / negative。\n\n"
    "回答内容：\n{text}"
)

_POS_WORDS = ["口碑不错", "实力强", "技术领先", "行业知名", "性价比高", "服务专业", "案例丰富",
              "值得推荐", "优质", "推荐", "好评", "领先"]
_NEG_WORDS = ["投诉", "差评", "质量", "纠纷", "不推荐", "口碑一般", "性价比偏低", "周期较长", "谨慎"]


class BaseSentimentAnalyzer:
    async def classify(self, brand: str, answer_text: str) -> str:
        raise NotImplementedError


class LLSentimentAnalyzer(BaseSentimentAnalyzer):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5), reraise=True)
    async def classify(self, brand: str, answer_text: str) -> str:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": _PROMPT.format(brand=brand, text=answer_text)}],
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
            data = resp.json()
        raw = data["choices"][0]["message"]["content"]
        val = json.loads(raw).get("sentiment", "neutral")
        return val if val in ("positive", "neutral", "negative") else "neutral"


class MockSentimentAnalyzer(BaseSentimentAnalyzer):
    async def classify(self, brand: str, answer_text: str) -> str:
        text = answer_text or ""
        pos = sum(1 for w in _POS_WORDS if w in text)
        neg = sum(1 for w in _NEG_WORDS if w in text)
        # batasi pada kalimat yang menyebut brand bila memungkinkan
        if brand:
            window = _window_around(text, brand)
            if window:
                pos = sum(1 for w in _POS_WORDS if w in window)
                neg = sum(1 for w in _NEG_WORDS if w in window)
        if neg > pos:
            return "negative"
        if pos > 0:
            return "positive"
        return "neutral"


def _window_around(text: str, brand: str, span: int = 60) -> str:
    idx = text.find(brand)
    if idx < 0:
        for alias in [brand]:
            idx = text.find(alias)
            if idx >= 0:
                break
    if idx < 0:
        return ""
    return text[max(0, idx - span): idx + span]


def build_analyzer(platform_cfg: dict) -> BaseSentimentAnalyzer:
    if platform_cfg.get("provider") == "doubao" and platform_cfg.get("api_key"):
        return LLSentimentAnalyzer(
            api_key=platform_cfg["api_key"],
            base_url=platform_cfg.get("base_url", ""),
            model=platform_cfg.get("model", ""),
        )
    return MockSentimentAnalyzer()
