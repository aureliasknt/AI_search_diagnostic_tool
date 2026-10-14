"""Smoke test API: health, login, buat diagnosa (mock engine), alur buka kunci."""
import os
import time

os.environ["DATABASE_URL"] = "sqlite:///./test_smoke.db"
os.environ["SECRET_KEY"] = "test-secret-key"

from fastapi.testclient import TestClient  # noqa: E402

import app.diagnoses.router as diag_router  # noqa: E402
from app.db import Base, engine  # noqa: E402
from app.engine.worker import run_diagnosis_sync  # noqa: E402
from app.main import app  # noqa: E402
from app.scripts_seed_helper import seed_minimal  # noqa: E402


class _SyncWorker:
    """Di TestClient tidak ada loop jangka panjang — jalankan pipeline sinkron."""

    def submit(self, diagnosis_id: int):
        run_diagnosis_sync(diagnosis_id)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_minimal()
    diag_router.get_worker = lambda: _SyncWorker()


client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["ok"]


def test_login_and_full_flow():
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post("/api/diagnoses", headers=headers, json={
        "company_name": "测试目标公司",
        "keywords": ["合肥污水处理设备厂家"],
        "competitors": ["竞品甲", "竞品乙"],
    })
    assert r.status_code == 200, r.text
    diag_id = r.json()["id"]
    code = r.json()["share_code"]

    # tunggu worker selesai (mock provider cepat)
    for _ in range(60):
        r = client.get(f"/api/diagnoses/{diag_id}", headers=headers)
        if r.json()["status"] == "done":
            break
        assert r.json()["status"] != "failed", r.json().get("error")
        time.sleep(0.5)
    assert r.json()["status"] == "done"

    # ringkasan publik (tanpa token) — tidak membocorkan konten terkunci
    r = client.get(f"/api/r/{code}")
    body = r.json()
    assert r.status_code == 200
    assert body["company_name"] == "测试目标公司"
    assert "metrics" not in body and "problems" not in body
    assert body["target"]["mention_rate"] > 0

    # konten lengkap ditolak tanpa unlock
    r = client.get(f"/api/r/{code}/full")
    assert r.status_code == 401

    # kirim kode (mock -> dev_code), verifikasi, buka laporan
    r = client.post(f"/api/r/{code}/send-code", json={"phone": "13800138000"})
    assert r.status_code == 200, r.text
    dev_code = r.json().get("dev_code")
    assert dev_code

    r = client.post(f"/api/r/{code}/verify", json={
        "phone": "13800138000", "code": dev_code, "name": "张三",
        "company": "测试目标公司", "consent": True})
    assert r.status_code == 200, r.text
    unlock = r.json()["unlock_token"]

    r = client.get(f"/api/r/{code}/full", params={"token": unlock})
    assert r.status_code == 200
    body = r.json()
    assert len(body["metrics"]) == 3
    assert len(body["problems"]) >= 2
    assert len(body["sentiment_items"]) > 0
    assert not body["locked"]

    # nomor yang sama tidak perlu kode lagi (anti-duplikasi)
    r = client.post(f"/api/r/{code}/verify", json={
        "phone": "13800138000", "code": "", "consent": True})
    assert r.status_code == 200

    # prospek masuk & ter-mask
    r = client.get("/api/prospects", headers=headers)
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["phone_mask"] == "138****8000"

    # share link + QR
    r = client.get(f"/api/diagnoses/{diag_id}/share", headers=headers)
    assert r.status_code == 200 and "<svg" in r.json()["qr_svg"]

    # excel export
    r = client.get("/api/prospects/export", headers=headers)
    assert r.status_code == 200
    assert r.headers["content-type"].endswith("sheet")
