from __future__ import annotations

import shlex
import subprocess
from typing import Sequence

from hermes.security.policy import SecurityPolicy


def run_shell(
    command: str | Sequence[str],
    timeout: float = 30.0,
    policy: SecurityPolicy | None = None,
    confirmed: bool = False,
) -> dict[str, object]:
    rendered = command if isinstance(command, str) else shlex.join(command)
    if policy is not None:
        policy.check_command(rendered, confirmed=confirmed)

    args = shlex.split(rendered) if isinstance(command, str) else list(command)
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return {"returncode": 127, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {"returncode": 124, "stdout": "", "stderr": f"timeout: {exc}"}
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
