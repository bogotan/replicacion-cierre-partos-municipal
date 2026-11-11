"""Pruebas de los insumos propios del artículo A2 y de los paneles intermedios del nivel A.

    python -m pytest pruebas/test_insumos.py -q

1. Huellas: cada archivo de los grupos «a2» y «a2-config» del manifiesto existe (salvo los no versionados, que se omiten
   con aviso si no se han descargado) y tiene el tamaño y la SHA-256 registrados.
2. Insumos externos: filas y columnas de la DIVIPOLA (1.122 entidades), del REPS 2022 (2.018 filas obstétricas y corte
   del 5 de noviembre de 2022 en los metadatos) y del catálogo del IDEAM (9.914 estaciones).
3. Intermedios contra lo publicado por el DANE: los 18.450.346 registros de nacimientos 1998–2025 son la suma de los
   nacidos vivos publicados (pruebas/insumos_eevv/totales_publicados_dane.csv); las defunciones de menores de un año y las
   neonatales precoces de 2018 por municipio de residencia son idénticas a las del cuadro 4 de defunciones 2018 del DANE
   (si se descargó; tolerancia 0).
4. Privacidad: el panel tiene una fila por municipio y año, ninguna columna individual, y las columnas suprimidas no
   tienen valores entre 1 y 4.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

import polars as pl
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from cierre_parto.constantes import COLS_SUPRIMIDAS  # noqa: E402

RAW = RAIZ / "data" / "raw"
INT = RAIZ / "data" / "intermedios"


def _manifiesto():
    with open(RAW / "MANIFIESTO.csv", encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f) if r["grupo"] in ("a2", "a2-config")]


@pytest.mark.parametrize("fila", _manifiesto(), ids=lambda r: r["archivo"])
def test_huellas(fila):
    p = (RAW / fila["archivo"]).resolve()
    if not p.exists():
        if fila["redistribuye"] == "no":
            pytest.skip(f"{fila['archivo']} no se versiona; corra scripts/00_descargar_insumos.py")
        pytest.fail(f"falta {fila['archivo']}")
    assert p.stat().st_size == int(fila["bytes"])
    assert hashlib.sha256(p.read_bytes()).hexdigest() == fila["sha256"]


def test_divipola():
    d = pl.read_csv(RAW / "externos" / "52" / "divipola_gdxc-w37w.csv", infer_schema=False)
    assert d.height == 1122 and d.width == 7


def test_reps_2022():
    d = pl.read_csv(RAW / "externos" / "52" / "reps_capacidad_obstetrica_2022.csv", infer_schema=False)
    assert d.height == 2018
    assert {"c_digo_sede", "nom_descripcion_capacidad", "num_cantidad_capacidad_instalada"} <= set(d.columns)
    assert d["fecha_corte"].str.contains("Nov  5 2022").all()


def test_ideam():
    d = pl.read_csv(RAW / "externos" / "52" / "ideam_estaciones.csv", infer_schema=False)
    assert d.height == 9914 and {"altitud", "latitud", "longitud"} <= set(d.columns)


def test_registros_contra_dane():
    with open(Path(__file__).parent / "insumos_eevv" / "totales_publicados_dane.csv", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    publicado = sum(int(r["total_publicado"]) for r in filas if r["tipo"] == "nacimientos" and 1998 <= int(r["anio"]) <= 2025)
    info = json.loads((INT / "panel_info.json").read_text())
    assert info["registros_nacimientos_1998_2025"] == publicado


def _cuadro4_2018():
    import pandas as pd
    p = RAW / "externos" / "62" / "CUADRO4-NOFETALES-2018-def.xls"
    if not p.exists():
        pytest.skip("cuadro 4 de 2018 no descargado (scripts/00_descargar_insumos.py)")
    xl = pd.ExcelFile(p, engine="calamine")
    filas = []
    for hoja in xl.sheet_names:
        if not re.fullmatch(r"\d\d", hoja) or hoja == "00":
            continue
        x = pd.read_excel(xl, sheet_name=hoja, header=None)
        for i in range(len(x)):
            c0, c1 = x.iat[i, 0], x.iat[i, 1]
            mun = None
            if isinstance(c0, str) and re.match(r"^\d{5} ", c0) and c1 == "TOTAL":
                mun = int(c0[:5])
            elif hoja == "11" and c0 == "TOTAL":          # Bogotá: el departamento es el municipio 11001
                mun = 11001
            if mun is not None:
                v = pd.to_numeric(x.iloc[i, 6:27], errors="coerce").fillna(0)     # menor de 1 hora … 6 a 11 meses
                filas.append((mun, int(v.sum()), int(v.iloc[0:9].sum())))         # 0 a 6 días: menor de 1 hora … 1 a 6 días
    return pl.DataFrame(filas, schema=["mun", "inf_dane", "neo_prec_dane"], orient="row")


def test_defunciones_infantiles_2018_contra_cuadro4():
    c = _cuadro4_2018()
    P = pl.read_parquet(INT / "panel_municipio_anio.parquet").filter(pl.col("anio") == 2018).select("mun", "d_inf", "d_neo_prec")
    j = c.join(P, on="mun", how="full", coalesce=True).fill_null(0)
    assert j.height == 1122
    assert (j["inf_dane"] == j["d_inf"]).all()
    assert (j["neo_prec_dane"] == j["d_neo_prec"]).all()


def test_sin_registros_individuales_y_supresion():
    P = pl.read_parquet(INT / "panel_municipio_anio.parquet")
    assert P.select(pl.struct("mun", "anio").n_unique()).item() == P.height
    for c in COLS_SUPRIMIDAS:
        assert P.filter(pl.col(c).is_between(1, 4)).height == 0, c
    A = pl.read_parquet(INT / "atributos_municipio.parquet")
    assert A["mun"].n_unique() == A.height == 1122
