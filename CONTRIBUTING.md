# Cómo contribuir

Lo más útil son avisos de normativa desactualizada y normas que falten en el corpus.

## Avisar de una norma desactualizada

Abre una incidencia con la plantilla **[Norma desactualizada](.github/ISSUE_TEMPLATE/norma-desactualizada.yml)**: norma, qué ha cambiado, enlace oficial y fecha. Si la norma quedó superada, se corrige además su vigencia en `skills/normativa-uvigo-eeae/data/curated.json`.

## Añadir una norma a mano

1. Guarda el texto como `.md` en `skills/normativa-uvigo-eeae/normativa/{curso,uvigo,eeae,eido,estatal,galicia}/`, según el ámbito.
2. Encabeza el archivo con un bloque `---` que incluya al menos `titulo`, `fuente` y `ambito`. Cualquier norma existente sirve de modelo.
3. Comprueba que el buscador la ve: `python3 skills/normativa-uvigo-eeae/scripts/buscar.py --lista | grep <fichero>`.

## Regenerar el corpus

```bash
python3 skills/normativa-uvigo-eeae/scripts/comprobar.py --novedades   # qué ha cambiado, sin tocar nada
bash tools/actualizar.sh                                               # rastrea las fuentes oficiales; necesita internet
python3 tools/huellas.py                                               # solo las huellas de los PDF
```

Después revisa a mano `skills/normativa-uvigo-eeae/data/curated.json` (marcas de vigencia) y `skills/normativa-uvigo-eeae/references/huecos.md`. El mantenimiento vive en [`tools/`](tools/README.md) y no viaja con la skill instalada.

## Adaptarlo a otro centro

La estructura sirve para otras escuelas y universidades: toca los descargadores de tu centro (`tools/fetch_*.py`), el mapa de temas (`skills/normativa-uvigo-eeae/references/temas.md`) y las instrucciones de la skill (`skills/normativa-uvigo-eeae/SKILL.md`).

## Benchmarks

Metodología y reproducción: [`benchmarks/README.md`](benchmarks/README.md).

¿Dudas o ayuda para adaptarlo? Escríbeme a través de [pablomagarinos.es](https://pablomagarinos.es).
