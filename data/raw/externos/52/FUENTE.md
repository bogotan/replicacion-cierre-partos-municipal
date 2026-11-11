# Fuentes externas del estudio 52 (desiertos obstétricos)

Descargadas el 23 de octubre de 2026 desde el portal de datos abiertos del Estado colombiano (datos.gov.co, API Socrata).

| Archivo | Conjunto | URL | Qué es |
|---|---|---|---|
| `divipola_gdxc-w37w.csv` | DIVIPOLA - Códigos municipios (DANE) | https://www.datos.gov.co/api/views/gdxc-w37w/rows.csv?accessType=DOWNLOAD | 1.122 entidades (1.103 municipios, 18 áreas no municipalizadas, 1 isla) con código, nombre, longitud y latitud. Corte 30 de diciembre de 2024 (filas actualizadas el 24-ene-2025). Las coordenadas son un punto de referencia del municipio publicado por el DANE; se usan como origen y destino de la distancia en línea recta. |
| `meta_gdxc.json` | metadatos del anterior | https://www.datos.gov.co/api/views/gdxc-w37w.json | descripción y fechas |
| `reps_capacidad_obstetrica_2022.csv` | Relación de IPS públicas y privadas según el nivel de atención y capacidad instalada (MinSalud, fuente REPS) | https://www.datos.gov.co/resource/s2ru-bqt6.csv con filtro `nom_descripcion_capacidad in ('Partos','TPR','Atención del Parto','Obstetricia')` | 2.018 filas de sedes con salas de partos o camas obstétricas; «Fecha corte REPS: Nov 5 2022». El municipio sale de las cinco primeras cifras del código de sede (10 dígitos con ceros a la izquierda). |
| `meta_s2ru.json` | metadatos del anterior | https://www.datos.gov.co/api/views/s2ru-bqt6.json | |
| `minsalud_camas_salas_dpto.csv` | Cantidad de ambulancias, camas y salas por departamento, año y naturaleza jurídica (MinSalud) | https://www.datos.gov.co/resource/fa2g-cdft.csv | salas de partos y camas de obstetricia habilitadas por departamento, 2017–2022 |
| `meta_fa2g.json` | metadatos del anterior | https://www.datos.gov.co/api/views/fa2g-cdft.json | |
| `ideam_estaciones.csv` | Catálogo Nacional de Estaciones del IDEAM (hp9r-jxuu) | https://www.datos.gov.co/resource/hp9r-jxuu.csv?$limit=50000 | 9.914 estaciones con altitud, latitud y longitud (filas actualizadas el 23-oct-2026). Se usa la altitud de la estación más cercana al punto de referencia de cada municipio como aproximación de su altitud (revisión adversarial, octubre de 2026). |
| `meta_hp9r.json` | metadatos del anterior | https://www.datos.gov.co/api/views/hp9r-jxuu.json | |
