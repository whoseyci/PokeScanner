from __future__ import annotations
import json
from pathlib import Path
from .barcode import normalize_barcode, upca_to_ean13
from .models import ProductCandidate

ROOT = Path(__file__).resolve().parents[1]
ALIASES = ROOT / "data" / "barcode_aliases.json"


def load_aliases() -> dict:
    if ALIASES.exists():
        return json.loads(ALIASES.read_text(encoding="utf-8"))
    return {}


def resolve_barcode(raw: str) -> tuple[str, dict, list[ProductCandidate]]:
    code = normalize_barcode(raw)
    variants = [code]
    if len(code) == 12:
        variants.append(upca_to_ean13(code))
    aliases = load_aliases()
    record = None
    matched = code
    for v in variants:
        if v in aliases:
            record = aliases[v]
            matched = v
            break
    if not record:
        return code, {}, []
    candidates = [ProductCandidate(barcode=matched, **c) for c in record.get("candidates", [])]
    candidates.sort(key=lambda c: c.confidence, reverse=True)
    return matched, record, candidates
