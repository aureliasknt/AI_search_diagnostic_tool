"""Provider LLM Doubao (Volcano Ark) — interface + implementasi nyata + mock.

Mode mock menghasilkan jawaban China sintetis yang menyebut subset brand
(target + kompetitor) dengan urutan/sentimen acak namun reproducible (seed),
sehingga seluruh pipeline parsing & skoring dapat diuji end-to-end tanpa API key.
"""
import random
import re
from dataclasses import dataclass, field

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .. import config as appcfg


@dataclass
class DoubaoAnswer:
    text: str
    references: list[str] = field(default_factory=list)


class BaseDoubaoProvider:
    async def ask(self, question: str, temperature: float) -> DoubaoAnswer:
        raise NotImplementedError


class RealDoubaoProvider(BaseDoubaoProvider):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
    async def ask(self, question: str, temperature: float) -> DoubaoAnswer:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": question}],
                    "temperature": temperature,
                },
            )
            resp.raise_for_status()
            data = resp.json()
        text = data["choices"][0]["message"]["content"]
        refs = re.findall(r"https?://[^\s\)\]\"'，。；]+", text)
        return DoubaoAnswer(text=text, references=refs)


# ---------- Mock provider ----------
_POS_ADJ = ["口碑不错", "实力强", "技术领先", "行业知名", "性价比高", "服务专业", "案例丰富"]
_NEG_ADJ = ["时有投诉", "口碑一般", "性价比偏低", "交付周期较长"]
_NEU_ADJ = ["中规中矩", "有一定市场基础", "规模中等"]
_OPENERS = [
    "关于这个问题，结合行业公开信息可以了解到：",
    "根据市场公开资料整理，供参考：",
    "这个领域可以重点关注以下几家企业：",
    "从行业反馈来看，常见的选择有：",
]
_LINK_POOL = [
    "https://example.com/news/a1.html",
    "https://example.com/industry/b2.html",
    "https://zhuanlan.example.com/c3",
    "https://news.example.com/d4.html",
]


class MockDoubaoProvider(BaseDoubaoProvider):
    """Jawaban sintetis. brand_recipes: {brand: {"p_mention": float, "p_pos": float}}"""

    def __init__(self, brands: list[str], seed: int, brand_recipes: dict[str, dict] | None = None):
        self.rng = random.Random(seed)
        self.brands = brands
        self.recipes = brand_recipes or {}

    def _recipe(self, brand: str) -> dict:
        return self.recipes.get(brand, {})

    async def ask(self, question: str, temperature: float) -> DoubaoAnswer:
        rng = self.rng
        mentioned = []
        for b in self.brands:
            if rng.random() < self._recipe(b).get("p_mention", 0.5):
                mentioned.append(b)

        lines: list[str] = [rng.choice(_OPENERS)]
        n = len(mentioned)
        for i, brand in enumerate(mentioned):
            pos_p = self._recipe(brand).get("p_pos", 0.6)
            r = rng.random()
            if r < pos_p:
                adj = rng.choice(_POS_ADJ)
            elif r < pos_p + 0.25:
                adj = rng.choice(_NEU_ADJ)
            else:
                adj = rng.choice(_NEG_ADJ)
            prefix = f"{i + 1}. " if n > 1 else ""
            lines.append(f"{prefix}{brand}：{adj}，是不少采购方会考虑的选择。")

        target = self.brands[0] if self.brands else ""
        if target and target in mentioned:
            pos_p = self._recipe(target).get("p_pos", 0.6)
            tone = "总体来看值得推荐。" if rng.random() < pos_p else "整体表现中规中矩，建议多方比较。"
            lines.append(f"其中{target}{rng.choice(_POS_ADJ) if rng.random() < pos_p else rng.choice(_NEU_ADJ)}，{tone}")
        elif target:
            lines.append(f"目前公开信息中关于{target}的介绍相对较少，建议直接联系厂家核实产品参数与案例。")

        refs = [u for u in _LINK_POOL if rng.random() < 0.35]
        if refs:
            lines.append("参考链接：" + "；".join(refs))
        return DoubaoAnswer(text="\n".join(lines), references=refs)


def build_provider(platform_cfg: dict, brands: list[str], seed: int,
                   brand_recipes: dict | None = None) -> BaseDoubaoProvider:
    if platform_cfg.get("provider") == "doubao" and platform_cfg.get("api_key"):
        return RealDoubaoProvider(
            api_key=platform_cfg["api_key"],
            base_url=platform_cfg.get("base_url") or appcfg.DOUBAO_BASE_URL,
            model=platform_cfg.get("model") or appcfg.DOUBAO_MODEL,
        )
    return MockDoubaoProvider(brands=brands, seed=seed, brand_recipes=brand_recipes)
