"""Orquestación de las estimaciones del artículo (nivel A) y de los agregados del nivel B que reemplazan celdas suprimidas.

estimar() reproduce, con los paneles de data/intermedios/, todas las cifras de output/resultados.json y las tablas CSV.
Es la etapa «estimar» del script original del artículo, sin cambios de método.
"""
from __future__ import annotations

import gc
import json
import math
import time
from pathlib import Path

import numpy as np
import polars as pl

from .constantes import (ANIOS, B_MULT, B_UNID, E_MAX, E_MIN, E_POST, K_COP, K_EST, K_HET, K_MEC, K_PRIM, K_SEL,
                         K_SUPRIMIDOS, N_PERM, SEMILLA, T, VENTANA)
from .datos import ETIQ, cargar, pesos_base, primeros_anios, resultados
from .estimadores import (bacon, balance, bootstrap_mult, covariables, cs, cs_ipw, gardner, media_base,
                          permutacion, poisson_etwfe, rambachan_roth, resumen, sun_abraham, twfe, wild_cluster)
from .evento import definir_evento
from .rutas import INTERMEDIOS, OUT, relativa


def _f(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else float(x)


def limpiar(o):
    if isinstance(o, dict):
        return {str(k): limpiar(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [limpiar(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return _f(float(o))
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.ndarray):
        return limpiar(o.tolist())
    return o


def muertes_fuera(W, G, sm):
    """Porcentaje de las muertes neonatales de residentes de los tratados ocurridas fuera del municipio: en g-3…g-1, en g…g+5
    y por año desde el cierre. Necesita los conteos completos (nivel B)."""
    tr = np.isfinite(G)
    fu, ex = W["d_neo_fuera"][sm], W["d_neo_ext"][sm]
    perf = {}
    for nom_, (a_, b_) in {"previo": (-3, -1), "posterior": (0, 5)}.items():
        num = den = 0.0
        for i in np.where(tr)[0]:
            gi = ANIOS.index(int(G[i]))
            for t_ in range(max(0, gi + a_), min(T, gi + b_ + 1)):
                num += fu[i, t_]; den += ex[i, t_]
        perf[nom_] = float(100 * num / den)
    perf["por_e"] = {}
    for e in range(-8, 7):
        num = den = 0.0
        for i in np.where(tr)[0]:
            t_ = ANIOS.index(int(G[i])) + e
            if 0 <= t_ < T:
                num += fu[i, t_]; den += ex[i, t_]
        perf["por_e"][e] = float(100 * num / den) if den else None
    return perf


def agregados_nivel_b(carpeta: Path) -> tuple[dict, np.ndarray]:
    """Con el panel completo (sin suprimir) de `carpeta`, calcula las cifras que el panel publicado ya no permite
    reproducir: el efecto sobre la pertenencia étnica y las muertes infantiles en domicilio (mismo estimador que el resto),
    el porcentaje de muertes neonatales ocurridas fuera del municipio y la marca municipal «20 % o más de nacimientos de
    grupos étnicos en 2008–2011». Son agregados de muchos municipios y se publican en agregados_nivel_b.json."""
    A, W = cargar(carpeta); Y = resultados(W); w_all = pesos_base(W)
    G_all, _ = definir_evento(W)
    sm = ~np.isnan(G_all); G, w = G_all[sm], w_all[sm]; n = int(sm.sum())
    princ = {}
    for k in K_SUPRIMIDOS:
        o = cs(Y[k][sm], G, w); bs = bootstrap_mult(o, n)
        r_ = resumen(o, bs); r_["media_base"] = media_base(Y[k][sm], G, w)
        princ[k] = r_
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)      # municipios sin nacimientos con etnia conocida en 2008–2011
        etn = np.nanmean(Y["etn"][:, ANIOS.index(2008):ANIOS.index(2011) + 1], axis=1)
    out = {"principal": limpiar(princ), "muertes_fuera": limpiar(muertes_fuera(W, G, sm)),
           "etn_mediana_tratados": float(np.nanmedian(etn[sm][np.isfinite(G)]))}
    return out, np.nan_to_num(etn) >= 20



def estimar(carpeta: Path | None = None, salida: Path | None = None):
    """Todas las estimaciones del artículo desde los paneles de data/intermedios/ (nivel A). Escribe salida/resultados.json
    y salida/tablas/*.csv. Las cifras de los resultados con celdas suprimidas se toman de agregados_nivel_b.json."""
    import warnings
    warnings.filterwarnings("ignore")
    t0 = time.time()
    carpeta = carpeta or INTERMEDIOS; salida = salida or OUT
    (salida / "tablas").mkdir(parents=True, exist_ok=True)
    f_ag = carpeta / "agregados_nivel_b.json"
    ag = json.loads(f_ag.read_text(encoding="utf-8")) if f_ag.exists() else None
    A, W = cargar(carpeta); Y = resultados(W); w_all = pesos_base(W)
    G_all, S = definir_evento(W)
    sm = ~np.isnan(G_all)
    G, w = G_all[sm], w_all[sm]
    Ys = {k: v[sm] for k, v in Y.items()}
    As = A.filter(pl.Series(sm))
    n = int(sm.sum())
    res = {"parametros": {"alto": 0.25, "bajo": 0.10, "persistencia": 2, "anios_estables": 3, "min_nacimientos": 30,
                          "ventana": [E_MIN, E_MAX], "horizonte": E_POST, "B_mult": B_MULT, "B_unid": B_UNID, "permutaciones": N_PERM,
                          "semilla": SEMILLA}}

    # muestra
    tr = np.isfinite(G)
    coh = {int(g): int((G == g).sum()) for g in sorted(set(G[tr].astype(int)))}
    eleg = W["res"].mean(axis=1) >= 30
    nac = W["res"]
    i2325 = [ANIOS.index(a) for a in (2023, 2024, 2025)]
    res["muestra"] = {
        "municipios_divipola": int(len(G_all)), "elegibles": int(eleg.sum()), "tratados": int(tr.sum()), "nunca": int(np.isinf(G).sum()),
        "excluidos_elegibles": int(eleg.sum() - sm.sum()), "cohortes": coh,
        "tratados_2001_2010": int(((G >= 2001) & (G <= 2010)).sum()), "tratados_2011_2020": int(((G >= 2011) & (G <= 2020)).sum()),
        "tratados_2021_2024": int(((G >= 2021) & (G <= 2024)).sum()),
        "nac_anual_tratados_2023_2025": float(nac[sm][tr][:, i2325].sum() / 3),
        "nac_anual_nunca_2023_2025": float(nac[sm][np.isinf(G)][:, i2325].sum() / 3),
        "nac_anual_pais_2023_2025": float(nac[:, i2325].sum() / 3),
        "tratados_pdet": int(As.filter(pl.Series(tr))["pdet"].sum()),
        "tratados_con_sala_reps2022": int((As.filter(pl.Series(tr))["salas_reps2022"].to_numpy() > 0).sum()),
        "tratados_hasta_2022": int((G <= 2022).sum()),
        "tratados_hasta_2022_con_sala": int(((G <= 2022) & (As["salas_reps2022"].to_numpy() > 0)).sum()),
        "nunca_con_sala_reps2022": int((As.filter(pl.Series(np.isinf(G)))["salas_reps2022"].to_numpy() > 0).sum()),
        "d_centro_mediana_tratados": float(np.median(As.filter(pl.Series(tr))["d_centro_0810"].to_numpy())),
        "d_centro_mediana_nunca": float(np.median(As.filter(pl.Series(np.isinf(G)))["d_centro_0810"].to_numpy())),
        "tratados_d25": int((As.filter(pl.Series(tr))["d_centro_0810"].to_numpy() >= 25).sum()),
    }
    # cuota local alrededor del evento (descriptivo, ponderado)
    Ssm = S[sm]; perfil = {}
    for e in range(-14, 7):
        vals, ws_ = [], []
        for i in np.where(tr)[0]:
            ti = ANIOS.index(int(G[i])) + e
            if 0 <= ti < T:
                vals.append(Ssm[i, ti]); ws_.append(w[i])
        if vals:
            perfil[e] = float(100 * np.average(vals, weights=ws_))
    res["cuota_local_tratados_por_e"] = perfil
    nv = np.isinf(G)
    res["cuota_local_nunca_por_anio"] = {a: float(100 * np.average(Ssm[nv, j], weights=w[nv])) for j, a in enumerate(ANIOS)}
    dep = As.filter(pl.Series(tr)).group_by("ndp").len().sort(["len", "ndp"], descending=[True, False])
    res["tratados_por_departamento"] = {r_[0]: r_[1] for r_ in dep.rows()}
    print(f"muestra lista ({time.time() - t0:.0f} s)", flush=True)

    # descriptivos (tabla 1): 1998–2000 y 2023–2025, tratados y nunca tratados, ponderados por nacimientos del periodo
    desc = {}
    for k in K_PRIM + K_MEC + K_SEL:
        if k in ("lres",) or k in K_SUPRIMIDOS:
            continue
        fila = {}
        for nom, sel in [("tratados", tr), ("nunca", nv)]:
            for per, cols in [("9800", [0, 1, 2]), ("2325", i2325)]:
                X = Ys[k][sel][:, cols]; Wt = nac[sm][sel][:, cols]
                ok = ~np.isnan(X)
                fila[f"{nom}_{per}"] = float((X[ok] * Wt[ok]).sum() / Wt[ok].sum()) if ok.any() and Wt[ok].sum() > 0 else None
        desc[k] = fila
    res["descriptivos"] = desc
    res["descriptivos_municipio"] = {
        "nac_9800_tratados": float(np.mean(w[tr])), "nac_9800_nunca": float(np.mean(w[nv])),
        "d_centro_tratados": float(np.mean(As.filter(pl.Series(tr))["d_centro_0810"].to_numpy())),
        "d_centro_nunca": float(np.mean(As.filter(pl.Series(nv))["d_centro_0810"].to_numpy())),
        "alt_tratados": float(np.nanmean(As.filter(pl.Series(tr))["alt"].to_numpy())),
        "alt_nunca": float(np.nanmean(As.filter(pl.Series(nv))["alt"].to_numpy())),
        "pdet_tratados": float(100 * As.filter(pl.Series(tr))["pdet"].mean()), "pdet_nunca": float(100 * As.filter(pl.Series(nv))["pdet"].mean()),
    }

    # resultados principales: CS, aún no tratados + nunca tratados, base g-1, ponderado
    princ, bss = {}, {}
    for k in K_PRIM + K_MEC + K_SEL:
        if k in K_SUPRIMIDOS and ag is not None:      # numeradores suprimidos en el panel publicado: cifra del nivel B
            princ[k] = ag["principal"][k]
            continue
        o = cs(Ys[k], G, w); bs = bootstrap_mult(o, n)
        r_ = resumen(o, bs); r_["media_base"] = media_base(Ys[k], G, w)
        princ[k] = r_; bss[k] = (o, bs)
    from scipy.stats import norm
    ps = sorted([(princ[k]["p"], k) for k in K_PRIM])
    m_ = len(ps); holm = {}; acum = 0.0
    for j, (p_, k) in enumerate(ps):
        acum = max(acum, min(1.0, (m_ - j) * p_)); holm[k] = acum
    for k in K_PRIM:
        princ[k]["p_holm"] = holm[k]
    res["principal"] = princ
    print(f"principal listo ({time.time() - t0:.0f} s)", flush=True)

    # especificaciones coprincipales (revisión de árbitro): base, grupo de control y ponderación
    pob18 = W["pob_tot"][sm][:, ANIOS.index(2018)]
    grandes = np.nan_to_num(pob18) >= 500_000
    res["ciudades_grandes"] = {"umbral": 500000, "municipios": int(grandes.sum()), "tratados": int((grandes & tr).sum()),
                               "nombres": sorted(As.filter(pl.Series(grandes))["nmun"].to_list())}
    rng = np.random.default_rng(SEMILLA)
    Vb = rng.choice([-1.0, 1.0], size=(B_MULT, n))      # las mismas réplicas que bootstrap_mult: permite cocientes conjuntos
    def iqr_se(D):
        return float((np.quantile(D, 0.75) - np.quantile(D, 0.25)) / 1.3489795)
    specs = {"A_base_g1": dict(), "B_post_menos_previo": "pmp", "C_base_promedio": dict(base_win=VENTANA),
             "D_solo_tratados": dict(control="tronly"), "D2_solo_tratados_promedio": dict(control="tronly", base_win=VENTANA),
             "E_sin_ponderar": dict(w1=True), "E2_sin_ponderar_promedio": dict(w1=True, base_win=VENTANA),
             "F_sin_grandes": dict(excl_ctrl=grandes), "F2_sin_grandes_promedio": dict(excl_ctrl=grandes, base_win=VENTANA)}
    cop, draws = {}, {}
    for nom, kw in specs.items():
        cop[nom] = {}
        for k in K_COP:
            if kw == "pmp":
                o = cs(Ys[k], G, w)
                pr = (o["e"] >= VENTANA[0]) & (o["e"] <= VENTANA[1])
                est_ = o["media"] - o["theta"][pr].mean(); psi = o["psi_media"] - o["psi"][pr].mean(axis=0)
                D = Vb @ psi / n
            else:
                kw2 = dict(kw); ww = np.ones(n) if kw2.pop("w1", False) else w
                o = cs(Ys[k], G, ww, **kw2); D = Vb @ o["psi_media"] / n; est_ = o["media"]
            se_ = iqr_se(D)
            from scipy.stats import norm
            cop[nom][k] = {"att": float(est_), "ee": se_, "ic_inf": float(est_ - 1.96 * se_), "ic_sup": float(est_ + 1.96 * se_),
                           "p": float(2 * (1 - norm.cdf(abs(est_ / se_)))) if se_ > 0 else None}
            draws[(nom, k)] = (est_, D)
        # Holm dentro de la familia primaria para cada especificación
        ps = sorted([(cop[nom][k]["p"], k) for k in K_PRIM if k in cop[nom]])
        acum = 0.0
        for j, (p_, k) in enumerate(ps):
            acum = max(acum, min(1.0, (len(ps) - j) * p_)); cop[nom][k]["p_holm"] = acum
    res["coprincipales"] = cop
    # escalado tipo Wald: efecto por cada nacimiento que deja de ocurrir en el municipio (cociente con la cuota local)
    esc = {}
    for nom in ["A_base_g1", "B_post_menos_previo", "C_base_promedio"]:
        e0, D0 = draws[(nom, "local")]
        esc[nom] = {"primera_etapa": float(e0)}
        for k in ["neo", "neo_prec", "inf", "pre37", "bp"]:
            e1, D1 = draws[(nom, k)]
            r0 = e1 / (-e0 / 100); rb = (e1 + D1) / (-(e0 + D0) / 100)
            base_k = princ[k]["media_base"]
            esc[nom][k] = {"escalado": float(r0), "ic_inf": float(np.quantile(rb, 0.025)), "ic_sup": float(np.quantile(rb, 0.975)),
                           "sup_simple": float(cop[nom][k]["ic_sup"] / (-e0 / 100)), "pct_base_sup_simple": float(100 * cop[nom][k]["ic_sup"] / (-e0 / 100) / base_k),
                           "pct_base": float(100 * r0 / base_k)}
    res["escalado_wald"] = esc
    # composición del peso de los controles (e = 0…5, especificación A)
    o = cs(Ys["neo"], G, w, info=True, con_if=False)
    top = np.argsort(-o["peso_ctrl"])[:5]
    res["peso_controles"] = {"nunca_tratados": float(o["peso_nunca"]),
                             "principales": [(As["nmun"][int(i)], float(o["peso_ctrl"][i])) for i in top],
                             "grandes": float(o["peso_ctrl"][grandes].sum())}
    # registro de defunciones: dónde ocurren las muertes neonatales de residentes de los tratados (M5)
    res["muertes_fuera"] = ag["muertes_fuera"] if ag is not None else muertes_fuera(W, G, sm)
    print(f"coprincipales listas ({time.time() - t0:.0f} s)", flush=True)

    # ventana larga (descriptiva) para la figura
    res["ventana_larga"] = {}
    for k in ["local", "km", "ces", "neo", "c4", "noinst"]:
        o = cs(Ys[k], G, w, emin=-14); bs = bootstrap_mult(o, n, B=499)
        res["ventana_larga"][k] = {int(e): {"theta": float(t), "ee": float(s)} for e, t, s in zip(o["e"], o["theta"], bs["se"])}

    # anticipación
    res["anticipacion"] = {}
    for k in K_PRIM + ["km", "local"]:
        res["anticipacion"][k] = {}
        for d in (3, 5):
            o = cs(Ys[k], G, w, emin=-8 - d, anticip=d); bs = bootstrap_mult(o, n)
            r_ = resumen(o, bs); del r_["eventos"]
            res["anticipacion"][k][str(d)] = r_

    # base promedio por distancia al centro de partos
    res["base_promedio_distancia"] = {}
    lejos = As["d_centro_0810"].to_numpy() >= 25
    for grp, mm in [("25 km o más", lejos), ("menos de 25 km", ~lejos)]:
        res["base_promedio_distancia"][grp] = {}
        for k in ["km", "km50", "neo", "neo_prec", "inf", "pre37"]:
            o = cs(Ys[k][mm], G[mm], w[mm], base_win=VENTANA); bs = bootstrap_mult(o, int(mm.sum()))
            r_ = resumen(o, bs); del r_["eventos"]
            res["base_promedio_distancia"][grp][k] = r_
    # estudios de eventos con base promedio (niveles frente al promedio previo) para las figuras
    res["eventos_base_promedio"] = {}
    for k in ["neo", "neo_prec", "inf", "pre37", "km", "ces"]:
        o = cs(Ys[k], G, w, base_win=VENTANA); bs = bootstrap_mult(o, n)
        res["eventos_base_promedio"][k] = resumen(o, bs)["eventos"]

    # Rambachan y Roth
    res["rambachan_roth"] = {k: rambachan_roth(*bss[k]) for k in K_PRIM + ["km", "km50"]}
    print(f"RR listo ({time.time() - t0:.0f} s)", flush=True)

    # comparación de estimadores
    est = {}
    for k in K_EST:
        e_ = {}
        o = cs(Ys[k], G, w, control="never"); bs = bootstrap_mult(o, n); r_ = resumen(o, bs)
        e_["cs_nunca"] = {kk: r_[kk] for kk in ("att", "ee", "ic_inf", "ic_sup")}
        o = cs(Ys[k], G, np.ones(n)); bs = bootstrap_mult(o, n); r_ = resumen(o, bs)
        e_["cs_sin_ponderar"] = {kk: r_[kk] for kk in ("att", "ee", "ic_inf", "ic_sup")}
        e_["sun_abraham"] = sun_abraham(Ys[k], G, w)
        e_["gardner"] = gardner(Ys[k], G, w)
        e_["twfe"] = twfe(Ys[k], G, w)
        e_["wcr"] = wild_cluster(Ys[k], G, w)
        e_["bacon"] = bacon(Ys[k], G, w)
        e_["bacon_sin_ponderar"] = bacon(Ys[k], G)
        e_["permutacion"] = permutacion(Ys[k], G, w)
        est[k] = e_
        gc.collect()   # pyfixest deja copias grandes de los datos; se liberan antes del siguiente resultado
        print(f"  estimadores {k} ({time.time() - t0:.0f} s)", flush=True)
    res["estimadores"] = est

    # Poisson para las muertes
    Dn = {"neo": W["d_neo_prec"] + W["d_neo_tard"], "neo_prec": W["d_neo_prec"], "posneo": W["d_posneo"], "inf": W["d_inf"]}
    gc.collect()
    res["poisson"] = {k: poisson_etwfe(v[sm], W["res"][sm], G) for k, v in Dn.items()}
    gc.collect()
    res["poisson_distancia"] = {grp: {k: poisson_etwfe(Dn[k][sm][mm], W["res"][sm][mm], G[mm]) for k in ("neo", "inf")}
                                for grp, mm in [("25 km o más", lejos), ("menos de 25 km", ~lejos)]}
    print(f"Poisson listo ({time.time() - t0:.0f} s)", flush=True)

    # IPW sobre trayectorias previas
    Xc = covariables(As, {k: v[sm] for k, v in W.items()}, Ys)
    ipw, p, keep, wc = cs_ipw({k: Ys[k] for k in K_EST + ["local"]}, G, Xc)
    res["ipw"] = ipw
    res["balance"] = balance(Xc, G, keep, wc)
    res["propension"] = {"p_tratados_mediana": float(np.median(p[tr])), "p_nunca_mediana": float(np.median(p[nv])),
                         "fuera_soporte": int((~keep).sum()), "tratados_soporte": int((keep & tr).sum()), "nunca_soporte": int((keep & nv).sum()),
                         "max_dif_est_ipw": float(max(abs(v["dif_est_ipw"]) for v in res["balance"].values())),
                         "max_dif_est": float(max(abs(v["dif_est"]) for v in res["balance"].values()))}
    print(f"IPW listo ({time.time() - t0:.0f} s)", flush=True)

    # definiciones alternativas
    variantes = {
        "principal": {},
        "abrupto": "abrupto",
        "volumen_24_12": dict(base="volumen", alto=24, bajo=12),
        "alto50_bajo25": dict(alto=0.5, bajo=0.25),
        "bajo5": dict(bajo=0.05),
        "persistencia3": dict(persist=3),
        "estable5": dict(k=5),
        "min50": dict(minres=50),
        "sin_sitio_local": dict(sit9=True),
        "balanceado_2020": "bal",
        "sin_2020_2021": "pand",
        "solo_aun_no": "nyt",
        "sin_2025": dict(anio_max=2024),
    }
    defs = {}
    for nom, kw in variantes.items():
        if isinstance(kw, dict):
            Gv, _ = definir_evento(W, **kw)
        else:
            Gv = G_all.copy()
            if kw == "abrupto":
                for i in np.where(np.isfinite(Gv))[0]:
                    if S[i, ANIOS.index(int(Gv[i])) - 3] < 0.25:
                        Gv[i] = np.nan
            if kw == "bal":
                Gv[np.isfinite(Gv) & (Gv > 2020)] = np.nan
        smv = ~np.isnan(Gv); Gs_ = Gv[smv]; ws_ = w_all[smv]
        fila = {"tratados": int(np.isfinite(Gs_).sum()), "nunca": int(np.isinf(Gs_).sum())}
        for k in ["local", "km", "km50"] + K_PRIM:
            Yk = Y[k][smv].copy()
            ctrl = "notyet"
            if kw == "pand":
                Yk[:, [ANIOS.index(2020), ANIOS.index(2021)]] = np.nan
            if isinstance(kw, dict) and kw.get("anio_max"):
                Yk[:, ANIOS.index(kw["anio_max"]) + 1:] = np.nan
            if kw == "nyt":
                Yk = Yk[np.isfinite(Gs_)]; Gq = Gs_[np.isfinite(Gs_)]; wq = ws_[np.isfinite(Gs_)]
                o = cs(Yk, Gq, wq, control="notyet"); bs = bootstrap_mult(o, len(Gq))
            else:
                o = cs(Yk, Gs_, ws_, control=ctrl); bs = bootstrap_mult(o, int(smv.sum()))
            r_ = resumen(o, bs)
            fila[k] = {kk: r_[kk] for kk in ("att", "ee", "ic_inf", "ic_sup", "pre", "p_wald_pre")}
            if k in ("neo_prec", "inf", "pre37"):
                if kw == "nyt":
                    o = cs(Yk, Gq, wq, control="notyet", base_win=VENTANA); bs = bootstrap_mult(o, len(Gq))
                else:
                    o = cs(Yk, Gs_, ws_, control=ctrl, base_win=VENTANA); bs = bootstrap_mult(o, int(smv.sum()))
                r_ = resumen(o, bs)
                fila[k + "_C"] = {kk: r_[kk] for kk in ("att", "ee", "ic_inf", "ic_sup")}
        defs[nom] = fila
        print(f"  definición {nom} ({time.time() - t0:.0f} s)", flush=True)
    res["definiciones"] = defs

    # heterogeneidad (muestra partida: tratados y controles del mismo grupo)
    if "etnico20" in As.columns:
        etn20 = As["etnico20"].to_numpy().astype(bool)
    else:
        etn20 = np.nan_to_num(np.nanmean(Ys["etn"][:, ANIOS.index(2008):ANIOS.index(2011) + 1], axis=1)) >= 20
    subs0810 = np.nanmean(Ys["subs"][:, ANIOS.index(2008):ANIOS.index(2011) + 1], axis=1)
    rur = primeros_anios(Ys["rural"], nac[sm])
    dcen = As["d_centro_0810"].to_numpy()
    pdet = As["pdet"].to_numpy()
    dims = {"distancia": (dcen >= 25, "25 km o más", "menos de 25 km"),
            "ruralidad": (rur >= 50, "mayoría rural", "mayoría urbana"),
            "etnia": (etn20, "20 % o más étnico", "menos de 20 % étnico"),
            "pdet": (pdet, "PDET", "no PDET"),
            "regimen": (subs0810 >= 80, "80 % o más subsidiado", "menos de 80 % subsidiado")}
    het = {}
    for dnom, (mask, a_, b_) in dims.items():
        het[dnom] = {}
        for gnom, mm in [(a_, mask), (b_, ~mask)]:
            fila = {"tratados": int((mm & tr).sum()), "controles": int((mm & nv).sum())}
            for k in K_HET:
                o = cs(Ys[k][mm], G[mm], w[mm]); bs = bootstrap_mult(o, int(mm.sum())); r_ = resumen(o, bs)
                fila[k] = {kk: r_[kk] for kk in ("att", "ee", "ic_inf", "ic_sup", "p")}
            for k in ("neo_prec", "inf"):
                o = cs(Ys[k][mm], G[mm], w[mm], base_win=VENTANA); bs = bootstrap_mult(o, int(mm.sum())); r_ = resumen(o, bs)
                fila[k + "_C"] = {kk: r_[kk] for kk in ("att", "ee", "ic_inf", "ic_sup", "p")}
            het[dnom][gnom] = fila
    # por periodo del cierre (se parte solo a los tratados)
    het["periodo"] = {}
    for gnom, mm in [("2001–2014", tr & (G <= 2014)), ("2015–2024", tr & (G >= 2015))]:
        keep = mm | nv
        fila = {"tratados": int(mm.sum()), "controles": int(nv.sum())}
        Gq = G.copy(); Gq[~keep] = np.nan; q = ~np.isnan(Gq)
        for k in K_HET:
            o = cs(Ys[k][q], Gq[q], w[q]); bs = bootstrap_mult(o, int(q.sum())); r_ = resumen(o, bs)
            fila[k] = {kk: r_[kk] for kk in ("att", "ee", "ic_inf", "ic_sup", "p")}
        for k in ("neo_prec", "inf"):
            o = cs(Ys[k][q], Gq[q], w[q], base_win=VENTANA); bs = bootstrap_mult(o, int(q.sum())); r_ = resumen(o, bs)
            fila[k + "_C"] = {kk: r_[kk] for kk in ("att", "ee", "ic_inf", "ic_sup", "p")}
        het["periodo"][gnom] = fila
    # Benjamini-Hochberg sobre todas las pruebas de heterogeneidad (grupos × resultados × especificaciones)
    celdas = [(d, g, k) for d in het for g in het[d] for k, v in het[d][g].items() if isinstance(v, dict)]
    pv = np.array([het[d][g][k]["p"] for d, g, k in celdas]); orden = np.argsort(pv); m_bh = len(pv)
    q = np.empty(m_bh); prev = 1.0
    for rank in range(m_bh, 0, -1):
        j = orden[rank - 1]; prev = min(prev, pv[j] * m_bh / rank); q[j] = prev
    for (d, g, k), qq in zip(celdas, q):
        het[d][g][k]["q_bh"] = float(qq)
    res["bh_pruebas"] = int(m_bh); res["bh_q_min"] = float(q.min())
    res["heterogeneidad"] = het
    res["umbrales_heterogeneidad"] = {"etn_mediana_tratados": (ag["etn_mediana_tratados"] if ag is not None else
                                                               float(np.nanmedian(np.nanmean(Ys["etn"][:, ANIOS.index(2008):ANIOS.index(2011) + 1], axis=1)[tr]))),
                                      "subs_mediana_tratados": float(np.nanmedian(subs0810[tr])),
                                      "rural_mediana_tratados": float(np.nanmedian(rur[tr]))}
    print(f"heterogeneidad lista ({time.time() - t0:.0f} s)", flush=True)

    # magnitudes para un tomador de decisiones
    nt = res["muestra"]["nac_anual_tratados_2023_2025"]
    mag = {}
    for k in ["neo", "inf", "neo_prec"]:
        for nom in ["B_post_menos_previo", "C_base_promedio"]:
            r_ = res["coprincipales"][nom][k]
            mag[f"{k}|{nom}"] = {"muertes_anuales": r_["att"] * nt / 1000, "ic_inf": r_["ic_inf"] * nt / 1000, "ic_sup": r_["ic_sup"] * nt / 1000,
                                  "pct_base": 100 * r_["att"] / princ[k]["media_base"],
                                  "pct_base_sup": 100 * r_["ic_sup"] / princ[k]["media_base"], "pct_base_inf": 100 * r_["ic_inf"] / princ[k]["media_base"]}
        r_ = princ[k]
        mag[k] = {"muertes_anuales": r_["att"] * nt / 1000, "ic_inf": r_["ic_inf"] * nt / 1000, "ic_sup": r_["ic_sup"] * nt / 1000,
                  "pct_base_sup": 100 * r_["ic_sup"] / r_["media_base"], "pct_base_inf": 100 * r_["ic_inf"] / r_["media_base"]}
    res["magnitudes"] = mag

    (salida / "resultados.json").write_text(json.dumps(limpiar(res), ensure_ascii=False, indent=1), encoding="utf-8")
    # tablas CSV
    tablas(res, salida / "tablas")
    # municipios tratados (lista pública, agregada)
    lista = As.select("mun", "ndp", "nmun", "pdet", "salas_reps2022", "d_centro_0810").with_columns(
        pl.Series("anio_cierre", np.where(np.isfinite(G), G, np.nan)), pl.Series("nac_9800", w)).filter(pl.Series(tr)).sort("anio_cierre")
    lista.write_csv(salida / "tablas" / "municipios_tratados.csv")
    print("->", relativa(salida / "resultados.json"), f"({time.time() - t0:.0f} s)")


def tablas(res, dest: Path):
    """Tablas CSV del artículo (cifras con todos sus decimales; el redondeo lo hace el texto)."""
    filas = []
    for nom, d in res["coprincipales"].items():
        for k, v in d.items():
            filas.append({"especificacion": nom, "resultado": k, **{kk: v.get(kk) for kk in ("att", "ee", "ic_inf", "ic_sup", "p", "p_holm")}})
    pl.DataFrame(filas).write_csv(dest / "tabla2b_coprincipales.csv")
    filas = []
    for nom, d in res["escalado_wald"].items():
        for k, v in d.items():
            if isinstance(v, dict):
                filas.append({"especificacion": nom, "primera_etapa": d["primera_etapa"], "resultado": k, **v})
    pl.DataFrame(filas).write_csv(dest / "tablaF_escalado_wald.csv")
    filas = []
    for k, r_ in res["principal"].items():
        filas.append({"resultado": k, "etiqueta": ETIQ.get(k, k), "media_base": r_["media_base"], "att": r_["att"], "ee": r_["ee"],
                      "ic_inf": r_["ic_inf"], "ic_sup": r_["ic_sup"], "p": r_["p"], "p_holm": r_.get("p_holm"),
                      "pre": r_["pre"], "p_wald_pre": r_["p_wald_pre"]})
    pl.DataFrame(filas).write_csv(dest / "tabla2_principal.csv")
    filas = []
    for k, d in res["descriptivos"].items():
        filas.append({"variable": k, "etiqueta": ETIQ.get(k, k), **d})
    pl.DataFrame(filas).write_csv(dest / "tabla1_descriptivos.csv")
    filas = []
    for k, e_ in res["estimadores"].items():
        base = res["principal"][k]
        filas.append({"resultado": k, "cs_aun_no": base["att"], "cs_aun_no_inf": base["ic_inf"], "cs_aun_no_sup": base["ic_sup"],
                      **{f"{nm}{suf}": e_[nm][c] for nm in ("cs_nunca", "cs_sin_ponderar", "sun_abraham", "gardner", "twfe")
                         for suf, c in (("", "att"), ("_inf", "ic_inf"), ("_sup", "ic_sup"))},
                      "twfe_p_wcr": e_["wcr"]["p_wcr"], "p_permutacion": e_["permutacion"]["p_perm"],
                      "ipw": res["ipw"][k]["att"], "ipw_inf": res["ipw"][k]["ic_inf"], "ipw_sup": res["ipw"][k]["ic_sup"]})
    pl.DataFrame(filas).write_csv(dest / "tabla3_estimadores.csv")
    filas = []
    for k, e_ in res["estimadores"].items():
        for pond, b in (("ponderado", e_["bacon"]), ("sin ponderar", e_["bacon_sin_ponderar"])):
            if "tipos" not in b:
                continue
            for tipo, v in b["tipos"].items():
                filas.append({"resultado": k, "ponderacion": pond, "tipo": tipo, "peso": v["peso"], "estimado": v["estimado"],
                              "comparaciones": v["comparaciones"], "twfe_balanceado": b["twfe_balanceado"]})
    pl.DataFrame(filas).write_csv(dest / "tablaA_bacon.csv")
    filas = []
    for nom, f in res["definiciones"].items():
        for k, v in f.items():
            if isinstance(v, dict):
                filas.append({"definicion": nom, "tratados": f["tratados"], "nunca": f["nunca"], "resultado": k, **v})
    pl.DataFrame(filas).write_csv(dest / "tablaB_definiciones.csv")
    filas = []
    for dnom, gg in res["heterogeneidad"].items():
        for gnom, f in gg.items():
            for k, v in f.items():
                if isinstance(v, dict):
                    filas.append({"dimension": dnom, "grupo": gnom, "tratados": f["tratados"], "controles": f["controles"], "resultado": k, **v})
    pl.DataFrame(filas).write_csv(dest / "tablaC_heterogeneidad.csv")
    filas = []
    for k, r_ in res["rambachan_roth"].items():
        for M, v in r_["grid"].items():
            filas.append({"resultado": k, "mbar": float(M), **v, "delta_pre_max": r_["delta_pre_max"], "mbar_quiebre": r_["mbar_quiebre"]})
    pl.DataFrame(filas).write_csv(dest / "tablaD_rambachan_roth.csv")
    filas = [{"covariable": k, **v} for k, v in res["balance"].items()]
    pl.DataFrame(filas).write_csv(dest / "tablaE_balance.csv")
    filas = []
    for k, r_ in res["principal"].items():
        for e, v in r_["eventos"].items():
            filas.append({"resultado": k, "e": int(e), **v})
    pl.DataFrame(filas).write_csv(dest / "estudio_eventos_cs.csv")
