"""Router panel admin: manajemen diagnosa (PRD 7.1)."""
import segno
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .. import config as appcfg
from ..db import get_db
from ..deps import get_current_user
from ..engine.worker import get_worker
from ..models import (BrandMetric, Diagnosis, GeoProfile, Problem, Sample,
                      SentimentItem, User)
from ..security import new_share_code

router = APIRouter(prefix="/diagnoses", tags=["diagnoses"], dependencies=[Depends(get_current_user)])

STATUS_LABEL = {"queued": "排队中", "running": "进行中", "done": "已完成", "failed": "失败"}


class GeoProfileIn(BaseModel):
    company_name: str
    stage: str = ""
    channels: str = ""
    content_eco: str = ""
    authority: str = ""
    visibility: str = ""
    acquisition_model: str = ""


class DiagnosisIn(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    keywords: list[str] = Field(min_length=1)
    competitors: list[str] = []
    geo_profiles: list[GeoProfileIn] = []


def _row(d: Diagnosis) -> dict:
    return {
        "id": d.id, "company_name": d.company_name, "keywords": d.keywords,
        "competitors": d.competitors, "status": d.status, "status_label": STATUS_LABEL.get(d.status, d.status),
        "error": d.error, "progress": d.progress, "share_code": d.share_code,
        "total_samples": d.total_samples, "score": d.score, "category": d.category,
        "created_at": d.created_at.isoformat(timespec="seconds") if d.created_at else None,
        "finished_at": d.finished_at.isoformat(timespec="seconds") if d.finished_at else None,
    }


@router.post("")
def create_diagnosis(body: DiagnosisIn, db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    from datetime import datetime, timedelta

    from ..config_store import get_config
    expiry = int(get_config(db, "report").get("expiry_days", 90))
    diag = Diagnosis(
        company_name=body.company_name.strip(),
        keywords=[k.strip() for k in body.keywords if k.strip()],
        competitors=[c.strip() for c in body.competitors if c.strip()],
        share_code=new_share_code(),
        expires_at=datetime.now() + timedelta(days=expiry),
        created_by=user.id,
    )
    db.add(diag)
    db.flush()
    for i, p in enumerate(body.geo_profiles):
        db.add(GeoProfile(diagnosis_id=diag.id, sort=i, **p.model_dump()))
    db.commit()
    get_worker().submit(diag.id)
    return _row(diag)


@router.get("")
def list_diagnoses(status: str | None = None, q: str | None = None,
                   page: int = 1, page_size: int = 20,
                   db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Diagnosis)
    if user.role != "admin":
        query = query.filter(Diagnosis.created_by == user.id)
    if status:
        query = query.filter(Diagnosis.status == status)
    if q:
        query = query.filter(Diagnosis.company_name.contains(q))
    total = query.count()
    rows = (query.order_by(Diagnosis.id.desc())
            .offset((page - 1) * page_size).limit(page_size).all())
    return {"total": total, "items": [_row(d) for d in rows]}


@router.get("/{diag_id}")
def diagnosis_detail(diag_id: int, db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    d = db.get(Diagnosis, diag_id)
    if d is None:
        raise HTTPException(404, "Diagnosa tidak ditemukan")
    if user.role != "admin" and d.created_by != user.id:
        raise HTTPException(403, "Bukan pemilik diagnosa")
    metrics = [{"brand_name": m.brand_name, "is_target": m.is_target, "mention_rate": m.mention_rate,
                "mention_count": m.mention_count, "position_score": m.position_score,
                "pos_count": m.pos_count, "neu_count": m.neu_count, "neg_count": m.neg_count,
                "sentiment_score": m.sentiment_score, "composite": m.composite, "rank": m.rank}
               for m in db.query(BrandMetric).filter_by(diagnosis_id=d.id).order_by(BrandMetric.rank)]
    samples = [{"id": s.id, "keyword": s.keyword, "question": s.question, "round_no": s.round_no,
                "answer_text": s.answer_text, "parse_json": s.parse_json, "sentiment_json": s.sentiment_json}
               for s in db.query(Sample).filter_by(diagnosis_id=d.id)]
    geo = [{"id": g.id, "company_name": g.company_name, "stage": g.stage, "channels": g.channels,
            "content_eco": g.content_eco, "authority": g.authority, "visibility": g.visibility,
            "acquisition_model": g.acquisition_model} for g in d.geo_profiles]
    problems = [{"id": p.id, "title": p.title, "problem_text": p.problem_text,
                 "suggestion_text": p.suggestion_text} for p in d.problems]
    return {**_row(d), "metrics": metrics, "samples": samples, "geo_profiles": geo,
            "problems": problems, "conclusion": d.conclusion}


@router.post("/{diag_id}/retry")
def retry_diagnosis(diag_id: int, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    d = db.get(Diagnosis, diag_id)
    if d is None:
        raise HTTPException(404, "Diagnosa tidak ditemukan")
    if user.role != "admin" and d.created_by != user.id:
        raise HTTPException(403, "Bukan pemilik diagnosa")
    if d.status != "failed":
        raise HTTPException(400, "Hanya diagnosa gagal yang bisa dicoba ulang")
    d.status, d.error, d.progress = "queued", None, 0
    db.commit()
    get_worker().submit(d.id)
    return _row(d)


@router.put("/{diag_id}/geo")
def upsert_geo_profiles(diag_id: int, body: list[GeoProfileIn],
                        db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    d = db.get(Diagnosis, diag_id)
    if d is None:
        raise HTTPException(404, "Diagnosa tidak ditemukan")
    if user.role != "admin" and d.created_by != user.id:
        raise HTTPException(403, "Bukan pemilik diagnosa")
    for g in d.geo_profiles:
        db.delete(g)
    db.flush()
    for i, p in enumerate(body):
        db.add(GeoProfile(diagnosis_id=d.id, sort=i, **p.model_dump()))
    db.commit()
    return {"ok": True, "count": len(body)}


@router.get("/{diag_id}/share")
def share_link(diag_id: int, db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    d = db.get(Diagnosis, diag_id)
    if d is None:
        raise HTTPException(404, "Diagnosa tidak ditemukan")
    if user.role != "admin" and d.created_by != user.id:
        raise HTTPException(403, "Bukan pemilik diagnosa")
    url = f"{appcfg.H5_BASE_URL}/r/{d.share_code}"
    qr = segno.make(url, error="m")
    return {"url": url, "qr_svg": qr.svg_inline(border=2)}
