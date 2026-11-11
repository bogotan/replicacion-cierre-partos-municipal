# Datos

| Carpeta | Qué hay | ¿Versionado? | Cómo se produce |
|---|---|---|---|
| `raw/MANIFIESTO.csv` | una fila por insumo crudo: archivo, grupo, fuente, catálogo, URL, fecha de descarga, tamaño, SHA-256, licencia, si se redistribuye y qué lo usa (79 del DANE, grupo «eevv»; 10 del artículo, grupos «a2» y «a2-config») | sí | a mano, al descargar |
| `raw/externos/52/` | DIVIPOLA con coordenadas, catálogo de estaciones del IDEAM, REPS 2022 y sus metadatos (vendorizados del estudio 52) | sí | `scripts/00_descargar_insumos.py` verifica sus huellas |
| `raw/externos/62/` | cuadro 4 de defunciones 2018 del DANE (se descarga; solo para una prueba) y extracto de completitud del estudio 55 (versionado) | en parte | ídem |
| `raw/*.zip`, `raw/antiguos/`, `raw/poblacion/` | microdatos de nacimientos y defunciones y proyecciones de población del DANE | no (términos del ANDA) | `scripts/00_descargar_insumos.py` → `scripts/insumos_eevv/00_descargar_microdatos.py` |
| `processed/` | bases de Estadísticas Vitales y población del paquete común (una fila por evento en `ext/`) | no | `make bases-eevv` (o la variable de entorno `PROCESADO` apuntando a una copia verificada) |
| `interim/62/` | cachés del nivel B: nacimientos por año, defunciones, población, atributos y el panel completo sin suprimir | no | `scripts/01_` a `04_` |
| `intermedios/` | panel municipio-año publicable, atributos, agregados del nivel B y totales de control: punto de partida del nivel A | sí | `scripts/04_intermedios.py` |

Diccionario: `docs/DICCIONARIO.md`. Fichas de los insumos y regla de celdas pequeñas: `docs/INSUMOS.md` (sección 4) y `docs/INSUMOS_EEVV.md`.
