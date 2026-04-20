from __future__ import annotations

from typing import Any, Callable


class Skill:
    """A reusable functional module exposed through a set of named functions."""

    name: str = "UNNAMED_SKILL"

    def __init__(self) -> None:
        self._functions: dict[str, Callable[..., Any]] = {}
        self._install_functions()

    def _install_functions(self) -> None:
        """Subclasses register their functions here."""

    def register(self, name: str, fn: Callable[..., Any]) -> None:
        self._functions[name] = fn

    def list_functions(self) -> list[str]:
        return sorted(self._functions)

    def invoke(self, function: str, *args: Any, **kwargs: Any) -> Any:
        if function not in self._functions:
            raise KeyError(f"{self.name}: function '{function}' not found")
        return self._functions[function](*args, **kwargs)


class SkillRegistry(dict[str, Skill]):
    """Convenience dict that lets you register Skill instances by their `.name`."""

    def add(self, skill: Skill) -> None:
        self[skill.name] = skill
