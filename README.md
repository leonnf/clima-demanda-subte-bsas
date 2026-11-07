# Incidencia de las condiciones climáticas en la demanda de pasajeros del subte de Buenos Aires (2018–2021)

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/leonnf/clima-demanda-subte-bsas/blob/main/ejecutar_en_colab.ipynb)

Trabajo Final Integrador — Metodología de la Investigación, Licenciatura en Ciencia de Datos, Universidad del Gran Rosario, 2026.

Este proyecto estudia si el clima influye en cuánta gente usa el subte de Buenos Aires. Cruza la demanda diaria de pasajeros (2018–2021) con temperatura y lluvia, y estima ese efecto separando lo que se debe al calendario, a la estacionalidad, a la pandemia y a la tarifa. Los resultados se contrastan además con modelos predictivos entrenados con y sin variables climáticas. Todas las tablas y figuras se regeneran con scripts numerados, y las cifras del informe pueden contrastarse con esas tablas.

## 1. Pregunta de investigación y objetivos

**Pregunta.** ¿En qué medida la temperatura media diaria y la ocurrencia de lluvia significativa se asocian con la demanda diaria de pasajeros del subte de Buenos Aires entre 2018 y 2021, una vez controlados el tipo de día, la estacionalidad mensual, el nivel tarifario, las fases de la pandemia y los días atípicos? De manera complementaria, ¿en qué medida el clima mejora la predicción de esa demanda?

**Objetivo general.** Analizar la relación entre las condiciones climáticas diarias (temperatura y precipitación) y la demanda de pasajeros del subte de Buenos Aires entre 2018 y 2021, separándola del efecto del calendario, la estacionalidad, la pandemia y la tarifa, y evaluar su utilidad para predecir la demanda.

**Objetivos específicos.**

1. Normalizar y unificar los registros de molinetes 2018–2021 y validar la serie de demanda.
2. Construir la base climática diaria (ERA5, NASA POWER, SABA) y validar sus fuentes.
3. Construir las variables de control (feriados, fases COVID, días atípicos, efectos fijos año-mes) y la serie de tarifas.
4. Estimar el efecto de la temperatura (H1).
5. Evaluar el efecto refugio ante la lluvia (H2).
6. Segmentar las estaciones por perfil horario (H3).
7. Contrastar la robustez con la tarifa.
8. Comunicar los hallazgos con visualizaciones reproducibles.
9. Comparar modelos predictivos con y sin clima, fuera de muestra.

## 2. Hipótesis y resultados

| Hipótesis | Resultado | Evidencia clave |
|---|---|---|
| **H1** — Con más frío hay más demanda | **Parcialmente sostenida** | −3.892 pasajeros/°C en 2018–2019 (p = 0,014); no significativa en 2018–2021 (p = 0,66) |
| **H2** — Ante lluvia ≥ 5 mm hay efecto refugio | **No sostenida: efecto opuesto** | −45.637 pasajeros; d de Cohen = −0,35 |
| **H3** — Las estaciones tienen perfiles horarios distintos | **Sostenida (exploratoria)** | K = 4, silueta 0,495 |
| **Predicción** — El clima mejora la predicción | **Mejora marginal** | Random Forest es el mejor modelo (RMSE 102.572 en 2019, R² 0,943); el clima reduce el RMSE un 2,1 % en la regresión |

La serie de demanda coincide con los molinetes en 2018–2019, pero no en 2020–2021, por errores de fecha en los archivos fuente.

## 3. Estructura del repositorio

```
.
├── README.md                        # este documento
├── ejecutar_en_colab.ipynb          # reproducción completa en Colab
├── descargar_datos.py               # descarga y verificación de datos crudos
├── requirements-colab.txt           # dependencias para Colab
├── datos/manifest.csv               # manifiesto SHA-256 de los archivos de datos
├── herramientas/                    # generador del manifiesto
├── recursos/                        # insumos curados y notebooks previos
│   ├── clima_diario_caba_2018_2021_consolidado.csv
│   ├── demanda_diaria_subte_2018_2021.csv
│   ├── 00_extraccion_y_curacion_datos_climaticos.ipynb
│   └── 01_analisis_precipitaciones_y_demanda_subte.ipynb
└── Ultima entrega/                  # entrega final del trabajo
    ├── README.md                    # requisitos, orden de ejecución y salidas
    ├── requirements.txt             # versiones originales (Python 3.8)
    ├── notebooks/                   # scripts 02 → 09 + comun.py
    └── resultados/
        ├── INFORME_RESULTADOS.md    # informe técnico de resultados
        ├── tablas/                  # 36 tablas CSV
        ├── figuras/                 # 12 figuras PNG
        └── artefactos/              # insumos de las figuras
```

## 4. Datos

| Fuente | Uso | Enlace |
|---|---|---|
| Molinetes del subte (BA Data) | Demanda diaria y por estación y hora | <https://data.buenosaires.gob.ar/dataset/subte-viajes-molinetes> (provistos por la cátedra) |
| ERA5 vía Open-Meteo | Temperatura y precipitación diaria | <https://open-meteo.com/> |
| NASA POWER | Contraste de la serie climática | <https://power.larc.nasa.gov/> |
| Meteostat (estación 87582, Aeroparque) | Validación de la serie climática | <https://meteostat.net/> |
| Registro histórico del precio del boleto | Nivel tarifario (hasta abril de 2019) | Provisto por la cátedra |

Los datos crudos (`dsets/`, 3,4 GB) **no están en el repo**. Se descargan con `python3 descargar_datos.py` y se verifican contra `datos/manifest.csv` (tamaño y SHA-256). El modo `--solo-verificar` compara los archivos presentes (OK / DISTINTO / FALTA) sin descargar nada.

## 5. Cómo reproducir

### Opción A — Colab (la más simple, sin instalar nada)

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/leonnf/clima-demanda-subte-bsas/blob/main/ejecutar_en_colab.ipynb)

Abrir el notebook y ejecutar *Entorno de ejecución → Ejecutar todas*. No requiere cuentas ni credenciales.

1. Clona el repositorio.
2. Instala las dependencias faltantes (pandas 2.x, holidays, gdown).
3. Descarga `dsets/` desde una copia pública en Google Drive (`FUENTE = "espejo_grupo"`) o desde la carpeta de la cátedra (`FUENTE = "catedra"`).
4. Verifica los datos contra el manifiesto. Los Parquet aparecen como FALTA hasta el paso 5.
5. Ejecuta los scripts 02 a 09 en orden.
6. Compara las tablas generadas con las del repositorio (`git diff`).
7. Muestra las figuras principales.

Tiempo de ejecución: unos 5 minutos.

### Opción B — Local

```bash
git clone https://github.com/leonnf/clima-demanda-subte-bsas.git
cd clima-demanda-subte-bsas
python3 -m venv .venv && source .venv/bin/activate
pip install -r "Ultima entrega/requirements.txt"     # versiones originales, Python 3.8

python3 descargar_datos.py                           # baja dsets/ y verifica
python3 descargar_datos.py --solo-verificar          # solo verifica

NP="Ultima entrega/notebooks"
python3 "$NP/02_base_analitica.py"
python3 "$NP/03_molinetes_2018_2019.py"
python3 "$NP/03b_verificacion_2020_2021.py"
python3 "$NP/03c_explicacion_diferencias.py"
python3 "$NP/04_eda.py"
python3 "$NP/05_hipotesis.py"
python3 "$NP/06_segmentacion_H3.py"
python3 "$NP/07_modelo_predictivo.py"
python3 "$NP/09_figuras.py"
```

Corrida completa: unos 11 minutos (657 s) y unos 8 GB de disco libres. Todas las rutinas aleatorias usan `random_state = 42`. Detalles en `Ultima entrega/README.md`.

### Opción C — Notebooks previos

- `recursos/00_extraccion_y_curacion_datos_climaticos.ipynb` regenera la base climática (requiere internet).
- `recursos/01_analisis_precipitaciones_y_demanda_subte.ipynb` es el análisis de la segunda entrega, conservado como referencia.

## 6. Reproducibilidad y versiones

Los resultados del informe se obtuvieron con Python 3.8 y las versiones fijadas en `Ultima entrega/requirements.txt`. La reproducción en Colab (Python 3.13, pandas 2.2, scikit-learn 1.6) mantiene todas las conclusiones, con estas diferencias:

| Cifra | Original (Python 3.8) | Colab (Python 3.13) |
|---|---|---|
| β temperatura, modelo M5 (2018–2019) | −3.892 | −3.902 |
| d de Cohen de H2 | −0,351 | −0,351 |
| RMSE de Random Forest | 102.572 | 103.540 |
| Días atípicos detectados | 35 | 37 |
| RMSE de HistGradientBoosting | 234.516 | 126.393 |

*Nota:* el desempeño de HistGradientBoosting depende mucho de la versión de scikit-learn. Random Forest sigue siendo el mejor modelo en ambas corridas.

## 7. Resultados

- **Tablas:** `Ultima entrega/resultados/tablas/` (36 CSV citados en el informe).
- **Figuras:** `Ultima entrega/resultados/figuras/` (12 PNG, 200 dpi, en español).
- **Informe técnico:** `Ultima entrega/resultados/INFORME_RESULTADOS.md`.

![Coeficientes de temperatura y lluvia por especificación](Ultima%20entrega/resultados/figuras/fig06_forest_plot_especificaciones.png)

![Perfiles horarios por cluster de estaciones](Ultima%20entrega/resultados/figuras/fig10_perfiles_por_cluster.png)

## 8. Limitaciones principales

- Los datos de demanda 2020–2021 no pudieron validarse contra los molinetes (errores de fecha en los archivos fuente).
- El diseño es observacional: las asociaciones estimadas no implican causalidad.
- Los molinetes cuentan validaciones de tarjeta, no personas.
- La serie tarifaria llega hasta abril de 2019, por lo que el control con tarifa se limita a enero 2018 – abril 2019.
- Los días atípicos detectados estadísticamente no están confirmados como paros o incidentes.

## 9. Autores

**Grupo 36:** Marco Fouad Abboud, Matías Gabriel Gallardo, Néstor Fabián León y Sebastián Luna.

**Cátedra:** Lic. María Cecilia Ribecco, Ing. Matías Agustín Pérez y Lic. Samira Elizabeth Robador Papich.

## 10. Uso de IA

Se usaron herramientas de IA generativa como apoyo a la programación y la redacción, conforme a la guía de la UGR. Las cifras provienen de código ejecutado y revisado por el equipo.

## 11. Licencia

Pendiente de definir por el grupo. Los datos conservan las licencias de sus fuentes.
