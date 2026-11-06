#!/usr/bin/env python3
"""09 - Figuras de la última entrega (PNG 200 dpi, en español).

Lee los artefactos y tablas generados por 02-07 y emite resultados/figuras/figNN_*.png
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                      # noqa: E402
from matplotlib.patches import Patch                 # noqa: E402
from scipy import stats                              # noqa: E402

from comun import DIAS, RES_ART, RES_FIG, RES_TAB    # noqa: E402

plt.rcParams.update({"figure.dpi": 110, "font.size": 9, "axes.grid": True,
                     "grid.alpha": 0.3, "figure.autolayout": True})

TAB = lambda n: pd.read_csv(RES_TAB / f"{n}.csv")     # noqa: E731
b = pd.read_parquet("recursos/base_analitica.parquet")
FASES = [("pre", "#cfe3f7"), ("ASPO", "#f7d4d4"), ("DISPO", "#f7e7c4"),
         ("2021", "#dff0d8")]


def guardar(fig, nombre: str) -> None:
    p = RES_FIG / f"{nombre}.png"
    fig.savefig(p, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[figura] {p.name}")


# ---------------------------------------------------------- 01 serie -------
fig, ax = plt.subplots(figsize=(13, 4.5))
for nombre, color in FASES:
    sub = b[b["fase"] == nombre]
    ax.axvspan(sub["fecha"].min(), sub["fecha"].max(), color=color, alpha=.7,
               label=f"Fase {nombre}" if nombre != "pre" else "Pre-pandemia")
ax.plot(b["fecha"], b["demanda_pasajeros"], lw=.7, color="#1f3864",
        label="Demanda diaria")
ati = b[b["dia_atipico"] == 1]
ax.scatter(ati["fecha"], ati["demanda_pasajeros"], s=18, color="#c00000",
           zorder=5, label=f"Días atípicos (n={len(ati)})")
ax.set_title("Demanda diaria de subte, 2018-2021, con fases COVID y días atípicos")
ax.set_ylabel("Pasajeros por día"); ax.set_xlabel("")
ax.legend(ncol=4, fontsize=8, loc="upper right")
guardar(fig, "fig01_serie_diaria_fases_atipicos")

# ------------------------------------- 02 demanda por día de semana y fase --
piv = (b.pivot_table(index="fecha_dow" if "fecha_dow" in b else b["fecha"].dt.weekday,
                     columns="fase", values="demanda_pasajeros", aggfunc="mean"))
piv.index = [DIAS[i] for i in piv.index]
fig, ax = plt.subplots(figsize=(9, 4.5))
piv[list(x[0] for x in FASES)].plot.bar(ax=ax, color=[x[1] for x in FASES],
                                        edgecolor="#333", lw=.4)
ax.set_title("Demanda media por día de la semana y fase COVID")
ax.set_xlabel(""); ax.set_ylabel("Pasajeros (media)")
ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
guardar(fig, "fig02_demanda_dia_semana_fase")

# ------------------------------------- 03 temperatura vs demanda -----------
hab_pre = b[(b["fase"] == "pre") & (b["es_dia_habil"] == 1)].copy()
for v in ["temperatura_media_c", "demanda_pasajeros"]:
    hab_pre[f"{v}_res"] = hab_pre[v] - hab_pre.groupby("anio_mes")[v].transform("mean")
fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.4))
ax[0].scatter(hab_pre["temperatura_media_c"], hab_pre["demanda_pasajeros"], s=10,
              alpha=.55, color="#1f3864")
r0 = hab_pre["temperatura_media_c"].corr(hab_pre["demanda_pasajeros"])
ax[0].set_title(f"Cruda (r = {r0:.3f})")
ax[1].scatter(hab_pre["temperatura_media_c_res"], hab_pre["demanda_pasajeros_res"],
              s=10, alpha=.55, color="#2e7d32")
r1 = hab_pre["temperatura_media_c_res"].corr(hab_pre["demanda_pasajeros_res"])
ax[1].set_title(f"Residualizada por año-mes (r = {r1:.3f})")
for a in ax:
    a.set_xlabel("Temperatura media (°C)")
    a.set_ylabel("Pasajeros")
fig.suptitle("Temperatura y demanda en días hábiles pre-pandemia (2018-2019)", y=1.02)
guardar(fig, "fig03_temp_vs_demanda")

# ------------------------------------- 04 días por intensidad de lluvia ----
t4 = TAB("t04_dias_por_intensidad_lluvia")
fig, ax = plt.subplots(figsize=(7.5, 4))
barras = ax.bar(t4["intensidad_lluvia"], t4["dias"], color="#4c78a8")
ax.bar_label(barras, fmt="%d")
ax.set_title("Días por intensidad de precipitación (1.425 días)")
ax.set_ylabel("Cantidad de días"); ax.set_xlabel("")
guardar(fig, "fig04_dias_intensidad_lluvia")

# ------------------------------------- 05 boxplots H2 ----------------------
m2 = pd.read_parquet(RES_ART / "h2_muestra.parquet")
orden = ["seco", "lluvia>=5mm"]
colores = ["#9ecae1", "#2171b5"]
fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
bp = ax[0].boxplot([m2.loc[m2.grupo == g, "demanda_pasajeros"] for g in orden],
                   labels=orden, showfliers=True, patch_artist=True,
                   medianprops=dict(color="#c00000"))
for p, c in zip(bp["boxes"], colores):
    p.set_facecolor(c)
t_h2 = TAB("t05_h2_contraste").iloc[0]
ax[0].set_title(f"Cruda: d = {t_h2['cohen_d']:.3f} (p = {t_h2['p_welch_bilateral']:.4f})")
bp = ax[1].boxplot([m2.loc[m2.grupo == g, "residuo_calendario"] for g in orden],
                   labels=orden, showfliers=True, patch_artist=True,
                   medianprops=dict(color="#c00000"))
for p, c in zip(bp["boxes"], colores):
    p.set_facecolor(c)
t_r = TAB("t05_h2_robustez_residuos").iloc[0]
ax[1].set_title(f"Residuos del calendario: d = {t_r['cohen_d']:.3f} "
                f"(p = {t_r['p_welch_bilateral']:.4f})")
for a in ax:
    a.set_ylabel("Pasajeros" if a is ax[0] else "Residuo (pasajeros)")
    a.set_xlabel("Grupo")
fig.suptitle("H2: días secos vs días con lluvia >= 5 mm (hábiles 2018-2019, "
             "sin feriados ni atípicos)", y=1.03)
guardar(fig, "fig05_boxplots_h2")

# ------------------------------------- 06 forest plot M0-M5 ----------------
esp = TAB("t05_especificaciones")
fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
for a, (beta, icb, ica, tit) in zip(ax, [
        ("beta_temp", "ic_temp_bajo", "ic_temp_alto", "β temperatura (°C)"),
        ("beta_lluvia", "ic_lluvia_bajo", "ic_lluvia_alto",
         "β lluvia ≥ 5 mm (dummy)")]):
    y = np.arange(len(esp))
    a.errorbar(esp[beta], y, xerr=[esp[beta] - esp[icb], esp[ica] - esp[beta]],
               fmt="o", color="#c0392b", capsize=3.5, ms=6)
    for j, p in enumerate(esp["p_temp_hac"] if beta == "beta_temp"
                          else esp["p_lluvia_hac"]):
        if p < .05:
            a.plot(esp[beta].iloc[j], y[j], marker="*", color="#f39c12", ms=11,
                   zorder=6)
    a.axvline(0, color="#333", lw=.9)
    a.set_yticks(y); a.set_yticklabels(esp["modelo"]); a.invert_yaxis()
    a.set_title(f"{tit}  (★ = p < 0,05)")
    a.set_xlabel("Coeficiente (pasajeros)")
fig.suptitle("Efecto de temperatura y lluvia por especificación (IC 95 % HAC)", y=1.02)
guardar(fig, "fig06_forest_plot_especificaciones")

# ------------------------------------- 07 residuos M1 ----------------------
art = pd.read_parquet(RES_ART / "m1_ajuste.parquet")
res = art["residuo"].to_numpy()
fig, ax = plt.subplots(1, 3, figsize=(13.5, 3.8))
ax[0].plot(art["fecha"], res, lw=.6, color="#1f3864")
ax[0].axhline(0, color="#333", lw=.8)
ax[0].set_title("Serie de residuos"); ax[0].set_xlabel("")
maxlag = 30
ac = [np.corrcoef(res[:-l], res[l:])[0, 1] for l in range(1, maxlag + 1)]
ax[1].bar(range(1, maxlag + 1), ac, color="#4c78a8", width=.7)
ax[1].axhline(1.96 / np.sqrt(len(res)), color="#c00000", ls="--", lw=.8,
              label="IC 95 %")
ax[1].set_title("ACF de residuos"); ax[1].set_xlabel("Rezago (días)")
ax[1].legend(fontsize=7)
stats.probplot(res, dist="norm", plot=ax[2])
ax[2].set_title("Q-Q normal")
guardar(fig, "fig07_diagnostico_residuos_m1")

# ------------------------------------- 08 bins de temperatura --------------
tb = TAB("t05_temp_bins")
fig, ax = plt.subplots(figsize=(7.5, 4.2))
ax.errorbar(tb["bin_temperatura"], tb["beta_vs_15_20"],
            yerr=[tb["beta_vs_15_20"] - tb["ic95_bajo"],
                  tb["ic95_alto"] - tb["beta_vs_15_20"]],
            fmt="o", color="#c0392b", capsize=4)
ax.axhline(0, color="#333", lw=.9)
ax.set_title("Efecto de la temperatura por tramos (M1, referencia 15-20 °C)")
ax.set_xlabel("Tramo de temperatura media (°C)")
ax.set_ylabel("β (pasajeros)")
guardar(fig, "fig08_efecto_bins_temperatura")

# ------------------------------------- 09 codo y silueta -------------------
tk = TAB("t06_kmeans_diagnostico")
fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ax[0].plot(tk["k"], tk["inercia"], "o-", color="#1f3864")
ax[0].set_title("Codo (inercia)"); ax[0].set_xlabel("K")
ax[1].plot(tk["k"], tk["silueta"], "o-", color="#2e7d32")
mejor = int(tk.loc[tk["silueta"].idxmax(), "k"])
ax[1].axvline(mejor, color="#c00000", ls="--", lw=.9, label=f"máximo en K={mejor}")
ax[1].set_title("Silueta media"); ax[1].set_xlabel("K"); ax[1].legend(fontsize=8)
guardar(fig, "fig09_codo_silueta")

# ------------------------------------- 10 perfiles por cluster -------------
hp = pd.read_parquet(RES_ART / "h3_perfiles_clusters.parquet")
tcl = TAB("t06_clusters")
etq = dict(zip(tcl["cluster"], tcl["etiqueta"]))
horas = [c for c in hp.columns if isinstance(c, (int, np.integer))
         or (isinstance(c, str) and c.isdigit())]
fig, ax = plt.subplots(figsize=(9.5, 4.6))
for c in sorted(hp["cluster"].unique()):
    sub = hp[hp["cluster"] == c]
    med = sub[horas].astype(float).mean()
    ax.plot([int(h) for h in horas], med.to_numpy(), "o-", ms=3.5,
            label=f"C{c}: {etq[c]} (n={len(sub)})")
ax.set_xticks(range(24))
ax.set_title("Perfil horario medio por cluster (días hábiles 2018-2019)")
ax.set_xlabel("Hora"); ax.set_ylabel("Participación media")
ax.legend(fontsize=8)
guardar(fig, "fig10_perfiles_por_cluster")

# ------------------------------------- 11 PCA y mapa -----------------------
fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.8))
for c in sorted(hp["cluster"].unique()):
    sub = hp[hp["cluster"] == c]
    ax[0].scatter(sub["pca1"], sub["pca2"], s=26, label=f"C{c}: {etq[c]}")
for _, r in hp.iterrows():
    ax[0].annotate(r["estacion"], (r["pca1"], r["pca2"]), fontsize=5.5,
                   xytext=(2, 2), textcoords="offset points")
var = TAB("t06_pca_varianza")
v1 = float(var.loc[var.componente == "PC1", "varianza_explicada"].iloc[0])
v2 = float(var.loc[var.componente == "PC2", "varianza_explicada"].iloc[0])
ax[0].set_xlabel(f"PC1 ({100*v1:.1f} %)"); ax[0].set_ylabel(f"PC2 ({100*v2:.1f} %)")
ax[0].set_title("PCA de perfiles horarios")
ax[0].legend(fontsize=7)

geo = TAB("t06_mapa_clusters")
for c in sorted(geo["cluster"].unique()):
    sub = geo[geo["cluster"] == c]
    ax[1].scatter(sub["long"], sub["lat"], s=34, label=f"C{c}")
for _, r in geo.iterrows():
    ax[1].annotate(r["estacion"], (r["long"], r["lat"]), fontsize=5.5,
                   xytext=(2, 2), textcoords="offset points")
ax[1].set_xlabel("Longitud"); ax[1].set_ylabel("Latitud")
ax[1].set_title("Estaciones por cluster (geoestaciones-accesibles)")
ax[1].legend(fontsize=7, loc="lower right")
guardar(fig, "fig11_pca_y_mapa_clusters")

# ------------------------------------- 12 real vs predicho -----------------
pred = pd.read_csv(RES_ART / "predicciones_2019.csv", parse_dates=["fecha"])
met = TAB("t07_metricas")
fig, ax = plt.subplots(1, 2, figsize=(13, 4.4))
ax[0].plot(pred["fecha"], pred["real"], lw=1.1, color="#1f3864", label="Real 2019")
for col, color in [("4_random_forest", "#c0392b"),
                   ("3_regresion_calendario_clima", "#2e7d32"),
                   ("1_ingenuo_semana_anterior", "#999999")]:
    ax[0].plot(pred["fecha"], pred[col], lw=.9, ls="--", color=color,
               label=col.split("_", 1)[1].replace("_", " "))
ax[0].set_title("Real vs predicho, 2019"); ax[0].set_ylabel("Pasajeros")
ax[0].set_xlabel(""); ax[0].legend(fontsize=7)
m = met.sort_values("rmse_2019")
barras = ax[1].barh(m["modelo"].str.replace("_", " "), m["rmse_2019"], color="#4c78a8")
ax[1].bar_label(barras, fmt="%.0f", fontsize=8)
ax[1].set_title("RMSE en el período de prueba (2019)")
ax[1].set_xlabel("RMSE (pasajeros)")
guardar(fig, "fig12_real_vs_predicho_rmse")

print("OK 09 figuras")
