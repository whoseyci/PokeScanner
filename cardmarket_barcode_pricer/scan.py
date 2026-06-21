#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys, webbrowser
from cm_pricer.barcode import validate_any
from cm_pricer.resolver import resolve_barcode
from cm_pricer.cardmarket import get_price


def lookup(barcode: str, fixture: bool = False, max_candidates: int | None = None) -> dict:
    validation = validate_any(barcode)
    code, record, candidates = resolve_barcode(validation["normalized"])
    if max_candidates:
        candidates = candidates[:max_candidates]
    out = {
        "input": barcode,
        "barcode": validation,
        "matched_barcode": code,
        "product_hint": {k: v for k, v in record.items() if k != "candidates"},
        "candidate_count": len(candidates),
        "candidates": [],
    }
    for cand in candidates:
        item = cand.to_dict()
        try:
            price = get_price(cand.cardmarket_url, prefer_fixtures=fixture)
            item["price"] = price.to_dict()
            item["ok"] = True
        except Exception as e:
            item["ok"] = False
            item["error"] = f"{type(e).__name__}: {e}"
        out["candidates"].append(item)
    return out


def print_human(result: dict) -> None:
    print(f"Barcode: {result['barcode']['normalized']} valid={result['barcode']['valid']}")
    hint = result.get("product_hint", {})
    if hint:
        print(f"Hint: {hint.get('name','')} | {hint.get('note','')}")
    if not result["candidates"]:
        print("No local barcode mapping found. Add one to data/barcode_aliases.json.")
        return
    for i,c in enumerate(result["candidates"],1):
        print(f"\n[{i}] {c['name']} ({c.get('unit') or c.get('category')}) confidence={c['confidence']}")
        print(f"    URL: {c['cardmarket_url']}")
        if c.get("ok"):
            p = c["price"]
            print(f"    Available: {p.get('available_items')} | From: €{p.get('from_price_eur')} | Trend: €{p.get('price_trend_eur')}")
            print(f"    30d: €{p.get('avg_30d_eur')} | 7d: €{p.get('avg_7d_eur')} | 1d: €{p.get('avg_1d_eur')}")
            print(f"    fetched_from: {p.get('fetched_from')}")
        else:
            print(f"    ERROR: {c.get('error')}")


def main():
    ap = argparse.ArgumentParser(description="Barcode → Cardmarket sealed product price lookup")
    ap.add_argument("barcode", nargs="?", help="EAN/UPC from scanner. If omitted, read stdin.")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fixture", action="store_true", help="Use bundled fixtures first. Good for tests/demo when Cardmarket blocks direct HTTP.")
    ap.add_argument("--first", action="store_true", help="Only fetch highest-confidence candidate.")
    ap.add_argument("--open", action="store_true", help="Open the strongest-confidence Cardmarket candidate in your default browser.")
    args = ap.parse_args()
    barcode = args.barcode or sys.stdin.readline().strip()
    result = lookup(barcode, fixture=args.fixture, max_candidates=1 if args.first else None)
    if args.open and result.get("candidates"):
        best = result["candidates"][0]
        url = best.get("cardmarket_url")
        if url:
            webbrowser.open(url, new=2)
            result["opened_url"] = url
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human(result)
        if args.open and result.get("opened_url"):
            print(f"\nOpened strongest candidate: {result['opened_url']}")


if __name__ == "__main__":
    main()
