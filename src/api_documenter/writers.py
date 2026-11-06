from html import escape
from pathlib import Path

from .models import Route


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
