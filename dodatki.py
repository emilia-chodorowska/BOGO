#!/usr/bin/env python3
"""Wszystko poza stronami BOGO, z tych samych danych (edycja.py). Odpalane przez `python3 generuj.py`.

1. og.html + images/bogo-social-preview-<MIESIAC>.jpg (podgląd linku strony BOGO)
2. ../new-client-offer/<OFERTA folder>/index.html + social-preview.html + social-preview.jpg
   (rejestracja z pakietem BOGO: pakiet = produkty kupowane, reszta to gratisy)
3. zrodla-<MIESIAC>/ceny-do-dokumentu.txt — blok „CENY” do dokumentu Google „Bogo”
4. teksty kart do hubów (new-client-offer/index.html, doterra-hub/index.html) — na ekran

Pliki HTML zapisuje tylko przy zmianie treści; grafiki renderuje, gdy HTML jest nowszy od JPG.
"""
import glob
import shutil
import subprocess
from pathlib import Path

import edycja as E
from liczenie import podzial

TU = Path(__file__).resolve().parent
OFERTA_DIR = TU.parent / "new-client-offer" / E.OFERTA["folder"]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
P = E.PRODUKTY


def zl(x):
    return f"{x:.2f}".replace(".", ",")


def pv(x):
    return f"{x:.1f}".replace(".", ",")


def ok10(x):
    """Zaokrąglenie do pełnych 10 zł (round-half-up), do haseł z „ok.”."""
    return int((x + 5) // 10 * 10)


def produktow(n):
    if n == 1:
        return "produkt"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return "produkty"
    return "produktów"


def zapisz(sciezka, tresc):
    sciezka = Path(sciezka)
    if sciezka.exists() and sciezka.read_text(encoding="utf-8") == tresc:
        return False
    sciezka.write_text(tresc, encoding="utf-8")
    return True


def renderuj(html, jpg):
    """1200×630 headless Chrome → JPEG; tylko gdy HTML nowszy od JPG."""
    html, jpg = Path(html), Path(jpg)
    if jpg.exists() and jpg.stat().st_mtime >= html.stat().st_mtime:
        return
    png = html.with_name("_og.png")
    subprocess.run([CHROME, "--headless", "--disable-gpu", f"--screenshot={png}", "--window-size=1200,630",
                    "--hide-scrollbars", "--default-background-color=FFFFFF", "--virtual-time-budget=4000",
                    f"file://{html}"], check=True, capture_output=True)
    from PIL import Image
    Image.open(png).convert("RGB").save(jpg, quality=86, optimize=True)
    png.unlink()
    print(f"  render: {jpg.relative_to(TU.parent)} ({jpg.stat().st_size // 1024} KB)")


# ---------- 1. podgląd linku strony BOGO ----------
og = f'''<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<title>og BOGO {E.MIESIAC}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; }}
  body {{ width: 1200px; height: 630px; overflow: hidden; background: #fcfbfa; font-family: 'Inter', sans-serif; position: relative; }}
  .lisc {{ position: absolute; width: 300px; opacity: .22; mix-blend-mode: multiply; }}
  .wrap {{ position: absolute; inset: 0; display: flex; align-items: center; gap: 48px; padding: 0 64px 0 72px; }}
  .txt {{ flex: 0 0 500px; }}
  .marka {{ font-size: 18px; font-weight: 700; letter-spacing: .18em; color: #4d6a5e; text-transform: uppercase; margin-bottom: 14px; }}
  h1 {{ font-family: 'Playfair Display', serif; font-size: 76px; font-weight: 600; line-height: 1; color: #1c1917; margin-bottom: 14px; }}
  .data {{ font-family: 'Playfair Display', serif; font-size: 34px; font-weight: 600; color: #4d6a5e; margin-bottom: 22px; }}
  .opis {{ font-size: 22px; line-height: 1.45; color: #57534e; margin-bottom: 26px; }}
  .pill {{ display: inline-block; padding: 12px 24px; border-radius: 999px; background: #eef2f0; border: 2px solid #c9d8d0; color: #3e554b; font-size: 20px; font-weight: 700; }}
  .foto {{ flex: 1; height: 360px; border-radius: 22px; overflow: hidden; box-shadow: 0 30px 60px -30px rgba(47,58,51,.45); }}
  .foto img {{ width: 100%; height: 100%; object-fit: cover; }}
</style>
</head>
<body>
  <img class="lisc" src="images/liscie-gora.jpg" style="top:0; left:0;" alt="">
  <img class="lisc" src="images/liscie-dol.jpg" style="bottom:0; right:0;" alt="">
  <div class="wrap">
    <div class="txt">
      <div class="marka">doTERRA</div>
      <h1>Oferta BOGO</h1>
      <div class="data">{E.OKRES}</div>
      <div class="opis">{len(E.ZESTAWY)} zestawów: kupujesz jeden produkt, drugi dostajesz gratis.</div>
      <div class="pill">Pakiet BOGO + {E.PREZENT_KROTKO} gratis</div>
    </div>
    <div class="foto"><img src="{E.FOTO_PAKIET}" alt=""></div>
  </div>
</body>
</html>
'''
zapisz(TU / "og.html", og)
renderuj(TU / "og.html", TU / f"images/bogo-social-preview-{E.MIESIAC}.jpg")


# ---------- 2. rejestracja z pakietem BOGO ----------
def wiersz(nazwa, poj, ile, etykieta):
    cena = P[nazwa]["pln"]
    return dict(nazwa=nazwa, poj=poj, ile=ile, etykieta=etykieta,
                poza=None if cena is None else round(cena * ile, 2))


kup = [wiersz(z["kup"][0], z["kup"][1], z["kup"][3], None) for z in E.ZESTAWY]
bogo = [wiersz(g[0], g[1], g[3], "gratis BOGO") for z in E.ZESTAWY for g in z["gratis"]]
prezent = [wiersz(E.PREZENT[0], E.PREZENT[1], 1, "gratis do pakietu")]
pv200 = [wiersz(n, r, 1, "gratis 200PV") for n, r in E.OFERTA["gratis_200pv"]]
wiersze = kup + bogo + prezent + pv200
cena_pakietu = round(sum(w["poza"] for w in kup), 2)
pv_pakietu = sum(z["kup"][2] for z in E.ZESTAWY)
for w, d in zip(wiersze, podzial(cena_pakietu, [w["poza"] for w in wiersze])):
    w["w_zestawie"] = d
gratisy = bogo + prezent + pv200
n_gratis = sum(w["ile"] for w in gratisy)
wartosc_gratisow = ok10(sum(w["poza"] or 0 for w in gratisy))
szac = any(w["nazwa"] in E.SZACUNKOWE for w in wiersze)
rz = E.OFERTA["rzeczownik_kup"]
n_kup = len(kup)
suma_poza = round(sum(w["poza"] or 0 for w in wiersze), 2)


def kr(w):
    k = P[w["nazwa"]]["krotko"]
    return f"2 × {k[0].lower()}{k[1:]}" if w["ile"] == 2 else k


TYTUL_OG = f'{E.OFERTA["miesiac"]} - Rejestracja z pakietem BOGO: {n_kup} {rz} + {n_gratis} {produktow(n_gratis)} gratis'
OPIS_OG = (f"Rejestracja z pakietem BOGO dōTERRA ({E.OKRES_KROTKO}): {n_kup} {rz}, {zl(cena_pakietu)} zł, "
           f"{pv(pv_pakietu)} PV. {n_gratis} {produktow(n_gratis)} gratis o wartości ok. {wartosc_gratisow} zł: "
           f"{E.OFERTA['gratisy_opis']}.")
URL = f"https://emilia-chodorowska.github.io/new-client-offer/{E.OFERTA['folder']}/"

li_kit = "\n".join(
    f'''                            <li data-product-name="{P[w["nazwa"]]["krotko"]}">{P[w["nazwa"]]["krotko"]} <span class="text-sm font-medium" style="color: var(--text-secondary);">({w["poj"]})</span></li>'''
    for w in kup)
img_kit = "\n".join(
    f'''                            <img src="images/{P[w["nazwa"]]["foto"]}" alt="{P[w["nazwa"]]["krotko"]}" class="h-24 md:h-44 object-contain">'''
    for w in kup)


def figura(w):
    p = P[w["nazwa"]]
    if w["ile"] == 1:
        return f'''                            <figure class="flex flex-col items-center gap-1.5 w-[4.5rem] md:w-24">
                                <img src="images/{p["foto"]}" alt="{p["krotko"]}" class="h-24 md:h-32 w-full object-contain object-bottom">
                                <figcaption class="text-[0.65rem] md:text-xs font-medium text-center leading-tight" style="color: var(--text-secondary);">{kr(w)}</figcaption>
                            </figure>'''
    imgs = "\n".join(f'''                                    <img src="images/{p["foto"]}" alt="{p["krotko"]}" class="h-24 md:h-32 w-auto object-contain object-bottom">''' for _ in range(w["ile"]))
    return f'''                            <figure class="flex flex-col items-center gap-1.5 w-[6.5rem] md:w-32">
                                <div class="flex items-end justify-center gap-1">
{imgs}
                                </div>
                                <figcaption class="text-[0.65rem] md:text-xs font-medium text-center leading-tight" style="color: var(--text-secondary);">{kr(w)}</figcaption>
                            </figure>'''


def grupa(tytul, ws):
    if not ws:
        return ""
    return f'''                    <div class="flex flex-col items-center gap-2">
                        <div class="text-xs font-semibold uppercase tracking-wider" style="color: var(--green);">{tytul}</div>
                        <div class="flex flex-wrap justify-center items-start gap-2 md:gap-3">
{chr(10).join(figura(w) for w in ws)}
                        </div>
                    </div>'''


def tr(w):
    k = P[w["nazwa"]]["krotko"]
    et = f' <span class="text-xs font-semibold" style="color: var(--green);">{w["etykieta"]}</span>' if w["etykieta"] else ""
    poza = "brak ceny" if w["poza"] is None else zl(w["poza"]) + ("*" if w["nazwa"] in E.SZACUNKOWE else "")
    wz = "—" if w["w_zestawie"] is None else zl(w["w_zestawie"])
    return f'''                                <tr data-product-name="{k}">
                                    <td class="py-1 px-2 border-b border-r text-center align-middle strike-column">
                                        <input type="checkbox" class="strike-toggle h-5 w-5 rounded border-gray-300 text-green-600 focus:ring-green-500 cursor-pointer" data-product-name="{k}">
                                    </td>
                                    <td class="py-3 px-4 border-b">{kr(w)} ({w["poj"]}){et}</td>
                                    <td class="py-1 px-2 border-b align-middle strike-column"><input type="text" class="w-full bg-gray-50 border-gray-300 rounded shadow-sm text-sm p-1 focus:ring-green-500 focus:border-green-500"></td>
                                    <td class="py-3 px-4 border-b text-right">{poza}</td>
                                    <td class="py-3 px-4 border-b text-right font-semibold">{wz}</td>
                                </tr>'''


nazwy200 = [P[n]["krotko"] for n, _ in E.OFERTA["gratis_200pv"]]
promo_przypis = ""
if nazwy200:
    lista = nazwy200[0] if len(nazwy200) == 1 else ", ".join(nazwy200[:-1]) + " i " + nazwy200[-1]
    promo_przypis = f'''
                        <p class="text-xs mt-2" style="color: var(--text-muted);">*{lista}: zamówienie rejestracyjne na 200 PV lub więcej, złożone od {E.OKRES_WARUNKI}</p>'''
przypis_szac = ""
if szac:
    n0 = next(iter(E.SZACUNKOWE))
    cena0 = P[n0]["pln"]
    cena_txt = f"{int(cena0)} zł" if cena0 == int(cena0) else f"{zl(cena0)} zł"
    przypis_szac = f'''
                    <p class="text-xs mt-3" style="color: var(--text-muted);">*{E.SZACUNEK_DOPELNIACZ[0].upper()}{E.SZACUNEK_DOPELNIACZ[1:]} nie ma jeszcze w cenniku doTERRA Polska – przyjęta cena szacunkowa {cena_txt} za sztukę.</p>'''

szablon = (TU / "szablony" / "oferta-rejestracji.html").read_text(encoding="utf-8")
oferta = szablon
for k, v in {
    "TYTUL": f'Rejestracja z pakietem BOGO – {E.OFERTA["miesiac"][0].lower()}{E.OFERTA["miesiac"][1:]}',
    "TYTUL_OG": TYTUL_OG, "OPIS_OG": OPIS_OG, "URL": URL,
    "MIESIAC": E.OFERTA["miesiac"], "OKRES_KROTKO": E.OKRES_KROTKO,
    "IMG_KIT": img_kit, "CENA": zl(cena_pakietu), "LI_KIT": li_kit, "PV": pv(pv_pakietu),
    "WARTOSC_GRATISOW": str(wartosc_gratisow), "GWIAZDKA_PROMO": "*" if nazwy200 else "", "PROMO_PRZYPIS": promo_przypis,
    "GRUPY": "\n".join(g for g in (grupa("Gratis BOGO (1+1)", bogo), grupa("Gratis do pakietu", prezent),
                                    grupa("Gratis przy rejestracji od 200 PV", pv200)) if g),
    "WIERSZE": "\n".join(tr(w) for w in wiersze),
    "SUMA_POZA": zl(suma_poza) + ("*" if szac else ""), "PRZYPIS_SZAC": przypis_szac,
}.items():
    oferta = oferta.replace("{{" + k + "}}", v)

sp = (TU / "szablony" / "oferta-social-preview.html").read_text(encoding="utf-8")
sp = (sp.replace("{{BADGE}}", f"{n_kup} {rz} + {n_gratis} {produktow(n_gratis)} gratis (ok. {wartosc_gratisow} zł)")
        .replace("{{PODTYTUL}}", f"{E.OKRES} · {zl(cena_pakietu)} zł · {pv(pv_pakietu)} PV"))

(OFERTA_DIR / "images").mkdir(parents=True, exist_ok=True)
for wspolny in ("doterralogo.png", "liscie-gora.png"):
    cel = OFERTA_DIR / "images" / wspolny
    if not cel.exists():
        zrodlo = next(iter(sorted(glob.glob(str(TU.parent / "new-client-offer" / "*" / "images" / wspolny)))), None)
        if zrodlo:
            shutil.copy(zrodlo, cel)
zapisz(OFERTA_DIR / "index.html", oferta)
zapisz(OFERTA_DIR / "social-preview.html", sp)
renderuj(OFERTA_DIR / "social-preview.html", OFERTA_DIR / "social-preview.jpg")

brak = [w["nazwa"] for w in wiersze if not (OFERTA_DIR / "images" / P[w["nazwa"]]["foto"]).exists()]
for n in dict.fromkeys(brak):
    print(f'  BRAK zdjęcia: python3 ~/.claude/scripts/doterra-image.py --product "{P[n]["en"]}" --output /tmp/x '
          f'→ {OFERTA_DIR.relative_to(TU.parent)}/images/{P[n]["foto"]}')
print(f"{E.OFERTA['folder']}/index.html: pakiet {zl(cena_pakietu)} zł, {pv(pv_pakietu)} PV, "
      f"{n_gratis} gratisów ok. {wartosc_gratisow} zł, suma poza {zl(suma_poza)}")


# ---------- 3. blok CENY do dokumentu „Bogo” ----------
def en(nazwa, ile):
    return ("2x " if ile == 2 else "") + P[nazwa]["en"]


linie = [f"BOGO {E.OKRES_KROTKO.replace('–', '-')}", "", "CENY", ""]
przed_pakiet = 0.0
for i, z in enumerate(E.ZESTAWY, 1):
    n, _, _, ile = z["kup"]
    cena = P[n]["pln"]
    poz = [z["kup"]] + z["gratis"]
    przed = sum(P[p[0]]["pln"] * p[3] for p in poz)
    gw = "*" if any(p[0] in E.SZACUNKOWE for p in poz) else ""
    przed_pakiet += przed
    linie += [f"PARA {i:02d} · {en(n, ile)} + {', '.join(en(g[0], g[3]) for g in z['gratis'])}",
              f"Cena pary przed: {zl(przed)} zł{gw}", f"Cena pary BOGO: {zl(cena)} zł", ""]
przed_pakiet += P[E.PREZENT[0]]["pln"]
linie += [f"PAKIET BOGO ({len(E.ZESTAWY)} par + {P[E.PREZENT[0]]['en']} {E.PREZENT[1]} gratis)",
          f"Cena przed: {zl(przed_pakiet)} zł{'*' if szac else ''}", f"Cena BOGO: {zl(cena_pakietu)} zł"]
if szac:
    n0 = next(iter(E.SZACUNKOWE))
    linie += ["", f"* {P[n0]['en']}: cena szacunkowa {zl(P[n0]['pln'])} zł za sztukę (brak w cenniku PL)"]
zr = TU / f"zrodla-{E.MIESIAC}"
zr.mkdir(exist_ok=True)
(zr / "ceny-do-dokumentu.txt").write_text("\n".join(linie) + "\n", encoding="utf-8")
print(f"blok CENY: zrodla-{E.MIESIAC}/ceny-do-dokumentu.txt")

# ---------- 4. teksty kart do hubów ----------
print("\nkarty w hubach:")
print(f"  new-client-offer/index.html  pill: BOGO · {E.OKRES_KROTKO}")
print(f"    h3: Rejestracja z pakietem BOGO · {zl(cena_pakietu)} zł")
print(f"    p:  {n_kup} {rz} ({pv(pv_pakietu)} PV) + gratisy o wartości ok. {wartosc_gratisow} zł: {E.OFERTA['gratisy_opis']}")
print(f"  doterra-hub/index.html  tytuł: Rejestracja z pakietem BOGO — {E.OKRES_KROTKO}")
print(f"    pod:  {n_kup} {rz}, {zl(cena_pakietu)} zł, {pv(pv_pakietu)} PV + gratisy ok. {wartosc_gratisow} zł ({E.OFERTA['gratisy_hub']})")
print(f"    link: {URL}")
