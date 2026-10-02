#!/usr/bin/env python3
"""Descarga la normativa propia de la Escola Internacional de Doutoramento (eido.uvigo.gal) que no está en el portal de Secretaría.

El Regulamento de estudos de doutoramento (625) y el RRI da EIDO (41) ya vienen del portal; aquí van los procedementos,
protocolos e guías que publica a EIDO na súa web. A «Normativa de permanencia» da web é só o capítulo 7 do
regulamento (arts. 26–29 de 625) e non se descarga.
"""
import json
import sys
from pathlib import Path
SKILL = Path(__file__).resolve().parent.parent / "skills" / "normativa-uvigo-eeae"
sys.path.insert(0, str(SKILL / "scripts"))
from lib import ROOT, download, to_text, write_norm

PAGE = "https://eido.uvigo.gal/gl/eido/normativa"
BASE = "https://eido.uvigo.gal/docs/"
# (ruta bajo /docs/, título según la web de la EIDO)
DOCS = [
    ("eido/normativa/EIDO_Codigo_Boas_Practicas.pdf", "Código de boas prácticas da EIDO"),
    ("eido/normativa/EIDO_Protocolo_defensa_tese.pdf", "Protocolo do acto de defensa da tese de doutoramento"),
    ("eido/normativa/Procedemento_cotutela.pdf", "Procedemento para a obtención da mención de cotutela na tese de doutoramento"),
    ("eido/normativa/Procedemento_teses_proteccion_datos.pdf", "Procedemento para teses suxeitas a protección de datos"),
    ("eido/normativa/Instrucion_gastos_tribunais_teses.pdf", "Instrución xerencial sobre gastos nos tribunais de teses"),
    ("eido/normativa/Convocatoria_reconocimiento_actividades.pdf", "Convocatoria de recoñecemento de actividades formativas de doutoramento"),
    ("teses/guia/EIDO_Guia_solicitude_deposito_tese.pdf", "Guía para a solicitude de depósito da tese"),
    ("teses/guia/EIDO_Normas_de_estilo_tese.pdf", "Normas de estilo para a presentación de teses de doutoramento"),
]
index = []
outdir = ROOT / "normativa" / "eido"
(outdir / "_originales").mkdir(parents=True, exist_ok=True)
for path, title in DOCS:
    fn = path.rsplit("/", 1)[1]
    data = download(BASE + path)
    text = to_text(data)
    (outdir / "_originales" / fn).write_bytes(data)
    out = outdir / (fn.rsplit(".", 1)[0].lower().replace("_", "-") + ".md")
    write_norm(out, {"titulo": title, "ambito": "Escola Internacional de Doutoramento (EIDO)", "fuente": PAGE, "url_documento": BASE + path,
                     "original_local": f"normativa/eido/_originales/{fn}", "estado_fuente": "publicado en la web de la EIDO (sin marca oficial de vigencia; la fecha está en el propio texto)",
                     "sin_texto": "SI (PDF escaneado: sin capa de texto, hace falta OCR)" if len(text) < 300 else ""}, text)
    print(f"{len(text):>8} chars  {out.name}")
    index.append({"file": str(out.relative_to(ROOT)), "titulo": title, "chars": len(text)})
json.dump(index, open(ROOT / "data" / "eido_index.json", "w"), ensure_ascii=False, indent=1)
