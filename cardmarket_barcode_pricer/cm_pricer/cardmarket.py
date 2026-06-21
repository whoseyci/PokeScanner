from __future__ import annotations
import html, json, re, time, urllib.request, urllib.error
from pathlib import Path
from .models import CardmarketPrice

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "data" / "cardmarket_price_fixtures.json"
CACHE_DIR = ROOT / "data" / "cache"


def eur_to_float(s: str | None) -> float | None:
    if not s:
        return None
    s = s.strip().replace("€", "").replace(" ", "")
    # German/EU format: 1.234,56
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def int_eu(s: str | None) -> int | None:
    if not s:
        return None
    try:
        return int(re.sub(r"\D+", "", s))
    except ValueError:
        return None


def strip_html(text: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def load_fixtures() -> dict:
    if FIXTURE_PATH.exists():
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return {}


def cache_key(url: str) -> str:
    import hashlib
    return hashlib.sha1(url.encode()).hexdigest()


def fetch_url(url: str, ttl_seconds: int = 900) -> tuple[str, str]:
    """Fetch Cardmarket page.

    Cardmarket often blocks non-browser requests. This function caches successful
    responses and raises a clear error on 403 so the caller can fall back to fixtures
    or an official/API/browser fetcher.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{cache_key(url)}.txt"
    meta = CACHE_DIR / f"{cache_key(url)}.meta.json"
    if path.exists() and meta.exists():
        age = time.time() - json.loads(meta.read_text()).get("time", 0)
        if age < ttl_seconds:
            return path.read_text(encoding="utf-8", errors="ignore"), "cache"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; personal barcode price checker; +local)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        data = r.read().decode("utf-8", errors="ignore")
    path.write_text(data, encoding="utf-8")
    meta.write_text(json.dumps({"time": time.time(), "url": url}, indent=2), encoding="utf-8")
    return data, "live"


def text_for_url(url: str, prefer_fixtures: bool = False) -> tuple[str, str]:
    fixtures = load_fixtures()
    if prefer_fixtures and url in fixtures:
        return fixtures[url]["text"], "fixture"
    try:
        return fetch_url(url)
    except Exception as e:
        if url in fixtures:
            return fixtures[url]["text"], f"fixture_after_fetch_error:{type(e).__name__}"
        raise


def parse_cardmarket_price(text: str, url: str, fetched_from: str = "unknown") -> CardmarketPrice:
    # Works on markdown-ish fetched text, raw HTML stripped text, or snippets.
    plain = strip_html(text)
    # Markdown title line often starts with '# title'; HTML stripped title still contains title text.
    title_match = re.search(r"^#\s*(.+?)(?:\n|$)", text.strip(), flags=re.M)
    title = title_match.group(1).strip() if title_match else ""
    if not title:
        # Cardmarket pages often include product name before "Available items".
        m = re.search(r"([^#\n]{4,120}?)(?:Available items|Boosters|Booster Boxes)", plain)
        title = (m.group(1).strip() if m else "Cardmarket product")
    compact = re.sub(r"\s+", "", plain)
    # Also keep a spaced version to handle labels with spaces.
    spaced = re.sub(r"\s+", " ", plain)

    def price_after(label: str):
        # Match both "Price Trend167,02 €" and "Price Trend 167,02 €".
        lab = re.escape(label).replace("\\ ", r"\s*")
        m = re.search(lab + r"\s*([0-9.]+,[0-9]{2}|[0-9]+(?:\.[0-9]{2})?)\s*€", spaced, flags=re.I)
        if not m:
            m = re.search(lab.replace(r"\s*", "") + r"([0-9.]+,[0-9]{2})€", compact, flags=re.I)
        return eur_to_float(m.group(1)) if m else None

    available = None
    m = re.search(r"Available\s*items\s*([0-9.]+)", spaced, flags=re.I) or re.search(r"Availableitems([0-9.]+)", compact, flags=re.I)
    if m:
        available = int_eu(m.group(1))

    result = CardmarketPrice(
        title=title,
        url=url,
        available_items=available,
        from_price_eur=price_after("From"),
        price_trend_eur=price_after("Price Trend"),
        avg_30d_eur=price_after("30-days average price"),
        avg_7d_eur=price_after("7-days average price"),
        avg_1d_eur=price_after("1-day average price"),
        fetched_from=fetched_from,
        raw_excerpt=spaced[:800],
    )
    return result


def get_price(url: str, prefer_fixtures: bool = False) -> CardmarketPrice:
    text, source = text_for_url(url, prefer_fixtures=prefer_fixtures)
    return parse_cardmarket_price(text, url, source)
