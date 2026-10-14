"""Seed data awal: user admin/sales + 1 diagnosa contoh (mock provider).

Jalankan dari folder backend:
    python -m scripts.seed
"""
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.config_store import ensure_defaults
from app.db import SessionLocal, init_db
from app.engine.worker import run_diagnosis_sync
from app.models import Diagnosis, User
from app.security import hash_password, new_share_code

ADMIN = {"username": "admin", "password": "admin123", "role": "admin"}
SALES = {"username": "sales01", "password": "sales123", "role": "sales"}


def ensure_user(db, username: str, password: str, role: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        user = User(username=username, password_hash=hash_password(password), role=role)
        db.add(user)
        db.commit()
    return user


def main():
    init_db()
    db = SessionLocal()
    try:
        ensure_defaults(db)
        admin = ensure_user(db, **ADMIN)
        ensure_user(db, **SALES)

        if db.query(Diagnosis).count() == 0:
            diag = Diagnosis(
                company_name="安徽绿清水处理设备有限公司",
                keywords=["合肥污水处理设备厂家"],
                competitors=["安徽蓝天环保科技有限公司", "合肥华净水务装备有限公司"],
                share_code=new_share_code(),
                created_by=admin.id,
            )
            db.add(diag)
            db.commit()
            print(f"Membuat diagnosa contoh id={diag.id} code={diag.share_code} ...")
            run_diagnosis_sync(diag.id)  # mock provider: selesai dalam hitungan detik
            db.refresh(diag)
            print(f"Selesai. Status={diag.status} skor={diag.score} ({diag.category})")
        else:
            print("Diagnosa sudah ada — skip.")

        print("\nAkun login panel admin:")
        print(f"  admin   / {ADMIN['password']}")
        print(f"  sales01 / {SALES['password']}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
