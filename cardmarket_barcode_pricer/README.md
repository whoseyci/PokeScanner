# Cardmarket Barcode Pricer

Local prototype for scanning a sealed-product EAN/UPC with a 1D barcode scanner and showing Cardmarket prices.

## What it does

```text
scan/type barcode
→ validate EAN/UPC
→ resolve barcode to sealed-product candidates
→ fetch or load Cardmarket product pages
→ parse Available / From / Price Trend / 30d / 7d / 1d prices
→ show all plausible candidates if barcode is ambiguous
```

A USB 1D scanner works because it usually behaves like a keyboard: it types digits and presses Enter.

## Quick test

```bash
cd cardmarket_barcode_pricer
python scan.py 0196214137158 --fixture
```

JSON:

```bash
python scan.py 0196214137158 --fixture --json
```

Open the strongest Cardmarket candidate directly from the CLI:

```bash
python scan.py 0196214137158 --first --open
```

Local scanner UI:

```bash
python server.py
# open http://127.0.0.1:8765
```

The UI now supports the highest-reliability workflow:

```text
scan barcode → resolve strongest-confidence candidate → open Cardmarket product page in a new tab
```

Enable the checkbox:

```text
auto-open strongest Cardmarket candidate
```

If the browser blocks the popup, use the per-candidate **Open Cardmarket** button.

## Sample result for `0196214137158`

This EAN validates as EAN-13 and maps to Pokémon TCG ME03 Perfect Order sealed products. It is ambiguous in retailer data, so the system returns candidates:

- `Perfect Order Booster` — likely single booster
- `Perfect Order Booster Box` — display/box candidate
- `Perfect Order Booster Box (18 Boosters)` — lower-confidence packaging variant

The fixture prices bundled for the trial are:

| Candidate | Available | From | Trend | 30d | 7d | 1d |
|---|---:|---:|---:|---:|---:|---:|
| Perfect Order Booster | 6420 | €3.30 | €5.03 | €4.74 | €5.21 | €4.99 |
| Perfect Order Booster Box | 1047 | €118.01 | €167.02 | €167.94 | €165.50 | €174.71 |
| Perfect Order Booster Box (18 Boosters) | 90 | €79.99 | €89.09 | €86.50 | €87.21 | €102.00 |

Prices move. Treat bundled fixtures as demo/cached snapshots, not current truth.

## Why fixtures exist

Direct unauthenticated HTTP requests to Cardmarket can return `403 Forbidden`. For a robust production setup, use one of:

1. official Cardmarket API where permitted,
2. a logged-in/browser fetcher you control,
3. manually cached snapshots,
4. a maintained barcode → Cardmarket product mapping database.

This prototype has a pluggable fetch layer and a fixture fallback so scanner and parser logic can be tested reliably.

## Add new barcode mappings

Edit:

```text
data/barcode_aliases.json
```

Add candidates with Cardmarket URLs and confidence scores. Barcode alone is often ambiguous for sealed products, especially when retailers reuse EANs for booster/display pages.

## Robustness rules

- Do not silently guess when a barcode maps to multiple Cardmarket products.
- Show multiple candidates with confidence and packaging unit.
- Cache fetched pages.
- Separate barcode resolution from price parsing.
- Prefer official API or browser automation over brittle raw scraping.
- Log fetch source: `live`, `cache`, `fixture`, or `fixture_after_fetch_error`.

## Files

```text
scan.py                         CLI lookup
server.py                       local scanner web UI
cm_pricer/barcode.py            EAN/UPC validation
cm_pricer/resolver.py           barcode → candidate mapping
cm_pricer/cardmarket.py         fetch/cache/parse Cardmarket pages
data/barcode_aliases.json       local barcode mapping DB
data/cardmarket_price_fixtures.json demo/current sample pages
web/index.html                  scanner UI
```
