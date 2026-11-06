#!/usr/bin/env python3
"""Descarga los datos de la cátedra y los verifica contra datos/manifest.csv.

Orden:
1. Carpeta de la cátedra con gdown, a dsets/. Si falla y URL_ESPEJO_DRIVE
   tiene una copia del grupo, se intenta esa.
2. Si falta el CSV de clima, avisa: se regenera con el notebook 00.
3. Cada archivo del manifiesto se marca OK, DISTINTO o FALTA.
   Un archivo DISTINTO se avisa y no se borra.

--solo-verificar chequea los hashes y no descarga nada.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

URL_CATEDRA = "https://drive.google.com/open?id=1N_upx66kxNa6MqUD40SsvJqioQLJ8jdm"
# Copia del grupo. Vacía hasta que exista un espejo propio.
URL_ESPEJO_DRIVE = ""

ROOT = Path(__file__).resolve().parent
# Misma regla que comun.DATA_DIR: la raíz del proyecto, o la carpeta indicada
# por la variable de entorno (debe contener dsets/ y recursos/).
DATA_DIR = Path(os.environ.get("DATA_DIR", ROOT)).expanduser().resolve()
DSETS = DATA_DIR / "dsets"
RES = DATA_DIR / "recursos"

MANIFIESTO = ROOT / "datos" / "manifest.csv"
CLIMA = RES / "clima_diario_caba_2018_2021_consolidado.csv"


def sha256_archivo(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def aplanar(destino: Path) -> None:
    """gdown a veces crea una subcarpeta con el nombre de Drive. La sube un nivel."""
    if (destino / "historico_2018.csv").exists() or (destino / "estaciones-accesibles.csv").exists():
        return
    subdirs = [p for p in destino.iterdir() if p.is_dir()]
    if len(subdirs) != 1:
        return
    sub = subdirs[0]
    for item in list(sub.iterdir()):
        target = destino / item.name
        if target.exists():
            print(f"  no se mueve {item.name}: ya existe y no se pisa")
            continue
        item.rename(target)
    try:
        sub.rmdir()
    except OSError:
        pass


def descargar_carpeta(url: str, destino: Path) -> None:
    if not url.strip():
        raise RuntimeError("la URL está vacía")
    destino.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "gdown", "--folder", url, "--output", str(destino)]
    print(" ", " ".join(cmd))
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        raise RuntimeError(f"gdown terminó con código {proc.returncode}")
    aplanar(destino)


def descargar_catedra() -> None:
    print(f"Descargando la carpeta de la cátedra en {DSETS}")
    print("Los archivos que ya existen no se borran.")
    try:
        descargar_carpeta(URL_CATEDRA, DSETS)
        return
    except Exception as exc:
        print(f"Falló la descarga de la cátedra: {exc}")
    if not URL_ESPEJO_DRIVE.strip():
        print("URL_ESPEJO_DRIVE está vacía: no hay copia del grupo para intentar.")
        return
    print(f"Intentando el espejo del grupo: {URL_ESPEJO_DRIVE}")
    try:
        descargar_carpeta(URL_ESPEJO_DRIVE, DSETS)
    except Exception as exc:
        print(f"También falló el espejo: {exc}")


def verificar() -> int:
    import pandas as pd

    if not MANIFIESTO.is_file():
        print(f"FALTA el manifiesto: {MANIFIESTO}")
        return 1
    man = pd.read_csv(MANIFIESTO)
    print(f"DATA_DIR = {DATA_DIR}")
    print(f"{'estado':<10} {'archivo'}")
    ok = distinto = falta = 0
    for row in man.itertuples(index=False):
        path = DATA_DIR / row.carpeta / row.archivo
        if not path.is_file():
            falta += 1
            print(f"{'FALTA':<10} {row.carpeta}/{row.archivo}")
            continue
        digest = sha256_archivo(path)
        if digest == row.sha256:
            ok += 1
            print(f"{'OK':<10} {row.carpeta}/{row.archivo}")
            continue
        distinto += 1
        print(f"{'DISTINTO':<10} {row.carpeta}/{row.archivo}")
        print(f"  AVISO: {path} no coincide con el manifiesto. No se borra nada.")
        print(f"  manifiesto: {row.sha256}")
        print(f"  disco:      {digest}")
    print(f"\nOK={ok}  DISTINTO={distinto}  FALTA={falta}  (de {len(man)})")
    return 0 if distinto == 0 and falta == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Descarga y verifica los datos del proyecto.")
    parser.add_argument(
        "--solo-verificar",
        action="store_true",
        help="Compara los archivos con el manifiesto, sin descargar.",
    )
    args = parser.parse_args(argv)
    if args.solo_verificar:
        print("Solo verificación: no se descarga nada.")
    else:
        descargar_catedra()
        if CLIMA.is_file():
            print(f"El CSV de clima ya está: {CLIMA}")
        else:
            print(f"AVISO: falta el CSV de clima ({CLIMA}).")
            print("  Se regenera ejecutando recursos/00_extraccion_y_curacion_datos_climaticos.ipynb.")
    return verificar()


if __name__ == "__main__":
    sys.exit(main())
