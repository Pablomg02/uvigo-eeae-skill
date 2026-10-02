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

PALETA = {"skill": "#1f6f8b", "sin_skill": "#b45309"}
COLORES_MODELO = {
    "deepseek": "#1f6f8b",
    "sonnet": "#b45309",
    "opus": "#4d7c0f",
}
ETIQUETAS_CORTAS = {"skill": "con skill", "sin_skill": "sin skill"}
ETIQUETAS_HEATMAP = {"deepseek": "DeepSeek", "sonnet": "Sonnet", "opus": "Opus"}


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

        return plt
    except ImportError:
        return None


def anotar_barra(ax, barra, valor: float, *, fuente: int, error: float = 0.0) -> None:
    centro = barra.get_x() + barra.get_width() / 2
    y = valor + error
    bbox = {"boxstyle": "round,pad=0.1", "fc": "#ffffff", "ec": "none", "alpha": 0.75} if error else None
    if y > 94:
        ax.annotate(f"{valor:.1f}", (centro, valor), textcoords="offset points",
                    xytext=(0, -6), ha="center", va="top", fontsize=fuente, color="#ffffff")
    else:
        ax.annotate(f"{valor:.1f}", (centro, y), textcoords="offset points",
                    xytext=(0, 4), ha="center", va="bottom", fontsize=fuente, color="#1f2937", bbox=bbox)


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


def graficar_barras(summary: dict, img_dir: Path, plt) -> str | None:
    tasas = summary["tasas"]
    meta = summary["meta"]
    modelos = [m for m in tasas if tasas[m]["skill"]["media_pct"] is not None or tasas[m]["sin_skill"]["media_pct"] is not None]
    if not modelos:
        return None
    etiquetas = [meta["modelos"].get(m, {}).get("etiqueta", m).split(" (")[0] for m in modelos]
    vals_skill = [tasas[m]["skill"]["media_pct"] or 0 for m in modelos]
    vals_sin = [tasas[m]["sin_skill"]["media_pct"] or 0 for m in modelos]
    reps = [meta["modelos"].get(m, {}).get("repeticiones") or 0 for m in modelos]
    hay_error = any(r > 1 for r in reps)
    err_skill = [tasas[m]["skill"]["sd_pct"] if r > 1 else 0 for m, r in zip(modelos, reps)]
    err_sin = [tasas[m]["sin_skill"]["sd_pct"] if r > 1 else 0 for m, r in zip(modelos, reps)]

    mejoras = [m for m in modelos if tasas[m]["mejora_puntos"] is not None]
    if len(modelos) == 1 and mejoras:
        mejora = tasas[modelos[0]]["mejora_puntos"]
        titulo = (f"{etiquetas[0]}: {mejora:+.1f} pp con la skill "
                  f"({vals_skill[0]:.1f} % frente a {vals_sin[0]:.1f} %)")
    elif mejoras:
        mejora_media = sum(tasas[m]["mejora_puntos"] for m in mejoras) / len(mejoras)
        if mejora_media >= 0:
            titulo = f"La skill sube el acierto en {len(mejoras)} de {len(modelos)} modelos (+{mejora_media:.1f} pp de media)"
        else:
            titulo = f"Sin mejora media con la skill ({mejora_media:+.1f} pp)"
    else:
        titulo = "Tasa de aserciones superadas con y sin skill"

    fig, ax = plt.subplots(figsize=(6.8, 4.8), dpi=150)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    if len(modelos) == 1:
        barras = ax.bar(
            [0, 1], [vals_skill[0], vals_sin[0]], width=0.56,
            color=[PALETA["skill"], PALETA["sin_skill"]], zorder=3,
        )
        for barra, valor in zip(barras, (vals_skill[0], vals_sin[0])):
            anotar_barra(ax, barra, valor, fuente=10)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["con skill", "sin skill"], fontsize=10, color="#374151")
        ax.tick_params(axis="x", length=0)
        ax.set_xlim(-0.65, 1.65)
    else:
        x = list(range(len(modelos)))
        ancho = 0.36
        pos_skill = [i - ancho / 2 for i in x]
        pos_sin = [i + ancho / 2 for i in x]
        barras_skill = ax.bar(pos_skill, vals_skill, ancho, yerr=err_skill, capsize=4, color=PALETA["skill"],
                              label="con skill", error_kw={"ecolor": "#333333", "lw": 1}, zorder=3)
        barras_sin = ax.bar(pos_sin, vals_sin, ancho, yerr=err_sin, capsize=4, color=PALETA["sin_skill"],
                            label="sin skill", error_kw={"ecolor": "#333333", "lw": 1}, zorder=3)
        for barras, valores, errores in ((barras_skill, vals_skill, err_skill), (barras_sin, vals_sin, err_sin)):
            for barra, valor, error in zip(barras, valores, errores):
                anotar_barra(ax, barra, valor, fuente=8, error=error or 0.0)
        ax.set_xticks(x)
        ax.set_xticklabels(etiquetas, fontsize=9)

    ax.set_ylabel("% de aserciones superadas", fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_title(titulo, fontsize=10.5, color="#111827", loc="left", pad=10)
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=8)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)

    pie = nota_pie_grafica(summary)
    if hay_error:
        pie += ("\nBarras de error: ±1 desviación típica entre ejecuciones; "
                "solo en modelos con más de una repetición")
    else:
        pie += ". Sin barras de error (1 repetición)"
    fig.text(0.5, 0.025, pie, ha="center", fontsize=7, color="#4b5563", linespacing=1.5)
    fig.subplots_adjust(left=0.10, right=0.98, top=0.88, bottom=0.20)
    ruta = img_dir / "bench-aciertos.png"
    fig.savefig(ruta, facecolor=fig.get_facecolor())
    plt.close(fig)
    return str(ruta.relative_to(REPO)) if ruta.is_relative_to(REPO) else str(ruta)


def _luminancia(color) -> float:
    """Luminancia relativa (WCAG) de un color RGBA."""
    def canal(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (canal(c) for c in color[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def graficar_mapa_calor(summary: dict, img_dir: Path, plt) -> str | None:
    filas = sorted({int(e) for modelo in summary["por_eval"].values() for cond in modelo.values() for e in cond})
    columnas = []
    for modelo in summary["por_eval"]:
        for condicion in ("skill", "sin_skill"):
            columnas.append((modelo, condicion))
    if not filas or not columnas:
        return None
    etiquetas_filas = [f"Eval {e}" for e in filas]
    etiquetas_columnas = [
        f"{ETIQUETAS_HEATMAP.get(m, summary['meta']['modelos'].get(m, {}).get('etiqueta', m))}\n{ETIQUETAS_CORTAS[c]}"
        for m, c in columnas
    ]
    datos = []
    for eval_id in filas:
        fila = []
        for modelo, condicion in columnas:
            valor = summary["por_eval"].get(modelo, {}).get(condicion, {}).get(str(eval_id))
            fila.append(float("nan") if valor is None else valor)
        datos.append(fila)

    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap, Normalize

    matriz = np.array(datos, dtype=float)
    enmascarada = np.ma.masked_invalid(matriz)

    cmap = LinearSegmentedColormap.from_list("bench", ["#eef4f7", "#0f4c5c"])
    cmap.set_bad("#f0f0f0")
    norm = Normalize(vmin=0, vmax=100)
    fig, ax = plt.subplots(figsize=(7.6, 5.2), dpi=150)
    fig.patch.set_facecolor("#ffffff")
    imagen = ax.imshow(enmascarada, cmap=cmap, vmin=0, vmax=100, aspect="auto")
    for i in range(len(filas)):
        for j in range(len(columnas)):
            valor = matriz[i, j]
            texto = "—" if math.isnan(valor) else f"{valor:.0f}"
            if math.isnan(valor):
                color = "#6b7280"
            else:
                color = "#ffffff" if _luminancia(cmap(norm(valor))) < 0.2 else "#1f2937"
            ax.text(j, i, texto, ha="center", va="center", fontsize=8.5, color=color)
    ax.set_xticks(range(len(columnas)))
    ax.set_xticklabels(etiquetas_columnas, fontsize=8)
    ax.set_yticks(range(len(filas)))
    ax.set_yticklabels(etiquetas_filas, fontsize=8)
    ax.set_xlabel("Modelo y condición", fontsize=9)
    ax.set_title("% de aserciones superadas por eval, modelo y condición", fontsize=10.5, color="#111827", loc="left", pad=10)
    barra = fig.colorbar(imagen, ax=ax, fraction=0.035, pad=0.02)
    barra.set_label("% superadas", fontsize=8)
    barra.ax.tick_params(labelsize=8)
    fig.text(0.5, 0.015, nota_pie_grafica(summary), ha="center", fontsize=7, color="#4b5563")
    fig.subplots_adjust(left=0.10, right=0.90, top=0.90, bottom=0.14)
    ruta = img_dir / "bench-mapa-calor.png"
    fig.savefig(ruta, facecolor=fig.get_facecolor())
    plt.close(fig)
    return str(ruta.relative_to(REPO)) if ruta.is_relative_to(REPO) else str(ruta)


def graficar_coste(summary: dict, img_dir: Path, plt) -> str | None:
    puntos = []
    for modelo, condiciones in summary["costes"]["por_modelo_condicion"].items():
        tasa_skill = summary["tasas"].get(modelo, {}).get("skill", {}).get("media_pct")
        tasa_sin = summary["tasas"].get(modelo, {}).get("sin_skill", {}).get("media_pct")
        for condicion, bloque in condiciones.items():
            coste = bloque.get("coste_medio_usd")
            valor = tasa_skill if condicion == "skill" else tasa_sin
            if coste is None or valor is None:
                continue
            puntos.append((modelo, condicion, coste, valor))
    if len(puntos) < 3:
        return None
    puntos.sort(key=lambda p: p[2])
    min_x, max_x = puntos[0][2], puntos[-1][2]
    if max_x <= 0 or (max_x - min_x) < 0.15 * max_x:
        return None
    if len({round(p[3]) for p in puntos}) < 3:
        return None
    margen = max((max_x - min_x) * 0.08, 1e-6)
    fig, ax = plt.subplots(figsize=(6.8, 4.4), dpi=150)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")
    colocados: list[float] = []
    for modelo, condicion, coste, valor in puntos:
        color = COLORES_MODELO.get(modelo, "#555555")
        marcador = "o" if condicion == "skill" else "s"
        ax.scatter(coste, valor, s=60, color=color, marker=marcador, edgecolors="#ffffff", linewidths=0.6, zorder=3)
        etiqueta = f"{summary['meta']['modelos'].get(modelo, {}).get('etiqueta', modelo).split(' (')[0]} · {ETIQUETAS_CORTAS[condicion]}"
        rango = sum(1 for v in colocados if abs(v - valor) < 4)
        colocados.append(valor)
        if coste <= min_x + margen:
            dx, dy = (8, 6 - 13 * rango)
        elif coste >= max_x - margen:
            dx, dy = (-8, 6 - 13 * rango)
        else:
            dx, dy = ((8, 6 - 13 * rango) if rango == 0 else (-8, 6 - 13 * rango))
        ax.annotate(etiqueta, (coste, valor), textcoords="offset points", xytext=(dx, dy),
                    ha="left" if dx > 0 else "right", fontsize=7, color="#333333",
                    bbox={"boxstyle": "round,pad=0.12", "fc": "#ffffff", "ec": "none", "alpha": 0.75})
    ax.set_xlabel("Coste medio por respuesta (USD)")
    ax.set_ylabel("% de aserciones superadas")
    ax.set_ylim(0, 100)
    ax.set_title("Acierto frente a coste por respuesta", fontsize=11, color="#222222")
    ax.grid(color="#e5e5e5", linewidth=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.text(0.5, -0.2, "Círculo: con skill; cuadrado: sin skill.", transform=ax.transAxes, ha="center",
            fontsize=7, color="#666666")
    fig.text(0.5, 0.02, nota_pie_grafica(summary), ha="center", fontsize=7, color="#4b5563")
    fig.subplots_adjust(left=0.12, right=0.97, top=0.90, bottom=0.22)
    ruta = img_dir / "bench-coste.png"
    fig.savefig(ruta, facecolor=fig.get_facecolor())
    plt.close(fig)
    return str(ruta.relative_to(REPO)) if ruta.is_relative_to(REPO) else str(ruta)


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
            for funcion in (graficar_barras, graficar_mapa_calor, graficar_coste):
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
