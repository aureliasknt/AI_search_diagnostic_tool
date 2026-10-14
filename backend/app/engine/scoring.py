"""Model penilaian komprehensif (PRD 4.3).

Skor 0-100, bobot default: tingkat penyebutan 40% / posisi 30% / sentimen 30%.
- mention_rate = sampel menyebut / total sampel x 100
- position   = posisi pertama = skor penuh, menurun linear per posisi berikutnya
               (rata-rata hanya atas sampel yang menyebut brand)
- sentiment  = (positif x 1 + netral x 0.5) / total sampel x 100
Kategori: >=80 良好, 60-79 一般, <60 较差.
"""
from dataclasses import dataclass, asdict


@dataclass
class BrandScore:
    brand: str
    is_target: bool
    total: int
    mention_samples: int
    mention_rate: float
    mention_count: int
    position_score: float
    pos_count: int
    neu_count: int
    neg_count: int
    sentiment_score: float
    composite: float

    def to_dict(self) -> dict:
        return asdict(self)


def category_of(score: float) -> str:
    if score >= 80:
        return "良好"
    if score >= 60:
        return "一般"
    return "较差"


def compute_brand_scores(parsed_samples: list[dict], sentiments: list[dict],
                         brands: list[str], is_target: str,
                         weights: dict) -> list[BrandScore]:
    """parsed_samples: [parse_answer(...) per sampel]
    sentiments:       [{brand: 'positive'|'neutral'|'negative'} per sampel]"""
    total = len(parsed_samples)
    out: list[BrandScore] = []
    for brand in brands:
        mention_samples = 0
        mention_count = 0
        pos_sums = []
        pos_count = neu_count = neg_count = 0

        for parsed, sent in zip(parsed_samples, sentiments):
            info = parsed.get(brand, {})
            if info.get("mentioned"):
                mention_samples += 1
                mention_count += info.get("count", 1)
                n_mentioned = max(sum(1 for v in parsed.values() if v.get("mentioned")), 1)
                order = info.get("order") or n_mentioned
                # posisi pertama = skor penuh; menurun linear sampai 0 di posisi terakhir.
                # brand yang disebut sendirian tetap = skor penuh.
                if n_mentioned <= 1:
                    pos_sums.append(100.0)
                else:
                    pos_sums.append(100.0 * (n_mentioned - order) / (n_mentioned - 1))
                s = sent.get(brand, "neutral")
                if s == "positive":
                    pos_count += 1
                elif s == "negative":
                    neg_count += 1
                else:
                    neu_count += 1

        mention_rate = (mention_samples / total * 100) if total else 0.0
        position_score = round(sum(pos_sums) / len(pos_sums), 2) if pos_sums else 0.0
        sentiment_score = round((pos_count + 0.5 * neu_count) / total * 100, 2) if total else 0.0
        w = weights or {"mention": 40, "position": 30, "sentiment": 30}
        composite = round(
            mention_rate * w.get("mention", 40) / 100
            + position_score * w.get("position", 30) / 100
            + sentiment_score * w.get("sentiment", 30) / 100, 2)
        out.append(BrandScore(
            brand=brand, is_target=(brand == is_target), total=total,
            mention_samples=mention_samples, mention_rate=round(mention_rate, 2),
            mention_count=mention_count, position_score=position_score,
            pos_count=pos_count, neu_count=neu_count, neg_count=neg_count,
            sentiment_score=sentiment_score, composite=composite,
        ))

    out.sort(key=lambda x: x.composite, reverse=True)
    return out


def rank_scores(scores: list[BrandScore]) -> dict[str, int]:
    return {b.brand: i for i, b in enumerate(sorted(scores, key=lambda x: x.composite, reverse=True), start=1)}


def neg_ratio(score: BrandScore) -> float:
    return round(score.neg_count / score.total * 100, 2) if score.total else 0.0
