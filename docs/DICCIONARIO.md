# Diccionario de los paneles intermedios y de las salidas

Variables de `data/intermedios/` y de `output/`. Las variables de las bases comunes de Estadísticas Vitales están en `docs/DICCIONARIO_EEVV.md`. Códigos del DANE usados (catálogo ANDA): sitio del parto 1 institución, 2 domicilio, 3 otro, 9 sin información; peso 1–4 = menos de 2.500 g (entre 1–8); `t_ges` 1–3 = menos de 38 semanas (entre 1–5); `t_ges_cie` 1–3 = menos de 37 semanas (entre 1–5; sin dato en 1998–2007, 2012, 2013 y 2020); consultas prenatales 0–25; tipo de parto 2 = cesárea (entre 1–3); quién atendió 1 = médico (entre 1–6); edad de la madre en grupos quinquenales 1 (10–14) a 9 (50–54); nivel educativo «primaria o menos» = 1, 2, 3, 8 en 1998–2007 y 1, 2, 13 en 2008–2025; régimen 2 = subsidiado; área 2–3 = centro poblado y rural disperso; pertenencia étnica 1–5 = grupo étnico (desde 2008; sin dato en 2012 y 2013); sitio de defunción 3 = domicilio.

## `panel_municipio_anio.parquet` (31.261 filas: municipio × año, 1998–2025)

Todas las cuentas se refieren a nacimientos de madres residentes en `mun` (nazcan donde nazcan), salvo `ocu_*`.

| Variable | Contenido |
|---|---|
| `mun`, `anio` | código DIVIPOLA armonizado (5 dígitos) y año |
| `res` | nacidos vivos de madres residentes |
| `loc_inst`, `loc_inst9`, `loc` | ocurridos en el propio municipio: en institución; en institución o sin sitio; en cualquier sitio |
| `sitk`, `noinst`, `dom`, `sit9` | con sitio conocido; en domicilio u otro; en domicilio; sin sitio |
| `kmk`, `km`, `km50` | con municipio de ocurrencia válido; suma de distancias en línea recta (km) al municipio de ocurrencia; ocurridos a más de 50 km |
| `pk`, `bp` | con peso conocido; con menos de 2.500 g |
| `gk`, `pre` | con gestación CIE conocida; menos de 37 semanas |
| `gk38`, `pre38` | con gestación conocida (serie completa); menos de 38 semanas |
| `atk`, `medico` | con persona que atendió conocida; atendidos por médico |
| `mk`, `mult` | con multiplicidad conocida; partos múltiples |
| `ck`, `c4`, `c0` | con número de controles conocido; cuatro o más; ninguno |
| `tk`, `ces` | con tipo de parto conocido; cesárea |
| `ek`, `adol`, `e35` | con edad de la madre conocida; madres de 10 a 19 años; de 35 o más |
| `edk`, `edb` | con educación conocida; primaria o menos |
| `rk`, `subs` | con régimen conocido; subsidiado |
| `ak`, `rural` | con área conocida; residencia rural (centro poblado y rural disperso) |
| `etk`, `etn` | con pertenencia étnica conocida; de algún grupo étnico (**celdas de 1 a 4 suprimidas**) |
| `hk`, `prim` | con número de hijos conocido; primer hijo |
| `ocu_inst`, `ocu_todos` | partos institucionales y todos los partos ocurridos en `mun`, de cualquier residencia |
| `d_neo_prec`, `d_neo_tard`, `d_posneo`, `d_inf` | defunciones de residentes de 0 a 6 días, 7 a 27 días, 28 días a 11 meses y menores de un año |
| `d_neo_ext`, `d_inf_ext` | defunciones neonatales e infantiles contadas en la base extendida (control; iguales a las anteriores) |
| `d_neo_fuera`, `d_inf_fuera` | defunciones neonatales e infantiles de residentes ocurridas en otro municipio (**celdas de 1 a 4 suprimidas**) |
| `d_inf_dom` | defunciones infantiles de residentes en el domicilio (**celdas de 1 a 4 suprimidas**) |
| `pob0`, `pob_tot` | población proyectada de 0 años y total (DANE, área «Total») |

## `atributos_municipio.parquet` (1.122 filas)

| Variable | Contenido |
|---|---|
| `mun`, `dpc`, `ndp`, `nmun`, `tipo` | código, departamento, nombres y tipo de entidad (DIVIPOLA) |
| `lat`, `lon` | punto de referencia del DANE |
| `alt`, `km_estacion` | altitud de la estación del IDEAM más cercana y distancia a ella |
| `pdet`, `zomac` | designaciones (config/) |
| `salas_reps2022` | salas de partos habilitadas en el REPS (5-nov-2022) |
| `d_centro_9800`, `d_centro_0810` | distancia al otro municipio más cercano con 365 o más partos institucionales al año en 1998–2000 y 2008–2010 |
| `etnico20` | 20 % o más de los nacimientos de 2008–2011 son de grupos étnicos (calculada en el nivel B con los conteos completos) |

## `agregados_nivel_b.json` y `panel_info.json`

- `agregados_nivel_b.json`: `principal.etn` y `principal.inf_dom` (efecto, error estándar, intervalos, estudio de eventos y media previa, con el mismo estimador que el resto), `muertes_fuera` (porcentajes previo, posterior y por año desde el cierre) y `etn_mediana_tratados`.
- `panel_info.json`: registros de nacimientos 1998–2025, filas, municipios, nacimientos y defunciones infantiles por año, celdas suprimidas por columna y celdas de 1 a 4 que se publican.

## `output/resultados.json`

Secciones: `parametros`, `muestra`, `cuota_local_*`, `descriptivos`, `principal` (especificación A para todos los resultados, con `eventos`), `coprincipales` (A, B, C, D, D2, E, E2, F, F2), `escalado_wald`, `peso_controles`, `ciudades_grandes`, `muertes_fuera`, `ventana_larga`, `anticipacion`, `base_promedio_distancia`, `eventos_base_promedio`, `rambachan_roth`, `estimadores` (CS nunca tratados, sin ponderar, Sun y Abraham, Gardner, TWFE, WCR, Bacon ponderada y sin ponderar, permutación), `poisson`, `poisson_distancia`, `ipw`, `balance`, `propension`, `definiciones`, `heterogeneidad` (con `q_bh`), `bh_*`, `umbrales_heterogeneidad`, `magnitudes`. Las tablas CSV de `output/tablas/` son vistas planas de esas secciones.
