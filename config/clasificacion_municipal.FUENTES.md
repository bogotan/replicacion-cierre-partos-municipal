# Clasificación municipal PDET / ZOMAC — fuentes y verificación

Archivo: `config/clasificacion_municipal.csv`
Columnas: `cod_mpio` (código DANE de 5 dígitos), `departamento`, `municipio`,
`pdet` (si/no), `zomac` (si/no).

El CSV lista **únicamente** los municipios que son PDET y/o ZOMAC (347 filas).
Cualquier municipio que no aparezca se trata como `pdet=no, zomac=no` ("resto
del país") en el pipeline. Esto mantiene el archivo acotado a lo que las normas
designan explícitamente, sin inventar un listado completo de municipios.

## PDET — 170 municipios

- **Norma:** Decreto Ley 893 de 2017, "por el cual se crean los Programas de
  Desarrollo con Enfoque Territorial (PDET)".
- **Fuente del listado (descargable, con código DANE):** Portal de Datos
  Abiertos del Estado colombiano, conjunto *Municipios PDET* (Agencia de
  Renovación del Territorio — ART), identificador Socrata `idrk-ba8y`.
  - CSV: `https://www.datos.gov.co/resource/idrk-ba8y.csv?$limit=500`
  - Ficha: `https://www.datos.gov.co/Agricultura-y-Desarrollo-Rural/Municipios-PDET/idrk-ba8y`
- **Verificación:** la descarga arroja exactamente **170 municipios**, cifra que
  coincide con la del Decreto Ley 893 de 2017.
- Descargado: 2026-10-03.

## ZOMAC — 344 municipios

- **Norma:** Decreto 1650 de 2017 (reglamenta la Ley 1819 de 2016), Anexo N.º 2
  "Metodología para la definición de las Zonas Más Afectadas por el Conflicto
  Armado (ZOMAC) y listado de municipios".
- **Fuente del listado (con código DANE):** compilación normativa de la DIAN
  (texto oficial del decreto con el Anexo N.º 2 en forma de tabla):
  `https://normograma.dian.gov.co/dian/compilacion/docs/decreto_1650_2017.htm`
  La tabla del Anexo tiene columnas `Nº | Código DANE | Departamento | Municipio`.
- **Verificación:** la tabla arroja exactamente **344 códigos DANE únicos**,
  cifra que coincide con la del Decreto 1650 de 2017 (y con la difusión oficial
  de "344 municipios" del DNP).
- Descargado: 2026-10-03.

## Control cruzado (sanidad de los listados)

167 de los 170 municipios PDET también son ZOMAC. Los **3** que son PDET pero
**no** ZOMAC son capitales que ZOMAC excluye y PDET incluye:

| cod_mpio | municipio   | departamento |
|----------|-------------|--------------|
| 20001    | Valledupar  | Cesar        |
| 47001    | Santa Marta | Magdalena    |
| 47189    | Ciénaga     | Magdalena    |

Esta discrepancia es la esperada entre ambas normas (ZOMAC excluyó ciertas
capitales y ciudades grandes), y confirma que los dos listados provienen de
fuentes independientes y no uno derivado del otro.

## Reproducir

```bash
# PDET
curl -sS "https://www.datos.gov.co/resource/idrk-ba8y.csv?\$limit=500" -o pdet.csv
# ZOMAC (Anexo 2 del Decreto 1650/2017, tabla HTML en el normograma DIAN)
curl -sS "https://normograma.dian.gov.co/dian/compilacion/docs/decreto_1650_2017.htm" -o zomac.htm
```
Luego `scripts/16_clasificacion_pdet_zomac.py` consume el CSV ya consolidado.
