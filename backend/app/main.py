import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config as appcfg
from .config_store import ensure_defaults
from .db import SessionLocal, init_db
from .engine.worker import requeue_interrupted

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="AI Search Diagnostic Tool", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=appcfg.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    _migrate()
    _ensure_guest_user()
    db = SessionLocal()
    try:
        ensure_defaults(db)
    finally:
        db.close()
    requeue_interrupted()


@app.get("/api/health")
def health():
    return {"ok": True}


from sqlalchemy import text

from .admincfg.router import router as config_router  # noqa: E402
from .auth.router import router as auth_router  # noqa: E402
from .diagnoses.router import router as diagnoses_router  # noqa: E402
from .prospects.router import router as prospects_router  # noqa: E402
from .public.router import router as public_router  # noqa: E402
from .reports.router import router as reports_router  # noqa: E402

app.include_router(auth_router, prefix="/api")
app.include_router(diagnoses_router, prefix="/api")
app.include_router(prospects_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(config_router, prefix="/api")
app.include_router(public_router, prefix="/api")


def _migrate():
    """Migrasi ringan SQLite: tambah kolom baru bila belum ada."""
    db = SessionLocal()
    try:
        for stmt in (
            "ALTER TABLE diagnoses ADD COLUMN sample_target INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE diagnoses ADD COLUMN industry VARCHAR(100) NOT NULL DEFAULT ''",
            "ALTER TABLE diagnoses ADD COLUMN products VARCHAR(255) NOT NULL DEFAULT ''",
        ):
            try:
                db.execute(text(stmt))
                db.commit()
            except Exception:
                db.rollback()  # kolom sudah ada
    finally:
        db.close()


def _ensure_guest_user():
    """User placeholder untuk diagnosa yang dibuat dari H5 publik."""
    import secrets

    from .models import User
    from .security import hash_password

    db = SessionLocal()
    try:
        if db.query(User).filter_by(username="h5_guest").first() is None:
            db.add(User(username="h5_guest",
                        password_hash=hash_password(secrets.token_urlsafe(24)),
                        role="sales"))
            db.commit()
    finally:
        db.close()
