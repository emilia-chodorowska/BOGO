#!/usr/bin/env python3
"""Wgrywanie na Dropbox przez rclone (konto `db-emilia:`), bez przeglądarki.

  python3 dropbox.py em                   → mój folder „BOGO Em/<MIESIAC>/”: wszystko, co ważne na koniec;
                                            składany w ~/MyProjects/doTERRA/BOGO Em/ (Finder), potem kopia na Dropbox
  python3 dropbox.py whatsapp             → ten sam komplet co „em” (+ gotowe grafiki z kółeczkami BOGO PL z katalogu Canvy)
                                            — linki i rolki (jako linki do Instagrama) każdy osobno jako miniatura z linkiem;
                                            bez zdjęć zestawów, EUR, huba i widoku zespołu; nagłówki sekcji bez dat;
                                            grafiki na Instagram → prosto do Asi Piwowarczyk (nie do grupy)
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
    """Gotowe grafiki z kółeczkami produktów bieżącej promocji (katalog Canvy), tylko PL (userka 27.10: EN/DE/UK to za dużo)."""
    import canva as C
    slugi = {E.PRODUKTY[n]["slug"] for n in C.produkty_promocji()}
    try:
        kat = json.loads((KAT / "katalog.json").read_text(encoding="utf-8"))["grafiki"]
    except Exception:
        return []
    kol = {"pl": 0, "en": 1, "de": 2, "uk": 3}
    g = [x for x in kat if x["slug"] in slugi and x["jezyk"] == "pl" and x["stan"] == "gotowa" and (KAT / x["plik"]).exists()]
    return [KAT / x["plik"] for x in sorted(g, key=lambda x: (kol.get(x["jezyk"], 9), x["strona"]))]


def miniatura(url, katalog, film=None):
    """Obrazek do linku: WhatsApp Web (ego) nie wczytuje pełnego podglądu linku, więc link idzie jako podpis zdjęcia.
    YouTube → okładka filmu, rolka → klatka z pobranego mp4, strona → jej og:image. Brak → None (sam tekst)."""
    import re
    import urllib.request
    katalog.mkdir(exist_ok=True)
    cel = katalog / (hashlib.md5(url.encode()).hexdigest()[:10] + ".jpg")
    if cel.exists():
        return cel
    try:
        if film:
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1", "-i", str(film), "-frames:v", "1", "-vf", "scale=720:-2", str(cel)], check=True)
            return cel
        if re.search(r"youtu\.be/|youtube\.com/", url):  # film i playlista: okładka z oEmbed
            from urllib.parse import quote
            oe = json.loads(urllib.request.urlopen(f"https://www.youtube.com/oembed?format=json&url={quote(url, safe='')}", timeout=20).read())
            obraz = oe["thumbnail_url"]
        else:
            strona = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read().decode("utf-8", "ignore")
            m = re.search(r'<meta[^>]+og:image[^>]+content="([^"]+)"', strona) or re.search(r'<meta[^>]+content="([^"]+)"[^>]+og:image', strona)
            if not m:
                return None
            obraz = m.group(1)
        cel.write_bytes(urllib.request.urlopen(urllib.request.Request(obraz, headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read())
        return cel
    except Exception as e:
        print(f"  bez miniatury: {url} ({e})")
        return None


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
        ("Grafiki z kółeczkami", grafiki_kolka()),
        ("Screeny z maila", sorted((em_lok / "Screeny z maila").glob("*"))),
        ("Screeny kart", sorted((em_lok / "Screeny kart/PLN").glob("*"), key=lambda f: ("pakiet" in f.name, f.name))),  # pakiet na koniec
        # bez zdjęć zestawów i EUR (ewentualnie osobna grupa „BOGO ENG od Claude”); Instagram idzie do Asi, nie tu
        ("Grafiki Ewy", sorted((em_lok / "Grafiki Ewy (WhatsApp)").glob("*"))),
        ("Tła do Canvy", sorted((em_lok / "Tla do Canvy").glob("*"))),
    ]
    kroki, pliki_krokow = [], []
    naglowki = set(stan.get("#naglowki", []))
    wyslane_linki = set(stan.get("#linki", []))

    def linki_sekcja(tytul, pary):
        """Każdy link osobną wiadomością: miniatura z linkiem w podpisie (pełny podgląd linku w WhatsApp Web nie działa)."""
        pary = [(opis, url, *film) for opis, url, *film in pary if url not in wyslane_linki]
        if not pary:
            return
        if tytul and tytul not in naglowki:
            kroki.append({"tekst": f"*{tytul}*"}); pliki_krokow.append([("#naglowek", tytul)])
        for opis, url, *film in pary:
            obraz = miniatura(url, em_lok / ".miniatury", film[0] if film else None)
            krok = {"zdjecia": [str(obraz)], "podpis": f"{opis}: {url}"} if obraz else {"tekst": f"{opis}: {url}", "podglad": True}
            kroki.append(krok); pliki_krokow.append([("#link", url)])

    linki_p = em_lok / "Linki.txt"
    if linki_p.exists():
        pary = []
        for l in linki_p.read_text(encoding="utf-8").splitlines():
            if ": http" in l:
                opis, url = l.split(": ", 1)
                opis = opis.strip()
                if "(EUR)" in opis or "index-eur" in url or "doterra-hub" in url or "team=true" in url:  # bez EUR, huba, widoku zespołu
                    continue
                if "youtu.be/" in url and opis != "calosc":  # z filmów: playlista + cały film, bez pojedynczych (userka 27.10.2026)
                    continue
                pary.append(("Cały film" if opis == "calosc" else opis, url.strip()))
        linki_sekcja(None, pary)  # bez nagłówka „Linki” (userka 27.10.2026)
    # rolki: link do Instagrama zamiast pliku mp4 (nazwa pliku RRRRMMDD-<shortcode>.mp4 z rolki.mjs)
    rolki = []
    for f in sorted((em_lok / "Rolki doTERRA").glob("*.mp4")):
        data, _, kod = f.stem.partition("-")
        if kod:
            rolki.append((f"Rolka doTERRA {data[6:8]}.{data[4:6]}", f"https://www.instagram.com/reel/{kod}/", f))
    linki_sekcja(None, rolki)  # bez nagłówka „Rolki doTERRA” (userka 27.10.2026)
    for pdf in nowe(sorted(em_lok.glob("*.pdf"))):
        kroki.append({"dokument": str(pdf)}); pliki_krokow.append([pdf])
    for tytul, pliki in sekcje:
        zdj = nowe([f for f in pliki if f.suffix.lower() in OBRAZY])
        filmy = nowe([f for f in pliki if f.suffix.lower() in FILMY])
        if not zdj and not filmy:
            continue
        if tytul not in naglowki:  # nagłówek sekcji raz na miesiąc, nie przy każdym dosłaniu
            kroki.append({"tekst": f"*{tytul}*"}); pliki_krokow.append([("#naglowek", tytul)])
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
            if isinstance(f, tuple) and f[0] == "#link":
                wyslane_linki.add(f[1])
            elif isinstance(f, tuple):
                naglowki.add(f[1])
            else:
                stan[str(f)] = md5(f)
    stan["#naglowki"] = sorted(naglowki)
    stan["#linki"] = sorted(wyslane_linki)
    stan_p.write_text(json.dumps(stan, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(l for l in out.strip().splitlines()[-25:]))
    if ok < len(kroki):
        sys.exit(1)


INSTAGRAM_DO = "Asia Piwowarczyk"  # grafiki na Instagram idą prosto do Asi, nie do „BOGO od Claude” (userka 27.10.2026)


def instagram_asia():
    em_lok = LOKALNIE / E.MIESIAC
    stan_p = em_lok / ".wyslane-instagram-asia.json"
    stan = json.loads(stan_p.read_text(encoding="utf-8")) if stan_p.exists() else {}
    md5 = lambda f: hashlib.md5(Path(f).read_bytes()).hexdigest()
    pliki = [f for f in sorted((em_lok / "Instagram").glob("*.png")) if stan.get(str(f)) != md5(f)]
    if not pliki:
        print(f"  Instagram → {INSTAGRAM_DO}: nic nowego")
        return
    zad = {"grupa": INSTAGRAM_DO, "kroki": [{"zdjecia": [str(f) for f in pliki]}]}
    r = subprocess.run([EGO_BIN, "nodejs"], input=f"const ZADANIE = {json.dumps(zad, ensure_ascii=False)};\n" + WA_SKRYPT.read_text(encoding="utf-8"),
                       capture_output=True, text=True, timeout=900)
    out = r.stdout + r.stderr
    if "WYSŁANE: 1/1" in out:
        for f in pliki:
            stan[str(f)] = md5(f)
        stan_p.write_text(json.dumps(stan, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  Instagram → {INSTAGRAM_DO}: {len(pliki)} grafik")
    else:
        print(f"  Instagram → {INSTAGRAM_DO}: BŁĄD\n" + "\n".join(out.strip().splitlines()[-6:]))
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
        instagram_asia()
    else:
        print(__doc__)
