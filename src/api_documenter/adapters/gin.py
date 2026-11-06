from dataclasses import dataclass
from pathlib import Path

from ..models import Route

_HTTP_METHODS = {
    "DELETE",
    "GET",
    "HEAD",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
}


@dataclass(frozen=True, slots=True)
class _Token:
    kind: str
    value: str


class GinAdapter:
    """Extract Gin route calls without importing or executing project code."""

    def parse_file(self, file_path: Path, source_root: Path) -> list[Route]:
        tokens = _tokenize(file_path.read_text(encoding="utf-8"))
        routes: list[Route] = []
        group_prefixes: dict[str, str | None] = {}
        source_file = file_path.relative_to(source_root).as_posix()

        for index, token in enumerate(tokens):
            if _is_group_assignment(tokens, index):
                group_name = token.value
                receiver = tokens[index + 2].value
                path_index = index + 6
                group_path = (
                    tokens[path_index].value
                    if (
                        path_index < len(tokens)
                        and tokens[path_index].kind == "string"
                        and path_index + 1 < len(tokens)
                        and tokens[path_index + 1].value in {",", ")"}
                    )
                    else None
                )
                parent_prefix = group_prefixes.get(receiver, "")
                group_prefixes[group_name] = (
                    _join_path(parent_prefix, group_path)
                    if parent_prefix is not None and group_path is not None
                    else None
                )
                continue

            if (
                token.kind != "identifier"
                or index + 4 >= len(tokens)
                or tokens[index + 1].value != "."
                or tokens[index + 2].value not in _HTTP_METHODS
                or tokens[index + 3].value != "("
            ):
                continue

            receiver_prefix = group_prefixes.get(token.value, "")
            if receiver_prefix is None:
                continue
            path_token = tokens[index + 4]
            if (
                path_token.kind != "string"
                or index + 5 >= len(tokens)
                or tokens[index + 5].value not in {",", ")"}
            ):
                continue

            routes.append(
                Route(
                    method=tokens[index + 2].value,
                    path=_join_path(receiver_prefix, path_token.value),
                    source_file=source_file,
                )
            )

        return sorted(routes, key=lambda route: (route.path, route.method))


def _is_group_assignment(tokens: list[_Token], index: int) -> bool:
    return (
        index + 7 < len(tokens)
        and tokens[index].kind == "identifier"
        and tokens[index + 1].value in {":=", "="}
        and tokens[index + 2].kind == "identifier"
        and tokens[index + 3].value == "."
        and tokens[index + 4].value == "Group"
        and tokens[index + 5].value == "("
    )


def _join_path(prefix: str, path: str) -> str:
    if not prefix:
        return path
    return f"{prefix.rstrip('/')}/{path.lstrip('/')}"


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
        elif char in {'"', "`", "'"}:
            token, index = _read_string(source, index)
            if token is not None:
                tokens.append(token)
        elif char.isalpha() or char == "_":
            end = index + 1
            while end < len(source) and (source[end].isalnum() or source[end] == "_"):
                end += 1
            tokens.append(_Token("identifier", source[index:end]))
            index = end
        elif source.startswith(":=", index):
            tokens.append(_Token("punctuation", ":="))
            index += 2
        else:
            tokens.append(_Token("punctuation", char))
            index += 1
    return tokens


def _read_string(source: str, start: int) -> tuple[_Token | None, int]:
    quote = source[start]
    index = start + 1
    if quote == "`":
        end = source.find("`", index)
        if end == -1:
            return None, len(source)
        return _Token("string", source[index:end]), end + 1

    value: list[str] = []
    while index < len(source):
        char = source[index]
        if char == quote:
            kind = "rune" if quote == "'" else "string"
            return _Token(kind, "".join(value)), index + 1
        if char in "\r\n":
            return None, index + 1
        if char != "\\":
            value.append(char)
            index += 1
            continue
        decoded, index = _read_escape(source, index + 1)
        if decoded is None:
            return None, index
        value.append(decoded)
    return None, len(source)


def _read_escape(source: str, index: int) -> tuple[str | None, int]:
    if index >= len(source):
        return None, index
    escape = source[index]
    simple_escapes = {
        "a": "\a",
        "b": "\b",
        "f": "\f",
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "v": "\v",
        "\\": "\\",
        '"': '"',
        "'": "'",
    }
    if escape in simple_escapes:
        return simple_escapes[escape], index + 1

    if escape in {"x", "u", "U"}:
        width = {"x": 2, "u": 4, "U": 8}[escape]
        digits = source[index + 1 : index + 1 + width]
        if len(digits) != width or any(
            digit not in "0123456789abcdefABCDEF" for digit in digits
        ):
            return None, index + 1 + width
        code_point = int(digits, 16)
        if code_point > 0x10FFFF:
            return None, index + 1 + width
        return chr(code_point), index + 1 + width

    if escape in "01234567":
        digits = source[index : index + 3]
        if len(digits) != 3 or any(digit not in "01234567" for digit in digits):
            return None, index + len(digits)
        byte = int(digits, 8)
        if byte > 0xFF:
            return None, index + 3
        return chr(byte), index + 3

    return None, index + 1
