# Replicación del artículo A2

Orden de ejecución, semillas, versiones, tiempos y memoria, y el resultado de las corridas en una copia limpia del repositorio.

## Contenido

1. Orden de ejecución
2. Semillas y determinismo
3. Versiones
4. Corrida en limpio del 29 de octubre de 2026
5. Diferencias con el script original

## 1. Orden de ejecución

**Nivel A** (desde `data/intermedios/`, versionados):

| Etapa | Script | Función | Salida |
|---|---|---|---|
| 6 | `scripts/06_estimar.py` | `cierre_parto.estimacion:estimar()` | `output/resultados.json`, `output/tablas/*.csv` |
| 7 | `scripts/07_figuras.py` | `cierre_parto.figuras:figuras()` | `output/figuras/*.png` |
| verificación | `pruebas/verificar_cifras.py` | | «Todo coincide.» |

**Nivel B** (desde los insumos originales):

| Etapa | Script | Entrada | Salida |
|---|---|---|---|
| 0 | `scripts/00_descargar_insumos.py` | URL del manifiesto | `data/raw/` verificado por huella (89 archivos) |
| bases comunes | `scripts/insumos_eevv/01_` a `04_` | zips del DANE | `data/processed/` (paquete común sin cambios) |
| 1 | `scripts/01_panel_nacimientos.py` | `data/processed/ext/nac_<año>` | `data/interim/62/mun_<año>.parquet` |
| 2 | `scripts/02_panel_defunciones.py` | `defunciones_eevv`, `ext/def_<año>`, `mun_pob_edad` | `data/interim/62/defunciones.parquet`, `poblacion.parquet` |
| 3 | `scripts/03_atributos.py` | DIVIPOLA, IDEAM, REPS, `config/` | `data/interim/62/atributos.parquet` |
| 4 | `scripts/04_intermedios.py --salida <carpeta>` | lo anterior | panel publicable, atributos, agregados del nivel B y totales |
| 5 | `scripts/05_comparar_intermedios.py` | reconstruidos y versionados | igualdad de filas y valores (tolerancia 1e-9) |

Con `make`: `make nivel-a`, `make pruebas`, `make nivel-b` (= `insumos bases-eevv pruebas-eevv intermedios comparar`), `make manuscrito`. Si ya existe una copia verificada de las bases comunes, la variable de entorno `PROCESADO=<carpeta processed>` hace que las etapas 1 a 4 la lean en lugar de `data/processed/`.

## 2. Semillas y determinismo

Semilla 20261024 en todos los procesos aleatorios (`constantes.py:SEMILLA`). Bootstrap multiplicador: 999 réplicas (499 en la ventana larga). Bootstrap salvaje agrupado: 999. Bootstrap por municipios del IPW: 199. Permutaciones: 500. Los municipios se ordenan por código y los años de 1998 a 2025 antes de estimar.

Las sumas por grupo de polars usan varios hilos y su orden puede variar; por eso la columna `km` (suma de distancias) cambia en el orden de 1e-14 relativo entre reconstrucciones del nivel B, por debajo de la tolerancia de la comparación.

**Semilla de hash.** Una auditoría de replicación del primer commit, hecha por otra instancia de Claude, (7f6d87e) obtuvo diferencias de hasta 6,3e-7 en los modelos de Poisson, Sun y Abraham y el TWFE dinámico (la mayor, en `poisson_distancia/25 km o más/inf/ic_sup`), sin cambio en ninguna cifra redondeada del texto. La causa es la semilla de hash de Python: pyfixest arma conjuntos de nombres de columnas cuyo orden de recorrido depende de ella, y cambia el orden de las operaciones. Con `PYTHONHASHSEED=0` el resultado es el mismo en todas las corridas, con uno o con varios hilos de numba. Desde el tercer commit, el `Makefile` exporta `PYTHONHASHSEED=0` y `scripts/_entorno.py` vuelve a lanzar cualquier script con esa semilla si no la tiene; por precaución también fija un hilo en numba y BLAS (`NUMBA_NUM_THREADS`, `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`). El segundo commit atribuyó la diferencia a los hilos, y eso era incorrecto. Además, los departamentos empatados de `tratados_por_departamento` ahora se ordenan por número y nombre. Con esto, `output/resultados.json` y las tablas CSV salen idénticos byte a byte en corridas desde cero (sección 4).

**Figuras.** Los PNG son idénticos píxel a píxel entre corridas, pero no byte a byte (la compresión de matplotlib varía). La prueba de las figuras es la de sus cifras.

## 3. Versiones

Python 3.13.16 y los paquetes exactos de `requirements.txt` (polars 2.0.0, numpy 2.5.3, pandas 3.0.5, scipy 1.18.1, pyfixest 0.60.0, matplotlib 3.11.2, python-calamine 0.9.0, pytest 9.2.0, entre otros). Entregables: pandoc 3.1.3 y XeLaTeX (TeX Live 2023). Fuente de las figuras: Inter.

## 4. Corrida en limpio del 29 de octubre de 2026

Máquina: 2 núcleos, 8 GB de RAM compartidos con otros tres procesos; todo con `nice -n 10`. La copia limpia se hizo con `git checkout-index` en una carpeta nueva, sin cachés y sin `output/` (se borraron `resultados.json`, las tablas y las figuras para que el nivel A las regenerara). Duración y memoria máxima medidas con `scripts/insumos_eevv/medir.py`.

| Paso | Inicio | Duración | Memoria máxima | Resultado |
|---|---|---|---|---|
| `make nivel-a` | 23:23 | 85 s | 1.106 MB | «Todo coincide.» (340 comprobaciones); `resultados.json` igual al versionado (con la semilla de hash fija, ver sección 2) |
| `make pruebas` | 23:24 | 8 s | 379 MB | 29 pruebas pasan, 2 omitidas (cuadro 4 aún no descargado); «Todo coincide.» |
| `scripts/00_descargar_insumos.py` | 23:26 | 68 s | 36 MB | 89 insumos con su huella (79 del DANE, 10 del artículo; se bajó el cuadro 4 del DANE) |
| `make pruebas-eevv` | 23:27 | 25 s | 429 MB | 234 pruebas del paquete común pasan (huellas, columnas y totales del DANE) |
| `make intermedios` | 23:28 | 6 s | 353 MB | etapas 1 a 4 |
| `make comparar` | 23:28 | 0 s | 130 MB | los cuatro intermedios coinciden con los versionados |
| `make pruebas` (con el cuadro 4) | 23:28 | 8 s | 421 MB | 31 pruebas pasan; «Todo coincide.» |

Para las bases comunes, la copia limpia usó los zips del DANE y la carpeta `data/processed/` de la reconstrucción en limpio del paquete común del mismo día (`docs/REPLICACION_EEVV.md`: 604 s, 932 MB de memoria máxima, 78 archivos idénticos byte a byte a los del repositorio de Estadísticas Vitales). Los zips se enlazaron desde esa copia y se verificaron de nuevo por su huella.

## 5. Diferencias con el script original

El código proviene de `scripts/62_cierre_salas_parto.py` del repositorio de Estadísticas Vitales, partido en etapas y funciones sin cambios de método. Con los mismos datos, todas las cifras de `resultados.json` coinciden; la única diferencia mayor de 1e-6 relativo está en el estimador de Gardner para la distancia (5,2487 frente a 5,2486), por el solucionador iterativo de pyfixest, y no cambia ninguna cifra redondeada del texto. Las secciones `descriptivos.etn` y `descriptivos.inf_dom` ya no se calculan, porque dependen de columnas suprimidas y no aparecen en el texto.
