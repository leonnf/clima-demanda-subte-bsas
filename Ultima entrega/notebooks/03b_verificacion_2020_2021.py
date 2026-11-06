#!/usr/bin/env python3
"""03b - Verificación completa de la demanda 2020 y 2021 contra los molinetes.

Motivo: los históricos 2020/2021 traen formatos de fecha mezclados
(dd/mm/aaaa, m/d/aaaa y aaaa-mm-dd), por lo que la verificación puntual del
paso (c) de 03 no coincide. Acá se recalcula la demanda diaria completa de
2020 y 2021 (una sola lectura por lotes por archivo) y se compara con
recursos/demanda_diaria_subte_2018_2021.csv.

Regla de desambiguación: el archivo viene ordenado por fecha; para cada fila
ambigua se toma la interpretación (d/m o m/d) que mantiene la serie
monóno­nica no decreciente, priorizando el formato vigente.
"""
from __future__ import annotations

import calendar

import numpy as np
import pandas as pd

from comun import DSETS, guardar_tabla

CHUNK = 1_000_000
csv = pd.read_csv("recursos/demanda_diaria_subte_2018_2021.csv", parse_dates=["fecha"])


def _valido(mes: int, dia: int) -> bool:
    return 1 <= mes <= 12 and 1 <= dia <= calendar.monthrange(2020, mes)[1]


def serie_diaria(archivo: str, sep: str, col_fecha: int, col_total: int,
                 anio: int) -> tuple[pd.Series, dict]:
    acum: dict[pd.Timestamp, float] = {}
    ctrl = {"filas": 0, "iso": 0, "slash": 0, "ilegibles": 0,
            "ambiguas_resueltas": 0, "cambios_formato": 0}
    prev = 0            # (mes*100+dia) de la última fila válida
    fmt = "d/m"         # formato vigente

    for ch in pd.read_csv(DSETS / archivo, sep=sep, usecols=["FECHA", "pax_TOTAL"],
                          dtype=str, chunksize=CHUNK, header=0):
        s = ch.iloc[:, 0].str.strip()
        tot = pd.to_numeric(ch.iloc[:, 1], errors="coerce")
        ctrl["filas"] += len(ch)

        # --- fechas ISO (aaaa-mm-dd): sin ambigüedad --------------------
        iso = s.str.contains("-", regex=False, na=False).astype(bool)
        ctrl["iso"] += int(iso.sum())
        if iso.any():
            fs = pd.to_datetime(s[iso], format="%Y-%m-%d", errors="coerce")
            for f, t in zip(fs.tolist(), tot[iso].tolist()):
                if pd.notna(f) and pd.notna(t):
                    acum[f] = acum.get(f, 0.0) + float(t)
                    prev = f.month * 100 + f.day

        # --- fechas con barra ------------------------------------------
        bar = (~iso) & s.str.contains("/", regex=False, na=False).astype(bool)
        ctrl["slash"] += int(bar.sum())
        if bar.any():
            p = s[bar].str.split("/", expand=True)
            a = pd.to_numeric(p[0], errors="coerce").tolist()
            b = pd.to_numeric(p[1], errors="coerce").tolist()
            tt = tot[bar].tolist()
            for ai, bi, t in zip(a, b, tt):
                if ai is None or bi is None or np.isnan(ai) or np.isnan(bi) or pd.isna(t):
                    ctrl["ilegibles"] += 1
                    continue
                ai, bi = int(ai), int(bi)
                if ai > 12 and bi > 12:
                    ctrl["ilegibles"] += 1
                    continue
                if ai > 12:
                    mes, dia = bi, ai                 # sólo puede ser d/m
                elif bi > 12:
                    mes, dia = ai, bi                 # sólo puede ser m/d
                else:
                    # ambigua: probar el formato vigente y, si rompe el orden,
                    # la otra interpretación
                    ctrl["ambiguas_resueltas"] += 1
                    if fmt == "d/m":
                        mc, dc, ma, da = bi, ai, ai, bi
                    else:
                        mc, dc, ma, da = ai, bi, bi, ai
                    if _valido(mc, dc) and mc * 100 + dc >= prev:
                        mes, dia = mc, dc
                    elif _valido(ma, da) and ma * 100 + da >= prev:
                        mes, dia = ma, da
                        nuevo = "m/d" if fmt == "d/m" else "d/m"
                        ctrl["cambios_formato"] += 1
                        fmt = nuevo
                    else:
                        mes, dia = mc, dc              # último recurso
                        if not _valido(mes, dia):
                            ctrl["ilegibles"] += 1
                            continue
                if not _valido(mes, dia):
                    ctrl["ilegibles"] += 1
                    continue
                f = pd.Timestamp(year=anio, month=mes, day=dia)
                acum[f] = acum.get(f, 0.0) + float(t)
                prev = mes * 100 + dia

    ser = pd.Series(acum).sort_index()
    return ser, ctrl


tablas = []
for archivo, sep, cf, ct, anio in [("historico_2020.csv", ",", 1, 10, 2020),
                                   ("historico_2021.csv", ";", 2, 11, 2021)]:
    ser, ctrl = serie_diaria(archivo, sep, cf, ct, anio)
    ref = csv[csv["fecha"].dt.year == anio].set_index("fecha")["demanda_pasajeros"]
    cmp = pd.DataFrame({"molinetes": ser, "csv": ref}).dropna(how="all")
    cmp["dif"] = cmp["csv"] - cmp["molinetes"]
    ok = cmp["dif"].abs() < 0.5
    print(f"\n{anio}: {ctrl}")
    print(f"  días con molinetes: {ser.size} | días en el CSV: {ref.size} | "
          f"comparables: {int(cmp['dif'].notna().sum())} | coinciden: {int(ok.sum())} | "
          f"difieren: {int((~ok & cmp['dif'].notna()).sum())} | "
          f"dif. máx.: {cmp['dif'].abs().max():,.0f}")
    ej = cmp[(~ok) & cmp["dif"].notna()].head(5).round(0)
    print(ej.to_string())
    tablas.append({"anio": anio, "filas_leidas": ctrl["filas"],
                   "fechas_iso": ctrl["iso"], "fechas_con_barra": ctrl["slash"],
                   "ambiguas_resueltas": ctrl["ambiguas_resueltas"],
                   "cambios_formato": ctrl["cambios_formato"],
                   "fechas_ilegibles": ctrl["ilegibles"],
                   "dias_con_molinetes": int(ser.size), "dias_en_csv": int(ref.size),
                   "dias_comparables": int(cmp["dif"].notna().sum()),
                   "dias_coinciden": int(ok.sum()),
                   "dias_difieren": int((~ok & cmp["dif"].notna()).sum()),
                   "dif_max_abs": float(cmp["dif"].abs().max())})
    cmp.round(0).to_csv(f"Ultima entrega/resultados/tablas/"
                        f"t03b_comparacion_diaria_{anio}.csv", encoding="utf-8")

guardar_tabla(pd.DataFrame(tablas), "t03b_verificacion_completa_2020_2021")
print("\nOK 03b")
