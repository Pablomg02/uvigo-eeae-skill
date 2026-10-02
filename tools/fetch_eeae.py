#!/usr/bin/env python3
"""Descarga los reglamentos propios de la Escola de Enxeñaría Aeronáutica e do Espazo (aero.uvigo.es)."""
import json
import sys
from pathlib import Path
SKILL = Path(__file__).resolve().parent.parent / "skills" / "normativa-uvigo-eeae"
sys.path.insert(0, str(SKILL / "scripts"))
from lib import ROOT, download, to_text, write_norm

PAGE = "https://aero.uvigo.es/gl/o-centro/normativa-e-formularios/"
BASE = "https://aero.uvigo.es/docs/escuela/normativa/"
# (fichero, título, fecha de aprobación según la web del centro)
DOCS = [
    ("RRI_EEAE.pdf", "Regulamento de réxime interno da EEAE", "2017-10-09"),
    ("ReTi.pdf", "Regulamento de titorización (plan de acción titorial)", "2016-06-17"),
    ("Practicas_EEAE.pdf", "Regulamento de prácticas externas da EEAE", "2024-11-21"),
    ("TFG-TFM_EEAE.pdf", "Regulamento de Traballo de Fin de Grao e de Máster da EEAE", "2018-12-19"),
    ("Normativa_mobilidade_EEAE.pdf", "Normativa de mobilidade da EEAE", "2026-04-24"),
    ("Deleg_competencias_EEAE.pdf", "Listado de competencias delegadas da Xunta de Escola", "2020-10-23"),
]
index = []
for fn, title, fecha in DOCS:
    data = download(BASE + fn)
    text = to_text(data)
    (ROOT / "normativa" / "eeae" / "_originales").mkdir(parents=True, exist_ok=True)
    (ROOT / "normativa" / "eeae" / "_originales" / fn).write_bytes(data)
    out = ROOT / "normativa" / "eeae" / (fn.rsplit(".", 1)[0].lower().replace("_", "-") + ".md")
    write_norm(out, {"titulo": title, "ambito": "Escola (EEAE)", "fecha_aprobacion": fecha, "fuente": PAGE, "url_documento": BASE + fn, "original_local": f"normativa/eeae/_originales/{fn}", "estado_fuente": "publicado en la web del centro (no hay marca oficial de vigencia)"}, text)
    print(f"{len(text):>8} chars  {out.name}")
    index.append({"file": str(out.relative_to(ROOT)), "titulo": title, "fecha": fecha, "chars": len(text)})
json.dump(index, open(ROOT / "data" / "eeae_index.json", "w"), ensure_ascii=False, indent=1)
