#!/usr/bin/env bash
# Reconstruye el corpus completo desde las fuentes oficiales. Tarda unos minutos y necesita internet.
# Requisitos: python3, pdftotext (poppler-utils) y pandoc.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SKILL="$REPO/skills/normativa-uvigo-eeae"
cd "$REPO/tools"
echo "1/8 Rastreando el portal de normativa de la UVigo..."; python3 -u "$SKILL/scripts/crawl_portal.py"
echo "2/8 Descargando normas de la UVigo (selección en fetch_uvigo.py)..."; python3 -u "$REPO/tools/fetch_uvigo.py"
echo "3/8 Descargando reglamentos de la EEAE..."; python3 -u "$REPO/tools/fetch_eeae.py"
echo "4/8 Descargando procedementos e guías da EIDO (doutoramento)..."; python3 -u "$REPO/tools/fetch_eido.py"
echo "5/8 Descargando legislación del BOE..."; python3 -u "$REPO/tools/fetch_laws.py"
echo "6/8 Descargando convenio y actas del DOG..."; python3 -u "$REPO/tools/fetch_dog.py"
echo "7/8 Descargando el calendario y los exámenes de la EEAE (curso en fetch_curso.py)..."; python3 -u "$REPO/tools/fetch_curso.py"
echo "8/8 Generando las huellas de los PDF locales..."; python3 -u "$REPO/tools/huellas.py"
echo
echo "Hecho. Huellas regeneradas en data/huellas.json. Revisa a mano: data/curated.json (marcas de vigencia) y references/huecos.md."
echo "Las normas nuevas de categorías ajenas a PDI/docencia no entran solas: 'python3 \"$SKILL/scripts/comprobar.py\" --novedades' antes de actualizar te las enseña."
