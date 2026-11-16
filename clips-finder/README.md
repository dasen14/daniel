# clips-finder

Encuentra los mejores clips de un directo de Twitch (pensado para directos de GTA 6 de 6 horas) usando **el chat, no IA**. Cuando el chat explota, ha pasado algo.

Con un solo comando descarga el chat, detecta los picos y te deja una carpeta con clips verticales listos para TikTok / Reels / Shorts. No necesita API keys de Twitch.

## Cómo funciona

1. Descarga el chat completo del VOD con [TwitchDownloaderCLI](https://github.com/lay295/TwitchDownloader) y lo guarda en `chat.json`.
2. Cuenta los mensajes en ventanas de 10 segundos.
3. Los mensajes con risas (`jajaja`, `jeje`, `haha`, `lol`, `lmao`, `XD`, `KEKW`, `LUL`, `OMEGALUL`, `ICANT`, 😂, 🤣...) cuentan el doble.
4. Ordena las ventanas por score y se queda con las más altas. Si dos picos están a menos de 30 segundos, solo conserva el mayor.
5. Regla de los 20 segundos: el chat reacciona tarde, así que cada clip empieza 20 s **antes** del pico (pico en `01:12:30` → clip desde `01:12:10`).
6. Descarga solo el tramo de cada clip (no el VOD entero) y lo recorta con ffmpeg a 1080x1920 (9:16, recorte central), 40 s por defecto.
7. Escribe los clips numerados por intensidad y un `resumen.csv`.
8. Con `--subtitulos`, transcribe el audio con Whisper y quema los subtítulos en el clip.

## Instalación

Necesitas Python 3.9+ y dos programas externos:

**ffmpeg**

```bash
winget install ffmpeg        # Windows
```

```bash
brew install ffmpeg          # macOS
```

```bash
sudo apt install ffmpeg      # Linux
```

**TwitchDownloaderCLI** — descarga el zip de tu sistema desde [las releases](https://github.com/lay295/TwitchDownloader/releases), descomprímelo y deja el ejecutable en el PATH o en esta misma carpeta, junto a `main.py`. En macOS/Linux dale permisos de ejecución:

```bash
chmod +x TwitchDownloaderCLI
```

**Whisper (solo si vas a usar `--subtitulos`)**

```bash
pip install -r requirements.txt
```

Sin subtítulos no hace falta instalar nada con pip: el resto usa solo la librería estándar.

## Uso

```bash
python main.py --vod <URL_O_ID_DEL_VOD> --salida ./clips --max_clips 10
```

| Opción | Por defecto | Qué hace |
| --- | --- | --- |
| `--vod` | (obligatorio) | URL o ID del VOD |
| `--salida` | `./clips` | Carpeta de salida |
| `--max_clips` | `10` | Número máximo de clips |
| `--duracion` | `40` | Duración de cada clip en segundos |
| `--subtitulos` | desactivado | Quema subtítulos generados con Whisper |
| `--modelo_whisper` | `small` | Modelo de Whisper (`tiny`, `base`, `small`, `medium`, `large`) |
| `--calidad` | la mejor | Calidad a descargar, p. ej. `1080p60` |
| `--solo_analisis` | desactivado | Solo detecta picos y escribe `resumen.csv`, sin cortar vídeo |
| `--chat` | — | Reutiliza un `chat.json` ya descargado |
| `--video` | — | Corta desde un vídeo local del VOD completo en vez de descargar cada tramo |
| `--twitchdownloader` | — | Ruta al ejecutable de TwitchDownloaderCLI |

## Ejemplo

El ID `2301234567` es un marcador: cámbialo por el de un VOD que siga disponible (los VOD de Twitch caducan a los 7-60 días).

```bash
python main.py --vod https://www.twitch.tv/videos/2301234567 --salida ./clips --max_clips 10
```

Salida por consola (cifras ilustrativas):

```
[1/4] Descargando el chat del VOD https://www.twitch.tv/videos/2301234567 (puede tardar unos minutos)...
[2/4] Analizando el chat en ventanas de 10 s...
      184302 mensajes, 10 picos seleccionados.
[4/4] Cortando 10 clips verticales (1080x1920) de 40 s...
      01_pico_01-12-30.mp4  (pico 01:12:30, inicio 01:12:10, score 412)
      02_pico_00-45-10.mp4  (pico 00:45:10, inicio 00:44:50, score 377)
      ...
Listo: 10 clips en /ruta/a/clips (resumen en resumen.csv)
```

Carpeta resultante:

```
clips/
├── chat.json
├── resumen.csv
├── 01_pico_01-12-30.mp4
├── 02_pico_00-45-10.mp4
└── ...
```

`resumen.csv`:

```csv
clip,timestamp_pico,timestamp_inicio,mensajes,score
01_pico_01-12-30.mp4,01:12:30,01:12:10,298,412
02_pico_00-45-10.mp4,00:45:10,00:44:50,301,377
```

`mensajes` es el número real de mensajes en la ventana de 10 s del pico; `score` es ese recuento con las risas contando doble.

Otros usos:

```bash
python main.py --vod 2301234567 --solo_analisis
```

```bash
python main.py --vod 2301234567 --duracion 30 --subtitulos
```

```bash
python main.py --vod 2301234567 --chat ./clips/chat.json --max_clips 20
```

## Errores habituales

- **«ffmpeg no está instalado»** / **«No encuentro TwitchDownloaderCLI»**: instálalos como se indica arriba. Se comprueba antes de descargar nada.
- **«Este VOD no tiene chat»**: el VOD no tiene replay de chat (highlight antiguo, chat desactivado). Sin chat no hay picos.
- **No se pudo descargar el chat**: URL/ID incorrecta, VOD caducado o solo para suscriptores.
- **ffmpeg falla con `--subtitulos`**: tu ffmpeg no trae `libass` (filtro `subtitles`); instala una build completa.
- Si un clip concreto falla, los demás se generan igualmente y el programa termina con código de error 1.

## Limitaciones

- El recorte vertical es siempre el centro de la imagen; si la acción está en un lateral, se pierde.
- Un pico de chat también puede ser un raid, una donación o un sorteo: revisa los clips antes de publicar.
