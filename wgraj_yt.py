#!/usr/bin/env python3
"""Sklejka BOGO → YouTube: części do playlisty + cały film z rozdziałami, napisy PL, wszystko niepubliczne.

  python3 wgraj_yt.py sklejka-2026-10.json               # wgraj, czego jeszcze nie ma
  python3 wgraj_yt.py sklejka-2026-10.json --od-nowa     # nowa wersja wszystkiego: stare wypadają z playlisty
  python3 wgraj_yt.py sklejka-2026-10.json --bez-calosci # tylko części do playlisty
  python3 wgraj_yt.py sklejka-2026-10.json --usun-stare  # skasuj z kanału filmy odłożone przez --od-nowa

Bierze to, co zrobił `sklejka.py` w katalogu "wynik": <id>.mp4 + <id>.srt + <id>.txt
(1. linia = tytuł, reszta = opis), calosc.* i playlista.txt.
Części z "czeka": true w JSON (brak pliku albo czekamy na lepszą wersję) są pomijane —
YouTube nie pozwala podmienić pliku w wgranym filmie, więc wgrywamy tylko wersję ostateczną.
Cały film idzie dopiero wtedy, gdy żadna część nie czeka.

Stan po każdym kroku leci do <wynik>/yt-stan.json — kolejne uruchomienie zaczyna od
pierwszego niezrobionego kroku. Koszt quoty: upload 1, wpis do playlisty 50, napisy 400,
utworzenie playlisty 50.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

EMAUTOTUBE = Path("/Users/emiliachodorowska/MyProjects/EmAutoTube")
sys.path.insert(0, str(EMAUTOTUBE / "backend"))
sys.path.insert(0, str(EMAUTOTUBE / "scripts"))

from googleapiclient.http import MediaFileUpload  # noqa: E402
from napisy_youtube import service  # noqa: E402


def upload(path: Path, title: str, description: str) -> str:
    cwd = os.getcwd()
    os.chdir(EMAUTOTUBE / "backend")  # credentials.json / token.json leżą w backend/; privacy z config.json = unlisted
    try:
        from downloader import VideoInfo
        from uploader import YouTubeUploader
        up = YouTubeUploader()
        if not up.is_available:
            raise RuntimeError(f"YouTube niedostępny: {up.initialization_error_message}")
        url = up.upload_video(video_path=path, video_info=VideoInfo({"title": title}),
                              custom_description=description)
    finally:
        os.chdir(cwd)
    if not url:
        raise RuntimeError("upload nie zwrócił adresu")
    return url.split("v=")[-1].split("&")[0]


def main() -> None:
    cfg_path = Path(sys.argv[1]).resolve()
    cfg = json.loads(cfg_path.read_text())
    wynik = cfg_path.parent / cfg["wynik"]
    stan_plik = wynik / "yt-stan.json"
    stan = json.loads(stan_plik.read_text()) if stan_plik.exists() else {}

    def save():
        stan_plik.write_text(json.dumps(stan, ensure_ascii=False, indent=1), encoding="utf-8")

    yt = service()
    if "--od-nowa" in sys.argv:
        stare, mapa = stan.setdefault("stare", []), stan.setdefault("stare_map", {})
        for k in list(stan):
            if isinstance(stan[k], dict) and k != "stare_map" and stan[k].get("video_id"):
                mapa[k] = stan.pop(k)["video_id"]
                stare.append(mapa[k])
        save()
        print(f"odłożone stare wersje: {len(stare)}", flush=True)
    if "--usun-stare" in sys.argv:
        for vid in list(stan.get("stare", [])):
            yt.videos().delete(id=vid).execute()
            stan["stare"].remove(vid)
            save()
            print(f"usunięty z kanału: {vid}", flush=True)
        return
    kolejnosc = [cz["id"] for cz in cfg["czesci"]]
    czeka = [cz["id"] for cz in cfg["czesci"] if cz.get("czeka")]

    if not stan.get("playlista"):
        r = yt.playlists().insert(part="snippet,status", body={
            "snippet": {"title": cfg["playlista"], "description": cfg["stopka"]},
            "status": {"privacyStatus": "unlisted"}}).execute()
        stan["playlista"] = r["id"]
        save()
        print(f"playlista: https://www.youtube.com/playlist?list={r['id']}", flush=True)

    filmy = [i for i in kolejnosc if i not in czeka] + ([] if czeka or "--bez-calosci" in sys.argv else ["calosc"])
    try:
        for fid in filmy:
            s = stan.setdefault(fid, {})
            mp4, srt, txt = (wynik / f"{fid}{e}" for e in (".mp4", ".srt", ".txt"))
            if not mp4.exists():
                print(f"[{fid}] brak {mp4.name} — pomijam", flush=True)
                continue
            tytul, opis = txt.read_text(encoding="utf-8").split("\n", 1)
            if not s.get("video_id"):
                s["video_id"] = upload(mp4, tytul.strip(), opis.strip())
                save()
                print(f"[{fid}] wgrany: https://youtu.be/{s['video_id']}", flush=True)
            if fid != "calosc" and not s.get("w_playliscie"):
                # pozycja = ile wcześniejszych (wg JSON) części już siedzi w playliście
                poz = sum(1 for i in kolejnosc[:kolejnosc.index(fid)] if stan.get(i, {}).get("w_playliscie"))
                yt.playlistItems().insert(part="snippet", body={"snippet": {
                    "playlistId": stan["playlista"], "position": poz,
                    "resourceId": {"kind": "youtube#video", "videoId": s["video_id"]}}}).execute()
                s["w_playliscie"] = True
                save()
                print(f"[{fid}] w playliście (pozycja {poz + 1})", flush=True)
            if not s.get("napisy"):
                yt.captions().insert(
                    part="snippet",
                    body={"snippet": {"videoId": s["video_id"], "language": "pl",
                                      "name": "Polski", "isDraft": False}},
                    media_body=MediaFileUpload(str(srt), mimetype="application/octet-stream"),
                ).execute()
                s["napisy"] = True
                save()
                print(f"[{fid}] ✅ napisy PL", flush=True)
    except Exception as exc:  # noqa: BLE001
        save()
        print(f"❌ {exc}"[:300], flush=True)
        if "quota" in str(exc).lower():
            print("Quota wyczerpana — reszta przy kolejnym przebiegu (reset o 9:00).", flush=True)

    # stara wersja wypada z playlisty dopiero, gdy jej następca już w niej jest
    zastapione = {stan["stare_map"][f] for f in stan.get("stare_map", {})
                  if stan.get(f, {}).get("w_playliscie") or f == "calosc"}
    tok = None
    while True:
        r = yt.playlistItems().list(part="snippet", playlistId=stan["playlista"], maxResults=50,
                                    pageToken=tok).execute()
        for it in r["items"]:
            if it["snippet"]["resourceId"]["videoId"] in zastapione:
                yt.playlistItems().delete(id=it["id"]).execute()
                print(f"z playlisty wypadł: {it['snippet']['resourceId']['videoId']}", flush=True)
        tok = r.get("nextPageToken")
        if not tok:
            break

    print(f"\nPlaylista: https://www.youtube.com/playlist?list={stan['playlista']}")
    for fid in kolejnosc + ["calosc"]:
        v = stan.get(fid, {}).get("video_id")
        print(f"  {fid}: " + (f"https://youtu.be/{v}" if v else ("czeka" if fid in czeka or fid == "calosc" else "—")))


if __name__ == "__main__":
    main()
