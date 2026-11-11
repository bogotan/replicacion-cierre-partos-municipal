#!/usr/bin/env python3
"""Nivel A, etapa 6. Todas las estimaciones del artículo desde data/intermedios/: output/resultados.json y
output/tablas/*.csv. Función: cierre_parto.estimacion.estimar(). Semilla 20261024. Unos 2 minutos con 2 núcleos.
"""
import warnings

import _entorno  # noqa: F401
from cierre_parto.estimacion import estimar

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    estimar()
