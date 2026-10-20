#!/usr/bin/env python3
"""Wgrywanie na Dropbox przez rclone (konto `db-emilia:`), bez przeglądarki.

  python3 dropbox.py em                   → mój folder „BOGO Em/<MIESIAC>/”: wszystko, co ważne na koniec;
                                            składany w ~/MyProjects/doTERRA/BOGO Em/ (Finder), potem kopia na Dropbox
  python3 dropbox.py grafiki-ewy "<link>" → grafiki od Ewy (link dropbox.com/home/… albo ścieżka) do
                                            „BOGO Em/<MIESIAC>/Grafiki Ewy (WhatsApp)” — do wysyłania klientom

`rclone copy` tylko dokłada i nadpisuje zmienione pliki, niczego nie kasuje.
Źródło zdjęć: zrodla-<MIESIAC>/dropbox/2 Zdjecia zestawow/ (po jednym na zestaw, gratis i pakiet, bez przycinania).
"""
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
    for pdf in ZR.glob("PL_*.pdf"):
        shutil.copy2(pdf, lok / f"Broszura BOGO {E.MIESIAC} PL.pdf")
    wrzuc(ZR / "rolki", "Rolki doTERRA")
    wrzuc(Path.home() / f"MyProjects/canva/materialy/_wygenerowane-bogo-{E.MIESIAC}/do-canvy", "Tla do Canvy")
    print(f"  lokalnie: {lok}")
    kopiuj(lok, f"BOGO Em/{E.MIESIAC}")


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
    else:
        print(__doc__)
