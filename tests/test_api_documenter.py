from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from api_documenter.adapters.axum import AxumAdapter
from api_documenter.adapters.express import ExpressAdapter
from api_documenter.adapters.fastapi import FastAPIAdapter
from api_documenter.adapters.gin import GinAdapter
from api_documenter.adapters.spring import SpringAdapter
from api_documenter.cli import main
from api_documenter.models import Route
from api_documenter.scanner import SourceScanner
from api_documenter.writers import write_html, write_markdown

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "fastapi_project"
EXPRESS_FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "express_project"
GIN_FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "gin_project"
SPRING_FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "spring_project"
AXUM_FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "axum_project"


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


class TestAxumAdapter(unittest.TestCase):
    def test_extracts_literal_routes_and_chained_router_variables(self):
        routes = AxumAdapter().parse_file(
            AXUM_FIXTURE_ROOT / "src" / "main.rs",
            AXUM_FIXTURE_ROOT,
        )

        self.assertEqual(
            routes,
            [
                Route("GET", "/", "src/main.rs"),
                Route("GET", "/health", "src/main.rs"),
                Route("HEAD", "/health", "src/main.rs"),
                Route("DELETE", "/items", "src/main.rs"),
                Route("GET", "/items", "src/main.rs"),
                Route("POST", "/items", "src/main.rs"),
                Route("GET", "/items/{id}", "src/main.rs"),
                Route("PUT", "/items/{id}", "src/main.rs"),
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


class TestGinAdapter(unittest.TestCase):
    def test_extracts_supported_routes_and_resolves_literal_group_prefixes(self):
        routes = GinAdapter().parse_file(
            GIN_FIXTURE_ROOT / "main.go",
            GIN_FIXTURE_ROOT,
        )

        self.assertEqual(
            routes,
            [
                Route("GET", "/api/users", "main.go"),
                Route("GET", "/api/v1/health", "main.go"),
                Route("GET", "/health", "main.go"),
                Route("HEAD", "/health", "main.go"),
                Route("OPTIONS", "/health", "main.go"),
                Route("DELETE", "/items/:id", "main.go"),
                Route("POST", "/users", "main.go"),
                Route("PATCH", "/users/:id", "main.go"),
                Route("PUT", "/users/:id", "main.go"),
            ],
        )


class TestSpringAdapter(unittest.TestCase):
    def test_extracts_supported_mappings_and_skips_unresolved_forms(self):
        routes = SpringAdapter().parse_file(
            SPRING_FIXTURE_ROOT / "src" / "main" / "java" / "example" / "UserController.java",
            SPRING_FIXTURE_ROOT,
        )

        self.assertEqual(
            routes,
            [
                Route("GET", "/admin/users", "src/main/java/example/UserController.java"),
                Route("GET", "/api/", "src/main/java/example/UserController.java"),
                Route("GET", "/api/health", "src/main/java/example/UserController.java"),
                Route("POST", "/api/items", "src/main/java/example/UserController.java"),
                Route("PUT", "/api/items", "src/main/java/example/UserController.java"),
                Route("POST", "/api/things", "src/main/java/example/UserController.java"),
                Route("PUT", "/api/things", "src/main/java/example/UserController.java"),
                Route("POST", "/api/users", "src/main/java/example/UserController.java"),
                Route("DELETE", "/api/users/{id}", "src/main/java/example/UserController.java"),
                Route("GET", "/api/users/{id}", "src/main/java/example/UserController.java"),
                Route("PATCH", "/api/users/{id}", "src/main/java/example/UserController.java"),
                Route("PUT", "/api/users/{id}", "src/main/java/example/UserController.java"),
                Route("GET", "/restricted", "src/main/java/example/UserController.java"),
            ],
        )


class TestSourceScanner(unittest.TestCase):
    def test_scans_supported_files_and_prunes_hidden_and_vendor_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "app.py").touch()
            (root / "main.rs").touch()
            (root / "main.go").touch()
            (root / "Controller.java").touch()
            (root / "routes.ts").touch()
            (root / "notes.txt").touch()
            (root / ".hidden").mkdir()
            (root / ".hidden" / "ignored.py").touch()
            (root / "node_modules").mkdir()
            (root / "node_modules" / "ignored.py").touch()

            self.assertEqual(
                SourceScanner().scan(root),
                [
                    root / "Controller.java",
                    root / "app.py",
                    root / "main.go",
                    root / "main.rs",
                    root / "routes.ts",
                ],
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
    def test_no_arguments_runs_interactive_wizard(self):
        with tempfile.TemporaryDirectory() as output_dir:
            stdout = StringIO()
            with (
                patch("sys.stdin.isatty", return_value=True),
                patch(
                    "builtins.input",
                    side_effect=[str(FIXTURE_ROOT), "1", output_dir],
                ),
                redirect_stdout(stdout),
            ):
                result = main([])

            documentation = (Path(output_dir) / "API_DOCUMENTATION.md").read_text()
            self.assertEqual(result, 0)
            self.assertTrue((Path(output_dir) / "API_DOCUMENTATION.md").is_file())
            self.assertFalse((Path(output_dir) / "api_doc.html").exists())
            self.assertIn("Detected 4 route(s)", stdout.getvalue())
            self.assertIn("GET /health (api.py)", stdout.getvalue())
            self.assertIn("| **GET** | `/health` | `api.py` |", documentation)

    def test_no_arguments_shows_help_when_stdin_is_not_a_tty(self):
        stdout = StringIO()
        with (
            patch("sys.stdin.isatty", return_value=False),
            patch("builtins.input") as input_mock,
            redirect_stdout(stdout),
        ):
            result = main([])

        self.assertEqual(result, 0)
        self.assertIn("usage: api-doc", stdout.getvalue())
        input_mock.assert_not_called()

    def test_interactive_wizard_handles_cancellation(self):
        stderr = StringIO()
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", side_effect=KeyboardInterrupt),
            redirect_stderr(stderr),
        ):
            result = main([])

        self.assertEqual(result, 130)
        self.assertIn("api-doc: cancelled", stderr.getvalue())

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

    def test_scan_command_generates_docs_for_gin_routes(self):
        with tempfile.TemporaryDirectory() as output_dir:
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "scan",
                        str(GIN_FIXTURE_ROOT),
                        "--format",
                        "markdown",
                        "--output-dir",
                        output_dir,
                    ]
                )

            documentation = (Path(output_dir) / "API_DOCUMENTATION.md").read_text()
            self.assertEqual(result, 0)
            self.assertIn("9 route(s)", stdout.getvalue())
            self.assertIn("| **GET** | `/api/v1/health` | `main.go` |", documentation)

    def test_scan_command_generates_docs_for_spring_routes(self):
        with tempfile.TemporaryDirectory() as output_dir:
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "scan",
                        str(SPRING_FIXTURE_ROOT),
                        "--format",
                        "markdown",
                        "--output-dir",
                        output_dir,
                    ]
                )

            documentation = (Path(output_dir) / "API_DOCUMENTATION.md").read_text()
            self.assertEqual(result, 0)
            self.assertIn("13 route(s)", stdout.getvalue())
            self.assertIn(
                "| **GET** | `/api/health` | `src/main/java/example/UserController.java` |",
                documentation,
            )
            self.assertNotIn("/api/inside-a-string", documentation)

    def test_scan_command_generates_docs_for_axum_routes(self):
        with tempfile.TemporaryDirectory() as output_dir:
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "scan",
                        str(AXUM_FIXTURE_ROOT),
                        "--format",
                        "markdown",
                        "--output-dir",
                        output_dir,
                    ]
                )

            documentation = (Path(output_dir) / "API_DOCUMENTATION.md").read_text()
            self.assertEqual(result, 0)
            self.assertIn("8 route(s)", stdout.getvalue())
            self.assertIn("| **GET** | `/health` | `src/main.rs` |", documentation)
            self.assertNotIn("/dynamic", documentation)

    def test_missing_project_returns_an_error(self):
        stderr = StringIO()
        with redirect_stderr(stderr):
            result = main(["scan", "missing-project"])

        self.assertEqual(result, 2)
        self.assertIn("project directory does not exist", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
