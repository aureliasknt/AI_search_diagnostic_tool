"""Konfigurasi aplikasi dari environment variables (.env tidak otomatis dimuat;
gunakan env shell atau file .env dengan python-dotenv jika perlu)."""
import os
from pathlib import Path


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = _env("SECRET_KEY", "dev-insecure-change-me")
if SECRET_KEY.startswith("dev-"):
    import warnings

    warnings.warn("SECRET_KEY masih default dev — ganti di production!", stacklevel=1)

DATABASE_URL = _env("DATABASE_URL", f"sqlite:///{BASE_DIR / 'aidiag.db'}")
WORKER_BACKEND = _env("WORKER_BACKEND", "local")

DOUBAO_API_KEY = _env("DOUBAO_API_KEY")
DOUBAO_BASE_URL = _env("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
DOUBAO_MODEL = _env("DOUBAO_MODEL", "doubao-seed-1-6-250615")

SMS_PROVIDER = _env("SMS_PROVIDER", "mock")

H5_BASE_URL = _env("H5_BASE_URL", "http://localhost:5173").rstrip("/")
CORS_ORIGINS = [o.strip() for o in _env(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:5174").split(",") if o.strip()]

JWT_ALGORITHM = "HS256"
TOKEN_TTL_HOURS = 12          # token login panel admin
UNLOCK_TTL_DAYS = 30          # token buka kunci laporan H5
