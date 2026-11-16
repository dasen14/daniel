#!/usr/bin/env python3
"""clips-finder: encuentra los mejores clips de un directo usando el chat de Twitch.

Sin IA: la señal es que el chat explota. Flujo:
  1. Descarga el chat del VOD con TwitchDownloaderCLI.
  2. Cuenta mensajes en ventanas de 10 s (las risas cuentan x2).
  3. Se queda con los picos más altos, sin solapes (< 30 s).
  4. Cada clip empieza 20 s ANTES del pico (el chat reacciona tarde).
  5. Corta cada clip en vertical 1080x1920 con ffmpeg.
  6. Escribe los clips + resumen.csv en la carpeta de salida.
"""

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

VENTANA = 10          # segundos por ventana de análisis
SEPARACION_MIN = 30   # dos picos a menos de esto se consideran el mismo momento
ANTICIPO = 20         # el clip empieza estos segundos antes del pico

# Risas en texto: jaja, jajaja, jeje, haha, lol, lmao, xd... (sin distinguir mayúsculas)
RISA_TEXTO = re.compile(
    r"(?<!\w)(?:[ajhsk]*(?:ja){2,}[ajhsk]*|(?:j+[aeiou]+){2,}j*|(?:h+[aeiou]+){2,}h*|lo+l+|lmf?ao+|x+d+|rofl)(?!\w)"
    r"|[😂🤣😆😹💀]",
    re.IGNORECASE,
)
# Emotes de risa habituales (Twitch, BTTV, FFZ, 7TV). Estos sí distinguen mayúsculas.
EMOTES_RISA = {
    "LUL", "LULW", "KEKW", "KEKL", "KEKWait", "OMEGALUL", "ICANT", "pepeLaugh",
    "EleGiggle", "4Head", "LMAO", "LuL", "OMEGALULiguess", "PepeLaugh", "KEKLEO",
    "xdd", "xdding", "JAJAJA", "Jajaja", "aaaJAJA",
}


class ErrorClips(Exception):
    """Error esperado: se muestra el mensaje al usuario sin traceback."""


# ---------------------------------------------------------------- utilidades

def hms(segundos, sep=":"):
    segundos = int(segundos)
    return f"{segundos // 3600:02d}{sep}{segundos % 3600 // 60:02d}{sep}{segundos % 60:02d}"


def ejecutar(cmd, descripcion, cwd=None):
    """Ejecuta un comando externo y lanza ErrorClips con el final de su salida si falla."""
    r = subprocess.run([str(c) for c in cmd], cwd=cwd, stdin=subprocess.DEVNULL,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, errors="replace")
    if r.returncode != 0:
        cola = "\n".join(r.stdout.strip().splitlines()[-15:])
        raise ErrorClips(f"Falló {descripcion} (código {r.returncode}):\n{cola}")
    return r.stdout


def buscar_ffmpeg():
    ruta = shutil.which("ffmpeg")
    if not ruta:
        raise ErrorClips(
            "ffmpeg no está instalado o no está en el PATH.\n"
            "  Windows: winget install Gyan.FFmpeg\n"
            "  macOS:   brew install ffmpeg\n"
            "  Linux:   sudo apt install ffmpeg")
    return ruta


def buscar_twitchdownloader(ruta_usuario):
    candidatos = [ruta_usuario] if ruta_usuario else [
        "TwitchDownloaderCLI", "TwitchDownloaderCLI.exe",
        Path(__file__).parent / "TwitchDownloaderCLI",
        Path(__file__).parent / "TwitchDownloaderCLI.exe",
    ]
    for c in candidatos:
        ruta = shutil.which(str(c))
        if ruta:
            return ruta
    raise ErrorClips(
        "No encuentro TwitchDownloaderCLI.\n"
        "  Descárgalo de https://github.com/lay295/TwitchDownloader/releases\n"
        "  y ponlo en el PATH, junto a main.py, o indícalo con --twitchdownloader RUTA")


# ---------------------------------------------------------------- 1. chat

def descargar_chat(td, vod, destino):
    if destino.exists():
        print(f"[1/4] Chat ya descargado, reutilizo {destino}")
        return
    print("[1/4] Descargando chat del VOD (puede tardar varios minutos)...")
    try:
        ejecutar([td, "chatdownload", "--id", vod, "-o", destino,
                  "--collision", "Overwrite", "--banner=false"],
                 "la descarga del chat")
    except ErrorClips as e:
        destino.unlink(missing_ok=True)
        raise ErrorClips(f"{e}\nComprueba que el VOD existe, es público y no ha caducado.")


def cargar_mensajes(ruta_json):
    """Devuelve una lista de (segundo_del_directo, texto)."""
    try:
        datos = json.loads(ruta_json.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        raise ErrorClips(f"No puedo leer el chat {ruta_json}: {e}")
    mensajes = []
    for c in datos.get("comments") or []:
        t = c.get("content_offset_seconds")
        if t is None:
            continue
        mensajes.append((float(t), (c.get("message") or {}).get("body") or ""))
    if not mensajes:
        raise ErrorClips(
            "Este VOD no tiene chat (0 mensajes). Sin chat no hay picos que detectar.\n"
            "Pasa con VODs muy antiguos, subidas/highlights sin chat o chat desactivado.")
    return mensajes


# ---------------------------------------------------------------- 2-5. análisis

def es_risa(texto):
    return bool(RISA_TEXTO.search(texto)) or any(p in EMOTES_RISA for p in texto.split())


def detectar_picos(mensajes, max_clips):
    """Ventanas de 10 s, risas x2, top N sin solapes. Devuelve lista de dicts."""
    n_mensajes, score = {}, {}
    for t, texto in mensajes:
        v = int(t // VENTANA)
        n_mensajes[v] = n_mensajes.get(v, 0) + 1
        score[v] = score.get(v, 0) + (2 if es_risa(texto) else 1)

    picos = []
    # De mayor a menor score; a igualdad, gana el que ocurre antes.
    for v in sorted(score, key=lambda v: (-score[v], v)):
        pico = v * VENTANA
        if any(abs(pico - p["pico"]) < SEPARACION_MIN for p in picos):
            continue  # solapa con un pico mayor ya elegido
        picos.append({"pico": pico, "inicio": max(0, pico - ANTICIPO),
                      "mensajes": n_mensajes[v], "score": score[v]})
        if len(picos) == max_clips:
            break
    return picos


# ---------------------------------------------------------------- 6. clips

def formato_srt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms % 3600000 // 60000:02d}:{ms % 60000 // 1000:02d},{ms % 1000:03d}"


def generar_srt(modelo, video, destino, idioma):
    resultado = modelo.transcribe(str(video), language=idioma, fp16=False)
    lineas = []
    for i, seg in enumerate(resultado["segments"], 1):
        lineas.append(f"{i}\n{formato_srt(seg['start'])} --> {formato_srt(seg['end'])}\n"
                      f"{seg['text'].strip()}\n")
    destino.write_text("\n".join(lineas), encoding="utf-8")
    return bool(lineas)


def cortar_clip(td, vod, video_local, inicio, duracion, destino, tmp, modelo, idioma, calidad=None):
    # Origen: o el vídeo local (--video) o solo el trozo necesario del VOD.
    if video_local:
        entrada = ["-ss", inicio, "-t", duracion, "-i", video_local]
    else:
        trozo = tmp / "trozo.mp4"
        cmd = [td, "videodownload", "--id", vod, "-o", trozo,
               "-b", f"{inicio}s", "-e", f"{inicio + duracion}s",
               "--collision", "Overwrite", "--banner=false",
               "--temp-path", tmp / "cache"]
        if calidad:
            cmd += ["-q", calidad]
        ejecutar(cmd, "la descarga del vídeo")
        entrada = ["-i", trozo]

    # Recorte central 9:16 y escalado a 1080x1920.
    filtro = "crop=ih*9/16:ih,scale=1080:1920,setsar=1"
    codificar = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                 "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart"]

    if modelo is None:
        ejecutar(["ffmpeg", "-y", *entrada, "-vf", filtro, *codificar, destino],
                 "el corte con ffmpeg")
        return

    # Con subtítulos: corto primero, transcribo el clip y quemo el .srt.
    sin_subs = tmp / "clip.mp4"
    ejecutar(["ffmpeg", "-y", *entrada, "-vf", filtro, *codificar, sin_subs],
             "el corte con ffmpeg")
    if not generar_srt(modelo, sin_subs, tmp / "subs.srt", idioma):
        shutil.move(sin_subs, destino)  # nadie habla en el clip
        return
    estilo = "FontSize=14,Bold=1,Outline=2,Alignment=2,MarginV=60"
    # cwd=tmp y nombres relativos para no tener que escapar rutas en el filtro.
    ejecutar(["ffmpeg", "-y", "-i", "clip.mp4",
              "-vf", f"subtitles=subs.srt:force_style='{estilo}'",
              *codificar[:6], "-c:a", "copy", "-movflags", "+faststart",
              destino.resolve()],
             "el quemado de subtítulos", cwd=tmp)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="Encuentra los mejores clips de un directo usando la actividad del chat de Twitch.")
    ap.add_argument("--vod", required=True, help="URL o ID del VOD de Twitch")
    ap.add_argument("--salida", default="./clips", help="carpeta de salida (por defecto ./clips)")
    ap.add_argument("--max_clips", type=int, default=10, help="número máximo de clips (por defecto 10)")
    ap.add_argument("--duracion", type=int, default=40, help="duración de cada clip en segundos (por defecto 40)")
    ap.add_argument("--subtitulos", action="store_true", help="quemar subtítulos generados con Whisper")
    ap.add_argument("--modelo_whisper", default="small", help="modelo de Whisper: tiny, base, small, medium... (por defecto small)")
    ap.add_argument("--idioma", default=None, help="idioma del audio para Whisper, p. ej. es o en (por defecto: autodetectar)")
    ap.add_argument("--video", default=None, help="vídeo local del VOD ya descargado (si no, se baja solo el trozo de cada clip)")
    ap.add_argument("--chat", default=None, help="JSON de chat ya descargado (por defecto se descarga y guarda en SALIDA/chat.json)")
    ap.add_argument("--calidad", default=None, help='calidad del vídeo a descargar, p. ej. "1080p60" (por defecto la mejor)')
    ap.add_argument("--solo_analisis", action="store_true", help="solo detectar picos y escribir resumen.csv, sin cortar vídeo")
    ap.add_argument("--twitchdownloader", default=None, help="ruta a TwitchDownloaderCLI si no está en el PATH")
    args = ap.parse_args()

    if args.max_clips < 1 or args.duracion < 1:
        raise ErrorClips("--max_clips y --duracion deben ser mayores que 0.")
    if args.video and not Path(args.video).is_file():
        raise ErrorClips(f"No existe el vídeo local: {args.video}")
    if args.chat and not Path(args.chat).is_file():
        raise ErrorClips(f"No existe el chat indicado en --chat: {args.chat}")

    # Comprobar dependencias antes de descargar nada.
    salida = Path(args.salida)
    chat_json = Path(args.chat) if args.chat else salida / "chat.json"
    cortar = not args.solo_analisis
    if cortar:
        buscar_ffmpeg()
    td = None
    if not chat_json.exists() or (cortar and not args.video):
        td = buscar_twitchdownloader(args.twitchdownloader)
    modelo = None
    if cortar and args.subtitulos:
        try:
            import whisper
        except ImportError:
            raise ErrorClips("--subtitulos necesita Whisper: pip install -r requirements.txt")
        print(f"Cargando modelo Whisper '{args.modelo_whisper}'...")
        modelo = whisper.load_model(args.modelo_whisper)

    salida.mkdir(parents=True, exist_ok=True)
    descargar_chat(td, args.vod, chat_json)

    mensajes = cargar_mensajes(chat_json)
    print(f"[2/4] {len(mensajes)} mensajes analizados en ventanas de {VENTANA} s")
    picos = detectar_picos(mensajes, args.max_clips)
    print(f"[3/4] {len(picos)} picos detectados:")
    for i, p in enumerate(picos, 1):
        p["nombre"] = f"{i:02d}_pico_{hms(p['pico'], '-')}.mp4"
        print(f"      {i:02d}. pico {hms(p['pico'])}  clip desde {hms(p['inicio'])}  "
              f"{p['mensajes']} msgs  score {p['score']}")

    with open(salida / "resumen.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["clip", "timestamp_pico", "timestamp_inicio", "mensajes", "score"])
        for p in picos:
            w.writerow([p["nombre"], hms(p["pico"]), hms(p["inicio"]), p["mensajes"], p["score"]])

    if not cortar:
        print(f"[4/4] Solo análisis: resumen en {salida / 'resumen.csv'}")
        return

    fallos = 0
    for i, p in enumerate(picos, 1):
        print(f"[4/4] Cortando clip {i}/{len(picos)}: {p['nombre']}")
        with tempfile.TemporaryDirectory(prefix="clips-finder-") as tmp:
            try:
                cortar_clip(td, args.vod, args.video, p["inicio"], args.duracion,
                            salida / p["nombre"], Path(tmp), modelo, args.idioma, args.calidad)
            except ErrorClips as e:
                fallos += 1
                print(f"      AVISO: {e}", file=sys.stderr)

    print(f"\nListo: {len(picos) - fallos} clips en {salida.resolve()} (+ resumen.csv)")
    if fallos:
        raise ErrorClips(f"{fallos} clip(s) no se pudieron generar; revisa los avisos de arriba.")


if __name__ == "__main__":
    try:
        main()
    except ErrorClips as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelado.", file=sys.stderr)
        sys.exit(130)
