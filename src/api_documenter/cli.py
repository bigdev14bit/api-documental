import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from .adapters.axum import AxumAdapter
from .adapters.express import ExpressAdapter
from .adapters.fastapi import FastAPIAdapter
from .adapters.gin import GinAdapter
from .adapters.spring import SpringAdapter
from .models import Route
from .scanner import SourceScanner
from .writers import write_html, write_markdown, write_openapi


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
        choices=("markdown", "html", "openapi", "both"),
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

    python_adapter = FastAPIAdapter()
    axum_adapter = AxumAdapter()
    express_adapter = ExpressAdapter()
    gin_adapter = GinAdapter()
    spring_adapter = SpringAdapter()
    routes: list[Route] = []
    for source_file in SourceScanner().scan(root):
        suffix = source_file.suffix.lower()
        adapter = (
            python_adapter
            if suffix == ".py"
            else axum_adapter
            if suffix == ".rs"
            else gin_adapter
            if suffix == ".go"
            else spring_adapter
            if suffix == ".java"
            else express_adapter
        )
        routes.extend(adapter.parse_file(source_file, root))
    return routes


def _write_docs(routes: list[Route], output_format: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if output_format in {"markdown", "both"}:
        write_markdown(routes, output_dir / "API_DOCUMENTATION.md")
    if output_format in {"html", "both"}:
        write_html(routes, output_dir / "api_doc.html")
    if output_format == "openapi":
        write_openapi(routes, output_dir / "openapi.json")


def _prompt_output_format(input_fn: Callable[[str], str]) -> str:
    formats = {"1": "markdown", "2": "html", "3": "openapi", "4": "both"}
    print("Output format: 1) Markdown  2) HTML  3) OpenAPI  4) Both")
    while True:
        choice = input_fn("Choose format [1-4, default 4]: ").strip() or "4"
        if choice in formats:
            return formats[choice]
        print("Please enter 1, 2, 3, or 4.")


def _run_wizard(input_fn: Callable[[str], str] | None = None) -> int:
    if input_fn is None:
        input_fn = input

    project_input = input_fn("Project directory [.]: ").strip() or "."
    project = Path(project_input).expanduser()
    routes = _scan(project)

    print(f"\nDetected {len(routes)} route(s):")
    if routes:
        for route in routes:
            print(f"  {route.method} {route.path} ({route.source_file})")
    else:
        print("  No routes detected.")

    output_format = _prompt_output_format(input_fn)
    default_output_dir = str(project)
    output_input = input_fn(
        f"Output directory [{default_output_dir}]: "
    ).strip() or default_output_dir
    output_dir = Path(output_input).expanduser()

    _write_docs(routes, output_format, output_dir)
    print(f"Generated documentation for {len(routes)} route(s) in {output_dir}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    effective_argv = sys.argv[1:] if argv is None else argv
    if not effective_argv:
        if not sys.stdin.isatty():
            parser.print_help()
            return 0
        try:
            return _run_wizard()
        except (KeyboardInterrupt, EOFError):
            print(f"{parser.prog}: cancelled", file=sys.stderr)
            return 130
        except (OSError, UnicodeError, SyntaxError, ValueError) as error:
            print(f"{parser.prog}: error: {error}", file=sys.stderr)
            return 2

    args = parser.parse_args(effective_argv)
    try:
        routes = _scan(args.project)
        _write_docs(routes, args.format, args.output_dir)
    except (OSError, UnicodeError, SyntaxError, ValueError) as error:
        print(f"{parser.prog}: error: {error}", file=sys.stderr)
        return 2

    print(f"Generated documentation for {len(routes)} route(s) in {args.output_dir}")
    return 0
