#!/usr/bin/env python3
"""05 - Hipótesis H1 (sensibilidad térmica), H2 (efecto refugio) y robustez de tarifa.

Salidas: tablas t05_*.csv y artefactos para las figuras.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson

from comun import DIAS, SEED, guardar_tabla

b = pd.read_parquet("recursos/base_analitica.parquet")
Y = "demanda_pasajeros"

# es_dia_habil tal como lo calculó el notebook 01 (bug de feriados incluido)
b["es_dia_habil_nb"] = (b["es_fin_de_semana"] == 0).astype(int)


# ------------------------------------------------------------- helpers -----
def dummies(df: pd.DataFrame, col: str, prefijo: str, base=None) -> pd.DataFrame:
    d = pd.get_dummies(df[col], prefix=prefijo, dtype=float)
    if base is not None:
        colbase = f"{prefijo}_{base}"
        if colbase in d.columns:
            d = d.drop(columns=[colbase])
    return d


def matriz(df: pd.DataFrame, clima: list[str], anio_mes: bool = True,
           fase: bool = True, dia_atipico: bool = True,
           feriado: bool = True) -> pd.DataFrame:
    partes = [df[clima].astype(float),
              dummies(df, "fecha_dow", "ds", base=0),      # Lunes = base
              ]
    if feriado:
        partes.append(df[["es_feriado"]].astype(float))
    if anio_mes:
        base_am = sorted(df["anio_mes"].unique())[0]
        partes.append(dummies(df, "anio_mes", "am", base=base_am))
    if fase:
        partes.append(dummies(df, "fase", "fase", base="pre"))
    if dia_atipico:
        partes.append(df[["dia_atipico"]].astype(float))
    X = pd.concat(partes, axis=1).astype(float)
    return sm.add_constant(X, has_constant="add")


def ajustar(df: pd.DataFrame, X: pd.DataFrame, y: pd.Series,
            hac: int | None = 7):
    m = sm.OLS(y.astype(float), X).fit()
    mh = m.get_robustcov_results(cov_type="HAC", maxlags=hac) if hac else None
    return m, mh


def diag(X: pd.DataFrame, m) -> dict:
    vif = [variance_inflation_factor(X.to_numpy(), i) for i in range(X.shape[1])]
    vif_s = pd.Series(vif, index=X.columns)
    bp = het_breuschpagan(m.resid, X.to_numpy())
    return {"vif_temp_max": float(vif_s.loc[[c for c in X.columns
                                             if c.startswith("temperatura")][0]]),
            "vif_lluvia": float(vif_s.loc[[c for c in X.columns
                                           if c.startswith("lluvia")][0]]) if any(
                c.startswith("lluvia") for c in X.columns) else np.nan,
            "durbin_watson": float(durbin_watson(m.resid)),
            "bp_pvalor": float(bp[1])}


def p_unilateral_t(t: float, df: float) -> float:
    """p para H0: beta >= 0 vs H1: beta < 0."""
    return float(stats.t.cdf(t, df))


b["fecha_dow"] = b["fecha"].dt.weekday

# =========================================================== H1: modelos ===
CLIMA_BASE = ["temperatura_media_c", "lluvia_significativa_5mm"]

specs = {}
ajustes = {}

# M0 - especificación del notebook 01 (réplica)
X0 = sm.add_constant(b[["temperatura_media_c", "es_dia_habil_nb",
                        "lluvia_significativa_5mm", "es_covid_aspo"]].astype(float),
                     has_constant="add")
specs["M0"] = (b, X0, b[Y])

# M1 - principal
X1 = matriz(b, CLIMA_BASE)
specs["M1"] = (b, X1, b[Y])

# M2 - M1 en log
specs["M2"] = (b, X1, b["log_demanda"])

# M3 - M1 con precipitación continua
X3 = matriz(b, ["temperatura_media_c", "precipitacion_mm"])
specs["M3"] = (b, X3, b[Y])

# M4 - M1 sin dia_atipico
X4 = matriz(b, CLIMA_BASE, dia_atipico=False)
specs["M4"] = (b, X4, b[Y])

# M5 - M1 solo 2018-2019
m1819 = b[b["anio"].isin([2018, 2019])].copy()
X5 = matriz(m1819, CLIMA_BASE)
specs["M5"] = (m1819, X5, m1819[Y])

filas = []
for nombre, (df, X, y) in specs.items():
    m, mh = ajustar(df, X, y)
    d = diag(X, m)
    beta_t = float(m.params["temperatura_media_c"])
    beta_l = float(m.params.get("lluvia_significativa_5mm",
                                m.params.get("precipitacion_mm", np.nan)))
    p_t = float(mh.pvalues[list(X.columns).index("temperatura_media_c")])
    lcol = "lluvia_significativa_5mm" if "lluvia_significativa_5mm" in X.columns \
        else "precipitacion_mm"
    p_l = float(mh.pvalues[list(X.columns).index(lcol)])
    ic = mh.conf_int()
    it, il = list(X.columns).index("temperatura_media_c"), list(X.columns).index(lcol)
    filas.append({"modelo": nombre, "n": int(m.nobs), "r2": m.rsquared,
                  "r2_ajustado": m.rsquared_adj, "beta_temp": beta_t,
                  "ic_temp_bajo": float(ic[it][0]), "ic_temp_alto": float(ic[it][1]),
                  "p_temp_hac": p_t, "t_temp_ols": float(m.tvalues["temperatura_media_c"]),
                  "p_temp_ols": float(m.pvalues["temperatura_media_c"]),
                  "beta_lluvia": beta_l, "p_lluvia_hac": p_l,
                  "ic_lluvia_bajo": float(ic[il][0]), "ic_lluvia_alto": float(ic[il][1]),
                  **d})
    ajustes[nombre] = (m, mh, X, y, df)

esp = pd.DataFrame(filas)
guardar_tabla(esp.round(6), "t05_especificaciones")

# ---- resultado puntual de H1 sobre M1 -------------------------------------
m1, mh1, X1m, y1, df1 = ajustes["M1"] and ajustes["M1"][0], None, None, None, None
m1, mh1, X1m, y1, df1 = ajustes["M1"]
idx_t = list(X1m.columns).index("temperatura_media_c")
beta = float(m1.params["temperatura_media_c"])
se = float(mh1.bse[idx_t])
t = float(mh1.tvalues[idx_t])
p1 = p_unilateral_t(t, mh1.df_resid)
ic_lo, ic_hi = float(mh1.conf_int()[idx_t][0]), float(mh1.conf_int()[idx_t][1])
media = float(b[Y].mean())
h1 = pd.DataFrame([{
    "coeficiente_beta_temp": beta, "error_estandar_hac": se, "t": t,
    "p_unilateral_H1_beta_menor_0": p1, "ic95_bajo": ic_lo, "ic95_alto": ic_hi,
    "pasajeros_por_grado": beta, "pct_demanda_media": 100 * beta / media,
    "demanda_media": media, "n": int(m1.nobs),
}])
guardar_tabla(h1.round(6), "t05_h1_sensibilidad_termica")
print("H1:", h1.round(4).to_dict("records")[0])

# ------------------------------------------------- sensibilidad no lineal ---
bins = [-np.inf, 10, 15, 20, 25, 30, np.inf]
etiq = ["<10", "10-15", "15-20", "20-25", "25-30", ">=30"]
b["t_bin"] = pd.cut(b["temperatura_media_c"], bins=bins, labels=etiq, right=False)
Xb = pd.concat([pd.get_dummies(b["t_bin"], prefix="t", dtype=float).drop(columns=["t_15-20"]),
                X1m.drop(columns=["temperatura_media_c"])], axis=1)
mb, mhb = ajustar(b, Xb, b[Y])
filas_b = []
for c in [c for c in Xb.columns if c.startswith("t_")]:
    i = list(Xb.columns).index(c)
    filas_b.append({"bin_temperatura": c[2:], "beta_vs_15_20": float(mb.params[c]),
                    "p_hac": float(mhb.pvalues[i]),
                    "ic95_bajo": float(mhb.conf_int()[i][0]),
                    "ic95_alto": float(mhb.conf_int()[i][1]),
                    "n": int(mb.nobs), "r2": mb.rsquared})
bins_tab = pd.DataFrame(filas_b)
guardar_tabla(bins_tab.round(4), "t05_temp_bins")

# ------------------------------------------------------------- artefactos ---
pd.DataFrame({"fecha": b["fecha"], "y": b[Y], "ajustado": m1.fittedvalues,
              "residuo": m1.resid}).to_parquet(
    "Ultima entrega/resultados/artefactos/m1_ajuste.parquet", index=False)

# =================================================================== H2 ====
sub = b[(b["es_dia_habil"] == 1) & (b["anio"].isin([2018, 2019])) &
        (b["es_feriado"] == 0) & (b["dia_atipico"] == 0)].copy()
sub["grupo"] = np.where(sub["precipitacion_mm"] < 0.1, "seco",
                        np.where(sub["lluvia_significativa_5mm"] == 1, "lluvia>=5mm",
                                 "excluido"))
muestra = sub[sub["grupo"] != "excluido"].copy()
print(f"H2 muestra: {len(muestra)} días "
      f"(seco {int((muestra.grupo=='seco').sum())}, "
      f"lluvia {int((muestra.grupo=='lluvia>=5mm').sum())})")


def cohen_d(a: np.ndarray, bb: np.ndarray) -> float:
    n1, n2 = len(a), len(bb)
    sp = np.sqrt(((n1 - 1) * a.std(ddof=1) ** 2 + (n2 - 1) * bb.std(ddof=1) ** 2)
                 / (n1 + n2 - 2))
    return float((a.mean() - bb.mean()) / sp)


def bootstrap_d(a: np.ndarray, bb: np.ndarray, reps: int = 2000) -> tuple[float, float]:
    rng = np.random.default_rng(SEED)
    ds = np.empty(reps)
    for i in range(reps):
        aa = rng.choice(a, len(a), replace=True)
        bbb = rng.choice(bb, len(bb), replace=True)
        ds[i] = cohen_d(aa, bbb)
    return float(np.percentile(ds, 2.5)), float(np.percentile(ds, 97.5))


def contraste(df: pd.DataFrame, valor: str, etiqueta: str) -> dict:
    seco = df.loc[df["grupo"] == "seco", valor].to_numpy()
    llu = df.loc[df["grupo"] == "lluvia>=5mm", valor].to_numpy()
    t, p2 = stats.ttest_ind(llu, seco, equal_var=False)
    p1 = float(stats.ttest_ind(llu, seco, equal_var=False, alternative="greater").pvalue)
    dif = llu.mean() - seco.mean()
    # IC 95 % de la diferencia (Welch)
    se_dif = np.sqrt(llu.var(ddof=1) / len(llu) + seco.var(ddof=1) / len(seco))
    dfw = (llu.var(ddof=1) / len(llu) + seco.var(ddof=1) / len(seco)) ** 2 / (
        (llu.var(ddof=1) / len(llu)) ** 2 / (len(llu) - 1) +
        (seco.var(ddof=1) / len(seco)) ** 2 / (len(seco) - 1))
    tcrit = stats.t.ppf(0.975, dfw)
    d = cohen_d(llu, seco)
    dlo, dhi = bootstrap_d(llu, seco)
    u, pmw = stats.mannwhitneyu(llu, seco, alternative="greater")
    return {"analisis": etiqueta, "n_seco": len(seco), "n_lluvia": len(llu),
            "media_seco": seco.mean(), "media_lluvia": llu.mean(),
            "diferencia": dif, "t_welch": float(t), "p_welch_unilateral": p1,
            "p_welch_bilateral": float(p2), "ic95_dif_bajo": dif - tcrit * se_dif,
            "ic95_dif_alto": dif + tcrit * se_dif,
            "mannwhitney_U": float(u), "p_mannwhitney_unilateral": float(pmw),
            "cohen_d": d, "d_ic95_bajo": dlo, "d_ic95_alto": dhi}


h2 = pd.DataFrame([contraste(muestra, Y, "demanda cruda (H2 principal)")])
guardar_tabla(h2.round(6), "t05_h2_contraste")
print("H2 crudo:", h2[["cohen_d", "p_welch_unilateral", "p_mannwhitney_unilateral"]].to_dict("records"))

# --- robustez: residuos del modelo de calendario ---------------------------
am_c = pd.get_dummies(muestra["anio_mes"], prefix="am", dtype=float)
ds_c = pd.get_dummies(muestra["fecha"].dt.weekday, prefix="ds", dtype=float)
Xc = pd.concat([am_c.drop(columns=[am_c.columns[0]]),
                ds_c.drop(columns=["ds_0"]),
                muestra[["es_feriado"]].astype(float),
                pd.get_dummies(muestra["fase"], prefix="fase", dtype=float)
                .drop(columns=["fase_pre"])], axis=1).astype(float)
Xc = sm.add_constant(Xc, has_constant="add")
mcal = sm.OLS(muestra[Y].astype(float), Xc).fit()
muestra["residuo_calendario"] = mcal.resid
h2r = pd.DataFrame([contraste(muestra, "residuo_calendario",
                              "residuos del modelo de calendario")])
guardar_tabla(h2r.round(6), "t05_h2_robustez_residuos")
print("H2 residuos:", h2r[["cohen_d", "p_welch_unilateral"]].to_dict("records"))

# --- versión del notebook 01 ----------------------------------------------
nb = b[(b["es_dia_habil_nb"] == 1) & (b["es_covid_aspo"] == 0)].copy()
nb["grupo"] = np.where(nb["lluvia_medible"] == 0, "seco", "lluvia>=5mm")
h2n = pd.DataFrame([contraste(nb, Y, "notebook 01: lluvia_medible, hábiles fuera de ASPO")])
guardar_tabla(h2n.round(6), "t05_h2_notebook01")
print("H2 notebook01:", h2n[["cohen_d", "p_welch_bilateral"]].to_dict("records"))

muestra[["fecha", "grupo", Y, "residuo_calendario", "anio_mes", "fecha_dow"]] \
    .to_parquet("Ultima entrega/resultados/artefactos/h2_muestra.parquet", index=False)

# --- desglose: por qué el signo cambia respecto del notebook 01 ------------
def desglose(df: pd.DataFrame, spec: str, lluvia_col: str) -> list[dict]:
    if lluvia_col == "lluvia_significativa_5mm":
        g = np.where(df[lluvia_col] == 1, "lluvia>=5mm",
                     np.where(df["precipitacion_mm"] < 0.1, "seco", "leve"))
    else:
        g = np.where(df[lluvia_col] == 1, "lluvia_medible", "seco")
    d2 = df.assign(_g=g)
    out = [{"especificacion": spec, "grupo": k, "n": len(v), "demanda_media": v.mean()}
           for k, v in d2.groupby("_g")[Y]]
    return out


desg = []
desg += desglose(nb, "notebook 01 (2018-2021, hábiles, sin ASPO, lluvia_medible)",
                 "lluvia_medible")
desg += desglose(nb[nb["anio"].isin([2018, 2019])],
                 "notebook 01 restringido a 2018-2019", "lluvia_medible")
desg += desglose(sub, "H2 (2018-2019, hábiles, sin feriado ni atípicos, 3 grupos)",
                 "lluvia_significativa_5mm")
desg += desglose(sub[sub["precipitacion_mm"] < 0.1].append(
    sub[sub["lluvia_medible"] == 1], ignore_index=True)
    if False else pd.concat([sub[sub["precipitacion_mm"] < 0.1],
                             sub[sub["lluvia_medible"] == 1]]),
                 "mismo subconjunto H2 con umbral lluvia_medible", "lluvia_medible")
guardar_tabla(pd.DataFrame(desg).round(0), "t05_h2_desglose")

# =============================================== robustez con tarifa ========
tar = pd.read_csv("dsets/registro-historico-del-precio-del-boleto.csv")
tar = tar.rename(columns={"año": "anio", "mes_numero": "mes", "mes": "mes_nombre",
                          "precio": "tarifa_nominal"})
sub_t = b[b["fecha"] <= "2019-04-30"].merge(tar[["anio", "mes", "tarifa_nominal"]],
                                             on=["anio", "mes"], how="inner")
sub_t["log_tarifa"] = np.log(sub_t["tarifa_nominal"])
sub_t["tendencia"] = ((sub_t["fecha"] - sub_t["fecha"].min()).dt.days / 30.44)

# A) M1 restringido al período
XA = matriz(sub_t, CLIMA_BASE, anio_mes=True, fase=False)
mA, mhA = ajustar(sub_t, XA, sub_t[Y])
# B) mes del año + tendencia + log(tarifa), sin efectos fijos año-mes
XB = pd.concat([sub_t[CLIMA_BASE].astype(float),
                pd.get_dummies(sub_t["fecha"].dt.weekday, prefix="ds",
                               dtype=float).drop(columns=["ds_0"]),
                pd.get_dummies(sub_t["mes"], prefix="mes", dtype=float).drop(
                    columns=["mes_1"]),
                sub_t[["es_feriado", "dia_atipico", "tendencia",
                       "log_tarifa"]].astype(float)], axis=1).astype(float)
XB = sm.add_constant(XB, has_constant="add")
mB, mhB = ajustar(sub_t, XB, sub_t[Y])


def fila_beta(m, mh, X, etiqueta):
    it = list(X.columns).index("temperatura_media_c")
    il = list(X.columns).index("lluvia_significativa_5mm")
    return {"modelo": etiqueta, "n": int(m.nobs),
            "periodo": f"{sub_t['fecha'].min().date()} a {sub_t['fecha'].max().date()}",
            "beta_temp": float(m.params["temperatura_media_c"]),
            "p_temp_hac": float(mh.pvalues[it]),
            "beta_lluvia": float(m.params["lluvia_significativa_5mm"]),
            "p_lluvia_hac": float(mh.pvalues[il]), "r2": m.rsquared}


tar_tab = pd.DataFrame([fila_beta(mA, mhA, XA, "M1 restringido 2018-01/2019-04"),
                        fila_beta(mB, mhB, XB,
                                  "mes del año + tendencia + log(tarifa)")])
guardar_tabla(tar_tab.round(6), "t05_robustez_tarifa")

# plantilla para que el grupo complete la serie de tarifas
fil, meses = [], []
for a in range(2019, 2022):
    for m_ in range(1, 13):
        if a == 2019 and m_ < 5:
            continue
        fil.append({"anio": a, "mes": m_, "precio": "", "fuente_norma": ""})
plantilla = pd.DataFrame(fil)
plantilla.to_csv("recursos/tarifa_complemento_manual.csv", index=False)
print(f"[plantilla] recursos/tarifa_complemento_manual.csv ({len(plantilla)} filas)")
print("OK 05")
