"""Rutas del artículo A2. Ninguna ruta absoluta: todo se resuelve desde la raíz del repositorio.

La raíz es la primera carpeta, subiendo desde este archivo, que contiene `src/cierre_parto/` (o la variable de entorno
RAIZ, si está fijada). Debajo de ella:

    data/raw/                 insumos originales y MANIFIESTO.csv (externos del artículo en data/raw/externos/)
    data/processed/           bases de Estadísticas Vitales del paquete común (nivel B; no se versionan)
    data/interim/62/          cachés del nivel B (agregados por año, atributos completos)
    data/intermedios/         paneles agregados versionados: punto de partida del nivel A
    output/                   resultados.json, tablas/ y figuras/
"""
from __future__ import annotations

import os
from pathlib import Path


def _raiz() -> Path:
    if os.environ.get("RAIZ"):
        return Path(os.environ["RAIZ"]).resolve()
    for p in Path(__file__).resolve().parents:
        if (p / "src" / "cierre_parto").is_dir():
            return p
    raise RuntimeError("No encuentro la raíz del repositorio (carpeta con src/cierre_parto/).")


RAIZ = _raiz()
RAW = RAIZ / "data" / "raw"
X52 = RAW / "externos" / "52"          # insumos vendorizados del estudio 52 (DIVIPOLA, REPS 2022, IDEAM)
X62 = RAW / "externos" / "62"          # insumos propios del artículo
# las bases del paquete común pueden estar en otra carpeta (variable de entorno PROCESADO), p. ej. una reconstrucción
# ya verificada; por defecto, data/processed/ de este repositorio
PROC = Path(os.environ["PROCESADO"]).resolve() if os.environ.get("PROCESADO") else RAIZ / "data" / "processed"
EXT = PROC / "ext"
CACHE = RAIZ / "data" / "interim" / "62"
INTERMEDIOS = RAIZ / "data" / "intermedios"
CONFIG = RAIZ / "config"
OUT = RAIZ / "output"


def relativa(p: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(RAIZ))
    except ValueError:
        return Path(p).name
