"""Vercel serverless function:  POST /api/plan"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(__file__))
from _planner import handle_request  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def _send(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(200, {"status": "ok", "agent": "study-planner"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        status, payload = handle_request(self.rfile.read(length))
        self._send(status, payload)
