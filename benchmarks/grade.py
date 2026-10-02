#!/usr/bin/env python3
"""Corrector automático de las ejecuciones de los benchmarks de normativa-uvigo-eeae.

Para cada ejecución sin nota construye un prompt de juez anónimo (sin modelo ni
condición), con la pregunta, las aserciones, el texto de los artículos citados
en `fuente` y la respuesta. El juez es Claude Opus 5.5 y devuelve por aserción
un resultado pass/fail con cita literal. Las notas se guardan en:

    results/<AAAA-MM-DD>/notas/<modelo>/<condicion>/<eval>-r<n>.json

Solo usa la biblioteca estándar de Python 3. Ver benchmarks/README.md.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import random
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True  # evita crear benchmarks/__pycache__ dentro del repo

import run

REPO = Path(__file__).resolve().parent.parent
DIR_SKILL = REPO / "skills" / "normativa-uvigo-eeae"
RUTA_BUSCAR = DIR_SKILL / "scripts" / "buscar.py"
TMP_BASE = Path(tempfile.gettempdir()) / "uvigo-plan"
DIR_JUEZ = TMP_BASE / "juez"

JUEZ_POR_DEFECTO = "claude-opus-5-5"
TIMEOUT_JUEZ = 600

ESQUEMA = """{
  "assertions": [
    {"indice": 0, "resultado": "pass" | "fail", "cita": "fragmento literal de la respuesta evaluada"}
  ],
  "comentario": "una o dos frases"
}"""


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------


def cargar_evals() -> dict:
    return run.cargar_evals()


def cargar_ejecuciones(results_dir: Path) -> list[tuple[Path, dict]]:
    ejecuciones = []
    for ruta in sorted((results_dir / "runs").glob("*/*/*.json")):
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        ejecuciones.append((ruta, datos))
    return ejecuciones


# ---------------------------------------------------------------------------
# Textos normativos citados (cacheados por eval)
# ---------------------------------------------------------------------------


def leer_fuente(fuente: str) -> str:
    """Extrae con buscar.py el texto de una fuente 'id art. n' o 'id'."""
    partes = fuente.split(" art. ")
    identificador = partes[0].strip()
    articulo = partes[1].strip() if len(partes) > 1 else None
    comando = [sys.executable, str(RUTA_BUSCAR), "--ver", identificador]
    if articulo:
        comando += ["--art", articulo]
    try:
        resultado = subprocess.run(
            comando,
            cwd=str(REPO),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
        )
    except subprocess.TimeoutExpired:
        return f"[Texto no disponible: buscar.py agotó el tiempo para {fuente}]"
    if resultado.returncode == 0 and resultado.stdout.strip():
        return resultado.stdout.strip()
    detalle = (resultado.stderr or "").strip()[:200]
    return f"[Texto no disponible para {fuente}: {detalle or 'sin salida'}]"


def obtener_textos_fuentes(evals: list[dict], results_dir: Path) -> dict:
    """Devuelve {eval_id: {fuente: texto}} y lo cachea en results_dir/corpus/."""
    ruta_cache = results_dir / "corpus" / "fuentes.json"
    cache: dict = {}
    if ruta_cache.exists():
        try:
            cache = json.loads(ruta_cache.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            cache = {}
    cambiado = False
    for ev in evals:
        clave = str(ev["id"])
        if clave in cache:
            continue
        mapa: dict[str, str] = {}
        for asercion in ev.get("assertions") or []:
            for fuente in asercion.get("fuente") or []:
                if fuente not in mapa:
                    mapa[fuente] = leer_fuente(fuente)
        cache[clave] = mapa
        cambiado = True
    if cambiado:
        ruta_cache.parent.mkdir(parents=True, exist_ok=True)
        ruta_cache.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return cache


# ---------------------------------------------------------------------------
# Prompt del juez
# ---------------------------------------------------------------------------


def construir_prompt_juez(ev: dict, respuesta: str, textos: dict[str, str]) -> str:
    vistos: set[str] = set()
    bloques = []
    for asercion in ev.get("assertions") or []:
        for fuente in asercion.get("fuente") or []:
            if fuente in vistos:
                continue
            vistos.add(fuente)
            bloques.append(f"### {fuente}\n{textos.get(fuente, '[Texto no disponible]')}")
    listado = "\n".join(
        f"{i}. {a['texto']}" for i, a in enumerate(ev.get("assertions") or [])
    )
    return f"""Eres un corrector objetivo de respuestas sobre normativa universitaria. No sabes qué modelo ha respondido: evalúa solo el contenido de la respuesta.

PREGUNTA PLANTEADA:
{ev['prompt']}

RESPUESTA DE REFERENCIA (orientativa, puede estar incompleta):
{ev.get('expected_output', '')}

TEXTOS NORMATIVOS CITADOS (úsalos para comprobar cifras, plazos y atribuciones; no dependas de tu memoria):
{chr(10).join(bloques) if bloques else '[Sin textos citados]'}

ASERCIONES A EVALUAR (cada una se refiere a la respuesta evaluada):
{listado}

RESPUESTA EVALUADA:
\"\"\"
{respuesta}
\"\"\"

Instrucciones:
- Para cada aserción decide "pass" (la respuesta la cumple de forma clara) o "fail" (no la cumple, la contradice o no es verificable en la respuesta).
- En "cita" copia un fragmento LITERAL de la respuesta evaluada que justifique el resultado. No puede estar vacía. Si el resultado es "fail" porque la respuesta omite algo, cita el fragmento más cercano que demuestre la omisión, o la frase completa si la respuesta no menciona nada relevante.
- "comentario": una o dos frases de valoración global.
- Devuelve SOLO un objeto JSON válido, sin texto adicional ni bloques de código, con este esquema exacto:
{ESQUEMA}"""


# ---------------------------------------------------------------------------
# Llamada al juez y validación
# ---------------------------------------------------------------------------


def llamar_juez(prompt: str, modelo: str) -> dict:
    DIR_JUEZ.mkdir(parents=True, exist_ok=True)
    comando = [
        "claude",
        "-p",
        "--model",
        modelo,
        "--output-format",
        "json",
        "--max-turns",
        "1",
        "--tools",
        "",
        "--setting-sources",
        "project",
        prompt,
    ]
    inicio = time.monotonic()
    resultado = subprocess.run(
        comando,
        cwd=str(DIR_JUEZ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=TIMEOUT_JUEZ,
    )
    duracion = round(time.monotonic() - inicio, 2)
    if resultado.returncode != 0:
        raise RuntimeError(f"claude falló (exit {resultado.returncode}): {(resultado.stderr or '').strip()[:300]}")
    datos = json.loads(resultado.stdout)
    error = f"{datos.get('subtype')}: {str(datos.get('result'))[:300]}" if datos.get("is_error") else None
    return {
        "texto": datos.get("result") or "",
        "tokens": datos.get("usage") or {},
        "coste_usd": datos.get("total_cost_usd"),
        "duracion_s": duracion,
        "error": error,
    }


def extraer_json(texto: str) -> dict:
    limpio = texto.strip()
    limpio = re.sub(r"^```(?:json)?\s*", "", limpio)
    limpio = re.sub(r"\s*```$", "", limpio)
    try:
        return json.loads(limpio)
    except json.JSONDecodeError:
        coincidencia = re.search(r"\{.*\}", limpio, re.DOTALL)
        if not coincidencia:
            raise
        return json.loads(coincidencia.group(0))


def validar_nota(nota, num_aserciones: int) -> tuple[bool, str]:
    """Valida el esquema y normaliza citas vacías a fail. Devuelve (válido, motivo)."""
    if not isinstance(nota, dict):
        return False, "la raíz no es un objeto"
    aserciones = nota.get("assertions")
    if not isinstance(aserciones, list) or len(aserciones) != num_aserciones:
        return False, f"se esperaban {num_aserciones} aserciones"
    indices = set()
    for asercion in aserciones:
        if not isinstance(asercion, dict):
            return False, "aserción no es objeto"
        indice = asercion.get("indice")
        if not isinstance(indice, int):
            return False, "índice no entero"
        if asercion.get("resultado") not in ("pass", "fail"):
            return False, f"resultado inválido en índice {indice}"
        if indice in indices:
            return False, f"índice repetido: {indice}"
        indices.add(indice)
        if not isinstance(asercion.get("cita"), str):
            return False, f"cita no textual en índice {indice}"
    if indices != set(range(num_aserciones)):
        return False, "faltan índices"
    if not isinstance(nota.get("comentario"), str):
        return False, "comentario ausente"
    return True, ""


def normalizar_citas(nota: dict) -> dict:
    """Una cita vacía incumple el esquema: se cuenta como fail y se documenta."""
    for asercion in nota["assertions"]:
        if not asercion["cita"].strip():
            asercion["resultado"] = "fail"
            asercion["cita_vacia"] = True
    return nota


def corregir_una(
    ev: dict,
    respuesta: str,
    textos: dict[str, str],
    modelo_juez: str,
) -> dict:
    prompt = construir_prompt_juez(ev, respuesta, textos)
    num_aserciones = len(ev.get("assertions") or [])
    inicio = time.monotonic()
    registro = {"prompt_juez": prompt, "juez": modelo_juez}
    ultimo_error = None
    for intento in (1, 2):
        try:
            salida = llamar_juez(prompt, modelo_juez)
        except Exception as exc:  # noqa: BLE001 - se guarda como error de corrección
            ultimo_error = f"fallo al invocar al juez: {exc}"
            continue
        registro.update(
            {
                "tokens_juez": salida["tokens"],
                "coste_usd_juez": salida["coste_usd"],
                "duracion_juez_s": salida["duracion_s"],
            }
        )
        if salida.get("error"):
            ultimo_error = salida["error"]
            continue
        try:
            nota = extraer_json(salida["texto"])
        except (json.JSONDecodeError, ValueError) as exc:
            ultimo_error = f"JSON del juez no parseable (intento {intento}): {exc}"
            prompt = prompt + "\n\nLa respuesta anterior no era JSON válido. Devuelve únicamente el objeto JSON del esquema."
            continue
        valido, motivo = validar_nota(nota, num_aserciones)
        if not valido:
            ultimo_error = f"JSON fuera de esquema (intento {intento}): {motivo}"
            prompt = prompt + "\n\nLa respuesta anterior no cumplía el esquema. Devuelve únicamente el objeto JSON del esquema, con todas las aserciones y una cita literal no vacía en cada una."
            continue
        registro["resultado"] = normalizar_citas(nota)
        registro["error"] = None
        registro["duracion_s"] = round(time.monotonic() - inicio, 2)
        return registro
    registro["resultado"] = None
    registro["error"] = ultimo_error or "corrección fallida"
    registro["duracion_s"] = round(time.monotonic() - inicio, 2)
    return registro


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parsear_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Corrige con Claude Opus las ejecuciones de los benchmarks (juez anónimo).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--results-dir", default="", help="Carpeta de resultados de run.py. Por defecto, benchmarks/results/<AAAA-MM-DD>.")
    p.add_argument("--evals", default="", help="Ids de eval separados por coma. Por defecto, todos.")
    p.add_argument("--jobs", type=int, default=4, help="Número de correcciones en paralelo.")
    p.add_argument("--model", default=JUEZ_POR_DEFECTO, help="Modelo juez.")
    p.add_argument("--force", action="store_true", help="Vuelve a corregir aunque la nota ya exista.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parsear_args(argv)

    if args.results_dir:
        results_dir = Path(args.results_dir).expanduser()
        if not results_dir.is_absolute():
            results_dir = (Path.cwd() / results_dir).resolve()
    else:
        results_dir = REPO / "benchmarks" / "results" / run.fecha_hoy()

    datos = cargar_evals()
    evals = {ev["id"]: ev for ev in datos["evals"]}
    if args.evals:
        try:
            pedidos = [int(x) for x in args.evals.split(",") if x.strip() != ""]
        except ValueError:
            print(f"--evals espera ids enteros separados por coma, recibido: {args.evals}", file=sys.stderr)
            return 2
        desconocidos = [i for i in pedidos if i not in evals]
        if desconocidos:
            print(f"Eval ids desconocidos: {desconocidos}", file=sys.stderr)
            return 2
        evals = {i: evals[i] for i in pedidos}

    ejecuciones = cargar_ejecuciones(results_dir)
    if args.evals:
        ejecuciones = [(r, d) for r, d in ejecuciones if d.get("eval_id") in evals]
    if not ejecuciones:
        print(f"No hay ejecuciones en {results_dir / 'runs'}")
        return 1

    # Solo se extraen los textos de los evals presentes en las ejecuciones.
    ids_presentes = {d.get("eval_id") for _, d in ejecuciones}
    evals_presentes = {i: ev for i, ev in evals.items() if i in ids_presentes}
    textos = obtener_textos_fuentes(list(evals_presentes.values()), results_dir)

    tareas = []
    saltadas = 0
    no_corregibles = 0
    for ruta, datos_run in ejecuciones:
        eval_id = datos_run.get("eval_id")
        modelo = datos_run.get("modelo")
        condicion = datos_run.get("condicion")
        rep = datos_run.get("rep")
        if eval_id not in evals:
            continue
        if datos_run.get("error") or datos_run.get("exit_code") != 0:
            no_corregibles += 1
            continue
        ruta_nota = run.ruta_nota(results_dir, modelo, condicion, eval_id, rep)
        if ruta_nota.exists() and not args.force:
            try:
                nota_previa = json.loads(ruta_nota.read_text(encoding="utf-8"))
                if nota_previa.get("resultado") and not nota_previa.get("error"):
                    saltadas += 1
                    continue
            except (json.JSONDecodeError, OSError):
                pass
        tareas.append((ruta_nota, datos_run, evals[eval_id]))

    random.shuffle(tareas)

    print(f"Resultados en: {results_dir}")
    print(
        f"Ejecuciones: {len(ejecuciones)} | saltadas (ya corregidas): {saltadas} | "
        f"no corregibles (fallo técnico): {no_corregibles} | a corregir: {len(tareas)}"
    )
    if not tareas:
        return 0

    fallos = 0
    coste_total = 0.0
    inicio = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as ex:
        futuros = {
            ex.submit(
                corregir_una,
                ev,
                datos_run.get("respuesta") or "",
                textos.get(str(datos_run.get("eval_id")), {}),
                args.model,
            ): (ruta_nota, datos_run)
            for ruta_nota, datos_run, ev in tareas
        }
        for futuro in concurrent.futures.as_completed(futuros):
            ruta_nota, datos_run = futuros[futuro]
            try:
                registro = futuro.result()
            except Exception as exc:  # noqa: BLE001
                registro = {
                    "prompt_juez": "",
                    "juez": args.model,
                    "resultado": None,
                    "error": f"excepción del corrector: {exc}",
                }
            nota = {
                "eval_id": datos_run.get("eval_id"),
                "grupo": datos_run.get("grupo"),
                "modelo": datos_run.get("modelo"),
                "condicion": datos_run.get("condicion"),
                "rep": datos_run.get("rep"),
                "juez": args.model,
                "resultado": registro.get("resultado"),
                "prompt_juez": registro.get("prompt_juez", ""),
                "tokens_juez": registro.get("tokens_juez"),
                "coste_usd_juez": registro.get("coste_usd_juez"),
                "duracion_juez_s": registro.get("duracion_juez_s"),
                "duracion_s": registro.get("duracion_s"),
                "contaminada": datos_run.get("contaminada", False),
                "skill_usada": datos_run.get("skill_usada", False),
                "error": registro.get("error"),
                "timestamp": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            }
            ruta_nota.parent.mkdir(parents=True, exist_ok=True)
            ruta_nota.write_text(json.dumps(nota, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if nota["error"]:
                fallos += 1
            if isinstance(nota.get("coste_usd_juez"), (int, float)):
                coste_total += nota["coste_usd_juez"]
            aprobadas = ""
            if nota.get("resultado"):
                resultados = [a["resultado"] for a in nota["resultado"]["assertions"]]
                aprobadas = f"{resultados.count('pass')}/{len(resultados)}"
            print(
                f"[{'FALLO' if nota['error'] else 'OK'}] {nota['modelo']} {nota['condicion']} "
                f"{nota['eval_id']}-r{nota['rep']} {aprobadas} "
                f"({nota.get('duracion_s')} s, {nota.get('coste_usd_juez')} USD)"
                + (f" error={nota['error'][:140]}" if nota["error"] else ""),
                flush=True,
            )
    print(
        f"Terminado en {round(time.monotonic() - inicio, 1)} s. "
        f"Correcciones fallidas: {fallos}. Coste del juez: {round(coste_total, 4)} USD"
    )
    return 0 if fallos == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
