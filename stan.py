#!/usr/bin/env python3
"""Stan grafik z kółeczkami dla edycji BOGO → zrodla-<MIESIAC>/stan-grafik.html (styl listy do odhaczania:
czeka na Ciebie · robię · gotowe).

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


def chip(p, href=None, dopisek=""):
    """Mały olejek ze zdjęciem — link, gdy jest dokąd prowadzić."""
    foto = C.PRODUKTY_DIR / p["foto"]
    img = f'<img src="produkty/{html.escape(p["foto"])}" alt="">' if foto.exists() else ""
    nazwa = html.escape(p["krotko"].replace("dōTERRA ", "")) + (f' <b>{html.escape(dopisek)}</b>' if dopisek else "")
    if href:
        return f'<a class="chip" href="{html.escape(href)}" target="_blank" rel="noopener">{img}{nazwa}</a>'
    return f'<span class="chip">{img}{nazwa}</span>'


def wiersz(stan, tekst, chipy, pod=""):
    """stan: ty (czeka na Ciebie) · ja (robię) · stoi (u mnie, ale czeka na Twój krok) · ok (gotowe)."""
    if not chipy:
        return ""
    pod = f'<div class="pod">{pod}</div>' if pod else ""
    return (f'<div class="row {stan}"><span class="ico"></span><div class="tresc"><div class="lbl">{tekst}</div>{pod}'
            f'<div class="chips">{"".join(chipy)}</div></div></div>')


def main():
    kat = katalog()
    kopie = wybory()
    R = {k: [] for k in ("skan", "zaznacz", "tlo", "strona", "karta", "kol3", "kol3_stoi", "kolka", "kolka_stoi", "jezyki",
                        "ok_strona", "ok_tlo", "ok_skan", "ok_zrodla", "ok_kol3", "ok_hasla", "ok_kolka", "ok_wszystko")}
    sprawdzono = set()
    for n in C.produkty_promocji():
        p = E.PRODUKTY[n]
        s = p["slug"]
        g = {x["jezyk"]: x for x in kat if x["slug"] == s}
        pl = g.get("pl")
        jezyki_gotowe = [j for j in JEZYKI if g.get(j, {}).get("stan") == "gotowa"]
        if len(jezyki_gotowe) == len(JEZYKI):
            R["ok_wszystko"].append(chip(p, (KAT / pl["plik"]).as_uri()))
            continue
        z = json.loads((MAT / s / "zrodla.json").read_text(encoding="utf-8")) if (MAT / s / "zrodla.json").exists() else {}
        hub = f"{HUB}#{s}"
        # Canva + tło
        plik_tla, _ = C.tlo(s)
        if pl:
            R["ok_strona"].append(chip(p, (KAT / pl["plik"]).as_uri(), f"str. {pl['strona']}"))
            R["ok_tlo"].append(chip(p))
        elif plik_tla:
            R["ok_tlo"].append(chip(p, plik_tla.as_uri()))
            R["strona"].append(chip(p, plik_tla.as_uri()))
        else:
            R["tlo"].append(chip(p))
        # źródła haseł
        skan = [x for x in z.get("pozycje", []) if x["zrodlo"] == "skan"]
        if skan:
            R["ok_skan"].append(chip(p))
        else:
            R["skan"].append(chip(p))
        if z.get("sprawdzono"):
            R["ok_zrodla"].append(chip(p))
            sprawdzono.add(z["sprawdzono"])
        d = karta(s)
        n_ct = sum(1 for h in (d or {}).get("haslaProposed", []) if h.get("zrodlo") == "reflect")
        if n_ct:
            R["ok_kol3"].append(chip(p, hub, str(n_ct)))
        elif skan:
            R["kol3"].append(chip(p, hub))
        else:
            R["kol3_stoi"].append(chip(p))
        # hasła PL
        wybrane = None
        if not d:
            R["karta"].append(chip(p))
        elif f"{d.get('noteId')}.json" in kopie:
            wybrane = len(kopia(f"{d['noteId']}.json").get("zaznaczone", []))
            R["ok_hasla"].append(chip(p, hub, str(wybrane)))
        else:
            R["zaznacz"].append(chip(p, hub))
        # kółka i języki
        if pl and pl["stan"] == "gotowa":
            R["ok_kolka"].append(chip(p, (KAT / pl["plik"]).as_uri()))
            brak = [j.upper() for j in JEZYKI if j not in jezyki_gotowe]
            R["jezyki"].append(chip(p, None, " · ".join(brak)))
        elif wybrane:
            R["kolka"].append(chip(p))
        else:
            R["kolka_stoi"].append(chip(p))

    daty = ", ".join(datetime.fromisoformat(x).strftime("%d.%m") for x in sorted(sprawdzono))
    ty = [
        wiersz("ty", "Wyślij skany stron z „Advanced Oil Magic” do grupy „Grafiki dla Claude” na WhatsAppie", R["skan"]),
        wiersz("ty", "Zaznacz hasła PL w hubie", R["zaznacz"], "klik w olejek otwiera jego kartę haseł"),
    ]
    ja = [
        wiersz("ja", "Generuję tło", R["tlo"]),
        wiersz("ja", "Zakładam stronę w Canvie z gotowym tłem", R["strona"]),
        wiersz("ja", "Robię kartę haseł (dokument „Bogo” + Claude)", R["karta"]),
        wiersz("ja", "Dokładam kolumnę Skan · WhatsApp · Discord w hubie", R["kol3"]),
        wiersz("ja", "Wstawiam hasła w kółka w Canvie", R["kolka"]),
        wiersz("ja", "Robię wersje językowe", R["jezyki"], "przy olejku brakujące języki"),
        wiersz("stoi", "Kolumna Skan · WhatsApp · Discord", R["kol3_stoi"], "ruszę po Twoich skanach"),
        wiersz("stoi", "Hasła w kółkach w Canvie", R["kolka_stoi"], "ruszę po Twoim wyborze haseł"),
    ]
    ok = [
        wiersz("ok", "Wszystkie języki gotowe", R["ok_wszystko"]),
        wiersz("ok", "Hasła PL wybrane", R["ok_hasla"], "liczba = zaznaczone hasła"),
        wiersz("ok", "Kółka PL w Canvie", R["ok_kolka"]),
        wiersz("ok", "Kolumna Skan · WhatsApp · Discord", R["ok_kol3"]),
        wiersz("ok", "Skan dostałam", R["ok_skan"]),
        wiersz("ok", "WhatsApp i Discord przejrzane", R["ok_zrodla"], f"sprawdzone {daty}" if daty else ""),
        wiersz("ok", "Tło gotowe", R["ok_tlo"]),
        wiersz("ok", "Strona w Canvie", R["ok_strona"]),
    ]
    def sekcja(klasa, tytul, wiersze, pusto):
        wiersze = [w for w in wiersze if w]
        tresc = "".join(wiersze) or f'<div class="pusto">{pusto}</div>'
        return f'<section class="{klasa}"><div class="head"><h2>{tytul}</h2><span class="count">{len(wiersze)}</span></div>{tresc}</section>'
    teraz = datetime.now().strftime("%d.%m.%Y, %H:%M")
    WYJ.write_text(SZABLON.replace("__OKRES__", html.escape(E.OKRES_KROTKO)).replace("__TERAZ__", teraz)
                   .replace("__TY__", sekcja("s-ty", "Czeka na Ciebie", ty, "Nic — wszystko po Twojej stronie zrobione."))
                   .replace("__JA__", sekcja("s-ja", "Robię", ja, "Nic w toku."))
                   .replace("__OK__", sekcja("s-ok", "Gotowe", ok, "Jeszcze nic.")),
                   encoding="utf-8")
    print(WYJ)


SZABLON = """<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Stan grafik · BOGO __OKRES__</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='22' fill='%236f9285'/%3E%3Cpath d='M28 52l15 15 30-32' fill='none' stroke='white' stroke-width='10' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
<style>
  :root{--green:#6f9285;--green-soft:#ecf2f0;--green-dark:#46605a;
        --amber:#b7791f;--amber-soft:#fdf4e3;--amber-line:#f0d9a8;
        --blue:#4f6d8f;--blue-soft:#eef2f7;
        --s100:#f5f4f1;--s200:#ebe9e4;--s300:#cfcdc4;--s400:#70706c;--s500:#4a4a47;--s800:#151513;--line:#f2f1ed}
  *{box-sizing:border-box}
  body{margin:0;background:#fff;color:#000;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;-webkit-font-smoothing:antialiased;padding:36px 16px 60px}
  .wrap{max-width:760px;margin:0 auto}
  .top{font-size:13px;color:var(--s400);margin-bottom:26px}
  .top h1{font-size:30px;font-weight:600;letter-spacing:-.02em;margin:0 0 4px;color:#000}
  section{margin-bottom:34px}
  .head{display:flex;align-items:center;gap:10px;margin-bottom:6px;padding-bottom:8px;border-bottom:2px solid var(--s200)}
  .head h2{font-size:21px;font-weight:600;letter-spacing:-.01em;margin:0;flex:1}
  .count{font-size:13px;font-weight:600;min-width:24px;height:24px;border-radius:999px;display:inline-flex;align-items:center;justify-content:center;padding:0 8px}
  .s-ty .head{border-color:var(--amber-line)} .s-ty .count{background:var(--amber-soft);color:var(--amber)}
  .s-ja .head{border-color:#dbe3ec} .s-ja .count{background:var(--blue-soft);color:var(--blue)}
  .s-ok .head{border-color:#d5e2dd} .s-ok .count{background:var(--green-soft);color:var(--green-dark)}
  .row{display:flex;gap:14px;padding:12px 0;border-bottom:1px solid var(--line)}
  .row:last-child{border-bottom:0}
  .ico{width:22px;height:22px;border-radius:50%;flex-shrink:0;margin-top:1px;position:relative;border:2px solid var(--s300)}
  .row.ty .ico{border-color:var(--amber);background:var(--amber-soft)}
  .row.ja .ico{border:2px solid var(--blue-soft);border-top-color:var(--blue);animation:obrot 1.4s linear infinite}
  .row.stoi .ico{border:2px dashed var(--s300)}
  .row.ok .ico{background:var(--green);border-color:var(--green)}
  .row.ok .ico::after{content:'';position:absolute;left:6.8px;top:3.4px;width:4.6px;height:9.2px;border:solid #fff;border-width:0 1.7px 1.7px 0;transform:rotate(45deg)}
  @keyframes obrot{to{transform:rotate(360deg)}}
  @media (prefers-reduced-motion:reduce){.row.ja .ico{animation:none}}
  .tresc{flex:1;min-width:0}
  .lbl{font-size:16px;color:var(--s800);line-height:1.35}
  .row.ty .lbl{font-weight:600}
  .row.stoi .lbl{color:var(--s400)}
  .row.ok .lbl{color:var(--s400);text-decoration:line-through;text-decoration-color:var(--s300)}
  .pod{font-size:12.5px;color:var(--s400);margin-top:2px}
  .chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
  .chip{display:inline-flex;align-items:center;gap:6px;font-size:13px;color:var(--s500);background:var(--s100);border-radius:999px;padding:3px 10px 3px 4px;text-decoration:none;line-height:1.3}
  .chip img{height:22px;width:16px;object-fit:contain}
  .chip b{font-weight:600;color:var(--s800)}
  a.chip:hover{background:var(--green-soft);color:var(--green-dark)}
  .row.ty .chip{background:var(--amber-soft);color:#7a5414}
  .row.ty a.chip:hover{background:#fbe9c6}
  .row.ok .chip{opacity:.75}
  .pusto{font-size:14px;color:var(--s400);padding:12px 0}
  .legend{display:flex;gap:16px;flex-wrap:wrap;font-size:12.5px;color:var(--s400);margin-top:10px}
  .legend span{display:inline-flex;align-items:center;gap:6px}
  .legend i{width:12px;height:12px;border-radius:50%;display:inline-block;border:2px solid var(--s300)}
  .legend .l-ty{border-color:var(--amber);background:var(--amber-soft)} .legend .l-ja{border-color:var(--blue-soft);border-top-color:var(--blue)}
  .legend .l-stoi{border-style:dashed} .legend .l-ok{background:var(--green);border-color:var(--green)}
</style>
</head>
<body>
<div class="wrap">
<div class="top">
  <h1>Stan grafik · BOGO __OKRES__</h1>
  Stan z __TERAZ__ · odśwież kartę po moim przebiegu
  <div class="legend"><span><i class="l-ty"></i>czeka na Ciebie</span><span><i class="l-ja"></i>robię</span><span><i class="l-stoi"></i>u mnie, czeka na Twój krok</span><span><i class="l-ok"></i>gotowe</span></div>
</div>
__TY__
__JA__
__OK__
</div>
</body>
</html>
"""

if __name__ == "__main__":
    main()
