/**
 * PokeScanner Barcode Resolver API for Google Apps Script
 * ------------------------------------------------------
 * Deploy as Web App: Execute as Me, access Anyone.
 * Then paste the Web App URL into PokeScanner's "Resolver API URL" field.
 *
 * Endpoint:
 *   .../exec?barcode=0196214139299
 *   .../exec?barcode=0196214139299&callback=foo   // JSONP for GitHub Pages
 *
 * It resolves barcode -> product hints -> Cardmarket public catalog candidates.
 * Cardmarket public files do NOT contain EANs, so unknown barcodes require either
 * manual hints here or optional external barcode/search providers.
 */

const CM_URLS = {
  PRICE_GUIDE: 'https://downloads.s3.cardmarket.com/productCatalog/priceGuide/price_guide_6.json',
  NONSINGLES: 'https://downloads.s3.cardmarket.com/productCatalog/productList/products_nonsingles_6.json'
};

// Add quick barcode hints here. These are only for resolving product names;
// prices/candidates are still pulled from Cardmarket public files.
const BARCODE_HINTS = {
  '0196214139299': ['illumina city mini tin', 'lumiose city mini tin', 'pokemon 13929 mini tin'],
  '0196214137158': ['perfect order booster', 'perfect order booster box', 'pokemon me03 perfect order']
};

// Optional: if you have a paid/free search API, add it here and parse it in lookupExternalBarcode_().
// For example, a Google Programmable Search endpoint or your own Sheet output.
const EXTERNAL_BARCODE_LOOKUP_URL_TEMPLATE = ''; // e.g. 'https://example.com/lookup?barcode={{BARCODE}}'
const ENABLE_UPCITEMDB_LOOKUP = true;
const ENABLE_BARCODE_MONSTER_LOOKUP = true;

function doGet(e) {
  const barcode = normalizeBarcode_(e.parameter.barcode || e.parameter.ean || e.parameter.upc || '');
  const callback = e.parameter.callback || '';
  const result = barcode ? resolveBarcode_(barcode) : { ok: false, error: 'missing barcode' };
  const body = JSON.stringify(result, null, 2);
  if (callback) {
    return ContentService.createTextOutput(callback + '(' + body + ');').setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  return ContentService.createTextOutput(body).setMimeType(ContentService.MimeType.JSON);
}

function resolveBarcode_(barcode) {
  const hints = [];
  (BARCODE_HINTS[barcode] || []).forEach(h => hints.push({ text: h, source: 'manual_hint' }));
  lookupExternalBarcode_(barcode).forEach(h => hints.push(h));
  if (!hints.length) nearbyBarcodeHints_(barcode).forEach(h => hints.push(h));
  if (!hints.length) {
    return { ok: false, barcode, reason: 'no_product_hints', message: 'Barcode valid maybe, but no product-name source found from APIs/hints. Add BARCODE_HINTS entry or configure an external lookup provider.' };
  }
  const products = loadJsonCached_(CM_URLS.NONSINGLES, 'cm_nonsingles', 6 * 3600).products || [];
  const guideRows = loadJsonCached_(CM_URLS.PRICE_GUIDE, 'cm_priceguide', 6 * 3600).priceGuides || [];
  const guide = {};
  guideRows.forEach(g => guide[g.idProduct] = g);
  const candidates = rankProducts_(hints.map(h => h.text).join(' '), products).slice(0, 12).map(r => {
    const g = guide[r.idProduct] || {};
    return {
      name: r.name,
      idProduct: r.idProduct,
      cardmarket_url: cardmarketUrl_(r),
      category: r.categoryName,
      idExpansion: r.idExpansion,
      confidence: r.confidence,
      source: 'apps_script_cardmarket_catalog_match',
      note: 'Resolved from barcode product hints + Cardmarket public product catalog.',
      price: {
        source: 'Cardmarket public daily price guide',
        from_price_eur: g.low || null,
        price_trend_eur: g.trend || null,
        avg_eur: g.avg || null,
        avg_1d_eur: g.avg1 || null,
        avg_7d_eur: g.avg7 || null,
        avg_30d_eur: g.avg30 || null
      }
    };
  });
  return { ok: true, barcode, hints, candidate_count: candidates.length, candidates };
}

function lookupExternalBarcode_(barcode) {
  const out = [];

  // 1) Built-in public UPCItemDB trial endpoint. It has sparse Pokémon coverage, but
  // when it returns a title this gives the desired barcode -> product-name bridge.
  if (ENABLE_UPCITEMDB_LOOKUP) {
    try {
      const url = 'https://api.upcitemdb.com/prod/trial/lookup?upc=' + encodeURIComponent(barcode);
      const res = UrlFetchApp.fetch(url, { muteHttpExceptions: true, followRedirects: true, headers: { Accept: 'application/json' }});
      if (res.getResponseCode() === 200) {
        const j = JSON.parse(res.getContentText());
        (j.items || []).slice(0, 5).forEach(item => {
          const text = [item.title, item.brand, item.description].filter(Boolean).join(' ');
          if (text) out.push({ text, source: 'upcitemdb' });
        });
      }
    } catch (err) {}
  }

  // 2) barcode.monster has some retail products, but also sparse TCG coverage.
  if (ENABLE_BARCODE_MONSTER_LOOKUP) {
    try {
      const url = 'https://barcode.monster/api/' + encodeURIComponent(barcode);
      const res = UrlFetchApp.fetch(url, { muteHttpExceptions: true, followRedirects: true, headers: { Accept: 'application/json' }});
      if (res.getResponseCode() === 200) {
        const j = JSON.parse(res.getContentText());
        const text = [j.description, j.company, j.title, j.name].filter(Boolean).join(' ');
        if (text) out.push({ text, source: 'barcode_monster' });
      }
    } catch (err) {}
  }

  // 3) Optional custom endpoint. This is where a paid BarcodeLookup API, your own
  // Google Sheet, or a Programmable Search JSON endpoint should be plugged in.
  if (EXTERNAL_BARCODE_LOOKUP_URL_TEMPLATE) {
    try {
      const url = EXTERNAL_BARCODE_LOOKUP_URL_TEMPLATE.replace('{{BARCODE}}', encodeURIComponent(barcode));
      const res = UrlFetchApp.fetch(url, { muteHttpExceptions: true, followRedirects: true, headers: { Accept: 'application/json,text/plain,*/*' }});
      if (res.getResponseCode() >= 200 && res.getResponseCode() < 300) {
        const txt = res.getContentText();
        try {
          const j = JSON.parse(txt);
          const candidates = j.items || j.products || j.results || [];
          candidates.slice(0, 5).forEach(item => {
            const t = item.title || item.name || item.product_name || item.description || '';
            if (t) out.push({ text: t, source: 'external_lookup' });
          });
        } catch (err) {
          if (txt) out.push({ text: txt.slice(0, 300), source: 'external_lookup_text' });
        }
      }
    } catch (err) {}
  }
  return out;
}

function nearbyBarcodeHints_(barcode) {
  const out = [];
  const raw = normalizeBarcode_(barcode);
  let best = null;
  Object.keys(BARCODE_HINTS).forEach(known => {
    if (known === raw) return;
    let shared = 0;
    for (let n = Math.min(raw.length, known.length); n >= 8; n--) {
      if (raw.slice(0, n) === known.slice(0, n)) { shared = n; break; }
    }
    if (!shared) return;
    const dist = Math.abs(Number(raw) - Number(known));
    if (shared >= 10 || (shared >= 9 && dist <= 1500)) {
      const score = shared * 100000 - dist;
      if (!best || score > best.score) best = { known, shared, dist, score };
    }
  });
  if (best) {
    BARCODE_HINTS[best.known].forEach(h => out.push({ text: h, source: 'nearby_barcode_family:' + best.known }));
  }
  return out;
}

function rankProducts_(query, products) {
  const q = normalizeText_(query);
  const qTokens = tokenSet_(q);
  const rows = [];
  products.forEach(p => {
    const nameNorm = normalizeText_(p.name || '');
    const nTokens = tokenSet_(nameNorm + ' ' + normalizeText_(p.categoryName || ''));
    let overlap = 0;
    qTokens.forEach(t => { if (nTokens.has(t)) overlap++; });
    let score = overlap / Math.max(1, qTokens.size);
    if (nameNorm.indexOf(q) >= 0 || q.indexOf(nameNorm) >= 0) score += 0.5;
    if (/mini tin/.test(q) && /mini tin/.test(nameNorm)) score += 0.35;
    if (/display|box/.test(q) && /display|booster box/.test(nameNorm)) score += 0.2;
    if (/booster/.test(q) && /booster/.test(nameNorm)) score += 0.2;
    if (score > 0.15) rows.push(Object.assign({}, p, { confidence: Math.min(0.99, Math.round(score * 100) / 100) }));
  });
  return rows.sort((a, b) => b.confidence - a.confidence || String(a.name).localeCompare(String(b.name)));
}

function normalizeText_(s) {
  return String(s || '')
    .toLowerCase()
    .normalize('NFKD').replace(/[\u0300-\u036f]/g, '')
    .replace(/optimale ordnung/g, 'perfect order')
    .replace(/illumina/g, 'lumiose')
    .replace(/mini tin box/g, 'mini tin')
    .replace(/[^a-z0-9]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function tokenSet_(s) {
  const stop = new Set(['pokemon','tcg','the','and','box','de','en']);
  return new Set(normalizeText_(s).split(' ').filter(t => t.length > 2 && !stop.has(t)));
}

function cardmarketUrl_(p) {
  const cat = categorySegment_(p.idCategory, p.categoryName);
  return 'https://www.cardmarket.com/en/Pokemon/Products/' + cat + '/' + slug_(p.name);
}

function categorySegment_(idCategory, categoryName) {
  if (Number(idCategory) === 52) return 'Boosters';
  if (Number(idCategory) === 53) return 'Booster-Boxes';
  if (Number(idCategory) === 1014) return 'Tins';
  if (/display/i.test(categoryName || '')) return 'Booster-Boxes';
  if (/booster/i.test(categoryName || '')) return 'Boosters';
  if (/tin/i.test(categoryName || '')) return 'Tins';
  return slug_(String(categoryName || 'Products').replace(/^Pokémon\s*/i, ''));
}

function slug_(name) {
  return String(name || '').replace(/:/g, '').replace(/&/g, 'and').replace(/[^A-Za-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function loadJsonCached_(url, key, ttlSeconds) {
  const cache = CacheService.getScriptCache();
  const cached = cache.get(key);
  if (cached) return JSON.parse(cached);
  const res = UrlFetchApp.fetch(url, { muteHttpExceptions: true, followRedirects: true, headers: { Accept: 'application/json' }});
  if (res.getResponseCode() !== 200) throw new Error('Fetch ' + url + ' HTTP ' + res.getResponseCode());
  const text = res.getContentText();
  // CacheService max value is ~100KB, these files are larger. Store only version marker impossible.
  // So we simply parse directly. For production, persist a filtered index in Properties/Drive.
  return JSON.parse(text);
}

function normalizeBarcode_(s) { return String(s || '').replace(/\D+/g, ''); }
