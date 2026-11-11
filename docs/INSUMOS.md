# Insumos del artículo A2: procedencia, términos y validación

Este documento tiene una ficha por cada insumo propio del artículo (grupos «a2» y «a2-config» de `data/raw/MANIFIESTO.csv`). Los microdatos de Estadísticas Vitales y las proyecciones de población del DANE (grupo «eevv», 79 archivos) se procesan con el paquete común sin cambios y tienen sus fichas en `docs/INSUMOS_EEVV.md`. La huella SHA-256, el tamaño y la fecha de descarga de cada archivo están en el manifiesto; `pruebas/test_insumos.py` y `make verificar-insumos` los comprueban.

## Contenido

1. Resumen de insumos
2. Fichas de los insumos propios
3. Código vendorizado del estudio 52
4. Agregados publicados y regla de celdas pequeñas
5. Validación de los intermedios contra cifras publicadas

## 1. Resumen de insumos

| Insumo | Archivo | Tamaño | ¿Versionado? | Uso |
|---|---|---|---|---|
| Microdatos de nacidos vivos 1998–2025 (DANE, ANDA) | `data/raw/*.zip`, `data/raw/antiguos/` | ~ 900 MB | no (términos del ANDA) | `scripts/insumos_eevv/03_base_nacimientos.py` → `data/processed/ext/nac_<año>.parquet` |
| Microdatos de defunciones no fetales 1979–2025 (DANE, ANDA) | ídem | | no | `scripts/insumos_eevv/02_base_defunciones.py` → `ext/def_<año>.parquet`, `defunciones_eevv.parquet` |
| Proyecciones municipales de población (DANE) | `data/raw/poblacion/` | | no | `scripts/insumos_eevv/04_poblacion.py` → `mun_pob_edad.parquet` |
| DIVIPOLA con coordenadas (DANE, datos.gov.co gdxc-w37w) | `data/raw/externos/52/divipola_gdxc-w37w.csv` | 70.850 B | sí (CC BY-SA 4.0) | universo de municipios, nombres, puntos de referencia |
| Catálogo Nacional de Estaciones (IDEAM, hp9r-jxuu) | `data/raw/externos/52/ideam_estaciones.csv` | 3.455.945 B | sí (CC BY-SA 4.0) | altitud aproximada (covariable) |
| REPS, capacidad instalada obstétrica, corte 5-nov-2022 (MinSalud, s2ru-bqt6) | `data/raw/externos/52/reps_capacidad_obstetrica_2022.csv` | 824.940 B | sí (CC BY-SA 4.0) | salas de partos por municipio |
| Metadatos de los tres conjuntos | `data/raw/externos/52/meta_*.json` | | sí | licencia y corte |
| Nota de procedencia del estudio 52 | `data/raw/externos/52/FUENTE.md` | | sí | documentación |
| Cuadro 4 de defunciones 2018 (DANE) | `data/raw/externos/62/CUADRO4-NOFETALES-2018-def.xls` | 4.244.992 B | no (se descarga) | validación de los intermedios |
| Completitud de defunciones de menores de 5 años, 2025 (estudio 55) | `data/raw/externos/62/completitud_dane_menores5_2025.json` | | sí | cifra de la sección 3.1 |
| Clasificación PDET y ZOMAC | `config/clasificacion_municipal.csv` | 11.293 B | sí | heterogeneidad y covariable |

## 2. Fichas de los insumos propios

### DIVIPOLA con coordenadas

- **Origen:** DANE, «DIVIPOLA - Códigos municipios», datos.gov.co, conjunto `gdxc-w37w`, corte del 30 de diciembre de 2024 (filas actualizadas el 24 de enero de 2025). URL: `https://www.datos.gov.co/api/views/gdxc-w37w/rows.csv?accessType=DOWNLOAD`. Descarga: 23 de octubre de 2026 (estudio 52).
- **Archivo:** 1.122 filas (1.103 municipios, 18 áreas no municipalizadas y una isla) y 7 columnas: código y nombre del departamento, código y nombre del municipio, tipo, longitud y latitud.
- **Términos:** CC BY-SA 4.0 (`meta_gdxc.json`). Se redistribuye.
- **Transformaciones:** `src/cierre_parto/armonizacion.py:coordenadas()`; la coma decimal se convierte a punto.
- **Validación:** 1.122 entidades, igual a la DIVIPOLA vigente (`test_divipola`).

### Catálogo Nacional de Estaciones del IDEAM

- **Origen:** IDEAM, datos.gov.co `hp9r-jxuu`. URL: `https://www.datos.gov.co/resource/hp9r-jxuu.csv?$limit=50000`. Descarga: 23 de octubre de 2026 (filas actualizadas ese mismo día; una descarga nueva puede tener otra huella).
- **Archivo:** 9.914 estaciones; se usan `altitud`, `latitud` y `longitud`.
- **Términos:** CC BY-SA 4.0 (`meta_hp9r.json`). Se redistribuye.
- **Transformaciones:** `armonizacion.py:altitudes()` asigna a cada municipio la altitud de la estación más cercana a su punto de referencia (mediana de la distancia a esa estación: 0,8 km).
- **Validación:** 9.914 filas y las tres columnas (`test_ideam`).

### REPS 2022, capacidad instalada obstétrica

- **Origen:** Ministerio de Salud y Protección Social, «Relación de IPS públicas y privadas según el nivel de atención y capacidad instalada», datos.gov.co `s2ru-bqt6`, filtrado a `nom_descripcion_capacidad in ('Partos','TPR','Atención del Parto','Obstetricia')`. Corte REPS: 5 de noviembre de 2022. Descarga: 23 de octubre de 2026.
- **Archivo:** 2.018 filas de sedes, 20 columnas.
- **Términos:** CC BY-SA 4.0 (`meta_s2ru.json`). Se redistribuye.
- **Transformaciones:** `panel.py:atributos()`: el municipio sale de las cinco primeras cifras del código de sede (10 dígitos); se suman las salas de partos («Partos») por municipio.
- **Validación:** 2.018 filas y fecha de corte «Nov 5 2022» en todas (`test_reps_2022`); 816 municipios con sala de partos, cifra que coincide con el estudio 52.

### Cuadro 4 de defunciones 2018

- **Origen:** DANE, Estadísticas Vitales, cifras definitivas 2018: «Defunciones por grupos de edad, sexo, según departamento, municipio y área de residencia». URL: `https://www.dane.gov.co/files/investigaciones/poblacion/2019/20-diciembre-2019/nofetales2018p/CUADRO4-NOFETALES-2018-def.xls`. Descarga: 29 de octubre de 2026.
- **Términos:** publicación del portal del DANE con la cita «Fuente: DANE». No se redistribuye; lo baja `scripts/00_descargar_insumos.py`.
- **Uso:** solo en `pruebas/test_insumos.py`, para validar los intermedios (sección 5) y sostener la regla de celdas (sección 4).

### Completitud del registro de defunciones de menores de cinco años, 2025 (estudio 55)

- **Origen:** cálculo de Sinergística (estudio 55, «calidad del registro de defunciones»), script `35_completitud_cnpv2018.py` del repositorio de Estadísticas Vitales: defunciones registradas en 2025 sobre las esperadas con las tasas de mortalidad estimadas por el DANE (Estimaciones del cambio demográfico, base CNPV 2018, actualización del 30 de julio de 2025) y la población proyectada. El archivo de origen (`output/tablas/completitud_cnpv2018.json`) tiene SHA-256 `2389241d5d7fe98edb017abf74ca7f7f8f0dc854d288c9f3280279c969ae1155`, registrado también dentro del extracto.
- **Archivo:** extracto JSON con el año 2025: completitud total 0,800 y por edad (menores de 5: 0,495; 5 a 59: 0,848; 60 y más: 0,798).
- **Términos:** CC BY 4.0 (cálculo propio con datos del DANE). Se versiona. No es una cifra publicada por el DANE como completitud, y el manuscrito lo dice.
- **Uso:** la cifra de 49,5 % de la sección 3.1. No entra en ninguna estimación. Reproducirla exige las proyecciones de mortalidad del DANE y el script del estudio 55; queda como insumo documentado.

### Clasificación PDET y ZOMAC

Ver `config/clasificacion_municipal.FUENTES.md` (Decreto Ley 893 de 2017, datos.gov.co `idrk-ba8y`; Decreto 1650 de 2017). La misma lista usa el artículo A1.

## 3. Código vendorizado del estudio 52

`src/cierre_parto/armonizacion.py` copia, sin cambios de lógica, cuatro funciones y una constante de `scripts/52_desiertos_obstetricos.py` del repositorio de Estadísticas Vitales (SHA-256 del archivo de origen: `5154dc3519dffa0ebe44c9c97903f5bf837cbea1a4811115f9830caeb7d6a1f2`): `ARMONIZA` (27086 → 27493, 94663 → 94343), `armonizar()`, `coordenadas()`, `altitudes()` y `haversine()`. Solo cambia la ruta de los insumos. Los tres insumos que esas funciones leen (DIVIPOLA, IDEAM, REPS) están en `data/raw/externos/52/` con la nota de procedencia original (`FUENTE.md`, que también menciona un archivo de salas por departamento que este artículo no usa).

El código del artículo proviene de `scripts/62_cierre_salas_parto.py` del mismo repositorio (SHA-256 `679a27f7c825a99bfd6b2db254c63edd17828230d90eb7fcb4eea5f66d109dab`), partido en etapas (`scripts/01_` a `07_`) y funciones (`src/cierre_parto/`). Los resultados del nivel A coinciden con los de ese script en todas las cifras (diferencias de coma flotante por debajo de 1e-5 relativo solo en el estimador de Gardner para la distancia, por el solucionador iterativo de pyfixest).

## 4. Agregados publicados y regla de celdas pequeñas

El estándar pide suprimir las celdas menores de 5 en cruces sensibles. El panel municipio-año tiene muchas: el 46,7 % de las celdas de muertes infantiles y el 44,7 % de las de muertes neonatales precoces están entre 1 y 4. Suprimirlas haría imposible reproducir cualquier estimación de mortalidad, porque el estimador usa la tasa de cada municipio en cada año, y no hay un agregado más grueso que sostenga los mismos efectos y errores estándar (el bootstrap necesita la contribución de cada municipio).

**Lo que no se suprime y por qué.** El DANE publica cruces más finos que los del panel. Su cuadro 4 de defunciones no fetales da, para cada municipio de residencia, área y sexo, las muertes de menos de 1 hora, de 1 a 23 horas, de 1 a 6 días, de 7 a 27 días, de 28 a 29 días, de 1 a 5 meses y de 6 a 11 meses, con celdas de 1, 2 o 3 casos. Las columnas `d_neo_prec`, `d_neo_tard`, `d_posneo` y `d_inf` del panel son sumas de esas celdas, sin sexo ni área; la prueba `test_defunciones_infantiles_2018_contra_cuadro4` comprueba que las de 2018 son idénticas a las del cuadro para los 1.122 municipios. Para los nacimientos, los cuadros definitivos del DANE publican por municipio de residencia de la madre el área, el peso al nacer (cuadro 6a), la edad de la madre (cuadro 7), el tiempo de gestación (cuadro 8), el número de hijos (cuadro 9) y el nivel educativo por edad (cuadro 13), y por municipio de ocurrencia el sitio del parto y quién lo atendió (cuadro 5) y el régimen (cuadro 12) (DANE, nacimientos 2018, cifras definitivas). Los conteos del panel por tipo de parto, controles prenatales, sitio del parto y régimen de la madre residente cruzan municipio, año y una sola característica del servicio, con la misma granularidad que esos cuadros; no describen personas y se publican.

**Lo que se suprime.** Cuatro columnas cruzan el municipio con algo que el DANE no publica a ese nivel y que puede ser sensible: la pertenencia étnica de los nacidos (`etn`; el DANE la publica solo por departamento, cuadro 11), las muertes infantiles en el domicilio (`d_inf_dom`) y las muertes neonatales e infantiles ocurridas fuera del municipio de residencia (`d_neo_fuera`, `d_inf_fuera`). En el panel versionado, sus valores de 1 a 4 son nulos (4.755, 7.930, 15.172 y 15.449 celdas).

**Qué cifras rompe la supresión y cómo se sostienen.** Con esas columnas suprimidas, el nivel A no podría recalcular cuatro cifras: el efecto del cierre sobre la proporción de nacimientos de grupos étnicos y sobre las muertes infantiles en domicilio (tabla A6), el porcentaje de muertes neonatales de residentes ocurridas fuera del municipio (91,5 % antes y 94,3 % después, sección 3.1) y la partición «20 % o más étnico» de la heterogeneidad. El nivel B las calcula con el panel completo y las guarda como agregados publicables: `data/intermedios/agregados_nivel_b.json` (efectos promedio, intervalos y porcentajes sobre cientos de municipios) y la marca municipal `etnico20` de `atributos_municipio.parquet` (sí o no, sin el conteo). El nivel A las lee de ahí (`estimacion.py:estimar()`), y `scripts/05_comparar_intermedios.py` comprueba en el nivel B que se reconstruyen idénticas.

## 5. Validación de los intermedios contra cifras publicadas

| Prueba | Qué compara | Resultado |
|---|---|---|
| `test_registros_contra_dane` | 18.450.346 registros de nacimientos 1998–2025 frente a la suma de los nacidos vivos publicados por el DANE (`pruebas/insumos_eevv/totales_publicados_dane.csv`) | iguales |
| `test_defunciones_infantiles_2018_contra_cuadro4` | muertes de menores de un año y neonatales precoces de 2018 por municipio de residencia frente al cuadro 4 del DANE | iguales en los 1.122 municipios |
| `pruebas/insumos_eevv/` | huellas de los 79 zips, columnas por año y totales anuales de las bases comunes frente a lo publicado | ver `docs/INSUMOS_EEVV.md` |
| `test_sin_registros_individuales_y_supresion` | una fila por municipio y año; ninguna celda de 1 a 4 en las columnas suprimidas | cumple |
