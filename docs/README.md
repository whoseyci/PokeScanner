# PokeScanner GitHub Pages

Static scanner UI for GitHub Pages.

## Works on GitHub Pages

- USB/keyboard barcode scan.
- Camera-based 1D scan via browser `BarcodeDetector` where supported.
- EAN/UPC validation.
- Barcode → local Cardmarket sealed-product candidates.
- Cached/exported price display.
- Optional browser fetch of Cardmarket public daily price guide (`price_guide_6.json`) by `idProduct`.
- Open strongest Cardmarket candidate in a new tab.
- For ambiguous barcodes: choose `Remember & Open`; future scans open that selected product automatically.
- For unknown barcodes: call the preconfigured Google Apps Script resolver API to turn the barcode into Cardmarket candidate links.
- If no resolver candidate exists: paste a Cardmarket product URL once and save a browser-local mapping.
- Export browser-local mappings as JSON for later commit into `data/barcode_aliases.json`.
- Optional external JSON price export URL.

## Limitations

- No live Cardmarket page scraping from GitHub Pages.
- No Cardmarket login/session access.
- Camera scanning requires HTTPS and browser support; Chrome/Edge are best.
- Unknown barcodes still need local mapping in `data/barcode_aliases.json`.
