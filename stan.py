#!/usr/bin/env python3
"""Stan grafik z kółeczkami dla edycji BOGO → zrodla-<MIESIAC>/stan-grafik.html (styl listy do odhaczania:
czeka na Ciebie · robię · gotowe).

  python3 stan.py                    → przebudowuje stronę z aktualnych danych (puszczaj po każdym przebiegu)
  python3 stan.py skany              → ten sam stan dla olejków ze skanów (SKANY) → canva/stan-grafiki-ze-skanow.html
  python3 stan.py bogo skany         → obie strony
  python3 stan.py w-canvie <slug>…   → po wstawieniu zatwierdzonych haseł w kółka: zapisuje, co jest w Canvie

Hasła rusza do Canvy dopiero zatwierdzenie w karcie hubu (kopia w repo: zatwierdzone {at, hasla}, edycja).
Zatwierdzone ≠ hasla-w-canvie.json → „Poprawiam grafikę”.

Źródła danych:
- katalog Canvy        canva/materialy/_katalog-grafik/katalog.json (strona, stan, języki)
- materiały per olejek canva/materialy/<slug>/zrodla.json — co obejrzane w skanach, WhatsAppie i na Discordzie
                       ({zrodlo: skan|whatsapp|discord, plik, rodzaj, glowny}); uzupełnia Claude po każdym przebiegu
- karty haseł          canva/hasla/output/<slug>.html (hasła z kolumny „Canva treści” = zrodlo „reflect”)
- wybór userki         repo lista-do-odhaczenia-dane/canva-hasla/<noteId>.json (gh api)

Kroki userki (skan do wysłania; „zaznacz hasła PL”, gdy 3 kolumny są pełne) idą też raz na listę dnia w apce
lista-do-odhaczenia (lista.json w tym samym repo); co wysłane — zrodla-<MIESIAC>/lista-wyslane.json.
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


# Zestawy produktów: „bogo” (bieżąca promocja) i „skany” (olejki ze skanem w Claude Inbox, bez grafiki — od 26.10.2026)
SKANY = [("lemon", "Cytryna"), ("lavender", "Lawenda"), ("peppermint", "Mięta pieprzowa"), ("tea-tree", "Drzewo herbaciane"),
         ("frankincense", "Kadzidło"), ("wild-orange", "Dzika pomarańcza"), ("copaiba", "Copaiba"),
         ("bergamotka", "Bergamotka", "bergamot-bergamotka"), ("marjoram", "Majeranek"), ("citronella", "Citronella"),
         ("balance", "Balance"), ("air", "Air (Breathe)"), ("deep-blue", "Deep Blue"), ("zengest", "ZenGest")]


def produkty_bogo():
    for n in C.produkty_promocji():
        p = E.PRODUKTY[n]
        foto = C.PRODUKTY_DIR / p["foto"]
        yield {"slug": p["slug"], "hub": p["slug"], "krotko": p["krotko"], "img": f"produkty/{p['foto']}" if foto.exists() else ""}


def produkty_skany():
    for s, nazwa, *hub in SKANY:
        rendery = sorted((MAT / s / "inspiracje-do-tla").glob("[0-9]*.png"), key=lambda f: len(f.name))
        yield {"slug": s, "hub": hub[0] if hub else s, "krotko": nazwa, "img": rendery[0].as_uri() if rendery else ""}


ZESTAWY = {
    "bogo": {"produkty": produkty_bogo, "wyj": WYJ, "tytul": f"Stan grafik · BOGO {E.OKRES_KROTKO}", "prefiks": "BOGO",
             "karta": "dokument „Bogo” + Claude", "wyslane": C.TU / f"zrodla-{E.MIESIAC}" / "lista-wyslane.json"},
    "skany": {"produkty": produkty_skany, "wyj": MAT.parent / "stan-grafiki-ze-skanow.html", "tytul": "Stan grafik · ze skanów z książki",
              "prefiks": "Grafiki ze skanów", "karta": "skan + Claude", "wyslane": MAT.parent / "stan-grafiki-ze-skanow-lista.json"},
}


def chip(p, href=None, dopisek=""):
    """Mały olejek ze zdjęciem — link, gdy jest dokąd prowadzić."""
    img = f'<img src="{html.escape(p["img"])}" alt="">' if p["img"] else ""
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


W_CANVIE = lambda slug: MAT / slug / "hasla-w-canvie.json"


def zapisz_w_canvie(slug):
    """Po wstawieniu haseł w kółka: zapamiętaj, które są w Canvie (stan porówna je z kolejnym zatwierdzeniem)."""
    d = karta(slug)
    k = kopia(f"{d['noteId']}.json") if d else {}
    z = (k.get("zatwierdzone") or {}).get("hasla")
    if not z:
        raise SystemExit(f"{slug}: hasła niezatwierdzone")
    W_CANVIE(slug).write_text(json.dumps({"hasla": z, "zatwierdzone": k["zatwierdzone"]["at"], "wstawione": datetime.now().isoformat(timespec="minutes")},
                                         ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{slug}: w Canvie {len(z)} haseł")


LISTA_REPO = "repos/emilia-chodorowska/lista-do-odhaczenia-dane/contents/lista.json"
DNI = ("Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela")


def do_listy(pozycje, WYSLANE):
    """Kroki userki → lista dnia (dzisiaj) w apce lista-do-odhaczenia. pozycje: [(klucz albo lista kluczy, etykieta, url)].
    Każdy klucz idzie raz (lista-wyslane.json) — odhaczona albo skasowana pozycja nie wraca przy kolejnym przebiegu."""
    import base64
    import random
    import string
    wyslane = json.loads(WYSLANE.read_text(encoding="utf-8")) if WYSLANE.exists() else {}
    pozycje = [([k] if isinstance(k, str) else k, e, u) for k, e, u in pozycje]
    nowe = [x for x in pozycje if any(k not in wyslane for k in x[0])]
    if not nowe:
        return
    def uid(prefix):
        ms, b36 = int(datetime.now().timestamp() * 1000), ""
        while ms:
            ms, r = divmod(ms, 36)
            b36 = "0123456789abcdefghijklmnopqrstuvwxyz"[r] + b36
        return prefix + b36 + "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    for _ in range(3):  # 409 = userka zapisała w międzyczasie → świeże pobranie i jeszcze raz
        r = subprocess.run(["gh", "api", LISTA_REPO], capture_output=True, text=True)
        if r.returncode:
            print("lista do odhaczania: nie pobrałam lista.json —", r.stderr.strip()); return
        meta = json.loads(r.stdout)
        d = json.loads(base64.b64decode(meta["content"]))
        dzis = datetime.now()
        kat = next((c for c in d["categories"] if c.get("day") == dzis.strftime("%Y-%m-%d") and not c.get("navSep")), None)
        if not kat:
            kat = {"id": uid("c"), "name": f"{DNI[dzis.weekday()]} {dzis.day}.{dzis.month:02d}", "day": dzis.strftime("%Y-%m-%d"), "items": []}
            d["categories"].append(kat)
        juz = {i.get("url") or i.get("label") for i in kat["items"]}
        for _, etykieta, url in nowe:
            if (url or etykieta) not in juz:
                poz = {"id": uid("i"), "label": etykieta, "checked": False, "mark": ""}
                if url:
                    poz["url"] = url
                kat["items"].append(poz)
        d["savedAt"] = int(dzis.timestamp() * 1000)
        d["savedAtLocal"] = dzis.strftime("%d.%m.%Y, %H:%M:%S")
        d["device"] = "Claude (skrypt)"
        body = json.dumps({"message": f"BOGO: {len(nowe)} poz. do listy {kat['name']}", "sha": meta["sha"],
                           "content": base64.b64encode(json.dumps(d, ensure_ascii=False, indent=1).encode()).decode()})
        r = subprocess.run(["gh", "api", "-X", "PUT", LISTA_REPO, "--input", "-"], input=body, capture_output=True, text=True)
        if r.returncode == 0:
            for klucze, etykieta, _ in nowe:
                for k in klucze:
                    wyslane[k] = dzis.strftime("%Y-%m-%d %H:%M")
                print(f"lista do odhaczania ({kat['name']}): {etykieta}")
            WYSLANE.write_text(json.dumps(wyslane, ensure_ascii=False, indent=1), encoding="utf-8")
            return
        if "409" not in r.stdout + r.stderr:
            print("lista do odhaczania: zapis nie przeszedł —", (r.stdout + r.stderr).strip()[:300]); return
    print("lista do odhaczania: 3× konflikt zapisu, spróbuję przy następnym przebiegu")


def main(zestaw="bogo"):
    Z = ZESTAWY[zestaw]
    kat = katalog()
    kopie = wybory()
    R = {k: [] for k in ("skan", "zaznacz", "tlo", "strona", "karta", "kol3", "kol3_stoi", "kolka", "kolka_stoi", "jezyki",
                        "ok_strona", "ok_tlo", "ok_skan", "ok_zrodla", "ok_kol3", "ok_hasla", "ok_kolka", "ok_wszystko", "do_listy", "skany_listy", "edycja", "poprawka", "przeglad")}
    sprawdzono = set()
    for p in Z["produkty"]():
        s = p["slug"]
        g = {x["jezyk"]: x for x in kat if x["slug"] == s}
        pl = g.get("pl")
        jezyki_gotowe = [j for j in JEZYKI if g.get(j, {}).get("stan") == "gotowa"]
        if len(jezyki_gotowe) == len(JEZYKI):
            R["ok_wszystko"].append(chip(p, (KAT / pl["plik"]).as_uri()))
            continue
        z = json.loads((MAT / s / "zrodla.json").read_text(encoding="utf-8")) if (MAT / s / "zrodla.json").exists() else {}
        hub = f"{HUB}#{p['hub']}"
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
            R["skany_listy"].append((f"skan:{s}", p["krotko"].replace("dōTERRA ", "")))
        if z.get("sprawdzono"):
            R["ok_zrodla"].append(chip(p))
            sprawdzono.add(z["sprawdzono"])
        d = karta(p["hub"])
        n_ct = sum(1 for h in (d or {}).get("haslaProposed", []) if h.get("zrodlo") == "reflect")
        if n_ct:
            R["ok_kol3"].append(chip(p, hub, str(n_ct)))
        elif skan:
            R["kol3"].append(chip(p, hub))
        else:
            R["kol3_stoi"].append(chip(p))
        # hasła PL
        k = kopia(f"{d['noteId']}.json") if d and f"{d.get('noteId')}.json" in kopie else {}
        zatw = (k.get("zatwierdzone") or {}).get("hasla") if not k.get("edycja") else None
        if not d:
            R["karta"].append(chip(p))
        elif zatw:
            R["ok_hasla"].append(chip(p, hub, str(len(zatw))))
        elif k.get("edycja"):
            R["edycja"].append(chip(p, hub))
        elif n_ct and not z.get("sprawdzono"):  # kolumna ze skanu jest, ale WhatsApp i Discord jeszcze nieprzejrzane
            R["przeglad"].append(chip(p, hub))
        elif n_ct:  # zaznaczanie dopiero przy komplecie kolumn
            R["zaznacz"].append(chip(p, hub))
            R["do_listy"].append((f"zaznacz-hasla:{s}", f"{Z['prefiks']}: zaznacz i zatwierdź hasła PL — {p['krotko'].replace('dōTERRA ', '')}", hub))
        # kółka i języki — Canva rusza dopiero po zatwierdzeniu; hasla-w-canvie.json = co jest teraz w kółkach
        w_canvie = json.loads(W_CANVIE(s).read_text(encoding="utf-8"))["hasla"] if W_CANVIE(s).exists() else None
        gotowa = bool(pl and pl["stan"] == "gotowa")
        if zatw and not gotowa:
            R["kolka"].append(chip(p, hub))
        elif zatw and w_canvie is not None and w_canvie != zatw:
            R["poprawka"].append(chip(p, hub))
        elif gotowa:
            R["ok_kolka"].append(chip(p, (KAT / pl["plik"]).as_uri()))
            brak = [j.upper() for j in JEZYKI if j not in jezyki_gotowe]
            R["jezyki"].append(chip(p, None, " · ".join(brak)))
        else:
            R["kolka_stoi"].append(chip(p))

    if R["skany_listy"]:  # skany jako jedna pozycja ze wszystkimi olejkami
        R["do_listy"].insert(0, ([k for k, _ in R["skany_listy"]], f"{Z['prefiks']}: skany z „Advanced Oil Magic” do grupy „Grafiki dla Claude” — "
                                 + ", ".join(n for _, n in R["skany_listy"]), None))
    do_listy(R["do_listy"], Z["wyslane"])
    daty = ", ".join(datetime.fromisoformat(x).strftime("%d.%m") for x in sorted(sprawdzono))
    ty = [
        wiersz("ty", "Wyślij skany stron z „Advanced Oil Magic” do grupy „Grafiki dla Claude” na WhatsAppie", R["skan"]),
        wiersz("ty", "Zaznacz i zatwierdź hasła PL w hubie", R["zaznacz"], "wszystkie kolumny wypełnione · klik w olejek otwiera jego kartę haseł"),
        wiersz("ty", "Hasła w trybie edycji — zatwierdź ponownie", R["edycja"], "grafika czeka przy poprzednio zatwierdzonych"),
    ]
    ja = [
        wiersz("ja", "Generuję tło", R["tlo"]),
        wiersz("ja", "Zakładam stronę w Canvie z gotowym tłem", R["strona"]),
        wiersz("ja", f"Robię kartę haseł ({Z['karta']})", R["karta"]),
        wiersz("ja", "Przeglądam Discord i WhatsApp — dołożę hasła z grafik", R["przeglad"]),
        wiersz("ja", "Dokładam kolumnę Skan · WhatsApp · Discord w hubie", R["kol3"]),
        wiersz("ja", "Wstawiam zatwierdzone hasła w kółka w Canvie", R["kolka"]),
        wiersz("ja", "Poprawiam grafikę — zmienione hasła", R["poprawka"]),
        wiersz("ja", "Robię wersje językowe", R["jezyki"], "przy olejku brakujące języki"),
    ]
    stoi = [
        wiersz("stoi", "Kolumna Skan · WhatsApp · Discord", R["kol3_stoi"], "po Twoich skanach"),
        wiersz("stoi", "Hasła w kółkach w Canvie", R["kolka_stoi"], "po zatwierdzeniu haseł"),
    ]
    ok = [
        wiersz("ok", "Wszystkie języki gotowe", R["ok_wszystko"]),
        wiersz("ok", "Hasła PL zatwierdzone", R["ok_hasla"], "liczba = zatwierdzone hasła"),
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
    Z["wyj"].write_text(SZABLON.replace("__TYTUL__", html.escape(Z["tytul"])).replace("__TERAZ__", teraz)
                   .replace("__TY__", sekcja("s-ty", "Czeka na Ciebie", ty, "Nic — wszystko po Twojej stronie zrobione."))
                   .replace("__JA__", sekcja("s-ja", "Robię", ja, "Nic w toku."))
                   .replace("__STOI__", sekcja("s-stoi", "Ruszę po Twoim kroku", stoi, "Nic nie czeka na Twój krok."))
                   .replace("__OK__", sekcja("s-ok", "Gotowe", ok, "Jeszcze nic.")),
                   encoding="utf-8")
    print(Z["wyj"])


SZABLON = """<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TYTUL__</title>
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
  .s-stoi .head{border-color:var(--s200)} .s-stoi .count{background:var(--s100);color:var(--s500)}
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
  <h1>__TYTUL__</h1>
  Stan z __TERAZ__ · odśwież kartę po moim przebiegu
  <div class="legend"><span><i class="l-ty"></i>czeka na Ciebie</span><span><i class="l-ja"></i>robię</span><span><i class="l-stoi"></i>ruszę po Twoim kroku</span><span><i class="l-ok"></i>gotowe</span></div>
</div>
__TY__
__JA__
__STOI__
__OK__
</div>
</body>
</html>
"""

if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["w-canvie"]:
        for s in sys.argv[2:]:
            zapisz_w_canvie(s)
        main()
    else:
        for z in (sys.argv[1:] or ["bogo"]):
            main(z)
