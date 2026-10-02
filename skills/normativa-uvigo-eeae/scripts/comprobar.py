#!/usr/bin/env python3
"""Comprueba EN DIRECTO, contra las fuentes oficiales, si la copia local de una norma sigue al día.

Uso:
  comprobar.py 565 709 losu convenio-pdi-laboral-ii-2011   # las normas que vas a citar (id del portal o nombre)
  comprobar.py --novedades                                 # normas nuevas en el portal, la EEAE y la EIDO; leyes del BOE modificadas

Qué mira según la fuente:
  UVigo (portal de Secretaría): estado (Validada/Anulada), documento sustituido y normas nuevas que la derogan o modifican.
  BOE: fecha de la última modificación del texto consolidado y si está derogada.
  EEAE / EIDO: si el PDF publicado ha cambiado o ha desaparecido.
  DOG: una publicación no cambia; lo que cambia el convenio son actas nuevas (búscalas en la web si importa).
Tarda unos segundos por norma. No modifica el corpus: si algo ha cambiado, actualiza con tools/actualizar.sh del repositorio.
"""
import argparse, hashlib, json, re, shutil, sys, urllib.error, urllib.request
from lib import ROOT, download, to_text
from buscar import docs, read_doc
import crawl_portal

BOE_API = "https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{}/{}"


def boe(boe_id, what):
    req = urllib.request.Request(BOE_API.format(boe_id, what), headers={"Accept": "application/xml", "User-Agent": "normativa-uvigo-eeae skill"})
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8")


def find(ref):
    """Devuelve la lista de (ámbito, ruta) de un id de portal o nombre de fichero."""
    if ref.isdigit():
        return [(a, p) for a, p in docs() if p.stem.startswith(f"{int(ref):03d}-")]
    exact = [(a, p) for a, p in docs() if p.stem == ref]
    return exact or [(a, p) for a, p in docs() if ref in p.stem]


def catalog():
    return {x["id"]: x for x in json.load(open(ROOT / "data" / "catalog.json"))}


def portal_nuevas(known):
    """Normas del portal con id que no está en el catálogo local (el listado sale ordenado de más nueva a más antigua)."""
    nuevas, page = [], 1
    while page <= 5:
        h = crawl_portal.get(f"{crawl_portal.BASE}/uv/web/normativa/public/?orderDir=DESC&page={page}")
        ids = [int(i) for i in dict.fromkeys(re.findall(r"public/show/(\d+)", h))]
        fresh = [i for i in ids if i not in known]
        nuevas += fresh
        if not ids or len(fresh) < len(ids):  # ya hemos llegado a normas conocidas
            break
        page += 1
    return [crawl_portal.detail(i) for i in nuevas]


def check_uvigo(pid, files, cat, nuevas):
    meta = read_doc(files[0][1])[0]
    d = crawl_portal.detail(pid)
    out = []
    if not d.get("titulo"):
        return [f"  ? no se pudo leer la ficha del portal (¿sin red?): verifícala con la herramienta web en {meta.get('url_portal')} o di que no se ha verificado en directo"]
    if d["estado"] != meta.get("estado_portal"):
        out.append(f"  ✗ CAMBIO DE ESTADO: local «{meta.get('estado_portal')}», ahora «{d['estado']}»")
    # se compara con todos los documentos del último rastreo (el corpus no guarda las copias traducidas)
    known_urls = {x["url"] for x in cat.get(pid, {}).get("docs", [])} or {read_doc(p)[0].get("url_documento") for _, p in files}
    live_urls = {x["url"] for x in d["docs"]}
    if live_urls and live_urls != known_urls:
        out.append("  ✗ El portal ofrece otro documento (texto sustituido o corregido): actualiza el corpus antes de citar.")
    if (d.get("observacions") or "") != (cat.get(pid, {}).get("observacions") or ""):
        out.append(f"  ! Observaciones cambiadas en el portal: {(d.get('observacions') or '')[:300]}")
    for n in nuevas:
        for r in n["relacionadas"]:
            if r["id"] == pid:
                out.append(f"  ✗ Norma nueva {n['id']} «{n['titulo'][:90]}» → {r['relacion']} esta norma")
    for r in d["relacionadas"]:
        if r["id"] not in cat:
            out.append(f"  ! Relación con una norma que no está en el catálogo local: {r['relacion']} {r['id']} «{r['titulo'][:80]}»")
    return out or [f"  ✓ sin cambios en el portal ({meta.get('url_portal')})"]


def check_boe(meta):
    bid = meta["id_boe"]
    m = boe(bid, "metadatos")
    last = max(re.findall(r"<fecha_actualizacion>(\d{8})", boe(bid, "texto/indice")), default="")
    out = []
    if re.search(r"<estatus_derogacion>S<", m):
        out.append("  ✗ El BOE la marca como DEROGADA")
    if re.search(r"<vigencia_agotada>S<", m):
        out.append("  ✗ El BOE la marca con vigencia agotada")
    if last and last > meta.get("boe_actualizado", ""):
        out.append(f"  ✗ Texto modificado en el BOE el {last} (copia local: {meta.get('boe_actualizado')}). Mira la versión vigente: {meta.get('fuente')}")
    return out or [f"  ✓ texto consolidado sin cambios desde {meta.get('boe_actualizado')} ({meta.get('fuente')})"]


def huellas():
    """Huellas de los PDF originales que no viajan en la versión para la app (las genera tools/huellas.py)."""
    p = ROOT / "data" / "huellas.json"
    return json.load(open(p)) if p.exists() else {}


def check_pdf(meta):
    url = meta.get("url_documento")
    if not url:
        return [f"  · no hay PDF que comparar (resumen propio o página web): consulta la fuente en línea ({meta.get('fuente')})"]
    try:
        data = download(url)
    except urllib.error.HTTPError as e:
        return [f"  ✗ El documento ya no está en {url} ({e}). Puede haberse sustituido: revisa {meta.get('fuente')}"]
    except Exception as e:
        return [f"  ? no se pudo comprobar (¿sin red? {e}); verifícalo con la herramienta web en {meta.get('fuente')} o di que no se ha verificado en directo"]
    if meta.get("sin_texto"):
        return ["  ? documento escaneado: no se puede comparar el texto"]
    local = ROOT / meta.get("original_local", "")
    sha = lambda b: hashlib.sha256(b).hexdigest()[:16]
    huella = huellas().get(meta.get("original_local"))
    # se compara con el texto del PDF original guardado (el .md puede llevar retoques, p. ej. cabeceras en las guías)
    if local.is_file():
        changed = to_text(data) != to_text(local.read_bytes())
    elif huella and sha(data) == huella["bytes"]:
        changed = False
    elif huella and shutil.which("pdftotext"):
        changed = sha(to_text(data).encode()) != huella["texto"]
    elif huella:  # sin el original ni pdftotext (versión de la app) no se puede comparar el texto
        return [f"  ? el PDF publicado no es idéntico byte a byte a la copia local y aquí no puedo comparar su texto: ábrelo ({url}) y contrasta lo que vayas a citar"]
    else:
        changed = sha(to_text(data).encode()) != meta.get("sha256_texto")
    if changed:
        return [f"  ✗ El PDF publicado ha cambiado desde la descarga ({meta.get('descargado')}): {url}"]
    return [f"  ✓ el PDF publicado coincide con la copia local ({url})"]


def web_nuevos(page, base, known_names):
    """PDF enlazados desde una página de normativa que no están en el corpus."""
    h = crawl_portal.get(page)
    links = dict.fromkeys(re.findall(r'href="([^"]+\.pdf)"', h))
    return [u for u in links if u.startswith(base) and u.rsplit("/", 1)[1] not in known_names]


def novedades():
    cat = catalog()
    corpus = {int(read_doc(p)[0]["id_portal"]) for a, p in docs(["uvigo"]) if read_doc(p)[0].get("id_portal")}
    print("Portal de normativa de la UVigo:")
    nuevas = portal_nuevas(set(cat))
    if not nuevas:
        print("  ✓ ninguna norma nueva desde el último rastreo")
    for n in nuevas:
        afecta = [f"{r['relacion']} {r['id']}" + (" (EN EL CORPUS)" if r["id"] in corpus else "") for r in n["relacionadas"]]
        print(f"  NUEVA {n['id']} [{n['estado']}] {n['titulo'][:110]}\n        {n.get('categoria') or ''} {('· ' + '; '.join(afecta)) if afecta else ''}")
    for nombre, page, base, folder in [
        ("Web de la EEAE", "https://aero.uvigo.es/gl/o-centro/normativa-e-formularios/", "/docs/escuela/normativa/", "eeae"),
        ("Web de la EIDO", "https://eido.uvigo.gal/gl/eido/normativa", "/docs/eido/normativa/", "eido"),
    ]:
        known = {read_doc(p)[0].get("url_documento", "").rsplit("/", 1)[-1] for a, p in docs([folder])}
        nuevos = [u for u in web_nuevos(page, base, known) if not u.rsplit("/", 1)[1].startswith(("DO-", "Convenio_cotutela", "Acceso_titulacions", "Convocatoria_complementos", "Procedemento_renovacion", "Normativa_permanencia"))]
        print(f"{nombre}:")
        print("\n".join(f"  NUEVO o no incluido: {u}" for u in nuevos) or "  ✓ nada nuevo")
    print("Legislación (BOE):")
    for a, p in docs(["estatal", "galicia"]):
        meta = read_doc(p)[0]
        if meta.get("id_boe"):
            res = check_boe(meta)
            if any("✗" in r for r in res):
                print(f"  {p.stem}:"); print("\n".join(res))
    print("  (las leyes no listadas arriba no han cambiado)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("refs", nargs="*", help="id del portal (565) o nombre de fichero (losu, rri-eeae…)")
    ap.add_argument("--novedades", action="store_true")
    a = ap.parse_args()
    if a.novedades:
        novedades()
    if a.refs:
        cat = catalog()
        try:
            nuevas = portal_nuevas(set(cat)) if any(r.isdigit() for r in a.refs) else []
        except Exception as e:
            sys.exit(f"? sin conexión con el portal de la UVigo ({e}). Comprueba la vigencia con la herramienta web (url_portal / fuente de cada norma) y dilo en la respuesta.")
        for ref in a.refs:
            files = find(ref)
            if not files:
                print(f"{ref}: no está en el corpus"); continue
            amb, p = files[0]
            meta = read_doc(p)[0]
            print(f"{ref} — {meta.get('titulo', '')[:100]}")
            try:
                if meta.get("id_portal"):
                    res = check_uvigo(int(meta["id_portal"]), [f for f in files if read_doc(f[1])[0].get("id_portal") == meta["id_portal"]], cat, nuevas)
                elif meta.get("id_boe"):
                    res = check_boe(meta)
                elif amb in ("eeae", "eido", "curso"):
                    res = check_pdf(meta)
                else:
                    res = ["  · publicación del DOG: el texto publicado no cambia; si hay actas o acuerdos nuevos, búscalos en la web (DOG / Comisión Paritaria)"]
            except Exception as e:
                res = [f"  ? no se pudo comprobar ({e}); di que la vigencia no se ha verificado en directo"]
            print("\n".join(res))
    if not a.refs and not a.novedades:
        ap.print_help()
