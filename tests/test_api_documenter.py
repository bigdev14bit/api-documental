from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
import tempfile
import unittest

from api_documenter.adapters.fastapi import FastAPIAdapter
from api_documenter.cli import main
from api_documenter.models import Route
from api_documenter.scanner import SourceScanner
from api_documenter.writers import write_html, write_markdown

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "fastapi_project"


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


class TestSourceScanner(unittest.TestCase):
    def test_scans_python_files_and_prunes_hidden_and_vendor_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "app.py").touch()
            (root / "notes.txt").touch()
            (root / ".hidden").mkdir()
            (root / ".hidden" / "ignored.py").touch()
            (root / "node_modules").mkdir()
            (root / "node_modules" / "ignored.py").touch()

            self.assertEqual(SourceScanner().scan(root), [root / "app.py"])


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

    def test_missing_project_returns_an_error(self):
        stderr = StringIO()
        with redirect_stderr(stderr):
            result = main(["scan", "missing-project"])

        self.assertEqual(result, 2)
        self.assertIn("project directory does not exist", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
