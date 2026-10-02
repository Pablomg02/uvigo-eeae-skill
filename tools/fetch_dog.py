#!/usr/bin/env python3
"""Descarga disposiciones del DOG (Diario Oficial de Galicia) que no están en el BOE:
convenio colectivo del PDI laboral y sus actas/adaptaciones."""
import html, json, re
import sys
from pathlib import Path
SKILL = Path(__file__).resolve().parent.parent / "skills" / "normativa-uvigo-eeae"
sys.path.insert(0, str(SKILL / "scripts"))
from lib import ROOT, download, write_norm

# (url html, clave, título, fecha publicación, nota sobre su papel)
DOCS = [
    ("https://www.xunta.gal/dog/Publicados/2011/20110414/Anuncio11926_es.html", "convenio-pdi-laboral-ii-2011",
     "II Convenio colectivo para el personal docente e investigador laboral de las universidades de A Coruña, Santiago de Compostela y Vigo (DOG 74, 14/04/2011)", "2011-04-14",
     "Texto base del convenio. Léelo siempre junto con el acta de 2025, que adapta parte de su contenido a la LOSU."),
    ("https://www.xunta.gal/dog/Publicados/2025/20250314/AnuncioG0767-280225-0004_gl.html", "convenio-pdi-laboral-acta-paritaria-2025-02-07",
     "Acta de la Comisión Paritaria del II Convenio PDI laboral (7/02/2025) para adaptarlo a los cambios normativos (DOG 51, 14/03/2025)", "2025-03-14",
     "Modifica/adapta el texto de 2011 (LOSU, conciliación, igualdad). Prevalece sobre el texto de 2011 en lo que lo modifique."),
    ("https://www.xunta.gal/dog/Publicados/2025/20250314/AnuncioG0767-280225-0002_gl.html", "convenio-pdi-laboral-acordo-xubilacion-2025",
     "Acuerdo de la Comisión Negociadora del II Convenio PDI laboral para la recuperación de la cláusula de jubilación (DOG 51, 14/03/2025)", "2025-03-14",
     "Recupera la cláusula de jubilación (art. 42 del convenio, que había decaído por la reforma laboral de 2012)."),
]


def extract(h):
    i = h.find('class="story"')
    h = h[h.find(">", i) + 1:] if i >= 0 else h
    for end in ("Ver referencia pdf", "© Xunta de Galicia", "Ver referencia"):
        j = h.find(end)
        if j > 0:
            h = h[:j]
            break
    h = re.sub(r"<script.*?</script>|<style.*?</style>", "", h, flags=re.S)
    h = re.sub(r"</(p|div|h\d|li|tr|table)>|<br\s*/?>", "\n", h)
    t = html.unescape(re.sub(r"<[^>]+>", "", h))
    return re.sub(r"\n\s*\n+", "\n\n", re.sub(r"[ \t]+", " ", t)).strip()


if __name__ == "__main__":
    idx = []
    for url, key, titulo, fecha, nota in DOCS:
        text = extract(download(url).decode("utf-8", "replace"))
        out = ROOT / "normativa" / "galicia" / f"{key}.md"
        write_norm(out, {"titulo": titulo, "ambito": "autonómico (DOG)", "fecha_publicacion": fecha, "fuente": url, "relevancia": nota}, text)
        print(f"{len(text):>8} chars  {key}")
        idx.append({"file": str(out.relative_to(ROOT)), "titulo": titulo, "fecha_publicacion": fecha, "fuente": url, "relevancia": nota, "chars": len(text)})
    json.dump(idx, open(ROOT / "data" / "dog_index.json", "w"), ensure_ascii=False, indent=1)
