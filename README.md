# Cuando el municipio deja de atender partos: prematuridad y mortalidad infantil en Colombia, 2001–2025

Repositorio de replicación del artículo A2. Autor: Daniel A. Garavito Jiménez (Sinergística, Bogotá). Código bajo MIT; texto, tablas, figuras y datos derivados bajo CC BY-NC 4.0; documentación de método bajo CC BY 4.0 (`LICENSE-datos.md`).

**Estado.** Artículo de Daniel A. Garavito Jiménez (Sinergística S.A.S., ORCID 0009-0009-6871-5807), enviado a *Lecturas de Economía* (Universidad de Antioquia) en noviembre de 2026. El texto del artículo y sus entregables se agregan a este repositorio cuando se publique; mientras tanto, el código, los agregados y las pruebas reproducen todas las cifras. En la preparación se usó Claude (Anthropic) como asistente de código y redacción, bajo la dirección y revisión del autor; los registros de `docs/REVISION.md` son revisiones simuladas por esa misma herramienta, no arbitraje externo.

## Contenido

1. Pregunta y hallazgo
2. Cómo reproducir
3. Insumos
4. Mapa del repositorio
5. Limitaciones conocidas

## 1. Pregunta y hallazgo

¿Qué les pasa a las madres y a los recién nacidos cuando su municipio deja de atender partos? Con 18,5 millones de nacidos vivos y las defunciones infantiles de las Estadísticas Vitales del DANE (1998–2025) se fecha el cierre funcional del parto local: el primer año en que, después de haber tenido parto institucional local estable, menos del 10 % de los nacimientos de residentes ocurre en una institución del propio municipio, de forma persistente. Hay 490 cierres entre 2001 y 2024. El efecto se estima con diferencias en diferencias escalonadas (Callaway y Sant'Anna) y seis especificaciones coprincipales.

Frente al año anterior al cierre, ningún resultado de salud cambia. Frente al promedio de los años previos, la prematuridad sube 0,57 puntos porcentuales (IC 95 %: 0,26 a 0,87) y la mortalidad infantil 0,36 por 1.000 (IC 95 %: −0,12 a 0,83); el salto aparece el año previo al cruce del umbral y se diluye con solo municipios que cierran después como control. No se detecta un daño robusto ni se puede descartar uno de magnitud apreciable para las madres desplazadas.

## 2. Cómo reproducir

```bash
pip install -r requirements.txt          # Python 3.13; para los entregables, además pandoc y XeLaTeX
make nivel-a                             # desde data/intermedios/ versionados: estimaciones, tablas, figuras y verificación
make pruebas                             # pytest pruebas/ y verificación de cada cifra del texto («Todo coincide.»)
make nivel-b                             # desde los microdatos del DANE: descarga, bases comunes, intermedios y comparación
```

**Nivel A** (lo que corre un árbitro): unos 2 minutos y 1,1 GB de memoria en una máquina de 2 núcleos. Parte de los paneles agregados municipio-año de `data/intermedios/` y reproduce todas las cifras del texto.

**Nivel B** (completo): descarga los 79 archivos del DANE y los verifica por su huella (unos 2 GB), construye las bases comunes con el paquete `insumos_eevv` (unos 10 minutos), reconstruye los intermedios con las etapas 01 a 04 y comprueba que coinciden con los versionados. Si ya hay una copia verificada de las bases comunes, se puede usar con `PROCESADO=<carpeta processed> make intermedios comparar`.

Tiempos, memoria, versiones y el resultado de las corridas en limpio: `docs/REPLICACION.md`.

## 3. Insumos

Se versionan los insumos pequeños y abiertos: la DIVIPOLA con coordenadas, el catálogo de estaciones del IDEAM y la capacidad obstétrica del REPS 2022 (datos.gov.co, CC BY-SA 4.0, vendorizados del estudio 52), la clasificación PDET y ZOMAC y un extracto de completitud del estudio 55. Se descargan y se verifican por su huella: los microdatos y las proyecciones de población del DANE, que no se redistribuyen por los términos del Archivo Nacional de Datos, y el cuadro 4 de defunciones 2018 del DANE, usado para validar los intermedios. Fichas, términos y validaciones: `docs/INSUMOS.md` y `docs/INSUMOS_EEVV.md`. Allí se explica también la regla de celdas pequeñas: cuatro columnas del panel tienen suprimidas las celdas de 1 a 4, y las cifras que dependen de ellas salen de agregados publicables del nivel B.

## 4. Mapa del repositorio

```
A2_cierre_salas_parto/
├── README.md, LICENSE, LICENSE-datos.md, CITATION.cff, requirements.txt, Makefile
├── config/                 clasificación PDET y ZOMAC y sus fuentes
├── src/
│   ├── cierre_parto/       código del artículo: rutas, constantes, armonización (estudio 52), panel (nivel B),
│   │                       evento, datos, estimadores (CS, bootstrap, Bacon, Rambachan-Roth, IPW…), estimación,
│   │                       figuras y tablas en Markdown
│   └── eevv_insumos/       paquete común de Estadísticas Vitales (sin cambios)
├── scripts/
│   ├── 00_descargar_insumos.py   descarga y verifica huellas
│   ├── 01_panel_nacimientos.py   nivel B: nacimientos por municipio y año
│   ├── 02_panel_defunciones.py   nivel B: defunciones infantiles y población
│   ├── 03_atributos.py           nivel B: atributos fijos del municipio
│   ├── 04_intermedios.py         nivel B: panel publicable, agregados y totales de control
│   ├── 05_comparar_intermedios.py
│   ├── 06_estimar.py             nivel A: output/resultados.json y output/tablas/
│   ├── 07_figuras.py             nivel A: output/figuras/
│   └── insumos_eevv/             scripts del paquete común (sin cambios)
├── data/                   raw/ (manifiesto y externos), intermedios/ (versionados), README.md
├── output/                 resultados.json, tablas/ (CSV) y figuras/ (PNG, 300 ppp)
├── pruebas/                test_insumos.py, test_calculos.py, test_estimadores.py, verificar_cifras.py, insumos_eevv/
└── docs/                   INSUMOS, CALCULOS, DICCIONARIO, REPLICACION, REVISION, FUENTES_LITERATURA (y los del paquete común)
```

## 5. Limitaciones conocidas

- La cifra de completitud de 49,5 % en menores de cinco años entra como insumo documentado del estudio 55; reproducirla exige las proyecciones de mortalidad del DANE y el código de ese estudio.
- Los conjuntos de datos.gov.co se actualizan: una descarga nueva del catálogo del IDEAM o del REPS puede tener otra huella. El artículo usa las copias versionadas.
