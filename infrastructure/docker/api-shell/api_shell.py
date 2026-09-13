"""Minimal local API health/version shell for the Phase 01 dependency stack."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = os.environ.get("APP_VERSION", "0.1.0")
SERVICE = "platform-api"


class Handler(BaseHTTPRequestHandler):
    server_version = "LenGeasLocalAPI/0.1"

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._json({"service": SERVICE, "version": VERSION, "status": "ok"})
            return
        if self.path == "/version":
            self._json({"service": SERVICE, "version": VERSION, "status": "ok"})
            return
        if self.path == "/metrics":
            body = (
                "# HELP lengeas_api_up Local API shell availability.\n"
                "# TYPE lengeas_api_up gauge\n"
                "lengeas_api_up 1\n"
            )
            encoded = body.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return
        self._json(
            {"error": {"code": "not_found", "message": "Route not found."}},
            HTTPStatus.NOT_FOUND,
        )

    def _json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt: str, *args: object) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()  # noqa: S104
