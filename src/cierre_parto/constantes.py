"""Constantes del diseño (años, ventana del estudio de eventos, réplicas, semilla, listas de resultados)."""
ANIOS = list(range(1998, 2026))
T = len(ANIOS)
SEMILLA = 20261024
E_MIN, E_MAX, E_POST = -8, 6, 5          # ventana del estudio de eventos y horizonte del promedio (e = 0…5)
B_MULT, B_UNID, N_PERM = 999, 199, 500   # réplicas del bootstrap multiplicador, del bootstrap por municipios y permutaciones
VENTANA = (-8, -2)                       # base promedio del periodo previo, sin el año g-1
P_MIN, P_MAX = 0.01, 0.99                # soporte común de la propensión

K_PRIM = ["noinst", "c4", "bp", "pre37", "ces", "neo", "neo_prec", "inf"]          # familia primaria (Holm)
K_MEC = ["local", "km", "km50", "dom", "c0", "medico", "pre38", "posneo", "inf_dom"]  # primera etapa y mecanismos
K_SEL = ["lres", "compl", "adol", "e35", "edb", "subs", "rural", "prim", "mult", "etn"]  # selección y composición
K_EST = ["km", "noinst", "c4", "bp", "pre37", "ces", "neo", "inf"]                  # comparación de estimadores
K_COP = ["local", "km", "km50", "noinst", "c4", "bp", "pre37", "ces", "neo", "neo_prec", "posneo", "inf"]  # coprincipales
K_HET = ["km", "km50", "noinst", "c4", "bp", "pre37", "ces", "neo", "neo_prec", "inf"]
# resultados cuyos numeradores municipales se suprimen (celdas de 1 a 4) en data/intermedios/; sus cifras salen de
# data/intermedios/agregados_nivel_b.json, calculadas en el nivel B con los conteos completos (docs/INSUMOS.md, sección 4)
K_SUPRIMIDOS = ["etn", "inf_dom"]
COLS_SUPRIMIDAS = ["etn", "d_inf_dom", "d_neo_fuera", "d_inf_fuera"]
