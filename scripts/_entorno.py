"""Arranque común de los scripts del artículo: fija el entorno para que las corridas sean deterministas y pone src/ en
el camino de importación. Sin rutas absolutas.

Determinismo. pyfixest arma internamente conjuntos de nombres de columnas cuyo orden depende de la semilla de hash de
Python; con semillas distintas, los modelos de Poisson, Sun y Abraham y el TWFE dinámico cambiaban hasta en 6,3e-7 entre
corridas (docs/REPLICACION.md, sección 2). Si PYTHONHASHSEED no vale 0, el script se vuelve a lanzar con PYTHONHASHSEED=0.
Además se fija un solo hilo en numba y BLAS, por precaución ante máquinas con otro número de núcleos.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

for _v in ("NUMBA_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable] + sys.argv)

_SRC = next(p / "src" for p in Path(__file__).resolve().parents if (p / "src" / "cierre_parto").is_dir())
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
