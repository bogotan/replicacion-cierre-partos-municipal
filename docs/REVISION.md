# Revisión de árbitro del artículo A2

Dictamen de una revisión de árbitro simulada (octubre de 2026), respuestas y cambios. A otra instancia de Claude (Anthropic), la misma herramienta usada para preparar el artículo, se le pidió actuar como árbitro; no es una revisión por pares externa.

## Contenido

1. Dictamen
2. Qué reprodujo el árbitro
3. Respuestas y cambios
4. Cambios posteriores para el repositorio

## 1. Dictamen

Revisión mayor. El árbitro reconstruyó desde cero la regla del evento y un estimador de Callaway y Sant'Anna propio, y reprodujo la muestra (1.046 elegibles, 490 tratados, 289 nunca tratados y 267 fuera; cohortes 48, 235 y 207), las medias previas (6,664; 17,36; 23,55) y los efectos de la primera versión (cuota −7,46 con su ventana; distancia 1,43; mortalidad neonatal −0,24; infantil −0,05; cesárea 1,63).

**Bloqueantes.**

- **B1.** El nulo de mortalidad depende de la base g−1. Los coeficientes previos de mortalidad son planos alrededor de −0,60 y los posteriores rondan −0,24: es un salto de nivel desde g−1. Posterior menos promedio previo da +0,36 (−0,09 a 0,81) en mortalidad neonatal y +0,55 (0,12 a 0,98) en infantil. La explicación de la §4.3 («la señal proviene de tendencias previas») quedaba refutada por las propias figuras.
- **B2.** La cota del 4,9 % no mide el efecto sobre las madres afectadas, porque el cierre desplaza 7,39 puntos de cuota local; escalado tipo Wald, el extremo superior es de unas 4,4 muertes por 1.000 nacimientos desplazados.

**Mayores.**

- **M1.** El control lo dominan las grandes ciudades: el 91 % del peso del control son nunca tratados y Bogotá sola pesa cerca de la cuarta parte. Con solo tratados como control, la distancia y la cuota cambian de signo o se achican.
- **M2.** La descomposición de Goodman-Bacon era sin ponderar y no descomponía el TWFE informado; horizontes distintos; Sun y Abraham y CS con nunca tratados comparten la base g−1.
- **M3.** La cuota local es mecánica por construcción del evento.
- **M4.** Error de código: la población de cero años sumaba cabecera, resto y total.
- **M5.** Registro de defunciones por residencia; completitud; cohortes 2021–2024 y 2025 preliminar.
- **M6.** Fischer et al. (2023) mal resumido.

**Menores.** «Menos de 38 semanas» no es prematuridad; sensibilidad de Rambachan y Roth; versión balanceada; promedio previo con su error estándar; redacción de Leal et al.; moderar la segunda implicación de política; formato doble ciego.

## 2. Qué reprodujo el árbitro

Su código (panel, regla del evento y estimador) es la base de `pruebas/test_calculos.py`, adaptado para leer `data/intermedios/` y sin importar nada del código del artículo. La prueba recalcula la muestra, las cohortes y los puntos estimados de las especificaciones A, B y C de seis resultados, y los errores estándar de C con un bootstrap por municipios propio.

## 3. Respuestas y cambios

El árbitro simulado reconstruyó desde cero la regla del evento y el estimador de Callaway y Sant'Anna y reprodujo las cifras de la primera versión (muestra, cohortes, medias previas y efectos de A). Objetó lo siguiente:

| Objeción | Qué cambió | Qué se mantuvo y por qué |
|---|---|---|
| (Bloqueante) El nulo de mortalidad depende de la base $g-1$; los $\theta(e)$ previos son planos alrededor de −0,60 y la §4.3 atribuía la señal del TWFE a tendencias previas. | Base promedio (C) y posterior menos previo (B) como coprincipales; figura 3 con niveles por año; título, resumen, §4.2–4.4 y conclusiones reescritos. Se retiró la explicación por tendencias previas. | Se mantiene A, porque ninguna base es neutral cuando el deterioro empieza antes del umbral; el texto expone las dos lecturas. |
| (Bloqueante) La cota del 4,9 % no mide el efecto sobre las madres desplazadas. | Escalado tipo Wald (tabla 3) y frase «no se detecta un cambio; el intervalo va de −12 % a +5 % con este estimando». | |
| El control lo dominan las grandes ciudades; la distancia no sobrevive a otros controles. | D, E y F (y sus versiones con base promedio) como coprincipales; se retiró «cuyo costo medible es la distancia». | |
| La descomposición de Goodman-Bacon no descomponía el TWFE informado; horizontes distintos; Sun y Abraham comparte la base con A. | Descomposición ponderada que reproduce el TWFE informado; TWFE dinámico con $e=0,\dots,5$; texto corregido. | |
| La cuota local es mecánica. | Se presenta como primera etapa descriptiva. | |
| Error de código: la población de cero años sumaba cabecera, resto y total. | Se filtra «Total»; la completitud pasa de 37 % a 73,9 % y su efecto de 1,32 a 2,64 puntos; se re-corrió todo. | La conclusión de que el cierre no empuja nacimientos fuera del registro se mantiene. |
| Registro de defunciones y 2025 preliminar. | Se documenta la asignación por residencia y la proporción de muertes neonatales fuera del municipio (91,5 % antes y 94,3 % después); se cita la completitud de menores de cinco años del estudio 55; sensibilidad sin 2025. | |
| Fischer et al. (2023) mal resumido. | Se aclara que sus resultados principales son TWFE y que el estimador de de Chaisemartin y D'Haultfoeuille da un aumento de la mortalidad infantil que los autores tratan como anómalo. | |
| Menores: «menos de 38 semanas» no es prematuridad; Rambachan y Roth; versión balanceada; promedio previo con EE; Leal et al.; política; formato doble ciego. | Prematuridad = menos de 37 semanas; se informa cuánto crece el extremo superior; cohortes hasta 2020; columna con promedio previo y EE (tabla A1); redacción de Leal et al. corregida; segunda implicación moderada y Benjamini-Hochberg en heterogeneidad; datos de la hoja de presentación marcados; depósito en Zenodo. | |

## 4. Cambios posteriores para el repositorio

Al convertir el artículo en un repositorio autosuficiente (29 de octubre de 2026) no cambió ninguna cifra del texto. Se partió el script en etapas y funciones, se vendorizó el código y los insumos del estudio 52, se aplicó la regla de celdas pequeñas a cuatro columnas del panel publicado (con agregados del nivel B que sostienen las cuatro cifras afectadas; `docs/INSUMOS.md`, sección 4) y se precisó en la sección 3.1 que la completitud de 49,5 % en menores de cinco años corresponde a 2025.
