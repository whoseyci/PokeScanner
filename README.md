# Cardmarket Barcode Pricer

Local prototype for scanning a sealed-product EAN/UPC with a 1D barcode scanner and showing Cardmarket prices.

## What it does

```text
scan/type barcode or use camera scanner
→ validate EAN/UPC
→ resolve barcode to sealed-product candidates
→ use public Cardmarket daily price guide by idProduct when possible
→ otherwise load cached/exported Cardmarket product-page text
→ parse/display Available / From-Low / Price Trend / 30d / 7d / 1d prices
→ show all plausible candidates if barcode is ambiguous
→ optionally open the strongest Cardmarket candidate
```

A USB 1D scanner works because it usually behaves like a keyboard: it types digits and presses Enter.

## GitHub Pages / camera scanner

The static app in `docs/index.html` now includes a camera scanner using the browser `BarcodeDetector` API.

Requirements:

```text
HTTPS page, e.g. GitHub Pages
Chrome/Edge recommended
camera permission granted
```

Expected Pages URL after pushing and enabling `main /docs`:

```text
https://whoseyci.github.io/PokeScanner/
```

The barcode `0196214139299` is now mapped to Lumiose/Illumina City Mini Tin candidates.

## Scan → select → remember

The static UI now supports the intended product flow:

```text
scan known unambiguous barcode → open strongest Cardmarket page
scan known ambiguous barcode   → show options → Remember & Open one → next scan opens it automatically
scan unknown barcode + resolver configured → resolver returns Cardmarket options → Remember & Open one → next scan opens it automatically
scan unknown barcode without resolver       → paste/select Cardmarket URL once → save local mapping → next scan opens it automatically
```

This memory is stored in browser `localStorage`. Use **Download local mappings** to export your browser-learned mappings and later merge them into `data/barcode_aliases.json`.

## Optional resolver API

To make unknown barcodes resolve automatically instead of manually searching Cardmarket, the page is preconfigured with this Google Apps Script resolver:

```text
https://script.google.com/macros/s/AKfycbzPJEot8sQaeBCSPsn-y7jXP32hlDSeHvAx5lshO9uKkshL1kYEMpT3fxrjG0Yy1k9B/exec
```

The resolver source is kept in:

```text
apps_script/PokeScannerApi.gs
```

If you redeploy it later, paste the new `/exec` URL into the PokeScanner page under **Online barcode resolver API**.

The resolver does:

```text
barcode → barcode API / manual hints / nearby barcode-family fallback → product-name hints → fuzzy match against Cardmarket public nonsingles catalog → Cardmarket candidate links + daily price guide data
```

Built-in barcode-name providers in the Apps Script:

```text
UPCItemDB public trial endpoint
barcode.monster public endpoint
optional custom endpoint via EXTERNAL_BARCODE_LOOKUP_URL_TEMPLATE
```

Important caveat: public barcode APIs have sparse Pokémon sealed-product coverage. If no provider knows the barcode, the resolver cannot infer the product from Cardmarket alone because Cardmarket's public product files do not include EAN/GTIN fields.

Because Cardmarket's public product files do not contain EAN/GTIN fields, the resolver still needs either manual barcode hints or an external barcode/product-name provider for truly unknown barcodes.

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
