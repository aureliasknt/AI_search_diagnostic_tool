"""Celery app — dipakai saat WORKER_BACKEND=celery (production ber-Redis).

Default dev memakai LocalWorker (asyncio in-process); modul ini tidak diimpor
kecuali backend celery dipilih, sehingga Redis tidak dibutuhkan saat dev.
"""
import os

from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("aidiag", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.task_routes = {"app.engine.celery_app.run_diagnosis_task": {"queue": "diagnosis"}}


@celery_app.task(name="app.engine.celery_app.run_diagnosis_task")
def run_diagnosis_task(diagnosis_id: int):
    from .worker import run_diagnosis_sync
    run_diagnosis_sync(diagnosis_id)
