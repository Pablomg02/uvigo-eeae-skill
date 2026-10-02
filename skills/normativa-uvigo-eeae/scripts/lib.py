"""Utilidades comunes: descarga, PDF -> texto, escritura de normas con cabecera de metadatos."""
import hashlib, re, shutil, subprocess, tempfile, time, unicodedata, urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (normativa-uvigo-eeae skill; uso personal)"}


def download(url, tries=3):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(2)


def slug(s, n=60):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n].strip("-")


def pdf_to_text(data: bytes) -> str:
    """Convierte PDF a texto. Devuelve '' si no hay capa de texto (PDF escaneado)."""
    if not shutil.which("pdftotext"):  # entorno sin poppler (p. ej. la app de Claude), donde pdfplumber viene instalado
        import io, pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return tidy("\n".join(pg.extract_text() or "" for pg in pdf.pages))
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(data)
        f.flush()
        run = lambda *opt: subprocess.run(["pdftotext", *opt, "-enc", "UTF-8", f.name, "-"], capture_output=True).stdout.decode("utf-8", "replace")
        out = run()
        # Algunos PDF (p. ej. los de la EIDO) guardan las tildes como acento combinado seguido de un hueco, y el modo
        # por defecto lo convierte en espacio ("duració n"), lo que rompe las búsquedas. El modo -raw no lo hace.
        if len(re.findall(r"[̀-ͯ] [a-zñ]", out)) > max(20, len(re.findall(r"[̀-ͯ][a-zñ]", out))):
            out = run("-raw")
    return tidy(out)


def office_to_text(data: bytes, suffix: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=suffix) as f:
        f.write(data)
        f.flush()
        out = subprocess.run(["pandoc", f.name, "-t", "plain", "--wrap=none"], capture_output=True).stdout.decode("utf-8", "replace")
    return tidy(out)


def tidy(t: str) -> str:
    t = t.replace("\x0c", "\n").replace("­", "")
    # algunos PDF (LaTeX) codifican "í" como "ı" (i sin punto) + acento combinado: rompe las búsquedas
    t = unicodedata.normalize("NFC", re.sub("ı([̀-ͯ])", r"i\1", t))
    t = re.sub(r"\.{4,}|(?:\. ){4,}", " … ", t)  # puntos de relleno de los índices
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t)  # palabras partidas por guion de fin de línea
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def kind_of(data: bytes) -> str:
    if data[:4] == b"%PDF":
        return "pdf"
    if data[:2] == b"PK":
        return "docx"
    if data[:4] == b"\xd0\xcf\x11\xe0":
        return "doc"
    return "other"


def to_text(data: bytes) -> str:
    k = kind_of(data)
    if k == "pdf":
        return pdf_to_text(data)
    if k in ("docx", "doc"):
        return office_to_text(data, "." + k)
    return ""


def write_norm(path: Path, meta: dict, body: str):
    """Escribe una norma como Markdown con cabecera YAML de metadatos (para citar y auditar)."""
    meta = {**meta, "descargado": date.today().isoformat(), "sha256_texto": hashlib.sha256(body.encode()).hexdigest()[:16]}
    head = "---\n" + "\n".join(f"{k}: {str(v).replace(chr(10), ' ')!r}" if isinstance(v, str) else f"{k}: {v}" for k, v in meta.items() if v not in (None, "")) + "\n---\n\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(head + body + "\n")
