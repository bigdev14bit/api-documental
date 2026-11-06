from html import escape
import json
from pathlib import Path
import re

from .models import Route

_PATH_PARAMETER = re.compile(r":([A-Za-z_][A-Za-z0-9_]*)")
_PATH_TEMPLATE_PARAMETER = re.compile(r"\{([^{}]+)\}")


def write_markdown(routes: list[Route], output_path: Path) -> None:
    lines = [
        "# API Documentation",
        "",
        "| HTTP Method | Path | Source File |",
        "| :--- | :--- | :--- |",
    ]
    for route in routes:
        path = route.path.replace("`", "\\`")
        source_file = route.source_file.replace("`", "\\`")
        lines.append(f"| **{route.method}** | `{path}` | `{source_file}` |")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(routes: list[Route], output_path: Path) -> None:
    cards = "\n".join(
        "    <tr>"
        f"<td>{escape(route.method)}</td>"
        f"<td><code>{escape(route.path)}</code></td>"
        f"<td><code>{escape(route.source_file)}</code></td>"
        "</tr>"
        for route in routes
    )
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>API Documentation</title>
</head>
<body>
  <main>
    <h1>API Documentation</h1>
    <table>
      <thead><tr><th>HTTP Method</th><th>Path</th><th>Source File</th></tr></thead>
      <tbody>
{cards}
      </tbody>
    </table>
  </main>
</body>
</html>
"""
    output_path.write_text(document, encoding="utf-8")


def write_openapi(routes: list[Route], output_path: Path) -> None:
    paths: dict[str, dict[str, dict[str, object]]] = {}
    source_files: dict[tuple[str, str], set[str]] = {}

    for route in routes:
        path = _PATH_PARAMETER.sub(r"{\1}", route.path)
        method = route.method.lower()
        operation = paths.setdefault(path, {}).setdefault(
            method,
            {
                "responses": {
                    "default": {
                        "description": (
                            "Response details are not available from static analysis."
                        )
                    }
                },
                "x-api-documenter-source-files": [],
            },
        )
        source_files.setdefault((path, method), set()).add(route.source_file)

        parameters = [
            {
                "name": name,
                "in": "path",
                "required": True,
                "schema": {},
            }
            for name in _PATH_TEMPLATE_PARAMETER.findall(path)
        ]
        if parameters:
            operation["parameters"] = parameters

    for path, operations in paths.items():
        for method, operation in operations.items():
            operation["x-api-documenter-source-files"] = sorted(
                source_files[(path, method)]
            )

    document = {
        "openapi": "3.1.0",
        "info": {
            "title": "API Documentation",
            "version": "unknown",
        },
        "paths": {
            path: dict(sorted(operations.items()))
            for path, operations in sorted(paths.items())
        },
    }
    output_path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
