"""Test data for the bundled Paydesk app, through its JSON API (examples/paydesk/server.py)."""
from __future__ import annotations

import json
import urllib.request


class PaydeskAdapter:
    def __init__(self, base_url: str):
        self.base = base_url.rstrip("/")

    def _call(self, method: str, path: str, body: dict | None = None):
        req = urllib.request.Request(self.base + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read() or b"{}")

    def create(self, kind: str, values: dict) -> dict:
        if kind != "invoice":
            raise ValueError(f"Paydesk can only create invoices, not '{kind}'")
        return self._call("POST", "/api/invoices", values)

    def get(self, kind: str, record: dict) -> dict:
        return self._call("GET", f"/api/invoices/{record['number']}")

    def delete(self, kind: str, record: dict) -> None:
        self._call("DELETE", f"/api/invoices/{record['number']}")
