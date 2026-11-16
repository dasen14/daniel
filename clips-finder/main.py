#!/usr/bin/env python3
"""clips-finder: encuentra los mejores clips de un VOD de Twitch usando el chat.

Sin IA y sin API keys: cuando el chat explota, ha pasado algo.

    python main.py --vod <URL_O_ID_DEL_VOD> --salida ./clips --max_clips 10
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
ANTICIPACION = 20     # el chat reacciona tarde: el clip empieza 20 s antes del pico

# Risas en texto, emotes de risa (en Twitch los emotes son texto) y emojis.
RISAS = re.compile(
    r"\b(?:a?(?:ja|je|ji|ha|he|js){2,}[jh]?"       # jaja, jajaja, jeje, haha, ajajaj, jsjs
    r"|lo+l|lmf?ao+|rofl|xd+"                       # lol, lmao, XD
    r"|kekw?|lul|lulw|omegalul|icant|pepelaugh)\b"  # emotes de risa
    r"|[😂🤣😆😹]",
    re.IGNORECASE,
)


class ErrorClips(Exception):
    """Error esperado: se muestra al usuario sin traceback."""


def hms(segundos, sep=":"):
    s = int(segundos)
    return f"{s // 3600:02d}{sep}{s % 3600 // 60:02d}{sep}{s % 60:02d}"


def ejecutar(cmd, **kwargs):
    """Ejecuta un comando externo y devuelve el proceso (sin lanzar si falla)."""
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kwargs)


# ---------------------------------------------------------------- dependencias

def buscar_ffmpeg():
    ruta = shutil.which("ffmpeg")
    if not ruta:
        raise ErrorClips(
            "ffmpeg no está instalado o no está en el PATH.\n"
            "  Windows: winget install ffmpeg\n"
            "  macOS:   brew install ffmpeg\n"
            "  Linux:   sudo apt install ffmpeg"
        )
    return ruta


def buscar_twitchdownloader(ruta_usuario):
    candidatos = [ruta_usuario] if ruta_usuario else []
    aqui = Path(__file__).resolve().parent
    for nombre in ("TwitchDownloaderCLI", "TwitchDownloaderCLI.exe"):
        candidatos += [shutil.which(nombre), aqui / nombre]
    for c in candidatos:
        if c and Path(c).is_file():
            return str(Path(c).resolve())
    raise ErrorClips(
        "No encuentro TwitchDownloaderCLI.\n"
        "  Descárgalo de https://github.com/lay295/TwitchDownloader/releases\n"
        "  y ponlo en el PATH, junto a main.py, o indica la ruta con --twitchdownloader."
    )


# ------------------------------------------------------------------------ chat

def descargar_chat(tdcli, vod, destino):
    print(f"[1/4] Descargando el chat del VOD {vod} (puede tardar unos minutos)...")
    p = subprocess.run(
        [tdcli, "chatdownload", "--id", vod, "-o", str(destino), "--collision", "Overwrite"]
    )
    if p.returncode != 0 or not destino.is_file():
        raise ErrorClips(
            "TwitchDownloaderCLI no pudo descargar el chat. Comprueba que la URL/ID del VOD "
            "es correcta, que el VOD sigue disponible y que no es solo para suscriptores."
        )


def cargar_offsets(ruta_chat):
    """Devuelve una lista de (segundo_del_vod, texto) por cada mensaje."""
    try:
        datos = json.loads(Path(ruta_chat).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as e:
        raise ErrorClips(f"No se pudo leer el JSON del chat ({ruta_chat}): {e}")
    mensajes = []
    for c in datos.get("comments") or []:
        offset = c.get("content_offset_seconds")
        if offset is None:
            continue
        mensajes.append((float(offset), (c.get("message") or {}).get("body") or ""))
    if not mensajes:
        raise ErrorClips(
            "Este VOD no tiene chat (0 mensajes). Sin chat no hay picos que detectar: "
            "puede que el VOD sea antiguo, un highlight sin replay de chat o que el chat estuviera desactivado."
        )
    return mensajes


def detectar_picos(mensajes, max_clips):
    """Agrupa en ventanas de 10 s, pondera risas x2 y elige los picos sin solaparse."""
    ventanas = {}  # índice de ventana -> [n_mensajes, score]
    for offset, texto in mensajes:
        v = ventanas.setdefault(int(offset // VENTANA), [0, 0])
        v[0] += 1
        v[1] += 2 if RISAS.search(texto) else 1

    picos = []
    orden = sorted(ventanas.items(), key=lambda kv: (-kv[1][1], kv[0]))
    for indice, (n, score) in orden:
        t = indice * VENTANA
        if all(abs(t - p["pico"]) >= SEPARACION_MIN for p in picos):
            picos.append({"pico": t, "inicio": max(0, t - ANTICIPACION), "mensajes": n, "score": score})
            if len(picos) == max_clips:
                break
    return picos


# ----------------------------------------------------------------------- vídeo

def descargar_tramo(tdcli, vod, inicio, duracion, destino, calidad):
    cmd = [tdcli, "videodownload", "--id", vod, "-b", f"{inicio}s", "-e", f"{inicio + duracion}s",
           "-o", destino, "--collision", "Overwrite", "--log-level", "Error", "--banner=false"]
    if calidad:
        cmd += ["-q", calidad]
    p = ejecutar(cmd)
    if p.returncode != 0 or not Path(destino).is_file():
        raise ErrorClips(f"No se pudo descargar el vídeo del tramo {hms(inicio)}:\n{p.stderr or p.stdout}")


def transcribir_a_srt(modelo, video, srt):
    resultado = modelo.transcribe(str(video), fp16=False)

    def marca(t):
        ms = int(round(t * 1000))
        return f"{ms // 3600000:02d}:{ms % 3600000 // 60000:02d}:{ms % 60000 // 1000:02d},{ms % 1000:03d}"

    lineas = []
    for i, seg in enumerate(resultado["segments"], 1):
        lineas.append(f"{i}\n{marca(seg['start'])} --> {marca(seg['end'])}\n{seg['text'].strip()}\n")
    Path(srt).write_text("\n".join(lineas), encoding="utf-8")
    return bool(lineas)


def cortar_vertical(ffmpeg, origen, destino, tmp, inicio=None, duracion=None, con_srt=False):
    """Recorta el centro a 9:16 y escala a 1080x1920. Si con_srt, quema tmp/subs.srt."""
    filtro = "crop=ih*9/16:ih,scale=1080:1920,setsar=1"
    if con_srt:
        # ffmpeg se ejecuta con cwd=tmp para no tener que escapar rutas en el filtro.
        filtro += ",subtitles=subs.srt:force_style='FontSize=14,Bold=1,Outline=2,Alignment=2,MarginV=60'"
    cmd = [ffmpeg, "-y", "-loglevel", "error"]
    if inicio is not None:
        cmd += ["-ss", inicio, "-t", duracion]
    cmd += ["-i", Path(origen).resolve(), "-vf", filtro,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", Path(destino).resolve()]
    p = ejecutar(cmd, cwd=tmp)
    if p.returncode != 0:
        raise ErrorClips(f"ffmpeg falló al generar {Path(destino).name}:\n{p.stderr.strip()}")


# ------------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description="Encuentra los mejores clips de un VOD de Twitch usando el chat.")
    ap.add_argument("--vod", required=True, help="URL o ID del VOD de Twitch")
    ap.add_argument("--salida", default="./clips", help="carpeta de salida (por defecto ./clips)")
    ap.add_argument("--max_clips", type=int, default=10, help="número máximo de clips (por defecto 10)")
    ap.add_argument("--duracion", type=int, default=40, help="duración de cada clip en segundos (por defecto 40)")
    ap.add_argument("--subtitulos", action="store_true", help="quemar subtítulos generados con Whisper")
    ap.add_argument("--modelo_whisper", default="small", help="modelo de Whisper: tiny, base, small, medium... (por defecto small)")
    ap.add_argument("--calidad", help='calidad del vídeo a descargar, p. ej. "1080p60" (por defecto la mejor)')
    ap.add_argument("--chat", help="usar un JSON de chat ya descargado en vez de descargarlo")
    ap.add_argument("--video", help="usar un vídeo local del VOD completo en vez de descargar cada tramo")
    ap.add_argument("--solo_analisis", action="store_true", help="solo detectar picos y escribir resumen.csv, sin cortar vídeo")
    ap.add_argument("--twitchdownloader", help="ruta al ejecutable TwitchDownloaderCLI")
    args = ap.parse_args()

    if args.max_clips < 1 or args.duracion < 1:
        raise ErrorClips("--max_clips y --duracion deben ser mayores que 0.")
    if args.video and not Path(args.video).is_file():
        raise ErrorClips(f"No existe el vídeo indicado en --video: {args.video}")

    # Comprobar todas las dependencias antes de empezar a descargar nada.
    ffmpeg = None if args.solo_analisis else buscar_ffmpeg()
    necesita_td = not args.chat or (not args.video and not args.solo_analisis)
    tdcli = buscar_twitchdownloader(args.twitchdownloader) if necesita_td else None
    whisper = None
    if args.subtitulos and not args.solo_analisis:
        try:
            import whisper
        except ImportError:
            raise ErrorClips("Para --subtitulos hace falta Whisper: pip install -r requirements.txt")

    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    if args.chat:
        ruta_chat = Path(args.chat)
        print(f"[1/4] Usando el chat ya descargado: {ruta_chat}")
    else:
        ruta_chat = salida / "chat.json"
        descargar_chat(tdcli, args.vod, ruta_chat)

    print("[2/4] Analizando el chat en ventanas de 10 s...")
    mensajes = cargar_offsets(ruta_chat)
    picos = detectar_picos(mensajes, args.max_clips)
    print(f"      {len(mensajes)} mensajes, {len(picos)} picos seleccionados.")

    for i, p in enumerate(picos, 1):
        p["clip"] = f"{i:02d}_pico_{hms(p['pico'], '-')}.mp4"

    with open(salida / "resumen.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["clip", "timestamp_pico", "timestamp_inicio", "mensajes", "score"])
        for p in picos:
            w.writerow([p["clip"], hms(p["pico"]), hms(p["inicio"]), p["mensajes"], p["score"]])

    if args.solo_analisis:
        for p in picos:
            print(f"      {p['clip']}  pico {hms(p['pico'])}  score {p['score']}")
        print(f"Listo (solo análisis): {salida / 'resumen.csv'}")
        return

    modelo = None
    if whisper:
        print(f"[3/4] Cargando el modelo de Whisper '{args.modelo_whisper}'...")
        modelo = whisper.load_model(args.modelo_whisper)

    print(f"[4/4] Cortando {len(picos)} clips verticales (1080x1920) de {args.duracion} s...")
    fallidos = 0
    with tempfile.TemporaryDirectory(prefix="clips-finder-") as tmp:
        tmp = Path(tmp)
        for p in picos:
            destino = salida / p["clip"]
            print(f"      {p['clip']}  (pico {hms(p['pico'])}, inicio {hms(p['inicio'])}, score {p['score']})")
            try:
                if args.video:
                    origen, corte = args.video, {"inicio": p["inicio"], "duracion": args.duracion}
                else:
                    origen, corte = tmp / "tramo.mp4", {}
                    descargar_tramo(tdcli, args.vod, p["inicio"], args.duracion, origen, args.calidad)
                if modelo:
                    # Primero el clip sin subtítulos, se transcribe, y se queman en una segunda pasada.
                    base = tmp / "base.mp4"
                    cortar_vertical(ffmpeg, origen, base, tmp, **corte)
                    if transcribir_a_srt(modelo, base, tmp / "subs.srt"):
                        cortar_vertical(ffmpeg, base, destino, tmp, con_srt=True)
                    else:
                        shutil.move(base, destino)  # nadie habla en el clip
                else:
                    cortar_vertical(ffmpeg, origen, destino, tmp, **corte)
            except ErrorClips as e:
                fallidos += 1
                print(f"      AVISO: {e}", file=sys.stderr)

    print(f"Listo: {len(picos) - fallidos} clips en {salida.resolve()} (resumen en resumen.csv)")
    if fallidos:
        raise ErrorClips(f"{fallidos} clip(s) no se pudieron generar; revisa los avisos de arriba.")


if __name__ == "__main__":
    try:
        main()
    except ErrorClips as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
