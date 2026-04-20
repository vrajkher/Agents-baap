from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


class SecurityViolation(RuntimeError):
    """Raised when an agent attempts an action that violates policy."""


DEFAULT_DESTRUCTIVE_TOKENS = (
    "rm -rf",
    "mkfs",
    "dd if=",
    ":(){ :|:& };:",
    "shutdown",
    "reboot",
    "format ",
)


@dataclass
class SecurityPolicy:
    allowed_roots: list[Path] = field(default_factory=list)
    require_confirmation_for_destructive: bool = True
    destructive_tokens: tuple[str, ...] = DEFAULT_DESTRUCTIVE_TOKENS
    encrypt_secrets: bool = True

    def check_path(self, path: Path) -> None:
        if not self.allowed_roots:
            return
        resolved = path.resolve()
        for root in self.allowed_roots:
            try:
                resolved.relative_to(root.resolve())
                return
            except ValueError:
                continue
        raise SecurityViolation(f"Path {resolved} is outside allowed roots")

    def check_command(self, command: str, confirmed: bool = False) -> None:
        lowered = command.lower()
        for token in self.destructive_tokens:
            if token in lowered:
                if self.require_confirmation_for_destructive and not confirmed:
                    raise SecurityViolation(
                        f"Destructive token '{token}' requires explicit confirmation"
                    )
