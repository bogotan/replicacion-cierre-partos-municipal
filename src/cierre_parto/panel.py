"""Etapas del nivel B: de las bases de Estadísticas Vitales (data/processed/) a los paneles municipio-año.

Las funciones reproducen la etapa «panel» del script original del artículo (62_cierre_salas_parto.py) partida en
pasos: nacimientos por año (agregar_anio), defunciones de menores de un año, población, atributos fijos del municipio,
ensamblaje del panel completo y la versión publicable con celdas suprimidas (suprimir).
"""
from __future__ import annotations

import time

import numpy as np
import polars as pl

from .armonizacion import altitudes, armonizar, haversine
from .constantes import ANIOS, COLS_SUPRIMIDAS
from .rutas import CACHE, CONFIG, EXT, PROC, X52


def agregar_anio(a: int, co: pl.DataFrame, usar_cache: bool = True) -> pl.DataFrame:
    """Agregados municipio de residencia (y de ocurrencia) de los nacidos vivos de un año, desde data/processed/ext/."""
    f = CACHE / f"mun_{a}.parquet"
    if usar_cache and f.exists():
        return pl.read_parquet(f)
    validos = co["cod"].to_list()
    cols = ["mun", "mun_oc", "sit_parto", "edad_madre", "niv_edum", "reg", "area", "etnia", "peso_nac", "t_ges", "t_ges_cie",
            "numconsul", "tipo_parto", "mul_parto", "n_hijosv", "aten_par"]
    lf = pl.scan_parquet(EXT / f"nac_{a}.parquet").select(cols).with_columns(armonizar("mun"), armonizar("mun_oc"))
    edu_bajo = [1, 2, 3, 8] if a <= 2007 else [1, 2, 13]
    edu_sd = [9] if a <= 2007 else [99]
    cr = co.select(pl.col("cod").alias("mun"), pl.col("lat").alias("la1"), pl.col("lon").alias("lo1")).lazy()
    cd = co.select(pl.col("cod").alias("mun_oc"), pl.col("lat").alias("la2"), pl.col("lon").alias("lo2")).lazy()
    sit = pl.when(pl.col("sit_parto").is_in([1, 2, 3])).then(pl.col("sit_parto")).otherwise(9)
    oc_ok = pl.col("mun_oc").is_in(validos)
    local = (pl.col("mun_oc") == pl.col("mun"))
    # residentes: municipio de residencia válido (el de ocurrencia puede faltar en contados casos)
    r = (lf.filter(pl.col("mun").is_in(validos)).join(cr, on="mun", how="left").join(cd, on="mun_oc", how="left")
         .with_columns(sit.alias("sit"),
                       pl.when(oc_ok & ~local).then(haversine(pl.col("la1"), pl.col("lo1"), pl.col("la2"), pl.col("lo2")))
                       .when(oc_ok).then(0.0).otherwise(None).alias("km"))
         .group_by("mun").agg(
             pl.len().alias("res"),
             (local & (sit == 1)).sum().alias("loc_inst"),
             (local & sit.is_in([1, 9])).sum().alias("loc_inst9"),
             local.sum().alias("loc"),
             sit.is_in([1, 2, 3]).sum().alias("sitk"),
             sit.is_in([2, 3]).sum().alias("noinst"),
             (sit == 2).sum().alias("dom"),
             (sit == 9).sum().alias("sit9"),
             pl.col("km").is_not_null().sum().alias("kmk"),
             pl.col("km").sum().alias("km"),
             (pl.col("km") > 50).sum().alias("km50"),
             pl.col("peso_nac").is_between(1, 8).sum().alias("pk"), pl.col("peso_nac").is_between(1, 4).sum().alias("bp"),
             pl.col("t_ges_cie").is_between(1, 5).sum().alias("gk"), pl.col("t_ges_cie").is_between(1, 3).sum().alias("pre"),
             pl.col("t_ges").is_between(1, 5).sum().alias("gk38"), pl.col("t_ges").is_between(1, 3).sum().alias("pre38"),
             pl.col("aten_par").is_between(1, 6).sum().alias("atk"), (pl.col("aten_par") == 1).sum().alias("medico"),
             pl.col("mul_parto").is_between(1, 5).sum().alias("mk"), pl.col("mul_parto").is_between(2, 5).sum().alias("mult"),
             pl.col("numconsul").is_between(0, 25).sum().alias("ck"), pl.col("numconsul").is_between(4, 25).sum().alias("c4"),
             (pl.col("numconsul") == 0).sum().alias("c0"),
             pl.col("tipo_parto").is_between(1, 3).sum().alias("tk"), (pl.col("tipo_parto") == 2).sum().alias("ces"),
             pl.col("edad_madre").is_between(1, 9).sum().alias("ek"), pl.col("edad_madre").is_between(1, 2).sum().alias("adol"),
             pl.col("edad_madre").is_between(6, 9).sum().alias("e35"),
             (~pl.col("niv_edum").is_in(edu_sd) & pl.col("niv_edum").is_not_null()).sum().alias("edk"),
             pl.col("niv_edum").is_in(edu_bajo).sum().alias("edb"),
             pl.col("reg").is_in([1, 2, 3, 4, 5, 6] if a <= 2007 else [1, 2, 3, 4, 5]).sum().alias("rk"),
             (pl.col("reg") == 2).sum().alias("subs"),
             pl.col("area").is_in([1, 2, 3]).sum().alias("ak"), pl.col("area").is_in([2, 3]).sum().alias("rural"),
             pl.col("etnia").is_between(1, 6).sum().alias("etk"), pl.col("etnia").is_between(1, 5).sum().alias("etn"),
             pl.col("n_hijosv").is_between(1, 30).sum().alias("hk"), (pl.col("n_hijosv") == 1).sum().alias("prim"),
         ))
    # ocurrencia: partos institucionales que ocurren en el municipio, de residentes o no
    o = (lf.filter(oc_ok).group_by("mun_oc").agg((sit == 1).sum().alias("ocu_inst"), pl.len().alias("ocu_todos"))
         .rename({"mun_oc": "mun"}))
    df = r.join(o, on="mun", how="full", coalesce=True).collect().fill_null(0).with_columns(pl.lit(a).cast(pl.Int16).alias("anio"))
    df = df.with_columns([pl.col(c).cast(pl.Float64) if c == "km" else pl.col(c).cast(pl.Int64)
                          for c in df.columns if c not in ("mun", "anio")])
    CACHE.mkdir(parents=True, exist_ok=True)
    df.write_parquet(f)
    return df


def nacimientos(co: pl.DataFrame, usar_cache: bool = True) -> pl.DataFrame:
    partes = []
    for a in ANIOS:
        t0 = time.time()
        partes.append(agregar_anio(a, co, usar_cache))
        print(f"  nacimientos {a} ({time.time() - t0:.1f} s)", flush=True)
    return pl.concat(partes, how="diagonal").fill_null(0)


def defunciones() -> pl.DataFrame:
    """Defunciones de menores de un año por municipio de residencia y año: subgrupos de edad (defunciones_eevv.parquet) y
    lugar de ocurrencia y sitio (ext/def_<año>.parquet; desde 1998 el sitio 1–2 es institución de salud y 3 domicilio)."""
    d = (pl.scan_parquet(PROC / "defunciones_eevv.parquet").filter(pl.col("anio").is_between(1998, 2025) & (pl.col("g") == 0))
         .with_columns(armonizar("mun"))
         .group_by(["anio", "mun"]).agg((pl.col("g1") == 0).sum().alias("d_neo_prec"), (pl.col("g1") == 1).sum().alias("d_neo_tard"),
                                        (pl.col("g1") == 2).sum().alias("d_posneo"), pl.len().alias("d_inf")).collect()
         .with_columns(pl.col("anio").cast(pl.Int16)))
    partes_d = []
    for a in ANIOS:
        dd = (pl.scan_parquet(EXT / f"def_{a}.parquet").filter(pl.col("g") == 0).select("mun", "mun_oc", "sit_defun", "g1")
              .with_columns(armonizar("mun"), armonizar("mun_oc"))
              .group_by("mun").agg(pl.col("g1").is_in([0, 1]).sum().alias("d_neo_ext"),
                                   (pl.col("g1").is_in([0, 1]) & (pl.col("mun_oc") != pl.col("mun"))).sum().alias("d_neo_fuera"),
                                   pl.len().alias("d_inf_ext"),
                                   (pl.col("mun_oc") != pl.col("mun")).sum().alias("d_inf_fuera"),
                                   (pl.col("sit_defun") == 3).sum().alias("d_inf_dom"))
              .with_columns(pl.lit(a).cast(pl.Int16).alias("anio")).collect())
        partes_d.append(dd)
    dx = pl.concat(partes_d).group_by(["anio", "mun"]).agg(pl.all().sum())
    return d.join(dx, on=["anio", "mun"], how="full", coalesce=True)


def poblacion() -> pl.DataFrame:
    """Población de 0 años y total por municipio y año (proyecciones del DANE). El archivo trae tres filas por municipio,
    año y edad (cabecera, centros poblados y rural disperso, total): se usa solo «Total»."""
    return (pl.scan_parquet(PROC / "mun_pob_edad.parquet").filter((pl.col("area") == "Total") & pl.col("ano").is_between(1998, 2025))
            .group_by(["ano", "mpio"]).agg(pl.col("pob").filter(pl.col("edad") == 0).sum().alias("pob0"),
                                          pl.col("pob").sum().alias("pob_tot")).collect()
            .select(pl.col("ano").cast(pl.Int16).alias("anio"), pl.col("mpio").cast(pl.Int32).alias("mun"), "pob0", "pob_tot")
            .with_columns(armonizar("mun")).group_by(["anio", "mun"]).agg(pl.col("pob0").sum(), pl.col("pob_tot").sum()))


def ensamblar(P: pl.DataFrame, d: pl.DataFrame, pob: pl.DataFrame, co: pl.DataFrame) -> pl.DataFrame:
    """Panel completo municipio-año (sin suprimir): nacimientos + defunciones + población, solo municipios de la DIVIPOLA."""
    cols_d = ["d_neo_prec", "d_neo_tard", "d_posneo", "d_inf", "d_neo_ext", "d_neo_fuera", "d_inf_ext", "d_inf_fuera", "d_inf_dom"]
    P = P.join(d, on=["anio", "mun"], how="left").with_columns([pl.col(c).fill_null(0).cast(pl.Int64) for c in cols_d])
    P = P.join(pob, on=["anio", "mun"], how="left")
    return P.filter(pl.col("mun").is_in(co["cod"].to_list())).sort(["mun", "anio"])


def atributos(P: pl.DataFrame, co: pl.DataFrame) -> pl.DataFrame:
    """Atributos fijos: departamento, nombre, coordenadas, altitud (IDEAM), PDET y ZOMAC, salas de partos del REPS 2022 y
    distancia al otro municipio más cercano con 365 o más partos institucionales al año (1998–2000 y 2008–2010)."""
    alt = altitudes(co)
    clas = pl.read_csv(CONFIG / "clasificacion_municipal.csv", infer_schema=False).select(
        pl.col("cod_mpio").cast(pl.Int32).alias("mun"), (pl.col("pdet") == "si").alias("pdet"), (pl.col("zomac") == "si").alias("zomac"))
    rp = pl.read_csv(X52 / "reps_capacidad_obstetrica_2022.csv", infer_schema=False).with_columns(
        pl.col("c_digo_sede").str.zfill(10).str.slice(0, 5).cast(pl.Int32).alias("mun"),
        pl.col("num_cantidad_capacidad_instalada").cast(pl.Int64)).with_columns(armonizar("mun"))
    rpm = rp.group_by("mun").agg(pl.col("num_cantidad_capacidad_instalada").filter(pl.col("nom_descripcion_capacidad") == "Partos")
                                 .sum().alias("salas_reps2022"))
    A = (co.select(pl.col("cod").alias("mun"), "dpc", "ndp", "nmun", "tipo", "lat", "lon")
         .join(alt, on="mun", how="left").join(clas, on="mun", how="left").join(rpm, on="mun", how="left")
         .with_columns(pl.col("pdet").fill_null(False), pl.col("zomac").fill_null(False), pl.col("salas_reps2022").fill_null(0)))
    lat = np.radians(A["lat"].to_numpy()); lon = np.radians(A["lon"].to_numpy()); cods = A["mun"].to_numpy()
    for a0, a1, nom in [(1998, 2000, "d_centro_9800"), (2008, 2010, "d_centro_0810")]:
        w = P.filter(pl.col("anio").is_between(a0, a1)).group_by("mun").agg((pl.col("ocu_inst").sum() / (a1 - a0 + 1)).alias("oi"))
        cen = set(w.filter(pl.col("oi") >= 365)["mun"].to_list())
        m = np.isin(cods, list(cen))
        dphi = lat[:, None] - lat[None, m]; dl = lon[:, None] - lon[None, m]
        h = np.sin(dphi / 2) ** 2 + np.cos(lat)[:, None] * np.cos(lat[m])[None, :] * np.sin(dl / 2) ** 2
        dd = 2 * 6371.0088 * np.arcsin(np.sqrt(h))
        dd[cods[:, None] == cods[None, m]] = np.inf   # otro municipio: se excluye el propio
        A = A.with_columns(pl.Series(nom, dd.min(axis=1)))
    return A.sort("mun")


def suprimir(P: pl.DataFrame) -> pl.DataFrame:
    """Versión publicable del panel: los conteos de COLS_SUPRIMIDAS entre 1 y 4 pasan a nulo (cruces que el DANE no publica
    por municipio: pertenencia étnica por municipio de residencia, muertes infantiles en domicilio y fuera del municipio)."""
    return P.with_columns([pl.when(pl.col(c).is_between(1, 4)).then(None).otherwise(pl.col(c)).alias(c) for c in COLS_SUPRIMIDAS])
