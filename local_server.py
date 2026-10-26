"""Run the whole site on your computer:  python local_server.py"""
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "api"))
from _planner import handle_request  # noqa: E402


class Local(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="public", **kwargs)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        status, payload = handle_request(self.rfile.read(length))
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    print(f"Open http://localhost:{port}", flush=True)
    HTTPServer(("0.0.0.0", port), Local).serve_forever()
