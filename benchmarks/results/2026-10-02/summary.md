# Resumen del benchmark de normativa-uvigo-eeae

Generado: 2026-10-02T18:07:17+02:00  
Ejecuciones: 20 | notas: 20 | juez: claude-opus-5-5  
Evals: 10 (grupos: desarrollo=6, nuevas=4)

> DeepSeek V4.1 Flash (OpenCode): 1 repetición por pregunta, así que el ± recoge la dispersión entre las preguntas de cada condición (no entre repeticiones). La comparación válida es con skill frente a sin skill dentro de cada modelo.

## Tasa de aserciones superadas por modelo y condición

| Modelo | Condición | Aserciones superadas | Runs con nota |
|---|---|---|---|
| DeepSeek V4.1 Flash (OpenCode) | con skill | 85.0 % ± 18.3 | 10 |
| DeepSeek V4.1 Flash (OpenCode) | sin skill | 58.3 % ± 28.6 | 10 |

## Mejora con skill (puntos porcentuales)

| Modelo | skill − sin skill |
|---|---|
| DeepSeek V4.1 Flash (OpenCode) | +26.7 pp |

## Resultado por grupo (desarrollo / nuevas)

| Modelo | Condición | Desarrollo | Nuevas |
|---|---|---|---|
| DeepSeek V4.1 Flash (OpenCode) | con skill | 80.6 % | 91.7 % |
| DeepSeek V4.1 Flash (OpenCode) | sin skill | 55.6 % | 62.5 % |

## Resultado por eval y condición

| Modelo | Eval | Con skill | Sin skill |
|---|---|---|---|
| DeepSeek V4.1 Flash (OpenCode) | 0 | 50.0 % | 83.3 % |
| DeepSeek V4.1 Flash (OpenCode) | 1 | 83.3 % | 66.7 % |
| DeepSeek V4.1 Flash (OpenCode) | 2 | 83.3 % | 33.3 % |
| DeepSeek V4.1 Flash (OpenCode) | 3 | 100.0 % | 100.0 % |
| DeepSeek V4.1 Flash (OpenCode) | 4 | 66.7 % | 33.3 % |
| DeepSeek V4.1 Flash (OpenCode) | 5 | 100.0 % | 16.7 % |
| DeepSeek V4.1 Flash (OpenCode) | 6 | 100.0 % | 33.3 % |
| DeepSeek V4.1 Flash (OpenCode) | 7 | 66.7 % | 50.0 % |
| DeepSeek V4.1 Flash (OpenCode) | 8 | 100.0 % | 83.3 % |
| DeepSeek V4.1 Flash (OpenCode) | 9 | 100.0 % | 83.3 % |

## Uso real de la skill

- Ejecuciones con skill: 10
- En las que la skill se usó de verdad: 10 (100.0 %)

## Coste y tiempo

| Modelo | Condición | Coste medio (USD) | Duración media (s) |
|---|---|---|---|
| DeepSeek V4.1 Flash (OpenCode) | con skill | 0.0139 | 82 |
| DeepSeek V4.1 Flash (OpenCode) | sin skill | 0.0134 | 64 |

- Coste total de las respuestas: 0.273 USD
- Coste total del juez: 2.5726 USD
- Duración media del juez por corrección: 12.9 s

## Incidencias

- Ejecuciones contaminadas: 0
- Ejecuciones fallidas (técnicas): 0
- Correcciones sin nota válida: 0

## Gráficas

- `docs/img/bench-aciertos.png`
- `docs/img/bench-mapa-calor.png`

