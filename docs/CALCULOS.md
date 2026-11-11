# Mapa de cálculos: de cada cifra a su función, su salida y su prueba

Cada cifra del resumen, la introducción, las conclusiones y las tablas y figuras principales del manuscrito, con la función que la calcula, la clave de `output/resultados.json` (o el archivo) donde queda y la prueba que la verifica. Siglas de las pruebas: **VC** = `pruebas/verificar_cifras.py` (cifra redondeada en su contexto del texto); **TC** = `pruebas/test_calculos.py` (recálculo independiente, sin el código del artículo); **TI** = `pruebas/test_insumos.py`; **TE** = `pruebas/test_estimadores.py`.

Funciones en `src/cierre_parto/`: `panel.py` (nivel B), `evento.py`, `datos.py`, `estimadores.py`, `estimacion.py`, `figuras.py`, `tablas_md.py`. La función de entrada del nivel A es `estimacion.py:estimar()` (script `scripts/06_estimar.py`).

## Contenido

1. Ecuaciones
2. Resumen y abstract
3. Introducción
4. Conclusiones
5. Tablas y figuras principales
6. Cifras de las secciones 3 y 4 que no están arriba

## 1. Ecuaciones

| Ecuación | Qué es | Función | Prueba |
|---|---|---|---|
| (1) cuota local $s_{mt}$ | partos institucionales de residentes en el propio municipio / nacimientos de residentes | `panel.py:agregar_anio()` (columnas `loc_inst`, `res`); `datos.py:resultados()` (`local`); `evento.py:definir_evento()` | TC (`test_muestra`) |
| (2) año de cierre $G_m$ | regla de 25 % estable, cruce del 10 % y persistencia | `evento.py:definir_evento()` | TC (`test_muestra`), VC |
| (3) ATT(g,t) | estimando | `estimadores.py:cs()` | TE (`test_cs_recupera_efecto_conocido`) |
| (4) tendencias paralelas con base $b$ | supuesto; base g−1 (A), promedio g−8…g−2 (C) o anticipación | `estimadores.py:cs(base_win=…, anticip=…)` | TE |
| (5) estimador de ATT(g,t) ponderado por nacimientos de 1998–2000 | diferencia de medias ponderadas de $Y_{mt}-\bar Y_{m,B_g}$ | `estimadores.py:cs()`; pesos en `datos.py:pesos_base()` | TE, TC (`test_puntos_A_B_C`) |
| (6) $\theta(e)$ y $\bar\theta$ | agregación por tiempo desde el cierre y promedio de e = 0…5 | `estimadores.py:cs()` | TE, TC |
| errores estándar | bootstrap multiplicador de Rademacher sobre las funciones de influencia, 999 réplicas, bandas uniformes | `estimadores.py:bootstrap_mult()`, `resumen()` | TE (`test_bootstrap_cobertura_aproximada`), TC (`test_error_estandar_C`) |
| (7) escalado tipo Wald | $\bar\theta_Y / (-\bar\theta_s/100)$ con las mismas réplicas | `estimacion.py:estimar()` (bloque «escalado tipo Wald») | VC |
| TWFE (texto de la sección 3.3) | efectos fijos de dos vías estático y dinámico | `estimadores.py:twfe()` (pyfixest) | TE (`test_bacon_reproduce_twfe`) |
| descomposición de Goodman-Bacon | comparaciones 2 × 2, ponderada como el TWFE | `estimadores.py:bacon()` | TE (`test_bacon_reproduce_twfe`), VC |
| Sun y Abraham; Gardner | interacciones cohorte × periodo relativo; did2s | `estimadores.py:sun_abraham()`, `gardner()` (pyfixest) | TE (`test_cs_igual_a_twfe_saturado_pyfixest` para el caso de una cohorte) |
| (8) Poisson ETWFE | razón de tasas por trienio de cohorte y periodo relativo | `estimadores.py:poisson_etwfe()` (pyfixest) | VC |
| (9) magnitudes relativas | cota del sesgo e intervalo por bootstrap; tendencia lineal | `estimadores.py:rambachan_roth()` | VC |
| IPW, permutación, bootstrap salvaje | ponderación por propensión en el soporte común; reasignación de años de cierre; WCR del TWFE | `estimadores.py:cs_ipw()`, `permutacion()`, `wild_cluster()` | VC |
| Holm y Benjamini-Hochberg | comparaciones múltiples | `estimacion.py:estimar()` | VC |

## 2. Resumen y abstract

| Cifra en el texto | Qué es | Script:función | Clave en `output/resultados.json` o archivo | Prueba |
|---|---|---|---|---|
| 18,5 millones de nacidos vivos | registros de nacimientos 1998–2025 | `scripts/04_intermedios.py:main()` | `data/intermedios/panel_info.json` → `registros_nacimientos_1998_2025` | TI (`test_registros_contra_dane`), TC, VC |
| 490 municipios | municipios con cierre funcional | `evento.py:definir_evento()` | `muestra.tratados` | TC, VC |
| 0,57 (0,26 a 0,87) | prematuridad, especificación C | `estimacion.py:estimar()` → `cs(base_win=(-8,-2))` | `coprincipales.C_base_promedio.pre37.{att,ic_inf,ic_sup}` | TC (`test_puntos_A_B_C`, `test_error_estandar_C`, `test_cifras_del_resumen`), VC |
| 0,36 (−0,12 a 0,83) | mortalidad infantil, especificación C | ídem | `coprincipales.C_base_promedio.inf` | TC, VC |
| «frente al año anterior al cierre, nada cambia» | intervalos de la especificación A que contienen el cero | `cs()` | `coprincipales.A_base_g1.{noinst,c4,bp,pre37,neo,neo_prec,inf}` | TC (`test_cifras_del_resumen`), VC |
| «se diluye con solo municipios que cierran después» | especificaciones D y D2 | `cs(control="tronly")` | `coprincipales.D_solo_tratados`, `D2_solo_tratados_promedio` | VC |

## 3. Introducción

| Cifra | Qué es | Función | Clave | Prueba |
|---|---|---|---|---|
| 4,8 % | cuota local de los tratados en 2023–2025 | `estimar()` (descriptivos) | `descriptivos.local.tratados_2325` | VC |
| 490 municipios | ver resumen | | `muestra.tratados` | TC, VC |
| 0,57 (0,26 a 0,87) sobre una base de 9,31 % | prematuridad C y media previa (g−3…g−1) | `cs()`, `media_base()` | `coprincipales.C_base_promedio.pre37`, `principal.pre37.media_base` | TC, VC |
| 0,30 y 0,36 por 1.000 | mortalidad neonatal precoz e infantil C | `cs()` | `coprincipales.C_base_promedio.{neo_prec,inf}.att` | TC, VC |
| 4,73 muertes por 1.000 nacimientos desplazados; 71 % | extremo superior del escalado de la mortalidad neonatal en A y su peso sobre la media previa | `estimar()` (escalado) | `escalado_wald.A_base_g1.neo.ic_sup`, `principal.neo.media_base` | VC |

## 4. Conclusiones

| Cifra | Qué es | Función | Clave | Prueba |
|---|---|---|---|---|
| 490 municipios | | `definir_evento()` | `muestra.tratados` | VC |
| −12 % a +5 % | intervalo de la mortalidad neonatal en A como porcentaje de la media previa | `estimar()` (magnitudes) | `magnitudes.neo.{pct_base_inf,pct_base_sup}` | VC |
| TWFE estático y base promedio sugieren daño; base g−1 no | | `twfe()`, `cs()` | `estimadores.neo.twfe`, `coprincipales` | VC |

## 5. Tablas y figuras principales

| Elemento | Contenido | Función | Archivo y claves | Prueba |
|---|---|---|---|---|
| Tabla 1 | características de tratados y nunca tratados, 1998–2000 y 2023–2025 | `estimar()` (descriptivos); `tablas_md.py:tabla1()` | `output/tablas/tabla1_descriptivos.csv`; `descriptivos.*` | VC (todas las filas) |
| Tabla 2 | seis especificaciones coprincipales | `estimar()` (coprincipales); `tablas_md.py:tabla_cop()` | `output/tablas/tabla2b_coprincipales.csv`; `coprincipales.*` | VC (todas las celdas); TC (A, B y C de seis resultados) |
| Tabla 3 | efecto por nacimiento desplazado | `estimar()` (escalado); `tablas_md.py:tabla_esc()` | `output/tablas/tablaF_escalado_wald.csv`; `escalado_wald.*` | VC |
| Figura 1 | cierres por año y cuota local por e | `figuras.py:figuras()` | `muestra.cohortes`, `cuota_local_tratados_por_e` | VC (cifras citadas) |
| Figura 2 | estudios de eventos de acceso, A | `figuras()` | `principal.{local,km,km50,noinst}.eventos` | VC (cifras citadas) |
| Figura 3 | estudios de eventos frente al promedio previo, C | `figuras()` (`fig8_eventos_base_promedio.png`) | `eventos_base_promedio.*` | VC (cifras citadas) |
| Figura 4 | comparación de estimadores | `figuras()` | `estimadores.*`, `coprincipales`, `ipw` | VC (tabla A3) |
| Figura 5 | heterogeneidad | `figuras()` (`fig7_heterogeneidad.png`) | `heterogeneidad.*` | VC (tabla A9) |
| Tablas A1 a A10 | anexo | `tablas_md.py` | `principal`, `coprincipales`, `estimadores`, `definiciones`, `rambachan_roth`, `anticipacion`, `heterogeneidad`, `balance` | VC (todas las filas) |

## 6. Cifras de las secciones 3 y 4 que no están arriba

Todas están en `pruebas/verificar_cifras.py`, que las recalcula desde `output/resultados.json` o desde el panel intermedio y busca la cifra redondeada en su frase. Las que dependen de columnas suprimidas en el panel publicado salen de `data/intermedios/agregados_nivel_b.json`, calculado en el nivel B con `estimacion.py:agregados_nivel_b()` y comparado en cada reconstrucción por `scripts/05_comparar_intermedios.py`:

| Cifra | Clave |
|---|---|
| 91,5 % y 94,3 % de muertes neonatales fuera del municipio | `muertes_fuera.{previo,posterior}` ← `agregados_nivel_b.json` |
| muertes infantiles en domicilio: −0,01 (−0,21 a 0,20) | `principal.inf_dom` ← `agregados_nivel_b.json` |
| pertenencia étnica (tabla A6) | `principal.etn` ← `agregados_nivel_b.json` |
| partición «20 % o más étnico» (tabla A9) | `heterogeneidad.etnia` con la marca `etnico20` de `atributos_municipio.parquet` |
| 49,5 % de completitud en menores de cinco años (2025) | `data/raw/externos/62/completitud_dane_menores5_2025.json` (insumo documentado; `docs/INSUMOS.md`) |
