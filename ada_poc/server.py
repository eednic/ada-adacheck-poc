#!/usr/bin/env python3
"""Controlled accessibility-analyzer behavior PoC. Python standard library only."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone
from pathlib import Path
import json, os, secrets, threading, html

HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', '8080'))
BASE = os.environ.get('PUBLIC_BASE_URL', f'http://localhost:{PORT}').rstrip('/')
TOKEN = os.environ.get('POC_TOKEN', secrets.token_urlsafe(12))
LOG = Path(os.environ.get('LOG_FILE', 'requests.jsonl'))
LOCK = threading.Lock()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass
    def record(self):
        parsed = urlparse(self.path)
        event = {'timestamp': datetime.now(timezone.utc).isoformat(), 'method': self.command,
                 'path': parsed.path, 'query': parsed.query, 'source_ip': self.client_address[0],
                 'user_agent': self.headers.get('User-Agent', ''), 'referer': self.headers.get('Referer', '')}
    with LOCK:
    with LOG.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event) + '\n')
    print("POC_REQUEST " + json.dumps(event), flush=True)
        return parsed
    def send(self, code, data=b'', content_type='text/plain; charset=utf-8', headers=None):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Cache-Control', 'no-store')
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        if self.command != 'HEAD': self.wfile.write(data)
    def do_HEAD(self): self.do_GET()
    def do_GET(self):
        p = self.record()
        q = parse_qs(p.query)
        t = q.get('t', [TOKEN])[0]
        if p.path in ('/', '/index.html', '/final'):
            page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>ADA Controlled PoC {html.escape(t)}</title><link rel="stylesheet" href="/style.css?t={html.escape(t)}"></head><body><main><h1>ADA controlled proof of concept</h1><p id="marker">MARKER-{html.escape(t)}</p><img src="/pixel.png?t={html.escape(t)}" alt="Controlled test pixel"><iframe title="Controlled test frame" src="/frame?t={html.escape(t)}"></iframe><p id="js-status">JavaScript has not executed.</p></main><script>document.getElementById('js-status').textContent='JavaScript executed';fetch('/beacon?t={html.escape(t)}&kind=javascript',{{mode:'no-cors',cache:'no-store'}}).catch(()=>{{}});</script></body></html>'''
            self.send(200, page.encode(), 'text/html; charset=utf-8')
        elif p.path == '/redirect':
            self.send(302, b'', headers={'Location': f'{BASE}/final?t={t}'})
        elif p.path == '/style.css':
            self.send(200, b'body { font-family: sans-serif; }', 'text/css')
        elif p.path == '/pixel.png':
            # valid 1x1 transparent PNG
            import base64
            self.send(200, base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9R8t8AAAAASUVORK5CYII='), 'image/png')
        elif p.path == '/frame':
            self.send(200, f'<!doctype html><html lang="en"><body><main><h1>FRAME-{html.escape(t)}</h1></main></body></html>'.encode(), 'text/html; charset=utf-8')
        elif p.path == '/beacon':
            self.send(204)
        elif p.path == '/health':
            self.send(200, b'ok')
        elif p.path == '/logs':
            # Localhost-only; never expose logs publicly
            if self.client_address[0] not in ('127.0.0.1', '::1'):
                self.send(403, b'Localhost only')
            else:
                self.send(200, LOG.read_bytes() if LOG.exists() else b'', 'application/x-ndjson')
        else:
            self.send(404, b'Not found')

if __name__ == '__main__':
    print(f'PoC URL: {BASE}/?t={TOKEN}', flush=True)
    print(f'Redirect URL: {BASE}/redirect?t={TOKEN}', flush=True)
    print(f'Local log: {LOG.resolve()}', flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
