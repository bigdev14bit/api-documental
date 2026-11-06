import ast
from pathlib import Path

from ..models import Route

_HTTP_METHODS = {
    "delete",
    "get",
    "head",
    "options",
    "patch",
    "post",
    "put",
    "trace",
}


class FastAPIAdapter:
    """Extract FastAPI-style route decorators without importing project code."""

    def parse_file(self, file_path: Path, source_root: Path) -> list[Route]:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
        routes: list[Route] = []
        source_file = file_path.relative_to(source_root).as_posix()

        for node in ast.walk(tree):
            for decorator in getattr(node, "decorator_list", []):
                if not isinstance(decorator, ast.Call):
                    continue
                if not isinstance(decorator.func, ast.Attribute):
                    continue

                route_name = decorator.func.attr.lower()
                path = self._route_path(decorator)
                if path is None or self._excluded_from_schema(decorator):
                    continue

                methods = (
                    self._api_route_methods(decorator)
                    if route_name == "api_route"
                    else [route_name.upper()] if route_name in _HTTP_METHODS else []
                )
                routes.extend(
                    Route(method=method, path=path, source_file=source_file)
                    for method in methods
                )

        return sorted(routes, key=lambda route: (route.path, route.method))

    @staticmethod
    def _route_path(decorator: ast.Call) -> str | None:
        path_node = decorator.args[0] if decorator.args else None
        if path_node is None:
            path_node = next(
                (
                    keyword.value
                    for keyword in decorator.keywords
                    if keyword.arg in {"path", "url"}
                ),
                None,
            )
        if isinstance(path_node, ast.Constant) and isinstance(path_node.value, str):
            return path_node.value
        return None

    @staticmethod
    def _api_route_methods(decorator: ast.Call) -> list[str]:
        methods_node = next(
            (keyword.value for keyword in decorator.keywords if keyword.arg == "methods"),
            None,
        )
        if not isinstance(methods_node, (ast.List, ast.Tuple, ast.Set)):
            return []
        return [
            element.value.upper()
            for element in methods_node.elts
            if isinstance(element, ast.Constant)
            and isinstance(element.value, str)
            and element.value.lower() in _HTTP_METHODS
        ]

    @staticmethod
    def _excluded_from_schema(decorator: ast.Call) -> bool:
        return any(
            keyword.arg == "include_in_schema"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is False
            for keyword in decorator.keywords
        )
