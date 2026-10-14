"""Helper seed minimal untuk test (tanpa menjalankan engine mock)."""
from .config_store import ensure_defaults
from .db import SessionLocal
from .models import User
from .security import hash_password


def seed_minimal():
    db = SessionLocal()
    try:
        ensure_defaults(db)
        user = db.query(User).filter(User.username == "admin").first()
        if user is None:
            user = User(username="admin", password_hash=hash_password("admin123"), role="admin")
            db.add(user)
            db.commit()
    finally:
        db.close()
