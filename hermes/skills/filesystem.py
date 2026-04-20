from __future__ import annotations

from pathlib import Path

from hermes.security.policy import SecurityPolicy
from hermes.skills.base import Skill


class FileSystemControl(Skill):
    name = "FILE_SYSTEM_CONTROL"

    def __init__(self, policy: SecurityPolicy | None = None) -> None:
        self.policy = policy or SecurityPolicy()
        super().__init__()

    def _install_functions(self) -> None:
        self.register("read_file", self.read_file)
        self.register("write_file", self.write_file)
        self.register("create_folder", self.create_folder)
        self.register("delete_file", self.delete_file)

    def read_file(self, path: str | Path) -> str:
        target = Path(path)
        self.policy.check_path(target)
        return target.read_text(encoding="utf-8")

    def write_file(self, path: str | Path, content: str) -> int:
        target = Path(path)
        self.policy.check_path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        return target.write_text(content, encoding="utf-8")

    def create_folder(self, path: str | Path) -> Path:
        target = Path(path)
        self.policy.check_path(target)
        target.mkdir(parents=True, exist_ok=True)
        return target

    def delete_file(self, path: str | Path, confirmed: bool = False) -> bool:
        target = Path(path)
        self.policy.check_path(target)
        if not confirmed and self.policy.require_confirmation_for_destructive:
            raise PermissionError("delete_file requires confirmed=True under current policy")
        if target.exists():
            target.unlink()
            return True
        return False
