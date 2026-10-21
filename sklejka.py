#!/usr/bin/env python3
"""Sklejka nagrań BOGO: osobne filmy części + cały film z rozdziałami + napisy .srt.

Lista części, kolejność, tempo i ręczne punkty cięcia: sklejka-RRRR-MM.json.
Nagrania: zrodla-RRRR-MM/nagrania/ (z transkrypcją <plik>.segments.json obok).
Wynik:    zrodla-RRRR-MM/film/ — <id>.mp4 + <id>.srt + <id>.txt (tytuł i opis), calosc.*

  python3 sklejka.py sklejka-2026-10.json            # wszystkie części + całość
  python3 sklejka.py sklejka-2026-10.json --czesc 5  # przelicz jedną część (np. gdy dojdzie plik), potem całość
  python3 sklejka.py sklejka-2026-10.json --ciecia   # tylko pokaż wyliczone punkty cięcia

Przycinanie: od pierwszego do ostatniego słowa z transkrypcji (z małym zapasem),
chyba że plik ma w JSON ręczne "od"/"do" (sekundy w oryginale).
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

ZAPAS_POCZ = 0.25   # s przed pierwszym słowem
ZAPAS_KON = 0.7     # s po ostatnim słowie
W, H, FPS = 1080, 1920, 30
LUFS = -16
MAX_ZNAKOW = 42     # na linię napisu
MAX_LINII = 2
MAX_CZAS = 6.0      # s na jeden napis


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw)


def dlugosc(plik):
    return float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "csv=p=0", str(plik)]).stdout.strip())


def slowa(plik):
    seg = plik.with_suffix(".segments.json")
    if not seg.exists():
        raise SystemExit(f"Brak transkrypcji: {seg.name} — puść /transkrypcja z --timestamps")
    out = []
    for s in json.loads(seg.read_text()):
        # halucynacje whispera: zapętlony tekst albo dużo znaków w ułamku sekundy
        dl = s["end"] - s["start"]
        if s.get("compression_ratio", 0) > 2.4 or len(s["text"].strip()) > 40 * max(dl, 0.05):
            continue
        for w in s.get("words", []):
            out.append((w["start"], w["end"], w["word"].strip()))
    return [w for w in out if w[2]]


def ciecie(plik, wpis):
    ws = slowa(plik)
    od = wpis.get("od", max(0.0, ws[0][0] - ZAPAS_POCZ))
    do = wpis.get("do", min(dlugosc(plik), ws[-1][1] + ZAPAS_KON))
    return od, do


def glosnosc(plik, od, do):
    """Pierwszy przebieg loudnorm — pomiar."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{od}", "-to", f"{do}",
                        "-i", str(plik), "-af", f"loudnorm=I={LUFS}:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], text=True, capture_output=True)
    m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr).group(0))
    return (f"loudnorm=I={LUFS}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
            f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
            f":offset={m['target_offset']}:linear=true")


# wszystko wychodzi jako SDR BT.709 — inaczej sklejka dziedziczy oznaczenie HDR pierwszej części
# i YouTube pokazuje nagrania SDR z przesadnym kontrastem
KOLOR = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
# ffmpeg 8 bierze oznaczenia kolorów z klatek, nie z opcji wyjścia — więc ustawiamy je na klatkach
TAGI = "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv"
# HLG z iPhone'a: tylko przeliczenie palety BT.2020 → BT.709, bez mapowania jasności
# (mapowanie tonów rozjaśniało twarze — HLG jest z założenia czytelne jako SDR)
HDR_NA_SDR = "zscale=tin=bt709:t=bt709:pin=bt2020:p=bt709:min=bt2020nc:m=bt709:r=tv,format=yuv420p,"


def renderuj_plik(plik, od, do, tempo, cel):
    dl = (do - od) / tempo
    trc = sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer",
              "-of", "default=nw=1:nk=1", str(plik)]).stdout.strip().strip(",")
    v = ((HDR_NA_SDR if trc in ("arib-std-b67", "smpte2084") else "")
         + f"scale={W}:{H}:force_original_aspect_ratio=decrease:out_color_matrix=bt709:out_range=tv,"
         f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,format=yuv420p,{TAGI},setsar=1,fps={FPS},setpts=(PTS-STARTPTS)/{tempo}")
    a = (f"asetpts=PTS-STARTPTS,{glosnosc(plik, od, do)},aresample=48000,"
         + (f"atempo={tempo}," if tempo != 1 else "")
         + f"afade=t=in:d=0.12,afade=t=out:st={max(0, dl - 0.2):.3f}:d=0.2")
    sh(["ffmpeg", "-y", "-hide_banner", "-ss", f"{od}", "-to", f"{do}", "-i", str(plik),
        "-vf", v, "-af", a, "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-pix_fmt", "yuv420p", *KOLOR, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", str(cel)])


def czasy_plansz(cz, ws):
    """[(od_s, klucz_panelu)] — przełączenie na pierwszym wystąpieniu frazy "od" w transkrypcji części."""
    norm = lambda t: re.sub(r"[^\w]", "", t.lower())
    slowa_cz = [norm(w[2]) for w in ws]
    out = []
    for pl in cz.get("plansze", []):
        if "od" not in pl:
            out.append((0.0, pl["panel"]))
            continue
        fraza = [norm(x) for x in pl["od"].split()]
        i = next((i for i in range(len(slowa_cz)) if slowa_cz[i:i + len(fraza)] == fraza), None)
        if i is None:
            raise SystemExit(f"{cz['id']}: nie ma w transkrypcji frazy „{pl['od']}”")
        out.append((max(0.0, ws[i][0] - 0.3), pl["panel"]))
    return out


def poziomo(pion, plansze, panele_dir, cel):
    """Pion po lewej na planszach przełączanych w czasie (rozmiar = rozmiar planszy, 1920x1080 × SKALA)."""
    from panele import VID_W as VW, SKALA
    VID_W, PW, PH = VW * SKALA, 1920 * SKALA, 1080 * SKALA
    wej = ["-i", str(pion)]
    for _, k in plansze:
        wej += ["-loop", "1", "-framerate", str(FPS), "-i", str(panele_dir / f"{k}.png")]
    # podkładem jest wideo (ono wyznacza czas, więc bez czarnych klatek na starcie),
    # plansza bez lewego pasa kładzie się na prawą część kadru
    f, tlo = [f"[0:v]scale={VID_W}:{PH}:flags=lanczos,setsar=1,pad={PW}:{PH}:0:0[t0]"], "[t0]"
    for j, (t, _) in enumerate(plansze, start=1):
        f.append(f"[{j}:v]crop={PW - VID_W}:{PH}:{VID_W}:0,"
                 f"scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[p{j}]")
        f.append(f"{tlo}[p{j}]overlay={VID_W}:0:enable='gte(t,{t:.3f})'[t{j}]")
        tlo = f"[t{j}]"
    f.append(f"{tlo}format=yuv420p,{TAGI}[out]")
    sh(["ffmpeg", "-y", "-hide_banner", *wej, "-filter_complex", ";".join(f),
        "-map", "[out]", "-map", "0:a", "-t", f"{dlugosc(pion):.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-r", str(FPS), *KOLOR,
        "-c:a", "copy", "-movflags", "+faststart", str(cel)])


def sklej(pliki, cel):
    lista = cel.with_suffix(".lista.txt")
    lista.write_text("".join(f"file '{p.resolve()}'\n" for p in pliki))
    sh(["ffmpeg", "-y", "-hide_banner", "-f", "concat", "-safe", "0", "-i", str(lista),
        "-c", "copy", "-movflags", "+faststart", str(cel)])
    lista.unlink()


# ---------- napisy ----------

def popraw(ws, poprawki):
    """Błędy rozpoznania (także wielowyrazowe) poprawiane na liście słów, przed podziałem na napisy."""
    for zle, dobrze in poprawki.items():
        n, out, i = len(zle.split()), [], 0
        while i < len(ws):
            kawalek = ws[i:i + n]
            m = re.fullmatch(rf"{re.escape(zle)}(\W*)", " ".join(w[2] for w in kawalek), re.IGNORECASE)
            if len(kawalek) == n and m:
                out.append((kawalek[0][0], kawalek[-1][1], dobrze + m.group(1)))
                i += n
            else:
                out.append(ws[i])
                i += 1
        ws = out
    return ws


def napisy_pliku(plik, od, do, tempo, przes):
    """Słowa z jednego pliku przeliczone na czas filmu wynikowego."""
    out = []
    for s, e, t in slowa(plik):
        if e <= od or s >= do:
            continue
        out.append(((max(s, od) - od) / tempo + przes, (min(e, do) - od) / tempo + przes, t))
    return out


def w_napisy(ws):
    cues, cur = [], []

    def zamknij():
        if cur:
            cues.append((cur[0][0], cur[-1][1], " ".join(w[2] for w in cur)))
            cur.clear()

    for w in ws:
        txt = " ".join(x[2] for x in cur + [w])
        if cur and (len(txt) > MAX_ZNAKOW * MAX_LINII or w[1] - cur[0][0] > MAX_CZAS):
            zamknij()
        cur.append(w)
        if re.search(r"[.?!]$", w[2]) and len(" ".join(x[2] for x in cur)) > MAX_ZNAKOW * 0.6:
            zamknij()
    zamknij()
    return cues


def zawin(t):
    if len(t) <= MAX_ZNAKOW:
        return t
    srodek = len(t) // 2
    spacje = [i for i, c in enumerate(t) if c == " "]
    i = min(spacje, key=lambda x: abs(x - srodek))
    return t[:i] + "\n" + t[i + 1:]


def czas_srt(t):
    ms = round(t * 1000)
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def zapisz_srt(cues, cel):
    with open(cel, "w", encoding="utf-8") as f:
        for n, (s, e, t) in enumerate(cues, 1):
            f.write(f"{n}\n{czas_srt(s)} --> {czas_srt(e)}\n{zawin(t)}\n\n")


def czas_yt(t):
    t = int(t)
    return f"{t // 3600}:{t // 60 % 60:02}:{t % 60:02}" if t >= 3600 else f"{t // 60}:{t % 60:02}"


# ---------- podgląd plansz ----------

def strona_podgladu(cfg, baza, wynik, podglady):
    """Każda plansza złożona z klatką z chwili, gdy się pojawia → <baza>/plansze-podglad.html."""
    from panele import VID_W as VW, SKALA
    VID_W = VW * SKALA
    pg = wynik / "podglad"
    pg.mkdir(exist_ok=True)
    uzyte, karty = set(), []
    for cz, plansze, pion in podglady:
        for t, k in plansze:
            jpg = pg / f"{cz['id']}-{k}.jpg"
            klatka = pg / ".klatka.png"
            sh(["ffmpeg", "-y", "-hide_banner", "-ss", f"{t + 2:.2f}", "-i", str(pion),
                "-frames:v", "1", "-update", "1", "-vf", f"scale={VID_W}:{1080 * SKALA}:flags=lanczos", str(klatka)])
            sh(["ffmpeg", "-y", "-hide_banner", "-i", str(wynik / "panele" / f"{k}.png"), "-i", str(klatka),
                "-filter_complex", "[0:v][1:v]overlay=0:0,scale=1280:720", "-frames:v", "1", "-update", "1",
                "-q:v", "3", str(jpg)])
            klatka.unlink()
            uzyte.add(k)
            karty.append((f"{cz['etykieta']} · od {czas_yt(t)}", jpg))
    for k in cfg["panele"]:
        if k not in uzyte:
            karty.append(("czeka na nagranie", wynik / "panele" / f"{k}.png"))
    rel = lambda p: p.relative_to(baza).as_posix()
    html = "".join(f'<figure><img src="{rel(p)}" loading="lazy"><figcaption>{o}</figcaption></figure>'
                   for o, p in karty)
    (baza / "plansze-podglad.html").write_text(f"""<!DOCTYPE html><html lang="pl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Plansze BOGO</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='20' fill='%234d6a5e'/%3E%3Crect x='18' y='26' width='20' height='48' rx='4' fill='white'/%3E%3Crect x='44' y='26' width='38' height='48' rx='4' fill='none' stroke='white' stroke-width='6'/%3E%3C/svg%3E">
<style>body{{margin:0;background:#faf9f6;font-family:Inter,-apple-system,sans-serif;color:#1c1917;padding:32px 16px}}
.wrap{{max-width:1320px;margin:0 auto}}h1{{font-size:24px;margin:0 0 20px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(520px,1fr));gap:20px}}
@media(max-width:600px){{.grid{{grid-template-columns:1fr}}}}
figure{{margin:0;background:#fff;border:1px solid #e7e5e4;border-radius:12px;overflow:hidden}}
img{{width:100%;display:block}}figcaption{{padding:10px 14px;font-size:14px;color:#57534e}}</style></head>
<body><div class="wrap"><h1>Plansze BOGO — {len(karty)} szt.</h1><div class="grid">{html}</div></div></body></html>""",
        encoding="utf-8")
    print(f"✅ plansze-podglad.html ({len(karty)} plansz)")


# ---------- główne ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--czesc", help="przelicz tylko części o tych id, po przecinku (reszta z dysku)")
    ap.add_argument("--ciecia", action="store_true", help="tylko pokaż punkty cięcia")
    ap.add_argument("--poziom", action="store_true", help="przelicz tylko układ poziomy (pion z dysku)")
    ap.add_argument("--podglad", action="store_true", help="strona z planszami na prawdziwych klatkach")
    ap.add_argument("--napisy", action="store_true",
                    help="tylko napisy, opisy i rozdziały (filmy części już wyrenderowane)")
    args = ap.parse_args()

    cfg_path = Path(args.config).resolve()
    cfg = json.loads(cfg_path.read_text())
    baza = cfg_path.parent
    zrodla = baza / cfg["nagrania"]
    wynik = baza / cfg["wynik"]
    wynik.mkdir(parents=True, exist_ok=True)
    poprawki = cfg.get("poprawki", {})

    gotowe = []  # (czesc, plik mp4, słowa w czasie części)
    podglady = []
    for cz in cfg["czesci"]:
        pliki = [zrodla / p["plik"] for p in cz["pliki"]]
        if not pliki or not all(p.exists() for p in pliki):
            print(f"⏸  {cz['id']} — brak pliku, pomijam")
            continue
        tempo = cz.get("tempo", 1.0)
        pion = wynik / "pion" / f"{cz['id']}.mp4"
        pion.parent.mkdir(exist_ok=True)
        mp4 = wynik / f"{cz['id']}.mp4" if cfg.get("poziomo") else pion
        tylko_opis = args.ciecia or args.napisy or args.podglad
        przelicz = not (tylko_opis or args.poziom) and (args.czesc is None or cz["id"] in args.czesc.split(",") or not pion.exists())

        przes, ws, kawalki = 0.0, [], []
        for i, (p, wpis) in enumerate(zip(pliki, cz["pliki"])):
            od, do = ciecie(p, wpis)
            print(f"   {cz['id']} · {p.name}: {od:.2f}–{do:.2f} s (z {dlugosc(p):.2f}), tempo {tempo}")
            if przelicz:
                k = wynik / f".{cz['id']}-{i}.mp4"
                renderuj_plik(p, od, do, tempo, k)
                kawalki.append(k)
            ws += napisy_pliku(p, od, do, tempo, przes)
            przes += (do - od) / tempo
        if args.ciecia:
            continue
        if przelicz:
            sklej(kawalki, pion)
            for k in kawalki:
                k.unlink()
            print(f"✅ pion/{pion.name} ({czas_yt(dlugosc(pion))})")
        if cfg.get("poziomo"):
            plansze = czasy_plansz(cz, ws)
            print(f"   plansze: " + ", ".join(f"{czas_yt(t)} {k}" for t, k in plansze))
            if args.podglad:
                podglady.append((cz, plansze, pion))
            elif not tylko_opis and (przelicz or not mp4.exists() or (args.poziom and (args.czesc is None or cz["id"] in args.czesc.split(",")))):
                poziomo(pion, plansze, wynik / "panele", mp4)
                print(f"✅ {mp4.name} (poziomo)")
        ws = popraw(ws, poprawki)
        zapisz_srt(w_napisy(ws), mp4.with_suffix(".srt"))
        (wynik / f"{cz['id']}.txt").write_text(
            f"{cz['tytul']}\n\n{cz['opis']}\n\n{cfg['stopka']}\n", encoding="utf-8")
        gotowe.append((cz, mp4, ws))

    if args.podglad:
        strona_podgladu(cfg, baza, wynik, podglady)
        return
    if args.ciecia or not gotowe:
        return

    # cały film: sklejka części + rozdziały + jeden .srt
    cal = wynik / "calosc.mp4"
    if not args.napisy:
        sklej([m for _, m, _ in gotowe], cal)
        if cfg.get("poziomo"):
            sklej([wynik / "pion" / m.name for _, m, _ in gotowe], wynik / "pion" / "calosc-pion.mp4")
    przes, rozdzialy, ws_cal = 0.0, [], []
    for cz, mp4, ws in gotowe:
        rozdzialy.append(f"{czas_yt(przes)} {cz['rozdzial']}")
        ws_cal += [(s + przes, e + przes, t) for s, e, t in ws]
        przes += dlugosc(mp4)
    zapisz_srt(w_napisy(ws_cal), cal.with_suffix(".srt"))
    (wynik / "playlista.txt").write_text(cfg["playlista"] + "\n", encoding="utf-8")
    brak = [cz["rozdzial"] for cz in cfg["czesci"] if cz not in [g[0] for g in gotowe]]
    (wynik / "calosc.txt").write_text(
        f"{cfg['calosc']['tytul']}\n\n{cfg['calosc']['opis']}\n\n" + "\n".join(rozdzialy)
        + f"\n\n{cfg['stopka']}\n", encoding="utf-8")
    print(f"✅ calosc.mp4 ({czas_yt(przes)})" + (f" — BEZ: {', '.join(brak)}" if brak else ""))


if __name__ == "__main__":
    main()
