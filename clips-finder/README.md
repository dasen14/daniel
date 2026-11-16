# clips-finder

Encuentra los mejores clips de un directo de Twitch **usando el chat, no IA**.
Cuando pasa algo brutal, el chat explota: la herramienta busca esos picos y te
deja una carpeta con los clips ya cortados en vertical (1080x1920).

Pensado para directos largos (p. ej. 6 horas de GTA 6) que no quieres ver enteros.

## Cómo funciona

1. Descarga el chat completo del VOD con TwitchDownloaderCLI (`chat.json`).
2. Cuenta los mensajes en ventanas de 10 segundos.
3. Los mensajes con risas (`jajaja`, `jeje`, `lol`, `lmao`, `XD`, `KEKW`, `LUL`, `OMEGALUL`, 😂...) cuentan **x2**.
4. Ordena las ventanas por score y se queda con las más altas. Si dos picos están a menos de 30 s, solo sobrevive el mayor.
5. **Regla de los 20 segundos:** el chat reacciona tarde, así que el clip empieza 20 s antes del pico (pico en `01:12:30` → clip desde `01:12:10`).
6. Descarga solo el trozo de vídeo de cada clip (no el VOD entero) y lo recorta con ffmpeg a 9:16, 1080x1920.
7. Escribe los clips ordenados por intensidad y un `resumen.csv`.

No necesita API keys de Twitch ni cuenta.

## Instalación

Necesitas Python 3.8+ y dos programas externos:

**1. ffmpeg**

| Sistema | Comando |
|---|---|
| Windows | `winget install Gyan.FFmpeg` |
| macOS | `brew install ffmpeg` |
| Linux | `sudo apt install ffmpeg` |

**2. TwitchDownloaderCLI** (open-source y gratuito)

Descarga el zip de tu sistema desde
<https://github.com/lay295/TwitchDownloader/releases> (el que se llama
`TwitchDownloaderCLI-...`), descomprímelo y deja el ejecutable en una de estas
ubicaciones:

- en esta misma carpeta, junto a `main.py` (lo más fácil), o
- en cualquier carpeta del PATH, o
- donde quieras, indicándolo con `--twitchdownloader RUTA`.

En macOS/Linux dale permisos: `chmod +x TwitchDownloaderCLI`.

**3. Dependencias de Python** (solo si vas a usar `--subtitulos`)

```bash
pip install -r requirements.txt
```

Sin subtítulos no hace falta instalar nada: el resto usa solo la librería estándar.

## Uso

```bash
python main.py --vod <URL_O_ID_DEL_VOD> --salida ./clips --max_clips 10
```

| Opción | Por defecto | Qué hace |
|---|---|---|
| `--vod` | (obligatorio) | URL o ID del VOD |
| `--salida` | `./clips` | Carpeta de salida |
| `--max_clips` | `10` | Número máximo de clips |
| `--duracion` | `40` | Duración de cada clip en segundos |
| `--subtitulos` | desactivado | Quema subtítulos generados con Whisper a partir del audio |
| `--modelo_whisper` | `small` | Modelo de Whisper (`tiny`, `base`, `small`, `medium`, `large`) |
| `--idioma` | autodetectar | Idioma del audio para Whisper (`es`, `en`...) |
| `--video` | — | Vídeo local del VOD ya descargado; evita descargar de Twitch |
| `--solo_analisis` | desactivado | Solo detecta picos y escribe `resumen.csv`, sin cortar vídeo |
| `--twitchdownloader` | — | Ruta a TwitchDownloaderCLI si no está en el PATH |

## Ejemplo

```bash
python main.py --vod https://www.twitch.tv/videos/2345678901 --salida ./clips --max_clips 10
```

Sustituye la URL por la de un VOD real: es la dirección de la página del vídeo
en Twitch (`twitch.tv/videos/<número>`); también vale solo el número.

Salida por pantalla:

```
[1/4] Descargando chat del VOD (puede tardar varios minutos)...
[2/4] 184213 mensajes analizados en ventanas de 10 s
[3/4] 10 picos detectados:
      01. pico 01:12:30  clip desde 01:12:10  412 msgs  score 655
      02. pico 00:45:10  clip desde 00:44:50  380 msgs  score 590
      ...
[4/4] Cortando clip 1/10: 01_pico_01-12-30.mp4
...
Listo: 10 clips en /ruta/a/clips (+ resumen.csv)
```

Carpeta resultante:

```
clips/
├── 01_pico_01-12-30.mp4     <- el momento más bestia
├── 02_pico_00-45-10.mp4
├── ...
├── 10_pico_03-58-20.mp4
├── resumen.csv
└── chat.json                <- chat descargado (se reutiliza si repites el comando)
```

`resumen.csv`:

```csv
clip,timestamp_pico,timestamp_inicio,mensajes,score
01_pico_01-12-30.mp4,01:12:30,01:12:10,412,655
02_pico_00-45-10.mp4,00:45:10,00:44:50,380,590
```

(Las cifras del ejemplo son ilustrativas.)

Más ejemplos:

```bash
# Ver primero qué picos hay, sin descargar vídeo (rápido)
python main.py --vod 2345678901 --solo_analisis

# Clips de 60 s con subtítulos en español
python main.py --vod 2345678901 --duracion 60 --subtitulos --idioma es

# Ya tienes el VOD descargado en el disco
python main.py --vod 2345678901 --video directo.mp4
```

## Notas

- **Recorte vertical:** se recorta el centro de la imagen. Si la acción o la
  cámara del streamer están en un lateral, quedarán fuera.
- **Reutilización:** si `chat.json` ya existe en la carpeta de salida no se
  vuelve a descargar. Usa una carpeta distinta para cada VOD (o borra
  `chat.json`) para no mezclar chats.
- **Subtítulos:** la primera vez Whisper descarga el modelo. En CPU va lento;
  `--modelo_whisper base` es más rápido y `medium` más preciso.
- **Emotes de risa:** la lista está al principio de `main.py` (`EMOTES_RISA`);
  añade ahí los emotes propios del canal.

## Errores habituales

| Mensaje | Solución |
|---|---|
| `ffmpeg no está instalado...` | Instala ffmpeg (ver arriba) y abre una terminal nueva |
| `No encuentro TwitchDownloaderCLI` | Ponlo junto a `main.py` o usa `--twitchdownloader` |
| `Este VOD no tiene chat` | El VOD no conserva chat (highlight/subida, chat desactivado); no hay señal que analizar |
| `Falló la descarga del chat` | El VOD no existe, ha caducado o es solo para suscriptores |
