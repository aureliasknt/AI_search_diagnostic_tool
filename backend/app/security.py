"""Keamanan: hash password (pbkdf2 stdlib), JWT, enkripsi nomor HP (Fernet),
masking tampilan, dan generator kode laporan."""
import base64
import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from cryptography.fernet import Fernet

from . import config

_pbkdf2_iter = 120_000


# ---------- password ----------
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _pbkdf2_iter)
    return f"pbkdf2${_pbkdf2_iter}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt_hex, hash_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


# ---------- JWT ----------
def create_token(sub: str, role: str, hours: int = config.TOKEN_TTL_HOURS) -> str:
    payload = {
        "sub": sub,
        "role": role,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=hours),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM])


def create_unlock_token(share_code: str, phone_hash: str, days: int = config.UNLOCK_TTL_DAYS) -> str:
    payload = {
        "typ": "unlock",
        "code": share_code,
        "ph": phone_hash,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=days),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_unlock_token(token: str) -> dict:
    payload = decode_token(token)
    if payload.get("typ") != "unlock":
        raise jwt.InvalidTokenError("bukan token unlock")
    return payload


# ---------- enkripsi nomor HP ----------
def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(config.SECRET_KEY.encode()).digest())
    return Fernet(key)


def encrypt_phone(phone: str) -> str:
    return _fernet().encrypt(phone.encode()).decode()


def decrypt_phone(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()


def hash_phone(phone: str) -> str:
    return hashlib.sha256(f"{config.SECRET_KEY}:{phone}".encode()).hexdigest()


def mask_phone(phone: str) -> str:
    """138****5678"""
    if len(phone) >= 7:
        return phone[:3] + "****" + phone[-4:]
    return phone[0] + "****"


CN_MOBILE_RE = re.compile(r"^1[3-9]\d{9}$")


def valid_cn_mobile(phone: str) -> bool:
    return bool(CN_MOBILE_RE.match(phone or ""))


# ---------- kode laporan (anti-enumerasi) ----------
def new_share_code(length: int = 12) -> str:
    return secrets.token_urlsafe(length)[:length]


def new_sms_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_sms_code(code: str) -> str:
    return hashlib.sha256(f"{config.SECRET_KEY}:{code}".encode()).hexdigest()
