"""Manajemen prospek (PRD 6.2): daftar ter-mask, status tindak lanjut, ekspor Excel."""
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import Diagnosis, Prospect, User

router = APIRouter(prefix="/prospects", tags=["prospects"],
                   dependencies=[Depends(get_current_user)])

STATUS_OPTIONS = ["new", "contacted", "scheduled", "deal", "invalid"]
STATUS_LABEL = {"new": "新线索", "contacted": "已联系", "scheduled": "已约见",
                "deal": "已成交", "invalid": "无效"}


class StatusIn(BaseModel):
    status: str


def _row(p: Prospect, diag: Diagnosis | None) -> dict:
    return {
        "id": p.id, "phone_mask": p.phone_mask, "name": p.name, "company": p.company,
        "diagnosis_id": p.diagnosis_id,
        "report_company": diag.company_name if diag else "",
        "report_keywords": diag.keywords if diag else [],
        "verified_at": p.verified_at.isoformat(timespec="seconds") if p.verified_at else None,
        "status": p.status, "status_label": STATUS_LABEL.get(p.status, p.status),
        "exported_pdf": p.exported_pdf,
        "created_at": p.created_at.isoformat(timespec="seconds") if p.created_at else None,
    }


def _scoped_query(db: Session, user: User):
    query = db.query(Prospect, Diagnosis).join(Diagnosis, Prospect.diagnosis_id == Diagnosis.id)
    if user.role != "admin":
        query = query.filter(Diagnosis.created_by == user.id)
    return query


@router.get("")
def list_prospects(status: str | None = None, diagnosis_id: int | None = None,
                   q: str | None = None, page: int = 1, page_size: int = 20,
                   db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = _scoped_query(db, user)
    if status:
        query = query.filter(Prospect.status == status)
    if diagnosis_id:
        query = query.filter(Prospect.diagnosis_id == diagnosis_id)
    if q:
        query = query.filter((Prospect.name.contains(q)) | (Prospect.company.contains(q))
                             | (Prospect.phone_mask.contains(q)))
    total = query.count()
    rows = (query.order_by(Prospect.id.desc())
            .offset((page - 1) * page_size).limit(page_size).all())
    return {"total": total, "items": [_row(p, d) for p, d in rows],
            "status_options": [{"value": k, "label": v} for k, v in STATUS_LABEL.items()]}


@router.patch("/{pid}")
def update_status(pid: int, body: StatusIn, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    if body.status not in STATUS_OPTIONS:
        raise HTTPException(422, "Status tidak dikenal")
    p = db.get(Prospect, pid)
    if p is None:
        raise HTTPException(404, "Prospek tidak ditemukan")
    diag = db.get(Diagnosis, p.diagnosis_id)
    if user.role != "admin" and diag.created_by != user.id:
        raise HTTPException(403, "Bukan pemilik prospek")
    p.status = body.status
    db.commit()
    return _row(p, diag)


@router.get("/export")
def export_excel(status: str | None = None, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    query = _scoped_query(db, user)
    if status:
        query = query.filter(Prospect.status == status)
    rows = query.order_by(Prospect.id.desc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "线索"
    ws.append(["手机号", "姓名", "公司", "来源报告(企业)", "来源关键词", "填写时间",
               "验证状态", "是否导出PDF", "跟进状态"])
    for p, d in rows:
        ws.append([p.phone_mask, p.name, p.company, d.company_name,
                   "、".join(d.keywords or []),
                   p.verified_at.strftime("%Y-%m-%d %H:%M") if p.verified_at else "",
                   "已验证", "是" if p.exported_pdf else "否", STATUS_LABEL.get(p.status, p.status)])
    for col, width in zip("ABCDEFGHI", [16, 12, 24, 28, 32, 18, 10, 12, 10]):
        ws.column_dimensions[col].width = width

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return StreamingResponse(
        buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=prospects_{stamp}.xlsx"})
