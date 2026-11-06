# Contexto para IA: Trabajo Final Integrador - Metodología de la Investigación

## Asignatura
**Metodología de la Investigación** - Licenciatura en Ciencias de Datos

---

## Objetivo del Trabajo
Aplicar los conocimientos de metodología de investigación a un proyecto concreto de análisis de datos de la **red de Subtes de Buenos Aires**.

---

## Dos Caminos Disponibles

### Opción A: Analítica de Datos
- **Enfoque:** Análisis exploratorio, limpieza y visualización
- **Herramientas:** Power BI, Plotly, Tableau, Dash, Looker Studio
- **Etapas:** EDA → Limpieza/Transformación → Dashboards e Insights
- **Perfil:** Menos código predictivo, más storytelling y visualización

### Opción B: Ciencia de Datos
- **Enfoque:** Modelado predictivo con Machine Learning
- **Herramientas:** Python (scikit-learn, TensorFlow, etc.)
- **Etapas:** EDA → Limpieza/Transformación → Modelado ML
- **Perfil:** Más código, métricas de modelos, comparación de algoritmos

---

## Datasets Disponibles

### 1. historico_2019.csv
- **Registros:** ~12,662,344 filas
- **Separador:** coma `,`
- **Columnas:** `periodo, fecha, desde, hasta, linea, molinete, estacion, pax_pagos, pax_pases_pagos, pax_franq, total`
- **NOTA:** Columnas en minúscula. Campo `periodo` (ej: 201901) y `fecha` (formato YYYY-MM-DD). Columna total se llama `total` (no `pax_TOTAL`).
- **Periodo:** Año 2019 completo

### 2. historico_2020.csv
- **Registros:** ~5,781,007 filas
- **Separador:** coma `,`
- **Columnas:** `FECHA, DESDE, HASTA, LINEA, MOLINETE, ESTACION, pax_pagos, pax_pases_pagos, pax_franq, pax_TOTAL`
- **NOTA:** Columnas en MAYÚSCULA. Sin campo `periodo`. Fecha formato DD/MM/YYYY. Columna total se llama `pax_TOTAL`.
- **Periodo:** Año 2020 completo (menos datos por pandemia)

### 3. historico_2021.csv
- **Registros:** ~8,071,681 filas
- **Separador:** punto y coma `;`
- **Columnas:** `periodo; FECHA; DESDE; HASTA; LINEA; MOLINETE; ESTACION; pax_pagos; pax_pases_pagos; pax_franq; pax_TOTAL`
- **NOTA:** Separador punto y coma. Tiene campo `periodo` (ej: 2021). Columnas en MAYÚSCULA.
- **Periodo:** Año 2021 completo

### 4. BaseUnificadaEstaciones.csv
- **Registros:** ~822,364 filas
- **Columnas:** `FECHA, ESTACION, LINEA, DESDE, HORA, CANTIDAD`
- **Descripción:** Pasajeros por estación, línea y franja horaria (cada 15 min)
- **Periodo:** Año 2020 (desde marzo)
- **Uso:** Análisis de demanda por hora/estación, patrones de uso

### 5. estaciones-accesibles.csv
- **Registros:** ~93 filas
- **Columnas:** `long, lat, linea, estacion, escaleras_mecanicas, ascensores`
- **Descripción:** Geolocalización y accesibilidad de estaciones
- **Uso:** Análisis de accesibilidad, mapas geográficos

### 6. lineas-de-subte.csv
- **Registros:** ~82 filas
- **Columnas:** `wkt, id, lineasub`
- **Descripción:** Geometrías WKT de las líneas de subte (MULTILINESTRING)
- **Uso:** Visualización geoespicial, mapas de las líneas

### 7. registro-historico-del-precio-del-boleto.csv
- **Registros:** ~305 filas
- **Columnas:** `año, mes_numero, mes, precio`
- **Descripción:** Evolución del precio del boleto desde 1994
- **Periodo:** 1994 - ~2024
- **Uso:** Análisis de inflación tarifaria, correlación precio-demanda

### 8. viajes_anual.csv
- **Registros:** ~48 filas
- **Columnas:** `year, LINEA, total`
- **Descripción:** Total de viajes anuales por línea
- **Periodo:** 2013 - 2020
- **Uso:** Tendencias anuales, comparación entre líneas

### 9. registro-historico-del-precio-del-boleto.xlsx
- **Descripción:** Versión Excel del registro de precios (mismos datos que CSV)

---

## ⚠️ IMPORTANTE: Inconsistencia en archivos históricos

Los tres archivos `historico_YYYY.csv` tienen **estructura diferente**:

| Característica | 2019 | 2020 | 2021 |
|----------------|------|------|------|
| Separador | `,` | `,` | `;` |
| Case columnas | minúscula | MAYÚSCULA | MAYÚSCULA |
| Campo `periodo` | Sí (ej: 201901) | No | Sí (ej: 2021) |
| Campo `fecha` | Sí (YYYY-MM-DD) | `FECHA` (DD/MM/YYYY) | `FECHA` (D/M/YYYY) |
| Columna total | `total` | `pax_TOTAL` | `pax_TOTAL` |
| Filas | ~12.6M | ~5.8M | ~8.1M |

**Se requiere normalización/estandarización antes de unificar los datos.**

---

## Estructura del Trabajo (Ambos Enfoques)

1. **Introducción** - Problema, justificación, objetivos
2. **Marco Teórico** - Metodología + conceptos de transporte/movilidad
3. **Metodología** - Diseño cuantitativo, etapas de análisis
4. **Propuesta de Solución** - Resultados, hipótesis contrastadas
5. **Conclusiones** - Reflexión final
6. **Bibliografía** - Fuentes citadas
7. **Anexo** - Código, tablas, visualizaciones

---

## Hipótesis Orientativas

- H1: Estaciones céntricas concentran mayor pasajeros en horas pico
- H2: Relación negativa entre aumentos de tarifa y pasajeros
- H3: Diferencia significativa entre días hábiles y fines de semana
- H4: Dashboards (Analítica) / Modelos (Ciencia) permiten mejor comunicación/predicción

---

## Requisitos para Aprobar

### Entrega Parcial (30%)
- Título del proyecto
- Problema a abordar
- Objetivo general
- Objetivos específicos (múltiples)
- Hipótesis inicial

### Entrega Final
- **Extensión:** Máximo 50 páginas (incluyendo anexos)
- **Formato:** PDF + link a video de defensa
- **Video:** Máximo 10 minutos presentando:
  - Objetivo del trabajo
  - Proceso seguido (etapas)
  - Dashboard o Modelos desarrollados
  - Conclusiones y recomendaciones

### Grupo
- Equipos de 4 a 6 integrantes (máximo 5 según consigna final)
- Trabajo grupal, entrega única

### Criterios Clave
1. **Metodología:** Aplicar correctamente los conceptos de la materia
2. **Exploración:** EDA completo con estadísticas descriptivas y visualizaciones
3. **Limpieza:** Documentar proceso ETL (valores faltantes, outliers, normalización)
4. **Análisis:** Profundidad según el camino elegido (dashboards o modelos)
5. **Hipótesis:** Formular y contrastar claramente
6. **Documentación:** Bibliografía completa, código documentado en anexo
7. **Comunicación:** Defensa oral clara y concisa (10 min máximo)

---

## Notas Adicionales
- Los datos de 2020 son significativamente menores (año pandemia) - considerar en análisis
- 2019 tiene el mayor volumen (~12.6M filas) como línea base pre-pandemia
- 2021 muestra recuperación post-pandemia (~8.1M filas)
- Se pueden usar datos complementarios del portal de datos abiertos de GCBA
- La accesibilidad de estaciones puede ser un ángulo interesante para el problema
