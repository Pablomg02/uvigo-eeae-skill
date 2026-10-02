#!/usr/bin/env python3
"""Descarga y convierte a texto las normas de la UVigo seleccionadas del portal de Secretaría.

Requiere data/catalog.json (generado por crawl_portal.py). La selección está aquí, en claro,
para poder auditarla y ampliarla. Solo se descargan normas con estado "Validada".
"""
import json, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
SKILL = Path(__file__).resolve().parent.parent / "skills" / "normativa-uvigo-eeae"
sys.path.insert(0, str(SKILL / "scripts"))
from lib import ROOT, download, slug, to_text, write_norm, kind_of
from sede_dl import fetch_attachments
import tempfile, os

# Categorías del portal que se incluyen completas (si la norma está Validada y tiene documento).
CATEGORIAS = ("Persoal docente e investigador", "Docencia", "Ordenación académica", "Estatutos da Universidade de Vigo", "Estudantes")

# Normas sueltas de otras categorías que importan a un profesor de la EEAE que investiga o hace el doctorado
# (doctorado, investigación, viajes, igualdad, datos, convivencia). Gobierno interno y trámites de gestión, fuera.
EXTRA = {
    # organización
    616: "Delegación de competencias", 267: "Estatutos", 41: "EIDO (regulamento de réxime interno)",
    # doctorado
    625: "Regulamento de estudos de doutoramento",
    # investigación y transferencia
    684: "Contratación persoal investigador", 621: "Contratación traballos art. 83 LOSU/LOU", 619: "Recursos liberados proxectos",
    497: "Comité ética seres humanos", 458: "Comité ética investigación", 413: "Persoal investigador visitante", 366: "Grupos e centros de investigación",
    215: "Creación de empresas", 213: "Propiedade industrial e intelectual", 433: "Sinatura científica", 147: "Xestión contratos art. 83 LOU",
    140: "Congresos internacionais", 556: "Trienios persoal investigador", 633: "Complementos axudas RRHH", 680: "Modifica instrución 7/2024",
    # viajes y gastos
    328: "Indemnizacións por razón de servizo 2019", 234: "Anexos indemnizacións", 526: "Importes máximos dietas", 246: "Ordes de comisión dixitais",
    244: "Gastos viaxes autorización", 315: "Contratación servizos viaxes",
    # condiciones de trabajo
    355: "Retribucións en IT", 522: "Reforma laboral", 523: "Réxime transitorio reforma laboral", 271: "Reordenación de horarios",
    96: "Medidas igualdade e conciliación", 94: "II Plan de Igualdade", 106: "Plan de prevención de riscos", 435: "Servizos a tempo parcial en empresas",
    # datos, convivencia, ética, TIC, lingua
    560: "Protección de datos", 118: "RGPD", 715: "Protocolo cambio nome/xénero", 673: "Protocolo acoso sexual", 656: "Canle interna de información",
    569: "Normas de convivencia", 567: "Réxime disciplinario estudantado", 566: "Código ético", 423: "Valedor/a universitaria", 62: "Uso de recursos informáticos",
    56: "Uso da lingua galega", 595: "PIUNE correo corporativo", 697: "Medios electrónicos propios (estudantado)",
    700: "Prácticas académicas externas (instrucións)", 701: "Prácticas formativas inversas",
}

# Fuera aunque encajen en una categoría: duplicados, superados, de otro colectivo o sin relación con la docencia en la EEAE.
EXCLUIR = {
    482, 491, 493, 494,          # escudo; listados 2021 de contratado doctor interino
    322, 323, 329, 330,          # suplemento europeo al título
    293, 291, 292, 333, 309,     # títulos, validación de estudios extranjeros, premios extraordinarios
    259, 571, 575,               # reorganización doutoramento (antigua); certificaciones; prórroga plans internacionalización
    320,                         # RD 1393/2007: derogado por RD 822/2021 (se descarga el RD 822/2021 desde el BOE)
    321,                         # RD 99/2011: se descarga la versión consolidada del BOE
    452, 461, 705, 670, 669, 654, 562, 520, 612, 580, 703, 712, 713,  # CEUVI, duplicado ES, institutos y centros de investigación
    719,                         # unidades docentes de Medicina (USC)
    # poda 2026-10: trámites de estudiantes que no decide el profesor
    211, 407, 721, 688, 430, 524, 543, 682, 696,  # libre mobilidade, simultaneidade, certificacións, carácter singular, matrícula condicionada, admisión, créditos por participación
    # poda 2026-10: solo funcionarios, carrera ajena o normas COVID/versiones viejas
    272, 489, 511, 540,          # xestión económica corpos docentes, PCD interinos a TU, eméritos, xubilación de funcionarios
    418, 443, 373,               # COVID (vulnerables, prórroga); axudante doutor 2020 (superada por 451)
    610, 664, 542, 647, 649,     # POD 2024/25 e 2025/26, dedicación 2023-25, convocatorias de docencia en lingua estranxeira anteriores a 695
}

# Entradas del portal sin archivo adjunto cuyo texto está en la sede electrónica (tablón): id -> id_taskdata de la sede.
SEDE = {709: "49251770"}


_TRAD = re.compile(r"castell|castel[aá]n|_cast|espa[nñ]ol|english|ingl[eé]s|portugu|_port|_es$|_en$|\ben$", re.I)


def es_traduccion(titulo_doc):
    """Heurística: copia en otro idioma de una norma (el nombre del documento empieza o acaba por el idioma)."""
    t = titulo_doc.strip()
    return bool(_TRAD.search(t[:20]) or _TRAD.search(t[-22:]))


def selected(catalog):
    out = {}
    for x in catalog:
        if x["estado"] != "Validada" or x["id"] in EXCLUIR:
            continue
        cat = x.get("categoria") or ""
        if x["id"] in EXTRA or any(k in cat for k in CATEGORIAS):
            if x["docs"] or x["id"] in SEDE:
                out[x["id"]] = x
    return out


def process(args):
    x, inv = args
    base = ROOT / "normativa" / "uvigo"
    docs = x["docs"]
    results = []
    if not docs and x["id"] in SEDE:
        with tempfile.TemporaryDirectory() as td:
            for fn, size, ct in fetch_attachments(SEDE[x["id"]], td):
                if fn.startswith("j_idt"):
                    continue
                docs.append({"titulo": fn, "bytes": open(os.path.join(td, fn), "rb").read(), "url": f"https://sede.uvigo.gal/public/bulletin/bulletin-details.xhtml?idtaskdata={SEDE[x['id']]}"})
    for n, d in enumerate(docs, 1):
        if len(docs) > 1 and es_traduccion(d["titulo"]):
            continue  # copia en otro idioma: mismo articulado que la versión principal, no se guarda
        try:
            data = d.get("bytes") or download(d["url"])
        except Exception as e:
            results.append({"id": x["id"], "error": str(e), "doc": d["titulo"]})
            continue
        text = to_text(data)
        name = f"{x['id']:03d}-{slug(x['titulo'], 55)}" + (f"-doc{n}" if len(docs) > 1 else "")
        # Se conserva siempre el original: pdftotext aplana las tablas y los PDF escaneados no tienen texto.
        ext = {"pdf": "pdf", "docx": "docx", "doc": "doc"}.get(kind_of(data), "bin")
        (base / "_originales").mkdir(exist_ok=True)
        (base / "_originales" / f"{name}.{ext}").write_bytes(data)
        pdf_local = f"normativa/uvigo/_originales/{name}.{ext}"
        meta = {
            "original_local": pdf_local,
            "titulo": x["titulo"], "titulo_documento": d["titulo"], "id_portal": x["id"], "ambito": x["rango"], "tipo": x["tipo"],
            "servizo": x["servizo"], "categoria": x["categoria"], "estado_portal": x["estado"], "observacions": x["observacions"], "periodo": x["periodo"],
            "url_portal": f"https://secretaria.uvigo.gal/uv/web/normativa/public/show/{x['id']}", "url_documento": d["url"],
            "diarios": "; ".join(x.get("diarios") or []), "sede": "; ".join(x.get("sede") or []),
            "deroga_a": "; ".join(f"{r['id']}" for r in x["relacionadas"] if r["relacion"].startswith("Deroga")),
            "modifica_a": "; ".join(f"{r['id']}" for r in x["relacionadas"] if r["relacion"].startswith("Modifica")),
            "derogada_por": "; ".join(str(i) for i in inv.get(x["id"], [])),
            "formato": kind_of(data),
            "sin_texto": "SI (PDF escaneado: sin capa de texto, hace falta OCR)" if len(text) < 300 else "",
        }
        write_norm(base / f"{name}.md", meta, text)
        results.append({"id": x["id"], "file": f"normativa/uvigo/{name}.md", "original": pdf_local, "chars": len(text), "titulo": x["titulo"], "doc": d["titulo"], "categoria": x["categoria"], "ambito": x["rango"]})
    return results


if __name__ == "__main__":
    catalog = json.load(open(ROOT / "data" / "catalog.json"))
    inv = {}
    for x in catalog:
        for r in x["relacionadas"]:
            if r["relacion"].startswith("Deroga"):
                inv.setdefault(r["id"], []).append(x["id"])
    sel = selected(catalog)
    print(len(sel), "normas seleccionadas", file=sys.stderr)
    out = []
    with ThreadPoolExecutor(4) as ex:
        for r in ex.map(process, [(x, inv) for x in sel.values()]):
            out += r
    json.dump(out, open(ROOT / "data" / "uvigo_index.json", "w"), ensure_ascii=False, indent=1)
    bad = [r for r in out if "error" in r or r["chars"] < 300]
    print(f"OK {len(out)} documentos; problemas: {len(bad)}")
    for r in bad:
        print("  PROBLEMA", r)
