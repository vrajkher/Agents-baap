from __future__ import annotations

import json
from typing import Any
from urllib import request, parse

from hermes.skills.base import Skill


class APIIntegration(Skill):
    """HTTP-based integration skill using the Python standard library.

    Drop in `requests` or `httpx` when richer functionality is needed; this
    variant keeps the dependency footprint zero for local-first deployments.
    """

    name = "API_INTEGRATION"

    def _install_functions(self) -> None:
        self.register("GET", self.get)
        self.register("POST", self.post)
        self.register("AUTH", self.auth)
        self.register("WEBHOOK", self.webhook)

    def get(self, url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
        if params:
            url = f"{url}?{parse.urlencode(params)}"
        return self._execute("GET", url, headers=headers)

    def post(self, url: str, payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
        body = json.dumps(payload or {}).encode("utf-8")
        merged = {"Content-Type": "application/json", **(headers or {})}
        return self._execute("POST", url, body=body, headers=merged)

    def auth(self, token: str, scheme: str = "Bearer") -> dict[str, str]:
        return {"Authorization": f"{scheme} {token}"}

    def webhook(self, url: str, event: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.post(url, payload={"event": event, "data": payload})

    def _execute(
        self,
        method: str,
        url: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        req = request.Request(url, data=body, method=method, headers=headers or {})
        try:
            with request.urlopen(req, timeout=30) as response:  # noqa: S310
                raw = response.read().decode("utf-8")
                try:
                    data: Any = json.loads(raw) if raw else None
                except json.JSONDecodeError:
                    data = raw
                return {"status": response.status, "data": data}
        except Exception as exc:  # pragma: no cover - network-bound
            return {"status": "error", "error": str(exc)}
