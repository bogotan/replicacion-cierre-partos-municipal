"""Figuras del artículo (matplotlib; estilo de la casa: Inter, fondo blanco, coma decimal, 300 ppp)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .constantes import VENTANA
from .datos import CORTA, ETIQ
from .rutas import OUT, relativa


AZUL, NARANJA, GRIS, VERDE, MORADO = "#11607A", "#C0601E", "#8a8a8a", "#1BA578", "#7B4FA3"


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    fam = "Inter" if any("Inter" in f.name for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
    plt.rcParams.update({"font.family": fam, "figure.dpi": 300, "savefig.dpi": 300, "font.size": 8,
                         "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e3e3e3",
                         "grid.linewidth": 0.6, "axes.axisbelow": True, "axes.edgecolor": "#555555", "axes.titlesize": 8.5,
                         "axes.titleweight": "semibold", "axes.titlelocation": "left", "figure.facecolor": "white", "axes.facecolor": "white",
                         "legend.frameon": False})
    return plt


def _coma(x, dec=0):
    s_ = f"{x:,.{dec}f}"
    return s_.replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")


def _auto(v):
    """Una cifra decimal salvo que el valor de la marca necesite dos (0,25; 0,75)."""
    return _coma(v, 1) if abs(round(v, 1) - v) < 1e-9 else _coma(v, 2)


def _ejes_coma(ax, dec_y=1, dec_x=None):
    from matplotlib.ticker import FuncFormatter
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: _auto(v) if dec_y == "auto" else _coma(v, dec_y)))
    if dec_x is not None:
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _coma(v, dec_x)))


def _evento(ax, ev, titulo, color=AZUL, base=-1):
    es = sorted(int(e) for e in ev)
    th = [ev[str(e)]["theta"] for e in es]
    lo = [ev[str(e)]["ic_inf"] for e in es]; hi = [ev[str(e)]["ic_sup"] for e in es]
    blo = [ev[str(e)].get("banda_inf", np.nan) for e in es]; bhi = [ev[str(e)].get("banda_sup", np.nan) for e in es]
    if base is None:
        order = np.argsort(es); x = np.array(es)[order]
        def ins(v, z):
            return np.array(v)[order]
    else:
        es2 = es + [base]; order = np.argsort(es2)
        x = np.array(es2)[order]
        def ins(v, z):
            return np.array(v + [z])[order]
    ax.fill_between(x, ins(blo, 0), ins(bhi, 0), color=color, alpha=0.12, lw=0, label="Banda uniforme 95 %")
    ax.vlines(es, lo, hi, color=color, lw=1.2)
    ax.plot(x, ins(th, 0), color=color, lw=1.4, marker="o", ms=3.2)
    ax.axhline(0, color="#555555", lw=0.8); ax.axvline(-0.5, color=GRIS, lw=0.8, ls="--")
    ax.set_title(titulo); ax.set_xlabel("Años desde el cierre")
    _ejes_coma(ax, "auto")


def figuras(salida: Path | None = None):
    salida = salida or OUT
    plt = _plt()
    r = json.loads((salida / "resultados.json").read_text(encoding="utf-8"))
    F = salida / "figuras"; F.mkdir(parents=True, exist_ok=True)

    # figura 1: cohortes y cuota local alrededor del cierre
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.8))
    coh = r["muestra"]["cohortes"]; xs = [int(k) for k in coh]; ys = [coh[k] for k in coh]
    axs[0].bar(xs, ys, color=AZUL, width=0.8)
    axs[0].set_title("A. Municipios que dejan de atender partos, por año"); axs[0].set_ylabel("Municipios")
    pe = r["cuota_local_tratados_por_e"]; ee = sorted(int(k) for k in pe)
    axs[1].plot(ee, [pe[str(e)] for e in ee], color=AZUL, lw=1.6, marker="o", ms=3)
    nv = r["cuota_local_nunca_por_anio"]
    axs[1].axhline(10, color=NARANJA, lw=0.9, ls="--"); axs[1].text(-14, 11.2, "Umbral del 10 %", color="#333333", fontsize=7)
    axs[1].axvline(-0.5, color=GRIS, lw=0.8, ls="--")
    axs[1].set_title("B. Partos de residentes en institución local (%)"); axs[1].set_xlabel("Años desde el cierre")
    axs[1].set_xticks(range(-14, 7, 2))
    _ejes_coma(axs[1], 0, dec_x=0)
    fig.tight_layout(); fig.savefig(F / "fig1_cierres_y_cuota_local.png"); plt.close(fig)

    # figura 2: acceso
    P = r["principal"]
    fig, axs = plt.subplots(2, 2, figsize=(7.2, 5.0))
    for ax, k in zip(axs.flat, ["local", "km", "km50", "noinst"]):
        _evento(ax, P[k]["eventos"], ETIQ[k])
    axs[0, 0].legend(loc="lower left", fontsize=7)
    fig.tight_layout(); fig.savefig(F / "fig2_eventos_acceso.png"); plt.close(fig)

    # figura 3: salud con base g-1 (anexo) y con base promedio del periodo previo (texto)
    fig, axs = plt.subplots(2, 3, figsize=(7.2, 4.8))
    for ax, k in zip(axs.flat, ["c4", "bp", "pre37", "ces", "neo", "inf"]):
        _evento(ax, P[k]["eventos"], CORTA[k])
    fig.tight_layout(); fig.savefig(F / "fig3_eventos_salud.png"); plt.close(fig)
    EB = r["eventos_base_promedio"]
    fig, axs = plt.subplots(2, 3, figsize=(7.2, 4.8))
    for ax, k in zip(axs.flat, ["km", "pre37", "ces", "neo", "neo_prec", "inf"]):
        _evento(ax, EB[k], CORTA[k], base=None)
        ax.axvspan(VENTANA[0] - 0.4, VENTANA[1] + 0.4, color="#8a8a8a", alpha=0.08, lw=0)
    fig.tight_layout(); fig.savefig(F / "fig8_eventos_base_promedio.png"); plt.close(fig)

    # figura 4: comparación de estimadores
    E = r["estimadores"]
    nombres = [("CS, base g−1", None, AZUL), ("CS, base promedio previo", "C", NARANJA), ("CS, solo tratados como control", "D", VERDE),
               ("CS, nunca tratados", "cs_nunca", AZUL), ("CS sin ponderar", "cs_sin_ponderar", "#b5b5b5"),
               ("CS-IPW (municipios)", "ipw", GRIS), ("Sun y Abraham", "sun_abraham", MORADO), ("Gardner (did2s)", "gardner", NARANJA),
               ("TWFE", "twfe", "#333333")]
    ks = ["km", "noinst", "c4", "bp", "pre37", "ces", "neo", "inf"]
    fig, axs = plt.subplots(2, 4, figsize=(7.4, 5.0), sharey=True)
    for ax, k in zip(axs.flat, ks):
        for j, (nm, key, col) in enumerate(nombres):
            d = (P[k] if key is None else r["ipw"][k] if key == "ipw" else r["coprincipales"]["C_base_promedio"][k] if key == "C"
                 else r["coprincipales"]["D_solo_tratados"][k] if key == "D" else E[k][key])
            y = len(nombres) - 1 - j
            ax.plot([d["ic_inf"], d["ic_sup"]], [y, y], color=col, lw=1.4)
            ax.plot(d["att"], y, "o", color=col, ms=4, mec="white", mew=0.6)
        ax.axvline(0, color="#555555", lw=0.8)
        ax.set_title(CORTA[k], fontsize=7.2); ax.set_yticks(range(len(nombres))); ax.set_yticklabels([n[0] for n in nombres][::-1], fontsize=6.8)
        from matplotlib.ticker import FuncFormatter
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _auto(v)))
        ax.tick_params(axis="x", labelsize=6.5); ax.locator_params(axis="x", nbins=4)
        ax.grid(axis="y", visible=False)
    fig.tight_layout(); fig.savefig(F / "fig4_estimadores.png"); plt.close(fig)

    # figura 5: ventana larga
    VL = r["ventana_larga"]
    fig, axs = plt.subplots(1, 4, figsize=(7.4, 2.4))
    for ax, k in zip(axs, ["local", "km", "ces", "neo"]):
        ev = {e: {"theta": v["theta"], "ic_inf": v["theta"] - 1.96 * v["ee"], "ic_sup": v["theta"] + 1.96 * v["ee"]} for e, v in VL[k].items()}
        _evento(ax, ev, CORTA[k])
        ax.title.set_fontsize(7)
    fig.tight_layout(); fig.savefig(F / "fig5_ventana_larga.png"); plt.close(fig)

    # figura 6: Rambachan y Roth
    RR = r["rambachan_roth"]
    fig, axs = plt.subplots(1, 4, figsize=(7.4, 2.4))
    for ax, k in zip(axs, ["km", "ces", "neo", "inf"]):
        Ms = sorted(float(m) for m in RR[k]["grid"] if float(m) <= 1.0)
        lo = [RR[k]["grid"][str(m) if str(m) in RR[k]["grid"] else str(int(m)) if m == int(m) else str(m)]["ic_inf"] for m in Ms]
        hi = [RR[k]["grid"][str(m) if str(m) in RR[k]["grid"] else str(int(m)) if m == int(m) else str(m)]["ic_sup"] for m in Ms]
        ax.vlines(Ms, lo, hi, color=AZUL, lw=2)
        ax.axhline(0, color="#555555", lw=0.8)
        li = RR[k]["lineal"]
        ax.vlines([-0.25], [li["ic_inf"]], [li["ic_sup"]], color=NARANJA, lw=2)
        ax.set_xticks([-0.25] + Ms); ax.set_xticklabels(["Lineal"] + [_coma(m, 2).rstrip("0").rstrip(",") for m in Ms], fontsize=6, rotation=45)
        ax.set_title(CORTA[k], fontsize=7); ax.set_xlabel("M̄ (magnitudes relativas)", fontsize=6.5)
        _ejes_coma(ax, 1)
    fig.tight_layout(); fig.savefig(F / "fig6_rambachan_roth.png"); plt.close(fig)

    # figura 7: heterogeneidad
    H = r["heterogeneidad"]
    ks = ["km50", "noinst", "neo_prec_C", "inf_C"]
    filas = [(d, g) for d in ["distancia", "ruralidad", "etnia", "pdet", "regimen", "periodo"] for g in H[d]]
    fig, axs = plt.subplots(1, 4, figsize=(7.4, 3.6), sharey=True)
    for ax, k in zip(axs, ks):
        for j, (d, g) in enumerate(filas):
            v = H[d][g][k]; y = len(filas) - 1 - j
            col = AZUL if j % 2 == 0 else NARANJA
            ax.plot([v["ic_inf"], v["ic_sup"]], [y, y], color=col, lw=1.4); ax.plot(v["att"], y, "o", color=col, ms=3.5, mec="white", mew=0.5)
        ax.axvline(0, color="#555555", lw=0.8)
        ax.set_yticks(range(len(filas))); ax.set_yticklabels([f"{g} ({H[d][g]['tratados']})" for d, g in filas][::-1], fontsize=6.3)
        ax.set_title(CORTA[k.replace("_C", "")] + (", base promedio" if k.endswith("_C") else ""), fontsize=7)
        ax.grid(axis="y", visible=False); ax.locator_params(axis="x", nbins=4)
        from matplotlib.ticker import FuncFormatter
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _auto(v))); ax.tick_params(axis="x", labelsize=6.5)
    fig.tight_layout(); fig.savefig(F / "fig7_heterogeneidad.png"); plt.close(fig)
    print("figuras ->", relativa(F))
