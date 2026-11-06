#!/usr/bin/env python3
"""06 - H3: perfiles horarios por estación, K-Means, PCA y mapa.

Construye el perfil de 24 horas desde demanda_estacion_hora_2018_2019.parquet,
lo compara con perfil_horario_estaciones_subte.csv, agrupa con K-Means (K=2..6)
y cruza con estaciones-accesibles.csv.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

from comun import SEED, fold_ascii, guardar_tabla, norm_estacion, norm_linea

eh = pd.read_parquet("recursos/demanda_estacion_hora_2018_2019.parquet")
n_dias = eh["fecha"].nunique()
print(f"datos: {eh.shape} | días hábiles: {n_dias} | "
      f"estaciones: {eh['estacion'].nunique()}")

# ------------------------------------- completeness: excluir incompletas ----
por_dias = eh.groupby("estacion")["fecha"].nunique()
completas = por_dias[por_dias >= 0.9 * n_dias].index
excluidas = por_dias[por_dias < 0.9 * n_dias]
print(f"estaciones completas (>=90% de los días): {len(completas)} | "
      f"excluidas: {len(excluidas)} -> {sorted(excluidas.index)}")

# --------------------------------------------------------- perfiles --------
def perfil_agregado(df: pd.DataFrame) -> pd.DataFrame:
    """Participación de cada hora en el total del período (fila = 1)."""
    t = df.groupby(["linea", "estacion", "hora"], as_index=False)["total"].sum()
    t["share"] = t.groupby(["linea", "estacion"])["total"].transform(
        lambda s: s / s.sum())
    return t


def perfil_media_diaria(df: pd.DataFrame) -> pd.DataFrame:
    """Participación diaria de cada hora, promediada en el período (fila = 1)."""
    d = df.groupby(["fecha", "linea", "estacion", "hora"], as_index=False)["total"].sum()
    d["share_dia"] = d.groupby(["fecha", "linea", "estacion"])["total"].transform(
        lambda s: s / s.sum())
    m = d.groupby(["linea", "estacion", "hora"], as_index=False)["share_dia"].mean()
    return m.rename(columns={"share_dia": "share"})


dfh = eh[eh["estacion"].isin(completas)]
pa = perfil_agregado(dfh)
pm = perfil_media_diaria(dfh)

# matriz ancha (estación x 24 horas)
mat = pm.pivot_table(index=["linea", "estacion"], columns="hora", values="share",
                     fill_value=0.0)
mat = mat.reindex(columns=range(24), fill_value=0.0)
print(f"matriz de perfiles: {mat.shape} | suma por fila: "
      f"[{mat.sum(axis=1).min():.4f}, {mat.sum(axis=1).max():.4f}]")

# ------------------------ comparación con perfil_horario_estaciones_subte ---
# el CSV de referencia viene plegado a ASCII (AGERO, SAENZ PEA): pliegamos los
# dos lados para poder comparar sin perder los acentos en nuestro parquet
ref = pd.read_csv("recursos/perfil_horario_estaciones_subte.csv")
ref["linea"] = ref["linea"].map(norm_linea)
ref["estacion"] = ref["estacion"].map(norm_estacion).map(fold_ascii)
ref_mat = ref.set_index(["linea", "estacion"])
ref_mat = ref_mat[[c for c in ref_mat.columns if str(c).isdigit()]]
ref_mat.columns = ref_mat.columns.astype(int)

mat_cmp = mat.copy()
mat_cmp.index = pd.MultiIndex.from_arrays(
    [mat.index.get_level_values("linea"), mat.index.get_level_values("estacion").map(fold_ascii)],
    names=["linea", "estacion"])

comun_idx = mat_cmp.index.intersection(ref_mat.index)
solo_nuestro = mat_cmp.index.difference(ref_mat.index)
solo_ref = ref_mat.index.difference(mat_cmp.index)
dif = (mat_cmp.loc[comun_idx] - ref_mat.loc[comun_idx]).abs()
max_dif = float(dif.max().max())
media_dif = float(dif.mean().mean())
por_est = dif.max(axis=1)
print(f"\ncomparación con perfil_horario_estaciones_subte.csv: "
      f"{len(comun_idx)} estaciones en común | máx |diferencia| = {max_dif:.6f} | "
      f"media = {media_dif:.6f} | solo en nuestro perfil: {len(solo_nuestro)} | "
      f"solo en el CSV: {len(solo_ref)}")
if len(solo_ref):
    print("  solo en el CSV:", sorted(solo_ref))
if len(solo_nuestro):
    print("  solo en el nuestro:", sorted(solo_nuestro))

guardar_tabla(pd.DataFrame({
    "estacion": [f"{l}-{e}" for l, e in comun_idx],
    "dif_max_por_estacion": por_est.values}).round(6),
    "t06_perfil_vs_csv_por_estacion")
guardar_tabla(pd.DataFrame([{
    "estaciones_en_comun": len(comun_idx), "solo_en_nuestro_perfil": len(solo_nuestro),
    "solo_en_el_csv": len(solo_ref), "dif_max_abs": max_dif, "dif_media_abs": media_dif,
    "estaciones_excluidas_incompletas": len(excluidas),
}]).round(6), "t06_perfil_vs_csv_resumen")

# ------------------------------------------------------------ K-Means -------
X = mat.to_numpy()
resumen_k, etiquetas = [], {}
for k in range(2, 7):
    km = KMeans(n_clusters=k, random_state=SEED, n_init=10).fit(X)
    sil = silhouette_score(X, km.labels_)
    resumen_k.append({"k": k, "inercia": km.inertia_, "silueta": sil,
                      "iteraciones": int(km.n_iter_)})
    etiquetas[k] = km.labels_
diag_k = pd.DataFrame(resumen_k)
guardar_tabla(diag_k.round(4), "t06_kmeans_diagnostico")
print("\n" + diag_k.round(4).to_string(index=False))

# elección: silueta máxima; si hay empate, el codo (mayor caída de inercia)
k_opt = int(diag_k.loc[diag_k["silueta"].idxmax(), "k"])
print(f"K elegido por silueta máxima: {k_opt}")

km = KMeans(n_clusters=k_opt, random_state=SEED, n_init=10).fit(X)
labels = km.labels_

# ------------------------------------------------------------------ PCA ----
pca = PCA(n_components=2, random_state=SEED)
coords = pca.fit_transform(X)
var_exp = pca.explained_variance_ratio_
print(f"PCA: varianza explicada PC1={var_exp[0]:.4f} PC2={var_exp[1]:.4f} "
      f"(total {var_exp.sum():.4f})")
guardar_tabla(pd.DataFrame([{"componente": "PC1", "varianza_explicada": var_exp[0]},
                            {"componente": "PC2", "varianza_explicada": var_exp[1]},
                            {"componente": "PC1+PC2", "varianza_explicada": var_exp.sum()}]
                           ).round(6), "t06_pca_varianza")

# --------------------------------------------------- caracterización --------
perfil_df = mat.copy()
perfil_df["cluster"] = labels
perfil_df["pca1"] = coords[:, 0]
perfil_df["pca2"] = coords[:, 1]

AM = range(4, 12)      # 04-11 h
PM = range(16, 22)     # 16-21 h
filas = []
for c in sorted(perfil_df["cluster"].unique()):
    sub = perfil_df[perfil_df["cluster"] == c]
    horas = [col for col in mat.columns]
    med = sub[horas].mean()
    pico_am = int(med[list(AM)].idxmax())
    pico_pm = int(med[list(PM)].idxmax())
    ratio = float(med[list(AM)].sum() / med[list(PM)].sum())
    filas.append({"cluster": c, "n_estaciones": len(sub),
                  "hora_pico_AM": pico_am, "hora_pico_PM": pico_pm,
                  "share_AM": med[list(AM)].sum(), "share_PM": med[list(PM)].sum(),
                  "ratio_AM_PM": ratio,
                  "estaciones": "; ".join(sorted(sub.index.get_level_values("estacion")))})
clusters = pd.DataFrame(filas)


def etiqueta(r: pd.DataFrame) -> str:
    if r["ratio_AM_PM"] >= 1.25:
        return "residencial: origen AM"
    if r["ratio_AM_PM"] <= 0.40:
        return "microcentro: destino PM muy marcado"
    if r["ratio_AM_PM"] <= 0.75:
        return "central: destino PM"
    return "mixto"


clusters["etiqueta"] = clusters.apply(etiqueta, axis=1)
guardar_tabla(clusters.round(4), "t06_clusters")
print("\n" + clusters[["cluster", "n_estaciones", "hora_pico_AM", "hora_pico_PM",
                       "ratio_AM_PM", "etiqueta"]].to_string(index=False))

perfil_df.reset_index().to_parquet(
    "Ultima entrega/resultados/artefactos/h3_perfiles_clusters.parquet", index=False)

# ------------------------------------------------------------------ mapa ----
geo = pd.read_csv("dsets/estaciones-accesibles.csv")
geo["linea"] = geo["linea"].map(norm_linea)
geo["estacion"] = geo["estacion"].map(norm_estacion)
# alias de la fuente geo hacia el nombre usado en los molinetes
geo["estacion"] = geo["estacion"].replace({"HUMBERTO 1°": "HUMBERTO I",
                                            "HUMBERTO 1": "HUMBERTO I"})
# los molinetes desambiguan con sufijo ".<línea>" (CALLAO.B); la fuente geo no
perfil_geo = perfil_df.reset_index().copy()
perfil_geo["estacion"] = [e[:-(len(l) + 1)] if e.endswith("." + l) else e
                          for e, l in zip(perfil_geo["estacion"], perfil_geo["linea"])]
geo_cl = geo.merge(perfil_geo[["linea", "estacion", "cluster"]],
                   on=["linea", "estacion"], how="inner")
sin_geo = perfil_geo.merge(
    geo[["linea", "estacion"]], on=["linea", "estacion"], how="left", indicator=True)
sin_geo = sin_geo[sin_geo["_merge"] == "left_only"]
print(f"\nestaciones con geo: {len(geo_cl)} de {len(perfil_df)} | "
      f"sin geo: {len(sin_geo)} -> "
      f"{sorted(zip(sin_geo['linea'], sin_geo['estacion']))}")
guardar_tabla(pd.DataFrame({"linea": sin_geo["linea"], "estacion": sin_geo["estacion"]}),
              "t06_estaciones_sin_geo")
geo_cl.to_csv("Ultima entrega/resultados/tablas/t06_mapa_clusters.csv", index=False)
print(f"[tabla] t06_mapa_clusters.csv ({len(geo_cl)} filas)")

# geo también para las excluidas (informe)
guardar_tabla(pd.DataFrame({"estacion": sorted(excluidas.index),
                            "dias_presentes": excluidas.sort_index().values}),
              "t06_estaciones_excluidas")
print("OK 06")
