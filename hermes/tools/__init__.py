from typing import Callable, Any

from hermes.tools.python_executor import run_python
from hermes.tools.shell import run_shell
from hermes.tools.filesystem_api import FileSystemAPI

__all__ = ["run_python", "run_shell", "FileSystemAPI", "default_tool_registry"]


def default_tool_registry() -> dict[str, Callable[..., Any]]:
    fs_api = FileSystemAPI()
    return {
        "Python Executor": run_python,
        "Shell Command Runner": run_shell,
        "File System API": fs_api,
    }
