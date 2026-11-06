from pathlib import Path
from typing import Protocol

from ..models import Route


class RouteAdapter(Protocol):
    def parse_file(self, file_path: Path, source_root: Path) -> list[Route]:
        """Extract normalized routes from a source file."""
