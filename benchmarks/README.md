# Benchmarks de `normativa-uvigo-eeae`

Arnés para medir cuánto mejora la skill las respuestas sobre normativa de la
EEAE y del doctorado de la UVigo. Solo usa la biblioteca estándar de Python 3
(`matplotlib` es opcional en `report.py`).

## Qué se mide y por qué

- **10 preguntas** (`evals.json`), cada una con 4–6 aserciones verificables
  contra la norma y un campo `fuente` (documento y artículo).
  - **Grupo `desarrollo` (6):** preguntas derivadas del temario con el que se
    afinó la skill. Miden si la skill responde bien lo que ya estaba previsto.
  - **Grupo `nuevas` (4):** preguntas escritas sin leer `SKILL.md` ni
    `references/`, incluida una trampa cuya respuesta correcta es «no consta
    publicado / no se puede verificar». Es el grupo que mide generalización.
- **Dos condiciones:** `skill` (con la skill del repo instalada en el
  workspace) y `sin_skill` (sin ella). **El prompt es idéntico** en ambas y
  ambas tienen el mismo acceso a herramientas (Bash, Read, Grep, Glob,
  WebFetch, WebSearch, Skill); lo que cambia es únicamente la presencia de la
  skill. Por eso lo comparable es «con frente a sin skill» dentro de cada
  modelo, no un modelo contra otro.
- **Repeticiones:** el arnés corre por defecto la matriz completa —DeepSeek V4.1
  Flash (`opencode-go/deepseek-v4.1-flash` vía OpenCode) con 3 repeticiones y
  Claude Sonnet 5.5 y Claude Opus 5.5 (vía Claude Code) con 1, como referencia
  orientativa: 100 ejecuciones—, configurable con `--models` y `--reps`.
  **La tanda publicada el 2026-10-02 se ejecutó solo con DeepSeek y 1 repetición
  por pregunta** (decisión de coste): 20 ejecuciones. Las cifras de esa tanda,
  por tanto, no permiten estimar la varianza entre repeticiones; en la tabla, el
  `±` de cada condición es la dispersión entre las 10 preguntas. Para repetir la
  matriz completa: `python3 benchmarks/run.py --models deepseek,sonnet,opus
  --reps deepseek=3,sonnet=1,opus=1`.

## Aislamiento (crítico)

La máquina tiene skills de usuario sincronizadas en `~/.claude/skills/synced/`
que no deben contaminar la condición `sin_skill`. Cada ejecución se lanza en un
directorio temporal limpio y:

- **Claude Code:** `CLAUDE_CONFIG_DIR` y `HOME` temporales con copia de
  `~/.claude/.credentials.json`; `--setting-sources project`; ajustes
  `disableBundledSkills`, `enabledPlugins` de los plugins internos y
  `skillOverrides` para las skills internas `design` y `doctor`. La skill se
  copia a `<workspace>/.claude/skills/normativa-uvigo-eeae` solo en `skill`.
- **OpenCode:** `HOME`, `XDG_CONFIG_HOME` y `XDG_DATA_HOME` temporales con
  `auth.json` copiado y un `opencode.json` de proyecto con permisos no
  interactivos; la skill se copia a `<workspace>/.opencode/skills/` solo en
  `skill`. Se oculta `customize-opencode` en ambas condiciones
  (`permission.skill`) y se fija `PWD` al workspace (OpenCode lo usa para
  localizar el proyecto si se lanza con otro `cwd`).

Evidencia reproducible:

```bash
python3 benchmarks/run.py --isolation-check
```

Deja el log en `/tmp/uvigo-bench/aislamiento.log` y un JSON por caso en
`/tmp/uvigo-bench/aislamiento/`. Resultado real del 2026-10-02:

| CLI | Condición | Skills visibles / respuesta | Veredicto |
|---|---|---|---|
| Claude (`claude-sonnet-5-5`) | `sin_skill` | `skills_visibles: []` → `NINGUNA` | Aislado |
| Claude (`claude-sonnet-5-5`) | `skill` | `skills_visibles: ['normativa-uvigo-eeae']` → `normativa-uvigo-eeae` | OK |
| OpenCode (`deepseek-v4.1-flash`) | `sin_skill` | `NINGUNA` | Aislado |
| OpenCode (`deepseek-v4.1-flash`) | `skill` | `normativa-uvigo-eeae` | OK |

Además, `run.py` marca `contaminada: true` en cualquier ejecución `sin_skill`
cuya transcripción mencione `normativa-uvigo-eeae`, `.claude/skills`,
`.opencode/skills`, `.agents/skills` o `SKILL.md`, o invoque la herramienta
`Skill`, y `skill_usada: true` en las ejecuciones `skill` que invoquen `Skill`
o lean dentro de la carpeta de la skill. `grade.py` reutiliza esas funciones y
`report.py` informa del % de uso real de la skill, las contaminadas y las
fallidas.

## Cómo reproducir

```bash
# 1. Prueba de aislamiento (4 ejecuciones baratas)
python3 benchmarks/run.py --isolation-check

# 2. Tanda de la que salen las cifras del README (20 ejecuciones, ~8 min con --jobs 4)
python3 benchmarks/run.py --models deepseek --reps deepseek=1

# 2b. Matriz completa por defecto (100 ejecuciones: DeepSeek ×3, Sonnet ×1, Opus ×1)
python3 benchmarks/run.py

# 3. Corrección con el juez (Claude Opus 5.5)
python3 benchmarks/grade.py

# 4. Resumen y gráficas
python3 benchmarks/report.py
```

Los resultados se guardan en `benchmarks/results/<AAAA-MM-DD>/`:

```
results/<fecha>/
├── runs/<modelo>/<condicion>/<eval>-r<n>.json    # respuesta, herramientas, tokens, coste, duración…
├── notas/<modelo>/<condicion>/<eval>-r<n>.json   # resultado del juez por aserción, con cita literal
├── corpus/fuentes.json                           # textos de los artículos citados (caché para el juez)
├── summary.json                                  # cifras agregadas (fuente del README)
└── summary.md                                    # el mismo resumen en Markdown
```

Subconjuntos y opciones útiles:

```bash
python3 benchmarks/run.py --evals 0,1 --models deepseek,sonnet --reps deepseek=1
python3 benchmarks/grade.py --results-dir benchmarks/results/2026-10-02 --evals 0,1
python3 benchmarks/report.py --results-dir benchmarks/results/2026-10-02
```

`run.py` es reanudable: se saltan las ejecuciones con `exit_code == 0` y sin
`error`; los fallos técnicos se reintentan al volver a lanzarlo. `--dry-run`
lista las ejecuciones previstas sin ejecutar nada.

## Corrección (juez)

`grade.py` usa `claude -p --model claude-opus-5-5` sin herramientas. El juez
**no sabe** qué modelo ni condición respondió: las ejecuciones se barajan y el
prompt solo incluye la pregunta, la respuesta de referencia, las aserciones,
los textos de los artículos citados en `fuente` (extraídos con
`scripts/buscar.py` y cacheados por eval) y la respuesta evaluada. Devuelve un
JSON validado por esquema con `pass`/`fail` y una cita literal por aserción; si
el JSON no valida se reintenta una vez. Una cita vacía incumple el esquema y se
cuenta como `fail` (anotado como `cita_vacia`).

## Coste y duración reales (tanda del 2026-10-02)

Tanda ejecutada: DeepSeek V4.1 Flash, 10 evals × 2 condiciones × 1 repetición =
**20 ejecuciones**, con `--jobs 4`.

- **Ejecuciones:** 20/20 correctas, 0 contaminadas, skill usada de verdad en las
  10 ejecuciones con skill (100 %). Pared de la tanda: **452,8 s**.
- **Corrección (juez Claude Opus 5.5):** 20/20 correctas, 0 fallos. Pared:
  **73,4 s**; ≈12,9 s por corrección.
- Coste de las respuestas: **$0,273** (≈$0,0137 por respuesta). Coste del juez:
  **$2,5726**. Total del dataset final: **$2,85**.
- Durante la tanda el detector marcó **3 ejecuciones `sin_skill` contaminadas**
  (mencionaban rutas o archivos de la skill); se repitieron las 3, con un coste
  adicional de ≈**$0,43** ($0,05 de respuestas + $0,37 de juez). Contando esa
  repetición, el benchmark completo costó ≈**$3,3**.
- La prueba de aislamiento cuesta ≈ **$0,03** (4 ejecuciones baratas).
- Cifras completas y verificables en
  `benchmarks/results/2026-10-02/summary.json`.

## Limitaciones

- **n pequeño:** la tanda publicada tiene 1 repetición por pregunta y un solo
  modelo (DeepSeek V4.1 Flash), así que no permite estimar la varianza entre
  repeticiones ni generalizar a otros modelos; el `±` es la dispersión entre
  preguntas de cada condición.
- **El juez es también uno de los modelos evaluados** (Opus 5.5) cuando se corre
  la matriz completa; en esta tanda solo actuó como juez. Por eso se
  audita a mano una muestra estratificada; el resultado se documenta en
  «Auditoría del juez».
- **Herramientas distintas entre CLIs**, sobre todo de búsqueda web: Claude
  Code usa `WebSearch`/`WebFetch` y OpenCode las suyas. Por eso solo se compara
  con frente a sin skill dentro de cada modelo.
- **La web cambia:** las respuestas «sin skill» pueden acertar por búsqueda en
  internet; el aislamiento impide que vean la skill, no que consulten la web.
- **El corpus tiene fecha:** las cifras de vigencia (p. ej. convenios o
  calendarios) corresponden al corpus incluido en el repo en su fecha.
- **`matplotlib` no está instalado en el entorno por defecto de la máquina de
  referencia:** `report.py` avisa y genera `summary.json`/`summary.md` sin
  gráficas. Las de `docs/img/` se generaron con matplotlib 3.11.2 en un venv
  temporal (`pip install matplotlib`).
- En la condición `sin_skill` el arnés oculta también las skills internas de
  cada CLI (`design`/`doctor` en Claude, `customize-opencode` en OpenCode) para
  que la única diferencia entre condiciones sea `normativa-uvigo-eeae`.

## Auditoría del juez

**Fecha:** 2026-10-02. **Tanda auditada:** DeepSeek V4.1 Flash, 10 evals × 2
condiciones × 1 repetición (20 ejecuciones), juez `claude-opus-5-5`.
**Método:** revisión manual aserción por aserción, con los textos normativos
delante (`results/2026-10-02/corpus/fuentes.json` y
`skills/normativa-uvigo-eeae/scripts/buscar.py`); cuando la respuesta citaba un
documento externo se comprobó su texto real (convocatoria 1785 y Anexos XV/IX
corregidos).

**Muestra elegida (10 ejecuciones, 60 aserciones):**

| Condición | Ejecución | Nota del juez | Criterio de selección |
|---|---|---|---|
| `skill` | `0-r1` | 3/6 (50,0 %) | nota más baja de la condición |
| `skill` | `4-r1` | 4/6 (66,7 %) | nota baja |
| `skill` | `7-r1` | 4/6 (66,7 %) | nota baja |
| `skill` | `8-r1` | 6/6 (100 %) | nota alta |
| `skill` | `9-r1` | 6/6 (100 %) | la trampa |
| `sin_skill` | `0-r1` | 5/6 (83,3 %) | comparación directa con `skill` 0 |
| `sin_skill` | `2-r1` | 2/6 (33,3 %) | nota baja |
| `sin_skill` | `5-r1` | 1/6 (16,7 %) | nota más baja de la tanda |
| `sin_skill` | `6-r1` | 2/6 (33,3 %) | nota baja |
| `sin_skill` | `9-r1` | 5/6 (83,3 %) | la trampa |

Cubre 8 de los 10 evals (0, 2, 4, 5, 6, 7, 8 y 9); fuera quedan el 1 y el 3.

**Tasa de acuerdo:** 58/60 = **96,7 %** (los 2 desacuerdos claros son falsos
`fail`). El caso discutible del eval 5 no computa como desacuerdo (57/60 =
95,0 % si se contara). El desacuerdo no supera el ~10 %, así que no se
modificaron `evals.json` ni `grade.py` y no se repitió la corrección.

**Desacuerdos claros (2, ambos falsos `fail`):**

1. **Eval 0, `skill`, aserción 5.** El juez falla con la cita «565, art. 61.1:
   contra una resolución desfavorable, recurso de alzada ante reitoría en 10
   días hábiles» y comenta que la respuesta «da plazos que no se pueden
   comprobar con los textos citados: el de 10 días hábiles para la alzada, que
   parece contradecir el plazo legal de un mes, y el de 3 meses para rectificar
   el acta». La respuesta no inventa: 565 art. 61.1 dice literalmente «poderá
   interpoñer un recurso de alzada ante a reitoría nun prazo de dez días
   hábiles» y las Normas de xestión académica (353) dicen «no prazo máximo de
   tres meses a partir da data límite de rexistro das cualificacións». El juez
   no recibió esos textos (la `fuente` de la aserción solo lista 565 arts. 35 y
   37), pero la aserción sí se cumple.
2. **Eval 4, `skill`, aserción 5.** El juez falla por «plazos y requisitos
   concretos que los textos aportados no permiten verificar» y por un plazo que
   le parece «incoherente». Los plazos citados existen: el Anexo XV corregido
   de la convocatoria 2026/27 (doc. 1785) fija «entre o 2 e o 13 de novembro de
   2026» y «entre o 5 e o 16 de abril de 2027»; el Anexo II del POD (709) fija
   «dende o 20 de decembro de 2025 ata o 20 de xaneiro de 2026, para a súa
   incorporación no segundo cuadrimestre»; y el Anexo IX corregido fija la
   renovación de matrícula «1/09-10/10». La respuesta además remite a la EIDO y
   al programa, como pide la aserción.

**Discutible (1, no computado):** eval 5, `sin_skill`, aserción 0. El juez la
aprueba, pero la respuesta omite el trámite de audiencia («tras atender o
profesorado e as delegacións do estudantado afectado», 565 art. 25.2). El
núcleo de la aserción (el calendario no se cambia a petición individual) sí
está; se documenta como rigor laxo, no como error.

**Veredictos pedidos:**

- **Eval 0 en `skill` (50,0 %):** no es un problema de enunciado. Los fallos de
  A3 y A4 son reales: la respuesta no dice que la segunda evaluación se
  solicita «ante o órgano de dirección do centro» y no menciona la composición
  del tribunal (tres miembros del PDI, sin el profesorado responsable). El
  fallo de A5 es injusto (desacuerdo 1). Corregido A5, el eval 0 sería 4/6
  (66,7 %). La diferencia con `sin_skill` (5/6) no viene de una aserción
  ambigua, sino de que esa respuesta sí citó «ante el decanato/dirección del
  centro»; ambas omitieron la composición del tribunal. La `fuente` de A5 es
  mejorable (le faltan 565 art. 61 y 353), pero no cambia la respuesta.
- **Evals 5 y 6 en `sin_skill` (16,7 % y 33,3 %):** fallos reales, no del
  juez. Eval 5: atribuye la nueva fecha al centro en vez de al profesorado
  (A1), omite la causa residual «Calquera outra causa sobrevida» (A2), da el
  plazo de avaliación global como «del 7 de septiembre al 7 de octubre de
  2026» cuando el calendario dice «1ºC: 8 setembro a 8 outubro» (A3), no dice
  que la prueba global va en la fecha oficial (A4) y aporta datos no
  respaldados, como la «instancia (EEAE-001)» (A5). Eval 6: omite que
  «ningunha unha duración inferior aos sete días» y el máximo de
  cinco períodos (A0), limita la lengua a «distinta del español» en vez de
  «distinta a calquera das linguas oficiais en España» (A2), contradice el
  art. 43.c al afirmar que los informantes «sí pueden luego formar parte del
  tribunal» (A3) y omite que si se superan los tres meses «iniciaranse de novo
  os trámites» (A5).
- **Eval 9 (la trampa) en ambas condiciones:** correcto. `skill` 6/6 y
  `sin_skill` 5/6; las dos rechazan el III Convenio, se apoyan en el art. 5 del
  II Convenio y en el acta de 7-feb-2025 y remiten al DOG. El único `fail`
  (`sin_skill`, A5) es defendible: afirma como existente un «derecho al cobro
  de sexenios/quinquenios» por «jurisprudencia del Supremo y resoluciones de
  2026» que no consta en los textos; la respuesta `skill` menciona lo mismo
  pero lo marca como no verificado («la pista de sexenios viene de fuentes
  sindicales, no verificadas»).

**Conclusión:** el juez es fiable en la muestra (96,7 % de acuerdo; los 2
errores son `fail` injustos en aserciones negativas «no inventa plazos» cuya
`fuente` no incluye los documentos que la respuesta cita). No se cambia nada.
Solo a efectos ilustrativos: con esos dos `pass`, `skill` subiría de 85,0 % a
88,3 % (eval 0 a 66,7 %, eval 4 a 83,3 %) y `sin_skill` seguiría en 58,3 %.

**Limitaciones:** muestra de 60 aserciones y 1 repetición por eval; la tanda
solo contiene DeepSeek, así que la estratificación es por condición y nota, no
por modelo; los dos falsos `fail` se explican porque el juez no recibe las
fuentes externas que la respuesta cita (convocatoria 1785, 709) y las evalúa de
memoria; las aserciones compuestas admiten matices (eval 4 A2 y eval 6 A1
pasaron con incisos omitidos); no se auditaron los evals 1 y 3.
