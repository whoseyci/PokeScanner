# Cardmarket Barcode Pricer GitHub Pages

Static scanner UI for GitHub Pages.

## What works on GitHub Pages

- Scan/type barcode.
- Validate EAN/UPC.
- Resolve to local Cardmarket sealed-product candidates.
- Show cached/exported prices from `data/cardmarket_price_fixtures.json`.
- Open the strongest-confidence Cardmarket page in a new browser tab.
- Optionally load an external daily price JSON URL if CORS allows it.

## What does not work on GitHub Pages

- Live scraping Cardmarket.
- Reading your logged-in Cardmarket session.
- Writing back to the mapping DB.

For live price parsing, run the local Python server or use an official API / daily export.
