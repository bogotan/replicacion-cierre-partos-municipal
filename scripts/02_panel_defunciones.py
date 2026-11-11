#!/usr/bin/env python3
"""Nivel B, etapa 2. Defunciones de menores de un año por municipio de residencia y año (subgrupos de edad, lugar de
ocurrencia, sitio) y población de 0 años y total por municipio y año.

Entradas: data/processed/defunciones_eevv.parquet, data/processed/ext/def_<año>.parquet y
data/processed/mun_pob_edad.parquet (paquete común). Salidas: data/interim/62/defunciones.parquet y poblacion.parquet.
Funciones: cierre_parto.panel.defunciones() y poblacion().
"""
import time

import _entorno  # noqa: F401
from cierre_parto.panel import defunciones, poblacion
from cierre_parto.rutas import CACHE

if __name__ == "__main__":
    t0 = time.time()
    CACHE.mkdir(parents=True, exist_ok=True)
    defunciones().write_parquet(CACHE / "defunciones.parquet")
    poblacion().write_parquet(CACHE / "poblacion.parquet")
    print(f"defunciones y población listas ({time.time() - t0:.0f} s)")
