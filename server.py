#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, mimetypes, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from scan import lookup

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), fmt % args))

    def send_json(self, obj, status=200):
        data = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/lookup":
            qs = urllib.parse.parse_qs(parsed.query)
            barcode = (qs.get("barcode") or [""])[0]
            fixture = (qs.get("fixture") or ["0"])[0] in ["1", "true", "yes"]
            first = (qs.get("first") or ["0"])[0] in ["1", "true", "yes"]
            try:
                self.send_json(lookup(barcode, fixture=fixture, max_candidates=1 if first else None))
            except Exception as e:
                self.send_json({"ok": False, "error": f"{type(e).__name__}: {e}"}, status=500)
            return
        rel = "index.html" if parsed.path in ["/", ""] else parsed.path.lstrip("/")
        path = (WEB / rel).resolve()
        if not str(path).startswith(str(WEB.resolve())) or not path.exists():
            self.send_error(404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Open http://{args.host}:{args.port} — scanner input acts like keyboard + Enter")
    server.serve_forever()

if __name__ == "__main__":
    main()
