from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Route:
    method: str
    path: str
    source_file: str
