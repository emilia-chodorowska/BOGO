#!/usr/bin/env python3
"""Grafika pakietu BOGO na Instagram (relacja 1080x1920 i post 1080x1350), w stylu plansz z panele.py.

  python3 ig.py      # PNG do zrodla-<MIESIAC>/instagram/ (dane z edycja.py)
"""
import subprocess
from pathlib import Path

from panele import CHROME, ZIELEN, TEKST, SZARY, JASNY

import edycja as E

BAZA = Path(__file__).resolve().parent
FOTY = BAZA / f"zrodla-{E.MIESIAC}" / "produkty"   # packshoty 1350 px (canva.py packshoty)
OUT = BAZA / f"zrodla-{E.MIESIAC}" / "instagram"
SKALA = 2


def ig_nazwa(n, ile=1):
    p = E.PRODUKTY[n]
    nazwa = p.get("ig") or p["krotko"].replace("dōTERRA ", "").replace("™", "")
    return f"{ile} × {nazwa}" if ile > 1 else nazwa


def poz(n, ile=1, gw=""):
    stem = E.PRODUKTY[n]["foto"].removesuffix(".png")
    return (stem + ("*2" if ile == 2 else ""), ig_nazwa(n, ile) + gw)


def zl(x):
    return f"{x:.2f}".replace(".", ",") + " zł"


KICKER = f"BOGO · dōTERRA · {E.OKRES}"
KUPUJESZ = [poz(z["kup"][0]) for z in E.ZESTAWY]
GRATIS = ([poz(g[0], g[3]) for z in E.ZESTAWY for g in z["gratis"]] + [poz(E.PREZENT[0])]
          + [poz(n, 1, "*") for n, _ in E.OFERTA["gratis_200pv"]])
PRZYPIS = "* gratis przy rejestracji z mojego polecenia" if E.OFERTA["gratis_200pv"] else ""
N_KUP = len(KUPUJESZ)
N_GRATIS = sum(g[3] for z in E.ZESTAWY for g in z["gratis"]) + 1 + len(E.OFERTA["gratis_200pv"])
_cena = sum(E.PRODUKTY[z["kup"][0]]["pln"] for z in E.ZESTAWY)
_bylo = sum(E.PRODUKTY[p[0]]["pln"] * p[3] for z in E.ZESTAWY for p in [z["kup"]] + z["gratis"]) + E.PRODUKTY[E.PREZENT[0]]["pln"]
CENA, BYLO = zl(_cena), zl(_bylo)

# format: wymiary, wysokość butelki, odstępy, rozmiary tekstu
FORMATY = {
    "relacja": dict(w=1080, h=1920, bh=245, top=230, dol=210, gap=36, h1=100, h2=72, cena=110, pill=30, et=21),
    "post": dict(w=1080, h=1350, bh=150, top=40, dol=40, gap=18, h1=70, h2=50, cena=78, pill=24, et=18),
}

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:__W__px;height:__H__px;overflow:hidden}
body{font-family:Inter,'Helvetica Neue',sans-serif;color:__TEKST__;position:relative;
  background:linear-gradient(160deg,#fcfbfa 0%,#faf9f6 50%,#eef2f0 100%);}
.blob{position:absolute;border-radius:50%;}
.b1{width:900px;height:900px;right:-380px;top:-300px;background:radial-gradient(circle,rgba(77,106,94,.13),rgba(77,106,94,0) 66%);}
.b2{width:800px;height:800px;left:-380px;bottom:-320px;background:radial-gradient(circle,rgba(120,113,108,.10),rgba(120,113,108,0) 68%);}
.wrap{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:__TOP__px 48px __DOL__px;}
.kicker{font-size:19px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;color:__ZIELEN__;margin-bottom:18px;}
h1{font-family:'Playfair Display',Georgia,serif;font-weight:600;text-align:center;line-height:1.02;letter-spacing:-.01em;}
h1 .a{display:block;font-size:__H1__px;}
h1 .b{display:block;font-size:__H2__px;color:__ZIELEN__;font-style:italic;margin-top:6px;}
.rule{width:84px;height:4px;background:__ZIELEN__;border-radius:2px;margin:__GAP__px 0;}
.pill{display:inline-block;font-size:__PILL__px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
  padding:12px 30px;border-radius:999px;margin:__GAP__px 0 calc(__GAP__px * .8);}
.pill.k{background:__ZIELEN__;color:#fff;}
.pill.g{border:3px solid __ZIELEN__;color:__ZIELEN__;}
.rz{display:grid;grid-template-columns:repeat(5,1fr);width:100%;column-gap:10px;row-gap:calc(__GAP__px * .7);}
.p{display:flex;flex-direction:column;align-items:center;}
.fot{height:__BH__px;display:flex;align-items:flex-end;justify-content:center;gap:4px;}
.fot img{height:100%;object-fit:contain;filter:drop-shadow(0 14px 22px rgba(28,25,23,.22));}
.fot.dwa img{height:86%;}
.et{margin-top:12px;font-size:__ET__px;font-weight:600;line-height:1.25;text-align:center;color:__TEKST__;min-height:2.5em;}
.przypis{margin-top:calc(__GAP__px * .6);font-size:__ET__px;font-weight:600;color:__SZARY__;}
.cena{display:flex;align-items:baseline;gap:26px;margin-top:calc(__GAP__px * .9);}
.cena .bylo{font-size:calc(__CENA__px * .4);font-weight:600;color:#a8a29e;text-decoration:line-through;}
.cena .jest{font-family:'Playfair Display',Georgia,serif;font-size:__CENA__px;font-weight:600;color:__ZIELEN__;line-height:1;}
"""

HTML = """<!DOCTYPE html><html lang="pl"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Playfair+Display:ital,wght@0,600;1,600&display=block" rel="stylesheet">
<style>__CSS__</style></head><body>
<div class="blob b1"></div><div class="blob b2"></div>
<div class="wrap">
  <div class="kicker">__KICKER__</div>
  <h1><span class="a">__N_RAZEM__ produktów</span><span class="b">w pakiecie BOGO</span></h1>
  <div class="pill k">Kupujesz __N_KUP__</div>
  <div class="rz">__KUP__</div>
  <div class="pill g">Dostajesz __N_GRATIS__ gratis</div>
  <div class="rz">__GRA__</div>
  <div class="przypis">__PRZYPIS__</div>
  <div class="cena"><span class="bylo">__BYLO__</span><span class="jest">__CENA__</span></div>
</div>
</body></html>"""


def img(slug):
    return f'<img src="{(FOTY / f"{slug}.png").as_uri()}">'


def komorki(lista):
    out = ""
    for slug, nazwa in lista:
        ile = 2 if slug.endswith("*2") else 1
        s = slug.removesuffix("*2")
        out += (f'<div class="p"><div class="fot{" dwa" if ile == 2 else ""}">{img(s) * ile}</div>'
                f'<div class="et">{nazwa}</div></div>')
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for nazwa, f in FORMATY.items():
        css = CSS
        for a, b in {"__W__": f["w"], "__H__": f["h"], "__TOP__": f["top"], "__DOL__": f["dol"], "__GAP__": f["gap"],
                     "__H1__": f["h1"], "__H2__": f["h2"], "__CENA__": f["cena"], "__PILL__": f["pill"],
                     "__ET__": f["et"], "__BH__": f["bh"], "__ZIELEN__": ZIELEN, "__TEKST__": TEKST,
                     "__SZARY__": SZARY, "__JASNY__": JASNY}.items():
            css = css.replace(a, str(b))
        html = (HTML.replace("__CSS__", css).replace("__KICKER__", KICKER)
                .replace("__KUP__", komorki(KUPUJESZ)).replace("__GRA__", komorki(GRATIS))
                .replace("__PRZYPIS__", PRZYPIS).replace("__N_RAZEM__", str(N_KUP + N_GRATIS))
                .replace("__N_KUP__", str(N_KUP)).replace("__N_GRATIS__", str(N_GRATIS)).replace("__BYLO__", BYLO).replace("__CENA__", CENA))
        hp = OUT / f"bogo-pakiet-{nazwa}.html"
        hp.write_text(html, encoding="utf-8")
        png = OUT / f"bogo-pakiet-{nazwa}.png"
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                        f"--force-device-scale-factor={SKALA}", f"--window-size={f['w']},{f['h']}",
                        "--virtual-time-budget=4000", f"--screenshot={png}", hp.as_uri()],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  {png.name}")


if __name__ == "__main__":
    main()
