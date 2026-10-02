#!/usr/bin/env python3
"""Agrega los resultados de los benchmarks de normativa-uvigo-eeae.

Lee results/<AAAA-MM-DD>/runs y results/<AAAA-MM-DD>/notas y escribe
summary.json y summary.md en esa misma carpeta. Si matplotlib está instalado,
genera además hasta tres gráficas en docs/img/ (o en --img-dir). Si no lo está,
avisa y sigue: el resumen no depende de las gráficas.

Solo usa la biblioteca estándar de Python 3 (matplotlib es opcional). Ver
benchmarks/README.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import statistics
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # evita crear benchmarks/__pycache__ dentro del repo

import run

REPO = Path(__file__).resolve().parent.parent

# Paleta categórica validada (slots 1-3; CVD y contraste comprobados) y tintas neutras.
COLORES_MODELO = {
    "deepseek": "#2a78d6",
    "opus": "#eb6834",
    "sonnet": "#1baf7a",
}
GRIS_SIN = "#a3a29b"
TINTA = {
    "primaria": "#0b0b0b",
    "secundaria": "#52514e",
    "tenue": "#8a8984",
    "rejilla": "#e6e5e0",
    "fondo": "#ffffff",
}
ETIQUETAS_CORTAS = {"skill": "con skill", "sin_skill": "sin skill"}
ETIQUETAS_EVAL = {
    0: "Revisión de examen",
    1: "Días por boda en periodo lectivo",
    2: "Horas de docencia (POD)",
    3: "Tribunal de TFG",
    4: "FPU: docencia y prórroga",
    5: "Cambio de fecha de examen",
    6: "Mención internacional",
    7: "Contratos art. 83",
    8: "Publicar notas en el tablón",
    9: "III Convenio (trampa)",
}


# ---------------------------------------------------------------------------
# Carga y cálculo
# ---------------------------------------------------------------------------


def cargar_ejecuciones(results_dir: Path) -> list[dict]:
    ejecuciones = []
    for ruta in sorted((results_dir / "runs").glob("*/*/*.json")):
        try:
            ejecuciones.append(json.loads(ruta.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return ejecuciones


def cargar_notas(results_dir: Path) -> list[dict]:
    notas = []
    for ruta in sorted((results_dir / "notas").glob("*/*/*.json")):
        try:
            notas.append(json.loads(ruta.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return notas


def clave(datos: dict) -> tuple:
    return (datos.get("modelo"), datos.get("condicion"), datos.get("eval_id"), datos.get("rep"))


def tasa(ejecucion: dict, nota: dict, evals: dict[int, dict]) -> float | None:
    """Proporción de aserciones superadas (0-1) o None si no hay nota válida."""
    if not nota or nota.get("error") or not nota.get("resultado"):
        return None
    ev = evals.get(ejecucion.get("eval_id"))
    if not ev or not ev.get("assertions"):
        return None
    aserciones = nota["resultado"].get("assertions")
    if not aserciones:
        return None
    aprobadas = sum(1 for a in aserciones if a.get("resultado") == "pass")
    return aprobadas / len(ev["assertions"])


def media_sd(valores: list[float]) -> tuple[float | None, float | None]:
    if not valores:
        return None, None
    media = statistics.mean(valores)
    sd = statistics.stdev(valores) if len(valores) > 1 else 0.0
    return media, sd


def nombre_juez(juez: str | None) -> str:
    """«claude-opus-5-5» -> «Opus 5.5»; si no se reconoce, lo deja tal cual."""
    if not juez:
        return "no registrado"
    partes = juez.split("-")
    if partes[0] == "claude" and len(partes) >= 3:
        return f"{partes[1].capitalize()} {'.'.join(partes[2:])}"
    return juez


def nota_metodologica(meta_modelos: dict) -> str:
    """Nota de cabecera redactada según los modelos y repeticiones reales."""
    partes = []
    for info in meta_modelos.values():
        etiqueta = info.get("etiqueta") or info.get("modelo") or "modelo"
        reps = info.get("repeticiones") or 0
        if reps == 1:
            partes.append(
                f"{etiqueta}: 1 repetición por pregunta, así que el ± recoge la "
                "dispersión entre las preguntas de cada condición (no entre repeticiones)"
            )
        elif reps > 1:
            partes.append(
                f"{etiqueta}: {reps} repeticiones por pregunta; el ± es la desviación "
                "típica entre las ejecuciones registradas de cada condición (incluye "
                "diferencias entre preguntas y entre repeticiones)"
            )
        else:
            partes.append(f"{etiqueta}: sin repeticiones registradas")
    partes.append("La comparación válida es con skill frente a sin skill dentro de cada modelo")
    return ". ".join(partes) + "."


def calcular_summary(results_dir: Path, evals: dict[int, dict]) -> dict:
    ejecuciones = cargar_ejecuciones(results_dir)
    notas_por_clave = {clave(n): n for n in cargar_notas(results_dir)}
    modelos = sorted({e.get("modelo") for e in ejecuciones if e.get("modelo")})
    grupos = sorted({ev.get("grupo") for ev in evals.values() if ev.get("grupo")})
    juez = next((n.get("juez") for n in notas_por_clave.values() if n.get("juez")), None)

    registros = []
    for ejecucion in ejecuciones:
        nota = notas_por_clave.get(clave(ejecucion))
        registros.append(
            {
                "ejecucion": ejecucion,
                "nota": nota,
                "tasa": tasa(ejecucion, nota, evals),
            }
        )

    tasas: dict = {}
    grupos_out: dict = {}
    por_eval: dict = {}
    for modelo in modelos:
        tasas[modelo] = {}
        grupos_out[modelo] = {}
        por_eval[modelo] = {}
        for condicion in ("skill", "sin_skill"):
            del_modelo = [r for r in registros if r["ejecucion"].get("modelo") == modelo and r["ejecucion"].get("condicion") == condicion]
            valores = [r["tasa"] for r in del_modelo if r["tasa"] is not None]
            media, sd = media_sd(valores)
            tasas[modelo][condicion] = {
                "media_pct": round(media * 100, 1) if media is not None else None,
                "sd_pct": round(sd * 100, 1) if sd is not None else None,
                "n_ejecuciones": len(del_modelo),
                "n_con_nota": len(valores),
                "n_repeticiones": max((r["ejecucion"].get("rep") or 0) for r in del_modelo) if del_modelo else 0,
                "orientativo_n1": len(valores) <= 1,
            }
            grupos_out[modelo][condicion] = {}
            for grupo in grupos:
                valores_grupo = [
                    r["tasa"]
                    for r in del_modelo
                    if r["tasa"] is not None and evals.get(r["ejecucion"].get("eval_id"), {}).get("grupo") == grupo
                ]
                media_g, _ = media_sd(valores_grupo)
                grupos_out[modelo][condicion][grupo] = round(media_g * 100, 1) if media_g is not None else None

            eval_ids = sorted({r["ejecucion"].get("eval_id") for r in del_modelo})
            for eval_id in eval_ids:
                valores_eval = [
                    r["tasa"] for r in del_modelo if r["ejecucion"].get("eval_id") == eval_id and r["tasa"] is not None
                ]
                media_e, _ = media_sd(valores_eval)
                por_eval[modelo].setdefault(condicion, {})[str(eval_id)] = (
                    round(media_e * 100, 1) if media_e is not None else None
                )
        media_skill = tasas[modelo]["skill"]["media_pct"]
        media_sin = tasas[modelo]["sin_skill"]["media_pct"]
        tasas[modelo]["mejora_puntos"] = (
            round(media_skill - media_sin, 1) if media_skill is not None and media_sin is not None else None
        )

    skill_runs = [r for r in registros if r["ejecucion"].get("condicion") == "skill"]
    uso_skill = {
        "n_ejecuciones_skill": len(skill_runs),
        "n_skill_usada": sum(1 for r in skill_runs if r["ejecucion"].get("skill_usada")),
        "pct_skill_usada": round(
            100 * sum(1 for r in skill_runs if r["ejecucion"].get("skill_usada")) / len(skill_runs), 1
        )
        if skill_runs
        else None,
    }

    def coste_medio(condicion: str, modelo: str | None = None) -> dict:
        filtro = [
            r
            for r in registros
            if r["ejecucion"].get("condicion") == condicion
            and (modelo is None or r["ejecucion"].get("modelo") == modelo)
        ]
        costes = [r["ejecucion"].get("coste_usd") for r in filtro if isinstance(r["ejecucion"].get("coste_usd"), (int, float))]
        duraciones = [r["ejecucion"].get("duracion_s") for r in filtro if isinstance(r["ejecucion"].get("duracion_s"), (int, float))]
        return {
            "n_con_coste": len(costes),
            "coste_medio_usd": round(statistics.mean(costes), 5) if costes else None,
            "coste_total_usd": round(sum(costes), 4) if costes else None,
            "duracion_media_s": round(statistics.mean(duraciones), 1) if duraciones else None,
        }

    costes = {
        "por_modelo_condicion": {
            modelo: {condicion: coste_medio(condicion, modelo) for condicion in ("skill", "sin_skill")}
            for modelo in modelos
        },
        "global": {
            "runs": coste_medio("skill"),
            "juez_costes_usd": [n.get("coste_usd_juez") for n in notas_por_clave.values() if isinstance(n.get("coste_usd_juez"), (int, float))],
            "juez_duraciones_s": [n.get("duracion_s") for n in notas_por_clave.values() if isinstance(n.get("duracion_s"), (int, float))],
        },
    }
    costes["global"]["runs_total_usd"] = round(
        sum(
            r["ejecucion"].get("coste_usd")
            for r in registros
            if isinstance(r["ejecucion"].get("coste_usd"), (int, float))
        ),
        4,
    )
    costes["global"]["juez_total_usd"] = round(sum(costes["global"]["juez_costes_usd"]), 4)
    costes["global"]["juez_duracion_media_s"] = (
        round(statistics.mean(costes["global"]["juez_duraciones_s"]), 1)
        if costes["global"]["juez_duraciones_s"]
        else None
    )
    costes["global"].pop("juez_costes_usd")
    costes["global"].pop("juez_duraciones_s")

    contaminadas = [
        f"{r['ejecucion'].get('modelo')} {r['ejecucion'].get('condicion')} {r['ejecucion'].get('eval_id')}-r{r['ejecucion'].get('rep')}"
        for r in registros
        if r["ejecucion"].get("contaminada")
    ]
    fallidas = [
        f"{r['ejecucion'].get('modelo')} {r['ejecucion'].get('condicion')} {r['ejecucion'].get('eval_id')}-r{r['ejecucion'].get('rep')}"
        for r in registros
        if r["ejecucion"].get("error") or r["ejecucion"].get("exit_code") not in (0, None)
    ]
    sin_corregir = [
        f"{n.get('modelo')} {n.get('condicion')} {n.get('eval_id')}-r{n.get('rep')}"
        for n in notas_por_clave.values()
        if n.get("error")
    ]

    metas_modelos = {}
    for modelo in modelos:
        reps = max(
            (r["ejecucion"].get("rep") or 0) for r in registros if r["ejecucion"].get("modelo") == modelo
        ) if any(r["ejecucion"].get("modelo") == modelo for r in registros) else 0
        metas_modelos[modelo] = {
            "etiqueta": run.MODELOS.get(modelo, {}).get("etiqueta", modelo),
            "cli": run.MODELOS.get(modelo, {}).get("cli"),
            "id_cli": run.MODELOS.get(modelo, {}).get("modelo_cli"),
            "esfuerzo": run.MODELOS.get(modelo, {}).get("effort") or run.MODELOS.get(modelo, {}).get("variant"),
            "repeticiones": reps,
        }

    return {
        "meta": {
            "generado": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "results_dir": (
                str(results_dir.relative_to(REPO)) if results_dir.is_relative_to(REPO) else str(results_dir)
            ),
            "n_evals": len(evals),
            "grupos": {g: sum(1 for ev in evals.values() if ev.get("grupo") == g) for g in grupos},
            "modelos": metas_modelos,
            "juez": juez,
            "n_ejecuciones": len(ejecuciones),
            "n_notas": len(notas_por_clave),
            "nota_metodologica": nota_metodologica(metas_modelos),
        },
        "tasas": tasas,
        "grupos": grupos_out,
        "por_eval": por_eval,
        "uso_skill": uso_skill,
        "costes": costes,
        "incidencias": {
            "contaminadas": contaminadas,
            "fallidas": fallidas,
            "sin_corregir": sin_corregir,
        },
    }


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------


def tabla_md(cabeceras: list[str], filas: list[list]) -> str:
    lineas = ["| " + " | ".join(cabeceras) + " |", "|" + "|".join(["---"] * len(cabeceras)) + "|"]
    for fila in filas:
        lineas.append("| " + " | ".join("" if v is None else str(v) for v in fila) + " |")
    return "\n".join(lineas)


def formato_pct(valor) -> str:
    return "—" if valor is None else f"{valor:.1f} %"


def generar_markdown(summary: dict) -> str:
    meta = summary["meta"]
    tasas = summary["tasas"]
    lineas = [
        "# Resumen del benchmark de normativa-uvigo-eeae",
        "",
        f"Generado: {meta['generado']}  ",
        f"Ejecuciones: {meta['n_ejecuciones']} | notas: {meta['n_notas']} | juez: {meta['juez']}  ",
        f"Evals: {meta['n_evals']} (grupos: {', '.join(f'{g}={n}' for g, n in meta['grupos'].items())})",
        "",
        "> " + meta["nota_metodologica"],
        "",
        "## Tasa de aserciones superadas por modelo y condición",
        "",
    ]
    filas = []
    for modelo, datos in tasas.items():
        etiqueta = meta["modelos"].get(modelo, {}).get("etiqueta", modelo)
        for condicion in ("skill", "sin_skill"):
            bloque = datos[condicion]
            valor = formato_pct(bloque["media_pct"])
            if bloque["sd_pct"] is not None and bloque["n_con_nota"] > 1:
                valor += f" ± {bloque['sd_pct']:.1f}"
            if bloque["orientativo_n1"] and bloque["n_con_nota"] == 1:
                valor += " (n=1, orientativo)"
            filas.append([etiqueta, ETIQUETAS_CORTAS[condicion], valor, bloque["n_con_nota"]])
    lineas.append(tabla_md(["Modelo", "Condición", "Aserciones superadas", "Runs con nota"], filas))
    lineas += ["", "## Mejora con skill (puntos porcentuales)", ""]
    filas = [
        [meta["modelos"].get(m, {}).get("etiqueta", m), f"{d['mejora_puntos']:+.1f} pp" if d["mejora_puntos"] is not None else "—"]
        for m, d in tasas.items()
    ]
    lineas.append(tabla_md(["Modelo", "skill − sin skill"], filas))

    lineas += ["", "## Resultado por grupo (desarrollo / nuevas)", ""]
    filas = []
    grupos = list(meta["grupos"].keys())
    for modelo, datos in summary["grupos"].items():
        for condicion in ("skill", "sin_skill"):
            fila = [meta["modelos"].get(modelo, {}).get("etiqueta", modelo), ETIQUETAS_CORTAS[condicion]]
            fila += [formato_pct(datos[condicion].get(g)) for g in grupos]
            filas.append(fila)
    lineas.append(tabla_md(["Modelo", "Condición"] + [g.capitalize() for g in grupos], filas))

    lineas += ["", "## Resultado por eval y condición", ""]
    filas = []
    for modelo, datos in summary["por_eval"].items():
        eval_ids = sorted({int(e) for cond in datos.values() for e in cond})
        for eval_id in eval_ids:
            fila = [meta["modelos"].get(modelo, {}).get("etiqueta", modelo), str(eval_id)]
            fila += [formato_pct(datos.get(c, {}).get(str(eval_id))) for c in ("skill", "sin_skill")]
            filas.append(fila)
    lineas.append(tabla_md(["Modelo", "Eval", "Con skill", "Sin skill"], filas))

    uso = summary["uso_skill"]
    lineas += [
        "",
        "## Uso real de la skill",
        "",
        f"- Ejecuciones con skill: {uso['n_ejecuciones_skill']}",
        f"- En las que la skill se usó de verdad: {uso['n_skill_usada']} ({formato_pct(uso['pct_skill_usada'])})",
        "",
        "## Coste y tiempo",
        "",
    ]
    filas = []
    for modelo, datos in summary["costes"]["por_modelo_condicion"].items():
        for condicion, bloque in datos.items():
            filas.append(
                [
                    meta["modelos"].get(modelo, {}).get("etiqueta", modelo),
                    ETIQUETAS_CORTAS[condicion],
                    f"{bloque['coste_medio_usd']:.4f}" if bloque["coste_medio_usd"] is not None else "—",
                    f"{bloque['duracion_media_s']:.0f}" if bloque["duracion_media_s"] is not None else "—",
                ]
            )
    lineas.append(tabla_md(["Modelo", "Condición", "Coste medio (USD)", "Duración media (s)"], filas))
    global_ = summary["costes"]["global"]
    lineas += [
        "",
        f"- Coste total de las respuestas: {global_['runs_total_usd']} USD",
        f"- Coste total del juez: {global_['juez_total_usd']} USD",
        f"- Duración media del juez por corrección: {global_['juez_duracion_media_s']} s",
        "",
        "## Incidencias",
        "",
        f"- Ejecuciones contaminadas: {len(summary['incidencias']['contaminadas'])}",
        f"- Ejecuciones fallidas (técnicas): {len(summary['incidencias']['fallidas'])}",
        f"- Correcciones sin nota válida: {len(summary['incidencias']['sin_corregir'])}",
        "",
    ]
    for etiqueta, lista in (
        ("Contaminadas", summary["incidencias"]["contaminadas"]),
        ("Fallidas", summary["incidencias"]["fallidas"]),
        ("Sin corregir", summary["incidencias"]["sin_corregir"]),
    ):
        if lista:
            lineas.append(f"**{etiqueta}:** " + ", ".join(lista))
            lineas.append("")
    graficas = summary.get("graficas", {})
    lineas += ["## Gráficas", ""]
    if graficas.get("generado"):
        for ruta in graficas.get("ficheros", []):
            lineas.append(f"- `{ruta}`")
    else:
        lineas.append(f"No generadas: {graficas.get('motivo', 'matplotlib no disponible')}")
    lineas.append("")
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Gráficas (opcionales)
# ---------------------------------------------------------------------------


def cargar_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
    except ImportError:
        return None
    fuentes = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams.update({
        "font.family": "Inter" if "Inter" in fuentes else "DejaVu Sans",
        "font.size": 9,
        "text.color": TINTA["primaria"],
        "axes.edgecolor": TINTA["rejilla"],
        "axes.labelcolor": TINTA["secundaria"],
        "xtick.color": TINTA["secundaria"],
        "ytick.color": TINTA["secundaria"],
        "figure.facecolor": TINTA["fondo"],
        "axes.facecolor": TINTA["fondo"],
        "savefig.facecolor": TINTA["fondo"],
    })
    return plt


def num_es(valor: float, decimales: int = 1) -> str:
    """Número con coma decimal, como en el README."""
    return f"{valor:.{decimales}f}".replace(".", ",")


def nombre_corto(meta: dict, modelo: str) -> str:
    return meta["modelos"].get(modelo, {}).get("etiqueta", modelo).split(" (")[0]


def texto_esfuerzo(meta: dict, modelo: str) -> str:
    return f"effort {meta['modelos'].get(modelo, {}).get('esfuerzo') or 'por defecto'}"


def nota_pie_grafica(summary: dict) -> str:
    """Nota al pie de las gráficas según modelos, repeticiones y juez reales."""
    meta = summary["meta"]
    reps = sorted({info.get("repeticiones") or 0 for info in meta["modelos"].values()})
    if not reps:
        txt_reps = "sin repeticiones registradas"
    elif len(reps) == 1:
        txt_reps = f"{reps[0]} repetición por pregunta" if reps[0] == 1 else f"{reps[0]} repeticiones por pregunta"
    else:
        txt_reps = "repeticiones: " + ", ".join(
            f"{m}={info.get('repeticiones')}" for m, info in meta["modelos"].items()
        )
    return (
        f"n={meta.get('n_evals')} preguntas por condición; {txt_reps}; "
        f"juez: {nombre_juez(meta.get('juez'))}"
    )


def _guardar(fig, plt, ruta: Path) -> str:
    fig.savefig(ruta, dpi=200)
    plt.close(fig)
    return str(ruta.relative_to(REPO)) if ruta.is_relative_to(REPO) else str(ruta)


def _pesa(ax, y: float, sin: float, con: float, color: str, *, fuente: float, grueso: bool = False) -> None:
    """Dibuja una «pesa»: sin skill (hueco, gris) unido a con skill (relleno, color del modelo)."""
    ax.plot([sin, con], [y, y], color=color, alpha=0.35, lw=2.5, solid_capstyle="round", zorder=2)
    ax.scatter([sin], [y], s=46, facecolor=TINTA["fondo"], edgecolor=GRIS_SIN, linewidths=1.8, zorder=3)
    ax.scatter([con], [y], s=58, color=color, edgecolor=TINTA["fondo"], linewidths=1.2, zorder=4)
    izq, der = (sin, con) if sin <= con else (con, sin)
    lados = ((der, "left", 7),) if sin == con else ((izq, "right", -7), (der, "left", 7))
    for x, ha, dx in lados:
        valor = x
        es_con = x == con
        ax.annotate(
            num_es(valor, 0 if fuente < 8 else 1) + (" =" if sin == con else ""), (x, y), textcoords="offset points", xytext=(dx, 0),
            ha=ha, va="center", fontsize=fuente,
            color=TINTA["primaria"] if es_con else TINTA["secundaria"],
            fontweight="semibold" if es_con and grueso else "normal",
        )


def _leyenda(destino, **kwargs) -> None:
    from matplotlib.lines import Line2D

    asas = [
        Line2D([], [], ls="", marker="o", ms=6.5, mfc=TINTA["fondo"], mec=GRIS_SIN, mew=1.8, label="sin skill"),
        Line2D([], [], ls="", marker="o", ms=7, mfc=TINTA["secundaria"], mec=TINTA["fondo"], label="con skill (color del modelo)"),
    ]
    destino.legend(handles=asas, ncol=2, frameon=False, fontsize=8, handletextpad=0.3,
                   columnspacing=1.4, labelcolor=TINTA["secundaria"], **kwargs)


def _ejes_pct(ax) -> None:
    ax.set_xlim(-4, 104)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0", "25", "50", "75", "100 %"], fontsize=7.5)
    ax.xaxis.set_ticks_position("top")
    ax.tick_params(axis="x", length=0, pad=2, colors=TINTA["tenue"])
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=TINTA["rejilla"], lw=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right", "left", "bottom"):
        ax.spines[lado].set_visible(False)


def graficar_barras(summary: dict, img_dir: Path, plt) -> str | None:
    """Acierto global y por grupo, con y sin skill, para cada modelo (gráfico de pesas)."""
    from matplotlib.transforms import blended_transform_factory

    tasas, grupos, meta = summary["tasas"], summary["grupos"], summary["meta"]
    modelos = [m for m in tasas if tasas[m]["skill"]["media_pct"] is not None and tasas[m]["sin_skill"]["media_pct"] is not None]
    if not modelos:
        return None

    filas = []  # (y, tipo, modelo, etiqueta, sin, con)
    y = 0.0
    for modelo in modelos:
        filas.append((y, "cabecera", modelo, None, None, None))
        y -= 1
        filas.append((y, "global", modelo, "Global", tasas[modelo]["sin_skill"]["media_pct"], tasas[modelo]["skill"]["media_pct"]))
        y -= 1
        for grupo, n in meta["grupos"].items():
            sin = grupos.get(modelo, {}).get("sin_skill", {}).get(grupo)
            con = grupos.get(modelo, {}).get("skill", {}).get(grupo)
            if sin is not None and con is not None:
                filas.append((y, "grupo", modelo, f"{grupo.capitalize()} ({n})", sin, con))
                y -= 1
        y -= 0.5

    alto = 1.75 + 0.33 * (-y)
    fig, ax = plt.subplots(figsize=(7.6, alto))
    fig.subplots_adjust(left=0.22, right=0.84, top=1 - 1.3 / alto, bottom=0.42 / alto)
    _ejes_pct(ax)
    ax.set_ylim(y + 0.6, 0.6)
    ax.set_yticks([])
    trans = blended_transform_factory(ax.transAxes, ax.transData)

    for fy, tipo, modelo, etiqueta, sin, con in filas:
        color = COLORES_MODELO.get(modelo, TINTA["secundaria"])
        if tipo == "cabecera":
            ax.plot([-0.285], [fy], marker="s", ms=7, color=color, transform=trans, clip_on=False)
            ax.text(-0.265, fy, nombre_corto(meta, modelo), transform=trans, ha="left", va="center",
                    fontsize=9.5, fontweight="semibold")
            ax.text(1.02, fy, texto_esfuerzo(meta, modelo), transform=trans, ha="left", va="center",
                    fontsize=7.5, color=TINTA["tenue"])
            continue
        grueso = tipo == "global"
        ax.text(-0.265, fy, etiqueta, transform=trans, ha="left", va="center", fontsize=8.5,
                color=TINTA["primaria"] if grueso else TINTA["secundaria"])
        _pesa(ax, fy, sin, con, color, fuente=8, grueso=grueso)
        ax.text(1.02, fy, f"{'+' if con - sin >= 0 else '−'}{num_es(abs(con - sin))} pp", transform=trans,
                ha="left", va="center", fontsize=8.5 if grueso else 8,
                fontweight="semibold" if grueso else "normal",
                color=TINTA["primaria"] if grueso else TINTA["secundaria"])

    mejoras = [tasas[m]["mejora_puntos"] for m in modelos]
    if len(modelos) == 1:
        titulo = f"La skill sube el acierto {num_es(mejoras[0])} puntos"
    elif all(d > 0 for d in mejoras):
        titulo = f"La skill sube el acierto en los {len(modelos)} modelos"
    else:
        titulo = f"La skill sube el acierto en {sum(d > 0 for d in mejoras)} de {len(modelos)} modelos"
    fig.text(0.03, 1 - 0.22 / alto, titulo, fontsize=12, fontweight="semibold", va="top")
    fig.text(0.03, 1 - 0.52 / alto, "% de aserciones superadas · a la derecha, mejora en puntos porcentuales",
             fontsize=8.5, color=TINTA["secundaria"], va="top")
    _leyenda(fig, loc="upper left", bbox_to_anchor=(0.025, 1 - 0.68 / alto))
    fig.text(0.03, 0.12 / alto, nota_pie_grafica(summary), fontsize=7, color=TINTA["tenue"])
    return _guardar(fig, plt, img_dir / "bench-aciertos.png")


def graficar_por_pregunta(summary: dict, img_dir: Path, plt) -> str | None:
    """Acierto por pregunta, con y sin skill: un panel de pesas por modelo."""
    from matplotlib.transforms import blended_transform_factory

    meta, por_eval = summary["meta"], summary["por_eval"]
    modelos = [m for m in por_eval if por_eval[m].get("skill") and por_eval[m].get("sin_skill")]
    if not modelos:
        return None
    evals = run.cargar_evals()["evals"]
    grupos = list(dict.fromkeys(ev.get("grupo") for ev in evals))

    filas = []  # (y, tipo, eval_id, etiqueta)
    y = 0.0
    for grupo in grupos:
        filas.append((y, "grupo", None, (grupo or "otros").capitalize()))
        y -= 1
        for ev in evals:
            if ev.get("grupo") == grupo:
                filas.append((y, "eval", ev["id"], f"{ev['id']} · {ETIQUETAS_EVAL.get(ev['id'], 'Eval')}"))
                y -= 1
        y -= 0.35

    alto = 2.0 + 0.28 * (-y)
    fig, ejes = plt.subplots(1, len(modelos), figsize=(3.0 + 2.9 * len(modelos), alto), sharey=True, squeeze=False)
    fig.subplots_adjust(left=0.235 if len(modelos) > 1 else 0.36, right=0.95, top=1 - 1.45 / alto,
                        bottom=0.42 / alto, wspace=0.3)
    mejoras = empates = total = 0
    for k, (ax, modelo) in enumerate(zip(ejes[0], modelos)):
        color = COLORES_MODELO.get(modelo, TINTA["secundaria"])
        _ejes_pct(ax)
        ax.set_ylim(y + 0.5, 0.6)
        ax.set_yticks([])
        trans = blended_transform_factory(ax.transAxes, ax.transData)
        cabecera = 1.0 + 0.42 / (alto * ax.get_position().height)
        ax.plot([0.0], [cabecera], marker="s", ms=7, color=color, transform=ax.transAxes, clip_on=False)
        ax.text(0.045, cabecera, f"{nombre_corto(meta, modelo)}  ·  {texto_esfuerzo(meta, modelo)}",
                transform=ax.transAxes, ha="left", va="center", fontsize=9.5, fontweight="semibold")
        for fy, tipo, eval_id, etiqueta in filas:
            if tipo == "grupo":
                if k == 0:
                    ax.text(-0.04, fy, etiqueta.upper(), transform=trans, ha="right", va="center",
                            fontsize=7, color=TINTA["tenue"], fontweight="semibold")
                continue
            if k == 0:
                ax.text(-0.04, fy, etiqueta, transform=trans, ha="right", va="center", fontsize=8,
                        color=TINTA["secundaria"])
            sin = por_eval[modelo]["sin_skill"].get(str(eval_id))
            con = por_eval[modelo]["skill"].get(str(eval_id))
            if sin is None or con is None:
                continue
            total += 1
            mejoras += con > sin
            empates += con == sin
            _pesa(ax, fy, sin, con, color, fuente=7)

    peores = total - mejoras - empates
    titulo = f"Con la skill mejora en {mejoras} de {total} casos pregunta-modelo"
    sub = f"{empates} igual{'es' if empates != 1 else ''}, {peores} peor{'es' if peores != 1 else ''} · % de aserciones superadas por pregunta"
    fig.text(0.02, 1 - 0.22 / alto, titulo, fontsize=12, fontweight="semibold", va="top")
    fig.text(0.02, 1 - 0.52 / alto, sub, fontsize=8.5, color=TINTA["secundaria"], va="top")
    _leyenda(fig, loc="upper right", bbox_to_anchor=(0.985, 1 - 0.14 / alto))
    fig.text(0.02, 0.12 / alto, nota_pie_grafica(summary), fontsize=7, color=TINTA["tenue"])
    return _guardar(fig, plt, img_dir / "bench-por-pregunta.png")


def graficar_coste(summary: dict, img_dir: Path, plt) -> str | None:
    """Acierto frente a coste medio por respuesta (escala logarítmica en el coste)."""
    meta = summary["meta"]
    puntos = {}
    for modelo, condiciones in summary["costes"]["por_modelo_condicion"].items():
        par = {}
        for condicion in ("sin_skill", "skill"):
            coste = condiciones.get(condicion, {}).get("coste_medio_usd")
            valor = summary["tasas"].get(modelo, {}).get(condicion, {}).get("media_pct")
            if coste and valor is not None:
                par[condicion] = (coste, valor)
        if len(par) == 2:
            puntos[modelo] = par
    if len(puntos) < 2:
        return None

    import math as _m

    costes = [c for par in puntos.values() for c, _ in par.values()]
    valores = [v for par in puntos.values() for _, v in par.values()]
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    fig.subplots_adjust(left=0.10, right=0.96, top=0.78, bottom=0.2)
    ax.set_xscale("log")
    lo, hi = min(costes) / 2.2, max(costes) * 2.2
    ax.set_xlim(lo, hi)
    marcas = [t for t in (0.003, 0.01, 0.03, 0.1, 0.3, 1, 3) if lo <= t <= hi]
    ax.set_xticks(marcas)
    ax.set_xticklabels([f"{num_es(t, 3 if t < 0.01 else 2 if t < 1 else 0)} $" for t in marcas], fontsize=8)
    ax.xaxis.set_minor_locator(plt.NullLocator())
    piso = max(0, 10 * _m.floor((min(valores) - 12) / 10))
    ax.set_ylim(piso, 100)
    ax.set_yticks(range(piso, 101, 10))
    ax.set_yticklabels([f"{v}" if v < 100 else "100 %" for v in range(piso, 101, 10)], fontsize=8)
    ax.tick_params(length=0, colors=TINTA["tenue"])
    ax.grid(color=TINTA["rejilla"], lw=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(TINTA["tenue"])
    ax.set_xlabel("Coste medio por respuesta (USD, escala logarítmica)", fontsize=8.5, color=TINTA["secundaria"])

    for modelo, par in puntos.items():
        color = COLORES_MODELO.get(modelo, TINTA["secundaria"])
        (cs, vs), (cc, vc) = par["sin_skill"], par["skill"]
        ax.annotate("", (cc, vc), (cs, vs), arrowprops={
            "arrowstyle": "-|>", "color": color, "alpha": 0.45, "lw": 2, "shrinkA": 6, "shrinkB": 7,
            "mutation_scale": 11,
        }, zorder=2)
        ax.scatter([cs], [vs], s=52, facecolor=TINTA["fondo"], edgecolor=GRIS_SIN, linewidths=1.8, zorder=3)
        ax.scatter([cc], [vc], s=64, color=color, edgecolor=TINTA["fondo"], linewidths=1.2, zorder=4)
        ax.annotate(f"{num_es(vs)} % · {num_es(cs, 3)} $", (cs, vs), textcoords="offset points",
                    xytext=(0, -13), ha="center", va="top", fontsize=7.5, color=TINTA["secundaria"])
        ax.annotate(f"{nombre_corto(meta, modelo)}\n{num_es(vc)} % · {num_es(cc, 3)} $", (cc, vc),
                    textcoords="offset points", xytext=(0, 11), ha="center", va="bottom", fontsize=8,
                    color=TINTA["primaria"], linespacing=1.25)

    con = sorted(((par["skill"][0], m) for m, par in puntos.items()))
    barato, caro = con[0][1], con[-1][1]
    ratio = puntos[caro]["skill"][0] / puntos[barato]["skill"][0]
    fig.text(0.03, 0.95, f"{nombre_corto(meta, caro)} cuesta ~{ratio:.0f}× más por respuesta que "
             f"{nombre_corto(meta, barato)}", fontsize=12, fontweight="semibold", va="top")
    fig.text(0.03, 0.875, "% de aserciones superadas frente a coste medio por respuesta · la flecha va de sin skill a con skill",
             fontsize=8.5, color=TINTA["secundaria"], va="top")
    _leyenda(ax, loc="lower right")
    fig.text(0.03, 0.025, nota_pie_grafica(summary) + " · " + "; ".join(
        f"{nombre_corto(meta, m)}: {texto_esfuerzo(meta, m)}" for m in puntos), fontsize=7, color=TINTA["tenue"])
    return _guardar(fig, plt, img_dir / "bench-coste.png")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parsear_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Agrega los resultados de los benchmarks y genera summary.json, summary.md y gráficas.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--results-dir", default="", help="Carpeta de resultados. Por defecto, benchmarks/results/<AAAA-MM-DD>.")
    p.add_argument("--img-dir", default="", help="Carpeta de las gráficas. Por defecto, docs/img.")
    p.add_argument("--no-plots", action="store_true", help="No genera gráficas.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parsear_args(argv)

    if args.results_dir:
        results_dir = Path(args.results_dir).expanduser()
        if not results_dir.is_absolute():
            results_dir = (Path.cwd() / results_dir).resolve()
    else:
        results_dir = REPO / "benchmarks" / "results" / run.fecha_hoy()

    evals = {ev["id"]: ev for ev in run.cargar_evals()["evals"]}
    if not (results_dir / "runs").exists():
        print(f"No hay ejecuciones en {results_dir / 'runs'}", file=sys.stderr)
        return 1

    summary = calcular_summary(results_dir, evals)
    img_dir = Path(args.img_dir).expanduser() if args.img_dir else REPO / "docs" / "img"
    if not img_dir.is_absolute():
        img_dir = (Path.cwd() / img_dir).resolve()

    graficas = {"generado": False, "ficheros": [], "motivo": None}
    if args.no_plots:
        graficas["motivo"] = "desactivadas con --no-plots"
    else:
        plt = cargar_matplotlib()
        if plt is None:
            graficas["motivo"] = "matplotlib no está instalado"
            print("Aviso: matplotlib no está instalado; se genera el resumen sin gráficas.")
        else:
            img_dir.mkdir(parents=True, exist_ok=True)
            for funcion in (graficar_barras, graficar_por_pregunta, graficar_coste):
                try:
                    ruta = funcion(summary, img_dir, plt)
                    if ruta:
                        graficas["ficheros"].append(ruta)
                except Exception as exc:  # noqa: BLE001 - una gráfica no debe tumbar el informe
                    print(f"Aviso: falló {funcion.__name__}: {exc}", file=sys.stderr)
            graficas["generado"] = bool(graficas["ficheros"])
            if not graficas["generado"]:
                graficas["motivo"] = "matplotlib disponible pero no se pudo dibujar ninguna gráfica"
    summary["graficas"] = graficas

    ruta_json = results_dir / "summary.json"
    ruta_md = results_dir / "summary.md"
    ruta_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ruta_md.write_text(generar_markdown(summary) + "\n", encoding="utf-8")
    print(f"Escrito {ruta_json}")
    print(f"Escrito {ruta_md}")
    if graficas["generado"]:
        for ruta in graficas["ficheros"]:
            print(f"Gráfica: {ruta}")
    else:
        print(f"Gráficas: {graficas['motivo']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
