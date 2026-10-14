from datetime import datetime

from sqlalchemy import (JSON, Boolean, DateTime, Float, ForeignKey, Integer,
                        String, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _now() -> datetime:
    return datetime.now()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(16), default="sales")  # admin | sales
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255))
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    competitors: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(16), default="queued")  # queued|running|done|failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    share_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_samples: Mapped[int] = mapped_column(Integer, default=0)
    sample_target: Mapped[int] = mapped_column(Integer, default=0)  # >0: H5 flow, jumlah pertanyaan tepat
    industry: Mapped[str] = mapped_column(String(100), default="")
    products: Mapped[str] = mapped_column(String(255), default="")
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    category: Mapped[str | None] = mapped_column(String(16), nullable=True)
    conclusion: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    metrics: Mapped[list["BrandMetric"]] = relationship(back_populates="diagnosis", cascade="all, delete-orphan")
    samples: Mapped[list["Sample"]] = relationship(back_populates="diagnosis", cascade="all, delete-orphan")
    geo_profiles: Mapped[list["GeoProfile"]] = relationship(back_populates="diagnosis", cascade="all, delete-orphan", order_by="GeoProfile.sort")
    sentiment_items: Mapped[list["SentimentItem"]] = relationship(back_populates="diagnosis", cascade="all, delete-orphan")
    problems: Mapped[list["Problem"]] = relationship(back_populates="diagnosis", cascade="all, delete-orphan", order_by="Problem.sort")


class Sample(Base):
    __tablename__ = "samples"

    id: Mapped[int] = mapped_column(primary_key=True)
    diagnosis_id: Mapped[int] = mapped_column(ForeignKey("diagnoses.id"), index=True)
    keyword: Mapped[str] = mapped_column(String(255))
    question: Mapped[str] = mapped_column(String(512))
    round_no: Mapped[int] = mapped_column(Integer, default=1)
    answer_text: Mapped[str] = mapped_column(Text, default="")
    parse_json: Mapped[dict] = mapped_column(JSON, default=dict)     # per-brand: mentioned/first_index/count/rank
    sentiment_json: Mapped[dict] = mapped_column(JSON, default=dict)  # per-brand: positive|neutral|negative

    diagnosis: Mapped[Diagnosis] = relationship(back_populates="samples")


class BrandMetric(Base):
    __tablename__ = "brand_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    diagnosis_id: Mapped[int] = mapped_column(ForeignKey("diagnoses.id"), index=True)
    brand_name: Mapped[str] = mapped_column(String(255))
    is_target: Mapped[bool] = mapped_column(Boolean, default=False)
    mention_rate: Mapped[float] = mapped_column(Float, default=0)
    mention_count: Mapped[int] = mapped_column(Integer, default=0)
    position_score: Mapped[float] = mapped_column(Float, default=0)
    pos_count: Mapped[int] = mapped_column(Integer, default=0)
    neu_count: Mapped[int] = mapped_column(Integer, default=0)
    neg_count: Mapped[int] = mapped_column(Integer, default=0)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0)
    composite: Mapped[float] = mapped_column(Float, default=0)
    rank: Mapped[int] = mapped_column(Integer, default=0)

    diagnosis: Mapped[Diagnosis] = relationship(back_populates="metrics")


class GeoProfile(Base):
    __tablename__ = "geo_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    diagnosis_id: Mapped[int] = mapped_column(ForeignKey("diagnoses.id"), index=True)
    company_name: Mapped[str] = mapped_column(String(255))
    stage: Mapped[str] = mapped_column(String(64), default="")
    channels: Mapped[str] = mapped_column(String(255), default="")
    content_eco: Mapped[str] = mapped_column(String(255), default="")
    authority: Mapped[str] = mapped_column(String(255), default="")
    visibility: Mapped[str] = mapped_column(String(255), default="")
    acquisition_model: Mapped[str] = mapped_column(String(255), default="")
    sort: Mapped[int] = mapped_column(Integer, default=0)

    diagnosis: Mapped[Diagnosis] = relationship(back_populates="geo_profiles")


class SentimentItem(Base):
    __tablename__ = "sentiment_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    diagnosis_id: Mapped[int] = mapped_column(ForeignKey("diagnoses.id"), index=True)
    publish_date: Mapped[str] = mapped_column(String(32), default="")
    item_type: Mapped[str] = mapped_column(String(32), default="")   # 竞品舆情 | 企业舆情
    title: Mapped[str] = mapped_column(String(512), default="")
    polarity: Mapped[str] = mapped_column(String(8), default="neutral")  # positive|neutral|negative
    company_name: Mapped[str] = mapped_column(String(255), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(512), default="")

    diagnosis: Mapped[Diagnosis] = relationship(back_populates="sentiment_items")


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(primary_key=True)
    diagnosis_id: Mapped[int] = mapped_column(ForeignKey("diagnoses.id"), index=True)
    title: Mapped[str] = mapped_column(String(512), default="")
    problem_text: Mapped[str] = mapped_column(Text, default="")
    suggestion_text: Mapped[str] = mapped_column(Text, default="")
    sort: Mapped[int] = mapped_column(Integer, default=0)

    diagnosis: Mapped[Diagnosis] = relationship(back_populates="problems")


class Config(Base):
    __tablename__ = "configs"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)


class Prospect(Base):
    __tablename__ = "prospects"
    __table_args__ = (UniqueConstraint("diagnosis_id", "phone_hash", name="uq_prospect_phone"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    diagnosis_id: Mapped[int] = mapped_column(ForeignKey("diagnoses.id"), index=True)
    phone_enc: Mapped[str] = mapped_column(Text)
    phone_hash: Mapped[str] = mapped_column(String(64))
    phone_mask: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(64), default="")
    company: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(16), default="new")
    # new | contacted | scheduled | deal | invalid
    exported_pdf: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class SmsCode(Base):
    __tablename__ = "sms_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    diagnosis_id: Mapped[int] = mapped_column(ForeignKey("diagnoses.id"), index=True)
    phone_hash: Mapped[str] = mapped_column(String(64), index=True)
    code_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
