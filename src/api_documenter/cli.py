import argparse
from pathlib import Path
import sys

from .adapters.fastapi import FastAPIAdapter
from .models import Route
from .scanner import SourceScanner
from .writers import write_html, write_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="api-doc",
        description="Generate API documentation from source code without executing it.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    scan = commands.add_parser("scan", help="scan a project and write API documentation")
    scan.add_argument("project", type=Path, help="project directory to scan")
    scan.add_argument(
        "--format",
        choices=("markdown", "html", "both"),
        default="both",
        help="documentation format to generate (default: both)",
    )
    scan.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="directory for generated files (default: current directory)",
    )
    return parser


def _scan(project: Path) -> list[Route]:
    root = project.resolve()
    if not root.is_dir():
        raise ValueError(f"project directory does not exist: {project}")

    adapter = FastAPIAdapter()
    routes: list[Route] = []
    for source_file in SourceScanner().scan(root):
        routes.extend(adapter.parse_file(source_file, root))
    return routes


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        routes = _scan(args.project)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        if args.format in {"markdown", "both"}:
            write_markdown(routes, args.output_dir / "API_DOCUMENTATION.md")
        if args.format in {"html", "both"}:
            write_html(routes, args.output_dir / "api_doc.html")
    except (OSError, UnicodeError, SyntaxError, ValueError) as error:
        print(f"{parser.prog}: error: {error}", file=sys.stderr)
        return 2

    print(f"Generated documentation for {len(routes)} route(s) in {args.output_dir}")
    return 0
