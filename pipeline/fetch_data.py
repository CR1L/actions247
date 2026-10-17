#!/usr/bin/env python3
"""Actions 24/7 - data pipeline (v1).

Pulls ONLY real data from free, keyless public sources and writes data/assets.json.
Anything that could not be fetched is stored as null and shown as "unknown" on the site.
Never invents numbers.

Sources:
  - xStocks public assets API        https://api.xstocks.fi/api/v2/public/assets
  - Ondo Global Markets token list   Binance public RWA list (type=1 = Ondo), keyless
  - DexScreener                       https://api.dexscreener.com/tokens/v1/{chain}/{addrs}
  - Yahoo Finance chart endpoint      https://query1.finance.yahoo.com/v8/finance/chart/{ticker}
  - Kraken public API                 AssetPairs + Ticker (aclass_base=tokenized_asset)
  - OKX public API                    instruments SPOT (instCategory 3 = tokenized stocks) + tickers
  - Bitpanda public API               /v3/currencies (real stocks/ETFs by ISIN; not tokens)
"""
import json, os, sys, time, datetime as dt, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
os.makedirs(os.path.join(DATA, "history"), exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (actions247 prototype; contact: none)"}
SOURCES = {}  # name -> {"ok": bool, "detail": str}

def get_json(url, timeout=25, retries=2):
    last = None
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa
            last = e
            time.sleep(1.5 * (i + 1))
    raise last

def src(name, ok, detail):
    SOURCES[name] = {"ok": ok, "detail": detail}
    print(f"[{'OK' if ok else 'FAIL'}] {name}: {detail}", file=sys.stderr)

# ---------------------------------------------------------------- xStocks
def fetch_xstocks():
    out, page = [], 0
    try:
        while True:
            d = get_json(f"https://api.xstocks.fi/api/v2/public/assets?page={page}")
            out.extend(d.get("nodes", []))
            if not d.get("page", {}).get("hasNextPage") or page > 50:
                break
            page += 1
        src("xStocks API", True, f"{len(out)} assets over {page+1} pages")
    except Exception as e:
        src("xStocks API", False, repr(e))
    return out

# ---------------------------------------------------------------- Ondo (via Binance public list)
def fetch_ondo():
    url = ("https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/"
           "market/token/rwa/stock/detail/list/ai?type=1")
    try:
        d = get_json(url)
        rows = d.get("data") or []
        src("Ondo token list (Binance public RWA list)", True, f"{len(rows)} token deployments")
        return rows
    except Exception as e:
        src("Ondo token list (Binance public RWA list)", False, repr(e))
        return []

# ---------------------------------------------------------------- DexScreener
DS_CHAIN = {"Solana": "solana", "Ethereum": "ethereum", "BinanceSmartChain": "bsc",
            "1": "ethereum", "56": "bsc"}

def fetch_dexscreener(chain_addrs):
    """chain_addrs: dict chain -> set(addresses). Returns {(chain, addr_lower): best_pair}"""
    best, n_req, n_fail = {}, 0, 0
    jobs = []
    for chain, addrs in chain_addrs.items():
        addrs = sorted(addrs)
        for i in range(0, len(addrs), 30):
            jobs.append((chain, addrs[i:i+30]))
    def run(job):
        chain, chunk = job
        time.sleep(0.25)
        return chain, chunk, get_json(f"https://api.dexscreener.com/tokens/v1/{chain}/{','.join(chunk)}")
    with ThreadPoolExecutor(4) as ex:
        futs = [ex.submit(run, j) for j in jobs]
        for f in futs:
            n_req += 1
            try:
                chain, chunk, pairs = f.result()
            except Exception:
                n_fail += 1
                continue
            for p in pairs or []:
                base = (p.get("baseToken") or {}).get("address", "")
                key = (chain, base.lower())
                liq = (p.get("liquidity") or {}).get("usd") or 0
                if p.get("priceUsd") is None:
                    continue
                cur = best.get(key)
                if cur is None or liq > ((cur.get("liquidity") or {}).get("usd") or 0):
                    best[key] = p
    src("DexScreener", n_req > n_fail, f"{n_req} batch requests, {n_fail} failed, {len(best)} tokens priced")
    return best

# ---------------------------------------------------------------- Yahoo chart (real share price)
def yahoo_symbol(t):
    return t.replace(".", "-")

def fetch_yahoo(tickers):
    res, fails = {}, []
    def one(t):
        u = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol(t)}?range=1d&interval=1d"
        try:
            m = get_json(u, retries=1)["chart"]["result"][0]["meta"]
            return t, {"price": m.get("regularMarketPrice"), "time": m.get("regularMarketTime"),
                       "currency": m.get("currency"), "name": m.get("longName") or m.get("shortName"),
                       "prev_close": m.get("chartPreviousClose"), "type": m.get("instrumentType"),
                       "exchange": m.get("fullExchangeName")}
        except Exception as e:
            return t, None
    with ThreadPoolExecutor(8) as ex:
        for t, v in ex.map(one, sorted(tickers)):
            if v and v.get("price") is not None:
                res[t] = v
            else:
                fails.append(t)
    src("Yahoo Finance chart (keyless)", len(res) > 0, f"{len(res)}/{len(tickers)} tickers priced; failed: {fails[:15]}")
    return res

def try_stooq():
    try:
        req = urllib.request.Request("https://stooq.com/q/l/?s=aapl.us&f=sd2t2c&h&e=csv", headers=UA)
        body = urllib.request.urlopen(req, timeout=15).read().decode()
        ok = body.lower().startswith("symbol")
        src("Stooq CSV (fallback, tested only)", ok, "works" if ok else "endpoint returned an HTML error page, not used")
    except Exception as e:
        src("Stooq CSV (fallback, tested only)", False, repr(e))

# ---------------------------------------------------------------- Exchanges
def fetch_kraken():
    try:
        pairs = get_json("https://api.kraken.com/0/public/AssetPairs?aclass_base=tokenized_asset")["result"]
        usd = sorted({v["altname"] for v in pairs.values() if v.get("wsname", "").endswith("/USD")})
        tick = {}
        for i in range(0, len(usd), 50):
            tick.update(get_json("https://api.kraken.com/0/public/Ticker?asset_class=tokenized_asset&pair="
                                 + ",".join(usd[i:i+50])).get("result", {}))
        out = {}
        for k, v in pairs.items():
            base = v.get("wsname", "").split("/")[0]  # e.g. TSLAx
            if v.get("aclass_base") != "tokenized_asset" or not base:
                continue
            rec = out.setdefault(base, {"pairs": [], "last": None})
            if v["wsname"] not in rec["pairs"]:
                rec["pairs"].append(v["wsname"])
            t = tick.get(v["altname"]) or {}
            if v["wsname"].endswith("/USD") and t:
                # mid of best bid/ask = live quote; last trade can be hours old on thin books
                try:
                    bid, ask = float(t["b"][0]), float(t["a"][0])
                    if bid > 0 and ask > 0 and (ask - bid) / ask < 0.05:
                        rec["last"], rec["price_kind"] = (bid + ask) / 2, "mid"
                except Exception:
                    pass
                if rec["last"] is None and t.get("c") and float(t["c"][0]) > 0:
                    rec["last"], rec["price_kind"] = float(t["c"][0]), "last trade"
        src("Kraken public API", True, f"{len(out)} tokenized assets listed, {sum(1 for r in out.values() if r['last'])} with a USD last price")
        return out
    except Exception as e:
        src("Kraken public API", False, repr(e))
        return {}

def fetch_okx():
    try:
        ins = get_json("https://www.okx.com/api/v5/public/instruments?instType=SPOT")["data"]
        tick = {x["instId"]: x for x in get_json("https://www.okx.com/api/v5/market/tickers?instType=SPOT")["data"]}
        out = {}
        for i in ins:
            if i.get("instCategory") != "3":
                continue
            base = i["baseCcy"]  # e.g. XTSLA
            und = base[1:]
            t = tick.get(i["instId"]) or {}
            rec = out.setdefault(und, {"okx_symbol": base, "pairs": [], "last": None, "list_time": None, "state": i.get("state")})
            rec["pairs"].append(i["instId"])
            if i["instId"].endswith("-USDT") and t:
                try:
                    bid, ask = float(t.get("bidPx") or 0), float(t.get("askPx") or 0)
                    if bid > 0 and ask > 0 and (ask - bid) / ask < 0.05:
                        rec["last"], rec["price_kind"] = (bid + ask) / 2, "mid"
                except Exception:
                    pass
                if rec["last"] is None and t.get("last") and float(t["last"]) > 0:
                    rec["last"], rec["price_kind"] = float(t["last"]), "last trade"
            lt = int(i["listTime"]) if i.get("listTime") else None
            if lt and (rec["list_time"] is None or lt < rec["list_time"]):
                rec["list_time"] = lt
        src("OKX public API", True, f"{len(out)} tokenized stocks (instCategory 3)")
        return out
    except Exception as e:
        src("OKX public API", False, repr(e))
        return {}

def fetch_bitpanda():
    try:
        d = get_json("https://api.bitpanda.com/v3/currencies")["data"]["attributes"]
        isins = {}
        for grp in ("stocks", "etfs"):
            for x in d.get(grp, []):
                a = x["attributes"]
                if a.get("isin"):
                    isins[a["isin"]] = {"symbol": a.get("symbol"), "name": a.get("name"), "group": grp}
        src("Bitpanda public API", True, f"{len(isins)} real stocks/ETFs with ISIN (not tokens)")
        return isins
    except Exception as e:
        src("Bitpanda public API", False, repr(e))
        return {}

# ---------------------------------------------------------------- main
def main():
    now = dt.datetime.now(dt.timezone.utc)
    xs = fetch_xstocks()
    ondo_rows = fetch_ondo()
    kraken, okx, bitpanda = fetch_kraken(), fetch_okx(), fetch_bitpanda()

    assets = {}
    US_MICS = {"XNAS", "XNYS", "ARCX", "BATS", "XASE", "XNGS", "XNMS", "XNCM"}
    skipped_non_us = 0
    for n in xs:
        sym = n["symbol"]
        mic = (((n.get("underlying") or {}).get("exchange") or {}).get("mic"))
        if mic not in US_MICS:  # v1 scope: US-listed underlyings only
            skipped_non_us += 1
            continue
        deps = [{"network": d["network"], "address": d["address"]} for d in n.get("deployments", [])]
        assets[sym] = {
            "id": sym.lower().replace(".", "-"), "symbol": sym, "issuer_family": "xStocks",
            "issuer_entity": "Backed Assets (JE) Limited", "underlying": n.get("underlyingSymbol"),
            "underlying_isin": n.get("underlyingIsin"), "token_isin": n.get("isin"),
            "name": (n.get("name") or "").replace(" xStock", ""),
            "exchange": ((n.get("underlying") or {}).get("exchange") or {}).get("abbreviation"),
            "trading_halted": n.get("isTradingHalted"), "multiplier": None,
            "chains": sorted({d["network"] for d in deps}), "deployments": deps,
        }
    for r in ondo_rows:
        sym = r["symbol"]
        a = assets.setdefault(sym, {
            "id": sym.lower().replace(".", "-"), "symbol": sym, "issuer_family": "Ondo Global Markets",
            "issuer_entity": "Ondo Global Markets (BVI) Limited", "underlying": r.get("ticker"),
            "underlying_isin": None, "token_isin": None, "name": None, "exchange": None,
            "trading_halted": None, "chains": [], "deployments": [],
            "multiplier": None, "ondo_asset_type": r.get("assetType")})
        chain = {"1": "Ethereum", "56": "BinanceSmartChain", "CT_501": "Solana"}.get(str(r.get("chainId")), str(r.get("chainId")))
        a["deployments"].append({"network": chain, "address": r.get("contractAddress")})
        a["chains"] = sorted(set(a["chains"]) | {chain})
        try:
            a["multiplier"] = float(r["multiplier"])
        except Exception:
            pass

    # ticker -> ISIN map from xStocks (lets us match Ondo tokens to Bitpanda by ISIN)
    isin_by_ticker = {a["underlying"]: a["underlying_isin"] for a in assets.values()
                      if a["issuer_family"] == "xStocks" and a.get("underlying_isin")}
    for a in assets.values():
        if not a.get("underlying_isin") and a.get("underlying") in isin_by_ticker:
            a["underlying_isin"] = isin_by_ticker[a["underlying"]]
            a["underlying_isin_note"] = "ISIN taken from the xStocks record of the same ticker"

    # DexScreener lookups: Solana for xStocks (most liquid), Ethereum/BSC for both
    want = {}
    for a in assets.values():
        for d in a["deployments"]:
            c = DS_CHAIN.get(d["network"])
            if c and d.get("address"):
                want.setdefault(c, set()).add(d["address"])
    ds = fetch_dexscreener(want)

    try_stooq()
    yh = fetch_yahoo({a["underlying"] for a in assets.values() if a.get("underlying")})

    for a in assets.values():
        best = None
        for d in a["deployments"]:
            c = DS_CHAIN.get(d["network"])
            p = ds.get((c, (d.get("address") or "").lower())) if c else None
            if p and (best is None or ((p.get("liquidity") or {}).get("usd") or 0) > ((best.get("liquidity") or {}).get("usd") or 0)):
                best = p
        if best:
            a["dex_price"] = float(best["priceUsd"])
            a["dex"] = {"name": "DexScreener", "chain": best.get("chainId"), "dex": best.get("dexId"),
                                       "pair_url": best.get("url"),
                                       "liquidity_usd": (best.get("liquidity") or {}).get("usd"),
                                       "volume_24h_usd": (best.get("volume") or {}).get("h24")}
            if not a.get("name"):
                nm = (best.get("baseToken") or {}).get("name") or ""
                a["name"] = nm.replace(" (Ondo Tokenized)", "").replace(" xStock", "") or None
        else:
            a["dex_price"], a["dex"] = None, None
        y = yh.get(a.get("underlying"))
        a["share_price"] = y["price"] if y else None
        a["share_price_time"] = y["time"] if y else None
        a["share_currency"] = y["currency"] if y else None
        a["share_exchange_name"] = y["exchange"] if y else None
        a["instrument_type"] = y["type"] if y else None
        if y and not a.get("name"):
            a["name"] = y["name"]
        if y and a["issuer_family"] == "Ondo Global Markets" and y.get("name"):
            a["name"] = a["name"] or y["name"]
        # platforms
        plats = []
        if a["issuer_family"] == "xStocks":
            k = kraken.get(a["symbol"])
            if k:
                plats.append({"platform": "Kraken", "listed": True, "product": a["symbol"], "pairs": k["pairs"],
                              "last_usd": k["last"], "price_kind": k.get("price_kind"), "type": "token"})
            o = okx.get(a["underlying"].replace(".", "")) if a.get("underlying") else None
            if o:
                plats.append({"platform": "OKX", "listed": True, "product": o["okx_symbol"], "pairs": o["pairs"],
                              "last_usd": o["last"], "price_kind": o.get("price_kind"), "type": "token (OKX Unified Tokenized Stock, backed by xStocks)",
                              "list_time": o["list_time"]})
        isin = a.get("underlying_isin")
        if isin and isin in bitpanda:
            plats.append({"platform": "Bitpanda", "listed": True, "product": bitpanda[isin]["symbol"],
                          "type": "real share/ETF (not a token)", "last_usd": None})
        a["platforms"] = plats

        # token price: prefer a regulated exchange order book (Kraken, then OKX), else the deepest DEX pool
        a["token_price"], a["token_price_source"] = None, None
        for pl in plats:
            if pl["platform"] in ("Kraken", "OKX") and pl.get("last_usd"):
                a["token_price"] = pl["last_usd"]
                a["token_price_source"] = {"name": pl["platform"], "kind": pl.get("price_kind"), "detail": next((x for x in pl["pairs"] if x.endswith(("/USD", "-USDT"))), pl["pairs"][0])}
                break
        if a["token_price"] is None and a.get("dex_price"):
            a["token_price"] = a["dex_price"]
            a["token_price_source"] = {"name": "DexScreener", "detail": f'{a["dex"]["dex"]} on {a["dex"]["chain"]}'}
        # premium vs fair value (Ondo tokens accrue dividends via multiplier; xStocks rebase, so 1:1)
        prem = None
        if a["token_price"] and a["share_price"] and a["share_currency"] == "USD":
            fair = a["share_price"] * (a["multiplier"] or 1.0)
            prem = (a["token_price"] / fair - 1) * 100
        a["premium_pct"] = round(prem, 3) if prem is not None else None
        liq = (a["dex"] or {}).get("liquidity_usd") or 0
        a["low_liquidity"] = a["token_price_source"] is not None and a["token_price_source"]["name"] == "DexScreener" and liq < 10000
        # |gap| > 5 %: almost always a data artefact (stock split not yet reflected, thin pool, ADR ratio)
        a["suspect_gap"] = prem is not None and abs(prem) > 5

    # drop Ondo portfolio / yield tokens (not single stocks): no asset type and no share price found
    for k in [k for k, a in assets.items() if a["issuer_family"] == "Ondo Global Markets"
              and a.get("ondo_asset_type") in (None, 4) and a["share_price"] is None]:
        del assets[k]

    out = {"generated_at": now.isoformat(), "sources": SOURCES,
           "counts": {"assets": len(assets), "skipped_non_us_xstocks": skipped_non_us,
                      "with_token_price": sum(1 for a in assets.values() if a["token_price"]),
                      "with_share_price": sum(1 for a in assets.values() if a["share_price"]),
                      "with_premium": sum(1 for a in assets.values() if a["premium_pct"] is not None),
                      "on_kraken": sum(1 for a in assets.values() if any(p["platform"] == "Kraken" for p in a["platforms"])),
                      "on_okx": sum(1 for a in assets.values() if any(p["platform"] == "OKX" for p in a["platforms"])),
                      "on_bitpanda_real_share": sum(1 for a in assets.values() if any(p["platform"] == "Bitpanda" for p in a["platforms"]))},
           "okx_listings": [{"okx_symbol": v["okx_symbol"], "underlying": k, "list_time": v["list_time"], "state": v["state"]}
                            for k, v in okx.items()],
           "assets": sorted(assets.values(), key=lambda a: (a["underlying"] or "", a["issuer_family"]))}
    with open(os.path.join(DATA, "assets.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    with open(os.path.join(DATA, "history", now.strftime("%Y-%m-%d") + ".json"), "w") as f:
        json.dump({"generated_at": out["generated_at"],
                   "symbols": sorted(assets.keys()),
                   "premiums": {k: v["premium_pct"] for k, v in assets.items()}}, f)
    print(json.dumps(out["counts"], indent=1))

if __name__ == "__main__":
    main()
