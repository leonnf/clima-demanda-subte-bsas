"""Utilidades compartidas por los scripts 02-07 de la última entrega.

Uso:  from comun import BASE, RES, RES_TAB, guardar_tabla
"""
from __future__ import annotations

import os
import pathlib

import pandas as pd

SEED = 42

BASE = pathlib.Path(__file__).resolve().parents[2]   # raiz del proyecto
# Carpeta con dsets/ y recursos/. Por defecto, la raíz del proyecto.
DATA_DIR = pathlib.Path(os.environ.get("DATA_DIR", BASE)).expanduser().resolve()
RES = DATA_DIR / "recursos"
DSETS = DATA_DIR / "dsets"
# Los scripts usan rutas relativas a la raíz ("recursos/...", "Ultima entrega/...").
os.chdir(BASE)
ENTREGA = BASE / "Ultima entrega"
RES_DIR = ENTREGA / "resultados"
RES_TAB = RES_DIR / "tablas"
RES_FIG = RES_DIR / "figuras"
RES_ART = RES_DIR / "artefactos"

for _p in (RES_TAB, RES_FIG, RES_ART):
    _p.mkdir(parents=True, exist_ok=True)

MESES = {1: "ENE", 2: "FEB", 3: "MAR", 4: "ABR", 5: "MAY", 6: "JUN",
         7: "JUL", 8: "AGO", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DIC"}
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def guardar_tabla(df: pd.DataFrame, nombre: str) -> pathlib.Path:
    """Escribe una tabla en resultados/tablas/ y devuelve la ruta."""
    p = RES_TAB / f"{nombre}.csv"
    df.to_csv(p, index=False, encoding="utf-8")
    print(f"[tabla] {p.name}  ({len(df)} filas)")
    return p


def reparar_encoding(s: str) -> str:
    """Repara mojibake (UTF-8 leído como Latin-1, 1 o 2 veces) en nombres."""
    if not isinstance(s, str):
        return s
    for _ in range(3):
        if not any(c in s for c in ("Ã", "Â", "\x83")):
            break
        try:
            s2 = s.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        if s2 == s:
            break
        s = s2
    return s


def norm_estacion(s: str) -> str:
    """Normaliza nombres de estación: repara encoding, mayúsculas, sin espacios raros."""
    if not isinstance(s, str):
        return s
    s = reparar_encoding(s).strip()
    return " ".join(s.upper().split())


def fold_ascii(s: str) -> str:
    """Pliega a ASCII eliminando los caracteres no-ASCII (para cruzar fuentes)."""
    if not isinstance(s, str):
        return s
    return "".join(c for c in s if ord(c) < 128).strip()


def norm_linea(s: str) -> str:
    """Normaliza la línea a una letra A-H."""
    if not isinstance(s, str):
        return s
    t = norm_estacion(s).replace("LINEA", "").replace("_", "").strip()
    t = t.replace(" ", "")
    return t[:1] if t else s
