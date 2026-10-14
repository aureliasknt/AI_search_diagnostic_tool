"""Worker asinkron + pipeline diagnostik end-to-end (PRD Bab 3-4).

Backend `local` menjalankan pipeline di thread terpisah dengan status di DB
(default dev). Backend `celery` tersedia untuk production ber-Redis
(WORKER_BACKEND=celery), memakai fungsi pipeline yang sama.
"""
import asyncio
import logging
import random
from datetime import datetime

import anyio
from sqlalchemy.orm import Session

from .. import config as appcfg
from ..config_store import get_config, effective_platform
from ..db import SessionLocal
from ..models import (BrandMetric, Diagnosis, Problem, Sample, SentimentItem)
from . import parser, problems as problems_mod, scoring
from .doubao import build_provider
from .questions import build_question_plan, build_question_plan_exact
from .sentiment import build_analyzer

log = logging.getLogger("worker")


# ----------------------------- pipeline -----------------------------
def _fake_sentiment_items(db: Session, diag: Diagnosis, brands: list[str],
                          samples: list[Sample], rng: random.Random) -> None:
    """Bangun baris tabel detail sentimen (MVP: dari jawaban Doubao + tautan
    yang terekstrak). Mode mock mensintesis baris dari sampel yang ada."""
    from datetime import timedelta
    base = datetime.now() - timedelta(days=180)
    type_label = {True: "企业舆情", False: "竞品舆情"}
    for s in samples:
        parsed = s.parse_json or {}
        for brand in brands:
            info = parsed.get(brand, {})
            if not info.get("mentioned"):
                continue
            sent = (s.sentiment_json or {}).get(brand, "neutral")
            date = (base + timedelta(days=rng.randint(0, 175))).strftime("%Y-%m-%d")
            db.add(SentimentItem(
                diagnosis_id=diag.id,
                publish_date=date,
                item_type=type_label[brand == diag.company_name],
                title=s.question[:60],
                polarity=sent,
                company_name=brand,
                summary=(s.answer_text or "")[:200],
                source="；".join(rng.sample(
                    ["豆包AI回答", "http://example.com/ref.html", "行业公开资料"], k=rng.randint(1, 2))),
            ))


def run_diagnosis_sync(diagnosis_id: int) -> None:
    db = SessionLocal()
    diag = db.get(Diagnosis, diagnosis_id)
    if diag is None:
        db.close()
        return

    try:
        diag.status = "running"
        diag.error = None
        diag.started_at = datetime.now()
        diag.progress = 5
        db.commit()

        platform = effective_platform(db)
        weights = get_config(db, "weights")
        templates = get_config(db, "question_templates")
        alias_rows = get_config(db, "aliases")
        rules = get_config(db, "recommendations")
        report_cfg = get_config(db, "report")
        alias_map = {r["brand"]: r.get("aliases", []) for r in alias_rows if r.get("brand")}

        variants = int(platform.get("variants", 3))
        rounds = int(platform.get("rounds", 2))
        temperature = float(platform.get("temperature", 0.5))
        brands = [diag.company_name] + list(diag.competitors or [])

        # resep mock: reproduktif per diagnosa, target punya probabilitas sendiri
        rng = random.Random(diag.share_code)
        recipes = {
            diag.company_name: {"p_mention": rng.uniform(0.35, 0.75), "p_pos": rng.uniform(0.45, 0.8)},
        }
        for c in diag.competitors or []:
            recipes[c] = {"p_mention": rng.uniform(0.3, 0.7), "p_pos": rng.uniform(0.4, 0.75)}

        provider = build_provider(platform, brands, seed=diag.id, brand_recipes=recipes)
        analyzer = build_analyzer(platform)

        # 1) susun rencana pertanyaan
        #    H5 flow (sample_target > 0): tepat N pertanyaan, kuota rata per keyword.
        #    Admin flow: legacy variants x rounds.
        if getattr(diag, "sample_target", 0):
            plan: list[tuple[str, str, int]] = build_question_plan_exact(
                diag.keywords or [diag.company_name], templates, diag.sample_target)
        else:
            plan = [(kw, q, r)
                    for kw in diag.keywords or []
                    for q in build_question_plan(kw, templates, variants)
                    for r in range(1, rounds + 1)]
        total = len(plan)
        diag.total_samples = total
        diag.progress = 10
        db.commit()

        # 2) query LLM secara paralel (semaphore)
        sem = asyncio.Semaphore(5)

        async def ask_one(kw: str, question: str, rnd: int):
            async with sem:
                ans = await provider.ask(question, temperature)
            parsed = parser.parse_answer(ans.text, brands, alias_map)
            sentiments = {}
            for brand in brands:
                if parsed.get(brand, {}).get("mentioned"):
                    sentiments[brand] = await analyzer.classify(brand, ans.text)
            return Sample(
                diagnosis_id=diag.id, keyword=kw, question=question, round_no=rnd,
                answer_text=ans.text, parse_json=parsed, sentiment_json=sentiments,
            )

        async def gather_all():
            tasks = [ask_one(kw, q, rnd) for (kw, q, rnd) in plan]
            done = 0
            samples: list[Sample] = []
            for fut in asyncio.as_completed(tasks):
                s = await fut
                samples.append(s)
                done += 1
                diag.progress = 10 + int(done / max(total, 1) * 60)
                if done % 5 == 0 or done == total:
                    db.commit()
            return samples

        samples = asyncio.run(gather_all())
        db.bulk_save_objects(samples)
        db.commit()
        diag.progress = 75

        # 3) skoring
        parsed_samples = [s.parse_json or {} for s in samples]
        sentiment_rows = [s.sentiment_json or {} for s in samples]
        scores = scoring.compute_brand_scores(parsed_samples, sentiment_rows, brands,
                                              diag.company_name, weights)
        ranks = scoring.rank_scores(scores)
        for sc in scores:
            db.add(BrandMetric(
                diagnosis_id=diag.id, brand_name=sc.brand, is_target=sc.is_target,
                mention_rate=sc.mention_rate, mention_count=sc.mention_count,
                position_score=sc.position_score, pos_count=sc.pos_count,
                neu_count=sc.neu_count, neg_count=sc.neg_count,
                sentiment_score=sc.sentiment_score, composite=sc.composite,
                rank=ranks[sc.brand],
            ))

        target = next((s for s in scores if s.is_target), scores[0] if scores else None)
        diag.score = target.composite if target else None
        diag.category = scoring.category_of(diag.score or 0)
        tmpl = report_cfg.get("conclusion_template", "")
        diag.conclusion = tmpl.format(
            company=diag.company_name,
            keywords="、".join(diag.keywords or []),
            mention_rate=f"{target.mention_rate:.0f}" if target else "-",
            rank=ranks.get(diag.company_name, "-") if target else "-",
        )
        diag.progress = 85

        # 4) kartu masalah & rekomendasi
        for i, card in enumerate(problems_mod.match_problems(rules, scores), start=1):
            db.add(Problem(diagnosis_id=diag.id, sort=i, **card))

        # 5) baris detail sentimen (mock: sintesis dari sampel)
        _fake_sentiment_items(db, diag, brands, samples, rng)

        diag.status = "done"
        diag.progress = 100
        diag.finished_at = datetime.now()
        db.commit()
        log.info("diagnosis %s selesai: skor=%s", diag.id, diag.score)
    except Exception as exc:  # noqa: BLE001 - catat ke DB agar bisa retry
        db.rollback()
        diag = db.get(Diagnosis, diagnosis_id)
        diag.status = "failed"
        diag.error = str(exc)[:2000]
        diag.finished_at = datetime.now()
        db.commit()
        log.exception("diagnosis %s gagal", diagnosis_id)
    finally:
        db.close()


# ----------------------------- queue -----------------------------
class LocalWorker:
    """Asyncio in-process: pipeline berjalan di thread terpisah (SQLAlchemy sync)."""

    def submit(self, diagnosis_id: int) -> None:
        async def _wrap():
            await anyio.to_thread.run_sync(run_diagnosis_sync, diagnosis_id)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(_wrap())
        else:
            loop.create_task(_wrap())


class CeleryWorker:
    def submit(self, diagnosis_id: int) -> None:
        from .celery_app import run_diagnosis_task
        run_diagnosis_task.delay(diagnosis_id)


def get_worker():
    if appcfg.WORKER_BACKEND == "celery":
        return CeleryWorker()
    return LocalWorker()


def requeue_interrupted() -> None:
    """Saat boot, diagnosa yang menggantung karena restart worker dijadwalkan ulang."""
    db = SessionLocal()
    try:
        stale = db.query(Diagnosis).filter(Diagnosis.status.in_(["queued", "running"])).all()
        for d in stale:
            d.status = "queued"
            d.progress = 0
        db.commit()
        for d in stale:
            get_worker().submit(d.id)
        if stale:
            log.info("%s diagnosa dijadwalkan ulang", len(stale))
    finally:
        db.close()
