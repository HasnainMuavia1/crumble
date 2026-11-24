"""Local helper for asset generation in a browser tab.

GET  /ref/<file>   -> serves crumble/assets/ref/<file> with CORS headers (for attaching references)
PUT  /save/<file>  -> writes the request body to crumble/assets/<file> (for saving generated images)
Listens on 127.0.0.1:5181 only.
"""
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "assets", "ref")
OUT = os.path.join(ROOT, "assets")
SAFE = re.compile(r"^[A-Za-z0-9._-]+$")


class H(BaseHTTPRequestHandler):
    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(204)
        self.cors()
        self.end_headers()

    def do_GET(self):
        if self.path.split("?")[0] == "/carry":
            # Loads ref images, stores them as data URLs in window.name, then returns to `back`.
            html = b"""<!doctype html><meta charset=utf-8><title>carry</title><body>carrying<script>
(async()=>{const q=new URLSearchParams(location.search); const files=q.get('files').split(','); const back=q.get('back');
const out=[]; for(const f of files){const b=await (await fetch('/ref/'+f)).blob();
  out.push(await new Promise(r=>{const fr=new FileReader(); fr.onload=()=>r({name:f, data:fr.result}); fr.readAsDataURL(b);}));}
const payload=JSON.stringify(out); window.name='CRUMBLE_REFS:'+payload; if(back && back.startsWith('https://chatgpt.com/')) location.replace(back+'#CRUMBLE_REFS='+encodeURIComponent(payload));})();
</script>"""
            self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers(); self.wfile.write(html); return
        if self.path.split("?")[0] == "/receiver":
            html = b"""<!doctype html><meta charset=utf-8><title>receiver</title><body>ready<script>
addEventListener('message', async e => {
  if (e.origin !== 'https://chatgpt.com') return;
  const {name, blob} = e.data || {};
  if (!name || !(blob instanceof Blob)) return;
  const r = await fetch('/save/' + name, {method:'PUT', body: blob});
  const t = await r.text(); document.body.textContent = t; e.source.postMessage({saved: t}, e.origin);
});
if (window.opener) window.opener.postMessage({receiverReady: true}, 'https://chatgpt.com');
</script>"""
            self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers(); self.wfile.write(html); return
        name = self.path.split("?")[0].removeprefix("/ref/")
        path = os.path.join(REF, name)
        if self.path == "/" or not SAFE.match(name) or not os.path.isfile(path):
            self.send_response(404); self.cors(); self.end_headers(); return
        data = open(path, "rb").read()
        self.send_response(200)
        self.cors()
        self.send_header("Content-Type", "image/webp" if name.endswith(".webp") else "image/jpeg" if name.endswith(".jpg") else "image/png")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        # Form submission: fields name, data (base64), back (URL to return to)
        import base64
        from urllib.parse import parse_qs
        if self.path.split("?")[0] != "/save-form":
            self.send_response(404); self.end_headers(); return
        n = int(self.headers.get("Content-Length", 0))
        q = parse_qs(self.rfile.read(n).decode("ascii", "ignore"))
        back = (q.get("back") or [""])[0]
        saved = []
        for name, data in zip(q.get("name") or [], q.get("data") or []):
            if not SAFE.match(name) or not name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")) or not data:
                continue
            if "," in data[:100]:
                data = data.split(",", 1)[1]
            raw = base64.b64decode(data)
            with open(os.path.join(OUT, name), "wb") as f:
                f.write(raw)
            saved.append(name)
        name = ",".join(saved); raw = b""
        if back.startswith("https://chatgpt.com/"):
            self.send_response(303); self.send_header("Location", back); self.end_headers()
        else:
            self.send_response(200); self.end_headers(); self.wfile.write(f"saved {name} {len(raw)}".encode())

    def do_PUT(self):
        name = self.path.split("?")[0].removeprefix("/save/")
        if not SAFE.match(name) or not name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            self.send_response(400); self.cors(); self.end_headers(); return
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        with open(os.path.join(OUT, name), "wb") as f:
            f.write(body)
        self.send_response(200)
        self.cors()
        self.end_headers()
        self.wfile.write(f"saved {name} {len(body)}".encode())


ThreadingHTTPServer(("127.0.0.1", 5181), H).serve_forever()
