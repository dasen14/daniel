#!/usr/bin/env python3
"""Calcula las métricas de 03-fase-post.md desde tabla-diaria.csv.
Uso: python3 evaluar.py tabla-diaria.csv <coste_fijo_eur> <objetivo_eur>"""
import csv, sys
from collections import defaultdict
path, coste_fijo, objetivo = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
rows = [r for r in csv.DictReader(open(path)) if r.get("clip_id")]
f = lambda r, k: float(r[k]) if r.get(k, "").strip() else None
views = sum(f(r, "views_24h") or 0 for r in rows)
ret = [f(r, "retencion_pct") for r in rows if f(r, "retencion_pct") is not None]
ret_media = sum(ret) / len(ret) if ret else 0
ingresos = sum(f(r, "ingresos_eur") or 0 for r in rows)
horas = sum(f(r, "min_invertidos") or 0 for r in rows) / 60
mejor = max(rows, key=lambda r: ((f(r, "views_24h") or 0), (f(r, "retencion_pct") or 0)), default=None)
maxv = max((f(r, "views_24h") or 0 for r in rows), default=0)
print(f"clips: {len(rows)} | views: {views:.0f} | retención media: {ret_media:.1f}% | ingresos: {ingresos:.2f} €")
print(f"horas: {horas:.1f} | €/hora: {(ingresos/horas if horas else 0):.2f} | coste total: {coste_fijo:.2f} € | coste/clip: {(coste_fijo/len(rows) if rows else 0):.2f} €")
if mejor: print(f"mejor hook: {mejor['hook']} ({mejor['views_24h']} views)")
if ingresos >= 0.5 * objetivo and horas and ingresos / horas > 0 and maxv > 10000: d = "ESCALAR"
elif ingresos == 0 and maxv <= 3000 and ret_media < 30: d = "ABANDONAR"
else: d = "PIVOTAR"
print("DECISIÓN:", d)
