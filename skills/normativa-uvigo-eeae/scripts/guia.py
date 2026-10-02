#!/usr/bin/env python3
"""Baja de DOCNET la guía docente de una materia de la EEAE y la imprime (no se guarda en el corpus).

Uso:
  python3 guia.py "sistemas de propulsion"            # busca por nombre en todas las titulaciones de la EEAE
  python3 guia.py O07G410V01945                       # o por código
  python3 guia.py propulsion --curso 2025_26          # otro curso (por defecto, el vigente según la fecha)
  python3 guia.py --lista [--titulacion O07G410V01]   # materias de una titulación (o de todas)
  python3 guia.py propulsion --grep "avaliación global"   # solo los párrafos que contienen el texto
"""
import argparse, html, re, sys, unicodedata
from datetime import date
from lib import download, pdf_to_text

BASE = "https://secretaria.uvigo.gal/docnet-nuevo/"
CENTRO = "107"  # Escola de Enxeñaría Aeronáutica e do Espazo
TITULACIONES = {"O07G410V01": "Grao en Enxeñaría Aeroespacial", "O07M197V01": "Máster Universitario en Enxeñería Aeronáutica",
                "O07M189V01": "Máster Universitario en Sistemas Aéreos non Tripulados"}
SECCIONES = re.compile(r"^(DATOS IDENTIFICATIVOS|Resultados de Formación e Aprendizaxe|Contidos|Planificación|Metodoloxía docente|Atención personalizada|"
                       r"Avaliación|Outros comentarios sobre a Avaliación|Bibliografía\. Fontes de información|Recomendacións)$", re.M)


def norm(s):
    return re.sub(r"[^a-z0-9 ]+", " ", unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower())


def curso_vigente():
    y = date.today().year if date.today().month >= 9 else date.today().year - 1
    return f"{y}_{str(y + 1)[2:]}"


def get(url):
    return download(url).decode("latin-1")


def materias(tit, curso):
    h = get(f"{BASE}guia_docent/?centre={CENTRO}&ensenyament={tit}&consulta=assignatures&any_academic={curso}&idioma=gal")
    return [(c, html.unescape(n).strip(), tit) for c, n in re.findall(r"assignatura=([A-Z0-9]+)[^\"]*\"[^>]*>([^<]+)", h)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("consulta", nargs="?", help="nombre (o parte) o código de la materia")
    ap.add_argument("--curso", default=curso_vigente(), help="formato 2026_27")
    ap.add_argument("--titulacion", help="código de titulación (por defecto, todas las de la EEAE)")
    ap.add_argument("--lista", action="store_true")
    ap.add_argument("--grep", help="solo los párrafos que contengan este texto")
    a = ap.parse_args()
    tits = [a.titulacion] if a.titulacion else list(TITULACIONES)
    todas = [m for t in tits for m in materias(t, a.curso)]
    if a.lista or not a.consulta:
        for c, n, t in todas:
            print(f"{c}  {n}  [{t}]")
        return
    q = norm(a.consulta).split()
    hits = [m for m in todas if a.consulta.upper() == m[0] or all(w in norm(m[1]) for w in q)]
    if not hits:
        sys.exit(f"Sin materia que coincida con «{a.consulta}» en {a.curso}. Prueba --lista o --curso.")
    nq = " ".join(q)
    exactas = [m for m in hits if " ".join(norm(m[1]).split()) == nq or " ".join(norm(m[1]).split()).endswith(": " + nq)]
    hits = exactas if len(exactas) == 1 else hits
    if len(hits) > 1:
        print("Varias coinciden; repite con el código:")
        for c, n, t in hits:
            print(f"{c}  {n}  [{t}]")
        return
    cod, nome, tit = hits[0]
    page = f"{BASE}guia_docent/?centre={CENTRO}&ensenyament={tit}&assignatura={cod}&any_academic={a.curso}&idioma=gal"
    pid = re.search(r"pdf_assig=(\d+)", get(page)).group(1)
    url = f"{BASE}docencia/guia_docent/pdf/?pdf=Y&pdf_assig={pid}&pdf_any_academic={a.curso}&idioma=gal"
    text = SECCIONES.sub(lambda m: "## " + m.group(1), pdf_to_text(download(url)))
    print(f"# Guía docente {a.curso.replace('_', '-')}: {nome} ({cod})\nFuente: {page}\nPDF: {url}\n")
    if a.grep:
        g = norm(a.grep).strip()
        text = "\n\n".join(p for p in re.split(r"\n\s*\n", text) if g in norm(p)) or f"(sin párrafos con «{a.grep}»)"
    print(text)


main()
