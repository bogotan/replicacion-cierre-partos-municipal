#!/usr/bin/env python3
"""Compara los intermedios reconstruidos en el nivel B con los versionados: mismas filas, columnas y valores (tras ordenar;
tolerancia 1e-9 en decimales) y mismos agregados del nivel B.

    python scripts/05_comparar_intermedios.py --nuevo data/interim/62/intermedios_b --referencia data/intermedios
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import polars as pl

import _entorno  # noqa: F401
from cierre_parto.rutas import RAIZ


def _ruta(x):
    p = Path(x)
    return p if p.is_absolute() else RAIZ / p


def comparar_parquet(a: Path, b: Path) -> list[str]:
    A, B = pl.read_parquet(a), pl.read_parquet(b)
    if A.columns != B.columns:
        return [f"{a.name}: columnas distintas"]
    if A.height != B.height:
        return [f"{a.name}: {A.height} filas frente a {B.height}"]
    claves = [c for c in ("mun", "anio") if c in A.columns]
    A, B = A.sort(claves), B.sort(claves)
    fallas = []
    for c in A.columns:
        x, y = A[c], B[c]
        if x.dtype.is_numeric() and y.dtype.is_numeric():
            xv, yv = x.cast(pl.Float64).to_numpy(), y.cast(pl.Float64).to_numpy()
            mismo_nulo = np.array_equal(np.isnan(xv), np.isnan(yv))
            if not mismo_nulo or np.nanmax(np.abs(np.nan_to_num(xv - yv)) / np.maximum(1, np.abs(np.nan_to_num(yv)))) > 1e-9:
                fallas.append(f"{a.name}: columna {c} distinta")
        elif not x.equals(y):
            fallas.append(f"{a.name}: columna {c} distinta")
    return fallas


def comparar_json(a: Path, b: Path) -> list[str]:
    def plano(o, p=""):
        if isinstance(o, dict):
            for k, v in o.items():
                yield from plano(v, f"{p}/{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                yield from plano(v, f"{p}[{i}]")
        else:
            yield p, o
    A, B = dict(plano(json.loads(a.read_text()))), dict(plano(json.loads(b.read_text())))
    if A.keys() != B.keys():
        return [f"{a.name}: claves distintas"]
    fallas = []
    for k in A:
        x, y = A[k], B[k]
        if isinstance(x, float) and isinstance(y, float):
            if abs(x - y) > 1e-9 * max(1.0, abs(y)):
                fallas.append(f"{a.name}{k}: {x} frente a {y}")
        elif x != y:
            fallas.append(f"{a.name}{k}: {x} frente a {y}")
    return fallas


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--nuevo", required=True)
    ap.add_argument("--referencia", default="data/intermedios")
    a = ap.parse_args()
    nuevo, ref = _ruta(a.nuevo), _ruta(a.referencia)
    fallas = []
    for f in sorted(ref.iterdir()):
        g = nuevo / f.name
        if not g.exists():
            fallas.append(f"falta {f.name}"); continue
        fallas += comparar_parquet(g, f) if f.suffix == ".parquet" else comparar_json(g, f)
        print(f"  {'igual' if not fallas else '…'}  {f.name}")
    if fallas:
        print("DIFERENCIAS:"); [print(" -", x) for x in fallas]
        sys.exit(1)
    print("Los intermedios reconstruidos coinciden con los versionados.")


if __name__ == "__main__":
    main()
