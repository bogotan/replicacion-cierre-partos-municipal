"""Armonización municipal, coordenadas, distancia y altitud: código vendorizado del estudio 52.

Procedencia: funciones `armonizar`, `coordenadas`, `altitudes` y `haversine` y la constante `ARMONIZA` copiadas sin
cambios de lógica de `scripts/52_desiertos_obstetricos.py` del repositorio de Estadísticas Vitales de Sinergística
(estudio 52, «desiertos obstétricos», octubre de 2026; SHA-256 del archivo de origen en docs/INSUMOS.md). Solo cambia
la ruta de los insumos, que ahora están en data/raw/externos/52/ de este repositorio.

    · ARMONIZA: 27086 (Belén de Bajirá, 2001–2007) -> 27493 (Nuevo Belén de Bajirá, DIVIPOLA 2024);
      94663 (Mapiripana, corregimiento departamental hasta 2021) -> 94343 (Barrancominas).
    · coordenadas(): DIVIPOLA del DANE con longitud y latitud (datos.gov.co gdxc-w37w, corte 30-dic-2024).
    · altitudes(): altitud de la estación del Catálogo Nacional de Estaciones del IDEAM (hp9r-jxuu) más cercana al punto
      de referencia de cada municipio.
    · haversine(): distancia sobre una esfera de radio 6.371,0088 km.
"""
from __future__ import annotations

import math

import numpy as np
import polars as pl

from .rutas import X52

ARMONIZA = {27086: 27493, 94663: 94343}


def armonizar(c: str) -> pl.Expr:
    e = pl.col(c)
    for k, v in ARMONIZA.items():
        e = pl.when(pl.col(c) == k).then(v).otherwise(e)
    return e.cast(pl.Int32).alias(c)


def coordenadas() -> pl.DataFrame:
    d = pl.read_csv(X52 / "divipola_gdxc-w37w.csv", infer_schema=False)
    d.columns = ["cdp", "ndp", "cod", "nmun", "tipo", "lon", "lat"]
    return d.select(
        pl.col("cod").cast(pl.Int32), pl.col("cdp").cast(pl.Int16).alias("dpc"),
        pl.col("ndp"), pl.col("nmun"), pl.col("tipo"),
        pl.col("lat").str.replace(",", ".").cast(pl.Float64),
        pl.col("lon").str.replace(",", ".").cast(pl.Float64))


def altitudes(co: pl.DataFrame) -> pl.DataFrame:
    """Altitud aproximada de cada municipio: la de la estación del Catálogo Nacional de Estaciones del IDEAM más cercana
    a su punto de referencia (datos.gov.co hp9r-jxuu). Se informa también la distancia a esa estación."""
    e = pl.read_csv(X52 / "ideam_estaciones.csv", infer_schema=False).select(
        pl.col("altitud").str.replace(",", ".").cast(pl.Float64, strict=False).alias("alt"),
        pl.col("latitud").str.replace(",", ".").cast(pl.Float64, strict=False).alias("lat"),
        pl.col("longitud").str.replace(",", ".").cast(pl.Float64, strict=False).alias("lon")).drop_nulls()
    e = e.filter(pl.col("lat").is_between(-5, 14) & pl.col("lon").is_between(-82, -66) & pl.col("alt").is_between(0, 5500))
    la, lo = np.radians(e["lat"].to_numpy()), np.radians(e["lon"].to_numpy())
    out = []
    for cod, lat, lon in co.select("cod", "lat", "lon").iter_rows():
        p1, l1 = math.radians(lat), math.radians(lon)
        a = np.sin((la - p1) / 2) ** 2 + math.cos(p1) * np.cos(la) * np.sin((lo - l1) / 2) ** 2
        d = 2 * 6371.0088 * np.arcsin(np.sqrt(a)); j = int(d.argmin())
        out.append((cod, float(e["alt"][j]), float(d[j])))
    return pl.DataFrame(out, schema={"mun": pl.Int32, "alt": pl.Float64, "km_estacion": pl.Float64}, orient="row")


def haversine(lat1, lon1, lat2, lon2) -> pl.Expr:
    r = 6371.0088
    p1, p2 = lat1.radians(), lat2.radians()
    dphi = (lat2 - lat1).radians()
    dl = (lon2 - lon1).radians()
    a = (dphi / 2).sin() ** 2 + p1.cos() * p2.cos() * (dl / 2).sin() ** 2
    return 2 * r * a.sqrt().arcsin()
