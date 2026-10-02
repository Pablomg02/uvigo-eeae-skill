#!/usr/bin/env python3
"""Rastrea el portal de normativa de la UVigo (secretaria.uvigo.gal) y escribe data/catalog.json.

Por cada norma guarda: id, título, rango, servicio, categoría, estado (Validada/Anulada),
tipo, observaciones, enlaces de descarga, enlaces al tablón de la sede y relaciones
("Deroga a", "Modifica a", ...). Uso: python3 scripts/crawl_portal.py
"""
import html, json, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = "https://secretaria.uvigo.gal"
UA = {"User-Agent": "Mozilla/5.0 (normativa-uvigo-eeae skill; uso personal)"}
OUT = Path(__file__).resolve().parent.parent / "data" / "catalog.json"


def get(url, tries=3):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode("utf-8", "replace")
        except Exception as e:
            if i == tries - 1:
                print("FALLO", url, e, file=sys.stderr)
                return ""
            time.sleep(2)


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def listing():
    items, page = {}, 1
    while True:
        h = get(f"{BASE}/uv/web/normativa/public/?orderDir=DESC&page={page}")
        cards = re.findall(r'<div class="uvigo-card-box">(.*?)<!-- card-box -->', h, flags=re.S)
        before = len(items)
        for card in cards:
            m = re.search(r"public/show/(\d+)", card)
            if m:
                items[int(m.group(1))] = {"id": int(m.group(1))}
        # el portal repite la última página si pides una inexistente: parar si no hay ids nuevos
        if len(items) == before:
            break
        print("listado página", page, len(items), file=sys.stderr)
        page += 1
        time.sleep(0.3)
    return items


def detail(i):
    h = get(f"{BASE}/uv/web/normativa/public/show/{i}")
    col = h[h.find('id="uvigomp-col2"'):h.find("Para calquera d")]
    txt = clean(col)
    d = {"id": i}
    t = re.search(r"Inicio (.+?) Estado ", txt)
    d["titulo"] = t.group(1) if t else ""
    for key, pat in {
        "estado": r"Estado (Validada|Anulada)",
        "tipo": r" Tipo (.+?) Rango ",
        "rango": r" Rango (.+?) (?:Servizo|Categorias)",
        "servizo": r" Servizo (.+?) Categorias",
        "categoria": r" Categorias (.+?) (?:Descrición|Observacións|Destinatarios|Documentos|Publicacións|Normativas relacionadas)",
        "descricion": r" Descrición (.+?) (?:Observacións|Destinatarios|Documentos|Publicacións)",
        "observacions": r" Observacións (.+?) (?:Destinatarios|Documentos|Publicacións)",
        "periodo": r"Período exp\. (\S+ - \S+)",
    }.items():
        m = re.search(pat, txt)
        d[key] = m.group(1).strip() if m else None
    d["docs"] = [
        {"titulo": clean(tt), "url": BASE + u}
        for u, tt in re.findall(r'<a href="(/uv/web/normativa/public/normativa/documento/downloadbyhash/[a-f0-9]+)" class="filename"[^>]*>(.*?)</a>', col, flags=re.S)
    ]
    ext = re.findall(r'<a target="_blank" href="(https?://[^"]+)">', col)
    d["sede"] = [u for u in ext if "sede.uvigo.gal" in u]
    d["diarios"] = [u for u in ext if "sede.uvigo.gal" not in u]
    rel = []
    if "Normativas relacionadas" in col:
        blk = col[col.find("Normativas relacionadas"):]
        for kind, body in re.findall(r"<strong>(.*?):</strong>(.*?)(?=<strong>|</table>)", blk, flags=re.S):
            for rid, rt in re.findall(r'public/show/(\d+)">(.*?)</a>', body, flags=re.S):
                rel.append({"relacion": clean(kind), "id": int(rid), "titulo": clean(rt)})
    d["relacionadas"] = rel
    time.sleep(0.2)
    return d


if __name__ == "__main__":
    ids = sorted(listing())
    with ThreadPoolExecutor(4) as ex:
        out = list(ex.map(detail, ids))
    out.sort(key=lambda x: -x["id"])
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("OK", len(out), "normas ->", OUT)
