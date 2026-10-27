#!/usr/bin/env python3
"""Napisy EN / DE / UK do filmu BOGO z nagrań zespołu: tłumaczenie polskich .srt i wgranie na YouTube.

  python3 napisy_obce.py sklejka-2026-10.json                    # przetłumacz, czego brakuje, i wgraj
  python3 napisy_obce.py sklejka-2026-10.json --bez-wgrywania    # tylko pliki <id>.<jezyk>.srt
  python3 napisy_obce.py sklejka-2026-10.json --jezyki en --czesc 1-wstep   # zawężenie

Uruchamiać po `wgraj_yt.py` (filmy i napisy PL już są na YouTube). Bierze każdą część z playlisty
i cały film (<wynik>/<id>.srt) i robi <id>.en.srt, <id>.de.srt, <id>.uk.srt — ta sama liczba
napisów i te same czasy, tłumaczony jest tylko tekst (Claude: SDK, gdy jest ANTHROPIC_API_KEY w środowisku,
inaczej `claude -p` w ramach subskrypcji). Uruchamiać pythonem z ~/MyProjects/EmAutoTube/venv (google-api, anthropic).
Wgrane ścieżki zapisuje w <wynik>/yt-stan.json (`napisy_en` itd.), kolejne uruchomienie dokańcza resztę.

Koszt quoty: 400 za ścieżkę. 8 filmów × 3 języki = 24 ścieżki = ok. 9 600 jednostek, czyli prawie cały
dzienny limit (reset o 9:00) — gdy się skończy, uruchom ponownie następnego dnia albo wgraj pliki .srt
przez YouTube Studio w ego (Języki → Dodaj język → Napisy → Prześlij plik).
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import edycja as E

sys.path.insert(0, "/Users/emiliachodorowska/MyProjects/EmAutoTube/scripts")
from przetlumacz_napisy import parse_srt, wrap  # noqa: E402

MODEL = "claude-sonnet-5-5"
BATCH = 40
JEZYKI = {"en": ("English", "angielski"), "de": ("Deutsch", "niemiecki"), "uk": ("Українська", "ukraiński")}

SYSTEM = """\
Tłumaczysz napisy do filmu o promocji BOGO dōTERRA (olejki eteryczne). Mówią osoby z zespołu, po polsku.

Zasady:
- Tłumacz na naturalny, mówiony język docelowy, nie kalką z polskiej składni.
- Zachowaj liczbę napisów co do jednego. Każdy wejściowy napis ma dokładnie jeden wyjściowy.
- Nie scalaj, nie dziel, nie dopisuj i nie pomijaj napisów. Pusty napis zwróć jako pusty ciąg.
- Napis bywa urwany w pół zdania — tłumacz go tak, by po sklejeniu z sąsiednimi tworzył spójne zdanie.
- Nazwy produktów dōTERRA podawaj tak, jak w słowniczku (oficjalne nazwy, bez tłumaczenia marek).
- Nie dopisuj komentarzy, didaskaliów ani znaczników.
- Odpowiadaj wyłącznie tablicą JSON: [{"i": <numer>, "t": "<tłumaczenie>"}]."""


def zapytaj(prompt: str) -> str:
    """Odpowiedź modelu: SDK z kluczem API, a bez klucza `claude -p` (subskrypcja)."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        import anthropic
        r = anthropic.Anthropic().messages.create(model=MODEL, max_tokens=16000, system=SYSTEM,
                                                  messages=[{"role": "user", "content": prompt}])
        return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    import subprocess
    r = subprocess.run(["claude", "-p", "--model", MODEL, "--system-prompt", SYSTEM, "--tools", "",
                        "--no-session-persistence", "--output-format", "text"],
                       input=prompt, capture_output=True, text=True, timeout=900)
    if r.returncode:
        raise RuntimeError(r.stderr[-300:])
    return r.stdout


def slowniczek():
    return "\n".join(f"{pl} → {d['en']}" for pl, d in E.PRODUKTY.items())


def tlumacz_plik(srt: Path, jezyk: str) -> Path:
    cel = srt.with_suffix(f".{jezyk}.srt")
    cues = parse_srt(srt.read_text(encoding="utf-8"))
    out: dict[int, str] = {}
    for start in range(0, len(cues), BATCH):
        chunk = cues[start:start + BATCH]
        prompt = (f"Język docelowy: {JEZYKI[jezyk][1]} ({jezyk}).\n\nSłowniczek nazw produktów (PL → oficjalna nazwa):\n"
                  f"{slowniczek()}\n\nNapisy do przetłumaczenia:\n"
                  + json.dumps([{"i": c["i"], "t": c["text"]} for c in chunk], ensure_ascii=False))
        for proba in range(3):
            try:
                raw = zapytaj(prompt).strip()
                raw = raw[raw.find("["):raw.rfind("]") + 1] if "[" in raw else raw
                raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
                got = {int(x["i"]): x["t"] for x in json.loads(raw)}
                if any(c["i"] not in got for c in chunk) and proba < 2:
                    continue
                out.update(got)
                break
            except Exception:
                if proba == 2:
                    raise
    cel.write_text("\n".join(f"{c['i']}\n{c['time']}\n{wrap(out.get(c['i'], c['text']))}\n" for c in cues), encoding="utf-8")
    return cel


def main() -> None:
    cfg_path = Path(sys.argv[1]).resolve()
    cfg = json.loads(cfg_path.read_text())
    wynik = cfg_path.parent / cfg["wynik"]
    stan_plik = wynik / "yt-stan.json"
    stan = json.loads(stan_plik.read_text()) if stan_plik.exists() else {}
    arg = lambda n: sys.argv[sys.argv.index(n) + 1] if n in sys.argv else None
    jezyki = (arg("--jezyki") or ",".join(JEZYKI)).split(",")
    filmy = [arg("--czesc")] if arg("--czesc") else [cz["id"] for cz in cfg["czesci"] if not cz.get("czeka")] + ["calosc"]
    wgrywaj = "--bez-wgrywania" not in sys.argv

    yt = None
    for fid in filmy:
        srt = wynik / f"{fid}.srt"
        if not srt.exists():
            print(f"[{fid}] brak {srt.name} — pomijam", flush=True)
            continue
        for j in jezyki:
            cel = srt.with_suffix(f".{j}.srt")
            if not cel.exists():
                tlumacz_plik(srt, j)
                print(f"[{fid}] {cel.name}", flush=True)
            s = stan.get(fid, {})
            if not wgrywaj or s.get(f"napisy_{j}"):
                continue
            if not s.get("video_id"):
                print(f"[{fid}] nie ma na YouTube — najpierw wgraj_yt.py", flush=True)
                continue
            if yt is None:
                from googleapiclient.http import MediaFileUpload
                from napisy_youtube import service
                yt = service()
            try:
                yt.captions().insert(part="snippet", body={"snippet": {
                    "videoId": s["video_id"], "language": j, "name": JEZYKI[j][0], "isDraft": False}},
                    media_body=MediaFileUpload(str(cel), mimetype="application/octet-stream")).execute()
            except Exception as exc:  # noqa: BLE001
                print(f"❌ {exc}"[:300], flush=True)
                if "quota" in str(exc).lower():
                    print("Quota wyczerpana — reszta przy kolejnym przebiegu (reset o 9:00).", flush=True)
                return
            s[f"napisy_{j}"] = True
            stan_plik.write_text(json.dumps(stan, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"[{fid}] ✅ napisy {j}", flush=True)


if __name__ == "__main__":
    main()
