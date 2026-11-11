#!/usr/bin/env python3
"""Nivel B, etapa 3. Atributos fijos de cada municipio: departamento y nombre (DIVIPOLA), altitud (estación del IDEAM
más cercana), PDET y ZOMAC (config/), salas de partos del REPS 2022 y distancia al otro municipio más cercano con 365 o
más partos institucionales al año. Salida: data/interim/62/atributos.parquet. Función: cierre_parto.panel.atributos().
"""
import time

import _entorno  # noqa: F401
from cierre_parto.armonizacion import coordenadas
from cierre_parto.panel import atributos, nacimientos
from cierre_parto.rutas import CACHE

if __name__ == "__main__":
    t0 = time.time()
    co = coordenadas()
    atributos(nacimientos(co), co).write_parquet(CACHE / "atributos.parquet")
    print(f"atributos listos ({time.time() - t0:.0f} s)")
