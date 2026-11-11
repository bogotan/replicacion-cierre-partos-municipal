"""Definición del evento: año de cierre funcional del parto local (ecuación 2 del manuscrito)."""
from __future__ import annotations

import numpy as np

from .constantes import ANIOS


def definir_evento(W, base="cuota", alto=0.25, bajo=0.10, persist=2, k=3, minres=30.0, sit9=False, anio_max=2025):
    """Año de cierre G (np.inf = nunca tratado; np.nan = fuera de la muestra).
    base="cuota": s = partos de residentes en institución del propio municipio / nacimientos de residentes.
      Tratado en g si (i) antes de g hubo k años consecutivos con s >= alto (parto local estable), (ii) s(g-1) >= bajo,
      (iii) s < bajo en g, …, g+persist-1, y (iv) el promedio de s desde g hasta 2025 es < bajo (persistencia).
      Nunca tratado: cumple (i) y s >= bajo todos los años 1998–2025.
    base="volumen": lo mismo con v = partos institucionales ocurridos en el municipio (de cualquier residencia) dividido por
      el factor de caída nacional de los nacimientos (año / 2008), con alto y bajo en partos por año.
    Muestra: promedio de nacimientos de residentes 1998–2025 >= minres. anio_max < 2025 define el evento sin los años
    posteriores (sensibilidad a 2025, preliminar)."""
    Tm = ANIOS.index(anio_max) + 1
    res = W["res"][:, :Tm]
    if base == "cuota":
        num = (W["loc_inst9"] if sit9 else W["loc_inst"])[:, :Tm]
        S = np.where(res > 0, num / np.maximum(res, 1), 0.0)
    else:
        nat = res.sum(axis=0); f = nat / nat[ANIOS.index(2008)]
        S = W["ocu_inst"][:, :Tm] / f[None, :]
    elig = res.mean(axis=1) >= minres
    G = np.full(len(S), np.nan)
    for i in range(len(S)):
        if not elig[i]:
            continue
        s = S[i]; run = 0; estable = None
        for t in range(Tm):
            run = run + 1 if s[t] >= alto else 0
            if run >= k:
                estable = t; break
        if estable is None:
            continue
        for t in range(max(estable + 1, 3), Tm - persist + 1):
            if s[t - 1] >= bajo and (s[t:t + persist] < bajo).all() and s[t:].mean() < bajo:
                G[i] = ANIOS[t]; break
        if np.isnan(G[i]) and (s >= bajo).all():
            G[i] = np.inf
    return G, S
