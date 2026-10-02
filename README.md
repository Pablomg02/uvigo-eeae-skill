# normativa-uvigo-eeae

Claude/agent skill for University of Vigo regulations — EEAE & doctoral school. Docs in Spanish.

[![Licencia MIT](https://img.shields.io/badge/licencia-MIT-blue.svg)](LICENSE)

> **¿Prisa?** Pásale este README a tu IA (Claude Code, Codex, OpenCode…) y dile *«instálame esta skill»*: aquí abajo tiene las instrucciones exactas, plataforma por plataforma.

## Qué es

Skill que responde dudas normativas del profesorado de la Escola de Enxeñaría Aeronáutica e do Espazo (EEAE) y de quien hace el doctorado en la Universidade de Vigo: exámenes, guías docentes, POD y dedicación, permisos, contratos, tesis, art. 83, incompatibilidades, protección de datos y régimen disciplinario. Trabaja sobre un **corpus local de 160 textos** (leyes estatales y gallegas, convenio del PDI laboral, normativa de la UVigo, la EEAE y la EIDO) con un buscador y un comprobador que contrasta la vigencia en directo con el portal de la UVigo, el BOE y las webs de la Escola y la EIDO. Responde en español y **cita artículo y fuente**; cuando no puede verificar algo, lo dice.

Pregunta de ejemplo: «Soy profesor asociado y un alumno me pide cambiar la fecha del examen porque se va de congreso. ¿Puedo?»

Formato de respuesta (recortado):

```
**Respuesta corta:** No / Depende de X — una frase.
**Fundamento**
- <Norma>, <rango y fecha>, art. X.Y: «cita literal breve». [enlace]
**Condiciones y excepciones:** plazos, requisitos, quién autoriza.
**Qué no he podido verificar:** (si aplica) huecos del corpus, norma de otro curso, tabla…
**Siguiente paso:** a quién preguntar o qué trámite hacer.
```

La versión para la app de Claude es el `.skill` de las [Releases](../../releases) (≈7 MB). El repositorio versiona solo los PDF imprescindibles (13 de 128); el resto se descarga bajo demanda cuando hace falta una tabla.

## Dónde funciona

| Plataforma | Estado |
|---|---|
| **Claude Code** (terminal, IDE, escritorio) | ✓ Probado: plugin desde marketplace y enlace manual en `~/.claude/skills/` |
| **Codex CLI** | ✓ Probado: `.agents/skills/` de proyecto y de usuario |
| **OpenCode** | ✓ Probado: `.opencode/skills/` y `~/.config/opencode/skills/`; también lee `~/.claude/skills/` |
| **claude.ai / app de Claude** | ✓ Subiendo el `.skill`; con ejecución de código y red para la comprobación en directo |
| **ChatGPT** | Limitado: solo planes de workspace con Skills; sin ellas, Proyecto/GPT con el ZIP como archivo y sin scripts |
| **Gemini CLI, Cursor, Copilot** | ✓ Por `.agents/skills/` (y `.claude/skills/`), según la documentación de cada uno |

## Instalación

**Claude Code**

```bash
claude plugin marketplace add Pablomg02/uvigo-eeae-skill
claude plugin install normativa-uvigo-eeae@uvigo-eeae-skill
```

Alternativa manual: clona el repo y enlaza `skills/normativa-uvigo-eeae` en `~/.claude/skills/normativa-uvigo-eeae`.

**Codex CLI**

```bash
git clone https://github.com/Pablomg02/uvigo-eeae-skill ~/uvigo-eeae-skill
mkdir -p ~/.agents/skills
ln -s ~/uvigo-eeae-skill/skills/normativa-uvigo-eeae ~/.agents/skills/normativa-uvigo-eeae
```

Dentro de un proyecto, usa `.agents/skills/` en su raíz. Codex también admite enlaces simbólicos.

**OpenCode**

```bash
git clone https://github.com/Pablomg02/uvigo-eeae-skill ~/uvigo-eeae-skill
mkdir -p ~/.config/opencode/skills
ln -s ~/uvigo-eeae-skill/skills/normativa-uvigo-eeae ~/.config/opencode/skills/normativa-uvigo-eeae
```

En un proyecto, `.opencode/skills/`, `.claude/skills/` o `.agents/skills/`.

**claude.ai / app de Claude**

Descarga `normativa-uvigo-eeae.skill` de la última Release y súbelo en **Customize → Skills → «Upload a skill»**. Activa «Code execution and file creation» y la salida a red con `secretaria.uvigo.gal`, `www.boe.es`, `aero.uvigo.es` y `eido.uvigo.gal`.

**ChatGPT**

Si tu plan (Business, Enterprise, Healthcare o Edu) tiene Skills: **Skills → Create → Upload from your computer**. Si no, adjunta el ZIP de la Release en un Proyecto y pega el contenido de `SKILL.md` como instrucciones (ver límites).

## Benchmarks

![Acierto de DeepSeek V4.1 Flash con y sin la skill](docs/img/bench-aciertos.png)

**DeepSeek V4.1 Flash** (vía OpenCode), 2 de octubre de 2026: 10 preguntas × 2 condiciones (con y sin skill) × 1 repetición por pregunta = **20 ejecuciones**, corregidas por el juez **Claude Opus 5.5**. Con la skill el acierto pasa de **58,3 % a 85,0 %** (**+26,7 puntos porcentuales**): por grupos, en las 6 preguntas de desarrollo sube de 55,6 % a 80,6 % y en las 4 nuevas —escritas sin mirar `SKILL.md`— de 62,5 % a 91,7 %. La skill se activó en el 100 % de las ejecuciones con skill; la salvedad es el eval 0, donde el baseline (83,3 %) superó a la skill (50,0 %) por fallos reales de esa respuesta, documentados en la auditoría del juez.

![Acierto por pregunta, con y sin skill](docs/img/bench-mapa-calor.png)

El arnés permite añadir Sonnet 5.5 y Opus 5.5 con `python3 benchmarks/run.py --models deepseek,sonnet,opus`, pero esta tanda se ejecutó solo con DeepSeek por coste. Metodología, aislamiento, coste real y limitaciones en [`benchmarks/README.md`](benchmarks/README.md).

## Alcance y adaptación

La skill es concreta de la UVigo, la EEAE y el doctorado (EIDO), pero su estructura —corpus con cabeceras de fuente y fecha, buscador, comprobador de vigencia, mapa de temas y jerarquía normativa— sirve de base para otras escuelas, facultades o universidades. Si quieres adaptarlo a tu centro y necesitas ayuda, escríbeme a través de [pablomagarinos.es](https://pablomagarinos.es).

## Límites y aviso legal

- **No está vinculada a la Universidade de Vigo** ni es una publicación oficial suya; los textos son fuentes oficiales de acceso público redistribuidas sin modificar (ver [`NOTICE.md`](NOTICE.md)).
- **No es asesoramiento jurídico.** Orienta y cita fuentes, pero no sustituye a la Asesoría Xurídica, la Vicerreitoría de Profesorado ni Recursos Humanos en decisiones con efectos sancionadores, contractuales o económicos.
- **El corpus es del 2026-10-01.** «Validada» en el portal no significa «vigente hoy»: antes de decidir, usa el comprobador en directo de la skill (`comprobar.py`) o consulta la fuente oficial.
- **Huecos conocidos:** la normativa de dedicación 2026/27 y la instrución de vacaciones 2026 no están publicadas; 8 documentos (7 PDF escaneados y un .docx) no tienen texto extraíble.
- **Solo cubre la EEAE.** Otros centros tienen sus propios reglamentos, que no están en el corpus.

## Mantenimiento, contribuciones y licencia

- Actualizar el corpus y cada curso nuevo: [`tools/README.md`](tools/README.md).
- Avisar de una norma desactualizada o adaptar la skill: [`CONTRIBUTING.md`](CONTRIBUTING.md).
- Código e instrucciones bajo licencia MIT ([`LICENSE`](LICENSE)); los textos normativos pertenecen a sus organismos emisores.

## Instrucciones para agentes de IA

Esta sección basta para instalar la skill sin leer nada más. La skill vive en [`skills/normativa-uvigo-eeae/`](skills/normativa-uvigo-eeae/) y su punto de entrada es `SKILL.md`. Los comandos `git clone` y el marketplace remoto requieren que el repo esté publicado en GitHub; si aún no lo está, sustituye `https://github.com/Pablomg02/uvigo-eeae-skill` por la ruta local del checkout (en Claude Code vale `claude plugin marketplace add /ruta/al/checkout`). Tras instalar, la comprobación común es preguntar «¿Qué skills tienes disponibles?» y confirmar que aparece `normativa-uvigo-eeae` (con el plugin de Claude Code sale como `normativa-uvigo-eeae:normativa-uvigo-eeae`).

### Claude Code

Marketplace (recomendado; el repo debe estar publicado):

```bash
claude plugin marketplace add Pablomg02/uvigo-eeae-skill
claude plugin install normativa-uvigo-eeae@uvigo-eeae-skill
claude plugin list
claude plugin details normativa-uvigo-eeae
```

Comprobación: `claude plugin list` muestra `normativa-uvigo-eeae@uvigo-eeae-skill` con `Status: ✔ enabled`, y `claude plugin details` muestra `Skills (1) normativa-uvigo-eeae`. En una sesión nueva, la skill instalada como plugin aparece en `claude -p` como `normativa-uvigo-eeae:normativa-uvigo-eeae` (namespace `plugin:skill`); con el enlace manual, como `normativa-uvigo-eeae`.

Alternativa manual (funciona ya, con el repo clonado):

```bash
git clone https://github.com/Pablomg02/uvigo-eeae-skill ~/uvigo-eeae-skill
mkdir -p ~/.claude/skills
ln -s ~/uvigo-eeae-skill/skills/normativa-uvigo-eeae ~/.claude/skills/normativa-uvigo-eeae
```

Comprobación: en una sesión nueva, `/skills` la lista como `normativa-uvigo-eeae` (o `claude -p "¿Qué skills tienes disponibles?"`).

### Codex CLI

```bash
git clone https://github.com/Pablomg02/uvigo-eeae-skill ~/uvigo-eeae-skill
mkdir -p ~/.agents/skills
ln -s ~/uvigo-eeae-skill/skills/normativa-uvigo-eeae ~/.agents/skills/normativa-uvigo-eeae
```

Para un solo proyecto, enlaza en `.agents/skills/` de su raíz. Comprobación: `codex exec --skip-git-repo-check "¿Qué skills tienes disponibles? Responde solo con la lista de nombres." < /dev/null` debe incluir `normativa-uvigo-eeae`; en la TUI, `/skills` o la mención `$normativa-uvigo-eeae`. El flag `--skip-git-repo-check` es necesario si el directorio de trabajo no es un repo git (`codex exec` aborta con «Not inside a trusted directory»); `< /dev/null` evita que espere entrada por stdin cuando se lanza desde un script o agente.

### OpenCode

```bash
git clone https://github.com/Pablomg02/uvigo-eeae-skill ~/uvigo-eeae-skill
mkdir -p ~/.config/opencode/skills
ln -s ~/uvigo-eeae-skill/skills/normativa-uvigo-eeae ~/.config/opencode/skills/normativa-uvigo-eeae
```

Para un solo proyecto, usa `.opencode/skills/` (OpenCode también lee `.claude/skills/` y `.agents/skills/`, y como global `~/.claude/skills/`). Comprobación: `opencode run "¿Qué skills tienes disponibles?"` debe incluir `normativa-uvigo-eeae`.

### claude.ai / app de Claude (documentado, no probado desde esta máquina)

1. Descarga `normativa-uvigo-eeae.skill` de la Release del repo (o genera `dist/normativa-uvigo-eeae.skill` con `python3 tools/empaquetar.py`).
2. **Customize → Skills → «+» → «+ Create skill» → «Upload a skill»** y sube el `.skill` (es un ZIP con la carpeta de la skill dentro).
3. En **Settings → Capabilities**, activa «Code execution and file creation» y «Allow network egress»; añade como dominios permitidos `secretaria.uvigo.gal`, `www.boe.es`, `aero.uvigo.es` y `eido.uvigo.gal`.
4. Comprobación: la skill aparece en Customize → Skills; al preguntar por normativa debe citar artículo y fuente y usar sus scripts.

### ChatGPT (documentado, no probado desde esta máquina)

1. Si el plan es Business, Enterprise, Healthcare o Edu y el workspace tiene Skills: **Skills → Create → Upload from your computer** y sube el ZIP de la Release.
2. Si no: crea un Proyecto (o GPT personalizado), adjunta el ZIP como archivo, pega el contenido de `SKILL.md` en las instrucciones y activa el análisis de datos.
3. Límites de la alternativa: no ejecuta `buscar.py` ni `comprobar.py`, así que no hay búsqueda en el corpus ni comprobación de vigencia en directo; solo puede leer los archivos del ZIP y buscar en la web.

### Otros agentes compatibles con Agent Skills

Gemini CLI (`~/.gemini/skills/` o `.agents/skills/`, y `gemini skills install`), Cursor (`~/.cursor/skills/` o `.agents/skills/`; también lee `.claude/skills/` y `.codex/skills/`) y GitHub Copilot (`.github/skills`, `.claude/skills`, `.agents/skills`, `~/.copilot/skills` o `~/.agents/skills`) usan el mismo formato. Basta clonar el repo y enlazar `skills/normativa-uvigo-eeae` en la ruta de skills que corresponda. (Rutas según la documentación de cada herramienta; no probadas desde esta máquina.)
