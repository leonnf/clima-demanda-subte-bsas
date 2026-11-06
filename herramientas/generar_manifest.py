#!/usr/bin/env python3
"""Recorre dsets/ y recursos/ y escribe datos/manifest.csv.

Columnas: archivo, carpeta, tamaño_bytes, sha256, fuente, url_fuente, observaciones.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

URL_CATEDRA = "https://drive.google.com/open?id=1N_upx66kxNa6MqUD40SsvJqioQLJ8jdm"
FUENTE_CLIMA = (
    "notebook 00 (ERA5/Open-Meteo, NASA POWER, Meteostat 87582)"
)
URL_ERA5 = "https://archive-api.open-meteo.com/v1/archive"
URL_NASA = "https://power.larc.nasa.gov/api/temporal/daily/point"
URL_METEOSTAT = "https://dev.meteostat.net/bulk/hourly.html"

ROOT = Path(__file__).resolve().parents[1]
CARPETAS = ("dsets", "recursos")
SALIDA = ROOT / "datos" / "manifest.csv"


def sha256_archivo(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def metadatos(carpeta: str, nombre: str) -> tuple[str, str, str]:
    if carpeta == "dsets":
        return (
            "cátedra",
            URL_CATEDRA,
            "Datos crudos publicados por la cátedra. El respaldo del grupo va en Drive.",
        )
    if nombre == "clima_diario_caba_2018_2021_consolidado.csv":
        return (
            FUENTE_CLIMA,
            URL_ERA5,
            f"También NASA POWER ({URL_NASA}) y Meteostat estación 87582 ({URL_METEOSTAT}). "
            "El notebook 00 lo escribe; descargar_datos.py repite esa lógica si el CSV falta.",
        )
    if nombre == "demanda_diaria_subte_2018_2021.csv":
        return (
            "Ultima entrega/notebooks/03_molinetes_2018_2019.py",
            "",
            "Derivado de dsets/historico_*.csv (suma diaria de pasajeros). "
            "Ese script no lo escribe: lo recalcula y lo compara. "
            "No hay otro generador en el repositorio.",
        )
    if nombre == "perfil_horario_estaciones_subte.csv":
        return (
            "Ultima entrega/notebooks/06_segmentacion_H3.py",
            "",
            "Derivado de los molinetes (participación horaria normalizada). "
            "El notebook 01 solo lo lee. 06 reconstruye el perfil y lo compara; "
            "no hay un script que escriba este CSV.",
        )
    if nombre == "base_analitica.parquet":
        return (
            "Ultima entrega/notebooks/02_base_analitica.py",
            "",
            "Inner join de clima y demanda diaria, con fases y días atípicos.",
        )
    if nombre == "demanda_estacion_hora_2018_2019.parquet":
        return (
            "Ultima entrega/notebooks/03_molinetes_2018_2019.py",
            "",
            "Demanda por estación y hora en días hábiles de 2018 y 2019.",
        )
    if nombre == "tarifa_complemento_manual.csv":
        return (
            "Ultima entrega/notebooks/05_hipotesis.py",
            "",
            "Plantilla vacía 2019-05 a 2021-12. No trae precios inventados.",
        )
    if nombre.startswith("00_extraccion"):
        return (
            "notebook 00 del grupo",
            URL_ERA5,
            "Cuaderno (o su PDF) que arma el CSV de clima.",
        )
    if nombre.startswith("01_analisis"):
        return (
            "notebook 01 del grupo",
            "",
            "Cuaderno (o su PDF) de precipitaciones y demanda. Lee el clima, la demanda diaria y el perfil horario.",
        )
    if nombre.endswith(".png"):
        return (
            "notebook 01 del grupo",
            "",
            "Figura de apoyo del análisis de precipitaciones.",
        )
    return ("recursos del grupo", "", "")


def archivos() -> list[Path]:
    encontrados: list[Path] = []
    for carpeta in CARPETAS:
        base = ROOT / carpeta
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.name.startswith(".~") or path.name.startswith("."):
                continue
            encontrados.append(path)
    return sorted(encontrados, key=lambda p: (p.parent.name, p.name.lower()))


def main() -> None:
    filas = []
    for path in archivos():
        carpeta = path.relative_to(ROOT).parts[0]
        fuente, url, obs = metadatos(carpeta, path.name)
        filas.append({
            "archivo": path.name,
            "carpeta": str(path.parent.relative_to(ROOT)),
            "tamaño_bytes": path.stat().st_size,
            "sha256": sha256_archivo(path),
            "fuente": fuente,
            "url_fuente": url,
            "observaciones": obs,
        })
        print(f"[hash] {carpeta}/{path.name}  {filas[-1]['tamaño_bytes']} bytes")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(filas, columns=[
        "archivo", "carpeta", "tamaño_bytes", "sha256",
        "fuente", "url_fuente", "observaciones",
    ]).to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"[manifiesto] {SALIDA}  ({len(filas)} archivos)")


if __name__ == "__main__":
    main()
