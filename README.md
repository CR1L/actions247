# Actions 24/7

Live at https://actions247.fr (GitHub Pages). `ci/update-and-deploy.yml` (to be moved to `.github/workflows/`; the deploy token lacked the `workflow` permission) reruns `fetch_data.py` + `check_data.py` + `build_site.py` every 4 hours and redeploys.

Tracker of tokenized US stocks for EU residents (FR default, EN toggle).

## Run
```bash
cd /workspace/actions247
python3 pipeline/fetch_data.py       # ~4 min, pulls real data -> data/assets.json (+ data/history/YYYY-MM-DD.json)
python3 pipeline/build_site.py       # static site -> site/ (index, methodologie, actif/<token>.html)
python3 pipeline/build_newsletter.py # French draft -> newsletter/numero-001-brouillon.md (ISSUE=2 for the next one)
cd site && python3 -m http.server 8247 --bind 127.0.0.1   # http://127.0.0.1:8247/
.venv/bin/python pipeline/screenshots.py                 # full-page screenshots -> screenshots/
```
Python stdlib only for the pipeline (no keys). Playwright (in .venv) only for screenshots, using /usr/bin/google-chrome.

## Data sources (all free, keyless)
| Source | Use | Status |
|---|---|---|
| xStocks public API `api.xstocks.fi/api/v2/public/assets` | token list, ISINs, chains, contracts | works (1460 assets; v1 keeps the US-listed ones) |
| Binance public RWA list (type=1 = Ondo) | Ondo Global Markets token list + dividend multiplier | works (Ondo's own API needs a key) |
| DexScreener `tokens/v1` | on-chain token prices, deepest pool, liquidity | works |
| Yahoo Finance chart `v8/finance/chart` | real share price | works (v7 quote endpoint is blocked) |
| Stooq CSV | fallback share price | failed (404), not used |
| Kraken `AssetPairs?aclass_base=tokenized_asset` + `Ticker?asset_class=tokenized_asset` | availability + bid/ask | works |
| OKX `public/instruments` (instCategory 3) + `market/tickers` | availability + bid/ask + listing dates | works |
| Bitpanda `v3/currencies` | real stocks/ETFs by ISIN (Bitpanda has no tokens) | works |

## Rules baked in
- Only fetched numbers are shown; unknowns are "n.d." / "n/a".
- Token price = Kraken/OKX bid/ask mid if available, else deepest DEX pool. Gap > 5 % flagged ⚠ (data artefact likely); DEX pools < $10k flagged.
- Ondo gap uses the dividend multiplier.
- Affiliate slots: `AFFILIATE` dict in `pipeline/build_site.py` (all None today, links go to official homepages, marked `data-affiliate-slot="TODO"`).
- Newsletter form is a placeholder (no service wired).

## SEO (build_site.py)
- FR pages at `/`, EN pages at `/en/` (same paths), each with canonical + hreflang fr/en/x-default, unique title/description, Open Graph + Twitter card (`site/assets/og.png`), JSON-LD (WebSite + Dataset on home, FinancialProduct + BreadcrumbList on token pages).
- `sitemap.xml` (all FR/EN URLs with alternates) and `robots.txt` generated on every build. Site URL constant: `SITE_URL = "https://actions247.fr"`.
