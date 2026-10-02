# Resumen del benchmark de normativa-uvigo-eeae

Generado: 2026-10-02T20:12:29+02:00  
Ejecuciones: 40 | notas: 40 | juez: claude-opus-5-5  
Evals: 10 (grupos: desarrollo=6, nuevas=4)

> DeepSeek V4.1 Flash (OpenCode, effort por defecto): 1 repetición por pregunta, así que el ± recoge la dispersión entre las preguntas de cada condición (no entre repeticiones). Claude Opus 5.5 (Claude Code, effort medium): 1 repetición por pregunta, así que el ± recoge la dispersión entre las preguntas de cada condición (no entre repeticiones). La comparación válida es con skill frente a sin skill dentro de cada modelo.

## Tasa de aserciones superadas por modelo y condición

| Modelo | Condición | Aserciones superadas | Runs con nota |
|---|---|---|---|
| DeepSeek V4.1 Flash (OpenCode, effort por defecto) | con skill | 85.0 % ± 18.3 | 10 |
| DeepSeek V4.1 Flash (OpenCode, effort por defecto) | sin skill | 58.3 % ± 28.6 | 10 |
| Claude Opus 5.5 (Claude Code, effort medium) | con skill | 91.7 % ± 11.8 | 10 |
| Claude Opus 5.5 (Claude Code, effort medium) | sin skill | 60.0 % ± 31.6 | 10 |

## Mejora con skill (puntos porcentuales)

| Modelo | skill − sin skill |
|---|---|
| DeepSeek V4.1 Flash (OpenCode, effort por defecto) | +26.7 pp |
| Claude Opus 5.5 (Claude Code, effort medium) | +31.7 pp |

## Resultado por grupo (desarrollo / nuevas)

| Modelo | Condición | Desarrollo | Nuevas |
|---|---|---|---|
| DeepSeek V4.1 Flash (OpenCode, effort por defecto) | con skill | 80.6 % | 91.7 % |
| DeepSeek V4.1 Flash (OpenCode, effort por defecto) | sin skill | 55.6 % | 62.5 % |
| Claude Opus 5.5 (Claude Code, effort medium) | con skill | 88.9 % | 95.8 % |
| Claude Opus 5.5 (Claude Code, effort medium) | sin skill | 61.1 % | 58.3 % |

## Resultado por eval y condición

| Modelo | Eval | Con skill | Sin skill |
|---|---|---|---|
| DeepSeek V4.1 Flash (OpenCode, effort por defecto) | 0 | 50.0 % | 83.3 % |
| DeepSeek V4.1 Flash (OpenCode, effort por defecto) | 1 | 83.3 % | 66.7 % |
| DeepSeek V4.1 Flash (OpenCode, effort por defecto) | 2 | 83.3 % | 33.3 % |
| DeepSeek V4.1 Flash (OpenCode, effort por defecto) | 3 | 100.0 % | 100.0 % |
| DeepSeek V4.1 Flash (OpenCode, effort por defecto) | 4 | 66.7 % | 33.3 % |
| DeepSeek V4.1 Flash (OpenCode, effort por defecto) | 5 | 100.0 % | 16.7 % |
| DeepSeek V4.1 Flash (OpenCode, effort por defecto) | 6 | 100.0 % | 33.3 % |
| DeepSeek V4.1 Flash (OpenCode, effort por defecto) | 7 | 66.7 % | 50.0 % |
| DeepSeek V4.1 Flash (OpenCode, effort por defecto) | 8 | 100.0 % | 83.3 % |
| DeepSeek V4.1 Flash (OpenCode, effort por defecto) | 9 | 100.0 % | 83.3 % |
| Claude Opus 5.5 (Claude Code, effort medium) | 0 | 100.0 % | 100.0 % |
| Claude Opus 5.5 (Claude Code, effort medium) | 1 | 83.3 % | 16.7 % |
| Claude Opus 5.5 (Claude Code, effort medium) | 2 | 83.3 % | 66.7 % |
| Claude Opus 5.5 (Claude Code, effort medium) | 3 | 100.0 % | 100.0 % |
| Claude Opus 5.5 (Claude Code, effort medium) | 4 | 100.0 % | 50.0 % |
| Claude Opus 5.5 (Claude Code, effort medium) | 5 | 66.7 % | 33.3 % |
| Claude Opus 5.5 (Claude Code, effort medium) | 6 | 100.0 % | 33.3 % |
| Claude Opus 5.5 (Claude Code, effort medium) | 7 | 83.3 % | 66.7 % |
| Claude Opus 5.5 (Claude Code, effort medium) | 8 | 100.0 % | 33.3 % |
| Claude Opus 5.5 (Claude Code, effort medium) | 9 | 100.0 % | 100.0 % |

## Uso real de la skill

- Ejecuciones con skill: 20
- En las que la skill se usó de verdad: 20 (100.0 %)

## Coste y tiempo

| Modelo | Condición | Coste medio (USD) | Duración media (s) |
|---|---|---|---|
| DeepSeek V4.1 Flash (OpenCode, effort por defecto) | con skill | 0.0139 | 82 |
| DeepSeek V4.1 Flash (OpenCode, effort por defecto) | sin skill | 0.0134 | 64 |
| Claude Opus 5.5 (Claude Code, effort medium) | con skill | 0.3661 | 48 |
| Claude Opus 5.5 (Claude Code, effort medium) | sin skill | 0.2911 | 52 |

- Coste total de las respuestas: 6.8452 USD
- Coste total del juez: 5.1999 USD
- Duración media del juez por corrección: 12.6 s

## Incidencias

- Ejecuciones contaminadas: 0
- Ejecuciones fallidas (técnicas): 0
- Correcciones sin nota válida: 0

## Gráficas

- `docs/img/bench-aciertos.png`
- `docs/img/bench-por-pregunta.png`
- `docs/img/bench-coste.png`

