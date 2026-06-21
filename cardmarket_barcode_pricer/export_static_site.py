#!/usr/bin/env python3
"""Refresh static GitHub Pages data from local mapping/fixture files."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
DOCS_DATA = ROOT / "docs" / "data"
DOCS_DATA.mkdir(parents=True, exist_ok=True)
for name in ["barcode_aliases.json", "cardmarket_price_fixtures.json"]:
    shutil.copyfile(ROOT / "data" / name, DOCS_DATA / name)
    print(f"updated docs/data/{name}")
print("Static site ready in docs/")
