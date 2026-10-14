"""Akses konfigurasi tersimpan di DB (tabel configs) dengan nilai default."""
import json

from sqlalchemy.orm import Session

from .models import Config

DEFAULTS: dict[str, dict] = {
    "weights": {"mention": 40, "position": 30, "sentiment": 30},
    "question_templates": [
        {"id": 1, "text": "{kw}哪家好"},
        {"id": 2, "text": "推荐一下{kw}"},
        {"id": 3, "text": "{kw}有哪些实力强的"},
        {"id": 4, "text": "{kw}排名靠前的有哪些"},
        {"id": 5, "text": "如何选择靠谱的{kw}"},
    ],
    "aliases": [],  # [{"brand": "讯灵", "aliases": ["讯灵AI"]}]
    "recommendations": [
        {
            "id": 1, "enabled": True, "metric": "mention_rate", "op": "<", "value": 50,
            "title": "品牌在AI搜索中曝光不足",
            "problem": "当客户在本次诊断的关键词下向豆包提问时，品牌被AI回答提及的比例偏低，大量精准获客场景被竞品截流。",
            "suggestion": "由企业市场部整理品牌介绍、产品线核心参数与客户案例，搭建可被AI抓取的官网知识库与问答内容；完成后使用本工具复测品牌提及率指标。",
        },
        {
            "id": 2, "enabled": True, "metric": "position_score", "op": "<", "value": 60,
            "title": "品牌在AI回答中排序靠后",
            "problem": "品牌虽被豆包回答提及，但出现位置靠后，首位推荐位置均被竞品占据，曝光质量明显不足。",
            "suggestion": "由企业内容运营团队围绕核心产品问题制作结构化图文与 FAQ 内容，布局行业垂直平台与自媒体矩阵；完成后复测品牌首位提及位置指标。",
        },
        {
            "id": 3, "enabled": True, "metric": "neg_ratio", "op": ">", "value": 10,
            "title": "品牌存在负面舆情内容",
            "problem": "豆包回答样本中出现了一定比例的负面描述，可能影响潜在客户的采购决策。",
            "suggestion": "由企业公关客服团队溯源负面内容并针对性处理，同时持续发布正向客户案例与权威背书内容；完成后复测负面情感倾向指标。",
        },
        {
            "id": 4, "enabled": True, "metric": "composite", "op": "<", "value": 60,
            "title": "整体GEO布局明显落后于竞品",
            "problem": "与同期诊断的竞品相比，品牌综合得分处于劣势，GEO营销体系尚未形成有效布局。",
            "suggestion": "建议启动系统性GEO优化：补齐官网可抓取知识库、第三方平台内容分发与权威资质建设，优先覆盖诊断关键词对应的高频问题；完成后整组复测对比。",
        },
    ],
    "platform": {
        "provider": "auto",          # auto|mock|doubao (auto = mock bila api_key kosong)
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "doubao-seed-1-6-250615",
        "temperature": 0.5,
        "variants": 3,               # variasi pertanyaan per kata kunci (3-5)
        "rounds": 2,                 # pengulangan per pertanyaan (2-3)
        "api_key": "",               # write-only, ter-mask saat dibaca
    },
    "sms": {
        "provider": "auto",          # auto|mock|aliyun|tencent
        "ttl_seconds": 300,
        "cooldown_seconds": 60,
        "daily_limit_per_phone": 20,
        "sign_name": "",             # diisi saat pendaftaran SMS selesai (PRD Bab 11)
        "template_code": "",
    },
    "report": {
        "expiry_days": 90,
        "conclusion_template": "当客户在AI豆包搜索「{keywords}」相关问题时，贵品牌的AI提及率为{mention_rate}%，综合排名第{rank}。",
    },
}


def get_config(db: Session, key: str) -> dict:
    row = db.get(Config, key)
    if row is None:
        return json.loads(json.dumps(DEFAULTS.get(key, {})))
    merged = json.loads(json.dumps(DEFAULTS.get(key, {})))
    if isinstance(merged, dict) and isinstance(row.value, dict):
        merged.update(row.value)
        return merged
    return row.value


def set_config(db: Session, key: str, value) -> None:
    row = db.get(Config, key)
    if row is None:
        row = Config(key=key, value=value)
        db.add(row)
    else:
        row.value = value
    db.commit()


def ensure_defaults(db: Session) -> None:
    for key, val in DEFAULTS.items():
        if db.get(Config, key) is None:
            db.add(Config(key=key, value=json.loads(json.dumps(val))))
    db.commit()


def effective_platform(db: Session) -> dict:
    cfg = get_config(db, "platform")
    if cfg.get("provider", "auto") == "auto":
        cfg["provider"] = "doubao" if cfg.get("api_key") else "mock"
    return cfg


def effective_sms(db: Session) -> dict:
    cfg = get_config(db, "sms")
    if cfg.get("provider", "auto") == "auto":
        from . import config as appcfg
        cfg["provider"] = appcfg.SMS_PROVIDER or "mock"
    return cfg
