#!/usr/bin/env python3
"""Pomocnik do grafik z kółeczkami w Canvie dla edycji BOGO (dane z edycja.py).

  python3 canva.py slugi             → slugi produktów promocji (do /canva-proces i /canva-hasla)
  python3 canva.py stan              → które produkty mają tło, hasła PL/EN/DE, packshot
  python3 canva.py do-canvy          → canva/materialy/_wygenerowane-bogo-<MIESIAC>/do-canvy/BOGO-<MIESIAC>-<slug>.png
  python3 canva.py packshoty         → oficjalne rendery do zrodla-<MIESIAC>/grafiki-produktow/ i do strony rejestracji

Tło do Canvy: najnowsze zaakceptowane (materialy/<slug>/tla/chatgpt__*.png), a gdy go brak —
najnowsze czekające na akceptację (tla/do-akceptacji/chatgpt__*.png; wtedy oznaczone na liście).
"""
import shutil
import subprocess
import sys
from pathlib import Path

import edycja as E

TU = Path(__file__).resolve().parent
MAT = Path.home() / "MyProjects/canva/materialy"
HASLA = Path.home() / "MyProjects/canva/hasla/output"
OFERTA_IMG = TU.parent / "new-client-offer" / E.OFERTA["folder"] / "images"
DOTERRA_IMAGE = Path.home() / ".claude/scripts/doterra-image.py"


def produkty_promocji():
    """Nazwy w kolejności: kupowany, gratisy (po zestawach), prezent do pakietu."""
    nazwy = []
    for z in E.ZESTAWY:
        nazwy += [z["kup"][0]] + [g[0] for g in z["gratis"]]
    nazwy.append(E.PREZENT[0])
    return list(dict.fromkeys(nazwy))


def tlo(slug):
    zaakc = sorted((MAT / slug / "tla").glob("chatgpt__*.png"))
    if zaakc:
        return zaakc[-1], True
    czeka = sorted((MAT / slug / "tla" / "do-akceptacji").glob("chatgpt__*.png"))
    return (czeka[-1], False) if czeka else (None, False)


def main(cmd):
    nazwy = produkty_promocji()
    if cmd == "slugi":
        print(" ".join(E.PRODUKTY[n]["slug"] for n in nazwy))
    elif cmd == "stan":
        print(f"{'produkt':34} {'slug':16} tło          hasła")
        for n in nazwy:
            s = E.PRODUKTY[n]["slug"]
            plik, ok = tlo(s)
            t = "zaakceptowane" if ok else ("do akceptacji" if plik else "BRAK")
            h = "/".join(j for j, suf in (("PL", ""), ("EN", "-en"), ("DE", "-de")) if (HASLA / f"{s}{suf}.html").exists()) or "BRAK"
            print(f"{n:34} {s:16} {t:13} {h}")
    elif cmd == "do-canvy":
        cel = MAT / f"_wygenerowane-bogo-{E.MIESIAC}" / "do-canvy"
        cel.mkdir(parents=True, exist_ok=True)
        for n in nazwy:
            s = E.PRODUKTY[n]["slug"]
            plik, ok = tlo(s)
            if not plik:
                print(f"  BRAK tła: {s}")
                continue
            shutil.copy2(plik, cel / f"BOGO-{E.MIESIAC}-{s}.png")
            print(f"  {s}: {plik.name}{'' if ok else '  (jeszcze do akceptacji)'}")
        print(cel)
    elif cmd == "packshoty":
        gp = TU / f"zrodla-{E.MIESIAC}" / "grafiki-produktow"
        gp.mkdir(parents=True, exist_ok=True)
        OFERTA_IMG.mkdir(parents=True, exist_ok=True)
        wszystkie = nazwy + [n for n, _ in E.OFERTA["gratis_200pv"]]
        for i, n in enumerate(wszystkie, 1):
            p = E.PRODUKTY[n]
            kto = ["--id", str(p["id"])] if p.get("id") else ["--product", p["en"]]
            for cel in (gp / f"{i:02d} {p['krotko'].replace('™', '')}.png", OFERTA_IMG / p["foto"]):
                if cel.exists():
                    continue
                r = subprocess.run([sys.executable, str(DOTERRA_IMAGE), *kto, "--output", str(cel)],
                                   capture_output=True, text=True)
                print(f"  {'ok  ' if r.returncode == 0 else 'BŁĄD'} {cel.name}  {r.stderr.strip()[:120]}")
        print(f"Obejrzyj: {gp} i {OFERTA_IMG} — nazwa angielska bywa niejednoznaczna (wtedy dopisz 'id' w PRODUKTY).")
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
