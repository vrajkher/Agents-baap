from __future__ import annotations

import io
import contextlib
from typing import Any


def run_python(source: str, globals_: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute a Python snippet in a controlled namespace and capture stdout."""
    namespace = globals_ if globals_ is not None else {}
    stdout = io.StringIO()
    error: str | None = None
    with contextlib.redirect_stdout(stdout):
        try:
            exec(source, namespace)  # noqa: S102 - explicit executor
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
    return {"stdout": stdout.getvalue(), "error": error, "namespace_keys": sorted(namespace)}
