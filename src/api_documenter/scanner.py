import os
from pathlib import Path

_IGNORED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "env",
    "node_modules",
    "venv",
}
_SOURCE_SUFFIXES = {
    ".py",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".mts",
    ".cts",
}


class SourceScanner:
    """Find supported source files while pruning common generated/vendor folders."""

    def scan(self, root: Path) -> list[Path]:
        files: list[Path] = []
        for current, child_dirs, file_names in os.walk(root):
            child_dirs[:] = sorted(
                child
                for child in child_dirs
                if child not in _IGNORED_DIRECTORIES and not child.startswith(".")
            )
            files.extend(
                Path(current) / name
                for name in file_names
                if Path(name).suffix.lower() in _SOURCE_SUFFIXES
            )
        return sorted(files)
