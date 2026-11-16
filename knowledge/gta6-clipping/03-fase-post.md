# 03 - FASE POST (día 8)

## Cálculo (usar solo `plantillas/tabla-diaria.csv`)
| Métrica | Fórmula |
|---|---|
| Views totales | suma(views_24h) |
| Retención media | media(retencion_pct) de filas con dato |
| Mejor hook | hook con mayor views_24h; empate -> mayor retención |
| Mejor tipo de clip | categoría (de ideas-30-clips) con mayor media de views |
| Ingresos totales | suma(ingresos_eur) |
| Coste total | coste_fijo_total_eur (herramienta + juego) + horas totales × coste_hora (preguntar; si no, 0) |
| Horas totales | suma(min_invertidos)/60 |
| €/hora | ingresos_totales / horas_totales |
| Coste por clip | coste_total / nº clips |
Ejecutar con un script o a mano; mostrar los números y la fila que los origina.

## Decisión (umbrales fijos)
- **ESCALAR** si: ingresos ≥ 50 % del objetivo Y €/hora > 0 Y al menos 1 clip > 10.000 views.
- **PIVOTAR** si: ingresos < 50 % del objetivo PERO retención media ≥ 40 % o algún clip > 10.000 views. Pivotar = cambiar plataforma principal al mejor canal, o tipo de clip al mejor, o permiso a gameplay propio.
- **ABANDONAR** si: ingresos = 0 Y ningún clip > 3.000 views Y retención media < 30 %.
- Si ninguna regla aplica -> PIVOTAR con la variable más débil.
Mostrar la regla exacta que se ha cumplido.

## Salida obligatoria
1. Tabla de métricas.
2. Decisión + regla cumplida.
3. 3 aprendizajes (cada uno: dato -> conclusión -> acción).
4. Si sigue: plan 7 días siguientes con la misma tabla de bloques de `02-fase-durante.md`, concentrando el 70 % del tiempo en el mejor tipo de clip y mejor plataforma.
