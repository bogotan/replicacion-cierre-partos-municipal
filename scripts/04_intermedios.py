#!/usr/bin/env python3
"""Nivel B, etapa 4. Ensambla el panel municipio-año completo y escribe los intermedios publicables del nivel A:

    panel_municipio_anio.parquet   panel con las celdas de 1 a 4 suprimidas en etn, d_inf_dom, d_neo_fuera y d_inf_fuera
    atributos_municipio.parquet    atributos fijos y la marca etnico20 (20 % o más de nacimientos étnicos en 2008–2011)
    agregados_nivel_b.json         cifras que necesitan las celdas suprimidas, calculadas con el panel completo
    panel_info.json                totales de control (nacimientos y defunciones por año, celdas suprimidas)

Por defecto escribe en data/intermedios/; con --salida, en otra carpeta (para compararla con la versionada). El panel
completo queda solo en data/interim/62/completo/ (no se versiona).
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import polars as pl

import _entorno  # noqa: F401
from cierre_parto.armonizacion import coordenadas
from cierre_parto.constantes import COLS_SUPRIMIDAS
from cierre_parto.estimacion import agregados_nivel_b
from cierre_parto.panel import ensamblar, nacimientos, suprimir
from cierre_parto.rutas import CACHE, INTERMEDIOS, RAIZ


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", default=str(INTERMEDIOS))
    a = ap.parse_args()
    salida = Path(a.salida) if Path(a.salida).is_absolute() else RAIZ / a.salida
    salida.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    co = coordenadas()
    P = ensamblar(nacimientos(co), pl.read_parquet(CACHE / "defunciones.parquet"), pl.read_parquet(CACHE / "poblacion.parquet"), co)
    A = pl.read_parquet(CACHE / "atributos.parquet")
    completo = CACHE / "completo"; completo.mkdir(parents=True, exist_ok=True)
    P.write_parquet(completo / "panel_municipio_anio.parquet"); A.write_parquet(completo / "atributos_municipio.parquet")
    ag, etn20 = agregados_nivel_b(completo)
    Ps = suprimir(P)
    Ps.write_parquet(salida / "panel_municipio_anio.parquet")
    A.with_columns(pl.Series("etnico20", etn20)).write_parquet(salida / "atributos_municipio.parquet")
    (salida / "agregados_nivel_b.json").write_text(json.dumps(ag, ensure_ascii=False, indent=1), encoding="utf-8")
    por_anio = P.group_by("anio").agg(pl.col("res").sum(), pl.col("d_inf").sum(), pl.col("d_neo_prec").sum()).sort("anio")
    from cierre_parto.rutas import EXT
    registros = sum(pl.scan_parquet(EXT / f"nac_{a}.parquet").select(pl.len()).collect().item() for a in range(1998, 2026))
    info = {"registros_nacimientos_1998_2025": int(registros), "filas": P.height, "municipios": int(P["mun"].n_unique()), "anios": [int(P["anio"].min()), int(P["anio"].max())],
            "nacimientos_residentes_por_anio": {int(r[0]): int(r[1]) for r in por_anio.select("anio", "res").rows()},
            "defunciones_infantiles_por_anio": {int(r[0]): int(r[1]) for r in por_anio.select("anio", "d_inf").rows()},
            "celdas_suprimidas": {c: int(P.filter(pl.col(c).is_between(1, 4)).height) for c in COLS_SUPRIMIDAS},
            "celdas_1_a_4_publicadas": {c: int(P.filter(pl.col(c).is_between(1, 4)).height)
                                         for c in ["d_inf", "d_neo_prec", "d_neo_tard", "d_posneo", "noinst", "dom", "c0", "bp", "pre", "ces"]}}
    (salida / "panel_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"intermedios -> {salida.name}/ ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
