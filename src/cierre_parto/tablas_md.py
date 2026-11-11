"""Tablas en Markdown del manuscrito a partir de output/resultados.json (las usan pruebas/verificar_cifras.py y quien
actualice el manuscrito: `python -m cierre_parto.tablas_md` desde src/)."""
import json

from .rutas import OUT

RES = OUT / "resultados.json"

ETQ = {"local": "Parto en institución del propio municipio (%)", "km": "Distancia media al sitio del parto (km)",
       "km50": "Parto a más de 50 km (%)", "noinst": "Parto no institucional (%)", "dom": "Parto en domicilio (%)",
       "c4": "Cuatro o más controles prenatales (%)", "c0": "Ningún control prenatal (%)", "medico": "Parto atendido por médico (%)",
       "bp": "Bajo peso al nacer (%)", "pre38": "37 semanas o menos (%)", "pre37": "Prematuro, menos de 37 semanas (%)", "inf_dom": "Muertes infantiles en domicilio (por 1.000)", "ces": "Cesárea (%)",
       "neo": "Mortalidad neonatal (por 1.000)", "neo_prec": "Mortalidad neonatal precoz (por 1.000)",
       "posneo": "Mortalidad posneonatal (por 1.000)", "inf": "Mortalidad infantil (por 1.000)",
       "lres": "Log de nacimientos de residentes", "compl": "Nacimientos / población de 0 años (%)",
       "adol": "Madres de 10 a 19 años (%)", "e35": "Madres de 35 años o más (%)", "edb": "Madres con primaria o menos (%)",
       "subs": "Régimen subsidiado (%)", "rural": "Residencia rural (%)", "prim": "Primer hijo (%)", "mult": "Parto múltiple (%)",
       "etn": "Pertenencia étnica (%)"}


def f(x, d=2):
    if x is None:
        return "n. d."
    s = f"{abs(x):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if round(x, d) == 0:
        return s
    return ("−" if x < 0 else "") + s


def pv(x):
    return "< 0,001" if x < 0.0005 else f(x, 3)


def ic(v, d=2):
    return f"{f(v['att'], d)} ({f(v['ic_inf'], d)} a {f(v['ic_sup'], d)})"


def cargar():
    return json.loads(RES.read_text(encoding="utf-8"))


def tabla1(r):
    D = r["descriptivos"]
    filas = ["| Variable | Tratados 1998–2000 | Tratados 2023–2025 | Nunca tratados 1998–2000 | Nunca tratados 2023–2025 |",
             "|---|---|---|---|---|"]
    for k in ["local", "km", "km50", "noinst", "c4", "medico", "bp", "pre37", "pre38", "ces", "neo", "inf", "compl", "adol", "edb", "subs", "rural"]:
        d = D[k]
        filas.append(f"| {ETQ[k]} | {f(d['tratados_9800'], 1)} | {f(d['tratados_2325'], 1)} | {f(d['nunca_9800'], 1)} | {f(d['nunca_2325'], 1)} |")
    return "\n".join(filas)


def tabla2(r):
    P = r["principal"]
    filas = ["| Resultado | Media previa | ATT, e = 0…5 (IC 95 %) | p (Holm) | Promedio previo e = −5…−2 (EE) | p prueba previa |",
             "|---|---|---|---|---|---|"]
    for k in ["local", "km", "km50", "noinst", "c4", "c0", "medico", "bp", "pre37", "pre38", "ces", "neo", "neo_prec", "posneo", "inf"]:
        v = P[k]
        ph = pv(v["p_holm"]) if v.get("p_holm") is not None else ""
        filas.append(f"| {ETQ[k]} | {f(v['media_base'], 2)} | {ic(v)} | {ph} | {f(v['pre'], 2)} ({f(v['ee_pre'], 2)}) | {pv(v['p_wald_pre'])} |")
    return "\n".join(filas)


NOMCOP = [("A_base_g1", "A. Base g−1"), ("B_post_menos_previo", "B. Posterior menos previo"), ("C_base_promedio", "C. Base promedio g−8…g−2"),
          ("D_solo_tratados", "D. Solo tratados como control"), ("E_sin_ponderar", "E. Sin ponderar"), ("F_sin_grandes", "F. Sin ciudades grandes")]


def tabla_cop(r):
    C = r["coprincipales"]
    filas = ["| Resultado | " + " | ".join(n for _, n in NOMCOP) + " |", "|---|" + "---|" * len(NOMCOP)]
    for k in ["local", "km", "km50", "noinst", "c4", "bp", "pre37", "ces", "neo", "neo_prec", "posneo", "inf"]:
        filas.append(f"| {ETQ[k]} | " + " | ".join(ic(C[nom][k]) for nom, _ in NOMCOP) + " |")
    return "\n".join(filas)


def tabla_cop2(r):
    C = r["coprincipales"]
    nom2 = [("D2_solo_tratados_promedio", "D2. Solo tratados, base promedio"), ("E2_sin_ponderar_promedio", "E2. Sin ponderar, base promedio"),
            ("F2_sin_grandes_promedio", "F2. Sin ciudades grandes, base promedio")]
    filas = ["| Resultado | " + " | ".join(n for _, n in nom2) + " |", "|---|---|---|---|"]
    for k in ["local", "km", "km50", "noinst", "c4", "bp", "pre37", "ces", "neo", "neo_prec", "posneo", "inf"]:
        filas.append(f"| {ETQ[k]} | " + " | ".join(ic(C[nom][k]) for nom, _ in nom2) + " |")
    return "\n".join(filas)


def tabla_esc(r):
    E = r["escalado_wald"]
    filas = ["| Especificación | Primera etapa (puntos de cuota local) | Prematuro (%) | Neonatal precoz (por 1.000) | Neonatal (por 1.000) | Infantil (por 1.000) |",
             "|---|---|---|---|---|---|"]
    for nom, et in [("A_base_g1", "A. Base g−1"), ("B_post_menos_previo", "B. Posterior menos previo"), ("C_base_promedio", "C. Base promedio g−8…g−2")]:
        d = E[nom]
        cel = [f"{f(d[k]['escalado'], 2)} ({f(d[k]['ic_inf'], 2)} a {f(d[k]['ic_sup'], 2)})" for k in ["pre37", "neo_prec", "neo", "inf"]]
        filas.append(f"| {et} | {f(d['primera_etapa'], 2)} | " + " | ".join(cel) + " |")
    return "\n".join(filas)


def tabla3(r):
    E, P, I, C = r["estimadores"], r["principal"], r["ipw"], r["coprincipales"]["C_base_promedio"]
    filas = ["| Resultado | CS, base g−1 | CS, base promedio | Sun y Abraham | Gardner | TWFE estático (p WCR) | TWFE dinámico, e = 0…5 | CS-IPW por municipio |",
             "|---|---|---|---|---|---|---|---|"]
    for k in ["km", "noinst", "c4", "bp", "pre37", "ces", "neo", "inf"]:
        e = E[k]
        filas.append(f"| {ETQ[k]} | {ic(P[k])} | {ic(C[k])} | {ic(e['sun_abraham'])} | {ic(e['gardner'])} | "
                     f"{f(e['twfe']['att'], 2)} ({pv(e['wcr']['p_wcr'])}) | {ic(e['twfe']['din_0_5'])} | {ic(I[k])} |")
    return "\n".join(filas)


def tabla_sel(r):
    P = r["principal"]
    filas = ["| Variable | Media previa | ATT, e = 0…5 (IC 95 %) | Promedio e = −5…−2 | p prueba previa |", "|---|---|---|---|---|"]
    for k in ["lres", "compl", "adol", "e35", "edb", "subs", "rural", "prim", "etn", "inf_dom"]:
        v = P[k]
        filas.append(f"| {ETQ[k]} | {f(v['media_base'], 2)} | {ic(v)} | {f(v['pre'], 2)} | {pv(v['p_wald_pre'])} |")
    return "\n".join(filas)


NOMDEF = {"principal": "Principal (25 % → 10 %)", "abrupto": "Caída abrupta (cuota ≥ 25 % en g−3)", "volumen_24_12": "Volumen escalado (24 → 12 partos)",
          "alto50_bajo25": "50 % → 25 %", "bajo5": "25 % → 5 %", "persistencia3": "Persistencia de 3 años", "estable5": "5 años estables",
          "min50": "50 o más nacimientos al año", "sin_sitio_local": "Sin sitio cuenta como local", "balanceado_2020": "Cohortes hasta 2020 (balanceado en e = 0…5)",
          "sin_2020_2021": "Sin 2020 y 2021", "solo_aun_no": "Solo tratados (aún no tratados)", "sin_2025": "Sin 2025 (evento con datos hasta 2024)"}


def tabla_def(r):
    D = r["definiciones"]
    filas = ["| Definición | Tratados | Nunca | Cuota local | Distancia (km) | Bajo peso | Cesárea | Neonatal | Infantil | Prematuro, base promedio | Neonatal precoz, base promedio | Infantil, base promedio |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for nom, d in D.items():
        filas.append(f"| {NOMDEF[nom]} | {d['tratados']} | {d['nunca'] if nom != 'solo_aun_no' else 0} | " +
                     " | ".join(ic(d[k]) for k in ["local", "km", "bp", "ces", "neo", "inf", "pre37_C", "neo_prec_C", "inf_C"]) + " |")
    return "\n".join(filas)


def tabla_het(r):
    H = r["heterogeneidad"]
    filas = ["| Dimensión y grupo | Tratados | Controles nunca tratados | Más de 50 km [q] | No institucional [q] | Prematuro [q] | Infantil, base g−1 [q] | Neonatal precoz, base promedio [q] | Infantil, base promedio [q] |",
             "|---|---|---|---|---|---|---|---|---|"]
    for d, gg in H.items():
        for g, v in gg.items():
            filas.append(f"| {d}: {g} | {v['tratados']} | {v['controles']} | " +
                         " | ".join(f"{ic(v[k])} [{f(v[k]['q_bh'], 2)}]" for k in ["km50", "noinst", "pre37", "inf", "neo_prec_C", "inf_C"]) + " |")
    return "\n".join(filas)


def tabla_bacon(r):
    filas = ["| Resultado | Ponderación | TWFE balanceado | Tratado vs. nunca (peso; estimado) | Temprano vs. tardío (peso; estimado) | Tardío vs. temprano (peso; estimado) |",
             "|---|---|---|---|---|---|"]
    for k in ["km", "noinst", "ces", "neo", "inf"]:
        for pond, key in (("por nacimientos", "bacon"), ("sin ponderar", "bacon_sin_ponderar")):
            b = r["estimadores"][k][key]; t = b["tipos"]
            cel = [f"{f(t[x]['peso'], 3)}; {f(t[x]['estimado'], 2)}" for x in ["tratado vs nunca tratado", "temprano vs tardío (aún no tratado)", "tardío vs temprano (ya tratado)"]]
            filas.append(f"| {ETQ[k]} | {pond} | {f(b['twfe_balanceado'], 2)} | " + " | ".join(cel) + " |")
    return "\n".join(filas)


def tabla_rr(r):
    R = r["rambachan_roth"]
    filas = ["| Resultado | Δ previo máximo | Tendencia lineal: ATT (IC 95 %) | M̄ = 0 | M̄ = 0,25 | M̄ = 0,5 | M̄ de quiebre |", "|---|---|---|---|---|---|---|"]
    for k in ["km", "km50", "noinst", "c4", "bp", "pre37", "ces", "neo", "neo_prec", "inf"]:
        v = R[k]; g = v["grid"]
        filas.append(f"| {ETQ[k]} | {f(v['delta_pre_max'], 2)} | {ic(v['lineal'])} | {f(g['0']['ic_inf'], 2)} a {f(g['0']['ic_sup'], 2)} | "
                     f"{f(g['0.25']['ic_inf'], 2)} a {f(g['0.25']['ic_sup'], 2)} | "
                     f"{f(g['0.5']['ic_inf'], 2)} a {f(g['0.5']['ic_sup'], 2)} | {f(v['mbar_quiebre'], 2)} |")
    return "\n".join(filas)


def tabla_ant(r):
    A, C, B = r["anticipacion"], r["coprincipales"]["C_base_promedio"], r["coprincipales"]["B_post_menos_previo"]
    filas = ["| Resultado | Base g−1 | Anticipación de 3 años (base g−4) | Anticipación de 5 años (base g−6) | Posterior menos previo | Base promedio g−8…g−2 |", "|---|---|---|---|---|---|"]
    for k in ["km", "noinst", "c4", "bp", "pre37", "ces", "neo", "neo_prec", "inf"]:
        filas.append(f"| {ETQ[k]} | {ic(r['principal'][k])} | {ic(A[k]['3'])} | {ic(A[k]['5'])} | {ic(B[k])} | {ic(C[k])} |")
    return "\n".join(filas)


def tabla_bal(r):
    nombres = {"local": "Cuota local (%)", "lres": "Log nacimientos", "noinst": "No institucional (%)", "c4": "4+ controles (%)", "bp": "Bajo peso (%)",
               "ces": "Cesárea (%)", "neo": "Neonatal (por 1.000)", "inf": "Infantil (por 1.000)", "rural": "Rural (%)", "subs": "Subsidiado (%)",
               "adol": "Madres de 10 a 19 años (%)", "edb": "Primaria o menos (%)", "ldist": "Log distancia al centro", "alt": "Altitud (miles de m)",
               "pdet": "PDET", "tend_local": "Cambio de la cuota local 1998–2000 a 2001–2003"}
    filas = ["| Covariable (1998–2000) | Tratados | Nunca tratados | Diferencia estandarizada | Diferencia estandarizada con IPW |", "|---|---|---|---|---|"]
    for k, v in r["balance"].items():
        filas.append(f"| {nombres[k]} | {f(v['tratados'], 2)} | {f(v['nunca'], 2)} | {f(v['dif_est'], 2)} | {f(v['dif_est_ipw'], 2)} |")
    return "\n".join(filas)


TABLAS = {"tabla1": tabla1, "tabla2": tabla2, "tabla_cop": tabla_cop, "tabla_cop2": tabla_cop2, "tabla_esc": tabla_esc, "tabla3": tabla3,
          "tabla_sel": tabla_sel, "tabla_def": tabla_def, "tabla_het": tabla_het, "tabla_bacon": tabla_bacon, "tabla_rr": tabla_rr,
          "tabla_ant": tabla_ant, "tabla_bal": tabla_bal}

if __name__ == "__main__":
    r = cargar()
    for n, fn in TABLAS.items():
        print(f"<!-- {n} -->"); print(fn(r)); print()
