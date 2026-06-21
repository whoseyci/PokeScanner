from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class ProductCandidate:
    barcode: str
    name: str
    cardmarket_url: str
    game: str = "Pokemon"
    category: str = "Sealed"
    language: str | None = None
    unit: str | None = None
    confidence: float = 0.5
    source: str = "local_alias"
    note: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class CardmarketPrice:
    title: str
    url: str
    available_items: Optional[int] = None
    from_price_eur: Optional[float] = None
    price_trend_eur: Optional[float] = None
    avg_30d_eur: Optional[float] = None
    avg_7d_eur: Optional[float] = None
    avg_1d_eur: Optional[float] = None
    fetched_from: str = "unknown"
    raw_excerpt: str = ""

    def to_dict(self):
        return asdict(self)
