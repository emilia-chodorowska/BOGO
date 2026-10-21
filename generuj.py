#!/usr/bin/env python3
"""Generator BOGO z danych w edycja.py.

`python3 generuj.py` robi wszystko: index.html (PLN), index-eur.html (EUR), og.html + render podglądu linku,
i stronę rejestracji z pakietem (../new-client-offer/<folder>/).
`python3 generuj.py pln|eur` — tylko jedna strona BOGO.

Ceny PLN: hurtowe brutto PL (wholesale_gross) z bazy aroma-pricing (doterra-image.py --info).
Ceny EUR: „EK-Preis” z kart produktów sklepu DE (shop.doterra.com/DE/de_DE/shop/<slug>/), czytane przez ego.
Cena i PV zestawu = cena i PV produktu kupowanego (tak liczy doTERRA, sprawdzone na lipcu 2026).
Brakująca cena (None) → strona pokazuje „brak ceny” zamiast zgadywać.
Cena szacunkowa (nazwa w SZACUNKOWE) → kwoty z gwiazdką i przypis „cena przybliżona”.
"""
import subprocess
import sys
from pathlib import Path

if len(sys.argv) < 2:
    for w in ("pln", "eur"):
        subprocess.run([sys.executable, __file__, w], check=True)
    subprocess.run([sys.executable, str(Path(__file__).with_name("dodatki.py"))], check=True)
    sys.exit()
WALUTA = sys.argv[1]

from edycja import (OKRES, OKRES_KROTKO, OKRES_WARUNKI, KONIEC, POPRZEDNIA, PREZENT_NAZWA, WARUNKI_EXTRA,
                    SZACUNEK_DOPELNIACZ, SZACUNKOWE, FOTO_PAKIET, FOTO_PREZENT, MIESIAC, PRODUKTY)
import edycja
import liczenie

DATA_CEN = edycja.DATA_CEN[WALUTA]
ZRODLO_CEN = {"pln": "cennika doTERRA Polska", "eur": "cennika doTERRA Niemcy (w euro)"}[WALUTA]
OG_IMAGE = f"https://raw.githubusercontent.com/emilia-chodorowska/BOGO/main/images/bogo-social-preview-{MIESIAC}.jpg"


def c(nazwa):
    return PRODUKTY[nazwa][WALUTA]


def poz(p):
    """(nazwa, pojemność, PV, ilość) → (nazwa, pojemność, cena, PV, ilość)"""
    n, r, pv_, ile = p
    return (n, r, c(n), pv_, ile)


ZESTAWY = [dict(z, kup=poz(z["kup"]), gratis=[poz(g) for g in z["gratis"]]) for z in edycja.ZESTAWY]
PREZENT = (edycja.PREZENT[0], edycja.PREZENT[1], c(edycja.PREZENT[0]))



PLIK = "index.html" if WALUTA == "pln" else "index-eur.html"
SYMBOL = "zł" if WALUTA == "pln" else "€"


def zl(x, waluta=True):
    s = f"{x:,.2f}".replace(",", " ").replace(".", ",").replace(" ", "")
    return f"{s} {SYMBOL}" if waluta else s


def pv(x):
    return f"{x:.1f}".replace(".", ",")


def wartosc(poz):
    _, _, cena, _, ile = poz
    return None if cena is None else round(cena * ile, 2)


def podzial(cena_zestawu, pozycje):
    return liczenie.podzial(cena_zestawu, [wartosc(p) for p in pozycje])


def nazwa_poz(p):
    n, r, _, _, ile = p
    return f"{'2 × ' if ile == 2 else ''}{n} ({r})"


# ---------- karty zestawów ----------
karty = []
wiersze = []
suma_przed = 0.0
brakuje_przed = []
szac_pakiet = False
suma_bogo = 0.0
suma_pv = 0.0
for i, z in enumerate(ZESTAWY, 1):
    kup = z["kup"]
    cena = kup[2]
    pozycje = [kup] + z["gratis"]
    wart = [wartosc(p) for p in pozycje]
    znane = all(v is not None for v in wart)
    przed = round(sum(wart), 2) if znane else None
    przybl = any(p[0] in SZACUNKOWE for p in pozycje)
    gw = "*" if przybl else ""
    szac_pakiet = szac_pakiet or przybl
    suma_bogo += cena
    suma_pv += kup[3]
    suma_przed += sum(v for v in wart if v is not None)
    if not znane:
        brakuje_przed.append(z["krotko"])

    sklad = " · ".join(nazwa_poz(p) for p in pozycje)
    dopisek = f'<div style="font-size:12px; color:#78716c; margin:-8px 0 14px;">{z["dopisek"]}</div>' if z.get("dopisek") else ""
    if znane:
        przed_html = f'<div style="font-size:19px; font-weight:600; color:#a8a29e; text-decoration:line-through; line-height:1.15;">{zl(przed)}{gw}</div>'
        oszcz = przed - cena
        pill = f'{zl(oszcz)}{gw} · {round(oszcz / przed * 100)}%'
    else:
        przed_html = f'<div style="font-size:14px; font-weight:600; color:#a8a29e; line-height:1.3;">{zl(cena)} + {z["krotko"]}</div>'
        pill = z["krotko"] + " gratis"
    karty.append(f'''
      <!-- ZESTAW {i} -->
      <article style="display:flex; gap:26px; background:#ffffff; border:1px solid #ece3d0; border-radius:20px; padding:20px; align-items:center; flex-wrap:wrap;">
        <div class="para-foto" style="flex:0 0 190px; height:170px; border-radius:14px; overflow:hidden; background:#faf9f6; display:flex; align-items:center; justify-content:center;">
          <img src="{z["foto"]}" alt="{sklad}" style="height:100%; width:100%; object-fit:cover;" onerror="this.style.opacity=.4">
        </div>
        <div style="flex:1 1 340px; min-width:0;">
          <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
            <span style="font-size:11px; font-weight:700; letter-spacing:.1em; color:#4d6a5e;">ZESTAW {i:02d}</span>
            <span style="font-size:11px; font-weight:600; color:#78716c;">· {pv(kup[3])} PV</span>
          </div>
          <h3 class="tytul-zestawu" style="font-size:20px; font-weight:600; color:#1c1917; margin:0 0 6px; line-height:1.25;">{z["tytul"]}</h3>
          <div style="font-size:13px; color:#57534e; margin:0 0 14px; line-height:1.5;"><strong style="color:#4d6a5e;">Kupujesz:</strong> {nazwa_poz(kup)} · <strong style="color:#4d6a5e;">Gratis:</strong> {", ".join(nazwa_poz(p) for p in z["gratis"])}</div>
          {dopisek}
          <div class="cena-row" style="display:flex; align-items:flex-end; gap:18px; flex-wrap:wrap;">
            <div>
              <div style="font-size:11px; color:#78716c; text-transform:uppercase; letter-spacing:.08em; margin-bottom:3px;">Cena zestawu przed</div>
              {przed_html}
            </div>
            <svg class="cena-strzalka" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#d6cbb4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 18px; margin-bottom:3px;"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            <div>
              <div style="font-size:11px; color:#4d6a5e; font-weight:700; text-transform:uppercase; letter-spacing:.08em; margin-bottom:3px;">Cena zestawu BOGO</div>
              <div style="font-size:26px; font-weight:700; color:#1c1917; line-height:1;">{zl(cena, False)} <span style="font-size:15px; font-weight:600;">{SYMBOL}</span></div>
            </div>
            <div class="cena-pill" style="margin-left:auto; max-width:100%; padding:10px 16px; background:#eef2f0; border-radius:12px; text-align:right;">
              <div style="font-size:11px; color:#4d6a5e; text-transform:uppercase; letter-spacing:.06em; font-weight:600;">Oszczędzasz</div>
              <div style="font-size:{20 if znane else 14}px; font-weight:700; color:#4d6a5e;{"" if znane else " white-space:normal;"}">{pill}</div>
            </div>
          </div>
        </div>
      </article>''')

    # tabela kalkulacji
    sep = "#f0eadd" if i == 1 else "#ddd2ba"
    wiersze.append(f'''          <tr style="border-top:1px solid {sep}; background:#faf9f6;"><td colspan="2" style="padding:10px 20px 9px; font-size:10.5px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; color:#4d6a5e;"><span style="display:inline-flex; align-items:center; gap:8px;"><span style="width:5px; height:5px; border-radius:50%; background:#4d6a5e;"></span>Zestaw {i:02d}</span><span class="para-cena" style="display:none; font-weight:600; letter-spacing:.02em; text-transform:none; color:#78716c;"> · {zl(cena)}</span></td><td class="zestaw-prawa" style="padding:10px 20px 9px; text-align:right; font-size:10.5px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:#78716c;">zestaw {zl(cena)}</td></tr>''')
    for j, (p, w, d) in enumerate(zip(pozycje, wart, podzial(cena, pozycje))):
        border = "" if j == 0 else "border-top:1px solid #f6f1e6; "
        poza = (zl(w, False) + ("*" if p[0] in SZACUNKOWE else "")) if w is not None else "brak ceny"
        wz = (zl(d, False) + gw) if d is not None else "—"
        wiersze.append(f'''          <tr style="{border}"><td style="padding:13px 20px 13px 34px;">{nazwa_poz(p)}</td><td style="padding:13px 16px; text-align:right; color:#78716c;">{poza}</td><td style="padding:13px 20px; text-align:right; font-weight:700; color:#4d6a5e;">{wz}</td></tr>''')

suma_przed += PREZENT[2]
suma_bogo = round(suma_bogo, 2)
suma_przed = round(suma_przed, 2)
wiersze.append(f'''          <tr style="border-top:1px solid #ddd2ba; background:#eef2f0;"><td style="padding:13px 20px;">{PREZENT[0]} ({PREZENT[1]}) — <strong style="color:#4d6a5e;">gratis do pakietu</strong></td><td style="padding:13px 16px; text-align:right; color:#78716c;">{zl(PREZENT[2], False)}</td><td style="padding:13px 20px; text-align:right; font-weight:700; color:#4d6a5e;">0,00</td></tr>''')

dopisek_brak = (" + " + ", ".join(brakuje_przed)) if brakuje_przed else ""
oszcz_pakiet = round(suma_przed - suma_bogo, 2)

WARUNKI_HTML = "\n".join('            <li style="display:flex; gap:12px; font-size:13.5px; line-height:1.55; color:#292524;"><span style="flex:0 0 6px; height:6px; border-radius:50%; background:#4d6a5e; margin-top:7px;"></span><span>{w}</span></li>'.format(w=w) for w in WARUNKI_EXTRA)

nota = "Ceny hurtowe brutto z " + ZRODLO_CEN + " z " + DATA_CEN + ". Kolumna „W zestawie” rozdziela cenę zestawu proporcjonalnie na produkty."
gp = "*" if szac_pakiet else ""
if szac_pakiet:
    nota += "<br>* Cena przybliżona: " + SZACUNEK_DOPELNIACZ + " nie ma jeszcze w cenniku doTERRA, przyjęto ok. " + zl(c(next(iter(SZACUNKOWE)))) + " za sztukę."
if brakuje_przed:
    nota += " Olejku do kąpieli Adaptiv nie ma jeszcze w cenniku — sumy „przed” i oszczędność nie zawierają jego wartości."

html = f'''<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Oferta BOGO | {OKRES}</title>

    <!-- === META TAGI OPEN GRAPH === -->
    <meta property="og:title" content="Oferta BOGO | {OKRES}">
    <meta property="og:description" content="5 zestawów: kupujesz jeden produkt, drugi dostajesz gratis. Pakiet BOGO: dodatkowo gratis {PREZENT_NAZWA} ({PREZENT[1]}).">
    <meta property="og:image" content="{OG_IMAGE}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:url" content="https://emilia-chodorowska.github.io/BOGO/{PLIK if WALUTA == "eur" else ""}">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Oferta BOGO | {OKRES}">
    <meta name="twitter:description" content="5 zestawów: kupujesz jeden produkt, drugi dostajesz gratis. Pakiet BOGO: dodatkowo gratis {PREZENT_NAZWA} ({PREZENT[1]}).">
    <meta name="twitter:image" content="{OG_IMAGE}">

    <meta name="theme-color" content="#fcfbfa">

    <!-- === FAVICON === -->
    <link rel="icon" type="image/x-icon" href="images/favicon.ico">
    <link rel="icon" type="image/png" sizes="32x32" href="images/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="images/favicon-16x16.png">
    <link rel="icon" sizes="192x192" href="images/android-chrome-192x192.png">
    <link rel="icon" sizes="512x512" href="images/android-chrome-512x512.png">
    <link rel="apple-touch-icon" sizes="180x180" href="images/apple-touch-icon.png">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=Playfair+Display:wght@500;600&amp;display=swap" rel="stylesheet">
    <style>
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; font-family: 'Inter', sans-serif; background: #fcfbfa; -webkit-font-smoothing: antialiased; }}
      a {{ color: #4d6a5e; text-decoration: none; }}
      a:hover {{ color: #3e554b; }}
      .tytul-zestawu span {{ color: #4d6a5e; }}
  @media (max-width: 560px) {{
    .cena-row {{ display: grid !important; grid-template-columns: auto auto; justify-content: start; column-gap: 26px; row-gap: 14px; align-items: start; }}
    .cena-strzalka {{ display: none; }}
    .cena-pill {{ margin-left: 0; grid-column: 1 / -1; display: flex; align-items: center; justify-content: space-between; gap: 12px; text-align: left; }}
    .cena-pill > div:last-child {{ font-size: 17px; white-space: nowrap; }}
    .para-foto {{ flex: 1 1 100% !important; height: 200px !important; }}
    .pakiet-kafle {{ display: grid !important; grid-template-columns: 1fr 1fr; gap: 10px; }}
    .pakiet-kafle > div:first-child {{ grid-column: 1 / -1; }}
    .pakiet-kafle > div {{ padding: 12px 16px !important; }}
    .gratis-foto {{ flex: 1 1 100% !important; height: 170px !important; }}
    .gratis-wartosc {{ flex: 1 1 100%; display: flex; align-items: center; justify-content: space-between; text-align: left !important; padding-right: 0 !important; border-top: 1px solid #f0eadd; padding-top: 12px; }}
    .kalk {{ font-size: 12.5px; }}
    .kalk th, .kalk td {{ padding: 11px 10px !important; }}
    .kalk tbody td:first-child {{ padding-left: 18px !important; }}
    .kalk thead th:first-child, .kalk tfoot td:first-child {{ padding-left: 12px !important; }}
    .kalk .para-cena {{ display: inline !important; }}
    .kalk .zestaw-prawa {{ font-size: 0 !important; padding-left: 0 !important; padding-right: 0 !important; }}
  }}
    </style>
</head>
<body>
<div style="min-height:100vh; background:#fcfbfa; padding:48px 20px;">
<div style="position:relative; max-width:1040px; margin:0 auto; background:#ffffff; border-radius:26px; box-shadow:0 30px 70px -40px rgba(47,58,51,.4); overflow:hidden;">

  <img src="images/liscie-gora.jpg" alt="" style="position:absolute; top:0; left:0; width:30%; opacity:.22; pointer-events:none; mix-blend-mode:multiply; z-index:0;" onerror="this.style.display='none'">
  <img src="images/liscie-dol.jpg" alt="" style="position:absolute; bottom:0; right:0; width:30%; opacity:.22; pointer-events:none; mix-blend-mode:multiply; z-index:0;" onerror="this.style.display='none'">

  <div style="position:relative; z-index:1; padding:clamp(28px,5vw,56px) clamp(20px,4.5vw,48px) 64px;">

    <!-- HERO -->
    <header style="text-align:center; margin-bottom:56px;">
      <img src="images/logobogo.png" alt="Logo BOGO doTERRA" style="width:120px; height:auto; margin:0 auto 26px; display:block;" onerror="this.style.display='none'">
      <div style="display:inline-flex; align-items:center; gap:10px; padding:7px 18px; border:1px solid #d6d3d1; border-radius:999px; color:#4d6a5e; font-size:12px; font-weight:600; letter-spacing:.14em; text-transform:uppercase; margin-bottom:22px;">
        <span style="width:6px; height:6px; border-radius:50%; background:#4d6a5e;"></span>
        Oferta limitowana
      </div>
      <h1 style="font-family:'Playfair Display',serif; font-weight:600; font-size:clamp(40px,8vw,64px); line-height:1.02; color:#1c1917; margin:0 0 6px; letter-spacing:.01em;">Oferta BOGO</h1>
      <p style="font-family:'Playfair Display',serif; font-size:clamp(24px,5vw,30px); font-weight:500; color:#4d6a5e; margin:0 0 20px;">{OKRES}</p>
      <p style="max-width:520px; margin:0 auto; color:#57534e; font-size:15px; line-height:1.6;">Kupujesz jeden produkt, drugi dostajesz <strong style="color:#4d6a5e;">gratis</strong>. Do całego pakietu BOGO dochodzi {PREZENT_NAZWA} ({PREZENT[1]}).</p>
      <div style="display:inline-flex; align-items:center; gap:10px; margin-top:24px; padding:12px 22px; background:#faf9f6; border-radius:14px; color:#57534e; font-size:13px; line-height:1.4;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4d6a5e" stroke-width="1.7"><circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3 2"></path></svg>
        Oferta kończy się <strong style="color:#4d6a5e; margin:0 4px;">{KONIEC}</strong> lub gdy zabraknie zapasów
      </div>
    </header>

    <!-- SECTION LABEL -->
    <div style="display:flex; align-items:center; gap:16px; margin-bottom:26px;">
      <span style="font-family:'Playfair Display',serif; font-size:clamp(26px,5vw,34px); font-weight:600; color:#1c1917;">Zestawy</span>
      <span style="flex:1; height:1px; background:#ddd2ba;"></span>
      <span style="font-size:12px; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:#78716c;">5 zestawów</span>
    </div>

    <!-- PRODUCT CARDS -->
    <div style="display:flex; flex-direction:column; gap:18px; margin-bottom:26px;">
{"".join(karty)}
    </div>

    <!-- BUNDLE SUMMARY -->
    <div style="background:#eef2f0; border:1px solid #dfe6e2; border-radius:22px; padding:clamp(20px,4vw,32px); margin-bottom:64px;">
      <div style="display:flex; gap:28px; align-items:center; flex-wrap:wrap;">
        <div style="flex:1 1 220px; min-width:200px; height:210px; border-radius:16px; overflow:hidden; background:#ffffff;">
          <img src="{FOTO_PAKIET}" alt="Pakiet BOGO — wszystkie 5 zestawów" style="height:100%; width:100%; object-fit:cover;" onerror="this.style.opacity=.4">
        </div>
        <div style="flex:2 1 320px; min-width:260px;">
          <div style="display:inline-flex; align-items:center; gap:8px; padding:6px 15px; background:#4d6a5e; border-radius:999px; font-size:11px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:#dbe4df; margin-bottom:14px;">Wszystkie zestawy + gratis</div>
          <h3 style="font-family:'Playfair Display',serif; font-size:clamp(26px,5vw,34px); font-weight:600; margin:0 0 6px; line-height:1.12; color:#1c1917;">Pakiet BOGO</h3>
          <p style="margin:0 0 20px; color:#57534e; font-size:14px; line-height:1.5;">Wszystkie 5 zestawów w jednym zamówieniu, a do tego <strong style="color:#4d6a5e;">GRATIS</strong> {PREZENT_NAZWA} ({PREZENT[1]}).</p>
          <div class="pakiet-kafle" style="display:flex; gap:12px; flex-wrap:wrap;">
            <div style="padding:14px 20px; background:#ffffff; border:1px solid #e7e5e4; border-radius:14px; flex:1 1 auto;">
              <div style="font-size:11px; color:#78716c; text-transform:uppercase; letter-spacing:.07em;">Płacisz</div>
              <div style="font-size:clamp(22px,4vw,26px); font-weight:700; color:#1c1917; line-height:1.15;">{zl(suma_bogo)}</div>
              <div style="font-size:12px; color:#a8a29e; margin-top:2px;"><span style="text-decoration:line-through;">zamiast {zl(suma_przed)}{gp}</span>{dopisek_brak}</div>
            </div>
            <div style="padding:14px 20px; background:#4d6a5e; border-radius:14px; flex:1 1 auto;">
              <div style="font-size:11px; color:#9fb3a9; text-transform:uppercase; letter-spacing:.07em;">Oszczędzasz</div>
              <div style="font-size:clamp(22px,4vw,26px); font-weight:700; color:#eaf0ec;">{"min. " if brakuje_przed else ""}{zl(oszcz_pakiet)}{gp}</div>
            </div>
            <div style="padding:14px 20px; background:#ffffff; border:1px solid #e7e5e4; border-radius:14px; flex:1 1 auto;">
              <div style="font-size:11px; color:#78716c; text-transform:uppercase; letter-spacing:.07em;">Łącznie PV</div>
              <div style="font-size:clamp(22px,4vw,26px); font-weight:700; color:#1c1917;">{pv(suma_pv)}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- GRATIS -->
      <div style="display:flex; gap:18px; align-items:center; margin-top:22px; padding:16px; background:#ffffff; border:1px dashed #d8e0dc; border-radius:16px; flex-wrap:wrap;">
        <div class="gratis-foto" style="flex:0 0 108px; height:108px; border-radius:12px; overflow:hidden; background:#faf9f6;">
          <img src="{FOTO_PREZENT}" alt="{PREZENT_NAZWA.capitalize()} gratis" style="height:100%; width:100%; object-fit:cover;" onerror="this.style.opacity=.4">
        </div>
        <div style="flex:1 1 240px; min-width:220px;">
          <div style="display:inline-block; padding:3px 11px; background:#eef2f0; color:#4d6a5e; border-radius:999px; font-size:10px; font-weight:700; letter-spacing:.09em; text-transform:uppercase; margin-bottom:7px;">Gratis do pakietu</div>
          <div style="font-size:16px; font-weight:700; color:#4d6a5e; line-height:1.25; margin-bottom:5px;">{PREZENT_NAZWA.capitalize()}</div>
          <p style="margin:0; font-size:12px; color:#78716c; line-height:1.5;">Tylko przy zakupie całego pakietu BOGO, nie przy zestawach kupowanych pojedynczo.</p>
        </div>
        <div class="gratis-wartosc" style="text-align:right; padding-right:6px;">
          <div style="font-size:10px; color:#a8a29e; text-transform:uppercase; letter-spacing:.06em;">Wartość</div>
          <div style="font-size:16px; font-weight:700; color:#4d6a5e;">{zl(PREZENT[2])}</div>
        </div>
      </div>
    </div>

    <!-- CALCULATION TABLE -->
    <div style="display:flex; align-items:center; gap:16px; margin-bottom:22px;">
      <span style="font-family:'Playfair Display',serif; font-size:clamp(26px,5vw,34px); font-weight:600; color:#1c1917;">Szczegółowa kalkulacja</span>
      <span style="flex:1; height:1px; background:#ddd2ba;"></span>
    </div>
    <div style="border:1px solid #ece3d0; border-radius:18px; overflow-x:auto; margin-bottom:16px; background:#fff;">
      <table class="kalk" style="width:100%; border-collapse:collapse; font-size:14px;">
        <thead>
          <tr style="background:#faf9f6;">
            <th style="text-align:left; padding:15px 20px; font-size:11px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:#78716c;">Produkt</th>
            <th style="text-align:right; padding:15px 16px; font-size:11px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:#78716c;">Poza zestawem</th>
            <th style="text-align:right; padding:15px 20px; font-size:11px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:#4d6a5e;">W zestawie</th>
          </tr>
        </thead>
        <tbody style="color:#292524;">
{chr(10).join(wiersze)}
        </tbody>
        <tfoot>
          <tr style="background:#4d6a5e; color:#f3efe4;"><td style="padding:18px 20px; font-weight:700; font-size:15px;">Suma</td><td style="padding:18px 16px; text-align:right; color:#cdd6c9; text-decoration:line-through;">{zl(suma_przed, False)}{gp}</td><td style="padding:18px 20px; text-align:right; font-weight:700; font-size:17px;">{zl(suma_bogo)}</td></tr>
        </tfoot>
      </table>
    </div>
    <div style="font-size:12px; color:#78716c; line-height:1.65; margin-bottom:60px; max-width:820px;">
      <p style="margin:0;">{nota}</p>
    </div>

    <!-- TERMS + HOW TO ORDER -->
    <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(min(320px,100%),1fr)); gap:26px;">

      <section style="display:flex; flex-direction:column;">
        <div style="display:flex; align-items:center; gap:14px; margin-bottom:20px;">
          <span style="font-family:'Playfair Display',serif; font-size:clamp(24px,5vw,30px); font-weight:600; color:#1c1917;">Warunki promocji</span>
        </div>
        <div style="background:#fff; border:1px solid #ece3d0; border-radius:18px; padding:26px; flex:1;">
          <ul style="list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:14px;">
            <li style="display:flex; gap:12px; font-size:13.5px; line-height:1.55; color:#292524;"><span style="flex:0 0 6px; height:6px; border-radius:50%; background:#4d6a5e; margin-top:7px;"></span><span>Promocja trwa od <strong style="color:#4d6a5e;">{OKRES_WARUNKI}</strong></span></li>
            <li style="display:flex; gap:12px; font-size:13.5px; line-height:1.55; color:#292524;"><span style="flex:0 0 6px; height:6px; border-radius:50%; background:#4d6a5e; margin-top:7px;"></span><span>Oferta obowiązuje <strong style="color:#4d6a5e;">do wyczerpania zapasów</strong> — może się skończyć wcześniej.</span></li>
            <li style="display:flex; gap:12px; font-size:13.5px; line-height:1.55; color:#292524;"><span style="flex:0 0 6px; height:6px; border-radius:50%; background:#4d6a5e; margin-top:7px;"></span><span>Limit: maksymalnie <strong style="color:#4d6a5e;">5 zamówień na każdy zestaw</strong> oraz <strong style="color:#4d6a5e;">5 pakietów BOGO</strong> na jedno konto.</span></li>
            <li style="display:flex; gap:12px; font-size:13.5px; line-height:1.55; color:#292524;"><span style="flex:0 0 6px; height:6px; border-radius:50%; background:#4d6a5e; margin-top:7px;"></span><span>{PREZENT_NAZWA.capitalize()} ({PREZENT[1]}) gratis dostajesz <strong style="color:#4d6a5e;">wyłącznie przy zakupie pakietu BOGO</strong>, nie przy kupowaniu zestawów pojedynczo.</span></li>
{WARUNKI_HTML}
          </ul>
        </div>
      </section>

      <section style="display:flex; flex-direction:column;">
        <div style="display:flex; align-items:center; gap:14px; margin-bottom:20px;">
          <span style="font-family:'Playfair Display',serif; font-size:clamp(24px,5vw,30px); font-weight:600; color:#1c1917;">Jak zamówić</span>
        </div>
        <div style="background:#fff; border:1px solid #ece3d0; border-radius:18px; padding:26px; flex:1;">
          <p style="margin:0 0 6px; font-size:14px; font-weight:600; color:#1c1917;">Sposób 1: jednorazowe zamówienie lojalnościowe (z koszyka)</p>
          <p style="margin:0 0 18px; font-size:12.5px; line-height:1.5; color:#57534e;">Dla osób, które przetworzyły i opłaciły zamówienie LRP w tym albo w poprzednim miesiącu. Comiesięczne LRP zostaje bez zmian.</p>
          <ol style="list-style:none; margin:0 0 22px; padding:0; display:flex; flex-direction:column; gap:14px;">
            <li style="display:flex; gap:14px; font-size:13.5px; line-height:1.5; color:#292524;"><span style="flex:0 0 26px; height:26px; border-radius:50%; background:#eef2f0; color:#4d6a5e; font-weight:700; font-size:12px; display:flex; align-items:center; justify-content:center;">1</span><span>Zaloguj się na <strong style="color:#4d6a5e;">shop.doterra.com</strong> i dodaj produkty BOGO przyciskiem <strong style="color:#4d6a5e;">„Dodaj do koszyka"</strong>.</span></li>
            <li style="display:flex; gap:14px; font-size:13.5px; line-height:1.5; color:#292524;"><span style="flex:0 0 26px; height:26px; border-radius:50%; background:#eef2f0; color:#4d6a5e; font-weight:700; font-size:12px; display:flex; align-items:center; justify-content:center;">2</span><span>Najedź na ikonę koszyka i kliknij <strong style="color:#4d6a5e;">„Zobacz swój koszyk"</strong>. Pasek śledzenia PV na górze strony oznacza, że zamówienie przejdzie jako jednorazowe lojalnościowe.</span></li>
            <li style="display:flex; gap:14px; font-size:13.5px; line-height:1.5; color:#292524;"><span style="flex:0 0 26px; height:26px; border-radius:50%; background:#eef2f0; color:#4d6a5e; font-weight:700; font-size:12px; display:flex; align-items:center; justify-content:center;">3</span><span>Kliknij <strong style="color:#4d6a5e;">„Przejdź do podsumowania"</strong>, a w okienku wybierz <strong style="color:#4d6a5e;">„Kontynuuj przetwarzanie jednorazowego zamówienia lojalnościowego"</strong>.</span></li>
            <li style="display:flex; gap:14px; font-size:13.5px; line-height:1.5; color:#292524;"><span style="flex:0 0 26px; height:26px; border-radius:50%; background:#eef2f0; color:#4d6a5e; font-weight:700; font-size:12px; display:flex; align-items:center; justify-content:center;">4</span><span>Sprawdź płatność i adres dostawy, potem kliknij <strong style="color:#4d6a5e;">„Sfinalizuj zamówienie"</strong>.</span></li>
          </ol>
          <div style="background:#faf9f6; border-left:3px solid #4d6a5e; border-radius:10px; padding:16px; font-size:12.5px; line-height:1.55; color:#57534e;">
            <p style="margin:0 0 10px;">Zamówienie może składać się <strong>wyłącznie z produktów BOGO</strong> — nie trzeba dokładać produktu ze standardowej oferty. Punkty lojalnościowe naliczają się od <strong>50 PV</strong>.</p>
            <p style="margin:0 0 10px;">Działa tylko na <strong>shop.doterra.com</strong>, nie na mydoterra.com.</p>
            <p style="margin:0;">Nie zastępuje comiesięcznego LRP 100 PV, które jest warunkiem prowizji (dotyczy konsultantów Wellness Advocate). Źródło: <a href="https://www.doterra.com/ME/pl_ME/faq-one-time-loyalty-order" target="_blank" rel="noopener" style="color:#4d6a5e;">FAQ doTERRA — jednorazowe zamówienia lojalnościowe</a>.</p>
          </div>

          <hr style="border:none; border-top:1px solid #ece3d0; margin:26px 0;">

          <p style="margin:0 0 18px; font-size:14px; font-weight:600; color:#1c1917;">Sposób 2: dodanie produktów BOGO do zamówienia lojalnościowego (LRP)</p>
          <ol style="list-style:none; margin:0 0 22px; padding:0; display:flex; flex-direction:column; gap:14px;">
            <li style="display:flex; gap:14px; font-size:13.5px; line-height:1.5; color:#292524;"><span style="flex:0 0 26px; height:26px; border-radius:50%; background:#eef2f0; color:#4d6a5e; font-weight:700; font-size:12px; display:flex; align-items:center; justify-content:center;">1</span><span>Zaloguj się i kliknij ikonę <strong style="color:#4d6a5e;">„Konto"</strong> na górnym pasku strony.</span></li>
            <li style="display:flex; gap:14px; font-size:13.5px; line-height:1.5; color:#292524;"><span style="flex:0 0 26px; height:26px; border-radius:50%; background:#eef2f0; color:#4d6a5e; font-weight:700; font-size:12px; display:flex; align-items:center; justify-content:center;">2</span><span>Z menu wybierz <strong style="color:#4d6a5e;">„Moje zamówienia lojalnościowe (LRP)"</strong>.</span></li>
            <li style="display:flex; gap:14px; font-size:13.5px; line-height:1.5; color:#292524;"><span style="flex:0 0 26px; height:26px; border-radius:50%; background:#eef2f0; color:#4d6a5e; font-weight:700; font-size:12px; display:flex; align-items:center; justify-content:center;">3</span><span>Kliknij <strong style="color:#4d6a5e;">„Zarządzaj zamówieniem"</strong>, aby otworzyć edycję swojego LRP.</span></li>
            <li style="display:flex; gap:14px; font-size:13.5px; line-height:1.5; color:#292524;"><span style="flex:0 0 26px; height:26px; border-radius:50%; background:#eef2f0; color:#4d6a5e; font-weight:700; font-size:12px; display:flex; align-items:center; justify-content:center;">4</span><span>Wyszukaj produkty BOGO — użyj wyszukiwarki lub przycisku <strong style="color:#4d6a5e;">„Przeglądaj"</strong>.</span></li>
            <li style="display:flex; gap:14px; font-size:13.5px; line-height:1.5; color:#292524;"><span style="flex:0 0 26px; height:26px; border-radius:50%; background:#eef2f0; color:#4d6a5e; font-weight:700; font-size:12px; display:flex; align-items:center; justify-content:center;">5</span><span>Dodaj wybrane produkty do koszyka i kliknij <strong style="color:#4d6a5e;">„Kolejny krok"</strong>.</span></li>
          </ol>
          <div style="background:#faf9f6; border-left:3px solid #4d6a5e; border-radius:10px; padding:16px; font-size:12.5px; line-height:1.55; color:#57534e;">
            <p style="margin:0 0 10px;"><strong style="color:#4d6a5e;">Pamiętaj:</strong> dodając artykuły BOGO do zamówienia lojalnościowego, <strong>musisz złożyć to zamówienie natychmiast</strong>, aby skorzystać z oferty.</p>
            <p style="margin:0;"><strong style="color:#4d6a5e;">Pamiętaj:</strong> wybierając cały pakiet BOGO, dodaj do szablonu LRP przynajmniej <strong>jeden produkt ze standardowej oferty</strong>, aby zamówienie mogło zostać przetworzone.</p>
          </div>
        </div>
      </section>
    </div>

    <p style="margin:48px 0 0; text-align:center; font-size:12px; color:#a8a29e;">Poprzednia oferta: <a href="{POPRZEDNIA[0]}/{PLIK if WALUTA == "eur" else ""}">{POPRZEDNIA[1]}</a></p>

  </div>
</div>
</div>
</body>
</html>
'''

Path(__file__).with_name(PLIK).write_text(html, encoding="utf-8")
print(f"{PLIK}: pakiet {zl(suma_bogo)}, przed {zl(suma_przed)}{dopisek_brak}, PV {pv(suma_pv)}")
