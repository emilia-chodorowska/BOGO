#!/usr/bin/env python3
"""Pomocnik do grafik z kółeczkami w Canvie dla edycji BOGO (dane z edycja.py).

  python3 canva.py slugi             → slugi produktów promocji BEZ grafiki w katalogu (tylko te idą do /canva-proces)
  python3 canva.py stan              → katalog (strona w Canvie), tło, hasła PL/EN/DE
  python3 canva.py do-canvy          → canva/materialy/_wygenerowane-bogo-<MIESIAC>/do-canvy/BOGO-<MIESIAC>-<slug>.png
  python3 canva.py packshoty         → oficjalne rendery do zrodla-<MIESIAC>/grafiki-produktow/, produkty/ (ig.py) i do strony rejestracji

Katalog gotowych grafik: canva/materialy/_katalog-grafik/katalog.json (strony projektu „z kółeczkami PL”,
pobrane z Canvy; stan „gotowa” / „puste-kolka” / „do-sprawdzenia”). Produkt z wpisem w katalogu NIE idzie przez
/canva-proces — pełna procedura tylko dla brakujących. „puste-kolka” = brakuje tylko haseł.

Tło do Canvy: najnowsze zaakceptowane (materialy/<slug>/tla/chatgpt__*.png), a gdy go brak —
najnowsze czekające na akceptację (tla/do-akceptacji/chatgpt__*.png; wtedy oznaczone na liście).
"""
import json
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
KATALOG = MAT / "_katalog-grafik" / "katalog.json"
PRODUKTY_DIR = TU / f"zrodla-{E.MIESIAC}" / "produkty"  # pełny rozmiar (1350 px) — ig.py, plansze filmu


def katalog(slug):
    if not KATALOG.exists():
        return []
    return [g for g in json.loads(KATALOG.read_text(encoding="utf-8"))["grafiki"] if g["slug"] == slug and g["jezyk"] == "pl"]


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
        print(" ".join(E.PRODUKTY[n]["slug"] for n in nazwy if not katalog(E.PRODUKTY[n]["slug"])))
    elif cmd == "stan":
        print(f"{'produkt':34} {'slug':16} {'katalog (Canva)':24} tło          hasła")
        for n in nazwy:
            s = E.PRODUKTY[n]["slug"]
            k = katalog(s)
            kt = ", ".join(f"str. {g['strona']} {g['stan']}" for g in k) or "BRAK → /canva-proces"
            plik, ok = tlo(s)
            t = "zaakceptowane" if ok else ("do akceptacji" if plik else "BRAK")
            h = "/".join(j for j, suf in (("PL", ""), ("EN", "-en"), ("DE", "-de"), ("UK", "-uk")) if (HASLA / f"{s}{suf}.html").exists()) or "BRAK"
            print(f"{n:34} {s:16} {kt:24} {t:13} {h}")
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
        PRODUKTY_DIR.mkdir(parents=True, exist_ok=True)
        wszystkie = nazwy + [n for n, _ in E.OFERTA["gratis_200pv"]]
        for i, n in enumerate(wszystkie, 1):
            p = E.PRODUKTY[n]
            kto = ["--id", str(p["id"])] if p.get("id") else ["--product", p["en"]]
            for cel in (gp / f"{i:02d} {p['krotko'].replace('™', '')}.png", OFERTA_IMG / p["foto"], PRODUKTY_DIR / p["foto"]):
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
