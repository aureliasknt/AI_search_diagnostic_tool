"""Endpoint publik H5 (tanpa login): AI推测行业 + mulai diagnosis mandiri.

Anti-abuse sederhana: rate limit per IP di memori + honeypot field `website`.
Diagnosa publik dibuat atas user placeholder `h5_guest` dan ditandai
`sample_target` (jumlah pertanyaan tepat, default 100).
"""
import time
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config_store import effective_platform, get_config
from ..db import get_db
from ..engine.guess import guess_for_company
from ..engine.worker import get_worker
from ..models import Diagnosis, User
from ..security import new_share_code

router = APIRouter(tags=["public"])

RATE = {"guess": (30, 3600), "start": (15, 3600)}  # (maks, jendela detik)
_hits: dict[str, list[float]] = {}


def _limit(key: str, request: Request):
    max_n, window = RATE[key]
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    arr = [t for t in _hits.get(f"{key}:{ip}", []) if now - t < window]
    if len(arr) >= max_n:
        raise HTTPException(429, "操作过于频繁，请稍后再试")
    arr.append(now)
    _hits[f"{key}:{ip}"] = arr


class GuessIn(BaseModel):
    company_name: str = Field(min_length=2, max_length=100)


class StartIn(BaseModel):
    company_name: str = Field(min_length=2, max_length=100)
    industry: str = Field(default="", max_length=100)
    products: str = Field(default="", max_length=255)
    keywords: list[str] = Field(min_length=1, max_length=10)
    competitors: list[str] = Field(default=[], max_length=5)
    website: str = ""  # honeypot: harus kosong


@router.post("/diagnose/guess")
async def guess(body: GuessIn, request: Request, db: Session = Depends(get_db)):
    _limit("guess", request)
    platform = effective_platform(db)
    return await guess_for_company(body.company_name.strip(), platform)


@router.post("/diagnose")
def start_diagnosis(body: StartIn, request: Request, db: Session = Depends(get_db)):
    _limit("start", request)
    if body.website:
        raise HTTPException(400, "Invalid request")
    keywords = [k.strip() for k in body.keywords if k.strip()]
    competitors = [c.strip() for c in body.competitors if c.strip()]
    if not keywords:
        raise HTTPException(422, "至少需要一个搜索关键词")

    guest = db.query(User).filter_by(username="h5_guest").first()
    if guest is None:
        raise HTTPException(500, "Server belum siap")

    expiry = int(get_config(db, "report").get("expiry_days", 90))
    diag = Diagnosis(
        company_name=body.company_name.strip(),
        keywords=keywords,
        competitors=competitors,
        industry=body.industry.strip(),
        products=body.products.strip(),
        share_code=new_share_code(),
        expires_at=datetime.now() + timedelta(days=expiry),
        created_by=guest.id,
        sample_target=100,
    )
    db.add(diag)
    db.commit()
    get_worker().submit(diag.id)
    return {"code": diag.share_code, "status": diag.status, "total": diag.sample_target}
