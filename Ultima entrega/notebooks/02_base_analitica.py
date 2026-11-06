#!/usr/bin/env python3
"""02 - Base analítica: clima + demanda, fases COVID y días atípicos.

Salida: recursos/base_analitica.parquet (1.425 filas) y tablas de control.
"""
from __future__ import annotations

import holidays
import numpy as np
import pandas as pd
from statsmodels.api import OLS, add_constant

from comun import DIAS, MESES, guardar_tabla

# ----------------------------------------------------------------- carga ---
clima = pd.read_csv("recursos/clima_diario_caba_2018_2021_consolidado.csv")
clima["fecha"] = pd.to_datetime(clima["fecha"])
dem = pd.read_csv("recursos/demanda_diaria_subte_2018_2021.csv")
dem["fecha"] = pd.to_datetime(dem["fecha"])

print(f"clima: {clima.shape}  demanda: {dem.shape}")

# ------------------------------------------------- días sin demanda (36) ---
faltantes = clima.loc[~clima["fecha"].isin(dem["fecha"]), ["fecha"]].copy()
faltantes["dia_semana"] = [DIAS[d] for d in faltantes["fecha"].dt.weekday]
faltantes["anio"] = faltantes["fecha"].dt.year
faltantes["mes"] = [MESES[m] for m in faltantes["fecha"].dt.month]
faltantes = faltantes.sort_values("fecha").reset_index(drop=True)
print(f"días sin demanda: {len(faltantes)}")
guardar_tabla(faltantes, "t01_dias_sin_demanda")

# ¿se concentran en algún período?
aspo_ini, aspo_fin = pd.Timestamp("2020-03-20"), pd.Timestamp("2020-11-08")
en_aspo = faltantes["fecha"].between(aspo_ini, aspo_fin)
print(f"  dentro del ASPO (20/03-08/11/2020): {en_aspo.sum()} de {len(faltantes)}")
print(faltantes.groupby(["anio", "mes"]).size().to_string())

# --------------------------------------------------------------- unión -----
base = pd.merge(clima, dem, on="fecha", how="inner").sort_values("fecha")
assert len(base) == 1425, len(base)

# CONTROL DE CALIDAD: el CSV de clima trae es_feriado = 0 en los 1.461 días
# (bug de isin() en el notebook 00). Reconstruimos feriado y día hábil con la
# misma fuente que pretendía usar el 00: calendario holidays.Argentina.
feriados = holidays.Argentina(years=range(2018, 2022))
base["es_feriado_clima"] = base["es_feriado"]           # tal cual viene (todo 0)
base["es_feriado"] = base["fecha"].dt.date.isin(feriados).astype(int)
base["es_fin_de_semana"] = base["fecha"].dt.weekday.isin([5, 6]).astype(int)
base["es_dia_habil"] = ((base["es_fin_de_semana"] == 0) &
                        (base["es_feriado"] == 0)).astype(int)
print(f"es_feriado en el CSV de clima: {int(base['es_feriado_clima'].sum())} (defectuoso)")
print(f"feriados reconstruidos: {int(base['es_feriado'].sum())}; "
      f"días hábiles: {int(base['es_dia_habil'].sum())}")

# ------------------------------------------------------- fases COVID -------
def fase(f):
    if f <= pd.Timestamp("2020-03-19"):
        return "pre"
    if f <= pd.Timestamp("2020-11-08"):
        return "ASPO"
    if f <= pd.Timestamp("2020-12-31"):
        return "DISPO"
    return "2021"


base["fase"] = base["fecha"].apply(fase)
base["anio_mes"] = base["fecha"].dt.strftime("%Y-%m")
base["anio"] = base["fecha"].dt.year
base["mes"] = base["fecha"].dt.month
base["log_demanda"] = np.log(base["demanda_pasajeros"])

# dummies de día de semana (Lunes = base)
dias = pd.get_dummies(base["fecha"].dt.weekday, dtype=int)
dias.columns = [f"dia_{DIAS[i].lower()}" for i in range(7)]
base = pd.concat([base, dias], axis=1)

# ------------------------------------------------- días atípicos ------------
# residuo de un modelo de calendario: año-mes + día de semana + feriado + fase
hab = base[base["es_dia_habil"] == 1].copy()
X = pd.concat([
    pd.get_dummies(hab["anio_mes"], prefix="am", dtype=int),
    pd.get_dummies(hab["fecha"].dt.weekday, prefix="ds", dtype=int),
    hab[["es_feriado"]].astype(float),
    pd.get_dummies(hab["fase"], prefix="fase", dtype=int).drop(columns=["fase_pre"]),
], axis=1).astype(float)
X = add_constant(X, has_constant="add")
res = OLS(hab["demanda_pasajeros"].astype(float), X).fit().resid
mad = np.median(np.abs(res - res.median()))
escala = 1.4826 * mad
z = (res - res.median()) / escala
hab["residuo_calendario"] = res
hab["z_robusto"] = z
atipicos = hab.loc[z < -3, ["fecha", "demanda_pasajeros", "residuo_calendario", "z_robusto"]]
atipicos = atipicos.sort_values("z_robusto")
atipicos["dia_semana"] = [DIAS[d] for d in atipicos["fecha"].dt.weekday]
atipicos["fase"] = atipicos["fecha"].map(base.set_index("fecha")["fase"])
print(f"\ndías atípicos (z_robusto < -3) sobre {len(hab)} días hábiles: {len(atipicos)}")
print(atipicos[["fecha", "demanda_pasajeros", "z_robusto"]].to_string(index=False))
guardar_tabla(atipicos.reset_index(drop=True), "t02_dias_atipicos")

base["dia_atipico"] = base["fecha"].isin(atipicos["fecha"]).astype(int)
print(f"dia_atipico=1 en {base['dia_atipico'].sum()} días")

# -------------------------------------------------------------- salida -----
base = base.sort_values("fecha").reset_index(drop=True)
base.to_parquet("recursos/base_analitica.parquet", index=False)
print(f"\nbase_analitica.parquet: {base.shape}")
print(f"fases: {base['fase'].value_counts().to_dict()}")
print("OK 02")
