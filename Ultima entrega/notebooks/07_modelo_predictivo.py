#!/usr/bin/env python3
"""07 - Componente predictivo: comparación de algoritmos (train 2018, test 2019).

Calendario: día de semana, feriado, mes y dia_atipico.
Clima: temperatura media/máxima/mínima, precipitación y lluvia >= 5 mm.
Búsqueda chica de hiperparámetros con TimeSeriesSplit(3) solo dentro de 2018.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from comun import SEED, guardar_tabla

Y = "demanda_pasajeros"
b = pd.read_parquet("recursos/base_analitica.parquet")
b = b.sort_values("fecha").reset_index(drop=True)

CAL = ["dia_lunes", "dia_martes", "dia_miércoles", "dia_jueves", "dia_viernes",
       "dia_sábado", "es_feriado", "mes", "dia_atipico"]
CLI = ["temperatura_media_c", "temperatura_max_c", "temperatura_min_c",
       "precipitacion_mm", "lluvia_significativa_5mm"]

ent = b[b["anio"] == 2018].copy()
pru = b[b["anio"] == 2019].copy()
print(f"train 2018: {len(ent)} días | test 2019: {len(pru)} días")

Xe, ye = ent[CAL + CLI], ent[Y]
Xp, yp = pru[CAL + CLI], pru[Y]


# ------------------------------------------------------------- ingenuo -----
def ingenuo(df: pd.DataFrame) -> np.ndarray:
    """Mismo día de la semana de la semana anterior (shift de 7 días)."""
    serie = b.set_index("fecha")[Y]
    idx = df["fecha"] - pd.Timedelta(days=7)
    return serie.reindex(idx).to_numpy()


# ------------------------------------------- búsqueda de hiperparámetros ----
tscv = TimeSeriesSplit(n_splits=3)


def buscar(modelo, params, X, y):
    gs = GridSearchCV(modelo, params, cv=tscv, scoring="neg_root_mean_squared_error",
                      n_jobs=1)
    gs.fit(X, y)
    return gs.best_params_, -gs.best_score_


rf = RandomForestRegressor(random_state=SEED, n_jobs=1)
params_rf = {"n_estimators": [200], "max_depth": [8, 12, None],
             "min_samples_leaf": [1, 5]}
best_rf, score_rf = buscar(rf, params_rf, Xe, ye)
print(f"RF mejores hiperparámetros: {best_rf} | RMSE CV(2018) = {score_rf:,.0f}")

hgb = HistGradientBoostingRegressor(random_state=SEED)
params_hgb = {"max_iter": [200, 400], "learning_rate": [0.1, 0.05],
              "max_leaf_nodes": [15, 31]}
best_hgb, score_hgb = buscar(hgb, params_hgb, Xe, ye)
print(f"HGB mejores hiperparámetros: {best_hgb} | RMSE CV(2018) = {score_hgb:,.0f}")

# ------------------------------------------------------------ modelos -------
modelos = {}
modelos["1_ingenuo_semana_anterior"] = None
modelos["2_regresion_calendario"] = make_pipeline(StandardScaler(),
                                                  LinearRegression())
modelos["3_regresion_calendario_clima"] = make_pipeline(StandardScaler(),
                                                        LinearRegression())
modelos["4_random_forest"] = RandomForestRegressor(**best_rf, random_state=SEED,
                                                    n_jobs=-1)
modelos["5_hist_gradient_boosting"] = HistGradientBoostingRegressor(**best_hgb,
                                                                    random_state=SEED)

Xe_cal, Xp_cal = ent[CAL], pru[CAL]
preds, metricas = {}, []
for nombre, mod in modelos.items():
    if mod is None:
        p = ingenuo(pru)
        p_ent = ingenuo(ent)
    else:
        con_clima = nombre in ("3_regresion_calendario_clima",
                               "4_random_forest", "5_hist_gradient_boosting")
        cols = CAL + CLI if con_clima else CAL
        mod.fit(ent[cols], ye)
        p = mod.predict(pru[cols])
        p_ent = mod.predict(ent[cols])
    preds[nombre] = p
    m = np.isfinite(p)
    rmse = float(np.sqrt(mean_squared_error(yp[m], p[m])))
    mae = float(mean_absolute_error(yp[m], p[m]))
    mape = float(np.mean(np.abs((yp[m] - p[m]) / yp[m])) * 100)
    r2 = float(r2_score(yp[m], p[m]))
    me = np.isfinite(p_ent)
    rmse_ent = float(np.sqrt(mean_squared_error(ye[me], p_ent[me])))
    metricas.append({"modelo": nombre, "n_test_2019": int(m.sum()),
                     "rmse_2019": rmse, "mae_2019": mae,
                     "mape_2019": mape, "r2_2019": r2, "rmse_2018": rmse_ent})
    print(f"{nombre}: RMSE {rmse:,.0f} | MAE {mae:,.0f} | MAPE {mape:.2f}% | "
          f"R2 {r2:.4f}")

met = pd.DataFrame(metricas)
met["delta_rmse_vs_modelo2"] = met["rmse_2019"] - float(
    met.loc[met["modelo"] == "2_regresion_calendario", "rmse_2019"].iloc[0])
guardar_tabla(met.round(4), "t07_metricas")

aporte = float(met.loc[met["modelo"] == "2_regresion_calendario", "rmse_2019"].iloc[0]) - \
    float(met.loc[met["modelo"] == "3_regresion_calendario_clima", "rmse_2019"].iloc[0])
print(f"aporte del clima (RMSE modelo 2 - modelo 3): {aporte:,.0f}")

# ------------------------------------ importancia por permutación (mejor árbol)
mejor_nombre = "5_hist_gradient_boosting" if float(
    met.loc[met["modelo"] == "5_hist_gradient_boosting", "rmse_2019"].iloc[0]) <= \
    float(met.loc[met["modelo"] == "4_random_forest", "rmse_2019"].iloc[0]) \
    else "4_random_forest"
mod_mejor = modelos[mejor_nombre]
imp = permutation_importance(mod_mejor, Xp, yp, n_repeats=10, random_state=SEED,
                             scoring="neg_root_mean_squared_error")
imp_tab = pd.DataFrame({"variable": Xp.columns,
                        "importancia": imp.importances_mean,
                        "importancia_sd": imp.importances_std}).sort_values(
    "importancia", ascending=False)
imp_tab.insert(0, "modelo", mejor_nombre)
guardar_tabla(imp_tab.round(4), "t07_importancia_permutacion")
print("\nimportancia por permutación:")
print(imp_tab.round(3).to_string(index=False))

# ----------------------------------------------------------- predicciones ---
out = pd.DataFrame({"fecha": pru["fecha"], "real": yp})
for k, v in preds.items():
    out[k] = v
out.to_csv("Ultima entrega/resultados/artefactos/predicciones_2019.csv",
           index=False, encoding="utf-8")
print("\nOK 07")
