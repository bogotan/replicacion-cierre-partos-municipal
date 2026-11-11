"""Lectura de los paneles intermedios y construcción de las variables de resultado (tasas municipio-año)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl

from .constantes import ANIOS, T
from .rutas import INTERMEDIOS


def cargar(carpeta: Path | None = None):
    """Lee los paneles de data/intermedios/ (o de `carpeta`) y los devuelve como arreglos municipio × año.
    Las celdas suprimidas (nulas) quedan como NaN."""
    carpeta = carpeta or INTERMEDIOS
    P = pl.read_parquet(carpeta / "panel_municipio_anio.parquet")
    A = pl.read_parquet(carpeta / "atributos_municipio.parquet").sort("mun")
    mun = A["mun"].to_numpy()
    idx = {m: i for i, m in enumerate(mun)}
    W = {}
    cols = [c for c in P.columns if c not in ("mun", "anio")]
    ii = np.array([idx[m] for m in P["mun"].to_list()]); tt = P["anio"].to_numpy().astype(int) - ANIOS[0]
    for c in cols:
        X = np.full((len(mun), T), np.nan)
        X[ii, tt] = P[c].to_numpy().astype(float)
        W[c] = X
    for c in ["res", "loc_inst", "loc_inst9", "ocu_inst", "d_inf", "d_neo_prec", "d_neo_tard", "d_posneo", "d_inf_dom",
              "d_neo_fuera", "d_neo_ext"]:
        W[c] = np.nan_to_num(W[c], nan=0.0)
    return A, W


def razon(num, den, k=100.0, minimo=1):
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den >= minimo, k * num / den, np.nan)


def resultados(W):
    """Variables de resultado municipio-año, sobre los nacidos de madres residentes (nazcan donde nazcan)."""
    Y = {}
    Y["local"] = razon(W["loc_inst"], W["res"])
    Y["ocu_esc"] = None  # se llena en definir_evento (volumen escalado)
    Y["noinst"] = razon(W["noinst"], W["sitk"])
    Y["dom"] = razon(W["dom"], W["sitk"])
    Y["km"] = razon(W["km"], W["kmk"], k=1.0)
    Y["km50"] = razon(W["km50"], W["kmk"])
    Y["c4"] = razon(W["c4"], W["ck"])
    Y["c0"] = razon(W["c0"], W["ck"])
    Y["medico"] = razon(W["medico"], W["atk"])
    Y["bp"] = razon(W["bp"], W["pk"])
    Y["pre38"] = razon(W["pre38"], W["gk38"])
    Y["pre37"] = razon(W["pre"], W["gk"], minimo=10)
    Y["ces"] = razon(W["ces"], W["tk"])
    Y["neo"] = razon(W["d_neo_prec"] + W["d_neo_tard"], W["res"], k=1000.0)
    Y["neo_prec"] = razon(W["d_neo_prec"], W["res"], k=1000.0)
    Y["posneo"] = razon(W["d_posneo"], W["res"], k=1000.0)
    Y["inf"] = razon(W["d_inf"], W["res"], k=1000.0)
    Y["inf_dom"] = razon(W["d_inf_dom"], W["res"], k=1000.0)
    Y["pfuera_neo"] = razon(W["d_neo_fuera"], W["d_neo_ext"])
    Y["lres"] = np.where(W["res"] > 0, np.log(np.maximum(W["res"], 1)), np.nan)
    Y["compl"] = razon(W["res"], W["pob0"])
    Y["adol"] = razon(W["adol"], W["ek"])
    Y["e35"] = razon(W["e35"], W["ek"])
    Y["edb"] = razon(W["edb"], W["edk"])
    Y["subs"] = razon(W["subs"], W["rk"])
    Y["rural"] = razon(W["rural"], W["ak"])
    Y["prim"] = razon(W["prim"], W["hk"])
    Y["etn"] = razon(W["etn"], W["etk"], minimo=10)
    Y["mult"] = razon(W["mult"], W["mk"])
    del Y["ocu_esc"]
    return Y


ETIQ = {"local": "Partos en institución del propio municipio (%)", "noinst": "Parto no institucional (%)",
        "dom": "Parto en domicilio (%)", "km": "Distancia media al sitio del parto (km)", "km50": "Parto a más de 50 km (%)",
        "c4": "Cuatro o más controles prenatales (%)", "c0": "Ningún control prenatal (%)", "medico": "Parto atendido por médico (%)",
        "bp": "Bajo peso al nacer (%)", "pre38": "37 semanas o menos (%)", "pre37": "Prematuro, menos de 37 semanas (%)",
        "inf_dom": "Muertes infantiles en domicilio (por 1.000)",
        "ces": "Cesárea (%)", "neo": "Mortalidad neonatal (por 1.000)", "neo_prec": "Mortalidad neonatal precoz (por 1.000)",
        "posneo": "Mortalidad posneonatal (por 1.000)", "inf": "Mortalidad infantil (por 1.000)",
        "lres": "Log de nacimientos de residentes", "compl": "Nacimientos / población de 0 años (%)",
        "adol": "Madres de 10 a 19 años (%)", "e35": "Madres de 35 años o más (%)", "edb": "Madres con primaria o menos (%)",
        "subs": "Régimen subsidiado (%)", "rural": "Residencia rural (%)", "prim": "Primer hijo (%)",
        "etn": "Pertenencia étnica (%)", "mult": "Parto múltiple (%)"}


CORTA = {"local": "Parto en institución local (%)", "km": "Distancia media (km)", "km50": "Parto a más de 50 km (%)",
         "noinst": "Parto no institucional (%)", "c4": "4+ controles prenatales (%)", "bp": "Bajo peso (%)",
         "pre38": "37 semanas o menos (%)", "pre37": "Prematuro (%)", "ces": "Cesárea (%)", "neo": "Neonatal (por 1.000)",
         "neo_prec": "Neonatal precoz (por 1.000)", "inf": "Infantil (por 1.000)"}


def pesos_base(W):
    """Peso fijo de cada municipio: nacimientos de residentes promedio en 1998–2000 (o en sus tres primeros años con
    nacimientos, para municipios creados después)."""
    R = W["res"]; w = R[:, :3].mean(axis=1)
    for i in np.where(w <= 0)[0]:
        v = R[i][R[i] > 0][:3]
        w[i] = v.mean() if len(v) else 0.0
    return w


def primeros_anios(X, R, k=3):
    """Media de X en 1998–2000 (o en los primeros k años con nacimientos)."""
    out = np.full(len(X), np.nan)
    for i in range(len(X)):
        ok = np.where((R[i] > 0) & ~np.isnan(X[i]))[0][:k]
        if len(ok):
            out[i] = X[i, ok].mean()
    return out
