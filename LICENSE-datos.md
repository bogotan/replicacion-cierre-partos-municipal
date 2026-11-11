# Licencias de los datos y del texto

- **Código** (`src/`, `scripts/`, `pruebas/`, `manuscrito/armar_entregables.py`, `Makefile`): MIT (`LICENSE`). Incluye, sin cambios, el paquete común de Estadísticas Vitales (`src/eevv_insumos/`, `scripts/insumos_eevv/`) y funciones del estudio 52 (`src/cierre_parto/armonizacion.py`), ambos de Daniel A. Garavito Jiménez bajo la misma licencia.
- **Texto del manuscrito, tablas y figuras** (`manuscrito/`, `output/`): Creative Commons Atribución-NoComercial 4.0 Internacional (CC BY-NC 4.0), © 2026 Daniel A. Garavito Jiménez; citar a Sinergística con enlace.
- **Documentación de método** (`docs/`, `README.md`, `data/README.md`): Creative Commons Atribución 4.0 Internacional (CC BY 4.0), © 2026 Daniel A. Garavito Jiménez.
- **Datos derivados de `data/intermedios/`**: CC BY-NC 4.0, salvo las columnas derivadas de fuentes CC BY-SA, que conservan CC BY-SA 4.0 (abajo). Cada fuente original se cita así:
  - Estadísticas Vitales y proyecciones de población: «Fuente: Departamento Administrativo Nacional de Estadística: www.dane.gov.co». Son agregados municipio-año sin registros individuales; las defunciones tienen la misma o menor granularidad que el cuadro 4 de defunciones del DANE, y las cuatro columnas que cruzan el municipio con características que el DANE no publica a ese nivel tienen suprimidas las celdas de 1 a 4 (`docs/INSUMOS.md`, sección 4).
  - DIVIPOLA (DANE), REPS 2022 (Ministerio de Salud y Protección Social) y Catálogo Nacional de Estaciones (IDEAM), de datos.gov.co: CC BY-SA 4.0. Las columnas de `atributos_municipio.parquet` derivadas de esas fuentes (coordenadas, altitud, salas de partos, distancias) se comparten con la misma licencia CC BY-SA 4.0.
  - Clasificación PDET y ZOMAC: normas públicas (Decreto Ley 893 de 2017; Decreto 1650 de 2017).
- **Insumos originales de `data/raw/`**: rigen los términos de cada fuente (`data/raw/MANIFIESTO.csv`, columna `licencia`). Los microdatos del DANE no se redistribuyen: los términos del Archivo Nacional de Datos prohíben ponerlos a disposición de múltiples usuarios sin visto bueno escrito del DANE (`docs/INSUMOS_EEVV.md`). El cuadro 4 de defunciones 2018 tampoco se redistribuye; se descarga del portal del DANE.

## Cambio de licencia

El 4 de noviembre de 2026, antes de publicar el repositorio, el texto, las tablas, las figuras y los datos derivados pasaron de CC BY 4.0 a CC BY-NC 4.0, según la política de licencias por capa de Sinergística. La documentación de método sigue en CC BY 4.0 y el código, en MIT.
