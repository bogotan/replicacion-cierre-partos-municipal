"""Pruebas de los estimadores escritos a mano (src/cierre_parto/estimadores.py) contra casos de solución conocida y
contra pyfixest.

1. cs(): con efectos de unidad y año más un efecto τ(g, e) conocido y sin ruido, recupera θ(e) exactamente (controles
   aún no tratados y nunca tratados; base g−1 y base promedio).
2. cs() con una sola cohorte y controles nunca tratados coincide con el estudio de eventos de efectos fijos de dos vías
   completamente saturado de pyfixest (todos los periodos relativos salvo −1), coeficiente por coeficiente.
3. bacon(): la suma ponderada de las comparaciones 2 × 2 reproduce el TWFE de pyfixest, con y sin pesos.
4. bootstrap_mult(): con un efecto puramente aleatorio, el error estándar de θ̄ se parece al desvío estándar de θ̄ en
   simulaciones repetidas (cobertura aproximada).
"""
from __future__ import annotations

import re
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from cierre_parto.constantes import ANIOS, T  # noqa: E402
from cierre_parto.estimadores import bacon, bootstrap_mult, cs, largo  # noqa: E402

warnings.filterwarnings("ignore")


def _panel(seed=1, n_por=12, ruido=0.0, tau=None):
    rng = np.random.default_rng(seed)
    cohortes = [2008, 2012, 2016, 2020]
    G = np.concatenate([np.full(n_por, g, float) for g in cohortes] + [np.full(3 * n_por, np.inf)])
    n = len(G)
    a = rng.normal(0, 2, n)[:, None]; l = rng.normal(0, 1, T)[None, :]
    tt = np.array(ANIOS)[None, :]
    e = tt - np.where(np.isfinite(G), G, 9999)[:, None]
    tau = tau or (lambda g, e: (1.0 + 0.1 * (g - 2008)) * (1 + 0.5 * e))
    efecto = np.where(e >= 0, np.vectorize(tau)(np.where(np.isfinite(G), G, 0)[:, None] + 0 * e, e), 0.0)
    Y = a + l + efecto + ruido * rng.normal(size=(n, T))
    return Y, G, efecto


def _theta_verdadero(G, w, tau_fn, emax=6):
    out = {}
    gs = sorted(set(G[np.isfinite(G)].astype(int)))
    for e in range(0, emax + 1):
        num = den = 0.0
        for g in gs:
            if g + e <= ANIOS[-1]:
                W = w[G == g].sum(); num += W * tau_fn(g, e); den += W
        out[e] = num / den
    return out


def test_cs_recupera_efecto_conocido():
    tau = lambda g, e: (1.0 + 0.1 * (g - 2008)) * (1 + 0.5 * e)  # noqa: E731
    Y, G, _ = _panel(tau=tau)
    w = np.linspace(1, 3, len(G))
    verdad = _theta_verdadero(G, w, tau)
    for kw in (dict(), dict(control="never"), dict(base_win=(-8, -2))):
        o = cs(Y, G, w, **kw)
        for e, th in zip(o["e"], o["theta"]):
            if 0 <= e <= 6:
                assert th == pytest.approx(verdad[int(e)], abs=1e-9), (kw, e)
            if e < -1 and "base_win" not in kw:
                assert th == pytest.approx(0.0, abs=1e-9)


def test_cs_igual_a_twfe_saturado_pyfixest():
    import pyfixest as pf
    rng = np.random.default_rng(7)
    G = np.concatenate([np.full(25, 2012.0), np.full(40, np.inf)])
    Y = rng.normal(size=(len(G), T)) + np.where((np.array(ANIOS)[None, :] >= 2012) & np.isfinite(G)[:, None], 1.5, 0)
    o = cs(Y, G, np.ones(len(G)), control="never", emin=-14, emax=13)
    df = largo(Y, G, np.ones(len(G)))
    df["rel"] = np.where(np.isfinite(df["G"]), df["e"], -1).astype(int)
    m = pf.feols("y ~ i(rel, ref=-1) | mun + anio", data=df)
    co = m.coef()
    for e, th in zip(o["e"], o["theta"]):
        nombre = [k for k in co.index if re.search(rf"::{int(e)}(\.0)?\]?$", k)]
        assert nombre, e
        assert th == pytest.approx(float(co[nombre[0]]), abs=1e-8)


@pytest.mark.parametrize("ponderado", [False, True])
def test_bacon_reproduce_twfe(ponderado):
    import pyfixest as pf
    Y, G, _ = _panel(seed=3, ruido=1.0)
    w = np.linspace(1, 5, len(G)) if ponderado else np.ones(len(G))
    b = bacon(Y, G, w if ponderado else None)
    df = largo(Y, G, w)
    m = pf.feols("y ~ D | mun + anio", data=df, weights="w")
    assert b["suma_ponderada"] == pytest.approx(b["twfe_balanceado"], abs=1e-10)
    assert b["twfe_balanceado"] == pytest.approx(float(m.coef()["D"]), abs=1e-8)


def test_bootstrap_cobertura_aproximada():
    est, se = [], []
    for s in range(40):
        Y, G, _ = _panel(seed=100 + s, ruido=1.0, tau=lambda g, e: 0.0)
        o = cs(Y, G, np.ones(len(G))); bs = bootstrap_mult(o, len(G), B=299, seed=s)
        est.append(o["media"]); se.append(bs["se_media"])
    est, se = np.array(est), np.array(se)
    assert np.std(est) == pytest.approx(np.mean(se), rel=0.35)
    assert np.mean(np.abs(est) <= 1.96 * se) >= 0.85
