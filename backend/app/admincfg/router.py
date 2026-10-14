"""Konfigurasi sistem (PRD 7.2) — khusus admin: bobot penilaian, templat
pertanyaan, alias brand, basis data rekomendasi, platform Doubao, laporan."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config_store import DEFAULTS, get_config, set_config
from ..db import get_db
from ..deps import require_admin

router = APIRouter(prefix="/config", tags=["config"], dependencies=[Depends(require_admin)])


def _mask_key(key: str) -> str:
    if not key:
        return ""
    return key[:4] + "****" + key[-4:] if len(key) > 10 else "****"


# ---------- bobot ----------
@router.get("/weights")
def get_weights(db: Session = Depends(get_db)):
    return get_config(db, "weights")


class WeightsIn(BaseModel):
    mention: float = Field(ge=0, le=100)
    position: float = Field(ge=0, le=100)
    sentiment: float = Field(ge=0, le=100)


@router.put("/weights")
def put_weights(body: WeightsIn, db: Session = Depends(get_db)):
    set_config(db, "weights", body.model_dump())
    return body


# ---------- templat / alias / rekomendasi (CRUD generik list) ----------
def _list(db: Session, key: str):
    return {"items": get_config(db, key)}


def _add(db: Session, key: str, item: dict):
    items = get_config(db, key)
    nid = max([i.get("id", 0) for i in items], default=0) + 1
    item["id"] = nid
    items.append(item)
    set_config(db, key, items)
    return item


def _update(db: Session, key: str, item_id: int, patch: dict):
    items = get_config(db, key)
    for it in items:
        if it.get("id") == item_id:
            it.update({k: v for k, v in patch.items() if v is not None or k in it})
            set_config(db, key, items)
            return it
    raise HTTPException(404, "Item tidak ditemukan")


def _delete(db: Session, key: str, item_id: int):
    items = get_config(db, key)
    kept = [i for i in items if i.get("id") != item_id]
    if len(kept) == len(items):
        raise HTTPException(404, "Item tidak ditemukan")
    set_config(db, key, kept)
    return {"ok": True}


class TemplateIn(BaseModel):
    text: str = Field(min_length=1)


@router.get("/templates")
def templates_list(db: Session = Depends(get_db)):
    return _list(db, "question_templates")


@router.post("/templates")
def templates_add(body: TemplateIn, db: Session = Depends(get_db)):
    return _add(db, "question_templates", body.model_dump())


@router.delete("/templates/{item_id}")
def templates_del(item_id: int, db: Session = Depends(get_db)):
    return _delete(db, "question_templates", item_id)


class AliasIn(BaseModel):
    brand: str = Field(min_length=1)
    aliases: list[str] = []


@router.get("/aliases")
def aliases_list(db: Session = Depends(get_db)):
    return _list(db, "aliases")


@router.post("/aliases")
def aliases_add(body: AliasIn, db: Session = Depends(get_db)):
    return _add(db, "aliases", body.model_dump())


@router.put("/aliases/{item_id}")
def aliases_update(item_id: int, body: AliasIn, db: Session = Depends(get_db)):
    return _update(db, "aliases", item_id, body.model_dump())


@router.delete("/aliases/{item_id}")
def aliases_del(item_id: int, db: Session = Depends(get_db)):
    return _delete(db, "aliases", item_id)


class RecommendationIn(BaseModel):
    metric: str = "mention_rate"
    op: str = "<"
    value: float = 50
    title: str = Field(min_length=1)
    problem: str = ""
    suggestion: str = ""
    enabled: bool = True


@router.get("/recommendations")
def rec_list(db: Session = Depends(get_db)):
    return _list(db, "recommendations")


@router.post("/recommendations")
def rec_add(body: RecommendationIn, db: Session = Depends(get_db)):
    return _add(db, "recommendations", body.model_dump())


@router.put("/recommendations/{item_id}")
def rec_update(item_id: int, body: RecommendationIn, db: Session = Depends(get_db)):
    return _update(db, "recommendations", item_id, body.model_dump())


@router.delete("/recommendations/{item_id}")
def rec_del(item_id: int, db: Session = Depends(get_db)):
    return _delete(db, "recommendations", item_id)


# ---------- platform & laporan ----------
@router.get("/platform")
def platform_get(db: Session = Depends(get_db)):
    cfg = get_config(db, "platform")
    cfg["api_key"] = _mask_key(cfg.get("api_key", ""))
    cfg["defaults"] = {k: DEFAULTS["platform"].get(k) for k in ("base_url", "model")}
    return cfg


class PlatformIn(BaseModel):
    provider: str = "auto"
    base_url: str = ""
    model: str = ""
    temperature: float = Field(0.5, ge=0, le=2)
    variants: int = Field(3, ge=3, le=5)
    rounds: int = Field(2, ge=2, le=3)
    api_key: str | None = None


@router.put("/platform")
def platform_put(body: PlatformIn, db: Session = Depends(get_db)):
    cfg = get_config(db, "platform")
    data = body.model_dump()
    if not data.get("api_key") or "****" in data["api_key"]:
        data["api_key"] = cfg.get("api_key", "")  # pertahankan kunci lama
    set_config(db, "platform", data)
    cfg = data.copy()
    cfg["api_key"] = _mask_key(cfg.get("api_key", ""))
    return cfg


@router.get("/report")
def report_get(db: Session = Depends(get_db)):
    return get_config(db, "report")


class ReportCfgIn(BaseModel):
    expiry_days: int = Field(90, ge=1, le=3650)
    conclusion_template: str = Field(min_length=1)


@router.put("/report")
def report_put(body: ReportCfgIn, db: Session = Depends(get_db)):
    set_config(db, "report", body.model_dump())
    return body
