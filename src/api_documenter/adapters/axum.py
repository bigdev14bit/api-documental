from dataclasses import dataclass
from pathlib import Path

from ..models import Route

_HTTP_METHODS = {
    "delete": "DELETE",
    "get": "GET",
    "head": "HEAD",
    "options": "OPTIONS",
    "patch": "PATCH",
    "post": "POST",
    "put": "PUT",
    "trace": "TRACE",
}


@dataclass(frozen=True, slots=True)
class _Token:
    kind: str
    value: str


class AxumAdapter:
    """Extract literal Axum Router routes without importing project code."""

    def parse_file(self, file_path: Path, source_root: Path) -> list[Route]:
        tokens = _tokenize(file_path.read_text(encoding="utf-8"))
        routes: list[Route] = []
        source_file = file_path.relative_to(source_root).as_posix()

        for index, token in enumerate(tokens):
            if (
                token.value != "route"
                or token.kind != "identifier"
                or index < 2
                or tokens[index - 1].value != "."
                or index + 1 >= len(tokens)
                or tokens[index + 1].value != "("
            ):
                continue
            close = _matching_delimiter(tokens, index + 1, "(", ")")
            if close is None:
                continue

            arguments = _split_top_level(tokens[index + 2 : close], ",")
            if len(arguments) != 2:
                continue
            path_argument, method_argument = arguments
            if len(path_argument) != 1 or path_argument[0].kind != "string":
                continue
            methods = _method_chain(method_argument)
            routes.extend(
                Route(method, path_argument[0].value, source_file)
                for method in methods
            )

        return sorted(routes, key=lambda route: (route.path, route.method))


def _method_chain(tokens: tuple[_Token, ...]) -> tuple[str, ...]:
    methods: list[str] = []
    cursor = 0
    while cursor < len(tokens):
        if cursor:
            if cursor + 1 >= len(tokens) or tokens[cursor].value != ".":
                return ()
            cursor += 1
        method = tokens[cursor]
        if method.kind != "identifier" or method.value not in _HTTP_METHODS:
            return ()
        cursor += 1
        if cursor >= len(tokens) or tokens[cursor].value != "(":
            return ()
        close = _matching_delimiter(tokens, cursor, "(", ")")
        if close is None:
            return ()
        methods.append(_HTTP_METHODS[method.value])
        cursor = close + 1
    return tuple(methods)


def _matching_delimiter(
    tokens: list[_Token] | tuple[_Token, ...],
    opening: int,
    open_value: str,
    close_value: str,
) -> int | None:
    depth = 0
    for index in range(opening, len(tokens)):
        if tokens[index].value == open_value:
            depth += 1
        elif tokens[index].value == close_value:
            depth -= 1
            if depth == 0:
                return index
    return None


def _split_top_level(
    tokens: tuple[_Token, ...],
    separator: str,
) -> list[tuple[_Token, ...]]:
    parts: list[tuple[_Token, ...]] = []
    depths = {"(": 0, "[": 0, "{": 0}
    closing = {")": "(", "]": "[", "}": "{"}
    start = 0
    for index, token in enumerate(tokens):
        if token.value == separator and not any(depths.values()):
            parts.append(tokens[start:index])
            start = index + 1
        elif token.value in depths:
            depths[token.value] += 1
        elif token.value in closing:
            depths[closing[token.value]] -= 1
    if start < len(tokens) or not parts:
        parts.append(tokens[start:])
    return parts


def _tokenize(source: str) -> list[_Token]:
    tokens: list[_Token] = []
    index = 0
    while index < len(source):
        if source[index].isspace():
            index += 1
        elif source.startswith("//", index):
            newline = source.find("\n", index + 2)
            index = len(source) if newline == -1 else newline + 1
        elif source.startswith("/*", index):
            index = _skip_block_comment(source, index)
        elif source[index] == "r" or (
            source[index] == "b"
            and index + 1 < len(source)
            and source[index + 1] == "r"
        ):
            raw_start = index + 1 if source[index] == "b" else index
            raw_end = _raw_string_end(source, raw_start)
            if raw_end is not None:
                quote_index = source.find('"', raw_start)
                content_start = quote_index + 1
                hashes = quote_index - raw_start - 1
                closing = '"' + "#" * hashes
                content_end = source.find(closing, content_start)
                if source[index] == "r":
                    tokens.append(_Token("string", source[content_start:content_end]))
                else:
                    tokens.append(_Token("dynamic", ""))
                index = raw_end
            else:
                index = _read_identifier_or_punctuation(source, index, tokens)
        elif source[index] == '"':
            token, index = _read_string(source, index)
            tokens.append(token)
        elif source[index] == "'":
            index = _skip_char_or_lifetime(source, index, tokens)
        else:
            index = _read_identifier_or_punctuation(source, index, tokens)
    return tokens


def _skip_block_comment(source: str, start: int) -> int:
    depth = 1
    index = start + 2
    while index < len(source) and depth:
        if source.startswith("/*", index):
            depth += 1
            index += 2
        elif source.startswith("*/", index):
            depth -= 1
            index += 2
        else:
            index += 1
    return index


def _raw_string_end(source: str, start: int) -> int | None:
    index = start + 1
    while index < len(source) and source[index] == "#":
        index += 1
    if index >= len(source) or source[index] != '"':
        return None
    hashes = index - start - 1
    closing = '"' + "#" * hashes
    end = source.find(closing, index + 1)
    return len(source) if end == -1 else end + len(closing)


def _read_string(source: str, start: int) -> tuple[_Token, int]:
    value: list[str] = []
    index = start + 1
    while index < len(source):
        char = source[index]
        if char == '"':
            return _Token("string", "".join(value)), index + 1
        if char in "\r\n":
            return _Token("dynamic", ""), index + 1
        if char != "\\":
            value.append(char)
            index += 1
            continue
        if index + 1 >= len(source):
            return _Token("dynamic", ""), len(source)
        escaped = source[index + 1]
        if escaped == "\n":
            index += 2
            while index < len(source) and source[index] in " \t":
                index += 1
        elif escaped in {'"', "\\"}:
            value.append(escaped)
            index += 2
        elif escaped == "n":
            value.append("\n")
            index += 2
        elif escaped == "r":
            value.append("\r")
            index += 2
        elif escaped == "t":
            value.append("\t")
            index += 2
        else:
            return _Token("dynamic", ""), _skip_quoted_string(source, index + 1)
    return _Token("dynamic", ""), len(source)


def _skip_quoted_string(source: str, start: int) -> int:
    index = start
    while index < len(source):
        if source[index] == "\\":
            index += 2
        elif source[index] == '"':
            return index + 1
        else:
            index += 1
    return len(source)


def _skip_char_or_lifetime(
    source: str,
    start: int,
    tokens: list[_Token],
) -> int:
    end = start + 1
    if end < len(source) and source[end] == "\\":
        end += 2
    else:
        end += 1
    if end < len(source) and source[end] == "'":
        return end + 1
    tokens.append(_Token("punctuation", "'"))
    return start + 1


def _read_identifier_or_punctuation(
    source: str,
    index: int,
    tokens: list[_Token],
) -> int:
    char = source[index]
    if char.isalpha() or char == "_":
        end = index + 1
        while end < len(source) and (source[end].isalnum() or source[end] == "_"):
            end += 1
        tokens.append(_Token("identifier", source[index:end]))
        return end
    tokens.append(_Token("punctuation", char))
    return index + 1
