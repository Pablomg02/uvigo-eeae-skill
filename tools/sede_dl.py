import re, sys, urllib.request, urllib.parse, http.cookiejar, html
def fetch_attachments(task_id, outdir):
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", "Mozilla/5.0")]
    url = f"https://sede.uvigo.gal/public/bulletin/bulletin-details.xhtml?idtaskdata={task_id}"
    h = op.open(url, timeout=60).read().decode("utf-8", "replace")
    out = []
    for m in re.finditer(r'<form id="([^"]*formDocuments\d*)"[^>]*action="([^"]+)".*?</form>', h, flags=re.S):
        form = m.group(0)
        fid = m.group(1)
        link = re.search(r'<a id="([^"]+)"[^>]*onclick="PrimeFaces.addSubmitParam', form)
        name = re.search(r'<span[^>]*>([^<]+\.\w{3,4})</span>', form)
        vs = re.search(r'name="javax.faces.ViewState"[^>]*value="([^"]+)"', form)
        if not (link and vs and name): continue
        data = {fid: fid, link.group(1): link.group(1), "procedurecode": "null", "javax.faces.ViewState": vs.group(1)}
        req = urllib.request.Request("https://sede.uvigo.gal" + html.unescape(m.group(2)), urllib.parse.urlencode(data).encode())
        r = op.open(req, timeout=90)
        body = r.read()
        fn = (name.group(1) if name else fid).strip()
        open(f"{outdir}/{fn}", "wb").write(body)
        out.append((fn, len(body), r.headers.get("Content-Type")))
    return out
if __name__ == "__main__":
    print(fetch_attachments(sys.argv[1], sys.argv[2]))
