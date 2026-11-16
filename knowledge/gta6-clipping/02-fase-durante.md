# 02 - FASE DURANTE (días 1-7 tras el lanzamiento)

## Rutina diaria en bloques (ajustar a `horas_dia`)
Para 60 min:
| Bloque | Min | Qué hacer |
|---|---|---|
| Buscar momentos | 15 | Revisar VOD/stream/grabación propia. Anotar 5 timestamps con 1 línea cada uno. |
| Clipear | 20 | 3 clips máx. 15-35 s, 9:16, subtítulos estilo fijo. |
| Titular | 5 | Pedir al agente `clip: <descripción>` para hooks/título/descripción. |
| Publicar | 10 | 1 clip por plataforma. Horas: 13:00, 19:00, 22:00 hora local (ajustar por datos). |
| Responder | 10 | Contestar todos los comentarios de las últimas 24 h. Fijar el mejor comentario. |
Para 30 min: 10 / 12 / 3 / 5 / 0 (responder al día siguiente).

## Por clip (comando `clip:`)
Devolver SIEMPRE este bloque:
```
HOOKS (<8 palabras):
1. ...
2. ...
3. ...
TÍTULO: ...
DESCRIPCIÓN TikTok: [1 frase] + #GTA6 #GTAVI #ViceCity + [crédito]
DESCRIPCIÓN Reels: [1 frase] + 3-5 hashtags + [crédito]
DESCRIPCIÓN Shorts: [1 frase] #GTA6 #Shorts + [crédito]
```
Crédito obligatorio si el gameplay no es propio: `Clip de @streamer con permiso`.

## Si un clip flojea (comando `flojea:`)
Diagnóstico por síntoma. Aplicar UN cambio y volver a medir:
| Síntoma (datos de la plataforma) | Cambiar |
|---|---|
| Views bajas (< 300 en 24 h) y retención < 30 % | Hook: reescribir con otra fórmula |
| Views normales, retención cae en 0-3 s | Primeros 2 segundos: empezar en la acción, cortar intro |
| Retención buena hasta la mitad, luego cae | Duración: recortar a < 20 s |
| Retención ok, pocos guardados/compartidos | Subtítulos: resaltar palabra clave + cierre con pregunta |
| Comentarios piden contexto | Añadir 1 línea de contexto en el segundo 2 |

## Tabla diaria (comando `tabla`)
Fila en `plantillas/tabla-diaria.csv`:
`dia,clip_id,plataforma,hook,views_24h,retencion_pct,guardados,comentarios,ingresos_eur,min_invertidos`
Pedir al usuario los datos que falten. No rellenar con estimaciones.
