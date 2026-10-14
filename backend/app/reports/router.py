"""Endpoint publik laporan H5 (PRD Bab 5-6): ringkasan, gerbang data kontak
(kode SMS + anti-duplikasi), konten lengkap setelah buka kunci, ekspor PDF."""
import asyncio
import logging
from datetime import datetime
from urllib.parse import quote

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import config as appcfg
from ..db import get_db
from ..models import Diagnosis, Prospect
from ..security import (create_unlock_token, decrypt_phone, decode_unlock_token,
                        encrypt_phone, hash_phone, mask_phone, valid_cn_mobile)
from ..sms.service import SmsSendError, send_verification_code, verify_code

log = logging.getLogger("reports")
router = APIRouter(prefix="/r", tags=["report-public"])


def _get_diag_by_code(db: Session, code: str) -> Diagnosis:
    d = db.query(Diagnosis).filter(Diagnosis.share_code == code).first()
    if d is None:
        raise HTTPException(404, "Laporan tidak ditemukan")
    if d.expires_at and datetime.now() > d.expires_at:
        raise HTTPException(410, "Masa berlaku laporan telah habis")
    return d


def _target_metrics(d: Diagnosis) -> dict:
    m = next((x for x in d.metrics if x.is_target), None)
    if m is None:
        return {}
    total = max(d.total_samples or 1, 1)
    return {
        "mention_rate": m.mention_rate, "mention_count": m.mention_count,
        "position_score": m.position_score, "sentiment_score": m.sentiment_score,
        "pos_count": m.pos_count, "neu_count": m.neu_count, "neg_count": m.neg_count,
        "neg_ratio": round(m.neg_count / total * 100, 2),
    }


def _public_payload(d: Diagnosis) -> dict:
    return {
        "company_name": d.company_name,
        "industry": getattr(d, "industry", "") or "",
        "products": getattr(d, "products", "") or "",
        "keywords": d.keywords,
        "status": d.status,
        "status_label": {"queued": "排队中", "running": "生成中", "done": "已完成", "failed": "生成失败"}.get(d.status, d.status),
        "progress": d.progress,
        "total_samples": d.total_samples,
        "score": d.score,
        "category": d.category,
        "conclusion": d.conclusion,
        "target": _target_metrics(d),
        "locked": True,
        "disclaimer": ("本报告全部指标均来自本次诊断关键词对应的豆包AI回答样本，"
                       "仅反映样本范围内的统计结果，供业务参考使用。"),
    }


class SendCodeIn(BaseModel):
    phone: str


class VerifyIn(BaseModel):
    phone: str
    code: str = ""
    name: str = ""
    company: str = ""
    consent: bool = False


def _extract_token(token: str | None) -> dict:
    if not token:
        raise HTTPException(401, "Laporan terkunci — isi data kontak dulu")
    try:
        return decode_unlock_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Sesi buka kunci habis — verifikasi ulang")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Token buka kunci tidak valid")


@router.get("/{code}")
def report_summary(code: str, db: Session = Depends(get_db)):
    d = _get_diag_by_code(db, code)
    if d.status != "done":
        return {**_public_payload(d), "running": d.status in ("queued", "running")}
    return _public_payload(d)


@router.post("/{code}/send-code")
async def send_code(code: str, body: SendCodeIn, db: Session = Depends(get_db)):
    d = _get_diag_by_code(db, code)
    if d.status != "done":
        raise HTTPException(400, "Laporan belum selesai dibuat")
    if not valid_cn_mobile(body.phone):
        raise HTTPException(422, "Format nomor HP China tidak valid (contoh: 13800138000)")
    try:
        return await send_verification_code(db, d.id, hash_phone(body.phone))
    except SmsSendError as exc:
        raise HTTPException(429, str(exc))


@router.post("/{code}/verify")
def unlock(code: str, body: VerifyIn, db: Session = Depends(get_db)):
    d = _get_diag_by_code(db, code)
    if not body.consent:
        raise HTTPException(422, "Persetujuan kebijakan privasi wajib dicentang")
    if not valid_cn_mobile(body.phone):
        raise HTTPException(422, "Format nomor HP China tidak valid")
    ph = hash_phone(body.phone)

    # anti-duplikasi: nomor yang sama per laporan hanya diverifikasi sekali
    existing = db.query(Prospect).filter_by(diagnosis_id=d.id, phone_hash=ph).first()
    if existing is None:
        if not body.code:
            raise HTTPException(422, "Kode verifikasi wajib diisi")
        if not verify_code(db, d.id, ph, body.code):
            raise HTTPException(400, "Kode verifikasi salah atau kedaluwarsa")
        db.add(Prospect(
            diagnosis_id=d.id, phone_enc=encrypt_phone(body.phone), phone_hash=ph,
            phone_mask=mask_phone(body.phone), name=body.name.strip(), company=body.company.strip(),
        ))
        db.commit()

    return {"unlock_token": create_unlock_token(d.share_code, ph)}


@router.get("/{code}/full")
def report_full(code: str, token: str | None = Query(default=None),
                db: Session = Depends(get_db)):
    d = _get_diag_by_code(db, code)
    payload = _extract_token(token)
    if payload.get("code") != d.share_code:
        raise HTTPException(401, "Token tidak cocok dengan laporan ini")
    if d.status != "done":
        raise HTTPException(400, "Laporan belum selesai")

    metrics = [{"brand_name": m.brand_name, "is_target": m.is_target, "mention_rate": m.mention_rate,
                "mention_count": m.mention_count, "position_score": m.position_score,
                "pos_count": m.pos_count, "neu_count": m.neu_count, "neg_count": m.neg_count,
                "sentiment_score": m.sentiment_score, "composite": m.composite, "rank": m.rank}
               for m in d.metrics]
    metrics.sort(key=lambda x: x["rank"])
    sentiment_items = [{"id": s.id, "publish_date": s.publish_date, "item_type": s.item_type,
                        "title": s.title, "polarity": s.polarity, "company_name": s.company_name,
                        "summary": s.summary, "source": s.source}
                       for s in d.sentiment_items]
    problems = [{"title": p.title, "problem_text": p.problem_text,
                 "suggestion_text": p.suggestion_text} for p in d.problems]
    geo = [{"company_name": g.company_name, "stage": g.stage, "channels": g.channels,
            "content_eco": g.content_eco, "authority": g.authority, "visibility": g.visibility,
            "acquisition_model": g.acquisition_model} for g in d.geo_profiles]
    samples = [{"question": s.question, "mentioned": [b for b, v in (s.parse_json or {}).items() if v.get("mentioned")],
                "sentiment": s.sentiment_json} for s in d.samples]
    # daftar Q&A lengkap untuk tab 查询详情 (pertanyaan + jawaban + highlight brand)
    queries = [{"keyword": s.keyword, "question": s.question, "round": s.round_no,
                "answer": s.answer_text,
                "mentioned": [b for b, v in (s.parse_json or {}).items() if v.get("mentioned")]}
               for s in d.samples]
    queries.sort(key=lambda x: (x["keyword"], x["round"], x["question"]))
    from ..config_store import get_config as _gc
    alias_rows = _gc(db, "aliases")
    alias_map = {r["brand"]: r.get("aliases", []) for r in alias_rows if r.get("brand")}
    return {**_public_payload(d), "locked": False, "metrics": metrics,
            "sentiment_items": sentiment_items, "problems": problems,
            "geo_profiles": geo, "samples": samples,
            "queries": queries, "alias_map": alias_map}


_browser = None


async def _get_browser():
    global _browser
    if _browser is None:
        from playwright.async_api import async_playwright
        _pw = await async_playwright().start()
        _browser = await _pw.chromium.launch()
    return _browser


@router.get("/{code}/pdf")
async def report_pdf(code: str, token: str | None = Query(default=None),
                     db: Session = Depends(get_db)):
    d = _get_diag_by_code(db, code)
    payload = _extract_token(token)
    if payload.get("code") != d.share_code:
        raise HTTPException(401, "Token tidak cocok dengan laporan ini")
    if d.status != "done":
        raise HTTPException(400, "Laporan belum selesai")

    url = f"{appcfg.H5_BASE_URL}/r/{d.share_code}?export=1&token={quote(token)}"
    try:
        browser = await _get_browser()
        page = await browser.new_page(viewport={"width": 750, "height": 1200})
        await page.goto(url, wait_until="load", timeout=60_000)
        await page.wait_for_selector(".foot", timeout=45_000)
        await page.wait_for_timeout(1500)
        pdf_bytes = await page.pdf(format="A4", print_background=True,
                                   margin={"top": "10mm", "bottom": "10mm",
                                           "left": "8mm", "right": "8mm"})
        await page.close()
    except Exception as exc:  # noqa: BLE001
        log.exception("render PDF gagal")
        raise HTTPException(500, f"Gagal membuat PDF: {exc}")

    # tandai prospek pemilik token telah mengekspor PDF
    prospect = db.query(Prospect).filter_by(diagnosis_id=d.id,
                                            phone_hash=payload.get("ph")).first()
    if prospect:
        prospect.exported_pdf = True
        db.commit()

    filename = f"{d.company_name}AI搜索诊断报告.pdf"
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"})
