#!/usr/bin/env python3
"""Arnés de ejecución de los benchmarks de normativa-uvigo-eeae.

Ejecuta la matriz modelos x condicion {skill, sin_skill} x evals x repeticiones.
Cada ejecución se lanza en un workspace temporal y aislado (sin acceso a las
skills de usuario de la máquina) y deja un JSON con la respuesta, las
herramientas usadas, los tokens, el coste y la duración en:

    results/<AAAA-MM-DD>/runs/<modelo>/<condicion>/<eval>-r<n>.json

Solo usa la biblioteca estándar de Python 3. Ver benchmarks/README.md.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DIR_SKILL = REPO / "skills" / "normativa-uvigo-eeae"
RUTA_EVALS = REPO / "benchmarks" / "evals.json"
# Base propia y exclusiva para los workspaces del benchmark: fuera de /tmp/uvigo-plan
# (los modelos exploran el directorio padre de su workspace y no deben encontrar
# copias de la skill ni artefactos de pruebas anteriores).
TMP_BASE = Path(tempfile.gettempdir()) / "uvigo-bench"

HERRAMIENTAS_CLAUDE = "Bash Read Grep Glob WebFetch WebSearch Skill"

# Ajustes con los que Claude Code no carga ninguna skill que no sea la del repo:
#   - disableBundledSkills: quita las skills incluidas en Claude Code.
#   - enabledPlugins: desactiva los plugins internos que exponen skills.
#   - skillOverrides: oculta las dos skills internas restantes (design, doctor).
# En la condición skill, la única skill visible pasa a ser normativa-uvigo-eeae.
AJUSTES_CLAUDE = {
    "disableBundledSkills": True,
    "enabledPlugins": {
        "cc-plugin-plugin-authoring@builtin": False,
        "cc-plugin-agents-md@builtin": False,
        "cc-plugin-telemetry@builtin": False,
    },
    "skillOverrides": {"design": "off", "doctor": "off"},
}

MODELOS = {
    "deepseek": {
        "cli": "opencode",
        "modelo_cli": "opencode-go/deepseek-v4.1-flash",
        # Sin "variant": OpenCode no envía reasoningEffort y el proveedor usa su
        # esfuerzo por defecto (variantes disponibles: low, high, max).
        "reps": 3,
        "etiqueta": "DeepSeek V4.1 Flash (OpenCode, effort por defecto)",
    },
    "sonnet": {
        "cli": "claude",
        "modelo_cli": "claude-sonnet-5-5",
        "reps": 1,
        "etiqueta": "Claude Sonnet 5.5 (Claude Code, effort por defecto)",
    },
    "opus": {
        "cli": "claude",
        "modelo_cli": "claude-opus-5-5",
        "effort": "medium",
        "reps": 1,
        "etiqueta": "Claude Opus 5.5 (Claude Code, effort medium)",
    },
}

CONDICIONES = ["skill", "sin_skill"]

# Patrones que delatan que una ejecución sin_skill vio o usó una skill.
PATRONES_SKILL = [
    "normativa-uvigo-eeae",
    ".claude/skills",
    ".opencode/skills",
    ".agents/skills",
    "SKILL.md",
]

PROMPT_AISLAMIENTO = (
    "Lista las skills disponibles (solo los nombres, uno por linea). "
    "Si no hay ninguna, escribe exactamente NINGUNA. No uses ninguna skill."
)


# ---------------------------------------------------------------------------
# Utilidades de rutas
# ---------------------------------------------------------------------------


def cargar_evals() -> dict:
    """Devuelve el contenido de benchmarks/evals.json."""
    return json.loads(RUTA_EVALS.read_text(encoding="utf-8"))


def fecha_hoy() -> str:
    return dt.date.today().isoformat()


def ruta_resultado(results_dir: Path, modelo: str, condicion: str, eval_id: int, rep: int) -> Path:
    return results_dir / "runs" / modelo / condicion / f"{eval_id}-r{rep}.json"


def ruta_nota(results_dir: Path, modelo: str, condicion: str, eval_id: int, rep: int) -> Path:
    return results_dir / "notas" / modelo / condicion / f"{eval_id}-r{rep}.json"


def ruta_auth_opencode() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "opencode" / "auth.json"


def ruta_credenciales_claude() -> Path:
    return Path.home() / ".claude" / ".credentials.json"


# ---------------------------------------------------------------------------
# Workspace aislado por ejecución
# ---------------------------------------------------------------------------


def config_opencode() -> dict:
    """Permisos no interactivos equivalentes a las herramientas de Claude."""
    return {
        "$schema": "https://opencode.ai/config.json",
        "permission": {
            "external_directory": "deny",
            "edit": "deny",
            "question": "deny",
            "skill": {"*": "allow", "customize-opencode": "deny"},
            "webfetch": "allow",
            "websearch": "allow",
            "bash": "allow",
        },
    }


def preparar_entorno(modelo: str, condicion: str) -> tuple[Path, Path, dict]:
    """Crea un workspace temporal limpio y devuelve (base, workspace, entorno).

    El workspace cuelga de un HOME temporal para que las búsquedas de skills
    hacia directorios superiores no puedan salir del entorno. En la condición
    skill se copia la skill del repo a la ruta que lee cada CLI; en sin_skill
    no se copia nada.
    """
    base = TMP_BASE / "runs" / uuid.uuid4().hex
    home = base / "home"
    ws = home / "workspace"
    ws.mkdir(parents=True)
    env = dict(os.environ)
    # subprocess no actualiza PWD; OpenCode lo usa para localizar el proyecto.
    env["PWD"] = str(ws)
    info = MODELOS[modelo]

    if info["cli"] == "claude":
        cfg = base / "claude-config"
        cfg.mkdir()
        cred = ruta_credenciales_claude()
        if cred.exists():
            shutil.copy2(cred, cfg / ".credentials.json")
        env["CLAUDE_CONFIG_DIR"] = str(cfg)
        env["HOME"] = str(home)
        if condicion == "skill":
            destino = ws / ".claude" / "skills" / DIR_SKILL.name
            destino.parent.mkdir(parents=True)
            shutil.copytree(DIR_SKILL, destino)
    else:
        cfg = base / "xdg-config"
        data = base / "xdg-data"
        cfg.mkdir(parents=True)
        (data / "opencode").mkdir(parents=True)
        auth = ruta_auth_opencode()
        if auth.exists():
            shutil.copy2(auth, data / "opencode" / "auth.json")
        env["HOME"] = str(home)
        env["XDG_CONFIG_HOME"] = str(cfg)
        env["XDG_DATA_HOME"] = str(data)
        (ws / "opencode.json").write_text(
            json.dumps(config_opencode(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        if condicion == "skill":
            destino = ws / ".opencode" / "skills" / DIR_SKILL.name
            destino.parent.mkdir(parents=True)
            shutil.copytree(DIR_SKILL, destino)

    return base, ws, env


def construir_comando(modelo: str, prompt: str, max_turns: int) -> list[str]:
    info = MODELOS[modelo]
    if info["cli"] == "claude":
        esfuerzo = ["--effort", info["effort"]] if info.get("effort") else []
        return [
            "claude",
            "-p",
            "--model",
            info["modelo_cli"],
            *esfuerzo,
            "--output-format",
            "stream-json",
            "--verbose",
            "--allowedTools",
            HERRAMIENTAS_CLAUDE,
            "--max-turns",
            str(max_turns),
            "--setting-sources",
            "project",
            "--settings",
            json.dumps(AJUSTES_CLAUDE, ensure_ascii=False),
            prompt,
        ]
    variante = ["--variant", info["variant"]] if info.get("variant") else []
    return [
        "opencode",
        "run",
        "-m",
        info["modelo_cli"],
        *variante,
        "--format",
        "json",
        "--auto",
        prompt,
    ]


# ---------------------------------------------------------------------------
# Parseo de salidas
# ---------------------------------------------------------------------------


def _truncar(valor, limite: int = 300) -> str:
    if isinstance(valor, str):
        texto = valor
    else:
        try:
            texto = json.dumps(valor, ensure_ascii=False)
        except (TypeError, ValueError):
            texto = str(valor)
    return texto[:limite]


def nombres_herramientas(tool_uses: list[dict]) -> list[str]:
    vistos: list[str] = []
    for tu in tool_uses:
        nombre = tu.get("herramienta")
        if nombre and nombre not in vistos:
            vistos.append(nombre)
    return vistos


def parsear_salida_claude(stdout: str) -> dict:
    tool_uses: list[dict] = []
    resultados: list[str] = []
    skills_visibles = None
    resultado = None
    for linea in stdout.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        try:
            ev = json.loads(linea)
        except json.JSONDecodeError:
            continue
        tipo = ev.get("type")
        if tipo == "system" and ev.get("subtype") == "init":
            skills_visibles = ev.get("skills") or []
        elif tipo == "assistant":
            for c in (ev.get("message") or {}).get("content") or []:
                if isinstance(c, dict) and c.get("type") == "tool_use":
                    tool_uses.append({"herramienta": c.get("name"), "entrada": c.get("input")})
        elif tipo == "user":
            for c in (ev.get("message") or {}).get("content") or []:
                if isinstance(c, dict) and c.get("type") == "tool_result":
                    resultados.append(_truncar(c.get("content"), 2000))
        elif tipo == "result":
            resultado = ev

    tokens: dict = {}
    coste = None
    respuesta = ""
    error = None
    num_turnos = None
    if resultado is not None:
        uso = resultado.get("usage") or {}
        tokens = {
            "input": uso.get("input_tokens"),
            "output": uso.get("output_tokens"),
            "cache_creation": uso.get("cache_creation_input_tokens"),
            "cache_read": uso.get("cache_read_input_tokens"),
        }
        tokens["total"] = sum(v for v in tokens.values() if isinstance(v, (int, float)))
        coste = resultado.get("total_cost_usd")
        respuesta = resultado.get("result") or ""
        num_turnos = resultado.get("num_turns")
        if resultado.get("is_error"):
            error = f"{resultado.get('subtype')}: {_truncar(respuesta, 300)}"
    return {
        "respuesta": respuesta,
        "herramientas": nombres_herramientas(tool_uses),
        "tokens": tokens,
        "coste_usd": coste,
        "num_turnos": num_turnos,
        "skills_visibles": skills_visibles,
        "tool_uses": tool_uses,
        "resultados_herramientas": resultados,
        "error": error,
    }


def parsear_salida_opencode(stdout: str) -> dict:
    tool_uses: list[dict] = []
    resultados: list[str] = []
    textos: list[str] = []
    tokens = {
        "input": 0,
        "output": 0,
        "reasoning": 0,
        "cache_read": 0,
        "cache_write": 0,
        "total": 0,
    }
    coste = 0.0
    error = None
    for linea in stdout.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        try:
            ev = json.loads(linea)
        except json.JSONDecodeError:
            continue
        tipo = ev.get("type")
        if tipo == "text":
            part = ev.get("part") or {}
            texto = part.get("text")
            if texto:
                textos.append(texto)
        elif tipo == "tool_use":
            part = ev.get("part") or {}
            estado = part.get("state") or {}
            tool_uses.append({"herramienta": part.get("tool"), "entrada": estado.get("input")})
            if estado.get("output"):
                resultados.append(_truncar(estado.get("output"), 2000))
        elif tipo == "step_finish":
            part = ev.get("part") or {}
            c = part.get("cost")
            if isinstance(c, (int, float)):
                coste += c
            tk = part.get("tokens") or {}
            tokens["input"] += tk.get("input") or 0
            tokens["output"] += tk.get("output") or 0
            tokens["reasoning"] += tk.get("reasoning") or 0
            cache = tk.get("cache") or {}
            tokens["cache_read"] += cache.get("read") or 0
            tokens["cache_write"] += cache.get("write") or 0
            tokens["total"] += tk.get("total") or 0
        elif tipo == "error":
            error = _truncar(ev.get("error"), 500)

    return {
        "respuesta": "\n".join(textos).strip(),
        "herramientas": nombres_herramientas(tool_uses),
        "tokens": tokens,
        "coste_usd": round(coste, 8) if coste else coste,
        "num_turnos": None,
        "skills_visibles": None,
        "tool_uses": tool_uses,
        "resultados_herramientas": resultados,
        "error": error,
    }


def parsear_salida(modelo: str, stdout: str) -> dict:
    if MODELOS[modelo]["cli"] == "claude":
        return parsear_salida_claude(stdout)
    return parsear_salida_opencode(stdout)


# ---------------------------------------------------------------------------
# Detección de contaminación y de uso real de la skill (reutilizable)
# ---------------------------------------------------------------------------


def construir_evidencia(parsed: dict) -> str:
    """Texto con las entradas y salidas de herramientas más las skills visibles."""
    partes: list[str] = []
    for tu in parsed.get("tool_uses") or []:
        partes.append(
            json.dumps(
                {"herramienta": tu.get("herramienta"), "entrada": tu.get("entrada")},
                ensure_ascii=False,
            )
        )
    partes.extend(parsed.get("resultados_herramientas") or [])
    if parsed.get("skills_visibles"):
        partes.append(json.dumps(parsed["skills_visibles"], ensure_ascii=False))
    return "\n".join(partes)


def detectar_contaminacion(condicion: str, parsed: dict) -> bool:
    """Marca una ejecución sin_skill que menciona rutas de skills o la skill."""
    if condicion != "sin_skill":
        return False
    evidencia = construir_evidencia(parsed) + "\n" + (parsed.get("respuesta") or "")
    return any(p in evidencia for p in PATRONES_SKILL)


def detectar_skill_usada(condicion: str, parsed: dict) -> bool:
    """Marca una ejecución skill que invoca o lee de verdad la skill del repo."""
    if condicion != "skill":
        return False
    for tu in parsed.get("tool_uses") or []:
        nombre = (tu.get("herramienta") or "").lower()
        entrada = json.dumps(tu.get("entrada"), ensure_ascii=False)
        if "normativa-uvigo-eeae" not in entrada:
            continue
        if nombre == "skill":
            return True
        if any(p in entrada for p in (".claude/skills", ".opencode/skills", ".agents/skills")):
            return True
    evidencia = construir_evidencia(parsed)
    return (
        ".claude/skills/normativa-uvigo-eeae" in evidencia
        or ".opencode/skills/normativa-uvigo-eeae" in evidencia
        or "normativa-uvigo-eeae/SKILL.md" in evidencia
    )


# ---------------------------------------------------------------------------
# Ejecución de una celda de la matriz
# ---------------------------------------------------------------------------


def _ejecutar_subproceso(comando: list[str], ws: Path, env: dict, timeout: int) -> tuple[str, str, int, str | None]:
    salida = ""
    err = ""
    exit_code: int | None = None
    error: str | None = None
    proc = subprocess.Popen(
        comando,
        cwd=str(ws),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        start_new_session=True,
    )
    try:
        salida, err = proc.communicate(timeout=timeout)
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            proc.kill()
        try:
            salida, err = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            pass
        exit_code = -9
        error = f"timeout de {timeout} s"
    return salida, err, exit_code, error


def ejecutar_una(
    modelo: str,
    condicion: str,
    eval_id: int,
    grupo: str,
    prompt: str,
    rep: int,
    args: argparse.Namespace,
) -> dict:
    """Ejecuta una celda y devuelve el registro que se guardará en JSON."""
    inicio = time.monotonic()
    base, ws, env = preparar_entorno(modelo, condicion)
    comando = construir_comando(modelo, prompt, args.max_turns)
    try:
        salida, err, exit_code, error = _ejecutar_subproceso(comando, ws, env, args.timeout)
    finally:
        if not args.keep_tmp:
            shutil.rmtree(base, ignore_errors=True)
    duracion = time.monotonic() - inicio

    parsed = parsear_salida(modelo, salida)
    if error is None and parsed.get("error"):
        error = parsed["error"]
    if error is None and exit_code not in (0, None):
        error = (err or "").strip()[-500:] or f"exit_code {exit_code}"

    contaminada = detectar_contaminacion(condicion, parsed)
    skill_usada = detectar_skill_usada(condicion, parsed)

    return {
        "eval_id": eval_id,
        "grupo": grupo,
        "modelo": modelo,
        "condicion": condicion,
        "rep": rep,
        "prompt": prompt,
        "respuesta": parsed.get("respuesta") or "",
        "herramientas": parsed.get("herramientas") or [],
        "tokens": parsed.get("tokens") or {},
        "coste_usd": parsed.get("coste_usd"),
        "duracion_s": round(duracion, 2),
        "exit_code": exit_code,
        "contaminada": contaminada,
        "skill_usada": skill_usada,
        "error": error,
        "timestamp": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "comando": comando,
        "transcripcion_resumen": {
            "skills_visibles": parsed.get("skills_visibles"),
            "num_turnos": parsed.get("num_turnos"),
            "tool_uses": [
                {
                    "herramienta": tu.get("herramienta"),
                    "entrada_resumen": _truncar(tu.get("entrada"), 300),
                }
                for tu in parsed.get("tool_uses") or []
            ],
            "stderr_tail": (err or "").strip()[-500:] or None,
        },
    }


def guardar_registro(ruta: Path, registro: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(registro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ejecucion_valida(ruta: Path) -> bool:
    if not ruta.exists():
        return False
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return datos.get("exit_code") == 0 and not datos.get("error")


# ---------------------------------------------------------------------------
# Prueba de aislamiento
# ---------------------------------------------------------------------------


def ejecutar_aislamiento(args: argparse.Namespace) -> int:
    """Ejecuta una pregunta barata en cada CLI y condición y deja evidencia."""
    ruta_log = Path(args.aislamiento_log) if args.aislamiento_log else TMP_BASE / "aislamiento.log"
    ruta_log.parent.mkdir(parents=True, exist_ok=True)
    casos = [
        ("sonnet", "sin_skill"),
        ("sonnet", "skill"),
        ("deepseek", "sin_skill"),
        ("deepseek", "skill"),
    ]
    lineas = [
        "Prueba de aislamiento de los benchmarks de normativa-uvigo-eeae",
        f"Fecha: {dt.datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"Pregunta: {PROMPT_AISLAMIENTO}",
        "",
    ]
    for i, (modelo, condicion) in enumerate(casos, 1):
        cli = MODELOS[modelo]["cli"]
        lineas.append(f"[{i}/4] modelo={modelo} cli={cli} condicion={condicion}")
        registro = ejecutar_una(
            modelo,
            condicion,
            0,
            "aislamiento",
            PROMPT_AISLAMIENTO,
            1,
            args,
        )
        lineas.append(f"  respuesta: {_truncar(registro['respuesta'], 500)!r}")
        lineas.append(f"  skills_visibles: {registro['transcripcion_resumen'].get('skills_visibles')}")
        lineas.append(f"  herramientas: {registro['herramientas']}")
        lineas.append(f"  contaminada: {registro['contaminada']} | skill_usada: {registro['skill_usada']}")
        lineas.append(f"  exit_code: {registro['exit_code']} | coste_usd: {registro['coste_usd']}")
        if registro.get("error"):
            lineas.append(f"  ERROR: {registro['error']}")
        if condicion == "sin_skill":
            veredicto = "AISLADO (no aparece ninguna skill)" if not registro["contaminada"] else "CONTAMINADO"
        else:
            menciona = "normativa-uvigo-eeae" in (registro["respuesta"] or "") or registro["skill_usada"]
            veredicto = "OK (aparece normativa-uvigo-eeae)" if menciona else "REVISAR (no aparece la skill)"
        lineas.append(f"  veredicto: {veredicto}")
        lineas.append("")
        ruta_evidencia = TMP_BASE / "aislamiento" / f"{cli}-{condicion}.json"
        guardar_registro(ruta_evidencia, registro)
    ruta_log.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"Evidencia de aislamiento en {ruta_log}")
    for linea in lineas:
        print(linea)
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parsear_reps(texto: str) -> dict:
    reps = {modelo: info["reps"] for modelo, info in MODELOS.items()}
    for trozo in texto.split(","):
        trozo = trozo.strip()
        if not trozo:
            continue
        if "=" not in trozo:
            raise argparse.ArgumentTypeError(f"--reps espera modelo=n, recibido: {trozo}")
        modelo, valor = trozo.split("=", 1)
        modelo = modelo.strip()
        if modelo not in MODELOS:
            raise argparse.ArgumentTypeError(f"modelo desconocido en --reps: {modelo}")
        try:
            reps[modelo] = int(valor)
        except ValueError:
            raise argparse.ArgumentTypeError(f"repeticiones no enteras en --reps: {trozo}")
        if reps[modelo] < 1:
            raise argparse.ArgumentTypeError(f"las repeticiones deben ser >= 1: {trozo}")
    return reps


def parsear_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Ejecuta los benchmarks de normativa-uvigo-eeae (modelos x con/sin skill x evals x reps).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--dry-run", action="store_true", help="Lista las ejecuciones previstas y termina sin ejecutar nada.")
    p.add_argument("--jobs", type=int, default=4, help="Número de ejecuciones en paralelo.")
    p.add_argument("--evals", default="", help="Ids de eval separados por coma (p. ej. '0,1'). Por defecto, todos.")
    p.add_argument("--models", default="deepseek,sonnet,opus", help="Modelos separados por coma (deepseek, sonnet, opus).")
    p.add_argument("--reps", type=parsear_reps, default="deepseek=3,sonnet=1,opus=1",
                   help="Repeticiones por modelo (p. ej. 'deepseek=3,sonnet=1,opus=1').")
    p.add_argument("--results-dir", default="", help="Carpeta de resultados. Por defecto, benchmarks/results/<AAAA-MM-DD>.")
    p.add_argument("--timeout", type=int, default=900, help="Segundos máximos por ejecución.")
    p.add_argument("--max-turns", type=int, default=40, help="Turnos máximos por ejecución en Claude.")
    p.add_argument("--keep-tmp", action="store_true", help="No borra los workspaces temporales (depuración).")
    p.add_argument("--isolation-check", action="store_true",
                   help="Ejecuta solo la prueba de aislamiento (4 ejecuciones baratas) y escribe el log.")
    p.add_argument("--aislamiento-log", default="", help="Ruta del log de la prueba de aislamiento.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parsear_args(argv)

    if args.isolation_check:
        return ejecutar_aislamiento(args)

    datos = cargar_evals()
    evals = datos["evals"]
    if args.evals:
        try:
            pedidos = [int(x) for x in args.evals.split(",") if x.strip() != ""]
        except ValueError:
            print(f"--evals espera ids enteros separados por coma, recibido: {args.evals}", file=sys.stderr)
            return 2
        por_id = {ev["id"]: ev for ev in evals}
        desconocidos = [i for i in pedidos if i not in por_id]
        if desconocidos:
            print(f"Eval ids desconocidos: {desconocidos}", file=sys.stderr)
            return 2
        evals = [por_id[i] for i in pedidos]

    modelos = [m.strip() for m in args.models.split(",") if m.strip()]
    for m in modelos:
        if m not in MODELOS:
            print(f"Modelo desconocido: {m}. Disponibles: {', '.join(MODELOS)}", file=sys.stderr)
            return 2

    reps = args.reps if isinstance(args.reps, dict) else parsear_reps(args.reps)

    if args.results_dir:
        results_dir = Path(args.results_dir).expanduser()
        if not results_dir.is_absolute():
            results_dir = (Path.cwd() / results_dir).resolve()
    else:
        results_dir = REPO / "benchmarks" / "results" / fecha_hoy()

    tareas = []
    for modelo in modelos:
        for condicion in CONDICIONES:
            for ev in evals:
                for rep in range(1, reps[modelo] + 1):
                    tareas.append((modelo, condicion, ev, rep))

    if args.dry_run:
        for modelo, condicion, ev, rep in tareas:
            print(f"{modelo} {condicion} {ev['id']}-r{rep}")
        print(f"Total: {len(tareas)} ejecuciones")
        return 0

    pendientes = []
    saltadas = 0
    for modelo, condicion, ev, rep in tareas:
        ruta = ruta_resultado(results_dir, modelo, condicion, ev["id"], rep)
        if ejecucion_valida(ruta):
            saltadas += 1
        else:
            pendientes.append((modelo, condicion, ev, rep))

    print(f"Resultados en: {results_dir}")
    print(f"Planificadas: {len(tareas)} | saltadas (ya completadas): {saltadas} | a ejecutar: {len(pendientes)}")
    if not pendientes:
        return 0

    fallos = 0
    inicio = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as ex:
        futuros = {
            ex.submit(ejecutar_una, modelo, condicion, ev["id"], ev["grupo"], ev["prompt"], rep, args): (
                modelo,
                condicion,
                ev,
                rep,
            )
            for modelo, condicion, ev, rep in pendientes
        }
        for futuro in concurrent.futures.as_completed(futuros):
            modelo, condicion, ev, rep = futuros[futuro]
            try:
                registro = futuro.result()
            except Exception as exc:  # noqa: BLE001 - se guarda como fallo técnico
                registro = {
                    "eval_id": ev["id"],
                    "grupo": ev["grupo"],
                    "modelo": modelo,
                    "condicion": condicion,
                    "rep": rep,
                    "prompt": ev["prompt"],
                    "respuesta": "",
                    "herramientas": [],
                    "tokens": {},
                    "coste_usd": None,
                    "duracion_s": None,
                    "exit_code": None,
                    "contaminada": False,
                    "skill_usada": False,
                    "error": f"excepción del arnés: {exc}",
                    "timestamp": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                    "comando": [],
                    "transcripcion_resumen": {},
                }
            ruta = ruta_resultado(results_dir, modelo, condicion, ev["id"], rep)
            guardar_registro(ruta, registro)
            estado = "OK" if ejecucion_valida(ruta) else "FALLO"
            if estado == "FALLO":
                fallos += 1
            extra = ""
            if registro.get("error"):
                extra = f" error={registro['error'][:120]}"
            print(
                f"[{estado}] {modelo} {condicion} {ev['id']}-r{rep} "
                f"({registro.get('duracion_s')} s, {registro.get('coste_usd')} USD){extra}",
                flush=True,
            )
    print(f"Terminado en {round(time.monotonic() - inicio, 1)} s. Fallos técnicos en esta pasada: {fallos}")
    print("Vuelve a lanzar run.py para reintentar los fallos (se saltan las ejecuciones válidas).")
    return 0 if fallos == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
