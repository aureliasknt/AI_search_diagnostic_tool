"""AI推测行业: tebak industri/produk/keyword dari nama perusahaan (PRD Bab 4).

Mode nyata: satu panggilan Doubao dengan prompt JSON. Mode mock (tanpa API key):
heuristik berbasis kata kunci industri dari nama perusahaan — cukup untuk demo
end-to-end, pengguna tetap bisa edit hasilnya secara manual di H5.
"""
import json
import random
import re

from .. import config as appcfg
from .doubao import RealDoubaoProvider

_PROMPT = (
    "你是一家GEO营销机构的行业研究助手。根据中国企业名称「{company}」，"
    "推测该企业所属行业、主营产品，以及终端客户在AI搜索时最可能使用的关键词，"
    "并给出2-3家同地区或同行业的竞品企业名称。"
    "严格只返回JSON（不要多余文字），格式："
    '{{"industry":"行业名称","products":"主营产品简述",'
    '"keywords":["3-5个客户搜索关键词"],"competitors":["2-3个竞品企业全称"]}}'
)

# ---------------- mock ----------------
_INDUSTRY_RULES = [
    (("污水处理", "净水", "水处理"), "污水处理设备制造", "污水处理设备",
     ["合肥污水处理设备厂家", "污水处理设备哪家好", "污水处理设备十大品牌"]),
    (("环保",), "环保设备与服务", "环保处理设备",
     ["环保设备厂家", "环保设备哪家好", "环保设备品牌排名"]),
    (("食品", "餐饮"), "食品加工", "食品加工与供应",
     ["食品代工厂家", "食品加工哪家好", "食品厂排名"]),
    (("机械", "机电", "智能装备"), "机械制造", "机械设备",
     ["机械设备厂家", "机械设备哪家好", "机械设备品牌"]),
    (("建材", "门窗", "装饰"), "建材制造", "建筑装饰材料",
     ["建材厂家", "建材哪家好", "建材品牌排名"]),
    (("物流", "运输", "供应链"), "物流运输", "物流运输服务",
     ["物流公司哪家好", "物流运输价格", "物流企业排名"]),
    (("教育", "培训"), "教育培训", "教育培训服务",
     ["培训机构哪家好", "教育培训排名", "培训班推荐"]),
    (("新能源", "光伏", "储能"), "新能源", "新能源设备与解决方案",
     ["新能源厂家", "光伏储能哪家好", "新能源企业排名"]),
    (("电子", "科技", "智能"), "电子设备制造", "智能电子设备",
     ["电子设备厂家", "智能设备哪家好", "电子设备品牌"]),
]

_FAKE_COMPETITORS = [
    "安徽中科{name}设备有限公司", "合肥蓝天{name}科技有限公司",
    "安徽恒瑞{name}设备有限公司", "合肥金鼎{name}科技有限公司",
    "安徽宏图{name}有限公司",
]


def _mock_guess(company: str) -> dict:
    rng = random.Random(company)
    short = re.sub(r"(有限责任公司|股份有限公司|有限公司|公司)$", "", company)
    short = short[-4:] if len(short) >= 4 else short

    industry, products, kw_core = "通用制造与技术服务", f"{short}主营产品与服务", short
    keywords = [f"{short}怎么样", f"{short}哪家好", f"{short}价格"]
    for keys, ind, prod, kws in _INDUSTRY_RULES:
        if any(k in company for k in keys):
            industry, products = ind, prod
            keywords = kws[:]
            break

    n_comp = rng.randint(2, 3)
    competitors = rng.sample(_FAKE_COMPETITORS, n_comp)
    competitors = [c.format(name=kw_core) for c in competitors]
    return {"industry": industry, "products": products,
            "keywords": keywords, "competitors": competitors}


def _parse_json_loose(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or "industry" not in data:
        return None
    return data


async def guess_for_company(company: str, platform_cfg: dict) -> dict:
    """Kembalikan {"industry", "products", "keywords", "competitors"}."""
    if platform_cfg.get("provider") == "doubao" and platform_cfg.get("api_key"):
        provider = RealDoubaoProvider(
            api_key=platform_cfg["api_key"],
            base_url=platform_cfg.get("base_url") or appcfg.DOUBAO_BASE_URL,
            model=platform_cfg.get("model") or appcfg.DOUBAO_MODEL,
        )
        ans = await provider.ask(_PROMPT.format(company=company), temperature=0.3)
        data = _parse_json_loose(ans.text)
        if data:
            return {
                "industry": str(data.get("industry") or "").strip()[:100],
                "products": str(data.get("products") or "").strip()[:255],
                "keywords": [str(k).strip()[:50] for k in (data.get("keywords") or []) if str(k).strip()][:8],
                "competitors": [str(c).strip()[:100] for c in (data.get("competitors") or []) if str(c).strip()][:5],
            }
    return _mock_guess(company)
