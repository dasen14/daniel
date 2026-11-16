# 01 - FASE PREVIA (antes del lanzamiento)

Orden de pasos: 1 Herramienta -> 2 Permiso -> 3 Checklist -> 4 Plan 7 días. No saltar.

## PASO 1 - Verificar la herramienta
Rellena esta tabla con datos de la web oficial (WebSearch + WebFetch si hay). Cada celda sin verificar = `VERIFICAR`.

| Campo | Valor | Fuente + fecha |
|---|---|---|
| Precio plan de pago (€/mes) | | |
| Plan gratis: existe | | |
| Límite plan gratis (minutos/clips/mes) | | |
| Marca de agua en gratis | | |
| Exportación vertical 9:16 | | |
| Subtítulos automáticos (idioma español) | | |
| Importa desde YouTube/Twitch por URL | | |
| Publicación directa a TikTok/Reels/Shorts | | |

Webs de referencia (verificar que siguen activas): openshorts.ai, ssemble.com, autoclip.ai, clipship.ai, clippersflow.com.
Regla de decisión: si el plan gratis pone marca de agua Y no exporta 9:16 -> no sirve para el test de 7 días; proponer alternativa o plan de pago y sumar su coste a `coste_fijo_total_eur`.

## PASO 2 - Permiso
Si `permiso = sin permiso`, ofrecer EXACTAMENTE estas 3 vías:
1. **Gameplay propio**: comprar/jugar GTA 6 y grabar en consola (PS5: botón Create; Xbox: botón Share). Coste = precio del juego (verificar). Cubierto por política de creadores de Rockstar (verificar texto vigente).
2. **Programa oficial de clipping de un streamer**: buscar en Discord/Twitter del streamer "clipping program", "clippers wanted", o plataformas como Whop/ClipBounty (verificar condiciones y pago por 1.000 views). Guardar captura del acuerdo.
3. **Permiso directo por escrito**: DM a 5 streamers pequeños (500-5.000 viewers) con esta plantilla:
   > Hola [nombre], hago clips verticales de GTA 6. ¿Me autorizas a clipear tu stream con crédito y enlace a tu canal en cada vídeo? Te paso los clips antes de publicar si quieres.
   Guardar la respuesta escrita.
Sin una de las 3 resuelta -> no se avanza a DURANTE.

## PASO 3 - Checklist previa
- [ ] 3 cuentas creadas con el mismo nombre y avatar (TikTok, Instagram, YouTube).
- [ ] Bio (máx. 80 caracteres): `Clips de GTA 6 cada día | [crédito a streamer o "gameplay propio"]`.
- [ ] Vídeo fijado de presentación de 10 s (opcional).
- [ ] 5 plantillas de hook guardadas (ver abajo).
- [ ] Estilo de subtítulos fijado (ver abajo).
- [ ] Carpeta de 30 ideas de clips (ver abajo) copiada a `plantillas/ideas-30-clips.md`.
- [ ] Herramienta instalada y 1 clip de prueba exportado en 9:16 sin errores.
- [ ] Tabla diaria creada (`plantillas/tabla-diaria.csv`).

### Fórmulas de hook (menos de 8 palabras)
| Fórmula | Ejemplo |
|---|---|
| Pregunta imposible | "¿Esto se puede hacer en GTA 6?" |
| Número + sorpresa | "3 segundos y perdió todo" |
| Contraste | "Parecía fácil. No lo era." |
| Dato oculto | "Nadie vio este detalle de Vice City" |
| Reto | "Intenta no reírte con este NPC" |

### Estilo de subtítulos (fijo para todos los clips)
- Fuente gruesa sans (Montserrat Black o similar), blanco con borde negro.
- 1-3 palabras por pantalla, centrado en tercio inferior-medio.
- Palabra clave en amarillo. Sin emojis en subtítulos.
- Duración objetivo: 15-35 s. Hook en pantalla en el segundo 0.

### 30 ideas de clips de GTA 6 (por categoría)
Física/bugs: 1 ragdoll absurdo · 2 coche volando · 3 NPC atascado · 4 bug gracioso de animación · 5 explosión en cadena.
Detalles del mundo: 6 reflejo/agua · 7 clima extremo · 8 interior secreto · 9 easter egg de GTA anteriores · 10 referencia a Vice City original.
Persecuciones: 11 escape a 5 estrellas · 12 salto imposible · 13 choque frontal cámara lenta · 14 persecución en moto · 15 huida en barco.
NPCs/diálogos: 16 frase viral de NPC · 17 reacción de NPC a algo raro · 18 policía haciendo algo absurdo · 19 pelea callejera · 20 NPC en redes sociales del juego.
Comparativas: 21 GTA 5 vs GTA 6 mismo lugar · 22 gráficos lluvia · 23 animación de recarga · 24 densidad de tráfico · 25 ciclo día/noche.
Momentos de streamer (solo con permiso): 26 grito/reacción · 27 primera muerte · 28 primera misión fallida · 29 descubrimiento sorpresa · 30 predicción cumplida/fallida.

## PASO 4 - Plan 7 días previos (30-60 min/día)
| Día | Tarea | Min |
|---|---|---|
| -7 | Crear 3 cuentas, bio, avatar | 45 |
| -6 | Instalar herramienta, clip de prueba 9:16, fijar estilo subtítulos | 60 |
| -5 | Resolver permiso (vía 1, 2 o 3). Enviar DMs si aplica | 45 |
| -4 | Grabar/clipear 3 clips de tráileres oficiales o GTA 5 para calentar cuentas (solo material permitido) | 60 |
| -3 | Publicar 1 clip de calentamiento por plataforma, anotar en tabla | 30 |
| -2 | Preparar 10 hooks escritos y 10 ideas priorizadas del listado de 30 | 30 |
| -1 | Confirmar hora de lanzamiento (zona horaria), lista de streamers con permiso, batería/espacio en consola | 30 |

Al cerrar el día -1: `fase_actual: DURANTE`, `dia_actual: 1` en estado.md.
