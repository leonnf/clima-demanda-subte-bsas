# Informe de resultados — Incidencia de las condiciones climáticas en la demanda de pasajeros del subte de Buenos Aires (2018–2021)

Trabajo Final Integrador — Metodología de la Investigación (Lic. en Ciencia de Datos).
Todas las cifras de este informe provienen de los scripts numerados de `Ultima entrega/notebooks/`
(ejecutados con `random_state=42`) y de las tablas/figuras guardadas en `Ultima entrega/resultados/`.

## 1. Resumen ejecutivo

- **H1 (sensibilidad térmica): NO SOSTENIDA en el modelo principal.** M1: β_temp = **−1.122 pasajeros/°C** (EE HAC = 2.543, t = −0,44, p unilateral = 0,330; IC 95 % [−6.111; +3.867]; −0,19 % de la demanda media).
- La misma hipótesis **sí se sostiene en el subperíodo pre-pandemia**: M5 (2018–2019) β_temp = **−3.892** (p HAC = 0,014) y en M0 sin errores robustos (β = −7.578; p(OLS) = 0,0002).
- **H2 (efecto refugio): NO SOSTENIDA; el efecto es del signo opuesto.** Días hábiles 2018–2019 sin feriados ni atípicos: lluvia ≥ 5 mm promedia 1.224.068 vs 1.269.706 en días secos → **d de Cohen = −0,351** (IC 95 % [−0,638; −0,075]), p bilateral = 0,017; con residuos del calendario **d = −0,596** (p = 0,000089).
- El resultado del notebook 01 (**d = 0,2022, p = 0,0032**) se reproduce exactamente y se explica por la inclusión de 2020–2021, no por la lluvia en 2018–2019 (ver §6).
- **H3 (perfiles horarios): exploratoria, sostenida como descripción.** 85 estaciones completas, **K = 4** (silueta 0,495), PCA con **93,1 %** de varianza en 2 componentes; los perfiles **coinciden con 85 de las 87 estaciones** del CSV no documentado (diferencia máxima 0,0418, media 0,0028).
- **Mejor modelo predictivo: Random Forest** (train 2018 / test 2019): **RMSE 102.572**, MAE 71.983, R² 0,943; el clima aporta 2.762 de RMSE (−2,1 %) en la regresión lineal.
- **Control de datos clave:** la demanda diaria coincide **exactamente en los 727 días de 2018–2019** con los molinetes, pero **no se pudo validar para 2020–2021** (44 y 110 días con diferencias).

## 2. Datos y ETL

**Unión analítica.** Inner join clima × demanda = **1.425 días** (2018-01-01 a 2021-12-31), guardado en `recursos/base_analitica.parquet` (1.425 × 47).

**Los 36 días sin demanda** (`t01_dias_sin_demanda.csv`): 3 en 2019 (30/04, 01/05, 29/05), **32 en 2020** y 1 en 2021 (14/11). Se concentran en cuatro bloques consecutivos: 03–10/01/2020, 03–10/02/2020, 03–10/11/2020 y 03–10/12/2020 (8 días cada uno, de lunes a domingo). **Solo 6 caen dentro de la ventana ASPO** (03–08/11/2020); el resto son huecos de publicación al inicio y al fin de 2020, no paros.

**Verificación de la serie de demanda** (`t03_comparacion_diaria_2018_2019.csv`, `t03b_*`, `t03c_*`):

| Período | Días comparables | Coinciden | Difieren | Dif. máxima | Veredicto |
|---|---|---|---|---|---|
| 2018–2019 (recalculado vs CSV) | 727 | **727** | 0 | **0,0** | coincide |
| 2020 (recalculado vs CSV) | 334 | 290 | 44 | 1.035.204 | **no coincide** |
| 2021 (recalculado vs CSV) | 344 | 234 | 110 | 682.592 | **no coincide** |

Veredicto puntual del paso 2 (un día hábil por año, con `awk`): 2020-01-02 molinetes 927.080 vs CSV 331.100; 2021-01-04 molinetes 166.811 vs CSV 131.542 → **no coinciden**. El análisis completo mostró que **90 de las 110 diferencias de 2021 (81,8 %) y 12 de las 44 de 2020 son exactamente un intercambio día↔mes**, es decir, un problema de convención de fecha (dd/mm vs mm/dd) en uno de los dos lados; además los históricos 2020/2021 mezclan formatos de fecha (2020: 5.779.170 filas con barra, 2.400.760 ambiguas resueltas por orden; 2021: 1.043.613 en ISO y 7.028.067 con barra) y **20 días de 2021 no aparecen en el histórico**. Se mantiene la serie original para el análisis (es la documentada y está verificada en 2018–2019) y se la marca como limitación.

**Controles de calidad de los molinetes 2018–2019** (`t03_controles_molinetes.csv`): 24.798.797 filas leídas (12.136.454 + 12.662.343); **78.207 filas basura** en `historico_2018.csv` (solo llevan `periodo`, sin fecha ni total); 0 valores negativos; **9 duplicados** sobre (fecha, desde, molinete) en 9 grupos.

**Calendario.** El CSV de clima trae `es_feriado = 0` en los 1.461 días (bug de `isin()` en el notebook 00), por lo que `es_dia_habil` original eran simplemente los 1.045 días de semana. Se reconstruyeron con la misma fuente que pretendía usar el 00 (`holidays.Argentina`): **72 feriados y 959 días hábiles**. Las columnas originales se conservan como `es_feriado_clima`.

**Equivalencias de estaciones** (`t03_equivalencias_estaciones.csv`): la normalización unificó 2 nombres con variantes de encoding (mojibake doble): `AGÜERO` ← `AgÃ¼ero | AgÃ¼ero | Agüero` (línea D) y `SAENZ PEÑA` ← `Saenz PeÃ±a | Saenz PeÃ±a | Saenz Peña` (línea A). Con eso, 94 nombres crudos pasan a **90 estaciones**.

**Origen de `perfil_horario_estaciones_subte.csv`.** No está documentado en ningún notebook (el 01 solo lo lee). Al reconstruirlo desde los molinetes 2018–2019 se obtienen **85 estaciones en común con diferencia máxima 0,0418 y media 0,0028** (el CSV tiene 87: le faltan Plaza de Mayo y Facultad de Derecho, que nosotros excluimos por incompletas). **Queda documentado: es el mismo cálculo (participación horaria normalizada) sobre los molinetes**, con un agregado ligeramente distinto.

## 3. Variables de control

**Fases** (`base_analitica.parquet`): pre 790 días (hasta 19/03/2020), ASPO 228 (20/03–08/11/2020), DISPO 43 (09/11–31/12/2020), 2021 364.

**Días atípicos** (`t02_dias_atipicos.csv`): 35 de 959 días hábiles con residuo del modelo de calendario (año-mes + día de semana + feriado + fase) menor a −3 desvíos robustos (MAD). **No se los llama "paros":** están listados para que el grupo los valide. Los más extremos:

| Fecha | Demanda | z robusto | Fecha | Demanda | z robusto |
|---|---|---|---|---|---|
| 2018-06-25 | 4 | −16,05 | 2019-12-24 | 377.031 | −9,49 |
| 2018-09-25 | 2 | −15,57 | 2019-04-18 | 550.875 | −9,20 |
| 2018-11-30 | 1 | −15,17 | 2018-03-29 | 554.355 | −8,61 |
| 2018-10-31 | 313.083 | −12,28 | 2020-03-18 | 335.797 | −8,41 |
| 2020-03-19 | 163.776 | −10,55 | 2021-12-09 | 344 | −5,53 |

Los 35 se usan como dummy `dia_atipico` en M1/M3/M4 y en el modelo predictivo.

## 4. Análisis exploratorio

**Demanda** (`t04_demanda_por_*`): media anual 954.521 (2018), 942.930 (2019), 232.051 (2020) y 263.948 (2021). Por fase: pre 930.423, ASPO 112.746, DISPO 151.288, 2021 263.948. Por tipo de día: hábil 774.098, fin de semana 268.077, feriado 200.939.

**Clima** (`t04_clima_resumen.csv`, `t04_dias_por_intensidad_lluvia.csv`): temperatura media 17,4 °C (min 3,8 / max 30,9), precipitación media 2,83 mm (max 82). Distribución de los 1.425 días: **seco 842 (59,1 %), leve 398 (27,9 %), moderada 126 (8,8 %), fuerte 59 (4,1 %)**.

**Validación de fuentes** (`t04_validacion_fuentes.csv`): temperatura ERA5 vs estación SABA (Aeroparque): **r = 0,9898** con 1.424 pares completos, **1 faltante (0,07 %)** y sesgo medio ERA5 − SABA = −0,72 °C. Las dos fuentes son intercambiables para temperatura.

**Confusión estacional** (`t04_correlacion_temp_demanda.csv`), días hábiles pre-pandemia (n = 532): correlación temperatura–demanda **cruda = −0,361**, **residualizada por año-mes = −0,002** (y −0,004 agregando día de la semana). La relación marginal es **casi enteramente estacional**: es la razón por la que M1 (con efectos fijos de mes) pierde significación respecto de M0.

## 5. H1 — Sensibilidad térmica

Modelo principal M1 (n = 1.425): demanda ~ temperatura media + lluvia ≥ 5 mm + día de semana + feriado + **efectos fijos año-mes** + fase COVID + `dia_atipico`, errores HAC (Newey-West, 7 rezagos).

| Estimación | Valor |
|---|---|
| β_temp | **−1.121,91 pasajeros/°C** |
| EE (HAC) | 2.543,26 |
| t | −0,441 |
| **p unilateral (H0: β ≥ 0 vs H1: β < 0)** | **0,330** |
| IC 95 % | [−6.111,03 ; +3.867,21] |
| En % de la demanda media (605.841) | −0,19 % |

**Conclusión: H1 no se sostiene en el modelo principal.** El signo es el esperado pero el intervalo incluye cero con holgura.

**Tabla de especificaciones** (`t05_especificaciones.csv`, errores HAC):

| Modelo | n | R² | R² aj. | β_temp | p temp | β_lluvia | p lluvia | VIF temp | VIF lluvia | DW | p BP |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M0 (notebook 01) | 1.425 | 0,360 | 0,358 | −7.578,19 | 0,075 | +22.481,94 | 0,497 | 1,07 | 1,01 | 0,59 | <0,001 |
| M1 (principal) | 1.425 | 0,806 | 0,798 | −1.121,91 | 0,659 | −2.854,04 | 0,879 | 4,18 | 1,06 | 1,37 | <0,001 |
| M2 (log) | 1.425 | 0,709 | 0,696 | +0,0018 | 0,802 | +0,0402 | 0,446 | 4,18 | 1,06 | 1,55 | <0,001 |
| M3 (precip. continua) | 1.425 | 0,806 | 0,798 | −972,70 | 0,702 | −665,73 | 0,374 | 4,18 | — | 1,37 | <0,001 |
| M4 (sin atípicos) | 1.425 | 0,774 | 0,765 | +1.124,20 | 0,687 | −8.392,54 | 0,677 | 4,16 | 1,06 | 1,32 | <0,001 |
| M5 (2018–2019) | 727 | 0,932 | 0,929 | **−3.892,05** | **0,014** | −19.025,58 | 0,179 | 4,04 | 1,07 | 1,71 | <0,001 |

M0 replica el notebook 01 (β = −7.578,19 pasajeros/°C y t(OLS) = −3,79; el informe anterior reportaba −7,578 en miles). En M3 el VIF de lluvia no aplica porque la variable es `precipitacion_mm` continua. **Ninguna especificación encuentra un efecto de lluvia significativo**; el único β_temp significativo es M5 (2018–2019).

**Sensibilidad no lineal** (`t05_temp_bins.csv`, referencia 15–20 °C): los tramos 10–15 (−21.959), 20–25 (−30.606), 25–30 (−33.885) y ≥30 (−20.189) son negativos pero **ninguno es significativo** (p entre 0,11 y 0,89); <10 °C da +11.823 (p = 0,74). No hay evidencia de no linealidad.

## 6. H2 — Efecto refugio ante la lluvia

Subconjunto: días hábiles 2018–2019, sin feriados ni `dia_atipico`; grupos lluvia ≥ 5 mm (n = 70) vs seco < 0,1 mm (n = 244); la lluvia leve queda excluida (`t05_h2_contraste.csv`).

| Estadístico | Valor |
|---|---|
| Media seco / lluvia | 1.269.706 / 1.224.068 |
| Diferencia (lluvia − seco) | **−45.637** (IC 95 % [−83.027 ; −8.248]) |
| t de Welch (unilateral μ_lluvia > μ_seco) | −2,421 → **p = 0,991** |
| p bilateral | **0,017** |
| Mann-Whitney (unilateral) | p = 0,9999 |
| **d de Cohen** (IC bootstrap 2.000 réplicas) | **−0,351 [−0,638 ; −0,075]** |
| Criterio a priori | d ≥ 0,20 en dirección positiva → **no alcanzado** |

Sobre los **residuos del modelo de calendario** (`t05_h2_robustez_residuos.csv`): medias +7.134 vs −24.868, diferencia −32.003 (IC [−47.547 ; −16.459]), **d = −0,596 [−0,908 ; −0,288]**, p bilateral = 0,000089.

**Conclusión: H2 no se sostiene.** En 2018–2019 los días con lluvia intensa tienen **menos** demanda, no más.

**Comparación con el notebook 01** (`t05_h2_notebook01.csv`, `t05_h2_desglose.csv`): la especificación anterior (lluvia_medible ≥ 0,1 mm, hábiles fuera del ASPO, 2018–2021, n = 490/366) se replica **exactamente: d = 0,202159, p = 0,003152**. El desglose muestra de dónde viene:

| Especificación | n seco / lluvia | media seco | media lluvia | diferencia |
|---|---|---|---|---|
| Notebook 01 (2018–2021) | 490 / 366 | 814.466 | 913.599 | **+99.133** |
| Notebook 01 restringido a 2018–2019 | 271 / 248 | 1.178.093 | 1.176.822 | −1.271 |
| H2 (2018–2019, umbral lluvia_medible) | 244 / 231 | 1.269.706 | 1.236.754 | −32.952 |
| H2 (2018–2019, umbral ≥ 5 mm) | 244 / 70 | 1.269.706 | 1.224.068 | −45.637 |

Es decir: **el d = 0,2022 del informe anterior lo generan los días de 2020–2021** (demanda deprimida), no un efecto de la lluvia en el período normal.

## 7. H3 — Perfiles horarios de estaciones (exploratoria)

`06_segmentacion_H3.py`: perfil de 24 horas por estación desde `demanda_estacion_hora_2018_2019.parquet` (804.220 filas, 490 días hábiles, 90 estaciones), participación media por hora con filas que suman 1.

- **Estaciones excluidas por incompletas** (< 90 % de los días hábiles): **5** → CATALINAS, CORREO CENTRAL, FACULTAD DE DERECHO, PLAZA DE MAYO, RETIRO E. **Quedan 85.**
- **Comparación con `perfil_horario_estaciones_subte.csv`**: **85 estaciones en común**, 0 solo en el nuestro, 2 solo en el CSV; **diferencia máxima 0,0418**, media 0,0028 (`t06_perfil_vs_csv_resumen.csv`).
- **K-Means K = 2…6** (`t06_kmeans_diagnostico.csv`): silueta 0,489 / 0,478 / **0,495** / 0,382 / 0,389; inercia 0,300 → 0,173 → 0,109 → 0,094 → 0,082. **Se elige K = 4** por tener la silueta máxima y porque la caída de inercia se aplana a partir de ahí.
- **PCA** (`t06_pca_varianza.csv`): PC1 = 84,2 %, PC2 = 8,9 %, **total 93,1 %**.

| Cluster | n | Pico AM | Pico PM | ratio AM/PM | Etiqueta |
|---|---|---|---|---|---|
| 0 | 36 | 8 h | 17 h | 1,20 | mixto |
| 1 | 11 | 11 h | 18 h | 0,27 | microcentro: destino PM muy marcado |
| 2 | 21 | 11 h | 18 h | 0,58 | central: destino PM |
| 3 | 17 | 8 h | 17 h | 2,52 | residencial: origen AM |

- **Mapa**: 77 de 85 estaciones se emparejan con `estaciones-accesibles.csv`; **14 no se pudieron emparejar** (`t06_estaciones_sin_geo.csv`): ALBERTI, FLORES, PASCO, RIO DE JANEIRO (A), LEANDRO N. ALEM, ROSAS (B), GENERAL SAN MARTIN, MARIANO MORENO (C), MINISTRO CARRANZA, SCALABRINI ORTIZ (D), GENERAL BELGRANO, INDEPENDENCIA.H, PZA. DE LOS VIRREYES (E), PATRICIOS (H) — la fuente geo no las publica con ese nombre.

## 8. Robustez con tarifa

El CSV de tarifas llega solo hasta **2019-04**; se creó `recursos/tarifa_complemento_manual.csv` (32 filas vacías: 2019-05 a 2021-12, columnas `anio, mes, precio, fuente_norma`) para que el grupo complete con las resoluciones de SBASE citadas en la 2da entrega. **No se inventó ningún valor.**

Comparación en 2018-01 → 2019-04 (n = 484), `t05_robustez_tarifa.csv`:

| Modelo | β_temp | p temp | β_lluvia | p lluvia | R² |
|---|---|---|---|---|---|
| M1 restringido (efectos fijos año-mes) | −5.485,01 | 0,0097 | −28.403,92 | 0,074 | 0,930 |
| Mes del año + tendencia + log(tarifa) | −5.490,48 | 0,0096 | −26.488,43 | 0,091 | 0,930 |

Los coeficientes **cambian menos de 1 %**, lo que confirma dos cosas: (i) el nivel tarifario está absorbido por los efectos fijos año-mes, de modo que **M1 no depende de completar la serie de tarifas**; y (ii) en este subperíodo el efecto térmico es significativo y negativo (consistente con M5).

## 9. Modelo predictivo

Train = 2018 (365 días), test = 2019 (362 días); 2020–2021 excluidos por el quiebre estructural. Búsqueda chica de hiperparámetros con `TimeSeriesSplit(3)` solo en 2018. Calendario: día de semana, feriado, mes y `dia_atipico`; clima: temp. media/máx/mín, precipitación y lluvia ≥ 5 mm (`t07_metricas.csv`).

| Modelo | RMSE 2019 | MAE | MAPE | R² | ΔRMSE vs M2 |
|---|---|---|---|---|---|
| 1 Ingenuo (semana anterior) | 276.099 | 124.830 | 28,2 % | 0,587 | +142.628 |
| 2 Regresión + calendario | 133.470 | 84.006 | 18,4 % | 0,903 | — |
| 3 Regresión + calendario + clima | 130.708 | 82.644 | 18,7 % | 0,907 | **−2.762 (−2,1 %)** |
| **4 Random Forest** | **102.572** | **71.983** | 21,9 % | **0,943** | −30.898 |
| 5 HistGradientBoosting | 234.516 | 142.383 | 33,1 % | 0,701 | +101.046 |

Hiperparámetros elegidos: RF `max_depth=None, min_samples_leaf=5, n_estimators=200` (RMSE CV 2018 = 305.788); HGB `learning_rate=0,05, max_iter=200, max_leaf_nodes=15`.

**Importancia por permutación en el mejor modelo de árboles (RF, test 2019, `t07_importancia_permutacion.csv`)**: dominan las variables de calendario (jueves 239.832, viernes 233.248, miércoles 226.863, martes 214.968, lunes 212.348, feriado 169.800, sábado 148.796; mes 36.174; `dia_atipico` 30.958) y recién después **temperatura media (1.087)** y precipitación (624); las temperaturas máx/mín y la lluvia ≥ 5 mm aportan poco o nada (negativo, es ruido). **El clima aporta, pero es marginal respecto del calendario.**

## 10. Supuestos y limitaciones

1. **Autocorrelación**: DW de M1 = 1,37 (residuos positivamente correlacionados); se usan errores HAC Newey-West con 7 rezagos, pero M0 con errores clásicos da t = −3,79 frente a −0,50 con la especificación completa.
2. **Heterocedasticidad**: p de Breusch-Pagan < 0,001 en todos los modelos; también se corrige con HAC.
3. **Atípicos sin confirmar**: los 35 días de `t02_dias_atipicos.csv` son residuos extremos, no paros verificados; requieren validación del grupo (fechas como 2018-06-25, 2018-09-25, 2018-11-30, 2018-10-31 y 2021-12-09 son candidatas evidentes).
4. **Los molinetes cuentan validaciones, no personas**: un usuario puede validar más de una vez; la serie es un flujo de transacciones, no de individuos.
5. **Tarifa incompleta**: solo hasta 2019-04; la robustez se estimó en ese subperíodo y la serie 2019-05→2021-12 queda como plantilla vacía.
6. **36 días sin demanda** (§2) y **20 días de 2021 sin molinetes**: la serie 2020–2021 **no se pudo validar** (44 y 110 días con diferencias, muchas por intercambio día↔mes).
7. **`es_feriado` del CSV de clima estaba en cero**; se reconstruyó con `holidays.Argentina` (72 feriados), no con un boletín oficial citado.
8. **M1 con efectos fijos año-mes absorbe casi toda la variación térmica**: la correlación residual temperatura–demanda es −0,002, por lo que la potencia para detectar H1 es baja; el efecto solo aparece en 2018–2019 (M5).
9. **El efecto de la lluvia es sensible al umbral y al período** (§6): reportar d = 0,20 sin especificar muestra es engañoso.

## 11. Cambios respecto de lo planificado en la 2da entrega

1. Se agregaron **03b y 03c**: la verificación puntual de 2020/2021 falló, así que se recalculó la demanda diaria completa de ambos años (una sola pasada) y se cuantificó el origen de las diferencias.
2. **`es_feriado`/`es_dia_habil` del CSV de clima estaban mal** (todo 0) y se reconstruyeron; esto cambia el subconjunto de días hábiles (1.045 → 959) y por lo tanto H2 y los atípicos.
3. Se documentó el **origen de `perfil_horario_estaciones_subte.csv`** (reproducible desde los molinetes, 85/87 estaciones).
4. M0 se **replica** del notebook 01 para comparar (β = −7.578,19) y se agregó la batería VIF/DW/BP en todas las especificaciones.
5. El resultado de H2 **invierte el signo** respecto de la 2da entrega al restringir a 2018–2019 y a días sin feriados ni atípicos; se desglosa la causa en §6.
6. La tarifa sigue incompleta: en lugar de estimar valores se entregó la plantilla `tarifa_complemento_manual.csv`.
7. Se reparó el mojibake de estaciones (`AGÜERO`, `SAENZ PEÑA`) al normalizar los nombres.

## 12. Reproducibilidad

**Orden de ejecución** (desde la raíz del proyecto, ver `README.md`):

| # | Script | Tiempo medido | Salida principal |
|---|---|---|---|
| 1 | `02_base_analitica.py` | 3 s | `recursos/base_analitica.parquet` |
| 2 | `03_molinetes_2018_2019.py` | 264 s | `recursos/demanda_estacion_hora_2018_2019.parquet` |
| 3 | `03b_verificacion_2020_2021.py` | 294 s | `t03b_*` |
| 4 | `03c_explicacion_diferencias.py` | 1 s | `t03c_*` |
| 5 | `04_eda.py` | 2 s | `t04_*` |
| 6 | `05_hipotesis.py` | 13 s | `t05_*` |
| 7 | `06_segmentacion_H3.py` | 26 s | `t06_*` |
| 8 | `07_modelo_predictivo.py` | 37 s | `t07_*` |
| 9 | `09_figuras.py` | 17 s | `fig01`…`fig12` |

Total medido en una corrida completa de punta a punta: **657 s (≈ 11 minutos)**, con rc = 0 en los 9 scripts. Semilla `random_state=42` en todas las rutinas aleatorias.

**Versiones** (`requirements.txt`): Python 3.8.10; pandas 2.0.3, numpy 1.24.4, scipy 1.10.1, statsmodels 0.14.1, scikit-learn 1.3.2, matplotlib 3.7.5, pyarrow 14.0.2, holidays 0.38.

**SHA-256 de los Parquet generados** (y del insumo climático, por referencia):

```
8fd767fee1a9efd64bb379a6e1a0bda4799724993b27c5676bc86d32e3ba8169  recursos/base_analitica.parquet
e6d740ba6a6e421f0e0cbed3a67cb00111c0c51421f6b42a48f6c19457b841df  recursos/demanda_estacion_hora_2018_2019.parquet
652a5e2cb4ae7c8a41197cc8a2cd89135927bf41f911580c40b0863ad75cc592  recursos/clima_diario_caba_2018_2021_consolidado.csv (insumo, ya verificado)
```

## 13. Índice de figuras

| Archivo | Contenido | Leyenda sugerida |
|---|---|---|
| `figuras/fig01_serie_diaria_fases_atipicos.png` | Serie diaria 2018–2021 con fases sombreadas y atípicos | "Figura 1. Demanda diaria con fases COVID y días atípicos (n = 35)." |
| `figuras/fig02_demanda_dia_semana_fase.png` | Demanda media por día de semana y fase | "Figura 2. Demanda media por día de la semana y fase." |
| `figuras/fig03_temp_vs_demanda.png` | Temp–demanda cruda y residualizada | "Figura 3. La correlación cruda desaparece al controlar el mes." |
| `figuras/fig04_dias_intensidad_lluvia.png` | Días por intensidad de lluvia | "Figura 4. Distribución de días por intensidad de lluvia." |
| `figuras/fig05_boxplots_h2.png` | Boxplots seco vs lluvia ≥ 5 mm, crudo y residual | "Figura 5. H2: días secos vs lluvia intensa." |
| `figuras/fig06_forest_plot_especificaciones.png` | β_temp y β_lluvia en M0–M5 con IC 95 % | "Figura 6. Efectos por especificación." |
| `figuras/fig07_diagnostico_residuos_m1.png` | Serie, ACF y Q-Q de residuos de M1 | "Figura 7. Diagnóstico de residuos de M1." |
| `figuras/fig08_efecto_bins_temperatura.png` | Efecto por tramo de temperatura | "Figura 8. Efecto térmico por tramos (no significativo)." |
| `figuras/fig09_codo_silueta.png` | Codo y silueta, K = 2…6 | "Figura 9. Selección de K." |
| `figuras/fig10_perfiles_por_cluster.png` | Perfiles horarios medios por cluster | "Figura 10. Perfiles horarios por cluster." |
| `figuras/fig11_pca_y_mapa_clusters.png` | PCA 2D y mapa de clusters | "Figura 11. PCA y distribución espacial." |
| `figuras/fig12_real_vs_predicho_rmse.png` | Real vs predicho 2019 y RMSE por modelo | "Figura 12. Desempeño predictivo en 2019." |

## 14. Índice de tablas

Todas en `resultados/tablas/`: `t01_dias_sin_demanda`, `t02_dias_atipicos`, `t03_comparacion_diaria_2018_2019`, `t03_controles_molinetes`, `t03_equivalencias_estaciones`, `t03_verificacion_2020_2021`, `t03b_verificacion_completa_2020_2021`, `t03b_comparacion_diaria_2020`, `t03b_comparacion_diaria_2021`, `t03c_explicacion_diferencias_2020_2021`, `t04_demanda_por_anio`, `t04_demanda_por_fase`, `t04_demanda_por_tipo_dia`, `t04_clima_resumen`, `t04_dias_por_intensidad_lluvia(_anio)`, `t04_validacion_fuentes`, `t04_correlacion_temp_demanda`, `t05_especificaciones`, `t05_h1_sensibilidad_termica`, `t05_temp_bins`, `t05_h2_contraste`, `t05_h2_robustez_residuos`, `t05_h2_notebook01`, `t05_h2_desglose`, `t05_robustez_tarifa`, `t06_perfil_vs_csv_resumen`, `t06_perfil_vs_csv_por_estacion`, `t06_estaciones_excluidas`, `t06_kmeans_diagnostico`, `t06_pca_varianza`, `t06_clusters`, `t06_estaciones_sin_geo`, `t06_mapa_clusters`, `t07_metricas`, `t07_importancia_permutacion`.
