#!/usr/bin/env python3
"""Verifica cada cifra del manuscrito A2 contra las salidas del repositorio (nivel A).

Recalcula desde:
  output/resultados.json                         estimaciones (scripts/06_estimar.py)
  data/intermedios/panel_municipio_anio.parquet  panel municipio-año (muestra, cohortes, nacimientos)
  data/intermedios/panel_info.json               totales de control del nivel B (registros de nacimientos)
y comprueba que cada número, con su redondeo exacto y en su contexto, aparece en manuscrito/manuscrito.md; que las
tablas del texto coinciden fila por fila con las que genera src/cierre_parto/tablas_md.py; que se cumplen las
afirmaciones cualitativas del texto (signos, intervalos que contienen o no el cero, q de Benjamini-Hochberg); que las
figuras existen, y las reglas de estilo y extensión. Termina en «Todo coincide.» o lista las fallas.

Uso: python pruebas/verificar_cifras.py
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from cierre_parto import tablas_md as T  # noqa: E402
from cierre_parto.constantes import ANIOS  # noqa: E402
from cierre_parto.datos import cargar  # noqa: E402
from cierre_parto.evento import definir_evento  # noqa: E402

MAN = RAIZ / "manuscrito"
_RUTA_TXT = RAIZ / "manuscrito" / "manuscrito.md"
if not _RUTA_TXT.exists():
    print("El texto del artículo no está en este repositorio; se agrega cuando se publique. Las pruebas de cálculo (pytest) sí corren.")
    sys.exit(0)
TXT = (MAN / "manuscrito.md").read_text(encoding="utf-8")
r = T.cargar()
f, pv = T.f, T.pv
fallas = []
n_ok = 0


def esta(que, s):
    global n_ok
    if s in TXT:
        n_ok += 1
    else:
        fallas.append(f"{que}: no se encontró «{s}»")


def ic(v, d=2):
    return f"{f(v['ic_inf'], d)} a {f(v['ic_sup'], d)}"


def cumple(que, cond):
    global n_ok
    if cond:
        n_ok += 1
    else:
        fallas.append(f"afirmación del texto no se cumple: {que}")


# ── 1. muestra, recalculada desde el panel intermedio con la regla del evento ─────────────────
A, W = cargar()
G, S = definir_evento(W)
trat, nunca = int(np.isfinite(G).sum()), int(np.isinf(G).sum())
eleg = int((W["res"].mean(axis=1) >= 30).sum())
M = r["muestra"]
cumple("muestra del panel = json", (trat, nunca, eleg) == (M["tratados"], M["nunca"], M["elegibles"]))
esta("tratados", f"; {f(trat, 0)} cumplen la definición de cierre")
esta("tratados intro", f"Entre 2001 y 2024 hay {f(trat, 0)} municipios con ese evento")
esta("tratados resumen", f"cierre funcional del parto local en {f(trat, 0)} municipios")
esta("nunca", f"{f(nunca, 0)} conservan el parto local")
esta("elegibles", f"{f(eleg, 0)} tienen 30 o más nacimientos al año")
esta("divipola", f"De las {f(len(G), 0)} entidades de la DIVIPOLA")
esta("excluidos", f"y {f(eleg - trat - nunca, 0)} quedan fuera")
gf = G[np.isfinite(G)]
c3 = [int(((gf >= a) & (gf <= b)).sum()) for a, b in [(2001, 2010), (2011, 2020), (2021, 2024)]]
esta("cohortes", f"{c3[0]} entre 2001 y 2010, {c3[1]} entre 2011 y 2020 y {c3[2]} entre 2021 y 2024")
esta("% cohortes 2021-2024", f"El {f(100 * c3[2] / trat, 0)} % de los cierres ocurrió entre 2021 y 2024")
i3 = [ANIOS.index(a) for a in (2023, 2024, 2025)]
nt = W["res"][np.isfinite(G)][:, i3].sum() / 3; npais = W["res"][:, i3].sum() / 3
esta("nac tratados", f"nacían al año {f(nt, 0)} hijos de madres residentes")
esta("nac tratados discusión", f"nacían cada año {f(nt, 0)} niños")
esta("% país", f"el {f(100 * nt / npais, 1)} % del país")
reg = json.loads((RAIZ / "data" / "intermedios" / "panel_info.json").read_text())["registros_nacimientos_1998_2025"]
esta("registros", f"unos {f(reg / 1e6, 1)} millones de registros")
esta("registros resumen", f"Con {f(reg / 1e6, 1)} millones de nacidos vivos")
sal = A["salas_reps2022"].to_numpy(); h22 = np.isfinite(G) & (G <= 2022)
esta("REPS", f"De los {f(int(h22.sum()), 0)} que cerraron hasta 2022, {f(int((h22 & (sal > 0)).sum()), 0)} tenían sala")
dc = A["d_centro_0810"].to_numpy()
esta("distancia mediana", f"es {f(float(np.median(dc[np.isfinite(G)])), 1)} km en los tratados y {f(float(np.median(dc[np.isinf(G)])), 1)} km en los nunca tratados")
esta("distancia mediana discusión", f"(mediana de {f(float(np.median(dc[np.isfinite(G)])), 1)} km)")
comp = json.loads((RAIZ / "data" / "raw" / "externos" / "62" / "completitud_dane_menores5_2025.json").read_text())
esta("completitud menores de 5", f"implican una completitud de {f(100 * comp['por_edad']['menores de 5'], 1)} % en esas edades en {comp['anio']}")

# ── 2. cifras descriptivas y de muestra desde resultados.json ────────────────────────────────
D1 = r["descriptivos"]; cu = r["cuota_local_tratados_por_e"]; P = r["principal"]
esta("cuota 2023-2025", f"En 2023–2025 esa proporción era {f(D1['local']['tratados_2325'], 1)} %")
esta("cuota por e", f"el {f(cu['-14'], 1)} % de los nacimientos de residentes de los tratados ocurría en una institución local; el año anterior al cierre, el {f(cu['-1'], 1)} %; el año del cierre, el {f(cu['0'], 1)} %")
caidas = [cu[str(e)] - cu[str(e + 1)] for e in range(-14, -1)]
cumple("la cuota cae más en g−1 que en cualquier año previo", caidas[-1] == max(caidas))
cumple("la distancia sube en g−1", P["km"]["eventos"]["-2"]["theta"] < 0)
esta("nunca 1998-2025", f"pasó de {f(r['cuota_local_nunca_por_anio']['1998'], 1)} % en 1998 a {f(r['cuota_local_nunca_por_anio']['2025'], 1)} % en 2025")
dm = r["descriptivos_municipio"]
esta("tamaño", f"(en promedio {f(dm['nac_9800_tratados'], 0)} nacimientos al año en 1998–2000, frente a {f(dm['nac_9800_nunca'], 0)})")
esta("37 semanas o menos", f"pasa de {f(D1['pre38']['tratados_9800'], 1)} % a {f(D1['pre38']['tratados_2325'], 1)} % de los nacimientos")
mf = r["muertes_fuera"]
esta("muertes fuera", f"el {f(mf['previo'], 1)} % de las muertes neonatales de residentes ocurría fuera del municipio en los tres años previos al cierre y el {f(mf['posterior'], 1)} % en los seis posteriores")
# (anexo A.4, registro de árbitro, retirado del manuscrito de envío) esta("muertes fuera anexo", f"({f(mf['previo'], 1)} % antes y {f(mf['posterior'], 1)} % después)")
pc = r["peso_controles"]
esta("peso nunca", f"En A, el {f(100 * pc['nunca_tratados'], 1)} % del peso del control")
esta("peso nunca autoexamen", f"El {f(100 * pc['nunca_tratados'], 1)} % del peso del control en A son nunca tratados")
esta("peso Bogotá y grandes", f"Bogotá sola pesa {f(100 * dict(pc['principales'])['BOGOTÁ, D.C.'], 1)} % y las doce ciudades grandes, {f(100 * pc['grandes'], 1)} %")
cumple("doce ciudades grandes", r["ciudades_grandes"]["municipios"] == 12)
esta("bh", f"Benjamini-Hochberg sobre las {f(r['bh_pruebas'], 0)} pruebas")

# ── 3. especificaciones coprincipales ─────────────────────────────────────────────────────────
C = r["coprincipales"]
A_, B_, C_ = C["A_base_g1"], C["B_post_menos_previo"], C["C_base_promedio"]
esta("resumen C prematuro", f"la prematuridad sube {f(C_['pre37']['att'], 2)} puntos (IC 95 %: {ic(C_['pre37'])})")
esta("resumen C infantil", f"la mortalidad infantil {f(C_['inf']['att'], 2)} por 1.000 (IC 95 %: {ic(C_['inf'])})")
en = lambda x: f"{x:.2f}".replace("-", "−")
esta("abstract", f"preterm birth rises {en(C_['pre37']['att'])} points (95 % CI: {en(C_['pre37']['ic_inf'])} to {en(C_['pre37']['ic_sup'])}) and infant mortality {en(C_['inf']['att'])} per 1,000 (95 % CI: {en(C_['inf']['ic_inf'])} to {en(C_['inf']['ic_sup'])})")
esta("intro C", f"la prematuridad sube {f(C_['pre37']['att'], 2)} puntos porcentuales (IC 95 %: {ic(C_['pre37'])}) sobre una base de {f(P['pre37']['media_base'], 2)} %")
esta("intro C mortalidad", f"de {f(C_['neo_prec']['att'], 2)} y {f(C_['inf']['att'], 2)} por 1.000")
esta("A local", f"Con la base A cambia {f(A_['local']['att'], 2)} puntos (IC 95 %: {ic(A_['local'])}) sobre una media previa de {f(P['local']['media_base'], 1)} %; con la base promedio, {f(C_['local']['att'], 2)} puntos")
esta("A km", f"aumenta {f(A_['km']['att'], 2)} km (IC 95 %: {ic(A_['km'])}) con la especificación A, sobre una base de {f(P['km']['media_base'], 1)} km, y {f(C_['km']['att'], 2)} km con la base promedio")
D_, E_, F_ = C["D_solo_tratados"], C["E_sin_ponderar"], C["F_sin_grandes"]
esta("km D E F", f"con solo municipios que cierran después es {f(D_['km']['att'], 2)} km (IC 95 %: {ic(D_['km'])}), sin ponderar {f(E_['km']['att'], 2)} y sin ciudades grandes {f(F_['km']['att'], 2)} (IC 95 %: {ic(F_['km'])})")
RR = r["rambachan_roth"]
esta("km lineal", f"Con la tendencia lineal previa extrapolada es {f(RR['km']['lineal']['att'], 2)} km (IC 95 %: {ic(RR['km']['lineal'])})")
esta("A noinst", f"({f(A_['noinst']['att'], 2)} puntos; IC 95 %: {ic(A_['noinst'])})")
cumple("partos a más de 50 km no aumentan en A", A_["km50"]["ic_inf"] < 0)
esta("A salud", f"la mortalidad neonatal {f(A_['neo']['att'], 2)} por 1.000 (IC 95 %: {ic(A_['neo'])}), la infantil {f(A_['inf']['att'], 2)} (IC 95 %: {ic(A_['inf'])}) y la prematuridad {f(A_['pre37']['att'], 2)} puntos (IC 95 %: {ic(A_['pre37'])})")
for k in ["noinst", "c4", "bp", "pre37", "neo", "neo_prec", "inf", "posneo"]:
    cumple(f"A: {k} contiene el cero", A_[k]["ic_inf"] <= 0 <= A_[k]["ic_sup"])
esta("pre A", f"es {f(P['neo']['pre'], 2)} por 1.000 (EE {f(P['neo']['ee_pre'], 2)}) para la neonatal y {f(P['inf']['pre'], 2)} (EE {f(P['inf']['ee_pre'], 2)}) para la infantil")
esta("wald A", f"(p = {f(P['neo']['p_wald_pre'], 3)} y {f(P['inf']['p_wald_pre'], 3)})")
esta("C salud", f"la prematuridad sube {f(C_['pre37']['att'], 2)} puntos (IC 95 %: {ic(C_['pre37'])}; p de Holm {pv(C_['pre37']['p_holm'])}) sobre una base de {f(P['pre37']['media_base'], 2)} %, la mortalidad neonatal precoz {f(C_['neo_prec']['att'], 2)} por 1.000 (IC 95 %: {ic(C_['neo_prec'])}) y la infantil {f(C_['inf']['att'], 2)} (IC 95 %: {ic(C_['inf'])})")
esta("B salud", f"{f(B_['pre37']['att'], 2)} puntos de prematuridad (IC 95 %: {ic(B_['pre37'])}), {f(B_['neo_prec']['att'], 2)} por 1.000 de mortalidad neonatal precoz (IC 95 %: {ic(B_['neo_prec'])}; p de Holm {pv(B_['neo_prec']['p_holm'])}) y {f(B_['inf']['att'], 2)} de mortalidad infantil (IC 95 %: {ic(B_['inf'])})")
D2, E2, F2 = C["D2_solo_tratados_promedio"], C["E2_sin_ponderar_promedio"], C["F2_sin_grandes_promedio"]
esta("D salud", f"la mortalidad infantil cambia {f(D_['inf']['att'], 2)} por 1.000 y la prematuridad {f(D_['pre37']['att'], 2)}; con esa misma restricción y base promedio, {f(D2['inf']['att'], 2)} (IC 95 %: {ic(D2['inf'])}) y {f(D2['pre37']['att'], 2)} (IC 95 %: {ic(D2['pre37'])})")
for k in ["pre37", "neo", "neo_prec", "inf"]:
    cumple(f"D y D2 no encuentran efecto en {k}", D_[k]["ic_inf"] <= 0 <= D_[k]["ic_sup"] and D2[k]["ic_inf"] <= 0 <= D2[k]["ic_sup"])
cumple("D: la distancia no aumenta", D_["km"]["ic_inf"] <= 0)
esta("E2 F2", f"Sin ponderar y con base promedio, la mortalidad infantil sube {f(E2['inf']['att'], 2)} (IC 95 %: {ic(E2['inf'])}); sin ciudades grandes y con base promedio, {f(F2['inf']['att'], 2)} (IC 95 %: {ic(F2['inf'])}), y la prematuridad {f(F2['pre37']['att'], 2)} (IC 95 %: {ic(F2['pre37'])})")
po = r["poisson"]
esta("Poisson", f"razones de tasas de {f(po['neo']['irr'], 3)} (IC 95 %: {f(po['neo']['ic_inf'], 3)} a {f(po['neo']['ic_sup'], 3)}) para la mortalidad neonatal y {f(po['inf']['irr'], 3)} (IC 95 %: {f(po['inf']['ic_inf'], 3)} a {f(po['inf']['ic_sup'], 3)}) para la infantil")
for nom in ["A_base_g1", "B_post_menos_previo", "C_base_promedio", "E_sin_ponderar", "F_sin_grandes"]:
    cumple(f"cesárea sube en {nom}", C[nom]["ces"]["ic_inf"] > 0)
cumple("cesárea no sube en D", D_["ces"]["ic_inf"] <= 0)
esta("ces lineal", f"es {f(RR['ces']['lineal']['att'], 2)}; IC 95 %: {ic(RR['ces']['lineal'])})")

# ── 4. escalado y magnitudes ──────────────────────────────────────────────────────────────────
ES = r["escalado_wald"]
ea = ES["A_base_g1"]["neo"]
pct = 100 * ea["ic_sup"] / P["neo"]["media_base"]
esta("escalado A", f"el cierre desplaza {f(-ES['A_base_g1']['primera_etapa'], 2)} puntos de cuota, y el intervalo de la mortalidad neonatal escalada va de {f(ea['ic_inf'], 2)} a {f(ea['ic_sup'], 2)} muertes por 1.000 nacimientos desplazados: el extremo superior es el {f(pct, 0)} % de la media previa")
esta("escalado intro", f"llega hasta {f(ea['ic_sup'], 2)} muertes por 1.000 nacimientos desplazados, el {f(pct, 0)} % de la media previa")
esta("escalado autoexamen", f"llega a {f(pct, 0)} %")
for k, txt in [("pre37", "la prematuridad sube {} puntos por cada nacimiento desplazado (IC 95 %: {})"),
               ("neo_prec", "la mortalidad neonatal precoz {} por 1.000 (IC 95 %: {}). Sin escalar")]:
    e = ES["C_base_promedio"][k]
    esta(f"escalado C {k}", txt.format(f(e["escalado"], 2), f"{f(e['ic_inf'], 2)} a {f(e['ic_sup'], 2)}"))
mg = r["magnitudes"]
lo_r, hi_r = f(mg["neo"]["pct_base_inf"], 0), f(mg["neo"]["pct_base_sup"], 0)
esta("intervalo % (resultados)", f"va de {lo_r} % a +{hi_r} % de la media previa")
esta("intervalo % (conclusiones)", f"va de {lo_r} % a +{hi_r} % de su nivel previo con ese estimando")
esta("cota % autoexamen", f"descarta aumentos mayores al {f(mg['neo']['pct_base_sup'], 1)} % de la media previa")
m = mg["inf|C_base_promedio"]
esta("muertes infantiles C", f"equivale a {f(m['muertes_anuales'], 0)} muertes adicionales al año (IC 95 %: {f(m['ic_inf'], 0)} a {f(m['ic_sup'], 0)})")
m = mg["neo"]
esta("muertes neonatales A", f"a {f(m['muertes_anuales'], 0)} muertes neonatales (IC 95 %: {f(m['ic_inf'], 0)} a {f(m['ic_sup'], 0)})")

# ── 5. estimadores, robustez, heterogeneidad ─────────────────────────────────────────────────
E = r["estimadores"]
esta("TWFE", f"El TWFE estático da {f(E['neo']['twfe']['att'], 2)} por 1.000 en mortalidad neonatal (p del bootstrap salvaje {pv(E['neo']['wcr']['p_wcr'])}), {f(E['inf']['twfe']['att'], 2)} en la infantil y {f(E['km']['twfe']['att'], 2)} km en distancia; Gardner, {f(E['neo']['gardner']['att'], 2)} y {f(E['inf']['gardner']['att'], 2)}")
for k in ["km", "noinst", "c4", "bp", "ces", "neo", "inf"]:
    b = E[k]["bacon"]
    cumple(f"Bacon ponderado reproduce su TWFE balanceado ({k})", abs(b["suma_ponderada"] - b["twfe_balanceado"]) < 1e-8)
    cumple(f"Bacon ponderado ≈ TWFE informado ({k})", abs(b["twfe_balanceado"] - E[k]["twfe"]["att"]) < 0.05)
bt = E["neo"]["bacon"]["tipos"]["tratado vs nunca tratado"]
esta("Bacon", f"asigna {f(bt['peso'], 3)} del peso a comparaciones de tratados con nunca tratados, con un estimado de {f(bt['estimado'], 2)}")
dn = E["neo"]["twfe"]["din_0_5"]
esta("TWFE dinámico", f"el TWFE dinámico da {f(dn['att'], 2)} (IC 95 %: {ic(dn)}) en mortalidad neonatal y {f(E['km']['twfe']['din_0_5']['att'], 2)} km en distancia")
DF = r["definiciones"]
cumple("trece variantes", len(DF) == 13)
for nom, d in DF.items():
    for k in ["neo", "inf"]:
        cumple(f"definición {nom}: {k} base g−1 contiene el cero", d[k]["ic_inf"] <= 0 <= d[k]["ic_sup"])
    cumple(f"definición {nom}: prematuridad con base promedio > 0 salvo solo tratados", (d["pre37_C"]["ic_inf"] > 0) == (nom != "solo_aun_no"))
s25 = DF["sin_2025"]
esta("sin 2025", f"{f(s25['tratados'], 0)} tratados), la prematuridad con base promedio sube {f(s25['pre37_C']['att'], 2)} (IC 95 %: {ic(s25['pre37_C'])}) y la mortalidad infantil {f(s25['inf_C']['att'], 2)} (IC 95 %: {ic(s25['inf_C'])})")
bal = DF["balanceado_2020"]
esta("balanceado", f"las cifras son {f(bal['pre37_C']['att'], 2)} y {f(bal['inf_C']['att'], 2)}")
cumple("sin caída diferencial de nacimientos", P["lres"]["ic_inf"] <= 0 <= P["lres"]["ic_sup"])
esta("completitud", f"era de {f(P['compl']['media_base'], 1)} % en los tratados antes del cierre y sube {f(P['compl']['att'], 2)} puntos (IC 95 %: {ic(P['compl'])})")
# (anexo A.4, registro de árbitro, retirado del manuscrito de envío) esta("completitud anexo", f"la completitud pasa de 37 % a {f(P['compl']['media_base'], 1)} % y su efecto de 1,32 a {f(P['compl']['att'], 2)} puntos")
esta("muertes en domicilio", f"({f(P['inf_dom']['att'], 2)} por 1.000; IC 95 %: {ic(P['inf_dom'])})")
for k in ["adol", "prim", "rural"]:
    cumple(f"composición {k} no cambia", P[k]["ic_inf"] <= 0 <= P[k]["ic_sup"])
cumple("la educación venía cambiando antes", P["edb"]["p_wald_pre"] < 0.05)
g = RR["neo"]["grid"]
esta("RR neo", f"el extremo superior del intervalo de la mortalidad neonatal pasa de {f(g['0']['ic_sup'], 2)} por 1.000 con $\\bar M=0$ a {f(g['0.25']['ic_sup'], 2)} con $\\bar M=0{{,}}25$ y {f(g['0.5']['ic_sup'], 2)} con $\\bar M=0{{,}}5$")
g = RR["inf"]["grid"]
esta("RR inf", f"el de la infantil, de {f(g['0']['ic_sup'], 2)} a {f(g['0.25']['ic_sup'], 2)} y {f(g['0.5']['ic_sup'], 2)}")
esta("RR km", f"deja de distinguirse de cero en $\\bar M={f(RR['km']['mbar_quiebre'], 2)}$")
An = r["anticipacion"]
esta("anticipación", f"la mortalidad neonatal precoz sube {f(An['neo_prec']['5']['att'], 2)} por 1.000 (IC 95 %: {ic(An['neo_prec']['5'])}) y la distancia {f(An['km']['5']['att'], 2)} km")
H = r["heterogeneidad"]
L = H["distancia"]["25 km o más"]; p1 = H["periodo"]["2001–2014"]["inf_C"]; u = H["ruralidad"]["mayoría urbana"]["inf_C"]
esta("het lejos km50", f"({f(L['km50']['att'], 2)} puntos; q = {f(L['km50']['q_bh'], 2)})")
esta("het periodo", f"({f(p1['att'], 2)} por 1.000; IC 95 %: {ic(p1)}; q = {f(p1['q_bh'], 2)})")
esta("het urbana", f"({f(u['att'], 2)}; q = {f(u['q_bh'], 2)})")
for v in (L["km50"], p1, u):
    cumple("q < 0,05 en las particiones citadas", v["q_bh"] < 0.05)
esta("het 2015-2024", f"En los cierres de 2015 a 2024 la mortalidad infantil con base promedio cambia {f(H['periodo']['2015–2024']['inf_C']['att'], 2)}")
esta("het lejos inf", f"la mortalidad infantil con base promedio sube {f(L['inf_C']['att'], 2)} (q = {f(L['inf_C']['q_bh'], 2)})")
esta("BH n", f"Tras Benjamini-Hochberg sobre {f(r['bh_pruebas'], 0)} pruebas")

# ── 6. tablas: cada fila generada debe estar en el texto ─────────────────────────────────────
for nombre, fn in T.TABLAS.items():
    for fila in fn(r).splitlines():
        if fila not in TXT:
            fallas.append(f"{nombre}: fila no encontrada «{fila[:70]}…»")
        else:
            n_ok += 1

# ── 7. figuras, estilo, extensión, referencias y formato ─────────────────────────────────────
for m_ in re.findall(r"\]\((\.\./output/figuras/[^)]+)\)", TXT):
    if not (MAN / m_).exists():
        fallas.append(f"figura inexistente: {m_}")
prohibidas = ["—", "Cabe ", "Es importante", "Asimismo", "No obstante", "Por otro lado", "Adicionalmente", "En conclusión", "crucial",
              "fundamental", "holístic", "potenciar", "abordar", "desafío", "panorama", "ecosistema", "sinergia", "conviene", "significativ"]
for w in prohibidas:
    if w.lower() in TXT.lower():
        fallas.append(f"estilo: aparece «{w}»")
if "cuyo costo medible es la distancia" in TXT.split("## Anexo")[0]:
    fallas.append("persiste la frase retirada sobre la distancia")
cuerpo = TXT.split("## Anexo (material suplementario)")[0].split("## Resumen")[1]
cuerpo = re.sub(r"\$\$.*?\$\$", "", cuerpo, flags=re.S)
palabras = len(re.findall(r"\S+", re.sub(r"!\[.*?\]\(.*?\)", "", cuerpo)))
if palabras > 8000:
    fallas.append(f"extensión: {palabras} palabras en el cuerpo principal (límite 8.000)")
res_es = len(re.findall(r"\S+", TXT.split("## Resumen")[1].split("**Palabras clave")[0]))
res_en = len(re.findall(r"\S+", TXT.split("## Abstract")[1].split("**Keywords")[0]))
if res_es > 150 or res_en > 150:
    fallas.append(f"resumen {res_es} / abstract {res_en} palabras (límite 150)")
texto, refs = TXT.split("## Referencias")[0], TXT.split("## Referencias")[1].split("## Anexo")[0]
for autor in ["Callaway", "Sun", "Gardner", "Goodman-Bacon", "Rambachan", "Wooldridge", "Kozhimannil", "Fischer", "Hung", "Grzybowski", "Leal", "Felipe"]:
    if autor in texto and autor not in refs:
        fallas.append(f"cita sin referencia: {autor}")
for cita, ref in [("Garavito Jiménez, 2026a", "Garavito Jiménez, D. A. (2026a)"), ("Garavito Jiménez, 2026b", "Garavito Jiménez, D. A. (2026b)")]:
    cumple(f"autocita {cita} con referencia", (cita not in texto) or (ref in refs))
for marca in ["[HOJA DE PRESENTACIÓN", "[Autocita: anonimizar]", "se depositará en Zenodo"]:
    esta("formato doble ciego", marca)

print(f"Comprobaciones superadas: {n_ok}; palabras del cuerpo principal: {palabras}; resumen: {res_es}; abstract: {res_en}.")
if fallas:
    print("FALLAS:")
    for x in fallas:
        print(" -", x)
    sys.exit(1)
print("Todo coincide.")
