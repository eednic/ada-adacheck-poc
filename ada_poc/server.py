
import os
import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path

PORT = int(os.environ.get("PORT", "8080"))
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
POC_TOKEN = os.environ.get("POC_TOKEN", "cdph-ada-test-001")

LOG = Path("/tmp/ada_requests.jsonl")
LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):

    def record(self):
        parsed = urlparse(self.path)

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": self.command,
            "path": parsed.path,
            "query": parsed.query,
            "source_ip": self.client_address[0],
            "user_agent": self.headers.get("User-Agent", ""),
            "referer": self.headers.get("Referer", "")
        }

        with LOCK:
            with LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")

            print(
                "POC_REQUEST " + json.dumps(event),
                flush=True
            )

        return parsed

    def send_response_body(self, status, content_type, body):
        if isinstance(body, str):
            body = body.encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = self.record()
        path = parsed.path
        query = parse_qs(parsed.query)
        token = query.get("t", [POC_TOKEN])[0]

        if path == "/":
            html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ADA Security Assessment PoC</title>
<link rel="stylesheet" href="/style.css?t={token}">
</head>
<body>
<main>
<h1>ADA Security Assessment</h1>

<p>Unique test marker: ADA-POC-2026</p>

<p>This page is used for authorized accessibility
and server-side resource loading tests.</p>

<img src="/pixel.png?t={token}"
     alt="Controlled resource loading test">

<iframe src="/frame?t={token}"
        title="Controlled iframe test"></iframe>

<div id="javascript-status">
JavaScript has not executed.
</div>

<script>
(function() {{
    document.getElementById(
        "javascript-status"
    ).textContent = "JavaScript executed successfully";

    var img = new Image();
    img.src = "/beacon?kind=javascript&t={token}";
}})();
</script>

</main>
</body>
</html>"""

            self.send_response_body(
                200,
                "text/html; charset=utf-8",
                html
            )

        elif path == "/style.css":
            css = """
body {
    font-family: Arial, sans-serif;
    margin: 40px;
    line-height: 1.6;
}
main {
    max-width: 800px;
}
"""
            self.send_response_body(
                200,
                "text/css",
                css
            )

        elif path == "/pixel.png" or path == "/beacon":
            # Valid transparent 1x1 PNG
            import base64

            png = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB"
                "CAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwM"
                "CAO+/lXcAAAAASUVORK5CYII="
            )

            self.send_response_body(
                200,
                "image/png",
                png
            )

        elif path == "/frame":
            html = f"""<!doctype html>
<html lang="en">
<head><title>Iframe Test</title></head>
<body>
<main>
<h1>Iframe Loaded</h1>
<p>Iframe marker: ADA-FRAME-{token}</p>
</main>
</body>
</html>"""

            self.send_response_body(
                200,
                "text/html; charset=utf-8",
                html
            )

        elif path == "/redirect":
            destination = f"/final?t={token}"

            self.send_response(302)
            self.send_header("Location", destination)
            self.send_header("Content-Length", "0")
            self.end_headers()

        elif path == "/final":
            html = f"""<!doctype html>
<html lang="en">
<head><title>Redirect Completed</title></head>
<body>
<main>
<h1>Redirect Followed Successfully</h1>
<p>Marker: ADA-REDIRECT-{token}</p>
</main>
</body>
</html>"""

            self.send_response_body(
                200,
                "text/html; charset=utf-8",
                html
            )

        elif path == "/health":
            self.send_response_body(
                200,
                "application/json",
                json.dumps({"status": "ok"})
            )

        else:
            self.send_response_body(
                404,
                "text/plain",
                "Not Found"
            )

    def do_POST(self):
        self.record()

        self.send_response_body(
            405,
            "application/json",
            json.dumps({"error": "Method not allowed"})
        )


if __name__ == "__main__":
    print(
        f"Starting ADA PoC server on 0.0.0.0:{PORT}",
        flush=True
    )

    print(
        f"PUBLIC_BASE_URL={PUBLIC_BASE_URL}",
        flush=True
    )

    server = ThreadingHTTPServer(
        ("0.0.0.0", PORT),
        Handler
    )

    server.serve_forever()
