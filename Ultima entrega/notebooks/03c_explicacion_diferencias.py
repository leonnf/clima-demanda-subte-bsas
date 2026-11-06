#!/usr/bin/env python3
"""03c - Análisis de las diferencias 2020/2021 entre molinetes y el CSV de demanda.

Lee las tablas ya generadas por 03b (no vuelve a leer los históricos) y
cuantifica cuántas diferencias se explican por un intercambio día<->mes.
"""
from __future__ import annotations

import pandas as pd

from comun import guardar_tabla

filas = []
for anio in (2020, 2021):
    c = pd.read_csv(f"Ultima entrega/resultados/tablas/t03b_comparacion_diaria_{anio}.csv",
                    index_col=0, parse_dates=True)
    dif = c[c["dif"].abs() > 0.5]

    def swap(d: pd.Timestamp) -> pd.Timestamp | None:
        try:
            return pd.Timestamp(year=d.year, month=d.day, day=d.month)
        except ValueError:
            return None

    explicadas = 0
    for d in dif.index:
        s = swap(d)
        if s is None or s not in c.index:
            continue
        if pd.notna(c.loc[s, "molinetes"]) and abs(c.loc[s, "molinetes"] - c.loc[d, "csv"]) < 0.5:
            explicadas += 1
    filas.append({
        "anio": anio, "dias_comparables": int(c["dif"].notna().sum()),
        "dias_coinciden": int((c["dif"].abs() < 0.5).sum()),
        "dias_difieren": len(dif),
        "diferencias_explicadas_por_intercambio_dia_mes": explicadas,
        "pct_explicadas": 100 * explicadas / len(dif) if len(dif) else 0.0,
        "dif_max_abs": float(c["dif"].abs().max()),
        "dias_sin_molinetes": int(c["molinetes"].isna().sum()),
        "dias_sin_csv": int(c["csv"].isna().sum()),
    })

t = pd.DataFrame(filas)
guardar_tabla(t.round(2), "t03c_explicacion_diferencias_2020_2021")
print(t.round(2).to_string(index=False))
print("OK 03c")
