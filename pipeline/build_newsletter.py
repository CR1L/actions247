#!/usr/bin/env python3
"""Drafts the weekly French newsletter from data/assets.json (real data only)."""
import json, os, datetime as dt
from zoneinfo import ZoneInfo
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, "data", "assets.json")))
LUX = ZoneInfo("Europe/Luxembourg")
gen = dt.datetime.fromisoformat(D["generated_at"]).astimezone(LUX)
A = D["assets"]
num = int(os.environ.get("ISSUE", "1"))

def fr(x, d=2):
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")
def reliable(a):
    s = (a.get("token_price_source") or {}).get("name")
    if a["premium_pct"] is None or a.get("suspect_gap"):
        return False
    return s in ("Kraken", "OKX") or ((a.get("dex") or {}).get("liquidity_usd") or 0) >= 50000

rel = [a for a in A if reliable(a)]
prem = sorted(rel, key=lambda a: -a["premium_pct"])[:5]
disc = sorted(rel, key=lambda a: a["premium_pct"])[:5]
by_und = {a["underlying"]: a for a in A if a["issuer_family"] == "xStocks"}
cut = gen - dt.timedelta(days=30)
new_okx = sorted([l for l in D.get("okx_listings", []) if l["list_time"] and
                  dt.datetime.fromtimestamp(l["list_time"] / 1000, dt.timezone.utc) >= cut.astimezone(dt.timezone.utc)],
                 key=lambda l: -l["list_time"])
C = D["counts"]
def line(a):
    src = a["token_price_source"]["name"]
    return (f"| {a['symbol']} | {a.get('name') or a['underlying']} | {fr(a['token_price'])} $ ({src}) | "
            f"{fr(a['share_price'])} $ | {'+' if a['premium_pct'] >= 0 else ''}{fr(a['premium_pct'])} % |")

MOIS = ["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"]
JOURS = ["lundi","mardi","mercredi","jeudi","vendredi","samedi","dimanche"]
datefr = f"{JOURS[gen.weekday()]} {gen.day} {MOIS[gen.month-1]} {gen.year}"
heure = gen.strftime("%Hh%M")

md = f"""# Actions 24/7 · Numéro {num}
*BROUILLON, non envoyé. Données relevées le {datefr} à {heure} (heure de Luxembourg).*

**Objet proposé :** Tesla, Nvidia… en token 24h/24 : ce qu'il faut savoir cette semaine

Bonjour,

Bienvenue dans le premier numéro d'Actions 24/7, la lettre qui suit les actions américaines tokenisées : ces tokens qui reproduisent le prix de Tesla, Nvidia ou du S&P 500 et qui s'échangent jour et nuit, week-end compris, sur des plateformes crypto.

Chaque semaine : ce qui vient d'être listé, les écarts de prix entre les tokens et les vraies actions, et ce qui change pour les résidents de l'Union européenne.

## Le marché en chiffres

- **{C['assets']} tokens** suivis sur des actions et ETF américains : {sum(1 for a in A if a['issuer_family']=='xStocks')} xStocks et {sum(1 for a in A if a['issuer_family']!='xStocks')} tokens Ondo Global Markets.
- **{C['on_kraken']}** sont listés sur Kraken et **{C['on_okx']}** sur OKX (sous le nom « X » + ticker, par exemple XTSLA).
- Seuls **{C['with_token_price']}** ont un prix exploitable aujourd'hui (carnet d'ordres Kraken ou OKX, ou pool on-chain). Beaucoup de tokens existent sur la blockchain sans réel marché derrière.

## Nouveautés : ce qui a été listé récemment
"""
if new_okx:
    md += f"Sur OKX, **{len(new_okx)} tokens** ont été listés ces 30 derniers jours :\n\n"
    for l in new_okx[:12]:
        d = dt.datetime.fromtimestamp(l["list_time"] / 1000, dt.timezone.utc).astimezone(LUX)
        nm = (by_und.get(l["underlying"]) or {}).get("name") or l["underlying"]
        md += f"- **{l['okx_symbol']}** ({nm}), listé le {d.day} {MOIS[d.month-1]}\n"
    if len(new_okx) > 12:
        md += f"- … et {len(new_okx)-12} autres.\n"
else:
    md += "Aucun nouveau listing OKX détecté sur les 30 derniers jours dans nos données.\n"
md += """
*À partir du prochain numéro, nous comparerons chaque semaine la liste complète des tokens (xStocks, Ondo, Kraken, OKX) pour repérer toutes les nouveautés.*

## Les plus gros écarts de prix

L'écart compare le prix du token au prix de la vraie action (corrigé du multiplicateur de dividendes pour Ondo). Nous ne retenons que les prix fiables : carnets d'ordres Kraken ou OKX, ou pools on-chain avec plus de 50 000 $ de liquidité, et écart inférieur à 5 %.

"""
md += f"*Relevé le {datefr} à {heure} : la Bourse américaine était ouverte, les écarts sont donc faibles. C'est le week-end, quand l'action ne cote plus et que le token continue de s'échanger, que les écarts deviennent intéressants. Le prochain numéro mesurera l'écart du dimanche soir.*\n\n"
md += "**Tokens au-dessus du prix de l'action (prime)**\n\n| Token | Société | Prix du token | Prix de l'action | Écart |\n|---|---|---|---|---|\n"
md += "\n".join(line(a) for a in prem)
md += "\n\n**Tokens en dessous du prix de l'action (décote)**\n\n| Token | Société | Prix du token | Prix de l'action | Écart |\n|---|---|---|---|---|\n"
md += "\n".join(line(a) for a in disc)
md += f"""

Sources des prix : Kraken, OKX et DexScreener pour les tokens ; Yahoo Finance pour les actions (prix du marché régulier, parfois en léger retard).

## À savoir : ce que vous détenez vraiment

Un token xStocks ou Ondo **n'est pas une action**. C'est un titre de créance qui suit le prix de l'action, adossé à des actions détenues par un dépositaire.

- Pas de propriété directe de l'action, **pas de droit de vote**.
- Un risque supplémentaire : celui de l'émetteur (Backed Assets pour les xStocks, Ondo Global Markets pour Ondo) et celui de la plateforme.
- Les dividendes sont pris en compte automatiquement (ajustement du nombre de tokens pour les xStocks, multiplicateur pour Ondo).

## Où les trouver depuis l'Europe

- **Kraken** : {C['on_kraken']} xStocks listés. [Lien partenaire Kraken : à venir]
- **OKX** : {C['on_okx']} actions tokenisées, ouvertes aux clients européens via OKX Europe (Malte). [Lien partenaire OKX : à venir]
- **Bitpanda** ne propose pas de tokens, mais la vraie action pour {C['on_bitpanda_real_share']} des sous-jacents suivis : utile pour comparer. [Lien partenaire Bitpanda : à venir]

L'accès dépend de votre pays de résidence et de votre profil, et peut changer à tout moment.

Le tableau complet est sur le site : [actions247 : lien à venir]

À la semaine prochaine,
L'équipe Actions 24/7

---
*Actions 24/7 est une publication d'information. Rien dans cette lettre n'est un conseil en investissement, une recommandation ou une offre. Les actions tokenisées sont des produits complexes et risqués : vous pouvez perdre tout votre capital. Elles ne sont pas proposées aux résidents des États-Unis ni aux US persons. Certains liens pourront être des liens d'affiliation ; ils ne changent ni les données ni le classement.*
"""
os.makedirs(os.path.join(ROOT, "newsletter"), exist_ok=True)
out = os.path.join(ROOT, "newsletter", f"numero-{num:03d}-brouillon.md")
open(out, "w").write(md)
print(out, "| reliable:", len(rel), "| new OKX:", len(new_okx))
