"""
Cliente HTTP mínimo (stdlib) para smoke tests RC — sin dependencia httpx.
"""
from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional


@dataclass
class HttpResponse:
    status: int
    body: Any
    headers: Mapping[str, str]
    raw_text: str


@dataclass
class HttpSmokeClient:
    base_url: str
    timeout_sec: float = 30.0
    default_headers: Dict[str, str] = field(default_factory=dict)

    def _url(self, path: str) -> str:
        base = self.base_url.rstrip("/")
        if not path.startswith("/"):
            path = "/" + path
        return base + path

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        form_body: Optional[Dict[str, str]] = None,
        bearer: Optional[str] = None,
    ) -> HttpResponse:
        hdrs = dict(self.default_headers)
        if headers:
            hdrs.update(headers)
        if bearer:
            hdrs["Authorization"] = f"Bearer {bearer}"

        data: Optional[bytes] = None
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            hdrs.setdefault("Content-Type", "application/json")
        elif form_body is not None:
            data = urllib.parse.urlencode(form_body).encode("utf-8")
            hdrs.setdefault("Content-Type", "application/x-www-form-urlencoded")

        req = urllib.request.Request(
            self._url(path),
            data=data,
            headers=hdrs,
            method=method.upper(),
        )
        ctx = ssl.create_default_context()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec, context=ctx) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return self._parse_response(resp.status, raw, dict(resp.headers))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            return self._parse_response(exc.code, raw, dict(exc.headers))

    def _parse_response(
        self, status: int, raw: str, headers: Dict[str, str]
    ) -> HttpResponse:
        body: Any = raw
        if raw:
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                body = raw
        return HttpResponse(status=status, body=body, headers=headers, raw_text=raw)
