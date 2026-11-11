"""Recálculo independiente de las cifras del resumen (y de las especificaciones A, B y C) desde data/intermedios/.

Este archivo no importa nada de src/cierre_parto: lee el panel con polars y reimplementa, a partir del código con el que
el árbitro reprodujo el artículo, la regla del evento (ecuación 2), las tasas y el estimador de Callaway y Sant'Anna
(ecuaciones 5 y 6) con base g−1 (A), base promedio g−8…g−2 (C) y la diferencia «posterior menos previo» (B). Compara con
output/resultados.json:
  · muestra: 1.046 elegibles, 490 tratados, 289 nunca tratados y 267 fuera; cohortes 48, 235 y 207;
  · puntos estimados de A, B y C para la cuota local, la distancia, la prematuridad y la mortalidad neonatal, neonatal
    precoz e infantil (tolerancia 1e-6);
  · errores estándar de C para prematuridad y mortalidad infantil con un bootstrap por municipios propio (199 réplicas;
    tolerancia relativa de 25 % frente al bootstrap multiplicador del artículo, que es otro procedimiento);
  · las cifras redondeadas del resumen: 490 municipios, 18,5 millones de nacidos vivos, 0,57 (0,26 a 0,87) y 0,36 (−0,12 a
    0,83), y que con base g−1 ningún resultado de salud se aparta de cero.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
import pytest

pytestmark = pytest.mark.filterwarnings("ignore::RuntimeWarning")
RAIZ = Path(__file__).resolve().parents[1]
A_ = list(range(1998, 2026)); T = 28
R = json.loads((RAIZ / "output" / "resultados.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def datos():
    P = pl.read_parquet(RAIZ / "data" / "intermedios" / "panel_municipio_anio.parquet")
    mun = np.sort(P["mun"].unique().to_numpy()); idx = {m: i for i, m in enumerate(mun)}
    ii = np.array([idx[m] for m in P["mun"].to_list()]); tt = P["anio"].to_numpy().astype(int) - 1998

    def arr(c, cero=False):
        X = np.full((len(mun), T), np.nan); X[ii, tt] = P[c].cast(pl.Float64).to_numpy()
        return np.nan_to_num(X) if cero else X
    res, li = arr("res", True), arr("loc_inst", True)
    S = np.where(res > 0, li / np.maximum(res, 1), 0.0)
    elig = res.mean(1) >= 30
    G = np.full(len(mun), np.nan)
    for i in range(len(mun)):
        if not elig[i]:
            continue
        s = S[i]; st = None
        for t in range(2, T):
            if (s[t - 2:t + 1] >= .25).all():
                st = t; break
        if st is None:
            continue
        for t in range(max(st + 1, 3), T - 1):
            if s[t - 1] >= .10 and s[t] < .10 and s[t + 1] < .10 and s[t:].mean() < .10:
                G[i] = A_[t]; break
        if np.isnan(G[i]) and (s >= .10).all():
            G[i] = np.inf
    w = res[:, :3].mean(1)
    for i in np.where(w <= 0)[0]:
        v = res[i][res[i] > 0][:3]; w[i] = v.mean() if len(v) else 0

    def tasa(n, d, k=100.0, minimo=1):
        with np.errstate(all="ignore"):
            return np.where(d >= minimo, k * n / d, np.nan)
    Y = {"local": 100 * li / np.where(res > 0, res, np.nan), "km": tasa(arr("km", True), arr("kmk", True), 1.0),
         "pre37": tasa(arr("pre"), arr("gk"), minimo=10), "neo": tasa(arr("d_neo_prec", True) + arr("d_neo_tard", True), res, 1000.0),
         "neo_prec": tasa(arr("d_neo_prec", True), res, 1000.0), "inf": tasa(arr("d_inf", True), res, 1000.0)}
    Y["local"] = np.where(res > 0, 100 * li / np.maximum(res, 1), np.nan)
    sm = ~np.isnan(G)
    return {"G": G[sm], "w": w[sm], "Y": {k: v[sm] for k, v in Y.items()}, "elig": int(elig.sum()), "Gall": G}


def att(y, G, w, base="g1", emin=-8, emax=6):
    """θ(e) y θ̄ (e = 0…5) de Callaway y Sant'Anna con controles aún no tratados y nunca tratados."""
    gs = sorted(set(G[np.isfinite(G)].astype(int))); acc = {}
    for g in gs:
        gi = g - 1998
        if base == "g1":
            b_hi = gi - 1; antic = 0
            if b_hi < 0:
                continue
            yb = y[:, b_hi]
        else:                                              # promedio de g−8…g−2 con al menos 3 años con dato
            b_hi = gi - 2; antic = 1
            if b_hi < 0:
                continue
            bloque = y[:, max(0, gi - 8):b_hi + 1]
            nb = (~np.isnan(bloque)).sum(1)
            with np.errstate(all="ignore"):
                yb = np.where(nb >= 3, np.nanmean(bloque, 1), np.nan)
        for e in range(emin, emax + 1):
            if base == "g1" and e == -1:
                continue
            ti = gi + e
            if not 0 <= ti < T:
                continue
            ct = (G > max(A_[ti], A_[b_hi]) + antic) & (G != g)
            dy = y[:, ti] - yb; ok = ~np.isnan(dy)
            wt = np.where((G == g) & ok, w, 0.0); wc = np.where(ct & ok, w, 0.0)
            if wt.sum() <= 0 or wc.sum() <= 0:
                continue
            d0 = np.nan_to_num(dy)
            acc.setdefault(e, []).append((wt.sum(), (wt * d0).sum() / wt.sum() - (wc * d0).sum() / wc.sum()))
    th = {e: sum(a * b for a, b in v) / sum(a for a, _ in v) for e, v in acc.items()}
    return np.mean([th[e] for e in range(0, 6)]), th


def test_muestra(datos):
    G = datos["G"]; tr = np.isfinite(G)
    assert (datos["elig"], int(tr.sum()), int(np.isinf(G).sum())) == (1046, 490, 289)
    assert datos["elig"] - len(G) == 267
    gf = G[tr]
    assert [int(((gf >= a) & (gf <= b)).sum()) for a, b in [(2001, 2010), (2011, 2020), (2021, 2024)]] == [48, 235, 207]


@pytest.mark.parametrize("k", ["local", "km", "pre37", "neo", "neo_prec", "inf"])
def test_puntos_A_B_C(datos, k):
    y, G, w = datos["Y"][k], datos["G"], datos["w"]
    mA, thA = att(y, G, w, "g1")
    mC, _ = att(y, G, w, "prom")
    mB = mA - np.mean([thA[e] for e in range(-8, -1) if e in thA])
    C = R["coprincipales"]
    assert mA == pytest.approx(C["A_base_g1"][k]["att"], abs=1e-6)
    assert mB == pytest.approx(C["B_post_menos_previo"][k]["att"], abs=1e-6)
    assert mC == pytest.approx(C["C_base_promedio"][k]["att"], abs=1e-6)


@pytest.mark.parametrize("k", ["pre37", "inf"])
def test_error_estandar_C(datos, k):
    y, G, w = datos["Y"][k], datos["G"], datos["w"]
    rng = np.random.default_rng(1); n = len(G); reps = []
    for _ in range(199):
        ix = rng.integers(0, n, n)
        reps.append(att(y[ix], G[ix], w[ix], "prom")[0])
    se = float(np.std(reps, ddof=1))
    assert se == pytest.approx(R["coprincipales"]["C_base_promedio"][k]["ee"], rel=0.25)


def _f(x, d=2):
    s = f"{abs(x):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if x < 0 and round(x, d) != 0 else "") + s


def test_cifras_del_resumen(datos):
    ruta = RAIZ / "manuscrito" / "manuscrito.md"
    if not ruta.exists():
        pytest.skip("El texto del artículo se agrega al repositorio cuando se publique.")
    man = ruta.read_text(encoding="utf-8")
    resumen = man.split("## Resumen")[1].split("**Palabras clave")[0]
    y, G, w = datos["Y"], datos["G"], datos["w"]
    info = json.loads((RAIZ / "data" / "intermedios" / "panel_info.json").read_text())
    assert f"Con {_f(info['registros_nacimientos_1998_2025'] / 1e6, 1)} millones de nacidos vivos" in resumen
    assert f"en {int(np.isfinite(G).sum())} municipios" in resumen
    C = R["coprincipales"]["C_base_promedio"]
    pre = att(y["pre37"], G, w, "prom")[0]; inf = att(y["inf"], G, w, "prom")[0]
    assert f"la prematuridad sube {_f(pre)} puntos (IC 95 %: {_f(C['pre37']['ic_inf'])} a {_f(C['pre37']['ic_sup'])})" in resumen
    assert f"la mortalidad infantil {_f(inf)} por 1.000 (IC 95 %: {_f(C['inf']['ic_inf'])} a {_f(C['inf']['ic_sup'])})" in resumen
    A = R["coprincipales"]["A_base_g1"]
    for k in ["noinst", "c4", "bp", "pre37", "neo", "neo_prec", "inf"]:      # «frente al año anterior al cierre, nada cambia»
        assert A[k]["ic_inf"] <= 0 <= A[k]["ic_sup"], k
