#!/usr/bin/env python3
"""Builds the static site in site/ from data/assets.json (FR default, EN toggle)."""
import json, os, html, datetime as dt
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
D = json.load(open(os.path.join(ROOT, "data", "assets.json")))
LUX = ZoneInfo("Europe/Luxembourg")

# Affiliate slots: Cyril has not signed up yet. Put the referral URL here once approved.
AFFILIATE = {
    "Kraken":   {"url": None, "fallback": "https://www.kraken.com/"},
    "OKX":      {"url": None, "fallback": "https://www.okx.com/en-eu"},
    "Bitpanda": {"url": None, "fallback": "https://www.bitpanda.com/"},
}
CHAIN = {"BinanceSmartChain": "BNB Chain", "Ethereum": "Ethereum", "Solana": "Solana", "Arbitrum": "Arbitrum",
         "Mantle": "Mantle", "Ink": "Ink", "Tron": "TRON", "TRON": "TRON", "TON": "TON", "XLayer": "X Layer",
         "Optimism": "Optimism", "Monad": "Monad", "Base": "Base"}
e = html.escape

SITE_URL = "https://actions247.fr"
LANG = "fr"          # language currently being built ("fr" -> /, "en" -> /en/)
OG_IMAGE = SITE_URL + "/assets/og.png"
PUBLISHER = {"@type": "Person", "name": "Cyril-Olivier Canet", "email": "cyril@mail.grokbot.com"}

def bi(fr, en, tag="span"):
    # each page is built once per language, so only that language's text is emitted
    return fr if LANG == "fr" else en

def P():
    """root path prefix for internal page links in the current language"""
    return "/" if LANG == "fr" else "/en/"

def url_for(lang, path):
    """absolute https URL of a page; path like '' (home), 'methodologie.html', 'actif/x.html'"""
    return SITE_URL + ("/" if lang == "fr" else "/en/") + path

def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + '</script>'

def lux_time(iso_or_ts):
    if iso_or_ts is None:
        return None
    t = dt.datetime.fromtimestamp(iso_or_ts, dt.timezone.utc) if isinstance(iso_or_ts, (int, float)) else dt.datetime.fromisoformat(iso_or_ts)
    return t.astimezone(LUX).strftime("%d/%m/%Y %H:%M")

GEN = lux_time(D["generated_at"])

def aff_link(platform, label_fr, label_en, cls="btn"):
    a = AFFILIATE[platform]
    url = a["url"] or a["fallback"]
    note = "" if a["url"] else ' data-affiliate-slot="TODO"'
    return (f'<a class="{cls}" href="{e(url)}" target="_blank" rel="sponsored nofollow noopener"{note}>'
            f'{bi(label_fr, label_en)}</a>')

def page(title, body, path="", desc="", ld=None, og_type="website"):
    fr_url, en_url = url_for("fr", path), url_for("en", path)
    canon = fr_url if LANG == "fr" else en_url
    ld_html = "".join(jsonld(x) for x in (ld or []))
    return f"""<!doctype html>
<html lang="{LANG}" data-lang="{LANG}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon}">
<link rel="alternate" hreflang="fr" href="{fr_url}">
<link rel="alternate" hreflang="en" href="{en_url}">
<link rel="alternate" hreflang="x-default" href="{fr_url}">
<meta property="og:site_name" content="Actions 24/7">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{OG_IMAGE}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:locale" content="{'fr_FR' if LANG == 'fr' else 'en_US'}">
<meta property="og:locale:alternate" content="{'en_US' if LANG == 'fr' else 'fr_FR'}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{OG_IMAGE}">
<link rel="stylesheet" href="/assets/style.css">
{ld_html}
</head><body>
<header class="top"><div class="wrap">
<a class="logo" href="{P()}">Actions <b>24/7</b></a>
<nav><a href="{P()}">{bi("Tableau","Table")}</a>
<a href="{P()}methodologie.html">{bi("Méthode et sources","Method &amp; sources")}</a>
<a href="{P()}#newsletter">Newsletter</a>
<span class="lang"><a class="lb{' on' if LANG == 'fr' else ''}" href="{fr_url}" hreflang="fr">FR</a><a class="lb{' on' if LANG == 'en' else ''}" href="{en_url}" hreflang="en">EN</a></span></nav>
</div></header>
<div class="wrap">
<div class="banner">{bi(
 "<strong>Information, pas un conseil en investissement.</strong> Les actions tokenisées ne sont pas des actions : elles ne donnent en général ni propriété directe ni droit de vote. Non destiné aux personnes américaines (US persons). La disponibilité dans l'UE dépend de votre pays et peut changer à tout moment.",
 "<strong>Information, not investment advice.</strong> Tokenized stocks are not shares: they generally give no direct ownership and no voting rights. Not for US persons. EU availability depends on your country and can change at any time.")}</div>
{body}
</div>
<footer><div class="wrap">
<p>{bi(
 "Actions 24/7 est un site d'information indépendant. Rien ici n'est un conseil en investissement, une recommandation ou une offre. Les produits cités sont complexes et risqués ; vous pouvez perdre tout votre capital. Ils ne sont pas proposés aux résidents des États-Unis ni aux US persons. Les données proviennent de sources publiques gratuites et peuvent être incomplètes, en retard ou fausses : vérifiez toujours auprès de l'émetteur et de la plateforme.",
 "Actions 24/7 is an independent information site. Nothing here is investment advice, a recommendation or an offer. The products listed are complex and risky; you can lose all your capital. They are not offered to US residents or US persons. Data comes from free public sources and may be incomplete, delayed or wrong: always check with the issuer and the platform.")}</p>
<p>{bi("Liens partenaires : certains liens vers des plateformes pourront être des liens d'affiliation. Ils ne changent ni les données ni l'ordre d'affichage.",
 "Partner links: some platform links may become affiliate links. They never change the data or the ranking.")}</p>
<p>{bi("Données mises à jour le","Data updated")} {GEN} (heure de Luxembourg / Luxembourg time).</p>
<p><a href="{P()}mentions-legales.html">{bi("Mentions légales","Legal notice")}</a></p>
</div></footer>
<script src="/assets/i18n.js"></script>
</body></html>"""

# ------------------------------------------------------------------ slim data for the table
def slim(a):
    return {"id": a["id"], "s": a["symbol"], "u": a["underlying"], "n": a.get("name"), "f": a["issuer_family"],
            "c": [CHAIN.get(c, c) for c in a["chains"]], "tp": a["token_price"],
            "ts": (a["token_price_source"] or {}).get("name"), "sp": a["share_price"],
            "pr": a["premium_pct"], "sg": a.get("suspect_gap"), "ll": a.get("low_liquidity"),
            "p": [p["platform"] for p in a["platforms"]], "it": a.get("instrument_type")}

os.makedirs(os.path.join(SITE, "actif"), exist_ok=True)
with open(os.path.join(SITE, "assets", "data.js"), "w") as f:
    f.write("window.A247=" + json.dumps({"g": GEN, "a": [slim(a) for a in D["assets"]]}, ensure_ascii=False, separators=(",", ":")) + ";")

def build(lang):
    global LANG
    LANG = lang
    OUT = SITE if lang == "fr" else os.path.join(SITE, "en")
    os.makedirs(os.path.join(OUT, "actif"), exist_ok=True)
    C = D["counts"]
    priced = C["with_premium"]

    # ------------------------------------------------------------------ home
    home = f"""
    <section class="hero">
    <h1>{bi("Toutes les actions américaines tokenisées, au même endroit","Every tokenized US stock, in one place")}</h1>
    <p>{bi("Tesla, Nvidia, l'indice S&amp;P 500… en token, échangeables 24h/24. Pour chaque token : qui l'émet, sur quelle blockchain, son prix face à la vraie action, et où un résident de l'UE peut l'acheter.",
    "Tesla, Nvidia, the S&amp;P 500… as tokens that trade around the clock. For each token: who issues it, which blockchain, its price versus the real share, and where an EU resident can buy it.")}</p>
    </section>
    <div class="stats">
    <div class="stat"><div class="n">{C['assets']}</div><div class="l">{bi("tokens suivis (xStocks + Ondo)","tokens tracked (xStocks + Ondo)")}</div></div>
    <div class="stat"><div class="n">{priced}</div><div class="l">{bi("avec écart de prix calculé","with price gap computed")}</div></div>
    <div class="stat"><div class="n">{C['on_kraken']}</div><div class="l">{bi("listés sur Kraken","listed on Kraken")}</div></div>
    <div class="stat"><div class="n">{C['on_okx']}</div><div class="l">{bi("listés sur OKX","listed on OKX")}</div></div>
    <div class="stat"><div class="n">{GEN}</div><div class="l">{bi("dernière mise à jour (Luxembourg)","last update (Luxembourg)")}</div></div>
    </div>
    <div class="controls">
    <input type="search" id="q" placeholder="Rechercher : TSLA, Nvidia, SPY…" data-ph-en="Search: TSLA, Nvidia, SPY…">
    <select id="fam"><option value="">{'Tous les émetteurs'}</option><option>xStocks</option><option>Ondo Global Markets</option></select>
    <select id="plat"><option value="">Toutes les plateformes</option><option>Kraken</option><option>OKX</option><option>Bitpanda</option></select>
    <label><input type="checkbox" id="onlyp" checked> {bi("Seulement les tokens avec un prix","Only tokens with a price")}</label>
    <span class="small" id="cnt"></span>
    </div>
    <div style="overflow-x:auto">
    <table id="t"><thead><tr>
    <th data-k="u">{bi("Action","Stock")}</th><th data-k="n" class="hide-m">{bi("Société","Company")}</th>
    <th data-k="s">Token</th><th data-k="f">{bi("Émetteur","Issuer")}</th><th data-k="c" class="hide-m">{bi("Blockchains","Chains")}</th>
    <th data-k="tp" class="num">{bi("Prix token","Token price")}</th><th data-k="sp" class="num">{bi("Prix action","Share price")}</th>
    <th data-k="pr" class="num">{bi("Écart","Gap")}</th><th data-k="p">{bi("Où l'acheter (UE)","Where to buy (EU)")}</th>
    </tr></thead><tbody></tbody></table></div>
    <p class="small">{bi(
    "Prix du token : milieu de la fourchette achat/vente du carnet d'ordres Kraken ou OKX si disponible, sinon le pool DEX le plus liquide (DexScreener). Prix de l'action : Yahoo Finance (prix du marché régulier, peut être en retard). Écart = prix du token ÷ (prix de l'action × multiplicateur de dividendes pour Ondo) − 1. ⚠ = écart supérieur à 5 %, presque toujours un artefact (division d'action non encore prise en compte, pool peu liquide, ratio ADR) : à vérifier. « n.d. » = donnée non disponible dans nos sources, jamais estimée.",
    "Token price: Kraken or OKX order-book bid/ask mid when available, otherwise the most liquid DEX pool (DexScreener). Share price: Yahoo Finance (regular market price, may be delayed). Gap = token price ÷ (share price × dividend multiplier for Ondo) − 1. ⚠ = gap above 5 %, almost always a data artefact (stock split not yet reflected, thin pool, ADR ratio): check it. “n/a” = not available in our sources, never estimated.")}</p>

    <section class="card" id="newsletter" style="margin-top:24px">
    <h2>{bi("La newsletter du week-end","The weekend newsletter")}</h2>
    <p class="small">{bi("Chaque semaine : les nouveaux tokens listés, les plus gros écarts de prix du week-end, les changements de disponibilité en Europe. Gratuit, en français.","Every week: new listings, the biggest weekend price gaps, EU availability changes. Free.")}</p>
    <form class="news" onsubmit="event.preventDefault();this.innerHTML='<p>'+(document.documentElement.dataset.lang==='en'?'Thanks! (Demo: sign-up is not active yet, nothing was sent.)':'Merci ! (Démo : l\\'inscription n\\'est pas encore active, rien n\\'a été envoyé.)')+'</p>'">
    <input type="email" required placeholder="votre@email.fr"><button type="submit">{bi("Je m'inscris","Subscribe")}</button>
    </form>
    <p class="small">{bi("Prototype : ce formulaire n'est relié à aucun service pour l'instant.","Prototype: this form is not connected to any service yet.")}</p>
    </section>
    <script src="/assets/data.js"></script><script src="/assets/table.js"></script>
    """
    home_title = bi("Actions tokenisées : acheter Tesla, Nvidia… en token (xStocks, Ondo) depuis l'Europe | Actions 24/7",
                    "Tokenized stocks: buy Tesla, Nvidia… as tokens (xStocks, Ondo) from Europe | Actions 24/7")
    home_desc = bi(f"Les {C['assets']} actions américaines tokenisées (xStocks, Ondo) : prix 24h/24, écart avec la vraie action, émetteur, et où les acheter depuis l'UE (Kraken, OKX). Mis à jour toutes les 4 heures.",
                   f"All {C['assets']} tokenized US stocks (xStocks, Ondo): 24/7 prices, gap to the real share, issuer, and where to buy them from the EU (Kraken, OKX). Updated every 4 hours.")
    website_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": "Actions 24/7", "url": url_for(LANG, ""),
                  "inLanguage": LANG, "description": home_desc, "publisher": PUBLISHER}
    dataset_ld = {"@context": "https://schema.org", "@type": "Dataset",
                  "name": bi("Actions américaines tokenisées (xStocks, Ondo) : prix, écarts et disponibilité dans l'UE",
                             "Tokenized US stocks (xStocks, Ondo): prices, gaps and EU availability"),
                  "description": home_desc, "url": url_for(LANG, ""), "inLanguage": LANG,
                  "creator": PUBLISHER, "dateModified": D["generated_at"], "isAccessibleForFree": True,
                  "keywords": ["actions tokenisées", "tokenized stocks", "xStocks", "Ondo Global Markets", "Kraken", "OKX"],
                  "variableMeasured": ["token price (USD)", "share price (USD)", "premium/discount (%)", "EU platform availability"],
                  "isBasedOn": ["https://xstocks.fi", "https://ondo.finance", "https://www.kraken.com", "https://www.okx.com", "https://finance.yahoo.com", "https://dexscreener.com"],
                  "distribution": [{"@type": "DataDownload", "encodingFormat": "application/javascript", "contentUrl": SITE_URL + "/assets/data.js"}]}
    open(os.path.join(OUT, "index.html"), "w").write(page(home_title, home, "", home_desc, [website_ld, dataset_ld]))

    # ------------------------------------------------------------------ asset pages
    OWN = {
     "xStocks": (
      "<p>Un xStock est un <strong>certificat de suivi</strong> (titre de créance au porteur) émis par <strong>Backed Assets (JE) Limited</strong>, une société de Jersey. Il suit le prix de l'action et est adossé 1:1 à des actions détenues chez des dépositaires réglementés, sur des comptes séparés.</p>"
      "<ul><li>Vous <strong>ne possédez pas l'action</strong> elle-même.</li><li><strong>Aucun droit de vote</strong>, aucun droit d'information auprès de la société.</li>"
      "<li>Les dividendes et divisions d'actions sont reflétés par un ajustement automatique du nombre de tokens (rebasing).</li>"
      "<li>Risque émetteur et risque de plateforme en plus du risque de l'action.</li>"
      "<li>Offre dans l'EEE sous un prospectus de base approuvé par la FMA du Liechtenstein, via des distributeurs agréés. Pas proposé aux États-Unis, au Canada, au Royaume-Uni ni en Australie (selon Kraken).</li></ul>",
      "<p>An xStock is a <strong>tracker certificate</strong> (bearer debt instrument) issued by <strong>Backed Assets (JE) Limited</strong>, a Jersey company. It tracks the share price and is backed 1:1 by shares held with regulated custodians in segregated accounts.</p>"
      "<ul><li>You <strong>do not own the share</strong> itself.</li><li><strong>No voting rights</strong>, no information rights towards the company.</li>"
      "<li>Dividends and stock splits are reflected by automatically adjusting token balances (rebasing).</li>"
      "<li>Issuer and platform risk on top of the stock's own risk.</li>"
      "<li>Offered in the EEA under a base prospectus approved by Liechtenstein's FMA, through licensed distributors. Not offered in the US, Canada, UK or Australia (per Kraken).</li></ul>",
      [("Documentation xStocks", "https://docs.xstocks.fi/docs/product-legal-overview"), ("Kraken : risques xStocks", "https://www.kraken.com/legal/xstocks")]),
     "Ondo Global Markets": (
      "<p>Un token Ondo (Ondo Global Markets, aujourd'hui « Ondo Stocks ») est un <strong>titre de créance</strong> de droit suisse émis par <strong>Ondo Global Markets (BVI) Limited</strong>, une société des îles Vierges britanniques. Sa valeur suit l'action, dividendes inclus, et il est adossé 1:1 (plus une marge) à des actions détenues via un courtier agréé.</p>"
      "<ul><li>Vous <strong>ne possédez pas l'action</strong> et n'avez <strong>aucun droit de vote</strong>.</li>"
      "<li>Les dividendes sont réinvestis via un <strong>multiplicateur</strong> : un token peut valoir un peu plus d'une action. Nous en tenons compte dans l'écart affiché.</li>"
      "<li>Interdit aux US persons. Dans l'EEE, certains tokens sont ouverts aux particuliers sous un prospectus approuvé au Liechtenstein, d'autres seulement aux investisseurs professionnels.</li></ul>",
      "<p>An Ondo token (Ondo Global Markets, now “Ondo Stocks”) is a Swiss-law <strong>debt security</strong> issued by <strong>Ondo Global Markets (BVI) Limited</strong>, a British Virgin Islands company. Its value tracks the share including dividends, and it is backed 1:1 (plus a buffer) by shares held through a licensed broker-dealer.</p>"
      "<ul><li>You <strong>do not own the share</strong> and have <strong>no voting rights</strong>.</li>"
      "<li>Dividends are reinvested via a <strong>multiplier</strong>: one token can be worth slightly more than one share. The gap shown accounts for it.</li>"
      "<li>Prohibited for US persons. In the EEA some tokens are open to retail investors under a Liechtenstein-approved prospectus, others only to professional investors.</li></ul>",
      [("Ondo : cadre légal", "https://docs.ondo.finance/ondo-stocks/legal-and-regulatory"), ("Ondo : éligibilité", "https://docs.ondo.finance/ondo-stocks/eligibility")]),
    }

    def money(v):
        return f"{v:,.2f} $".replace(",", " ").replace(".", ",") if v is not None else '<span class="unk">n.d.</span>'
    def money_en(v):
        return f"${v:,.2f}" if v is not None else '<span class="unk">n/a</span>'
    def pct(v):
        if v is None:
            return bi('<span class="unk">n.d.</span>', '<span class="unk">n/a</span>')
        cls = "pos" if v >= 0 else "neg"
        s = f"{v:+.2f}"
        return bi(f'<span class="{cls}">{s.replace(".", ",")} %</span>', f'<span class="{cls}">{s}%</span>')

    for a in D["assets"]:
        fam = a["issuer_family"]
        own_fr, own_en, links = OWN[fam]
        name = a.get("name") or a["underlying"]
        plats = a["platforms"]
        plat_html = ""
        for p in plats:
            if p["platform"] == "Bitpanda":
                desc = bi(f"Pas de token : Bitpanda propose la <strong>vraie action</strong> ({e(p['product'])}), avec droits économiques complets. Produit différent, utile pour comparer.",
                          f"No token: Bitpanda offers the <strong>real share</strong> ({e(p['product'])}) with full economic rights. A different product, useful for comparison.")
            elif p["platform"] == "OKX":
                desc = bi(f"Listé sous le nom <strong>{e(p['product'])}</strong> (Unified Tokenized Stock adossé aux xStocks), paires : {e(', '.join(p['pairs']))}. Prix : {money(p.get('last_usd'))}. Proposé dans l'UE via OKX Europe Markets (Malte, MiFID II), selon votre éligibilité.",
                          f"Listed as <strong>{e(p['product'])}</strong> (Unified Tokenized Stock backed by xStocks), pairs: {e(', '.join(p['pairs']))}. Price: {money_en(p.get('last_usd'))}. Offered in the EU via OKX Europe Markets (Malta, MiFID II), subject to eligibility.")
            else:
                desc = bi(f"Listé : {e(', '.join(p['pairs']))}. Prix : {money(p.get('last_usd'))}. Accessible aux particuliers dans certains pays seulement : vérifiez la liste de Kraken pour votre pays.",
                          f"Listed: {e(', '.join(p['pairs']))}. Price: {money_en(p.get('last_usd'))}. Retail access in selected countries only: check Kraken's country list.")
            plat_html += f'<div style="margin:10px 0"><span class="pl {p["platform"]}">{p["platform"]}</span> {desc}<br>{aff_link(p["platform"], "Voir sur " + p["platform"], "Open " + p["platform"], "btn ghost")}</div>'
        if not plat_html:
            plat_html = bi("<p>Aucune plateforme vérifiée dans nos sources (Kraken, OKX, Bitpanda) pour ce token. Il peut exister ailleurs (portefeuilles, DEX, autres plateformes) : non vérifié.</p>",
                           "<p>No platform verified in our sources (Kraken, OKX, Bitpanda) for this token. It may exist elsewhere (wallets, DEXs, other venues): not verified.</p>")
        dex = a.get("dex")
        flags = ""
        if a.get("suspect_gap"):
            flags += f'<p class="warn">⚠ {bi("Écart supérieur à 5 % : probablement un artefact de données (division d'action, pool peu liquide, ratio). Ne pas s'y fier sans vérifier.","Gap above 5 %: probably a data artefact (stock split, thin pool, ratio). Do not rely on it without checking.")}</p>'
        if a.get("low_liquidity"):
            flags += f'<p class="warn">⚠ {bi("Liquidité on-chain faible (moins de 10 000 $) : le prix affiché peut être peu représentatif.","Low on-chain liquidity (under $10,000): the price shown may not be representative.")}</p>'
        if a.get("trading_halted"):
            flags += f'<p class="warn">⚠ {bi("Émission/rachat suspendus chez l’émetteur selon l’API xStocks.","Issuance/redemption halted by the issuer according to the xStocks API.")}</p>'
        src = a.get("token_price_source") or {}
        mult = ""
        if a.get("multiplier"):
            mult = f"<dt>{bi('Multiplicateur (dividendes)','Multiplier (dividends)')}</dt><dd>{a['multiplier']:.6f}</dd>"
        deps = "".join(f"<li>{e(CHAIN.get(d['network'], d['network']))} : <code>{e(d['address'] or '')}</code></li>" for d in a["deployments"][:12])
        body = f"""
    <p class="small"><a href="{P()}">← {bi("Toutes les actions tokenisées","All tokenized stocks")}</a></p>
    <h1 style="margin:6px 0">{e(a['symbol'])} <span class="small" style="font-size:18px">· {e(name)}</span></h1>
    <p><span class="tag {'x' if fam=='xStocks' else 'o'}">{e(fam)}</span> {''.join(f'<span class="tag">{e(CHAIN.get(c,c))}</span>' for c in a['chains'])}</p>
    <div class="grid"><div>
    <div class="card"><h2>{bi("Prix","Price")}</h2>
    <div style="display:flex;gap:30px;flex-wrap:wrap">
    <div><div class="small">{bi("Prix du token","Token price")}</div><div class="big">{bi(money(a['token_price']), money_en(a['token_price']))}</div><div class="small">{e(src.get('name') or '')} {e(src.get('detail') or '')} {('(' + bi('milieu achat/vente' if src.get('kind')=='mid' else 'dernier échange', 'bid/ask mid' if src.get('kind')=='mid' else 'last trade') + ')') if src.get('kind') else ''}</div></div>
    <div><div class="small">{bi("Prix de l'action","Share price")} ({e(a['underlying'] or '')})</div><div class="big">{bi(money(a['share_price']), money_en(a['share_price']))}</div><div class="small">Yahoo Finance · {e(lux_time(a.get('share_price_time')) or '')} (Lux)</div></div>
    <div><div class="small">{bi("Écart","Gap")}</div><div class="big">{pct(a['premium_pct'])}</div></div>
    </div>{flags}</div>
    <div class="card"><h2>{bi("Ce que vous détenez vraiment","What you actually own")}</h2>{bi(own_fr, own_en, "div")}
    <p class="small">{bi("Sources","Sources")} : {' · '.join(f'<a href="{u}" target="_blank" rel="noopener">{e(t)}</a>' for t,u in links)}</p></div>
    <div class="card"><h2>{bi("Où l'acheter depuis l'UE","Where to buy from the EU")}</h2>{plat_html}
    <p class="small">{bi("La présence dans la liste publique d'une plateforme ne garantit pas que vous y avez accès : cela dépend de votre pays, de votre statut et du test d'adéquation.","Being in a platform's public market list does not guarantee you can access it: that depends on your country, status and appropriateness test.")}</p></div>
    </div><div>
    <div class="card"><h2>{bi("Fiche technique","Details")}</h2><dl class="kv">
    <dt>{bi("Émetteur","Issuer")}</dt><dd>{e(a['issuer_entity'])}</dd>
    <dt>{bi("Action sous-jacente","Underlying")}</dt><dd>{e(a['underlying'] or '')} {('· ' + e(a['share_exchange_name'])) if a.get('share_exchange_name') else ''}</dd>
    <dt>ISIN {bi("action","share")}</dt><dd>{e(a.get('underlying_isin') or '') or bi('<span class="unk">n.d.</span>','<span class="unk">n/a</span>')}</dd>
    <dt>ISIN token</dt><dd>{e(a.get('token_isin') or '') or bi('<span class="unk">n.d.</span>','<span class="unk">n/a</span>')}</dd>
    {mult}
    <dt>{bi("Pool DEX le plus liquide","Deepest DEX pool")}</dt><dd>{(f'<a href="{e(dex["pair_url"])}" target="_blank" rel="noopener">{e(dex["dex"])} · {e(dex["chain"])}</a> · ' + bi(f'liquidité {money(dex["liquidity_usd"])}', f'liquidity {money_en(dex["liquidity_usd"])}')) if dex else bi('<span class="unk">aucun trouvé</span>','<span class="unk">none found</span>')}</dd>
    </dl></div>
    <div class="card"><h2>{bi("Contrats","Contracts")}</h2><ul class="small" style="padding-left:18px">{deps}</ul>
    <p class="small">{bi("Vérifiez toujours l'adresse sur le site de l'émetteur avant toute opération.","Always verify the address on the issuer's site before any transaction.")}</p></div>
    </div></div>
    """
        famshort = "xStocks" if fam == "xStocks" else "Ondo"
        where = ", ".join(p["platform"] for p in plats if p["platform"] != "Bitpanda")
        title = bi(f"{a['symbol']} : acheter l'action {name} tokenisée ({famshort}) depuis l'Europe | Actions 24/7",
                   f"{a['symbol']}: buy tokenized {name} stock ({famshort}) from Europe | Actions 24/7")
        desc = bi(f"{a['symbol']}, l'action {name} ({a['underlying']}) tokenisée par {famshort} : prix 24h/24, écart avec la vraie action, ce que vous détenez vraiment"
                  + (f", où l'acheter dans l'UE ({where})." if where else ", plateformes UE vérifiées."),
                  f"{a['symbol']}, tokenized {name} ({a['underlying']}) stock by {famshort}: 24/7 price, gap to the real share, what you actually own"
                  + (f", where to buy it in the EU ({where})." if where else ", verified EU platforms."))
        path = "actif/" + a["id"] + ".html"
        prod = {"@context": "https://schema.org", "@type": "FinancialProduct",
                "name": f"{a['symbol']} ({name})", "url": url_for(LANG, path), "description": desc, "inLanguage": LANG,
                "category": bi("Action tokenisée", "Tokenized stock"),
                "provider": {"@type": "Organization", "name": a["issuer_entity"]},
                "brand": {"@type": "Brand", "name": fam}}
        if a.get("token_isin"):
            prod["identifier"] = {"@type": "PropertyValue", "propertyID": "ISIN", "value": a["token_isin"]}
        crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Actions 24/7", "item": url_for(LANG, "")},
            {"@type": "ListItem", "position": 2, "name": a["symbol"], "item": url_for(LANG, path)}]}
        open(os.path.join(OUT, path), "w").write(page(title, body, path, desc, [prod, crumbs], "article"))
        PAGES.append(path)

    # ------------------------------------------------------------------ methodology
    rows = "".join(f"<tr><td>{e(k)}</td><td>{'✅' if v['ok'] else '❌'}</td><td class='small' style='white-space:normal'>{e(v['detail'])}</td></tr>" for k, v in D["sources"].items())
    meth = f"""<h1>{bi("Méthode et sources","Method &amp; sources")}</h1>
    <div class="card"><h2>{bi("Sources de données (dernier passage)","Data sources (last run)")}</h2>
    <table><tr><th>Source</th><th>OK</th><th>{bi("Détail","Detail")}</th></tr>{rows}</table>
    <p class="small">{bi("Nous n'affichons que des données récupérées. Une valeur manquante est marquée « n.d. », jamais estimée. Périmètre v1 : xStocks dont l'action sous-jacente est cotée aux États-Unis, et tokens Ondo Global Markets.","We only show fetched data. A missing value is marked “n/a”, never estimated. v1 scope: xStocks whose underlying is US-listed, and Ondo Global Markets tokens.")}</p></div>
    <div class="card"><h2>{bi("Avertissements","Disclaimers")}</h2>{bi(
    "<ul><li>Ceci n'est pas un conseil en investissement. Nous ne recommandons aucun produit.</li><li>Les actions tokenisées ne sont pas des actions : pas de propriété directe, pas de droit de vote, risque émetteur et risque de plateforme.</li><li>Produits interdits aux US persons et aux résidents américains.</li><li>La disponibilité dans l'UE dépend de chaque plateforme, de votre pays et de votre profil ; elle peut changer sans préavis.</li><li>Les prix peuvent être en retard ; l'action sous-jacente ne cote pas la nuit ni le week-end, alors que le token, lui, continue de s'échanger.</li></ul>",
    "<ul><li>This is not investment advice. We recommend no product.</li><li>Tokenized stocks are not shares: no direct ownership, no voting rights, issuer and platform risk.</li><li>Not for US persons or US residents.</li><li>EU availability depends on each platform, your country and profile; it can change without notice.</li><li>Prices may be delayed; the underlying share does not trade at night or on weekends, while the token keeps trading.</li></ul>","div")}</div>"""
    open(os.path.join(OUT, "methodologie.html"), "w").write(page(
        bi("Méthode et sources des données sur les actions tokenisées | Actions 24/7", "Tokenized stock data: method and sources | Actions 24/7"), meth, "methodologie.html",
        bi("Comment Actions 24/7 calcule les prix et écarts des actions tokenisées xStocks et Ondo : sources (Kraken, OKX, DexScreener, Yahoo Finance), règles et limites.",
           "How Actions 24/7 computes prices and gaps for xStocks and Ondo tokenized stocks: sources (Kraken, OKX, DexScreener, Yahoo Finance), rules and limits.")))

    # ------------------------------------------------------------------ legal notice (mentions légales)
    legal = f"""<h1>{bi("Mentions légales","Legal notice")}</h1>
    <div class="card"><h2>{bi("Éditeur du site","Publisher")}</h2>
    <p>{bi("Le site actions247.fr est édité à titre personnel par Cyril-Olivier Canet, particulier résidant au Luxembourg.",
    "The website actions247.fr is published in a personal capacity by Cyril-Olivier Canet, a private individual resident in Luxembourg.")}</p>
    <p>{bi("Directeur de la publication : Cyril-Olivier Canet.","Publication director: Cyril-Olivier Canet.")}</p>
    <p>Contact : <a href="mailto:cyril@mail.grokbot.com">cyril@mail.grokbot.com</a></p></div>
    <div class="card"><h2>{bi("Hébergement","Hosting")}</h2>
    <p>GitHub Inc. (GitHub Pages)<br>88 Colin P Kelly Jr St<br>San Francisco, CA 94107<br>{bi("États-Unis","USA")}<br><a href="https://github.com" rel="noopener">github.com</a></p></div>
    <div class="card"><h2>{bi("Données personnelles et cookies","Personal data and cookies")}</h2>
    <p>{bi("Le site ne dépose aucun cookie et n'utilise aucun outil de mesure d'audience ni de publicité. L'hébergeur peut conserver des journaux techniques (dont l'adresse IP) pour assurer la sécurité du service. Pour toute question : cyril@mail.grokbot.com.",
    "The site sets no cookies and uses no analytics or advertising tools. The host may keep technical logs (including IP addresses) for security purposes. Questions: cyril@mail.grokbot.com.")}</p></div>
    <div class="card"><h2>{bi("Contenu et responsabilité","Content and liability")}</h2>
    <p>{bi("Les informations publiées sont fournies à titre informatif uniquement et ne constituent pas un conseil en investissement. Les données proviennent de sources publiques tierces (voir « Méthode et sources ») et peuvent être incomplètes, en retard ou erronées. Les noms et marques cités appartiennent à leurs propriétaires respectifs.",
    "Published information is for information only and is not investment advice. Data comes from third-party public sources (see “Method &amp; sources”) and may be incomplete, delayed or wrong. Names and trademarks mentioned belong to their respective owners.")}</p></div>"""
    open(os.path.join(OUT, "mentions-legales.html"), "w").write(page(
        bi("Mentions légales | Actions 24/7", "Legal notice | Actions 24/7"), legal, "mentions-legales.html",
        bi("Mentions légales du site actions247.fr : éditeur, hébergeur, données personnelles et responsabilité.",
           "Legal notice for actions247.fr: publisher, host, personal data and liability.")))


PAGES = []   # asset page paths (filled by the FR build)
build("fr")
asset_paths = list(PAGES)
build("en")

# ------------------------------------------------------------------ sitemap.xml + robots.txt
lastmod = dt.datetime.fromisoformat(D["generated_at"]).date().isoformat()
paths = ["", "methodologie.html", "mentions-legales.html"] + asset_paths
xml = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for pth in paths:
    alts = (f'<xhtml:link rel="alternate" hreflang="fr" href="{url_for("fr", pth)}"/>'
            f'<xhtml:link rel="alternate" hreflang="en" href="{url_for("en", pth)}"/>'
            f'<xhtml:link rel="alternate" hreflang="x-default" href="{url_for("fr", pth)}"/>')
    for lg in ("fr", "en"):
        xml.append(f'<url><loc>{url_for(lg, pth)}</loc><lastmod>{lastmod}</lastmod>{alts}</url>')
xml.append("</urlset>")
open(os.path.join(SITE, "sitemap.xml"), "w").write("\n".join(xml) + "\n")
open(os.path.join(SITE, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")

# ------------------------------------------------------------------ GitHub Pages: custom domain + no Jekyll
open(os.path.join(SITE, "CNAME"), "w").write("actions247.fr\n")
open(os.path.join(SITE, ".nojekyll"), "w").write("")
print("built", len(asset_paths), "asset pages x 2 languages,", 2 * len(paths), "sitemap URLs")
