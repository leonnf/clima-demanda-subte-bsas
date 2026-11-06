# Última entrega — Incidencia del clima en la demanda de subte (2018-2021)

Este directorio contiene el código, las tablas y las figuras de la última entrega del
Trabajo Final Integrador. Todo el informe (`resultados/INFORME_RESULTADOS.md`) se genera
a partir de los scripts numerados de `notebooks/`; ningún número del informe está escrito
a mano.

## 1. Requisitos

- Python 3.8 o superior (probado con 3.8.10, Linux).
- Dependencias: `pip install -r requirements.txt`
  (pandas 2.0.3, numpy 1.24.4, scipy 1.10.1, statsmodels 0.14.1, scikit-learn 1.3.2,
  matplotlib 3.7.5, pyarrow 14.0.2, holidays 0.38).
- Disco: ~8 GB libres (los históricos de molinetes pesan ~2,4 GB y se leen una sola vez).
- Las rutas de los scripts son relativas a la raíz del proyecto (la carpeta que contiene
  `dsets/`, `recursos/` y `Ultima entrega/`). `comun.py` fija ahí el directorio de trabajo,
  así que se pueden lanzar desde cualquier carpeta.

## 2. Datos de entrada (no se modifican)

| Ruta | Uso |
|---|---|
| `recursos/clima_diario_caba_2018_2021_consolidado.csv` | clima diario (1.461 días, SHA-256 verificado) |
| `recursos/demanda_diaria_subte_2018_2021.csv` | serie de demanda diaria (1.425 días) |
| `dsets/historico_2018.csv`, `dsets/historico_2019.csv` | molinetes 15 min, usados completos |
| `dsets/historico_2020.csv`, `dsets/historico_2021.csv` | solo verificación puntual (03b) |
| `dsets/registro-historico-del-precio-del-boleto.csv` | tarifa nominal hasta 2019-04 |
| `dsets/estaciones-accesibles.csv` | lat/long para el mapa |
| `recursos/perfil_horario_estaciones_subte.csv` | solo comparación (06) |

`Subtes/` e `historico_2014-2017.csv` **no se usan**.

## 3. Orden de ejecución

```bash
cd "Metodología de la investigación"          # raíz del proyecto
NP="Ultima entrega/notebooks"

python3 $NP/02_base_analitica.py              # 3 s       -> recursos/base_analitica.parquet
python3 $NP/03_molinetes_2018_2019.py         # 264 s     -> recursos/demanda_estacion_hora_2018_2019.parquet
python3 $NP/03b_verificacion_2020_2021.py     # 294 s     -> tablas t03b_*
python3 $NP/03c_explicacion_diferencias.py    # 1 s       -> tabla t03c_*
python3 $NP/04_eda.py                         # 2 s       -> tablas t04_*
python3 $NP/05_hipotesis.py                   # 13 s      -> tablas t05_* y recursos/tarifa_complemento_manual.csv
python3 $NP/06_segmentacion_H3.py             # 26 s      -> tablas t06_*
python3 $NP/07_modelo_predictivo.py           # 37 s      -> tablas t07_* y predicciones_2019.csv
python3 $NP/09_figuras.py                     # 17 s      -> figuras fig01..fig12
```

Ejecución completa: **657 s ≈ 11 minutos** en una corrida de punta a punta (03 y 03b son los que
tardan: leen 2,4 GB y 1,1 GB respectivamente, en una sola pasada por lote de 1.000.000 de filas).

Todas las rutinas aleatorias usan `random_state=42` (constante `SEED` en `comun.py`),
porque los resultados son reproducibles de punta a punta.

## 4. Salidas

- `resultados/INFORME_RESULTADOS.md` — informe.
- `resultados/tablas/*.csv` — 36 tablas (todas las citadas en el informe).
- `resultados/figuras/figNN_*.png` — 12 figuras, 200 dpi, en español.
- `resultados/artefactos/*.parquet|csv` — residuos de M1, muestra de H2, perfiles y
  clusters, predicciones de 2019 (insumos de las figuras).
- `recursos/base_analitica.parquet` y `recursos/demanda_estacion_hora_2018_2019.parquet`
  — bases analíticas (SHA-256 listados en el informe).
- `recursos/tarifa_complemento_manual.csv` — plantilla vacía 2019-05 a 2021-12 para
  completar con las resoluciones de SBASE.

## 5. Notas

- `comun.py` es el módulo compartido (rutas, semilla, normalización de estaciones,
  escritura de tablas). Los scripts no dependen de estado entre sí salvo los archivos
  indicados en el orden anterior.
- En `03` se leen los históricos 2018-2019 con `usecols`, `dtype` y `chunksize`; no se
  cargan completos en memoria.
- Si se quiere regenerar solo las figuras: `python3 $NP/09_figuras.py`.

## 6. Cómo reproducir

Los datos crudos (`dsets/`, ~2,4 GB) no están en el repo. `datos/manifest.csv` registra
tamaño, SHA-256 y fuente de cada archivo de `dsets/` y `recursos/`, y
`descargar_datos.py --solo-verificar` los compara (OK / DISTINTO / FALTA, sin borrar nada).
Los dos `.parquet` de `recursos/` dan FALTA hasta ejecutar 02 y 03, que los generan.

### Local

```bash
git clone <REPO_URL> proyecto && cd proyecto
pip install -r "Ultima entrega/requirements.txt" gdown   # versiones exactas (Python 3.8)
python3 descargar_datos.py                               # baja dsets/ y verifica
# o copiá la carpeta de la cátedra a dsets/ y corré: python3 descargar_datos.py --solo-verificar
```

Después, los scripts en el orden de la sección 3.

### Colab con Drive

1. Copiá a tu Drive la carpeta de la cátedra
   (<https://drive.google.com/open?id=1N_upx66kxNa6MqUD40SsvJqioQLJ8jdm>).
2. Abrí `ejecutar_en_colab.ipynb` en Colab y completá `REPO_URL`.
3. En la celda de datos poné `OPCION = "A"` y en `DRIVE_DSETS` la ruta de esa copia
   (p. ej. `/content/drive/MyDrive/dsets`). El notebook monta Drive y enlaza `dsets/`.
4. Ejecutá todas las celdas.

### Colab con descarga

Igual que la anterior, pero con `OPCION = "B"`: `descargar_datos.py` baja la carpeta de la
cátedra con `gdown --folder`. Si esa descarga falla y `URL_ESPEJO_DRIVE` (en
`descargar_datos.py`) tiene una copia del grupo, intenta con esa.

En Colab se instala `requirements-colab.txt` (versiones mínimas, Python 3.10 o superior).
Con versiones más nuevas que las de `requirements.txt` los resultados pueden diferir
levemente: con pandas 3, por ejemplo, 02 marca 3 días atípicos más.
