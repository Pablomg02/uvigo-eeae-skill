#!/usr/bin/env python3
"""Prepara la versión para subir a la app de Claude (claude.ai): crea dist/normativa-uvigo-eeae.skill.

La app admite como mucho 30 MB sin comprimir y da problemas con más de ~200 archivos, así que se dejan fuera los
scripts de descarga (allí no se puede actualizar) y casi todos los PDF originales. De los PDF que no viajan se
guarda una huella en data/huellas.json (la genera tools/huellas.py) para que comprobar.py pueda seguir detectando
cambios, y buscar.py --layout los descarga de su fuente si el entorno tiene red. Ejecútalo después de cada actualización.
"""
import json, sys, zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "normativa-uvigo-eeae"
sys.path.insert(0, str(SKILL / "scripts"))
from buscar import docs, read_doc

# PDF originales que sí viajan: tablas que se consultan a menudo (POD, dedicación, indemnizaciones) y el calendario y los exámenes de la Escola.
ORIGINALES = ("709-", "657-", "234-", "328-regulamento-para-a-liquidacion-e-tramitacion-de-indemni-doc3", "Calendario_EEAE", "Exames_Aero")
SCRIPTS = ["buscar.py", "comprobar.py", "guia.py", "lib.py", "crawl_portal.py"]
DATA = ["catalog.json", "curated.json", "huellas.json"]
MAX_BYTES, MAX_FILES = 30_000_000, 200

if not (SKILL / "data" / "huellas.json").is_file():
    sys.exit("Falta data/huellas.json: ejecuta antes tools/huellas.py")
huellas = json.loads((SKILL / "data" / "huellas.json").read_text())

files = {"SKILL.md": (SKILL / "SKILL.md").read_bytes()}
# Licencia MIT y aviso de terceros: en la raíz del repo y dentro del paquete.
files.update({n: (REPO / n).read_bytes() for n in ("LICENSE", "NOTICE.md") if (REPO / n).is_file()})
files.update({f"references/{p.name}": p.read_bytes() for p in sorted((SKILL / "references").glob("*.md"))})
files.update({f"scripts/{s}": (SKILL / "scripts" / s).read_bytes() for s in SCRIPTS})
files.update({f"data/{d}": (SKILL / "data" / d).read_bytes() for d in DATA})
for amb, p in docs():
    meta = read_doc(p)[0]
    if meta.get("traduccion"):
        continue
    files[str(p.relative_to(SKILL))] = p.read_bytes()
    orig = meta.get("original_local")
    if not orig or not (SKILL / orig).is_file():
        continue
    data = (SKILL / orig).read_bytes()
    name = orig.rsplit("/", 1)[-1]
    # viajan los PDF imprescindibles y los escaneados pequeños que la skill abre como imagen
    if name.startswith(ORIGINALES) or (meta.get("sin_texto") and name.endswith(".pdf") and len(data) < 1_000_000):
        files[orig] = data

total = sum(len(v) for v in files.values())
rutas = [k for k, v in files.items() if not k.endswith(".pdf") and str(REPO).encode() in v]
print(f"{len(files)} archivos, {total / 1e6:.1f} MB sin comprimir ({len(huellas)} huellas de PDF que no viajan)")
if rutas:
    sys.exit("Hay rutas absolutas de tu ordenador en: " + ", ".join(rutas))
if total > MAX_BYTES or len(files) > MAX_FILES:
    sys.exit(f"Supera el límite de la app ({MAX_BYTES / 1e6:.0f} MB, {MAX_FILES} archivos): quita originales de ORIGINALES o normas de fetch_uvigo.py")
out = REPO / "dist" / f"{SKILL.name}.skill"
out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for k, v in sorted(files.items()):
        z.writestr(f"{SKILL.name}/{k}", v)
print(f"Listo: {out} ({out.stat().st_size / 1e6:.1f} MB comprimido). Súbelo en claude.ai → Customize → Skills → «Upload a skill».")
