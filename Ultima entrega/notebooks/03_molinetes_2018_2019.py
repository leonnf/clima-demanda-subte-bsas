#!/usr/bin/env python3
"""03 - Pasada única sobre los históricos de molinetes 2018-2019.

(a) Demanda diaria recalculada vs recursos/demanda_diaria_subte_2018_2021.csv
(b) Demanda por estación y hora (días hábiles) -> recursos/demanda_estacion_hora_2018_2019.parquet
(c) Verificación puntual de 2020 y 2021 con awk (un día hábil por año)

Los archivos se leen una sola vez, por lotes (chunksize=1e6), con usecols+dtype.
"""
from __future__ import annotations

import subprocess
import time

import numpy as np
import pandas as pd

from comun import DSETS, guardar_tabla, norm_estacion, norm_linea

CHUNK = 1_000_000
USECOLS = ["fecha", "desde", "linea", "molinete", "estacion", "total"]
DTYPES = {"fecha": "str", "desde": "str", "linea": "str",
          "molinete": "str", "estacion": "str", "total": "str"}

# días hábiles reconstruidos en 02 (feriados del calendario AR)
base = pd.read_parquet("recursos/base_analitica.parquet")
habiles = set(base.loc[base["es_dia_habil"] == 1, "fecha"].astype("int64").values)
habiles = frozenset(habiles)

acum_dia: list[pd.DataFrame] = []
acum_eh: list[pd.DataFrame] = []
hashes: list[np.ndarray] = []
pares_raw: set[tuple[str, str]] = set()
molinete_code: dict[str, int] = {}
ctrl = {"filas": 0, "nulos_total": 0, "negativos": 0,
        "fechas_invalidas": 0, "desde_invalidos": 0}


def procesar(chunk: pd.DataFrame) -> None:
    ctrl["filas"] += len(chunk)
    tot = pd.to_numeric(chunk["total"], errors="coerce")
    ctrl["nulos_total"] += int(tot.isna().sum())
    ctrl["negativos"] += int((tot < 0).sum())

    fecha = pd.to_datetime(chunk["fecha"], format="%Y-%m-%d", errors="coerce")
    ctrl["fechas_invalidas"] = ctrl.get("fechas_invalidas", 0) + int(fecha.isna().sum())
    dias = (fecha.fillna(pd.Timestamp("1970-01-01")).astype("int64")
            // 86_400_000_000_000).to_numpy().astype(np.int32)

    # --- duplicados por (fecha, desde, molinete) sin guardar el frame -------
    hh_raw = pd.to_numeric(chunk["desde"].str.slice(0, 2), errors="coerce")
    mm_raw = pd.to_numeric(chunk["desde"].str.slice(3, 5), errors="coerce")
    ctrl["desde_invalidos"] = ctrl.get("desde_invalidos", 0) + int(
        (hh_raw.isna() | mm_raw.isna()).sum())
    hh = hh_raw.fillna(0).astype(np.int16)
    mm = mm_raw.fillna(0).astype(np.int16)
    minutos = (hh * 60 + mm).to_numpy().astype(np.int32)
    valida = (~fecha.isna()).to_numpy()          # filas basura: sin fecha ni total
    if valida.any():
        cod = np.empty(len(chunk), dtype=np.int32)
        for m in chunk["molinete"].unique():
            if m not in molinete_code:
                molinete_code[m] = len(molinete_code)
        cod[:] = chunk["molinete"].map(molinete_code).to_numpy()
        h = (dias[valida].astype(np.uint64) << 40) | \
            (minutos[valida].astype(np.uint64) << 20) | cod[valida].astype(np.uint64)
        hashes.append(h)

    # --- (a) demanda diaria total ----------------------------------------
    tmp = pd.DataFrame({"fecha": fecha, "total": tot.to_numpy()})
    acum_dia.append(tmp.groupby("fecha", as_index=False)["total"].sum())

    # --- (b) estación x hora, solo días hábiles ---------------------------
    es_hab = np.isin(fecha.astype("int64").to_numpy(), np.fromiter(habiles, dtype=np.int64))
    if es_hab.any():
        sub = chunk.loc[es_hab]
        sub_tot = tot.to_numpy()[es_hab]
        horas = (hh.to_numpy()[es_hab] * 60 + mm.to_numpy()[es_hab]) // 60
        acum_eh.append(pd.DataFrame({"fecha": fecha.to_numpy()[es_hab],
                                     "linea": sub["linea"].to_numpy(),
                                     "estacion": sub["estacion"].to_numpy(),
                                     "hora": horas.astype(np.int8),
                                     "total": sub_tot}))
    # nombres crudos distintos (para la tabla de equivalencias)
    par = chunk[["linea", "estacion"]].drop_duplicates()
    pares_raw.update(zip(par["linea"].tolist(), par["estacion"].tolist()))


for archivo in ["historico_2018.csv", "historico_2019.csv"]:
    t0 = time.time()
    n = 0
    for ch in pd.read_csv(DSETS / archivo, usecols=USECOLS, dtype=DTYPES,
                          chunksize=CHUNK, low_memory=False):
        procesar(ch)
        n += len(ch)
    print(f"{archivo}: {n:,} filas leídas en {time.time()-t0:.0f}s")

# --------------------------------------------------------------- controles --
todos = np.concatenate(hashes)
_, counts = np.unique(todos, return_counts=True)
ctrl["filas_duplicadas"] = int((counts[counts > 1] - 1).sum())
ctrl["grupos_duplicados"] = int((counts > 1).sum())
print(f"controles: {ctrl}")

dem_total = pd.concat(acum_dia).groupby("fecha", as_index=False)["total"].sum()
dem_total = dem_total.sort_values("fecha")

# ------------------------------------------------- (a) vs CSV de demanda ---
csv = pd.read_csv("recursos/demanda_diaria_subte_2018_2021.csv", parse_dates=["fecha"])
csv_1819 = csv[csv["fecha"].dt.year.isin([2018, 2019])].copy()
cmp = pd.merge(csv_1819, dem_total, on="fecha", how="outer", suffixes=("_csv", "_mol"))
cmp["dif"] = cmp["demanda_pasajeros"] - cmp["total"]
solo_csv = int(cmp["total"].isna().sum())
solo_mol = int(cmp["demanda_pasajeros"].isna().sum())
comparables = cmp.dropna(subset=["dif"])
dif_max = float(comparables["dif"].abs().max())
n_distintos = int((comparables["dif"].abs() > 0.5).sum())
print(f"\n(a) 2018-2019: {len(comparables)} días comparables | "
      f"dif. máx. {dif_max:,.1f} | días distintos {n_distintos} | "
      f"solo en CSV {solo_csv} | solo en molinetes {solo_mol}")
guardar_tabla(comparables.sort_values("fecha").assign(
    fecha=lambda d: d["fecha"].dt.strftime("%Y-%m-%d")).round(1),
    "t03_comparacion_diaria_2018_2019")
veredicto = "coincide" if (dif_max <= 0.5 and n_distintos == 0 and solo_csv == 0 and solo_mol == 0) \
    else "difiere -> usar versión recalculada"
print(f"veredicto (a): {veredicto}")

# ------------------------------------------------- (b) estación x hora ------
eh = pd.concat(acum_eh, ignore_index=True)
# normalización de nombres de estación y línea (repara también el mojibake)
eh["linea"] = eh["linea"].map(norm_linea)
eh["estacion"] = eh["estacion"].map(norm_estacion)
eh = eh.groupby(["fecha", "linea", "estacion", "hora"], as_index=False)["total"].sum()
eh["fecha"] = pd.to_datetime(eh["fecha"])
eh = eh.sort_values(["estacion", "fecha", "hora"])
eh.to_parquet("recursos/demanda_estacion_hora_2018_2019.parquet", index=False)
print(f"\n(b) demanda_estacion_hora_2018_2019.parquet: {eh.shape} | "
      f"{eh['estacion'].nunique()} estaciones | {eh['fecha'].nunique()} días hábiles")

# equivalencias de nombres de estación
pares_ok = {(str(a), str(c)) for a, c in pares_raw
            if isinstance(a, str) and isinstance(c, str)}
raw = pd.DataFrame(sorted(pares_ok), columns=["linea_raw", "estacion_raw"])
raw["linea_norm"] = raw["linea_raw"].map(norm_linea)
raw["estacion_norm"] = raw["estacion_raw"].map(norm_estacion)
equiv = raw.groupby("estacion_norm").agg(
    variantes=("estacion_raw", lambda s: " | ".join(sorted(set(s)))),
    n_variantes=("estacion_raw", lambda s: len(set(s))),
    lineas=("linea_norm", lambda s: "/".join(sorted(set(s))))).reset_index()
equiv = equiv[equiv["n_variantes"] > 1].sort_values("estacion_norm")
print(f"(b) estaciones con más de un nombre crudo: {len(equiv)}")
guardar_tabla(equiv, "t03_equivalencias_estaciones")
guardar_tabla(pd.DataFrame([ctrl]).T.reset_index().rename(columns={"index": "control", 0: "valor"}),
              "t03_controles_molinetes")

# ------------------------------------- (c) verificación 2020 y 2021 (awk) --
def verificar(archivo: str, dia: int, mes: int, anio: int, sep: str,
              col_fecha: int, col_total: int) -> tuple[float, int]:
    """Suma el total de un día con awk, sin cargar el archivo en memoria."""
    prog = ("NR>1 { split($%d,p,\"/\"); if (p[1]+0==%d && p[2]+0==%d && p[3]+0==%d)"
            " { s+=$%d; n++ } } END { printf \"%%.0f %%d\", s, n }"
            % (col_fecha, dia, mes, anio, col_total))
    cmd = ["awk", "-F" + sep, prog, str(DSETS / archivo)]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    s, n = out.stdout.split()
    return float(s), int(n)


clima = pd.read_parquet("recursos/base_analitica.parquet", columns=["fecha", "es_dia_habil",
                                                                    "demanda_pasajeros"])
verif = []
for anio, archivo, sep, cf, ct in [
        (2020, "historico_2020.csv", ",", 1, 10),
        (2021, "historico_2021.csv", ";", 2, 11)]:
    d = clima[(clima["fecha"].dt.year == anio) & (clima["es_dia_habil"] == 1)].iloc[0]
    suma, nfilas = verificar(archivo, d["fecha"].day, d["fecha"].month, anio, sep, cf, ct)
    csv_val = float(d["demanda_pasajeros"])
    verif.append({"anio": anio, "fecha": d["fecha"].strftime("%Y-%m-%d"),
                  "suma_molinetes": suma, "csv_demanda": csv_val,
                  "diferencia": suma - csv_val, "filas": nfilas,
                  "coincide": "sí" if abs(suma - csv_val) < 0.5 else "no"})
    print(f"(c) {anio} {d['fecha'].date()}: molinetes {suma:,.0f} vs CSV {csv_val:,.0f} "
          f"-> {'coincide' if abs(suma-csv_val) < 0.5 else 'NO coincide'} ({nfilas} filas)")
guardar_tabla(pd.DataFrame(verif), "t03_verificacion_2020_2021")

print("\nOK 03")
