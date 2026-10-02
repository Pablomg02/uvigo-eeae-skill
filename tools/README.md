# Mantenimiento de la skill

Aquí vive lo que **no viaja** con la skill instalada: los scripts que reconstruyen el corpus desde las fuentes oficiales y el empaquetador. La skill solo lleva lo que la IA usa al responder.

**Requisitos:** python3 (biblioteca estándar), `pdftotext` (poppler-utils) y `pandoc` para reconstruir el corpus; `huellas.py` y `empaquetar.py` solo necesitan python3.

## Antes de actualizar

```bash
python3 skills/normativa-uvigo-eeae/scripts/comprobar.py --novedades
```

En segundos dice si hay normas nuevas en el portal de la UVigo, la Escola o la EIDO y leyes del BOE modificadas. Las normas nuevas de categorías que no se descargan solas se añaden a `EXTRA` en `fetch_uvigo.py`.

## Actualización completa

```bash
bash tools/actualizar.sh      # minutos; necesita internet
```

Rastrea el portal y las webs de la Escola y la EIDO, descarga BOE y DOG, regenera los índices y genera las huellas de los PDF que no viajan en `data/huellas.json`. Después se revisan a mano `data/curated.json` (marcas de vigencia) y `references/huecos.md`. Solo las huellas: `python3 tools/huellas.py`.

## Empaquetar para la app de Claude

```bash
python3 tools/empaquetar.py   # deja dist/normativa-uvigo-eeae.skill
```

El paquete lleva la skill sin los scripts de mantenimiento y solo con los PDF imprescindibles. Súbelo en claude.ai → Ajustes → Capacidades → Skills.

## Cada curso nuevo

En `fetch_curso.py` cambia `CURSO` (p. ej. `"2027_28"`) y ejecútalo: descarga el calendario y los exámenes de la Escola. Las guías docentes no se guardan: `guia.py` usa por defecto el curso vigente.

## Añadir una norma a mano

Guarda su texto como `.md` en la carpeta del ámbito que corresponda (`normativa/{curso,uvigo,eeae,eido,estatal,galicia}/`) con una cabecera `---` como las demás (al menos `titulo`, `fuente`, `ambito`); el buscador la encuentra sin más.
