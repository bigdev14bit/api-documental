from dataclasses import dataclass
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
}


@dataclass(frozen=True, slots=True)
class _Token:
    kind: str
    value: str


class ExpressAdapter:
    """Extract Express-style route calls without importing project code."""

    def parse_file(self, file_path: Path, source_root: Path) -> list[Route]:
        tokens = _tokenize(file_path.read_text(encoding="utf-8"))
        close_to_open = _matching_parentheses(tokens)
        routes: list[Route] = []
        source_file = file_path.relative_to(source_root).as_posix()

        for index, token in enumerate(tokens):
            if (
                token.value != "."
                or index + 2 >= len(tokens)
                or tokens[index + 1].kind != "identifier"
                or tokens[index + 1].value.lower() not in _HTTP_METHODS
                or tokens[index + 2].value != "("
            ):
                continue

            route_path = _chained_route_path(tokens, index, close_to_open)
            if route_path is None:
                first_argument = tokens[index + 3] if index + 3 < len(tokens) else None
                if first_argument is None or first_argument.kind != "string":
                    continue
                route_path = first_argument.value

            routes.append(
                Route(
                    method=tokens[index + 1].value.upper(),
                    path=route_path,
                    source_file=source_file,
                )
            )

        return sorted(routes, key=lambda route: (route.path, route.method))


def _chained_route_path(
    tokens: list[_Token],
    method_dot: int,
    close_to_open: dict[int, int],
) -> str | None:
    call_close = method_dot - 1
    while call_close >= 0 and tokens[call_close].value == ")":
        call_open = close_to_open.get(call_close)
        if call_open is None or call_open < 2 or tokens[call_open - 2].value != ".":
            return None

        method_name = tokens[call_open - 1].value.lower()
        if method_name == "route":
            path_token = tokens[call_open + 1] if call_open + 1 < len(tokens) else None
            return (
                path_token.value
                if path_token is not None and path_token.kind == "string"
                else None
            )
        if method_name not in _HTTP_METHODS:
            return None
        call_close = call_open - 3
    return None


def _matching_parentheses(tokens: list[_Token]) -> dict[int, int]:
    openings: list[int] = []
    matching: dict[int, int] = {}
    for index, token in enumerate(tokens):
        if token.value == "(":
            openings.append(index)
        elif token.value == ")" and openings:
            opening = openings.pop()
            matching[index] = opening
    return matching


def _tokenize(source: str) -> list[_Token]:
    tokens: list[_Token] = []
    index = 0
    while index < len(source):
        char = source[index]
        if char.isspace():
            index += 1
        elif source.startswith("//", index):
            newline = source.find("\n", index + 2)
            index = len(source) if newline == -1 else newline + 1
        elif source.startswith("/*", index):
            end = source.find("*/", index + 2)
            index = len(source) if end == -1 else end + 2
        elif char in {"'", '"', "`"}:
            token, index = _read_string(source, index)
            if token is not None:
                tokens.append(token)
        elif char.isalpha() or char in {"_", "$"}:
            end = index + 1
            while end < len(source) and (
                source[end].isalnum() or source[end] in {"_", "$"}
            ):
                end += 1
            tokens.append(_Token("identifier", source[index:end]))
            index = end
        else:
            tokens.append(_Token("punctuation", char))
            index += 1
    return tokens


def _read_string(source: str, start: int) -> tuple[_Token | None, int]:
    quote = source[start]
    index = start + 1
    value: list[str] = []
    interpolated = False
    while index < len(source):
        char = source[index]
        if char == "\\" and index + 1 < len(source):
            escaped = source[index + 1]
            if escaped == "\n":
                index += 2
                continue
            value.append({"n": "\n", "r": "\r", "t": "\t"}.get(escaped, escaped))
            index += 2
        elif char == quote:
            kind = "string" if quote != "`" or not interpolated else "dynamic"
            return _Token(kind, "".join(value)), index + 1
        else:
            if quote == "`" and source.startswith("${", index):
                interpolated = True
            value.append(char)
            index += 1
    return None, len(source)
