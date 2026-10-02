#!/usr/bin/env python3
"""Genera data/huellas.json con las huellas (bytes y texto) de los PDF originales que no viajan en la versión de la app.

comprobar.py las usa cuando no tiene el PDF local para detectar si el publicado ha cambiado. Necesita los PDF
en normativa/*/_originales/ (la copia del maintainer); actualizar.sh lo ejecuta como paso final.
"""
import hashlib, json, sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "normativa-uvigo-eeae"
sys.path.insert(0, str(SKILL / "scripts"))
from lib import ROOT, to_text
from buscar import docs, read_doc

# PDF que sí viajan en el paquete: no hace falta guardarles huella.
ORIGINALES = ("709-", "657-", "234-", "328-regulamento-para-a-liquidacion-e-tramitacion-de-indemni-doc3", "Calendario_EEAE", "Exames_Aero")

sha = lambda b: hashlib.sha256(b).hexdigest()[:16]
huellas = {}
for amb, p in docs():
    meta = read_doc(p)[0]
    if meta.get("traduccion"):
        continue
    orig = meta.get("original_local")
    if not orig or not (ROOT / orig).is_file():
        continue
    if orig.rsplit("/", 1)[-1].startswith(ORIGINALES):
        continue
    if amb in ("eeae", "eido", "curso"):  # los que comprueba comprobar.py comparando el PDF publicado
        data = (ROOT / orig).read_bytes()
        huellas[orig] = {"bytes": sha(data), "texto": sha(to_text(data).encode())}
json.dump(huellas, open(ROOT / "data" / "huellas.json", "w"), ensure_ascii=False, indent=1)
print(f"{len(huellas)} huellas de PDF -> data/huellas.json")
