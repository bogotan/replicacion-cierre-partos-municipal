# Fuentes del artículo A2

Consultadas entre el 24 y el 25 de octubre de 2026. Para cada una: qué se verificó en ella. Solo se citan fuentes que se abrieron y leyeron.

## Datos

| Fuente | URL | Qué se verificó o usó |
|---|---|---|
| DANE, Estadísticas Vitales 2024 (catálogo 878) | https://microdatos.dane.gov.co/index.php/catalog/878 | Productor, cobertura nacional y municipal; desde 2022 se integran registros de la Registraduría sin contacto con el sector salud, lo que puede aumentar los campos vacíos. Microdatos 1998–2025 en `data/processed/ext/` (script 50). |
| DANE, DIVIPOLA con coordenadas (gdxc-w37w) | https://www.datos.gov.co/api/views/gdxc-w37w | Puntos de referencia municipales para la distancia de haversine (archivo del estudio 52). |
| MinSalud, REPS capacidad instalada (s2ru-bqt6) | https://www.datos.gov.co/resource/s2ru-bqt6 | Salas de partos habilitadas por municipio, corte 5-nov-2022 (archivo del estudio 52). |
| IDEAM, Catálogo Nacional de Estaciones (hp9r-jxuu) | https://www.datos.gov.co/resource/hp9r-jxuu | Altitud de la estación más cercana como covariable (archivo del estudio 52). |

## Normas

| Fuente | URL | Qué se verificó |
|---|---|---|
| Resolución 3280 de 2018 (MinSalud) | https://normograma.supersalud.gov.co/compilacion/docs/resolucion_minsaludps_3280_2018.htm | Fecha (2-ago-2018); adopta la Ruta Integral de Atención en Salud Materno Perinatal; el índice incluye «Implementación de hogares maternos de paso» (6.2.2); el numeral 2.2.3 pide a las EAPB garantizar las rutas en el municipio de residencia y mecanismos que eviten el desplazamiento a otros municipios. |
| Resolución 3100 de 2019 (MinSalud) | https://normograma.supersalud.gov.co/compilacion/docs/resolucion_minsaludps_3100_2019.htm | Fecha (25-nov-2019); procedimientos de inscripción en el REPS y habilitación; art. 14.1: los nuevos servicios de atención del parto requieren visita previa; art. 13: el cierre de servicios de atención del parto se informa por escrito a la secretaría de salud y a las entidades pagadoras con al menos veinte días calendario de antelación. |

## Literatura

| Referencia | URL abierta | Qué se verificó |
|---|---|---|
| Kozhimannil et al. (2018), *JAMA* 319(12):1239–1247 | https://jamanetwork.com/journals/jama/fullarticle/2674780 | Diseño (2004–2014, 1.086 condados, 179 con pérdida de servicios); efectos al año en no adyacentes: partos fuera del hospital 0,70 pp (0,30 a 1,10), en hospitales sin unidad obstétrica 3,06 pp, prematuros 0,67 pp (0,02 a 1,33); en adyacentes, sin cambio en partos fuera del hospital (0,08) ni prematuros (0,23). |
| Fischer, Royer y White (2023), IZA DP 15987 | https://docs.iza.org/dp15987.pdf | Resultados principales con estudios de eventos TWFE; con el estimador de de Chaisemartin y D'Haultfoeuille la mortalidad infantil aumenta de forma significativa, resultado que los autores juzgan anómalo. 605 condados que perdieron todo servicio obstétrico, 1989–2019; distancia +30 millas; parto fuera del condado +27,5 pp; parto fuera del hospital sin cambio; mortalidad infantil nula (excluye aumentos > 5,4 %); cesárea −1,1 pp; mecanismo: hospitales receptores de mayor calidad. |
| Hung et al. (2016), *Health Services Research* 51(4):1546–1560 | https://experts.umn.edu/en/publications/why-are-obstetric-units-in-rural-hospitals-closing-their-doors/ | 306 hospitales rurales en nueve estados; 7,2 % cerró entre 2010 y 2014; 29 millas adicionales para el parto. |
| Grzybowski, Stoll y Kornelsen (2011), *BMC Health Services Research* 11:147 | https://link.springer.com/content/pdf/10.1186/1472-6963-11-147.pdf | 49.402 nacimientos rurales en Columbia Británica; OR de mortalidad perinatal 3,17 (1,45 a 6,95) a más de 4 horas; sin diferencias entre 1 y 4 horas. |
| Leal et al. (2020), *Revista de Saúde Pública* 54:8 | https://scielosp.org/pdf/rsp/2020.v54/08/pt | Nascer no Brasil, 19.117 mujeres SUS; peregrinación a un hospital 19,7 % y a dos 3,8 % (23,5 % en total); OR prematuridad espontánea 1,61 (1,29 a 2,01), bajo peso 1,56, *near miss* neonatal 1,48. |
| Felipe et al. (2024), *Cadernos de Saúde Pública* 40(5) | https://www.scielosp.org/pdf/csp/2024.v40n5/e00064423 | Partos de riesgo habitual del SUS fuera del municipio: 15,9 % (2010–2011) a 21,5 % (2018–2019); tiempo en bus 96,1 minutos en 2018–2019. |
| Callaway y Sant'Anna (2021), *Journal of Econometrics* 225(2):200–230 | https://arxiv.org/abs/1803.09015 ; datos de publicación en https://bibbase.org/network/publication/callaway-santanna-differenceindifferenceswithmultipletimeperiods-2021 | Parámetros por cohorte y periodo, agregaciones, IPW/OR/DR, bootstrap multiplicador. |
| Sun y Abraham (2021), *Journal of Econometrics* 225(2):175–199 | https://arxiv.org/abs/1804.05785 ; https://ideas.repec.org/a/eee/econom/v225y2021i2p175-199.html | Contaminación de adelantos y rezagos del TWFE; DOI. |
| Gardner (2022), arXiv:2207.05943 | https://arxiv.org/abs/2207.05943 | Primera etapa con observaciones no tratadas; segunda etapa. |
| Goodman-Bacon (2021), *Journal of Econometrics* 225(2):254–277 | https://www.nber.org/papers/w25018 | TWFE como promedio ponderado de comparaciones 2 × 2; datos de la versión publicada. |
| Rambachan y Roth (2023), *Review of Economic Studies* 90(5):2555–2591 | https://ideas.repec.org/a/oup/restud/v90y2023i5p2555-2591..html ; borrador https://scholar.harvard.edu/sites/scholar.harvard.edu/files/jroth/files/honestparalleltrends_main.pdf | Restricciones de suavidad y magnitudes relativas, conjunto identificado, intervalos FLCI y condicionales/híbridos. |
| Rambachan y Roth, HonestDiD (README) | https://github.com/asheshrambachan/HonestDiD | Definición de magnitudes relativas respecto a la mayor violación previa entre periodos consecutivos (el borrador de 2020 la planteaba respecto al periodo inmediato). |
| Wooldridge (2023), *The Econometrics Journal* 26(3):C31–C66 | https://ideas.repec.org/a/oup/emjrnl/v26y2023i3pc31-c66..html | DiD no lineal con adopción escalonada; Poisson con media exponencial. |
| Garavito Jiménez (2026b), Estudio 55, nota técnica | `estudios-eevv/55_calidad_dato_defunciones/nota_tecnica.md` | Completitud implícita en las tasas del DANE: 49,5 % en menores de cinco años (cálculo del estudio, no publicado por el DANE como completitud). |
| Garavito Jiménez (2026a), Estudio 52, nota técnica | `estudios-eevv/52_desiertos_obstetricos/nota_tecnica.md` | 816 municipios con sala en el REPS 2022, 227 con menos de 12 partos; salas del país 2017–2022; subregistro y limitaciones. |
| Revista *Lecturas de Economía*, normas para autores | https://revistas.udea.edu.co/index.php/lecturasdeeconomia/about/submissions | 8.000 palabras con notas, tablas, figuras y referencias; resumen ≤ 150 palabras en español e inglés; 5 a 6 palabras clave; JEL; APA 7; ecuaciones numeradas a la derecha; datos y código replicables. |
| *Revista de Salud Pública* (UNAL), normas | https://revistas.unal.edu.co/index.php/revsaludpublica/about/submissions | 4.500 palabras, hasta 3 tablas o figuras, Vancouver: se descartó por extensión. |

## No citadas por no poder abrirse

- PubMed y PMC (registro 29522161, PMC5885848) exigen verificación de navegador; se leyó el artículo de Kozhimannil et al. en el sitio de *JAMA*.
- Abadie (2005) sobre DiD semiparamétrico: no se abrió el original; la versión IPW se atribuye a Callaway y Sant'Anna (2021).
