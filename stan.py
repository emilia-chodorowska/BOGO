#!/usr/bin/env python3
"""Stan grafik z kółeczkami dla edycji BOGO → zrodla-<MIESIAC>/stan-grafik.html (styl Kappahl).

  python3 stan.py            → przebudowuje stronę z aktualnych danych (puszczaj po każdym przebiegu)

Źródła danych:
- katalog Canvy        canva/materialy/_katalog-grafik/katalog.json (strona, stan, języki)
- materiały per olejek canva/materialy/<slug>/zrodla.json — co obejrzane w skanach, WhatsAppie i na Discordzie
                       ({zrodlo: skan|whatsapp|discord, plik, rodzaj, glowny}); uzupełnia Claude po każdym przebiegu
- karty haseł          canva/hasla/output/<slug>.html (hasła z kolumny „Canva treści” = zrodlo „reflect”)
- wybór userki         repo lista-do-odhaczenia-dane/canva-hasla/<noteId>.json (gh api)
"""
import html
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

import canva as C
import edycja as E

MAT = C.MAT
KAT = MAT / "_katalog-grafik"
WYJ = C.TU / f"zrodla-{E.MIESIAC}" / "stan-grafik.html"
HUB = "https://emilia-chodorowska.github.io/canva-hasla/"
DATA_RE = re.compile(r'<script id="hasla-data" type="application/json">(.*?)</script>', re.S)
JEZYKI = ("pl", "en", "de", "uk")


def katalog():
    return json.loads((KAT / "katalog.json").read_text(encoding="utf-8"))["grafiki"] if (KAT / "katalog.json").exists() else []


def wybory():
    """Nazwy plików kopii wyboru haseł w repo (noteId.json) — puste, gdy gh nie odpowiada."""
    r = subprocess.run(["gh", "api", "repos/emilia-chodorowska/lista-do-odhaczenia-dane/contents/canva-hasla", "--jq", ".[].name"],
                       capture_output=True, text=True)
    return set(r.stdout.split()) if r.returncode == 0 else set()


def kopia(nazwa):
    r = subprocess.run(["gh", "api", f"repos/emilia-chodorowska/lista-do-odhaczenia-dane/contents/canva-hasla/{nazwa}", "--jq", ".content"],
                       capture_output=True, text=True)
    if r.returncode:
        return {}
    import base64
    return json.loads(base64.b64decode(r.stdout))


def karta(slug):
    p = C.HASLA / f"{slug}.html"
    if not p.exists():
        return None
    return json.loads(DATA_RE.search(p.read_text(encoding="utf-8")).group(1))


def pill(kind, text, href=None):
    t = html.escape(text)
    if href:
        return f'<a class="p {kind}" href="{html.escape(href)}" target="_blank" rel="noopener">{t}</a>'
    return f'<span class="p {kind}">{t}</span>'


def komorka_zrodla(z, zrodlo, slug):
    poz = [p for p in z.get("pozycje", []) if p["zrodlo"] == zrodlo]
    glowne = [p for p in poz if p["glowny"]]
    def href(p):
        if p["plik"].startswith("reflect:"):
            return "https://reflect.app/g/emiliachodorowska/" + p["plik"].split(":", 1)[1]
        return (MAT / slug / "poprzednie-grafiki" / p["plik"]).as_uri()
    if glowne:
        rodzaje = list(dict.fromkeys(re.sub(r"\s*\(.*?\)", "", p["rodzaj"]) for p in glowne))
        tekst = " + ".join(rodzaje[:2]) + (f" +{len(rodzaje) - 2}" if len(rodzaje) > 2 else "")
        return pill("ok", tekst, href(glowne[0]))
    uw = z.get("uwagi", {}).get(zrodlo)
    if poz:
        return pill("no", uw or "tylko " + poz[0]["rodzaj"], href(poz[0]))
    if zrodlo == "skan":
        return pill("ty", "czekam")
    return pill("no", uw or "brak")


def main():
    kat = katalog()
    kopie = wybory()
    wiersze, gotowe = [], []
    for n in C.produkty_promocji():
        p = E.PRODUKTY[n]
        s = p["slug"]
        g = {x["jezyk"]: x for x in kat if x["slug"] == s}
        pl = g.get("pl")
        jezyki_gotowe = [j for j in JEZYKI if g.get(j, {}).get("stan") == "gotowa"]
        if len(jezyki_gotowe) == len(JEZYKI):
            gotowe.append((p["krotko"], (KAT / pl["plik"]).as_uri()))
            continue
        z = json.loads((MAT / s / "zrodla.json").read_text(encoding="utf-8")) if (MAT / s / "zrodla.json").exists() else {}
        strona = pill("ok", f"str. {pl['strona']}", (KAT / pl["plik"]).as_uri()) if pl else pill("cl", "brak · nowa strona")
        d = karta(s)
        ma_skan = any(x["zrodlo"] == "skan" for x in z.get("pozycje", []))
        n_ct = sum(1 for h in (d or {}).get("haslaProposed", []) if h.get("zrodlo") == "reflect")
        if not ma_skan:
            ct = pill("no", "czeka na skan")
        elif n_ct:
            ct = pill("ok", f"{n_ct} haseł", f"{HUB}#{s}")
        else:
            ct = pill("cl", "do zbudowania")
        if not d:
            hasla = pill("ty", "brak haseł")
        elif f"{d.get('noteId')}.json" in kopie:
            zazn = kopia(f"{d['noteId']}.json").get("zaznaczone", [])
            hasla = pill("ok", f"wybrane {len(zazn)}", f"{HUB}#{s}")
        else:
            hasla = pill("ty", "do wyboru", f"{HUB}#{s}")
        if not pl:
            kolka = pill("cl", "nowa strona")
        elif pl["stan"] == "puste-kolka":
            kolka = pill("cl", "puste kółka")
        else:
            kolka = pill("ok" if jezyki_gotowe else "cl", " · ".join(j.upper() for j in jezyki_gotowe) or pl["stan"])
        foto = C.PRODUKTY_DIR / p["foto"]
        img = f'<img src="produkty/{html.escape(p["foto"])}" alt="">' if foto.exists() else ""
        wiersze.append(f'<tr><td><span class="prod">{img}<span>{html.escape(p["krotko"].replace("dōTERRA ", ""))}</span></span></td><td>{strona}</td>'
                       f'<td>{komorka_zrodla(z, "skan", s)}</td><td>{komorka_zrodla(z, "whatsapp", s)}</td>'
                       f'<td>{komorka_zrodla(z, "discord", s)}</td><td>{ct}</td><td>{hasla}</td><td>{kolka}</td></tr>')
    teraz = datetime.now().strftime("%d.%m.%Y, %H:%M")
    WYJ.write_text(SZABLON.replace("__OKRES__", html.escape(E.OKRES_KROTKO)).replace("__TERAZ__", teraz)
                   .replace("__WIERSZE__", "\n".join(wiersze))
                   .replace("__GOTOWE__", "".join(f'<a class="p ok" href="{h}" target="_blank" rel="noopener">{html.escape(t)}</a>' for t, h in gotowe)),
                   encoding="utf-8")
    print(WYJ)


SZABLON = """<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Stan grafik · BOGO __OKRES__</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='22' fill='%234d6a5e'/%3E%3Ccircle cx='38' cy='40' r='16' fill='%23fcfbfa'/%3E%3Ccircle cx='64' cy='62' r='16' fill='%23fcfbfa' fill-opacity='.6'/%3E%3C/svg%3E">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Playfair+Display:wght@500;600&display=swap" rel="stylesheet">
<style>
  :root{--bg:#f1ede7;--card:#fcfbfa;--ink:#3f3a35;--muted:#8a857d;--line:#ece7e0;
        --sage:#4d6a5e;--sage-bg:#eef2f0;--sage-line:#dfe7e3;
        --sand:#8a6a45;--sand-bg:#f5ede2;--sand-line:#eadcc8;
        --mist:#5f6b78;--mist-bg:#eef0f3;--mist-line:#e0e4ea;
        --off:#a29d95;--off-bg:#f3f1ee}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,-apple-system,sans-serif;padding:40px 16px 60px}
  .wrap{max-width:var(--maxw,1180px);margin:0 auto}
  body[data-wide="1"] .wrap{max-width:none;padding:0 24px}
  header{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap;margin-bottom:22px}
  .eyebrow{font-size:11px;letter-spacing:.30em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
  h1{font-family:"Playfair Display",Georgia,serif;font-weight:500;font-size:34px;margin:0;letter-spacing:-.3px}
  .kiedy{font-size:13px;color:var(--muted);margin-top:8px}
  .btn{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);background:var(--card);border-radius:999px;padding:7px 14px;font:inherit;font-size:13px;color:var(--muted);cursor:pointer}
  .btn:hover{color:var(--ink)} .btn svg{width:15px;height:15px}
  .legend{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 14px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:18px;overflow-x:auto;box-shadow:0 10px 30px rgba(63,58,53,.06)}
  table{border-collapse:collapse;width:100%;font-size:13.5px}
  th{font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);font-weight:500;text-align:left;padding:16px 14px 12px;border-bottom:1px solid var(--line);white-space:nowrap}
  td{padding:12px 14px;border-bottom:1px solid var(--line);white-space:nowrap;vertical-align:middle}
  tr:last-child td{border-bottom:0}
  .prod{display:flex;align-items:center;gap:12px;font-family:"Playfair Display",Georgia,serif;font-size:16px}
  .prod img{height:40px;width:28px;object-fit:contain}
  .p{display:inline-block;font-size:12.5px;font-weight:500;border-radius:999px;padding:4px 11px;border:1px solid transparent;text-decoration:none}
  a.p:hover{filter:brightness(.96);text-decoration:underline}
  .p.ok{background:var(--sage-bg);color:var(--sage);border-color:var(--sage-line)}
  .p.ty{background:var(--sand-bg);color:var(--sand);border-color:var(--sand-line)}
  .p.cl{background:var(--mist-bg);color:var(--mist);border-color:var(--mist-line)}
  .p.no{background:var(--off-bg);color:var(--off)}
  .done{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:16px 4px 0;font-size:13px;color:var(--muted)}
  .stopka{margin-top:28px;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--sage)}
</style>
</head>
<body>
<div class="wrap">
<header>
  <div>
    <div class="eyebrow">Grafiki z kółeczkami · BOGO __OKRES__</div>
    <h1>Stan grafik</h1>
    <div class="kiedy">Stan z __TERAZ__ · skan, WhatsApp i Discord sprawdzam przy każdym przebiegu</div>
  </div>
  <button class="btn" id="wideBtn" type="button"></button>
</header>
<div class="legend"><span class="p ok">jest</span><span class="p ty">Twoja kolej</span><span class="p cl">moja kolej</span><span class="p no">brak</span></div>
<div class="card"><table>
<thead><tr><th>Produkt</th><th>Strona w Canvie</th><th>Skan z książki</th><th>WhatsApp</th><th>Discord</th><th>Canva treści</th><th>Hasła PL</th><th>Kółka PL · EN · DE · UK</th></tr></thead>
<tbody>
__WIERSZE__
</tbody></table></div>
<div class="done">Gotowe we wszystkich językach: __GOTOWE__</div>
<div class="stopka">dōTERRA · BOGO __OKRES__</div>
</div>
<script>
(function(){
  var b=document.getElementById('wideBtn');
  var ico={max:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>',
           min:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/><line x1="14" y1="10" x2="21" y2="3"/><line x1="3" y1="21" x2="10" y2="14"/></svg>'};
  function set(w){document.body.dataset.wide=w?'1':'0';b.innerHTML=w?ico.min+'Zwykła szerokość':ico.max+'Szeroki widok';try{localStorage.setItem('stanGrafikWide',w?'1':'0')}catch(e){}}
  var w=false;try{w=localStorage.getItem('stanGrafikWide')==='1'}catch(e){}
  set(w);b.onclick=function(){set(document.body.dataset.wide!=='1')};
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
