from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
import tempfile
import unittest

from api_documenter.adapters.express import ExpressAdapter
from api_documenter.adapters.fastapi import FastAPIAdapter
from api_documenter.cli import main
from api_documenter.models import Route
from api_documenter.scanner import SourceScanner
from api_documenter.writers import write_html, write_markdown

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "fastapi_project"
EXPRESS_FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "express_project"


class TestFastAPIAdapter(unittest.TestCase):
    def test_extracts_literal_http_routes_without_executing_code(self):
        routes = FastAPIAdapter().parse_file(FIXTURE_ROOT / "api.py", FIXTURE_ROOT)

        self.assertEqual(
            routes,
            [
                Route("GET", "/health", "api.py"),
                Route("DELETE", "/items/{item_id}", "api.py"),
                Route("GET", "/items/{item_id}", "api.py"),
                Route("POST", "/users", "api.py"),
            ],
        )


class TestExpressAdapter(unittest.TestCase):
    def test_extracts_literal_routes_without_executing_code(self):
        routes = ExpressAdapter().parse_file(
            EXPRESS_FIXTURE_ROOT / "src" / "routes.ts",
            EXPRESS_FIXTURE_ROOT,
        )

        self.assertEqual(
            routes,
            [
                Route("GET", "/health", "src/routes.ts"),
                Route("DELETE", "/items", "src/routes.ts"),
                Route("GET", "/items", "src/routes.ts"),
                Route("POST", "/items", "src/routes.ts"),
                Route("POST", "/users", "src/routes.ts"),
                Route("PATCH", "/users/:userId", "src/routes.ts"),
                Route("PUT", "/users/:userId", "src/routes.ts"),
                Route("GET", "/version", "src/routes.ts"),
            ],
        )


class TestSourceScanner(unittest.TestCase):
    def test_scans_supported_files_and_prunes_hidden_and_vendor_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "app.py").touch()
            (root / "routes.ts").touch()
            (root / "notes.txt").touch()
            (root / ".hidden").mkdir()
            (root / ".hidden" / "ignored.py").touch()
            (root / "node_modules").mkdir()
            (root / "node_modules" / "ignored.py").touch()

            self.assertEqual(
                SourceScanner().scan(root),
                [root / "app.py", root / "routes.ts"],
            )


class TestWriters(unittest.TestCase):
    def test_writes_empty_markdown_and_escapes_html(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            markdown_path = root / "empty.md"
            html_path = root / "routes.html"

            write_markdown([], markdown_path)
            write_html([Route("GET", "/<item>", "api.py")], html_path)

            self.assertIn("| :--- | :--- | :--- |", markdown_path.read_text())
            self.assertIn("&lt;item&gt;", html_path.read_text())


class TestCLI(unittest.TestCase):
    def test_scan_command_writes_only_the_selected_format(self):
        with tempfile.TemporaryDirectory() as output_dir:
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "scan",
                        str(FIXTURE_ROOT),
                        "--format",
                        "markdown",
                        "--output-dir",
                        output_dir,
                    ]
                )

            self.assertEqual(result, 0)
            self.assertTrue((Path(output_dir) / "API_DOCUMENTATION.md").is_file())
            self.assertFalse((Path(output_dir) / "api_doc.html").exists())
            self.assertIn("4 route(s)", stdout.getvalue())

    def test_scan_command_generates_docs_for_express_routes(self):
        with tempfile.TemporaryDirectory() as output_dir:
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "scan",
                        str(EXPRESS_FIXTURE_ROOT),
                        "--format",
                        "markdown",
                        "--output-dir",
                        output_dir,
                    ]
                )

            documentation = (Path(output_dir) / "API_DOCUMENTATION.md").read_text()
            self.assertEqual(result, 0)
            self.assertIn("8 route(s)", stdout.getvalue())
            self.assertIn("| **GET** | `/health` | `src/routes.ts` |", documentation)
            self.assertIn("| **POST** | `/items` | `src/routes.ts` |", documentation)

    def test_missing_project_returns_an_error(self):
        stderr = StringIO()
        with redirect_stderr(stderr):
            result = main(["scan", "missing-project"])

        self.assertEqual(result, 2)
        self.assertIn("project directory does not exist", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
