#!/usr/bin/env python3
"""04 - Análisis exploratorio breve: demanda, clima, fuentes y confusión estacional."""
from __future__ import annotations

import numpy as np
import pandas as pd

from comun import guardar_tabla

b = pd.read_parquet("recursos/base_analitica.parquet")

DEMANDA = "demanda_pasajeros"

# --------------------------------------------- 1. demanda descriptiva ------
def resumen(df: pd.DataFrame, col: str = DEMANDA) -> dict:
    s = df[col]
    return {"n": len(s), "media": s.mean(), "mediana": s.median(), "sd": s.std(),
            "min": s.min(), "p25": s.quantile(.25), "p75": s.quantile(.75),
            "max": s.max()}


por_anio = b.groupby("anio").apply(lambda g: pd.Series(resumen(g)))
por_anio.insert(0, "grupo", por_anio.index.astype(str))
guardar_tabla(por_anio.round(0).reset_index(drop=True), "t04_demanda_por_anio")

por_fase = b.groupby("fase").apply(lambda g: pd.Series(resumen(g)))
por_fase.insert(0, "grupo", por_fase.index)
guardar_tabla(por_fase.round(0).reset_index(drop=True), "t04_demanda_por_fase")

b["tipo_dia"] = np.where(b["es_dia_habil"] == 1, "hábil",
                        np.where(b["es_fin_de_semana"] == 1, "fin de semana", "feriado"))
por_tipo = b.groupby("tipo_dia").apply(lambda g: pd.Series(resumen(g)))
por_tipo.insert(0, "grupo", por_tipo.index)
guardar_tabla(por_tipo.round(0).reset_index(drop=True), "t04_demanda_por_tipo_dia")

# ------------------------------------------------------------- 2. clima ----
clima_cols = ["temperatura_media_c", "temperatura_max_c", "temperatura_min_c",
              "precipitacion_mm"]
clima_res = b[clima_cols].agg(["count", "mean", "std", "min", "median", "max"]).T
clima_res = clima_res.reset_index().rename(columns={"index": "variable"})
guardar_tabla(clima_res.round(2), "t04_clima_resumen")

bins = [-np.inf, 0.1, 5, 20, np.inf]
etiquetas = ["seco (<0,1 mm)", "leve (0,1-5 mm)", "moderada (5-20 mm)", "fuerte (>=20 mm)"]
b["intensidad_lluvia"] = pd.cut(b["precipitacion_mm"], bins=bins, labels=etiquetas,
                                right=False)
inten = (b.groupby(["intensidad_lluvia"], observed=False)
          .agg(dias=("fecha", "size"), pct=("fecha", lambda s: 100 * len(s) / len(b)))
          .reset_index())
inten_anio = (b.groupby(["anio", "intensidad_lluvia"], observed=False)
              .agg(dias=("fecha", "size")).reset_index())
guardar_tabla(inten.round(2), "t04_dias_por_intensidad_lluvia")
guardar_tabla(inten_anio, "t04_dias_por_intensidad_lluvia_anio")

# ----------------------------------- 3. validación de fuentes ERA5 vs SABA --
par = b[["temp_media_c_era5", "temp_media_c_saba"]].dropna()
n_saba_falt = int(b["temp_media_c_saba"].isna().sum())
valid = pd.DataFrame([{
    "serie": "temperatura media diaria (ERA5 vs SABA Aeroparque)",
    "n_pares_completos": len(par),
    "correlacion_pearson": par["temp_media_c_era5"].corr(par["temp_media_c_saba"]),
    "faltantes_saba": n_saba_falt,
    "pct_faltantes_saba": 100 * n_saba_falt / len(b),
    "sesgo_era5_menos_saba": (par["temp_media_c_era5"] - par["temp_media_c_saba"]).mean(),
}])
guardar_tabla(valid.round(4), "t04_validacion_fuentes")

# ------------------ 4. temperatura-demanda con y sin control de mes --------
pre_hab = b[(b["fase"] == "pre") & (b["es_dia_habil"] == 1)].copy()
print(f"días hábiles pre-pandemia: {len(pre_hab)}")

for v in ["temperatura_media_c", DEMANDA]:
    g = pre_hab.groupby("anio_mes")[v]
    pre_hab[f"{v}_resid"] = pre_hab[v] - g.transform("mean")

cruda = pre_hab["temperatura_media_c"].corr(pre_hab[DEMANDA])
resid = pre_hab["temperatura_media_c_resid"].corr(pre_hab[f"{DEMANDA}_resid"])
# control adicional: además del mes, día de semana
X = pd.concat([pd.get_dummies(pre_hab["anio_mes"], dtype=int),
               pd.get_dummies(pre_hab["fecha"].dt.weekday, dtype=int)], axis=1).astype(float)
resid_ds = {}
for v in ["temperatura_media_c", DEMANDA]:
    r = pre_hab[v] - X.mul(np.linalg.lstsq(X.to_numpy(), pre_hab[v].to_numpy(),
                                           rcond=None)[0], axis=1).sum(axis=1)
    resid_ds[v] = r
resid_ds_corr = pd.DataFrame(resid_ds).corr().iloc[0, 1]

tabla_corr = pd.DataFrame([
    {"especificacion": "cruda (días hábiles pre-pandemia)", "n": len(pre_hab),
     "correlacion_temp_demanda": cruda},
    {"especificacion": "residualizada por año-mes (efectos fijos de mes)", "n": len(pre_hab),
     "correlacion_temp_demanda": resid},
    {"especificacion": "residualizada por año-mes + día de la semana", "n": len(pre_hab),
     "correlacion_temp_demanda": resid_ds_corr},
])
guardar_tabla(tabla_corr.round(4), "t04_correlacion_temp_demanda")

print(f"correlación cruda: {cruda:.4f} | residualizada por año-mes: {resid:.4f} "
      f"| + día de semana: {resid_ds_corr:.4f}")
print("OK 04")
