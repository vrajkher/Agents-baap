from __future__ import annotations

from pathlib import Path
from typing import Iterable

from hermes.security.policy import SecurityPolicy


class FileSystemAPI:
    """Thin object-oriented wrapper around path operations the framework uses."""

    def __init__(self, policy: SecurityPolicy | None = None) -> None:
        self.policy = policy or SecurityPolicy()

    def __call__(self, action: str, *args: object, **kwargs: object) -> object:
        if not hasattr(self, action):
            raise AttributeError(f"FileSystemAPI has no action '{action}'")
        return getattr(self, action)(*args, **kwargs)

    def list_dir(self, path: str | Path) -> list[str]:
        target = Path(path)
        self.policy.check_path(target)
        return sorted(p.name for p in target.iterdir())

    def exists(self, path: str | Path) -> bool:
        target = Path(path)
        self.policy.check_path(target)
        return target.exists()

    def copy(self, src: str | Path, dst: str | Path) -> Path:
        source, destination = Path(src), Path(dst)
        self.policy.check_path(source)
        self.policy.check_path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
        return destination

    def walk(self, path: str | Path) -> Iterable[Path]:
        target = Path(path)
        self.policy.check_path(target)
        yield from target.rglob("*")
