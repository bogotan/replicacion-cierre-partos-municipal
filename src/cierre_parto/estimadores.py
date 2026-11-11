"""Estimadores del artículo, escritos a mano salvo donde se indica.

    cs()               Callaway y Sant'Anna (2021): ATT(g,t) con base universal, ventana de base o anticipación; FI por municipio
    bootstrap_mult()   bootstrap multiplicador de Rademacher sobre las funciones de influencia (agrupado por municipio)
    rambachan_roth()   magnitudes relativas (implementación simplificada) y tendencia lineal previa
    twfe(), bacon()    efectos fijos de dos vías (pyfixest) y descomposición de Goodman-Bacon (2021), ponderada o no
    wild_cluster()     bootstrap salvaje agrupado restringido (WCR) del TWFE estático
    sun_abraham(), gardner(), poisson_etwfe()   con pyfixest
    cs_ipw()           CS con ponderación por propensión (controles nunca tratados) y bootstrap por municipios
    permutacion()      inferencia por permutación de los años de cierre
Las pruebas de pruebas/test_estimadores.py comparan cs() con casos de solución conocida y con pyfixest.
"""
from __future__ import annotations

import math

import numpy as np

from .constantes import ANIOS, B_MULT, B_UNID, E_MAX, E_MIN, E_POST, N_PERM, P_MAX, P_MIN, SEMILLA, T
from .datos import primeros_anios


def cs(Y, G, w, control="notyet", emin=E_MIN, emax=E_MAX, epost=E_POST, con_if=True, w_ctrl=None, anticip=0, base_k=1,
       base_win=None, min_base=3, excl_ctrl=None, info=False):
    """ATT(g,t) de Callaway y Sant'Anna con base universal y su función de influencia (FI) por municipio.
    control="notyet": aún no tratados en max(t, base) + nunca tratados; "never": solo nunca tratados; "tronly": solo
    municipios tratados más tarde (sin nunca tratados).
    Base: por defecto el año g-1. anticip = δ > 0 la mueve a g-1-δ y exige controles sin tratar en t + δ. base_k > 1 usa el
    promedio de g-base_k…g-1. base_win = (lo, hi) usa el promedio de los años g+lo…g+hi (al menos min_base con dato) y exige
    controles sin tratar en t + (-1-hi); en ese caso se estiman todos los θ(e) de la ventana, incluidos los de la base, que
    muestran el nivel de cada año frente al promedio previo.
    excl_ctrl: municipios que no pueden ser control (p. ej., ciudades grandes).
    Devuelve θ(e), el promedio θ̄ de e = 0…epost y el promedio previo, con sus FI, ponderando las cohortes por la suma de pesos
    de sus tratados. info=True agrega la composición del peso de los controles en e = 0…epost."""
    n = len(G)
    gs = sorted(set(G[np.isfinite(G)].astype(int)))
    if base_win is None:
        be = -1 - anticip
        lo_b, hi_b = be - base_k + 1, be
        es = [e for e in range(emin, emax + 1) if not (lo_b <= e <= hi_b)]
        antic = anticip
    else:
        lo_b, hi_b = base_win
        be = hi_b
        es = list(range(emin, emax + 1))
        antic = -1 - hi_b
    acc = {e: [] for e in es}
    peso_ctrl = np.zeros(n); peso_nunca = []
    for g in gs:
        gi = ANIOS.index(g); b = gi + hi_b; b0 = gi + lo_b
        if b < 0:
            continue
        tr = G == g
        if base_win is None and base_k == 1:
            yb = Y[:, b]
        else:
            if base_win is None and b0 < 0:
                continue
            with np.errstate(all="ignore"):
                bk = Y[:, max(0, b0):b + 1]
                nb = (~np.isnan(bk)).sum(axis=1)
                req = base_k if base_win is None else min_base
                yb = np.where(nb >= req, np.nansum(bk, axis=1) / np.maximum(nb, 1), np.nan)
        for e in es:
            ti = gi + e
            if ti < 0 or ti >= T:
                continue
            if control == "never":
                ct = np.isinf(G)
            else:
                ct = (G > max(ANIOS[ti], ANIOS[b]) + antic) & (G != g)
                if control == "tronly":
                    ct = ct & np.isfinite(G)
            if excl_ctrl is not None:
                ct = ct & ~excl_ctrl
            dy = Y[:, ti] - yb
            ok = ~np.isnan(dy)
            wt = np.where(tr & ok, w, 0.0); wc = np.where(ct & ok, w if w_ctrl is None else w_ctrl, 0.0)
            if wt.sum() <= 0 or wc.sum() <= 0:
                continue
            d0 = np.nan_to_num(dy)
            mt = (wt * d0).sum() / wt.sum(); mc = (wc * d0).sum() / wc.sum()
            psi = n * (wt * (d0 - mt) / wt.sum() - wc * (d0 - mc) / wc.sum()) if con_if else None
            acc[e].append((wt.sum(), mt - mc, psi))
            if info and 0 <= e <= epost:
                peso_ctrl += wt.sum() * wc / wc.sum()
                peso_nunca.append((wt.sum(), (wc * np.isinf(G)).sum() / wc.sum()))
    th, PS, ee = [], [], []
    for e in es:
        if not acc[e]:
            continue
        wsum = sum(a[0] for a in acc[e])
        th.append(sum(a[0] * a[1] for a in acc[e]) / wsum)
        PS.append(sum(a[0] * a[2] for a in acc[e]) / wsum if con_if else None)
        ee.append(e)
    th = np.array(th); ee = np.array(ee)
    post = (ee >= 0) & (ee <= epost)
    if base_win is None:
        pre = (ee >= lo_b - 4) & (ee <= lo_b - 1)
    else:
        pre = (ee >= lo_b) & (ee <= hi_b)
    out = {"e": ee, "theta": th, "media": th[post].mean(), "pre": th[pre].mean() if pre.any() else float("nan"),
           "base_e": lo_b, "ventana": base_win is not None}
    if con_if:
        PS = np.array(PS)              # parámetros × n
        out["psi"] = PS
        out["psi_media"] = PS[post].mean(axis=0)
        out["psi_pre"] = PS[pre].mean(axis=0) if pre.any() else np.zeros(n)
    if info:
        out["peso_ctrl"] = peso_ctrl / peso_ctrl.sum()
        out["peso_nunca"] = sum(a * b for a, b in peso_nunca) / sum(a for a, _ in peso_nunca)
    return out


def bootstrap_mult(out, n, B=B_MULT, seed=SEMILLA):
    """Bootstrap multiplicador (Rademacher) sobre las FI, agrupado por municipio (la unidad es el municipio)."""
    rng = np.random.default_rng(seed)
    V = rng.choice([-1.0, 1.0], size=(B, n))
    Mpsi = np.vstack([out["psi"], out["psi_media"][None, :], out["psi_pre"][None, :]])
    est = np.concatenate([out["theta"], [out["media"], out["pre"]]])
    D = V @ Mpsi.T / n                                   # B × parámetros (desvíos)
    se = (np.quantile(D, 0.75, axis=0) - np.quantile(D, 0.25, axis=0)) / 1.3489795
    k = len(out["theta"])
    t_max = np.max(np.abs(D[:, :k]) / np.where(se[:k] > 0, se[:k], np.nan), axis=1)
    crit = float(np.nanquantile(t_max, 0.95))
    ee = out["e"]; prei = np.where((ee >= E_MIN) & (ee < out["base_e"]))[0]
    th_p = out["theta"][prei]
    try:
        if len(prei) == 0 or out.get("ventana"):
            raise ValueError("sin periodos previos fuera de la base")
        Sg = np.cov(D[:, prei].T)
        wald = float(th_p @ np.linalg.solve(Sg, th_p)); from scipy.stats import chi2
        p_wald = float(1 - chi2.cdf(wald, len(prei)))
    except Exception:
        wald, p_wald = float("nan"), float("nan")
    return {"se": se[:k], "se_media": float(se[k]), "se_pre": float(se[k + 1]), "crit_unif": crit, "D": D,
            "wald_pre": wald, "p_wald_pre": p_wald, "gl_pre": int(len(prei))}


def resumen(out, bs):
    from scipy.stats import norm
    m, s = out["media"], bs["se_media"]
    return {"att": m, "ee": s, "ic_inf": m - 1.96 * s, "ic_sup": m + 1.96 * s, "p": float(2 * (1 - norm.cdf(abs(m / s)))) if s > 0 else None,
            "pre": out["pre"], "ee_pre": bs["se_pre"], "p_wald_pre": bs["p_wald_pre"], "gl_pre": bs["gl_pre"],
            "eventos": {int(e): {"theta": float(t), "ee": float(se), "ic_inf": float(t - 1.96 * se), "ic_sup": float(t + 1.96 * se),
                                 "banda_inf": float(t - bs["crit_unif"] * se), "banda_sup": float(t + bs["crit_unif"] * se)}
                        for e, t, se in zip(out["e"], out["theta"], bs["se"])}}


def media_base(Y, G, w, cohort_window=(-3, -1)):
    """Media ponderada del resultado entre los tratados en los años g-3…g-1 (nivel de referencia para leer el ATT)."""
    num = den = 0.0
    for i in np.where(np.isfinite(G))[0]:
        gi = ANIOS.index(int(G[i]))
        v = Y[i, max(0, gi + cohort_window[0]):gi + cohort_window[1] + 1]
        v = v[~np.isnan(v)]
        if len(v):
            num += w[i] * v.mean(); den += w[i]
    return num / den if den else float("nan")


def rambachan_roth(out, bs, mbar_grid=(0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0)):
    """Δ^RM(M̄): |δ_{t+1} - δ_t| <= M̄ · max_{s<0} |δ_{s+1} - δ_s| para t >= -1 (δ_{-1} = 0). Para θ̄ = media de e = 0…5 el
    sesgo máximo es b = M̄ · Δ · media(e + 1). IC: [cuantil 2,5 % de (θ̄* - b*), cuantil 97,5 % de (θ̄* + b*)] sobre las
    réplicas del bootstrap multiplicador, que propagan la incertidumbre de Δ. Aproximación conservadora; Rambachan y Roth
    proponen intervalos condicionales o híbridos."""
    ee = out["e"]; k = len(ee)
    D = bs["D"]
    th = out["theta"][None, :] + D[:, :k]
    be = out["base_e"]
    full_e = list(ee); pre_idx = [j for j, e in enumerate(ee) if e < be]
    # diferencias consecutivas previas incluyendo θ(base) = 0
    pre_e = sorted([ee[j] for j in pre_idx]) + [be]
    def dif_max(throw):
        vals = {e: throw[full_e.index(e)] for e in pre_e if e != be}; vals[be] = 0.0
        return max(abs(vals[pre_e[j + 1]] - vals[pre_e[j]]) for j in range(len(pre_e) - 1))
    delta_hat = dif_max(out["theta"])
    delta_b = np.array([dif_max(r) for r in th])
    media_b = out["media"] + D[:, k]
    factor = np.mean([e - be for e in range(0, E_POST + 1)])
    res = {"delta_pre_max": float(delta_hat), "factor": float(factor), "grid": {}}
    for M in mbar_grid:
        lo = float(np.quantile(media_b - M * delta_b * factor, 0.025)); hi = float(np.quantile(media_b + M * delta_b * factor, 0.975))
        res["grid"][str(M)] = {"ic_inf": lo, "ic_sup": hi, "sesgo_max": float(M * delta_hat * factor)}
    # punto de quiebre: menor M̄ (rejilla fina) en que el IC contiene 0
    quiebre = None
    for M in np.arange(0, 5.001, 0.05):
        lo = np.quantile(media_b - M * delta_b * factor, 0.025); hi = np.quantile(media_b + M * delta_b * factor, 0.975)
        if lo <= 0 <= hi:
            quiebre = float(round(M, 2)); break
    res["mbar_quiebre"] = quiebre
    # tendencia lineal previa (Δ^SD con M = 0): se ajusta una recta a θ(e), e = -8…-1, y se extrapola
    pe = np.array([e for e in ee if e < be] + [be])
    def corr(throw):
        y = np.array([throw[full_e.index(e)] for e in pe if e != be] + [0.0])
        b1, b0 = np.polyfit(pe, y, 1)
        return np.mean([throw[full_e.index(e)] - (b0 + b1 * e) for e in range(0, E_POST + 1) if e in full_e])
    c0 = corr(out["theta"]); cb = np.array([corr(r) for r in th])
    res["lineal"] = {"att": float(c0), "ic_inf": float(np.quantile(cb, 0.025)), "ic_sup": float(np.quantile(cb, 0.975))}
    return res


def largo(Y, G, w, extra=None):
    import pandas as pd
    n = len(G)
    mun = np.repeat(np.arange(n), T); anio = np.tile(np.array(ANIOS), n)
    Gr = np.repeat(G, T)
    e = np.where(np.isfinite(Gr), anio - np.where(np.isfinite(Gr), Gr, 0), np.nan)
    df = pd.DataFrame({"mun": mun, "anio": anio, "y": Y.reshape(-1), "w": np.repeat(w, T), "G": Gr, "e": e})
    df["D"] = ((df["e"] >= 0) & np.isfinite(df["G"])).astype(float)
    if extra is not None:
        for k, v in extra.items():
            df[k] = v.reshape(-1)
    return df.dropna(subset=["y"]).reset_index(drop=True)


def twfe(Y, G, w):
    import pyfixest as pf
    df = largo(Y, G, w)
    m = pf.feols("y ~ D | mun + anio", data=df, weights="w", vcov={"CRV1": "mun"})
    b, se = float(m.coef()["D"]), float(m.se()["D"])
    # dinámico con extremos agrupados (e <= -8 y e >= 6), referencia e = -1
    df["eb"] = np.where(np.isfinite(df["G"]), np.clip(df["e"], E_MIN, E_MAX), -1).astype(int)
    md = pf.feols("y ~ i(eb, ref=-1) | mun + anio", data=df, weights="w", vcov={"CRV1": "mun"})
    co = md.coef(); sd = md.se(); V = np.asarray(md._vcov); names = list(co.index)
    din = {}; L = np.zeros(len(names))
    for k in names:
        ev = int(float(k.split("::")[1].rstrip("]")))
        din[ev] = {"theta": float(co[k]), "ee": float(sd[k])}
        if 0 <= ev <= E_POST:
            L[names.index(k)] = 1.0
    L /= L.sum()
    bd = float(L @ co.values); sdd = float(math.sqrt(L @ V @ L))
    return {"att": b, "ee": se, "ic_inf": b - 1.96 * se, "ic_sup": b + 1.96 * se, "eventos": din,
            "din_0_5": {"att": bd, "ee": sdd, "ic_inf": bd - 1.96 * sdd, "ic_sup": bd + 1.96 * sdd}}


def wild_cluster(Y, G, w, B=B_MULT, seed=SEMILLA):
    """Bootstrap salvaje agrupado restringido (WCR, Rademacher) para el TWFE estático: H0 β = 0."""
    from pyfixest.estimation import demean
    df = largo(Y, G, w)
    fl = np.column_stack([df["mun"].to_numpy(), df["anio"].to_numpy() - ANIOS[0]]).astype(np.uint64)
    X = np.column_stack([df["y"].to_numpy(), df["D"].to_numpy()]).astype(float)
    Xd, _ = demean(X, fl, df["w"].to_numpy().astype(float))
    yt, dt = Xd[:, 0], Xd[:, 1]; wv = df["w"].to_numpy()
    cl = df["mun"].to_numpy(); ncl = cl.max() + 1
    den = (wv * dt * dt).sum()
    def est(y):
        b = (wv * dt * y).sum() / den
        u = y - b * dt
        sc = np.bincount(cl, weights=wv * dt * u, minlength=ncl)
        return b, math.sqrt((sc ** 2).sum()) / den
    b0, s0 = est(yt)
    rng = np.random.default_rng(seed)
    tb = np.empty(B)
    for r in range(B):
        v = rng.choice([-1.0, 1.0], size=ncl)
        bb, ss = est(yt * v[cl])
        tb[r] = bb / ss
    return {"att": float(b0), "t": float(b0 / s0), "p_wcr": float(np.mean(np.abs(tb) >= abs(b0 / s0)))}


def bacon(Y, G, w=None):
    """Descomposición de Goodman-Bacon (2021) del TWFE estático en el panel balanceado. Con pesos fijos por municipio (w),
    la descomposición se aplica al TWFE ponderado: equivale a replicar cada municipio en proporción a su peso, de modo que
    las participaciones de grupo y las medias son ponderadas y la suma reproduce el TWFE ponderado balanceado."""
    ok = ~np.isnan(Y).any(axis=1)
    if ok.sum() < 10:
        return {"no_aplica": "sin panel balanceado (años sin dato)"}
    Y = Y[ok]; G = G[ok]
    w = np.ones(len(G)) if w is None else w[ok]
    wn = w / w.sum()
    tt = np.arange(T)
    D = (np.isfinite(G)[:, None] & (tt[None, :] >= (np.where(np.isfinite(G), G, 1e9)[:, None] - ANIOS[0]))).astype(float)
    def within(X):
        return X - X.mean(1, keepdims=True) - (wn[:, None] * X).sum(0, keepdims=True) + (wn[:, None] * X).sum() / T
    Dt = within(D)
    beta = float((wn[:, None] * Dt * Y).sum() / (wn[:, None] * Dt ** 2).sum())
    U = np.isinf(G); nU = wn[U].sum()
    gs = sorted(set(G[np.isfinite(G)].astype(int)))
    nk = {g: wn[G == g].sum() for g in gs}; Dk = {g: (T - (g - ANIOS[0])) / T for g in gs}
    def m(sel, cols):
        return float((wn[sel][:, None] * Y[np.ix_(sel, cols)]).sum() / (wn[sel].sum() * len(cols)))
    comps = []
    for k in gs:
        ki = k - ANIOS[0]; sk = G == k
        if nU > 0:
            nkU = nk[k] / (nk[k] + nU)
            s_ = (nk[k] + nU) ** 2 * nkU * (1 - nkU) * Dk[k] * (1 - Dk[k])
            pre, post = tt[:ki], tt[ki:]
            b = (m(sk, post) - m(sk, pre)) - (m(U, post) - m(U, pre))
            comps.append(("tratado vs nunca tratado", s_, b))
    for a, k in enumerate(gs):
        for l in gs[a + 1:]:
            ki, li = k - ANIOS[0], l - ANIOS[0]
            nkl = nk[k] / (nk[k] + nk[l])
            sk_ = ((nk[k] + nk[l]) * (1 - Dk[l])) ** 2 * nkl * (1 - nkl) * ((Dk[k] - Dk[l]) / (1 - Dk[l])) * ((1 - Dk[k]) / (1 - Dk[l]))
            pre, mid, post = tt[:ki], tt[ki:li], tt[li:]
            bk = (m(G == k, mid) - m(G == k, pre)) - (m(G == l, mid) - m(G == l, pre))
            comps.append(("temprano vs tardío (aún no tratado)", sk_, bk))
            sl_ = ((nk[k] + nk[l]) * Dk[k]) ** 2 * nkl * (1 - nkl) * (Dk[l] / Dk[k]) * ((Dk[k] - Dk[l]) / Dk[k])
            bl = (m(G == l, post) - m(G == l, mid)) - (m(G == k, post) - m(G == k, mid))
            comps.append(("tardío vs temprano (ya tratado)", sl_, bl))
    tot = sum(c[1] for c in comps)
    out = {"twfe_balanceado": beta, "municipios": int(ok.sum()), "tipos": {}}
    for tipo in sorted(set(c[0] for c in comps)):
        cc = [c for c in comps if c[0] == tipo]
        ws = sum(c[1] for c in cc) / tot
        out["tipos"][tipo] = {"peso": float(ws), "estimado": float(sum(c[1] * c[2] for c in cc) / sum(c[1] for c in cc)), "comparaciones": len(cc)}
    out["suma_ponderada"] = float(sum(c[1] * c[2] for c in comps) / tot)
    return out


def sun_abraham(Y, G, w):
    """Sun y Abraham (2021): interacciones cohorte × periodo relativo (e = -8…6 sueltos; e < -8 y e > 6 agrupados por cohorte),
    efectos fijos de municipio y año, control = nunca tratados; θ(e) promedia las cohortes con su peso."""
    import pyfixest as pf
    sel = np.isinf(G) | np.isfinite(G)
    df = largo(Y[sel], G[sel], w[sel])
    gs = sorted(set(df.loc[np.isfinite(df["G"]), "G"].astype(int)))
    cols, meta, nuevas = [], [], {}
    for g in gs:
        eg = df["e"].where(df["G"] == g)
        for e in list(range(E_MIN, E_MAX + 1)) + ["lo", "hi"]:
            if e == -1:
                continue
            if e == "lo":
                v = (eg < E_MIN)
            elif e == "hi":
                v = (eg > E_MAX)
            else:
                v = (eg == e)
            v = v.fillna(False).astype(float)
            if v.sum() == 0:
                continue
            nm = f"sa_{g}_{e if isinstance(e, str) else ('m' + str(-e) if e < 0 else e)}"
            nuevas[nm] = v.to_numpy(); cols.append(nm); meta.append((g, e))
    import pandas as pd
    df = pd.concat([df, pd.DataFrame(nuevas, index=df.index)], axis=1)
    m = pf.feols("y ~ " + " + ".join(cols) + " | mun + anio", data=df, weights="w", vcov={"CRV1": "mun"})
    co = m.coef(); V = np.asarray(m._vcov); names = list(co.index)
    Wg = {g: w[G == g].sum() for g in gs}
    th, ses, ee = [], [], []
    L_post = np.zeros(len(names)); npost = 0
    for e in range(E_MIN, E_MAX + 1):
        if e == -1:
            continue
        L = np.zeros(len(names)); tot = 0.0
        for (g, ev), nm in zip(meta, cols):
            if ev == e and nm in names:
                L[names.index(nm)] = Wg[g]; tot += Wg[g]
        if tot == 0:
            continue
        L /= tot
        th.append(float(L @ co.values)); ses.append(float(math.sqrt(L @ V @ L))); ee.append(e)
        if 0 <= e <= E_POST:
            L_post += L; npost += 1
    L_post /= npost
    b = float(L_post @ co.values); se = float(math.sqrt(L_post @ V @ L_post))
    return {"att": b, "ee": se, "ic_inf": b - 1.96 * se, "ic_sup": b + 1.96 * se,
            "eventos": {e: {"theta": t, "ee": s} for e, t, s in zip(ee, th, ses)}}


def gardner(Y, G, w):
    """Gardner (2022), did2s de pyfixest: primera etapa con observaciones no tratadas (efectos de municipio y año),
    segunda etapa con indicadores de periodo relativo (extremos agrupados; nunca tratados en la referencia)."""
    import pyfixest as pf
    df = largo(Y, G, w)
    df["eb"] = np.where(np.isfinite(df["G"]), np.clip(df["e"], E_MIN, E_MAX), -1).astype(int)
    # municipios sin ninguna observación no tratada con dato (p. ej., prematuridad antes de 2008) no identifican su efecto fijo
    # (se exigen dos o más, porque pyfixest descarta los efectos fijos con una sola observación)
    cnt = df.loc[df["D"] == 0].groupby("mun").size()
    df = df[df["mun"].isin(cnt[cnt >= 2].index)].reset_index(drop=True)
    m = pf.did2s(df, yname="y", first_stage="~ 0 | mun + anio", second_stage="~ i(eb, ref=-1)", treatment="D",
                 cluster="mun", weights="w")
    co = m.coef(); V = np.asarray(m._vcov); names = list(co.index)
    din = {}
    for k in names:
        ev = int(float(k.split("::")[1].rstrip("]")))
        din[ev] = {"theta": float(co[k]), "ee": float(math.sqrt(V[names.index(k), names.index(k)]))}
    L = np.zeros(len(names))
    for k in names:
        ev = int(float(k.split("::")[1].rstrip("]")))
        if 0 <= ev <= E_POST:
            L[names.index(k)] = 1.0
    L /= L.sum()
    b = float(L @ co.values); se = float(math.sqrt(L @ V @ L))
    return {"att": b, "ee": se, "ic_inf": b - 1.96 * se, "ic_sup": b + 1.96 * se, "eventos": din}


def poisson_etwfe(Dn, N, G):
    """Poisson con efectos fijos de municipio y año y exposición (log de nacimientos), saturado en las celdas tratadas
    grupo de cohortes (trienios) × periodo relativo (Wooldridge, ETWFE); controles: nunca tratados y aún no tratados. Devuelve la razón de tasas promedio de
    e = 0…5 (ponderada por los nacimientos de cada celda) con IC por método delta y errores agrupados por municipio."""
    import pyfixest as pf
    df = largo(Dn, G, np.ones(len(G)), extra={"N": N})
    df = df[df["N"] > 0].reset_index(drop=True)
    df["lofs"] = np.log(df["N"])
    # cohortes agrupadas en trienios (2001–2003, 2004–2006, …) para evitar celdas sin muertes (separación)
    df["Gb"] = np.where(np.isfinite(df["G"]), ANIOS[0] + 3 * ((df["G"].fillna(0) - 2001) // 3) + 3, np.nan)
    gs = sorted(set(df.loc[np.isfinite(df["Gb"]), "Gb"].astype(int)))
    cols, meta, nuevas = [], [], {}
    for g in gs:
        for e in list(range(0, E_POST + 1)) + ["hi"]:
            if e == "hi":
                v = ((df["Gb"] == g) & (df["e"] > E_POST))
            else:
                v = ((df["Gb"] == g) & (df["e"] == e))
            if v.sum() == 0:
                continue
            nm = f"c_{g}_{e}"; nuevas[nm] = v.astype(float).to_numpy(); cols.append(nm); meta.append((g, e, float(df.loc[v, "N"].sum())))
    import pandas as pd
    df = pd.concat([df, pd.DataFrame(nuevas, index=df.index)], axis=1)
    m = pf.fepois("y ~ " + " + ".join(cols) + " | mun + anio", data=df, offset="lofs", vcov={"CRV1": "mun"})
    co = m.coef(); V = np.asarray(m._vcov); names = list(co.index)
    L = np.zeros(len(names))
    for (g, e, nn), nm in zip(meta, cols):
        if e != "hi" and nm in names:
            L[names.index(nm)] = nn
    L /= L.sum()
    b = float(L @ co.values); se = float(math.sqrt(L @ V @ L))
    return {"irr": math.exp(b), "ic_inf": math.exp(b - 1.96 * se), "ic_sup": math.exp(b + 1.96 * se), "log": b, "ee": se}


COVS = ["local", "lres", "noinst", "c4", "bp", "ces", "neo", "inf", "rural", "subs", "adol", "edb", "ldist", "alt", "pdet", "tend_local"]


def covariables(A, W, Y):
    R = W["res"]
    X = {k: primeros_anios(Y[k], R) for k in ["local", "lres", "noinst", "c4", "bp", "ces", "neo", "inf", "rural", "subs", "adol", "edb"]}
    X["ldist"] = np.log(A["d_centro_9800"].to_numpy())
    X["alt"] = A["alt"].to_numpy() / 1000.0
    X["pdet"] = A["pdet"].to_numpy().astype(float)
    # trayectoria previa de la cuota local: cambio entre 1998–2000 y 2001–2003 (puntos porcentuales)
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            X["tend_local"] = np.nanmean(Y["local"][:, 3:6], axis=1) - np.nanmean(Y["local"][:, 0:3], axis=1)
    M = np.column_stack([X[k] for k in COVS])
    # imputación por la media para los pocos faltantes (municipios creados después)
    col_mean = np.nanmean(M, axis=0)
    M = np.where(np.isnan(M), col_mean[None, :], M)
    return M


def logit(X, d, fw, iters=50):
    Z = np.column_stack([np.ones(len(X)), (X - X.mean(0)) / X.std(0)])
    b = np.zeros(Z.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-Z @ b))
        g = Z.T @ (fw * (d - p)) - 1e-4 * b
        H = (Z * (fw * p * (1 - p))[:, None]).T @ Z + 1e-4 * np.eye(len(b))
        st = np.linalg.solve(H, g); b += st
        if np.abs(st).max() < 1e-8:
            break
    return 1 / (1 + np.exp(-Z @ b))


def propension(Xc, G, fw=None):
    fw = np.ones(len(G)) if fw is None else fw
    return logit(Xc, np.isfinite(G).astype(float), fw)


def balance(Xc, G, keep, wctrl):
    """Diferencias estandarizadas (tratados menos nunca tratados) sin ponderar en toda la muestra y, en el soporte común,
    con los controles ponderados por p/(1-p). El denominador es la desviación conjunta de toda la muestra."""
    tr = np.isfinite(G); nv = np.isinf(G)
    out = {}
    for j, k in enumerate(COVS):
        x = Xc[:, j]
        sd = math.sqrt((x[tr].var() + x[nv].var()) / 2)
        mt, mc = x[tr].mean(), x[nv].mean()
        tk, nk = tr & keep, nv & keep
        mtw, mcw = x[tk].mean(), np.average(x[nk], weights=wctrl[nk])
        out[k] = {"tratados": float(mt), "nunca": float(mc), "dif_est": float((mt - mc) / sd) if sd > 0 else 0.0,
                  "tratados_soporte": float(mtw), "nunca_ipw": float(mcw), "dif_est_ipw": float((mtw - mcw) / sd) if sd > 0 else 0.0}
    return out


def cs_ipw(Yd, G, Xc, B=B_UNID, seed=SEMILLA):
    """CS con controles nunca tratados ponderados por p/(1-p) (versión IPW de Callaway y Sant'Anna, 2021), por municipio
    (sin ponderar por nacimientos) y en el soporte común (propensión entre 0,01 y 0,99). La propensión sale de una logística
    sobre covariables de 1998–2000 y la tendencia previa de la cuota local. Inferencia: bootstrap por municipios (B réplicas)
    que re-estima la propensión y el soporte común en cada réplica."""
    n = len(G)
    def una(fw):
        p = propension(Xc, G, fw)
        keep = (p >= P_MIN) & (p <= P_MAX) & (fw > 0)
        wc = np.where(keep, fw * p / (1 - p), 0.0); wt = np.where(keep, fw, 0.0)
        return {k: cs(Y, G, wt, control="never", con_if=False, w_ctrl=wc)["media"] for k, Y in Yd.items()}, p, keep, wc
    est, p, keep, wc = una(np.ones(n))
    rng = np.random.default_rng(seed)
    reps = {k: [] for k in Yd}
    for _ in range(B):
        fw = np.bincount(rng.integers(0, n, n), minlength=n).astype(float)
        e_, _, _, _ = una(fw)
        for k in Yd:
            reps[k].append(e_[k])
    out = {}
    for k in Yd:
        r = np.array(reps[k]); se = float(np.nanstd(r, ddof=1))
        out[k] = {"att": float(est[k]), "ee": se, "ic_inf": float(est[k] - 1.96 * se), "ic_sup": float(est[k] + 1.96 * se)}
    return out, p, keep, wc


def permutacion(Y, G, w, n_perm=N_PERM, seed=SEMILLA):
    """Inferencia por permutación: se reasignan al azar los años de cierre (incluido «nunca») entre los municipios de la
    muestra, conservando el tamaño de cada cohorte."""
    rng = np.random.default_rng(seed)
    obs = cs(Y, G, w, con_if=False)["media"]
    sims = np.array([cs(Y, rng.permutation(G), w, con_if=False)["media"] for _ in range(n_perm)])
    return {"att": float(obs), "p_perm": float((np.sum(np.abs(sims) >= abs(obs)) + 1) / (n_perm + 1))}
