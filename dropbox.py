#!/usr/bin/env python3
"""Wgrywanie na Dropbox przez rclone (konto `db-emilia:`), bez przeglądarki.

  python3 dropbox.py ewa "<folder Ewy>"   → do folderu udostępnionego przez Ewę (np. „BOGO 10.2026”)
                                            TYLKO zdjęcia zestawów, podfolder „Bogo zdjęcia”
  python3 dropbox.py em                   → mój folder „BOGO Em/<MIESIAC>/”: wszystko, co ważne na koniec

`rclone copy` tylko dokłada i nadpisuje zmienione pliki, niczego nie kasuje.
Źródło zdjęć: zrodla-<MIESIAC>/dropbox/2 Zdjecia zestawow/ (po jednym na zestaw, gratis i pakiet, bez przycinania).
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import edycja as E

TU = Path(__file__).resolve().parent
ZR = TU / f"zrodla-{E.MIESIAC}"
KONTO = "db-emilia:"
ZDJECIA = ZR / "dropbox" / "2 Zdjecia zestawow"


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
    cel = f"BOGO Em/{E.MIESIAC}/"
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "Linki.txt").write_text(linki(), encoding="utf-8")
        kopiuj(tmp, cel)
    kopiuj(TU / f"screeny-{E.MIESIAC}", cel + "Screeny kart")
    pod = ZR / "_podglady"
    pod.mkdir(exist_ok=True)
    for z, n in ((TU / f"images/bogo-social-preview-{E.MIESIAC}.jpg", "Podglad linku BOGO.jpg"),
                 (TU.parent / "new-client-offer" / E.OFERTA["folder"] / "social-preview.jpg", "Podglad linku rejestracja.jpg")):
        if z.exists():
            (pod / n).write_bytes(z.read_bytes())
    kopiuj(pod, cel + "Podglady linkow")
    kopiuj(ZR / "dropbox" / "1 Grafiki doTERRA", cel + "Grafiki doTERRA")
    kopiuj(ZDJECIA, cel + "Zdjecia zestawow")
    for pdf in ZR.glob("PL_*.pdf"):
        subprocess.run(["rclone", "copyto", str(pdf), KONTO + cel + f"Broszura BOGO {E.MIESIAC} PL.pdf"], check=True)
        print(f"  ok  {cel}Broszura")
    kopiuj(ZR / "rolki", cel + "Rolki doTERRA")
    kopiuj(Path.home() / f"MyProjects/canva/materialy/_wygenerowane-bogo-{E.MIESIAC}/do-canvy", cel + "Tla do Canvy")


def ewa(folder):
    if not subprocess.run(["rclone", "lsd", KONTO + folder], capture_output=True).returncode == 0:
        sys.exit(f"Nie ma folderu „{folder}” na {KONTO} — Ewa musi go udostępnić (Dołącz do folderu w Dropboxie).")
    kopiuj(ZDJECIA, f"{folder}/Bogo zdjęcia")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "ewa":
        ewa(sys.argv[2])
    elif len(sys.argv) >= 2 and sys.argv[1] == "em":
        em()
    else:
        print(__doc__)
