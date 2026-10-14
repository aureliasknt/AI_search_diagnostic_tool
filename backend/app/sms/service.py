"""Layanan SMS verifikasi (PRD 6.1): provider pluggable.

- mock: kode dikembalikan di response dev & log (default dev)
- aliyun / tencent: stub — isi kredensial & template setelah pendaftaran
  (PRD Bab 11 butuh konfirmasi penyedia & tanda tangan SMS)
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config_store import effective_sms
from ..models import SmsCode
from ..security import hash_sms_code, new_sms_code

log = logging.getLogger("sms")


class SmsSendError(Exception):
    pass


class BaseSmsProvider:
    async def send(self, phone: str, code: str, sign_name: str, template_code: str) -> None:
        raise NotImplementedError


class MockSmsProvider(BaseSmsProvider):
    async def send(self, phone: str, code: str, sign_name: str, template_code: str) -> None:
        log.info("[MOCK SMS] -> %s : kode verifikasi %s", phone, code)


class AliyunSmsProvider(BaseSmsProvider):
    async def send(self, phone: str, code: str, sign_name: str, template_code: str) -> None:
        # TODO: integrasi RPC aliyun dysms setelah akun & tanda tangan tersedia (PRD Bab 11)
        raise SmsSendError("Provider Aliyun SMS belum dikonfigurasi — isi sign_name/template & kredensial")


class TencentSmsProvider(BaseSmsProvider):
    async def send(self, phone: str, code: str, sign_name: str, template_code: str) -> None:
        # TODO: integrasi Tencent Cloud SMS setelah akun tersedia (PRD Bab 11)
        raise SmsSendError("Provider Tencent SMS belum dikonfigurasi — isi sign_name/template & kredensial")


def _provider(name: str) -> BaseSmsProvider:
    return {"mock": MockSmsProvider, "aliyun": AliyunSmsProvider,
            "tencent": TencentSmsProvider}.get(name, MockSmsProvider)()


async def send_verification_code(db: Session, diagnosis_id: int, phone: str) -> dict:
    """Kirim kode baru; terapkan cooldown & batas harian. Return {"dev_code"?}."""
    cfg = effective_sms(db)
    now = datetime.now()

    last = (db.execute(select(SmsCode).where(
        SmsCode.diagnosis_id == diagnosis_id, SmsCode.phone_hash == phone)
        .order_by(SmsCode.created_at.desc()).limit(1)).scalars().first())
    if last and (now - last.created_at).total_seconds() < int(cfg.get("cooldown_seconds", 60)):
        wait = int(cfg.get("cooldown_seconds", 60)) - int((now - last.created_at).total_seconds())
        raise SmsSendError(f"Tunggu {wait} detik sebelum kirim ulang kode")

    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    sent_today = db.execute(select(func.count(SmsCode.id)).where(
        SmsCode.diagnosis_id == diagnosis_id, SmsCode.phone_hash == phone,
        SmsCode.created_at >= day_start)).scalar_one()
    if sent_today >= int(cfg.get("daily_limit_per_phone", 20)):
        raise SmsSendError("Batas harian pengiriman kode untuk nomor ini tercapai")

    code = new_sms_code()
    await _provider(cfg.get("provider", "mock")).send(
        phone, code, cfg.get("sign_name", ""), cfg.get("template_code", ""))

    row = SmsCode(
        diagnosis_id=diagnosis_id, phone_hash=phone,
        code_hash=hash_sms_code(code),
        expires_at=now + timedelta(seconds=int(cfg.get("ttl_seconds", 300))),
    )
    db.add(row)
    db.commit()
    out = {"ok": True, "ttl_seconds": int(cfg.get("ttl_seconds", 300))}
    if cfg.get("provider") == "mock":
        out["dev_code"] = code  # hanya mode mock/dev — hapus provider ini di production
    return out


def verify_code(db: Session, diagnosis_id: int, phone_hash: str, code: str) -> bool:
    row = (db.execute(select(SmsCode).where(
        SmsCode.diagnosis_id == diagnosis_id, SmsCode.phone_hash == phone_hash,
        SmsCode.used.is_(False)).order_by(SmsCode.created_at.desc()).limit(1)).scalars().first())
    if row is None:
        return False
    now = datetime.now()
    if now > row.expires_at:
        return False
    if row.attempts >= 5:
        return False
    row.attempts += 1
    ok = row.code_hash == hash_sms_code(code)
    if ok:
        row.used = True
    db.commit()
    return ok
