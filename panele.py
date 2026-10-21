#!/usr/bin/env python3
"""Plansze 1920x1080 do poziomej wersji sklejki BOGO (wzór: relacja-yt, wariant D).

Pion nagrania stoi po lewej (VID_W px), panel po prawej: para, rola (kupujesz / gratis),
nazwa, pojemność, opis, zdjęcia produktów. Kolory i fonty ze strony BOGO.
Definicje: "panele" w sklejka-RRRR-MM.json. Bez cen — decyzja userki.

  python3 panele.py sklejka-2026-10.json     # PNG do <wynik>/panele/
"""
import base64
import json
import struct
import subprocess
import sys
from pathlib import Path


CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
VID_W = 608   # 1080x1920 przeskalowane do wysokości 1080 (w px CSS)
SKALA = 2     # render 2x → plansze i film 3840x2160 (ostre butelki na dużym ekranie i lepsza jakość na YouTube)

ZIELEN = "#4d6a5e"
TEKST = "#1c1917"
SZARY = "#57534e"
JASNY = "#78716c"

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1920px;height:1080px;overflow:hidden}
body{font-family:Inter,'Helvetica Neue',sans-serif;background:linear-gradient(122deg,#fcfbfa 0%,#faf9f6 50%,#eef2f0 100%);}
.blob{position:absolute;border-radius:50%;}
.b1{width:980px;height:980px;right:-260px;top:-360px;background:radial-gradient(circle,rgba(77,106,94,.12),rgba(77,106,94,0) 66%);}
.b2{width:760px;height:760px;right:160px;bottom:-430px;background:radial-gradient(circle,rgba(120,113,108,.10),rgba(120,113,108,0) 68%);}
.hole{position:absolute;left:0;top:0;width:__VW__px;height:1080px;background:#000;}
.shadow{position:absolute;left:__VW__px;top:0;width:70px;height:1080px;background:linear-gradient(90deg,rgba(28,25,23,.14),rgba(28,25,23,0));}
.panel{position:absolute;left:__PL__px;top:0;width:__PW__px;height:1080px;display:flex;align-items:center;gap:56px;}
.txt{flex:1 0 500px;min-width:0;}
.kicker{white-space:nowrap;font-size:20px;font-weight:700;letter-spacing:.24em;text-transform:uppercase;color:__ZIELEN__;margin-bottom:22px;}
.rola{display:inline-block;font-size:17px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
  padding:8px 18px;border-radius:999px;margin-bottom:22px;}
.rola.k{background:__ZIELEN__;color:#fff;}
.rola.g{border:2px solid __ZIELEN__;color:__ZIELEN__;}
.name{font-family:'Playfair Display',Georgia,serif;font-size:__NS__px;font-weight:600;letter-spacing:-.01em;line-height:1.1;color:__TEKST__;}
.meta{font-size:24px;font-weight:600;color:__SZARY__;margin-top:16px;}
.rule{width:84px;height:4px;background:__ZIELEN__;border-radius:2px;margin:26px 0 24px;}
.desc{font-size:26px;line-height:1.55;color:__SZARY__;}
.pic{flex:0 0 auto;display:flex;align-items:flex-end;justify-content:center;gap:18px;}
.grupy{flex:0 0 auto;display:flex;flex-direction:column;gap:22px;}
.grupa .et{font-size:15px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:__ZIELEN__;margin-bottom:10px;}
.grupa .rz{display:flex;align-items:flex-end;gap:8px;}
.grupa img{height:__GH__px;object-fit:contain;filter:drop-shadow(0 12px 22px rgba(28,25,23,.2));}
.pic.siatka{flex-wrap:wrap;max-width:450px;row-gap:28px;}
.pic img{height:__PICH__px;object-fit:contain;filter:drop-shadow(0 22px 40px rgba(28,25,23,.22));}
.foot{position:absolute;bottom:58px;left:__PL__px;font-size:19px;color:__JASNY__;}
.num{position:absolute;top:56px;right:88px;font-size:18px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:#a8a29e}
"""

HTML = """<!DOCTYPE html><html lang="pl"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Playfair+Display:wght@600&display=block" rel="stylesheet">
<style>__CSS__</style></head><body>
<div class="blob b1"></div><div class="blob b2"></div>
<div class="hole"></div><div class="shadow"></div>
<div class="num">__NUM__</div>
<div class="panel">
  <div class="txt">
    <div class="kicker">BOGO · dōTERRA · październik 2026</div>
    __ROLA__
    <div class="name">__NAME__</div>
    __META__
    <div class="rule"></div>
    <div class="desc">__DESC__</div>
  </div>
  <div class="pic__SIATKA__">__PIC__</div>
</div>
<div class="foot">__STOPKA__</div>
</body></html>"""


def meta(p):
    if "ml" not in p:
        return ""
    return f'<div class="meta">{p["ml"]}' + (f" × {p['ilosc']}" if p.get("ilosc", 1) > 1 else "") + "</div>"


def buduj(cfg_path):
    cfg_path = Path(cfg_path).resolve()
    cfg = json.loads(cfg_path.read_text())
    baza = cfg_path.parent
    out = baza / cfg["wynik"] / "panele"
    out.mkdir(parents=True, exist_ok=True)
    foty = baza / cfg["zdjecia"]
    etykiety = {pl["panel"]: cz["etykieta"] for cz in cfg["czesci"] for pl in cz["plansze"]}
    pl_x = VID_W + 86
    pw = 1920 - pl_x - 86
    for klucz, p in cfg["panele"].items():
        img = lambda z: f'<img src="data:image/png;base64,{base64.b64encode((foty / f"{z}.png").read_bytes()).decode()}">'
        if "grupy" in p:   # kilka podpisanych rzędów butelek (np. cały zestaw)
            n, pich = 0, 0
            imgs = "".join(f'<div class="grupa"><div class="et">{g["etykieta"]}</div><div class="rz">'
                           + "".join(img(z) for z in g["zdjecia"]) + "</div></div>" for g in p["grupy"])
        else:
            n = len(p["zdjecia"])
            pich = 600 if n == 1 else (520 if n == 2 else (260 if n <= 4 else 230))
            imgs = "".join(img(z) for z in p["zdjecia"])
        ns = 66 if len(p["nazwa"]) < 22 else (54 if len(p["nazwa"]) < 34 else 46)
        rola = p.get("rola")
        rola_html = (f'<div class="rola {"k" if rola == "kupujesz" else "g"}">{rola}</div>' if rola else "")
        css = CSS
        for a, b in {"__VW__": VID_W, "__PL__": pl_x, "__PW__": pw, "__NS__": ns, "__PICH__": pich, "__GH__": 170,
                     "__ZIELEN__": ZIELEN, "__TEKST__": TEKST, "__SZARY__": SZARY, "__JASNY__": JASNY}.items():
            css = css.replace(a, str(b))
        html = (HTML.replace("__CSS__", css).replace("__NUM__", etykiety.get(klucz, ""))
                .replace("__ROLA__", rola_html).replace("__NAME__", p["nazwa"])
                .replace("__META__", meta(p)).replace("__DESC__", p["opis"])
                .replace("__PIC__", imgs).replace('<div class="pic__SIATKA__">', '<div class="grupy">' if "grupy" in p else
                             '<div class="pic' + (" siatka" if n >= 5 else "") + '">').replace("__STOPKA__", cfg["stopka_planszy"]))
        hp = out / f"{klucz}.html"
        hp.write_text(html, encoding="utf-8")
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                        f"--force-device-scale-factor={SKALA}", "--window-size=1920,1080",
                        "--virtual-time-budget=4000", f"--screenshot={out / f'{klucz}.png'}",
                        hp.as_uri()], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  {klucz}.png")


if __name__ == "__main__":
    buduj(sys.argv[1])
