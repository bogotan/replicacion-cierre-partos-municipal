#!/usr/bin/env python3
"""Nivel B, etapa 1. Agrega los nacidos vivos 1998–2025 por municipio de residencia de la madre (y los partos
institucionales por municipio de ocurrencia), un archivo por año en data/interim/62/mun_<año>.parquet.

Entrada: data/processed/ext/nac_<año>.parquet (paquete común: scripts/insumos_eevv/03_base_nacimientos.py) y la DIVIPOLA
con coordenadas (data/raw/externos/52/). Función: cierre_parto.panel.agregar_anio().
"""
import argparse
import time

import _entorno  # noqa: F401
from cierre_parto.armonizacion import coordenadas
from cierre_parto.panel import nacimientos
from cierre_parto.rutas import CACHE


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rehacer", action="store_true", help="ignora la caché de data/interim/62/")
    a = ap.parse_args()
    t0 = time.time()
    CACHE.mkdir(parents=True, exist_ok=True)
    nacimientos(coordenadas(), usar_cache=not a.rehacer)
    print(f"nacimientos listos ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
