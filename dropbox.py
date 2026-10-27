#!/usr/bin/env python3
"""Wgrywanie na Dropbox przez rclone (konto `db-emilia:`), bez przeglądarki.

  python3 dropbox.py em                   → mój folder „BOGO Em/<MIESIAC>/”: wszystko, co ważne na koniec;
                                            składany w ~/MyProjects/doTERRA/BOGO Em/ (Finder), potem kopia na Dropbox
  python3 dropbox.py whatsapp             → ten sam komplet co „em” (+ gotowe grafiki z kółeczkami BOGO z katalogu Canvy)
                                            do grupy WhatsApp „BOGO od Claude”; Dropbox zostaje jako kopia (decyzja 27.10.2026).
                                            Wysyła tylko nowe/zmienione pliki (BOGO Em/<MIESIAC>/.wyslane-whatsapp.json, md5).
  python3 dropbox.py grafiki-ewy "<link>" → grafiki od Ewy (link dropbox.com/home/… albo ścieżka) do
                                            „BOGO Em/<MIESIAC>/Grafiki Ewy (WhatsApp)” — do wysyłania klientom

`rclone copy` tylko dokłada i nadpisuje zmienione pliki, niczego nie kasuje.
Źródło zdjęć: zrodla-<MIESIAC>/dropbox/2 Zdjecia zestawow/ (po jednym na zestaw, gratis i pakiet, bez przycinania).
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import edycja as E

TU = Path(__file__).resolve().parent
ZR = TU / f"zrodla-{E.MIESIAC}"
KONTO = "db-emilia:"
ZDJECIA = ZR / "dropbox" / "2 Zdjecia zestawow"
LOKALNIE = TU.parent / "BOGO Em"  # poza repo BOGO (Pages publikuje wszystko)


def kopiuj(zrodlo, cel, *flagi):
    zrodlo = Path(zrodlo)
    if not zrodlo.exists() or (zrodlo.is_dir() and not any(zrodlo.iterdir())):
        print(f"  BRAK: {zrodlo.relative_to(TU)}")
        return
    subprocess.run(["rclone", "copy", str(zrodlo), KONTO + cel, "--exclude", ".DS_Store", *flagi], check=True)
    print(f"  ok  {cel}")


def linki():
    oferta = f"https://emilia-chodorowska.github.io/new-client-offer/{E.OFERTA['folder']}/"
    l = [f"BOGO {E.OKRES}", "",
         f"Strona BOGO (PLN): https://emilia-chodorowska.github.io/BOGO/",
         f"Strona BOGO (EUR): https://emilia-chodorowska.github.io/BOGO/index-eur.html",
         f"Rejestracja z pakietem BOGO: {oferta}",
         f"Rejestracja, widok zespołu: {oferta}?team=true",
         "Hub doTERRA (sekcja BOGO): https://emilia-chodorowska.github.io/doterra-hub/"]
    yt = ZR / "film" / "yt-stan.json"
    if yt.exists():
        d = json.loads(yt.read_text(encoding="utf-8"))
        l += ["", "Film z nagrań zespołu (YouTube, niepubliczne):"]
        if d.get("playlista"):
            l.append(f"Playlista: https://www.youtube.com/playlist?list={d['playlista']}")
        for k, v in d.items():
            if isinstance(v, dict) and v.get("video_id"):
                l.append(f"{k}: https://youtu.be/{v['video_id']}")
    return "\n".join(l) + "\n"


def em():
    """Składa folder lokalnie (widać go w Finderze), potem kopia na Dropbox."""
    lok = LOKALNIE / E.MIESIAC
    lok.mkdir(parents=True, exist_ok=True)
    (lok / "Linki.txt").write_text(linki(), encoding="utf-8")

    def wrzuc(zrodlo, nazwa):
        zrodlo = Path(zrodlo)
        if not zrodlo.exists():
            print(f"  BRAK: {zrodlo}")
            return
        shutil.copytree(zrodlo, lok / nazwa, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".DS_Store"))

    wrzuc(TU / f"screeny-{E.MIESIAC}", "Screeny kart")
    (lok / "Screeny z maila").mkdir(exist_ok=True)
    for n, cel in (("mail-5-par.png", "1 Piec par.png"), ("mail-pakiet.png", "2 Pakiet i gratis.png")):
        if (ZR / "mail" / n).exists():
            shutil.copy2(ZR / "mail" / n, lok / "Screeny z maila" / cel)
        else:
            print(f"  BRAK: zrodla-{E.MIESIAC}/mail/{n}")
    wrzuc(ZDJECIA, "Zdjecia zestawow")
    (lok / "Instagram").mkdir(exist_ok=True)
    for png in (ZR / "instagram").glob("*.png"):
        shutil.copy2(png, lok / "Instagram" / png.name)
    for pdf in ZR.glob("PL_*.pdf"):
        shutil.copy2(pdf, lok / f"Broszura BOGO {E.MIESIAC} PL.pdf")
    wrzuc(ZR / "rolki", "Rolki doTERRA")
    wrzuc(Path.home() / f"MyProjects/canva/materialy/_wygenerowane-bogo-{E.MIESIAC}/do-canvy", "Tla do Canvy")
    print(f"  lokalnie: {lok}")
    kopiuj(lok, f"BOGO Em/{E.MIESIAC}")


GRUPA_WA = "BOGO od Claude"
EGO_BIN = str(Path.home() / ".local/bin/ego-browser")
WA_SKRYPT = Path.home() / "MyProjects/canva/proces/automaty/ego/wyslij_whatsapp.mjs"
KAT = Path.home() / "MyProjects/canva/materialy/_katalog-grafik"
OBRAZY = {".png", ".jpg", ".jpeg", ".webp"}
FILMY = {".mp4", ".mov"}  # przez „Zdjęcia i filmy” WhatsApp Web nie robi podglądu rolek → idą jako dokument


def grafiki_kolka():
    """Gotowe grafiki z kółeczkami produktów bieżącej promocji (katalog Canvy), wszystkie gotowe języki."""
    import canva as C
    slugi = {E.PRODUKTY[n]["slug"] for n in C.produkty_promocji()}
    try:
        kat = json.loads((KAT / "katalog.json").read_text(encoding="utf-8"))["grafiki"]
    except Exception:
        return []
    kol = {"pl": 0, "en": 1, "de": 2, "uk": 3}
    g = [x for x in kat if x["slug"] in slugi and x["stan"] == "gotowa" and (KAT / x["plik"]).exists()]
    return [KAT / x["plik"] for x in sorted(g, key=lambda x: (kol.get(x["jezyk"], 9), x["strona"]))]


def whatsapp():
    """Komplet BOGO do grupy WhatsApp: nagłówek sekcji (tekst) + pliki; tylko to, czego jeszcze nie wysłano."""
    em_lok = LOKALNIE / E.MIESIAC
    if not em_lok.exists():
        sys.exit(f"Brak {em_lok} — najpierw python3 dropbox.py em")
    stan_p = em_lok / ".wyslane-whatsapp.json"
    stan = json.loads(stan_p.read_text(encoding="utf-8")) if stan_p.exists() else {}
    md5 = lambda f: hashlib.md5(Path(f).read_bytes()).hexdigest()
    nowe = lambda pliki: [f for f in pliki if stan.get(str(f)) != md5(f)]
    sekcje = [
        ("Zdjęcia zestawów", sorted((em_lok / "Zdjecia zestawow").glob("*"))),
        ("Grafiki z kółeczkami", grafiki_kolka()),
        ("Screeny z maila", sorted((em_lok / "Screeny z maila").glob("*"))),
        ("Screeny kart · PLN", sorted((em_lok / "Screeny kart/PLN").glob("*"))),
        ("Screeny kart · EUR", sorted((em_lok / "Screeny kart/EUR").glob("*"))),
        ("Instagram", sorted((em_lok / "Instagram").glob("*"))),
        ("Grafiki Ewy", sorted((em_lok / "Grafiki Ewy (WhatsApp)").glob("*"))),
        ("Tła do Canvy", sorted((em_lok / "Tla do Canvy").glob("*"))),
        ("Rolki doTERRA", sorted((em_lok / "Rolki doTERRA").glob("*"))),
    ]
    kroki, pliki_krokow = [], []
    linki_p = em_lok / "Linki.txt"
    if linki_p.exists() and linki_p in nowe([linki_p]):
        kroki.append({"tekst": linki_p.read_text(encoding="utf-8").strip()}); pliki_krokow.append([linki_p])
    for pdf in nowe(sorted(em_lok.glob("*.pdf"))):
        kroki.append({"dokument": str(pdf)}); pliki_krokow.append([pdf])
    naglowki = set(stan.get("#naglowki", []))
    for tytul, pliki in sekcje:
        zdj = nowe([f for f in pliki if f.suffix.lower() in OBRAZY])
        filmy = nowe([f for f in pliki if f.suffix.lower() in FILMY])
        if not zdj and not filmy:
            continue
        if tytul not in naglowki:  # nagłówek sekcji raz na miesiąc, nie przy każdym dosłaniu
            kroki.append({"tekst": f"*{tytul}* · BOGO {E.OKRES}"}); pliki_krokow.append([("#naglowek", tytul)])
        for i in range(0, len(zdj), 30):
            kroki.append({"zdjecia": [str(f) for f in zdj[i:i + 30]]}); pliki_krokow.append(zdj[i:i + 30])
        for f in filmy:
            kroki.append({"dokument": str(f)}); pliki_krokow.append([f])
    if not kroki:
        print("  nic nowego do wysłania")
        return
    print(f"  {len(kroki)} wiadomości do „{GRUPA_WA}”…", flush=True)
    log = em_lok / ".wyslane-whatsapp-log.json"
    zad = {"grupa": GRUPA_WA, "kroki": kroki, "log": str(log)}
    r = subprocess.run([EGO_BIN, "nodejs"], input=f"const ZADANIE = {json.dumps(zad, ensure_ascii=False)};\n" + WA_SKRYPT.read_text(encoding="utf-8"),
                       capture_output=True, text=True, timeout=3600)
    out = r.stdout + r.stderr
    ok = sum(1 for l in out.splitlines() if l.startswith("KROK OK:"))
    for pl in pliki_krokow[:ok]:
        for f in pl:
            if isinstance(f, tuple):
                naglowki.add(f[1])
            else:
                stan[str(f)] = md5(f)
    stan["#naglowki"] = sorted(naglowki)
    stan_p.write_text(json.dumps(stan, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(l for l in out.strip().splitlines()[-25:]))
    if ok < len(kroki):
        sys.exit(1)


def grafiki_ewy(link):
    """Proces zależny od Ewy: jej gotowe grafiki do mojego folderu, skąd wysyłam je na WhatsAppie."""
    from urllib.parse import unquote, urlparse
    sciezka = unquote(urlparse(link).path).split("/home/", 1)[-1] if "dropbox.com" in link else link
    sciezka = sciezka.strip("/")
    if subprocess.run(["rclone", "lsd", KONTO + sciezka], capture_output=True).returncode != 0 and \
       subprocess.run(["rclone", "lsf", KONTO + sciezka], capture_output=True).returncode != 0:
        sys.exit(f"Nie widzę „{sciezka}” na {KONTO} — folder musi być udostępniony i dołączony w Dropboxie.")
    lok = LOKALNIE / E.MIESIAC / "Grafiki Ewy (WhatsApp)"
    lok.mkdir(parents=True, exist_ok=True)
    subprocess.run(["rclone", "copy", KONTO + sciezka, str(lok), "--exclude", ".DS_Store"], check=True)
    print(f"  lokalnie: {lok} ({sum(1 for _ in lok.iterdir())} plików)")
    kopiuj(lok, f"BOGO Em/{E.MIESIAC}/Grafiki Ewy (WhatsApp)")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "grafiki-ewy":
        grafiki_ewy(sys.argv[2])
    elif len(sys.argv) >= 2 and sys.argv[1] == "em":
        em()
    elif len(sys.argv) >= 2 and sys.argv[1] == "whatsapp":
        whatsapp()
    else:
        print(__doc__)
