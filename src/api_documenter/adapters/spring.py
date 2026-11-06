from dataclasses import dataclass
from pathlib import Path

from ..models import Route

_FIXED_METHODS = {
    "DeleteMapping": ("DELETE",),
    "GetMapping": ("GET",),
    "PatchMapping": ("PATCH",),
    "PostMapping": ("POST",),
    "PutMapping": ("PUT",),
}
_HTTP_METHODS = {
    "DELETE",
    "GET",
    "HEAD",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
    "TRACE",
}
_CLASS_MODIFIERS = {
    "abstract",
    "final",
    "private",
    "protected",
    "public",
    "sealed",
    "static",
    "strictfp",
}


@dataclass(frozen=True, slots=True)
class _Token:
    kind: str
    value: str


@dataclass(frozen=True, slots=True)
class _Annotation:
    start: int
    end: int
    name: str
    arguments: tuple[tuple[_Token, ...], ...]


@dataclass(frozen=True, slots=True)
class _Mapping:
    paths: tuple[str, ...]
    methods: tuple[str, ...]


class SpringAdapter:
    """Extract Spring MVC mappings without importing or executing project code."""

    def parse_file(self, file_path: Path, source_root: Path) -> list[Route]:
        tokens = _tokenize(file_path.read_text(encoding="utf-8"))
        annotations = _annotations(tokens)
        curly_depth, paren_depth = _depths(tokens)
        matching_braces = _matching_braces(tokens)
        source_file = file_path.relative_to(source_root).as_posix()
        routes: list[Route] = []

        for class_index, body_open, body_close in _classes(tokens, matching_braces):
            mappings = _class_mappings(
                tokens,
                class_index,
                annotations,
                curly_depth,
            )
            if mappings is None:
                continue

            body_depth = curly_depth[body_open] + 1
            for annotation in annotations.values():
                if (
                    not body_open < annotation.start < body_close
                    or curly_depth[annotation.start] != body_depth
                    or paren_depth[annotation.start] != 0
                ):
                    continue
                mapping = _mapping(annotation)
                if mapping is None or not _precedes_method(
                    tokens,
                    annotation.end,
                    body_close,
                    body_depth,
                    curly_depth,
                    paren_depth,
                    annotations,
                ):
                    continue

                for class_mapping in mappings:
                    methods = (
                        tuple(
                            method
                            for method in mapping.methods
                            if method in class_mapping.methods
                        )
                        if class_mapping.methods and mapping.methods
                        else class_mapping.methods or mapping.methods
                    )
                    if not methods:
                        continue
                    for prefix in class_mapping.paths:
                        for path in mapping.paths:
                            full_path = _join_path(prefix, path)
                            routes.extend(
                                Route(method, full_path, source_file) for method in methods
                            )

        return sorted(routes, key=lambda route: (route.path, route.method))


def _classes(
    tokens: list[_Token],
    matching_braces: dict[int, int],
) -> list[tuple[int, int, int]]:
    classes: list[tuple[int, int, int]] = []
    for index, token in enumerate(tokens):
        if token.kind != "identifier" or token.value not in {
            "class",
            "enum",
            "interface",
            "record",
        }:
            continue
        if index > 0 and tokens[index - 1].value == "@":
            continue
        if index + 1 >= len(tokens) or tokens[index + 1].kind != "identifier":
            continue

        body_open = next(
            (
                cursor
                for cursor in range(index + 2, len(tokens))
                if tokens[cursor].value == "{"
                or tokens[cursor].value == ";"
            ),
            None,
        )
        if body_open is None or tokens[body_open].value != "{":
            continue
        body_close = matching_braces.get(body_open)
        if body_close is not None:
            classes.append((index, body_open, body_close))
    return classes


def _class_mappings(
    tokens: list[_Token],
    class_index: int,
    annotations: dict[int, _Annotation],
    curly_depth: list[int],
) -> tuple[_Mapping, ...] | None:
    declaration_depth = curly_depth[class_index]
    candidates: list[_Annotation] = []
    for annotation in annotations.values():
        if (
            annotation.start >= class_index
            or curly_depth[annotation.start] != declaration_depth
            or not _is_class_prefix(tokens, annotation.end, class_index, annotations)
        ):
            continue
        if annotation.name == "RequestMapping":
            candidates.append(annotation)

    if not candidates:
        return (_Mapping(("",), ()),)

    mappings: list[_Mapping] = []
    for annotation in candidates:
        mapping = _mapping(annotation)
        if mapping is None:
            return None
        mappings.append(mapping)
    return tuple(mappings)


def _is_class_prefix(
    tokens: list[_Token],
    start: int,
    end: int,
    annotations: dict[int, _Annotation],
) -> bool:
    cursor = start
    while cursor < end:
        annotation = annotations.get(cursor)
        if annotation is not None:
            cursor = annotation.end
        elif (
            tokens[cursor].kind == "identifier"
            and tokens[cursor].value in _CLASS_MODIFIERS
        ):
            cursor += 1
        else:
            return False
    return True


def _mapping(annotation: _Annotation) -> _Mapping | None:
    paths: tuple[str, ...] | None = None
    selected_methods: tuple[str, ...] | None = None
    positional_seen = False

    for argument in annotation.arguments:
        if not argument:
            continue
        equals = _top_level_index(argument, "=")
        if equals is None:
            if positional_seen or paths is not None:
                return None
            positional_seen = True
            paths = _string_values(argument)
            if paths is None:
                return None
            continue

        key = argument[0].value if equals == 1 else ""
        value = argument[equals + 1 :]
        if not value:
            return None
        if key in {"path", "value"}:
            if paths is not None:
                return None
            paths = _string_values(value)
            if paths is None:
                return None
        elif key == "method":
            if selected_methods is not None:
                return None
            selected_methods = _request_methods(value)
            if selected_methods is None:
                return None

    if annotation.name in _FIXED_METHODS:
        if selected_methods is not None:
            return None
        methods = _FIXED_METHODS[annotation.name]
    elif annotation.name == "RequestMapping":
        methods = selected_methods or ()
    else:
        return None

    return _Mapping(paths or ("",), methods)


def _string_values(tokens: tuple[_Token, ...]) -> tuple[str, ...] | None:
    if len(tokens) == 1 and tokens[0].kind == "string":
        return (tokens[0].value,)
    if len(tokens) < 2 or tokens[0].value != "{" or tokens[-1].value != "}":
        return None
    values: list[str] = []
    for item in _split_top_level(tokens[1:-1], ","):
        if len(item) != 1 or item[0].kind != "string":
            return None
        values.append(item[0].value)
    return tuple(values)


def _request_methods(tokens: tuple[_Token, ...]) -> tuple[str, ...] | None:
    values = (tokens,)
    if len(tokens) >= 2 and tokens[0].value == "{" and tokens[-1].value == "}":
        values = tuple(_split_top_level(tokens[1:-1], ","))

    methods: list[str] = []
    for value in values:
        identifiers = [token.value for token in value if token.kind == "identifier"]
        method = identifiers[-1].upper() if identifiers else ""
        is_bare_method = len(value) == 1 and value[0].kind == "identifier"
        is_request_method = (
            len(value) >= 3
            and len(value) % 2 == 1
            and all(
                token.kind == "identifier" if index % 2 == 0 else token.value == "."
                for index, token in enumerate(value)
            )
            and value[-3].value == "RequestMethod"
        )
        if not method or method not in _HTTP_METHODS or not (
            is_bare_method or is_request_method
        ):
            return None
        methods.append(method)
    return tuple(methods)


def _precedes_method(
    tokens: list[_Token],
    start: int,
    body_close: int,
    body_depth: int,
    curly_depth: list[int],
    paren_depth: list[int],
    annotations: dict[int, _Annotation],
) -> bool:
    cursor = start
    while cursor < body_close:
        annotation = annotations.get(cursor)
        if annotation is not None:
            cursor = annotation.end
            continue
        if curly_depth[cursor] != body_depth or paren_depth[cursor] != 0:
            cursor += 1
            continue
        if tokens[cursor].value in {";", "=", "{", "}"}:
            return False
        if tokens[cursor].value == "(":
            return cursor > start and tokens[cursor - 1].kind == "identifier"
        cursor += 1
    return False


def _annotations(tokens: list[_Token]) -> dict[int, _Annotation]:
    result: dict[int, _Annotation] = {}
    for index, token in enumerate(tokens):
        if token.value != "@":
            continue
        annotation = _parse_annotation(tokens, index)
        if annotation is not None:
            result[index] = annotation
    return result


def _parse_annotation(tokens: list[_Token], start: int) -> _Annotation | None:
    cursor = start + 1
    if cursor >= len(tokens) or tokens[cursor].kind != "identifier":
        return None
    if tokens[cursor].value == "interface":
        return None
    name = tokens[cursor].value
    cursor += 1
    while (
        cursor + 1 < len(tokens)
        and tokens[cursor].value == "."
        and tokens[cursor + 1].kind == "identifier"
    ):
        name = tokens[cursor + 1].value
        cursor += 2

    arguments: tuple[tuple[_Token, ...], ...] = ()
    end = cursor
    if cursor < len(tokens) and tokens[cursor].value == "(":
        close = _matching_delimiter(tokens, cursor, "(", ")")
        if close is None:
            return None
        arguments = tuple(_split_top_level(tokens[cursor + 1 : close], ","))
        end = close + 1
    return _Annotation(start, end, name, arguments)


def _top_level_index(tokens: tuple[_Token, ...], value: str) -> int | None:
    depths = {"(": 0, "[": 0, "{": 0}
    closing = {")": "(", "]": "[", "}": "{"}
    for index, token in enumerate(tokens):
        if token.value == value and not any(depths.values()):
            return index
        if token.value in depths:
            depths[token.value] += 1
        elif token.value in closing:
            depths[closing[token.value]] -= 1
    return None


def _split_top_level(
    tokens: tuple[_Token, ...] | list[_Token],
    separator: str,
) -> list[tuple[_Token, ...]]:
    parts: list[tuple[_Token, ...]] = []
    depths = {"(": 0, "[": 0, "{": 0}
    closing = {")": "(", "]": "[", "}": "{"}
    start = 0
    for index, token in enumerate(tokens):
        if token.value == separator and not any(depths.values()):
            parts.append(tuple(tokens[start:index]))
            start = index + 1
        elif token.value in depths:
            depths[token.value] += 1
        elif token.value in closing:
            depths[closing[token.value]] -= 1
    if start < len(tokens):
        parts.append(tuple(tokens[start:]))
    return parts


def _depths(tokens: list[_Token]) -> tuple[list[int], list[int]]:
    curly: list[int] = []
    paren: list[int] = []
    curly_count = 0
    paren_count = 0
    for token in tokens:
        curly.append(curly_count)
        paren.append(paren_count)
        if token.value == "{":
            curly_count += 1
        elif token.value == "}":
            curly_count = max(0, curly_count - 1)
        elif token.value == "(":
            paren_count += 1
        elif token.value == ")":
            paren_count = max(0, paren_count - 1)
    return curly, paren


def _matching_braces(tokens: list[_Token]) -> dict[int, int]:
    openings: list[int] = []
    matching: dict[int, int] = {}
    for index, token in enumerate(tokens):
        if token.value == "{":
            openings.append(index)
        elif token.value == "}" and openings:
            matching[openings.pop()] = index
    return matching


def _matching_delimiter(
    tokens: list[_Token],
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


def _join_path(prefix: str, path: str) -> str:
    if not prefix:
        return path
    if not path:
        return prefix
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
        elif source.startswith('"""', index):
            end = source.find('"""', index + 3)
            tokens.append(_Token("dynamic", ""))
            index = len(source) if end == -1 else end + 3
        elif char == '"':
            token, index = _read_string(source, index)
            tokens.append(token)
        elif char == "'":
            _, index = _read_char(source, index)
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
        simple = {
            "b": "\b",
            "f": "\f",
            "n": "\n",
            "r": "\r",
            "s": " ",
            "t": "\t",
            '"': '"',
            "'": "'",
            "\\": "\\",
        }
        if escaped in simple:
            value.append(simple[escaped])
            index += 2
        elif escaped == "u":
            digits = source[index + 2 : index + 6]
            if len(digits) != 4 or any(
                digit not in "0123456789abcdefABCDEF" for digit in digits
            ):
                return _Token("dynamic", ""), index + 2 + len(digits)
            value.append(chr(int(digits, 16)))
            index += 6
        elif escaped in "01234567":
            end = index + 2
            while end < min(index + 4, len(source)) and source[end] in "01234567":
                end += 1
            value.append(chr(int(source[index + 1 : end], 8)))
            index = end
        else:
            return _Token("dynamic", ""), index + 2
    return _Token("dynamic", ""), len(source)


def _read_char(source: str, start: int) -> tuple[None, int]:
    index = start + 1
    while index < len(source):
        if source[index] == "\\":
            index += 2
        elif source[index] == "'":
            return None, index + 1
        elif source[index] in "\r\n":
            return None, index + 1
        else:
            index += 1
    return None, len(source)
