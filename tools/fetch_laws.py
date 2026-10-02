#!/usr/bin/env python3
"""Descarga la legislación estatal/autonómica de la que depende la normativa de la UVigo.

Fuente: API de datos abiertos del BOE (legislación consolidada). Para cada bloque (artículo,
disposición...) el BOE guarda todas las versiones históricas; aquí se conserva la última, que es
la vigente en la fecha de descarga. Los metadatos incluyen la fecha de actualización del BOE y el
estado de derogación, para que la skill pueda avisar si un texto está desfasado.
"""
import html, json, re, sys, urllib.request
from pathlib import Path
SKILL = Path(__file__).resolve().parent.parent / "skills" / "normativa-uvigo-eeae"
sys.path.insert(0, str(SKILL / "scripts"))
from lib import ROOT, write_norm, slug

API = "https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{}/{}"

# (id BOE, clave corta, ámbito, por qué importa a un profesor contratado)
LAWS = [
    ("BOE-A-2023-7500", "losu", "estatal", "Ley Orgánica del Sistema Universitario: figuras de PDI contratado, derechos, deberes, dedicación, acceso."),
    ("BOE-A-2015-11719", "ebep", "estatal", "Estatuto Básico del Empleado Público: deberes, código de conducta, régimen disciplinario, permisos, aplicable también al personal laboral."),
    ("BOE-A-2015-11430", "estatuto-trabajadores", "estatal", "Estatuto de los Trabajadores: jornada, contratos, permisos, extinción, supletorio del convenio."),
    ("BOE-A-1985-151", "incompatibilidades", "estatal", "Ley 53/1984 de incompatibilidades del personal al servicio de las AAPP (actividad privada, segunda actividad pública)."),
    ("BOE-A-2015-10565", "lpac", "estatal", "Procedimiento administrativo común: plazos, notificaciones, recursos, abstención y recusación."),
    ("BOE-A-2015-10566", "lrjsp", "estatal", "Régimen jurídico del sector público: órganos colegiados (actas, convocatorias, quórum), abstención."),
    ("BOE-A-2018-16673", "lopdgdd", "estatal", "Protección de datos y derechos digitales (incluye desconexión digital, art. 88)."),
    ("BOE-A-1996-8930", "propiedad-intelectual", "estatal", "Texto refundido de la Ley de Propiedad Intelectual (obras docentes, materiales, autoría)."),
    ("BOE-A-2023-4513", "ley-informantes", "estatal", "Protección de las personas que informan sobre infracciones (canal interno de la UVigo)."),
    ("BOE-A-2007-6115", "ley-igualdad", "estatal", "Ley Orgánica de igualdad efectiva de mujeres y hombres (acoso sexual y por razón de sexo)."),
    ("BOE-A-2022-2978", "ley-convivencia-universitaria", "estatal", "Ley de convivencia universitaria (régimen disciplinario del estudiantado, deberes del PDI)."),
    ("BOE-A-2021-15781", "rd-822-2021-ordenacion-ensenanzas", "estatal", "Organización de las enseñanzas universitarias y aseguramiento de su calidad (créditos, TFG/TFM, planes de estudio)."),
    ("BOE-A-2010-20147", "rd-1791-2010-estatuto-estudiante", "estatal", "Estatuto del Estudiante Universitario: derechos del alumnado que el profesor debe respetar (evaluación, revisión, tutorías)."),
    ("BOE-A-1989-21967", "rd-1086-1989-retribuciones", "estatal", "Retribuciones del profesorado universitario (complementos, sexenios)."),
    ("BOE-A-2011-2541", "rd-99-2011-doctorado", "estatal", "Enseñanzas oficiales de doctorado (dirección de tesis, tutoría, comisión académica)."),
    ("BOE-A-2019-3700", "rd-103-2019-epif", "estatal", "Estatuto del personal investigador predoctoral en formación: contrato predoctoral, docencia máxima (art. 4), derechos y deberes."),
    ("BOE-A-2011-9617", "ley-ciencia", "estatal", "Ley 14/2011 de la Ciencia, la Tecnología y la Innovación: contratos predoctorales y postdoctorales (arts. 20–23), personal investigador."),
    ("BOE-A-2013-7911", "lei-6-2013-sistema-universitario-galicia", "autonómico", "Ley 6/2013 del Sistema universitario de Galicia (pendiente de adaptación a la LOSU)."),
]


def fetch(boe_id, what):
    req = urllib.request.Request(API.format(boe_id, what), headers={"Accept": "application/xml", "User-Agent": "normativa-uvigo-eeae skill"})
    return urllib.request.urlopen(req, timeout=120).read().decode("utf-8")


def ultima_modificacion(boe_id):
    """Fecha (AAAAMMDD) del bloque modificado más recientemente en el texto consolidado."""
    return max(re.findall(r"<fecha_actualizacion>(\d{8})", fetch(boe_id, "texto/indice")), default="")


def tag(x, name):
    m = re.search(rf"<{name}[^>]*>(.*?)</{name}>", x, flags=re.S)
    return html.unescape(m.group(1)).strip() if m else ""


def strip(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def body_text(xml):
    lines = []
    for bloque in re.findall(r"<bloque [^>]*>.*?</bloque>", xml, flags=re.S):
        tipo = re.search(r'tipo="(\w+)"', bloque).group(1)
        if tipo in ("nota_inicial", "firma"):
            continue
        versions = re.findall(r"<version [^>]*>(.*?)</version>", bloque, flags=re.S)
        if not versions:
            continue
        for cls, p in re.findall(r'<p class="([^"]+)"[^>]*>(.*?)</p>', versions[-1], flags=re.S):
            p = strip(p)
            if not p:
                continue
            if cls in ("articulo",):
                lines += ["", f"## {p}"]
            elif cls.startswith(("titulo", "capitulo", "libro", "seccion", "centro")) or cls in ("disposicion", "anexo_num", "anexo_tit"):
                lines += ["", f"# {p}"]
            else:
                lines.append(p)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


if __name__ == "__main__":
    index = []
    for boe_id, key, ambito, why in LAWS:
        meta_xml = fetch(boe_id, "metadatos")
        titulo = tag(meta_xml, "titulo")
        text = body_text(fetch(boe_id, "texto"))
        sub = "galicia" if ambito == "autonómico" else "estatal"
        out = ROOT / "normativa" / sub / f"{key}.md"
        meta = {
            "titulo": titulo,
            "ambito": ambito,
            "id_boe": boe_id,
            "fecha_disposicion": tag(meta_xml, "fecha_disposicion"),
            # fecha de la última modificación real del texto (la de los metadatos cambia aunque el texto no cambie)
            "boe_actualizado": ultima_modificacion(boe_id),
            "derogada": tag(meta_xml, "estatus_derogacion"),
            "fuente": tag(meta_xml, "url_html_consolidada"),
            "relevancia": why,
        }
        write_norm(out, meta, text)
        print(f"{len(text):>9} chars  {key:45} {titulo[:70]}")
        index.append({"file": str(out.relative_to(ROOT)), **meta, "chars": len(text)})
    json.dump(index, open(ROOT / "data" / "laws_index.json", "w"), ensure_ascii=False, indent=1)
