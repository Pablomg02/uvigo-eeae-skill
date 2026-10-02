#!/usr/bin/env python3
"""Buscador de normativa (BM25 sobre fragmentos por artículo), tolerante a gallego/castellano y a tildes.

Uso:
  buscar.py "vacaciones profesorado contratado"            # mejores fragmentos de toda la normativa
  buscar.py "tribunal tfg" --ambito eeae -n 5              # solo normas de la Escola
  buscar.py "permiso lactancia" --ambito estatal,galicia
  buscar.py --ver 512-regulamento-de-profesorado --art 12  # leer un artículo concreto completo
  buscar.py --ver convenio-pdi-laboral-ii-2011 --art 30
  buscar.py --lista [--ambito uvigo]                        # qué documentos hay

Cada resultado indica documento, artículo, ámbito, estado y fuente, para poder citarlo.
Por defecto oculta lo marcado como histórico/superado en data/curated.json (usa --historicas para verlo).
"""
import argparse, json, math, re, sys, unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NORMATIVA = ROOT / "normativa"
AMBITOS = {"curso": "curso", "uvigo": "uvigo", "eeae": "eeae", "eido": "eido", "estatal": "estatal", "galicia": "galicia"}

# Equivalencias castellano -> gallego (y variantes) para que una pregunta en castellano encuentre texto en gallego.
SINONIMOS = {
    "vacaciones": ["vacacions", "vacacións"], "tutorias": ["titorias", "titorías"], "tutoria": ["titoria"], "examen": ["exame", "exames"],
    "examenes": ["exames"], "calificacion": ["cualificacion"], "calificaciones": ["cualificacions"], "evaluacion": ["avaliacion"],
    "asignatura": ["materia"], "asignaturas": ["materias"], "profesor": ["profesorado", "docente"], "profesores": ["profesorado"],
    "baja": ["baixa"], "permiso": ["licenza", "permiso"], "permisos": ["licenzas", "permisos"], "contrato": ["contrato", "contratacion"],
    "contratado": ["contratado", "contratacion"], "horas": ["horas"], "horario": ["horario", "horarios"], "reunion": ["reunion", "sesion"],
    "convocatoria": ["convocatoria", "convocatorias"], "trabajo": ["traballo"], "fin": ["fin"], "grado": ["grao"], "master": ["mestrado", "master"],
    "jubilacion": ["xubilacion"], "ano": ["ano"], "acoso": ["acoso"], "datos": ["datos"], "docencia": ["docencia"], "plazo": ["prazo"],
    "plazos": ["prazos"], "recurso": ["recurso", "recursos"], "revision": ["revision"], "reclamacion": ["reclamacion"], "actas": ["actas", "acta"],
    "estudiantes": ["estudantes", "estudantado"], "alumnos": ["estudantes", "estudantado"], "alumno": ["estudante"], "departamento": ["departamento"],
    "sustituto": ["substituto"], "sustitucion": ["substitucion"], "sustituir": ["substituir"], "ayudante": ["axudante"], "asociado": ["asociado"],
    "guia": ["guia"], "docente": ["docente"], "dedicacion": ["dedicacion"], "reconocimiento": ["recoñecemento", "reconocimiento"],
    "viaje": ["viaxe"], "viajes": ["viaxes"], "gastos": ["gastos"], "dietas": ["dietas"], "incompatibilidad": ["incompatibilidade"],
    "cargo": ["cargo"], "ausencia": ["ausencia", "ausencias"], "falta": ["falta", "faltas"], "enfermedad": ["enfermidade"], "maternidad": ["maternidade"],
    "paternidad": ["paternidade"], "lactancia": ["lactancia"], "conciliacion": ["conciliacion"], "teletrabajo": ["teletraballo"], "jornada": ["xornada"],
    "tesis": ["tese"], "doctorado": ["doutoramento"], "doctor": ["doutor"], "investigacion": ["investigacion"], "propiedad": ["propiedade"],
    "intelectual": ["intelectual"], "idioma": ["lingua"], "lengua": ["lingua"], "gallego": ["galego"], "ingles": ["ingles", "estranxeira"],
    "practicas": ["practicas"], "beca": ["bolsa", "beca"], "sancion": ["sancion"], "disciplinario": ["disciplinario"], "queja": ["queixa"],
    "quejas": ["queixas"], "sugerencias": ["suxestions"], "tribunal": ["tribunal"], "comision": ["comision"], "claustro": ["claustro"],
    "conservar": ["custodia", "conservar"], "guardar": ["custodia", "conservar"], "grabar": ["gravar", "gravacion"], "grabacion": ["gravacion"],
    "movil": ["mobil", "dispositivos"], "moviles": ["mobiles", "dispositivos"], "notas": ["cualificacions", "notas"], "nota": ["cualificacion"],
    "copiar": ["fraude", "copia"], "copia": ["fraude", "copia"], "plagio": ["plaxio", "orixinalidade"], "fecha": ["data"], "fechas": ["datas"],
    "cierre": ["peche"], "nombre": ["nome"], "alumnado": ["estudantado"], "cuatrimestre": ["cuadrimestre"], "clase": ["clase", "sesion"],
    "clases": ["clases", "sesions"], "cambiar": ["modificar", "cambio"], "suspender": ["suspenso"], "aprobar": ["superar", "aprobar"],
    "junta": ["xunta"], "director": ["director", "directora"], "secretario": ["secretario", "secretaria"], "voto": ["voto"], "quorum": ["quorum"],
}
STOP = set("de la el los las un una unos unas y o u e en a al del por para con sin sobre que se su sus lo le les es son ser como mas pero si no ni da do das dos os as na nas no nos ao aos polo pola polos polas".split())
PREFIX = 6


def fold(s):
    return unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode()


def stems(text):
    return [w[:PREFIX] for w in re.findall(r"[a-z0-9]+", fold(text)) if w not in STOP and len(w) > 1]


def expand(query):
    out = []
    for w in re.findall(r"[a-z0-9]+", fold(query)):
        if w in STOP:
            continue
        out.append(w[:PREFIX])
        for syn in SINONIMOS.get(w, []):
            out.append(fold(syn)[:PREFIX])
    return out


def read_doc(path):
    raw = path.read_text(errors="replace")
    meta, body = {}, raw
    if raw.startswith("---\n"):
        head, _, body = raw[4:].partition("\n---\n")
        for line in head.splitlines():
            k, _, v = line.partition(": ")
            meta[k.strip()] = v.strip().strip("'")
    return meta, body


HEAD = re.compile(r"^(#{1,3} .+|Art(?:igo|ículo|\.)\s*\d+[ºª°]?.*|Artículo único.*|Disposici[óo]n .+|DISPOSICI[ÓO]N .+|ANEXO.*|Anexo.*|T[ÍI]TULO.*|CAP[ÍI]TULO.*|Cap[ií]tulo.*|Secci[óo]n.*)$")


def chunks(body, maxlen=1800):
    """Divide el texto en fragmentos que empiezan en cada artículo/disposición y no pasan de ~maxlen caracteres."""
    cur_head, buf, out = "(inicio)", [], []

    def flush():
        txt = "\n".join(buf).strip()
        while len(txt) > maxlen * 1.5:
            cut = txt.rfind("\n", 0, maxlen)
            cut = cut if cut > maxlen // 2 else maxlen
            out.append((cur_head, txt[:cut].strip()))
            txt = txt[cut:].strip()
        if txt:
            out.append((cur_head, txt))

    for line in body.splitlines():
        if HEAD.match(line.strip()) and not re.match(r"^#{1,3} (?:[IVX]+|FELIPE|REY)\b", line.strip()):
            flush()
            buf = [line]
            cur_head = line.lstrip("# ").strip()[:110]
        else:
            buf.append(line)
    flush()
    return out


def load_curated():
    p = ROOT / "data" / "curated.json"
    return json.loads(p.read_text()) if p.exists() else {}


def docs(ambitos=None):
    for amb in AMBITOS:
        if ambitos and amb not in ambitos:
            continue
        for p in sorted((NORMATIVA / amb).glob("*.md")):
            yield amb, p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="?")
    ap.add_argument("-n", type=int, default=8, help="número de fragmentos")
    ap.add_argument("--ambito", help="curso,uvigo,eeae,eido,estatal,galicia (separados por coma)")
    ap.add_argument("--historicas", action="store_true", help="incluir normas marcadas como históricas/superadas")
    ap.add_argument("--ver", help="nombre (o parte) del fichero a leer")
    ap.add_argument("--art", help="con --ver: número o texto del artículo/apartado")
    ap.add_argument("--lista", action="store_true")
    ap.add_argument("--layout", help="id o nombre de fichero: extrae del PDF ORIGINAL conservando columnas (para tablas e importes); usar con --grep")
    ap.add_argument("--grep", help="con --layout: texto a localizar en el PDF (sin distinguir tildes)")
    ap.add_argument("-C", type=int, default=30, help="con --layout: líneas de contexto tras cada coincidencia")
    ap.add_argument("--ancho", type=int, default=900, help="caracteres por fragmento mostrado")
    a = ap.parse_args()
    ambitos = set(a.ambito.split(",")) if a.ambito else None
    curated = load_curated()

    def status(meta, path):
        c = curated.get(meta.get("id_portal", "")) or curated.get(path.stem) or {}
        return c

    if a.lista:
        for amb, p in docs(ambitos):
            meta, body = read_doc(p)
            c = status(meta, p)
            sin = f" | SIN TEXTO: abrir {meta.get('original_local')}" if meta.get("sin_texto") else ""
            print(f"[{amb}] {p.stem}  | {meta.get('titulo','')[:90]} | {c.get('vigencia','')}{sin}")
        return

    if a.layout:
        import io, shutil, subprocess, tempfile, urllib.request
        if not a.grep:
            sys.exit("--layout necesita --grep 'texto a localizar'")
        if a.layout.isdigit():
            found = [(amb, p) for amb, p in docs(ambitos) if p.stem.startswith(f"{int(a.layout):03d}-")]
        else:
            found = [(amb, p) for amb, p in docs(ambitos) if a.layout in p.stem]
        found = [(amb, p) for amb, p in found if not read_doc(p)[0].get("traduccion")] or found
        for amb, p in found:
            meta, _ = read_doc(p)
            orig, url = meta.get("original_local") or "", meta.get("url_documento")
            if not orig.endswith(".pdf"):
                print(f"[{p.stem}] el original no es un PDF; usa --ver")
                continue
            if (ROOT / orig).exists():
                data = (ROOT / orig).read_bytes()
            else:  # la versión para la app de Claude solo lleva algunos originales: se descarga de la fuente
                try:
                    data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
                    orig = url
                except Exception as e:
                    print(f"[{p.stem}] sin PDF original local y no se pudo descargar ({e}); ábrelo en {url} o usa --ver")
                    continue
            if shutil.which("pdftotext"):
                with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
                    f.write(data); f.flush()
                    pages = subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True).stdout.decode("utf-8", "replace").split("\x0c")
            else:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(data)) as pdf:
                    pages = [pg.extract_text(layout=True) or "" for pg in pdf.pages]
            needle = fold(a.grep)
            n = 0
            for pi, page in enumerate(pages, 1):
                lines = page.splitlines()
                for li, line in enumerate(lines):
                    if needle in fold(line):
                        print(f"━━ [{p.stem}] {meta.get('titulo','')[:90]}  — PDF {orig}, página {pi}")
                        import textwrap
                        block = [l for l in lines[max(0, li - 2): li + a.C] if l.strip()]
                        print(textwrap.dedent("\n".join(block)))
                        print()
                        n += 1
                        break
                if n >= 3:
                    break
            if not n:
                print(f"[{p.stem}] «{a.grep}» no aparece en el PDF (¿escaneado? ¿otro término?)")
        return

    if a.ver:
        # número = id del portal (p. ej. 512; muestra todos los documentos de esa norma); texto = parte del nombre de fichero
        if a.ver.isdigit():
            found = [(amb, p) for amb, p in docs(ambitos) if p.stem.startswith(f"{int(a.ver):03d}-")]
        else:
            found = [(amb, p) for amb, p in docs(ambitos) if a.ver in p.stem]
            found = found[:1] if len(found) > 1 and not any(a.ver == p.stem for _, p in found) and len({p.stem.rsplit("-doc", 1)[0] for _, p in found}) > 1 else found
        if not found:
            sys.exit("No hay ningún fichero que contenga: " + a.ver)
        for amb, p in found:
            meta, body = read_doc(p)
            c = status(meta, p)
            print(f"# {meta.get('titulo')}  [{p.stem}]\n# documento: {meta.get('titulo_documento','')}\n# fuente: {meta.get('url_portal') or meta.get('fuente')}\n# original: {meta.get('original_local','')}\n# estado: {meta.get('estado_portal','')} {c.get('vigencia','')} {c.get('nota','')}\n")
            if not a.art:
                print(body + "\n")
                continue
            pat = re.compile(rf"^(?:#+\s*)?(?:Art(?:igo|ículo|\.)\s*)?{re.escape(a.art)}(?!\d)", re.I)
            heads = [h for h, t in chunks(body, 10**6)]
            shown = False
            for h, t in chunks(body, 10**6):
                if pat.match(h) or (a.art.lower() in h.lower() and len(a.art) > 3):
                    print(t + "\n")
                    shown = True
            if not shown:
                print("No se encontró ese artículo en este fichero. Encabezados disponibles (primeros 60):")
                for h in heads[:60]:
                    print("  ", h)
        return

    if not a.query:
        ap.error("falta la consulta")

    q = expand(a.query)
    if not q:
        sys.exit("Consulta vacía")
    corpus = []  # (amb, path, meta, head, text, tf, length)
    df = Counter()
    for amb, p in docs(ambitos):
        meta, body = read_doc(p)
        c = status(meta, p)
        if c.get("vigencia") in ("historica", "superada", "duplicada") and not a.historicas:
            continue
        if meta.get("traduccion"):  # copias en otro idioma de versiones antiguas del corpus
            continue
        for head, txt in chunks(body):
            toks = stems(head + " " + txt)
            tf = Counter(toks)
            corpus.append((amb, p, meta, head, txt, tf, len(toks)))
            for t in set(q):
                if t in tf:
                    df[t] += 1
    N = len(corpus) or 1
    avg = sum(c[6] for c in corpus) / N
    k1, b = 1.4, 0.75
    scored = []
    qset = set(q)
    for amb, p, meta, head, txt, tf, ln in corpus:
        s = 0.0
        for t in qset:
            if t in tf:
                idf = math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))
                s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * ln / avg))
        hits = sum(1 for t in qset if t in tf)
        s *= 1 + 0.35 * hits / max(len(qset), 1)  # premia los fragmentos que cubren más términos de la consulta
        if s > 0:
            scored.append((s, amb, p, meta, head, txt))
    scored.sort(key=lambda x: -x[0])
    seen, shown = set(), 0
    for s, amb, p, meta, head, txt in scored:
        key = (p, head)
        if key in seen:
            continue
        seen.add(key)
        c = status(meta, p)
        fecha = meta.get("observacions") or meta.get("fecha_aprobacion") or meta.get("fecha_publicacion") or meta.get("fecha_disposicion", "")
        print(f"━━ [{amb}] {meta.get('titulo','?')[:120]}")
        print(f"   {head}   (puntuación {s:.1f}; archivo: {p.stem})")
        flag = " ".join(x for x in [meta.get("estado_portal", ""), c.get("vigencia", ""), c.get("nota", "")] if x)
        print(f"   fecha/obs: {fecha[:100]} | estado: {flag or '—'}")
        if meta.get("sin_texto"):
            print("   ⚠ sin texto extraíble: abrir el original:", meta.get("original_local"))
        print("   " + txt[: a.ancho].replace("\n", "\n   "))
        print()
        shown += 1
        if shown >= a.n:
            break
    if not shown:
        print("Sin resultados. Prueba con sinónimos o términos más generales, y revisa references/huecos.md.")


if __name__ == "__main__":
    main()
