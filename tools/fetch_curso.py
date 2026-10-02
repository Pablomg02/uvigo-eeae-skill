#!/usr/bin/env python3
"""Descarga el calendario académico y las fechas de exames da EEAE do curso indicado (CURSO), comúns a todo o profesorado.

As guías docentes non se descargan aquí: cada materia baixa baixo demanda con `guia.py`.
Cada curso: cambia CURSO e executa este script.
"""
import json
import sys
from pathlib import Path
SKILL = Path(__file__).resolve().parent.parent / "skills" / "normativa-uvigo-eeae"
sys.path.insert(0, str(SKILL / "scripts"))
from lib import ROOT, download, to_text, write_norm

CURSO = "2026_27"
EEAE = "https://aero.uvigo.es/docs/docencia/"
ANO = CURSO.replace("_", "-20")  # 2026_27 -> 2026-2027 (só para títulos)
CENTRO = [  # (ruta, título, página onde se publica)
    (f"calendario/Calendario_EEAE_{CURSO.replace('_', '-')}.pdf", f"Calendario académico da EEAE {ANO}", "https://aero.uvigo.es/gl/docencia/calendario-academico"),
    (f"exames/Exames_Aero_{CURSO.replace('_', '-')}.pdf", f"Calendario de exames do Grao en Enxeñaría Aeroespacial {ANO}", "https://aero.uvigo.es/gl/docencia/exames"),
]

out_dir = ROOT / "normativa" / "curso"
orig = out_dir / "_originales"
orig.mkdir(parents=True, exist_ok=True)
for old in list(out_dir.glob("calendario-*.md")) + list(out_dir.glob("exames-*.md")):
    old.unlink()  # só o curso actual
index = []


def save(data, fn, meta):
    (orig / fn).write_bytes(data)
    text = to_text(data)
    out = out_dir / (fn.rsplit(".", 1)[0].lower().replace("_", "-") + ".md")
    write_norm(out, {**meta, "curso": ANO, "original_local": f"normativa/curso/_originales/{fn}",
                     "sin_texto": "SI (PDF escaneado: sin capa de texto)" if len(text) < 300 else ""}, text)
    print(f"{len(text):>8} chars  {out.name}")
    index.append({"file": str(out.relative_to(ROOT)), "titulo": meta["titulo"], "chars": len(text)})


for ruta, titulo, pagina in CENTRO:
    save(download(EEAE + ruta), ruta.rsplit("/", 1)[1], {"titulo": titulo, "ambito": "Escola (EEAE)", "fuente": pagina, "url_documento": EEAE + ruta,
                                                         "estado_fuente": "publicado en la web del centro; puede corregirse durante el curso"})
json.dump(index, open(ROOT / "data" / "curso_index.json", "w"), ensure_ascii=False, indent=1)
