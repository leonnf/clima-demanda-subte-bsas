# Disponibilidad de datos — Incidencia del clima en la demanda de subte (2018–2021)

## Inventario

| Archivo | Ubicación | Filas | Estado | Sirve para | Acción |
|---|---|---|---|---|---|
| historico_2018.csv | dsets/ y Subtes/ | 12.136.454 | duplicado (md5 idéntico) | Demanda / features molinetes | Usar en dsets/ |
| historico_2019.csv | dsets/ y Subtes/ | 12.662.343 | duplicado (md5 idéntico) | Idem | Usar en dsets/ |
| historico_2020.csv | dsets/ y Subtes/ | 5.781.006 | duplicado (md5 idéntico) | Idem | Usar en dsets/ |
| historico_2021.csv | dsets/ y Subtes/ | 8.071.680 | duplicado (md5 idéntico) | Idem | Usar en dsets/ |
| historico_2014–2017.csv | solo Subtes/ | 10,9 / 11,0 / 11,5 / 11,9 M | OK (fuera de rango) | No (proyecto 2018–2021) | Ignorar / archivar |
| BaseUnificadaEstaciones, estaciones-accesibles, lineas-de-subte, viajes_anual, registro-boleto (.csv/.xlsx) | dsets/ y Subtes/ | — | duplicado (md5 idéntico) | Estaciones / tarifa | Usar en dsets/ |
| clima_diario_caba_2018_2021_consolidado.csv | recursos/ | 1.461 × 32 col | OK — SHA-256 **coincide** con 652a5e2c…cc592 | Variables climáticas (H1/H2) | Ninguna |
| demanda_diaria_subte_2018_2021.csv | recursos/ | 1.425 × 2 col | OK (verificado) | Eje dependiente | Reconstruir/recalcular igual |
| perfil_horario_estaciones_subte.csv | recursos/ | 87 × 26 col | dudoso (origen no trazado) | H3 (K-Means por estación) | Ver veredicto |
| registro-historico-del-precio-del-boleto (.csv/.xlsx) | dsets/ y Subtes/ | 304 | incompleto (1994–2019-04) | Tarifa nominal parcial | Ver sección 4 |
| 63cf6db…png | recursos/ | — | OK | Figura de apoyo | Ninguna |

Esquema de molinetes: 2018 y 2019 traen `fecha,desde,hasta,linea,molinete,estacion,pax_pagos,pax_pases_pagos,pax_franq,total` (más `periodo`; en 2019 `periodo` va primero). 2020 usa mayúsculas y `pax_TOTAL` con fecha `dd/mm/aaaa`. 2021 usa **punto y coma** como separador, mayúsculas y `pax_TOTAL`. 2014–2017 traen variantes extra (`ID_ESTACION`, `PAX_FREQ`, `V1`, comillas). Hay que normalizar nombre de columnas, separador y formato de fecha.

## Veredicto demanda_diaria_subte_2018_2021.csv
**Real:** el `total` de historico_2019.csv coincide exactamente — 2019-01-02: 836.802 (molinetes) vs 836.802,0 (CSV); 2019-07-10: 1.344.177 vs 1.344.177,0.

## Veredicto perfil_horario_estaciones_subte.csv
**Sirve para H3 pero su origen no está en los notebooks:** 01 solo lo lee (`pd.read_csv`), nunca lo escribe; 87 estaciones × 24 horas normalizadas (suma 1 por fila), coherente con los molinetes, aunque el 01 menciona 90 estaciones. Reproducir desde los históricos antes de entregar.

## Diferencias 00 vs 00_SL
Mismas fuentes (ERA5 Open-Meteo, NASA POWER, Meteostat 87582), mismas fechas (2018-01-01 a 2021-12-31) y mismo CSV de salida con el mismo SHA-256. Cambia solo el feature engineering: la versión SL agrega dummies por día de la semana (`Lunes`…`Domingo_Feriado`) en lugar de los binarios `es_fin_de_semana`/`es_dia_habil` originales.

## Figura 63cf6db…png
Histograma de precipitación diaria en días lluviosos + barras de clasificación de días por intensidad (Seco / Leve / Moderada / Tormenta, total 1.461 días).

## 4. Tarifa
CSV y XLSX traen **lo mismo**: 304 filas de datos (305 con encabezado) en ambos, último registro **2019-04**. Rango: 1994-01 a 2019-04 → **no cubre 2020–2021**.

| Período | Precio |
|---|---|
| 2018-01 a 2018-07 | 7,50 |
| 2018-08 a 2018-10 | 12,50 |
| 2018-11 | 13,50 |
| 2018-12 | 14,50 |
| 2019-01 | 15,50 |
| 2019-02 a 2019-03 | 16,50 |
| 2019-04 | 19,00 |
| 2019-05 a 2021-12 | **falta** |

## 5. Descargas necesarias
**Ninguna obligatoria.** Clima íntegro (SHA-256 verificado); demanda verificada; históricos completos 2018–2021.
- *Opcional:* tarifa real 2019-05→2021 — IPCBA, Dirección General de Estadística y Censos, GCBA (estadisticaciudad.gob.ar). No descargar en este paso.
- *Si se rompiera el CSV de clima:* reejecutar `00_extraccion_y_curacion_datos_climaticos.ipynb` (ERA5 vía archive-api.open-meteo.com, NASA POWER, Meteostat 87582).

## Carpeta de trabajo recomendada
**`dsets/`** para los históricos 2018–2021 (idénticos a `Subtes/`, permisos abiertos) y **`recursos/`** para los derivados; `Subtes/` queda solo como archivo de 2014–2017.
