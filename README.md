# API Documenter

API Documenter statically scans Python, Go, Java, JavaScript, and TypeScript
source files and generates Markdown or HTML documentation for FastAPI, Gin,
Spring MVC, and Express routes. It parses source without importing or executing
the scanned project.

## Install

```sh
python -m pip install .
```

This installs the `api-doc` command. For development, run from the repository:

```sh
PYTHONPATH=src python -m api_documenter --help
```

## Generate documentation

Scan a project and write both formats into the current directory:

```sh
api-doc scan ./my-service
```

Choose a single format and/or an output directory:

```sh
api-doc scan ./my-service --format markdown --output-dir ./docs
api-doc scan ./my-service --format html --output-dir ./docs
```

The generated files are `API_DOCUMENTATION.md` and `api_doc.html`. An empty
route scan still writes a valid document with an empty table.

## Supported frameworks and routes

| Framework | Source files | Supported route forms |
| --- | --- | --- |
| FastAPI | `.py` | Literal-path decorators such as `@app.get("/users")`, `@router.post(path="/users")`, and `@app.api_route("/users", methods=["GET", "POST"])` |
| Express | `.js`, `.jsx`, `.mjs`, `.cjs`, `.ts`, `.tsx`, `.mts`, `.cts` | Literal-path calls such as `app.get("/users", handler)`, `router.post("/users", handler)`, and `app.route("/users").get(handler).post(handler)` |
| Gin | `.go` | Literal-path calls to `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, and `OPTIONS`; literal `Group` prefixes are resolved for simple assigned groups |
| Spring MVC | `.java` | Literal `@GetMapping`, `@PostMapping`, `@PutMapping`, `@PatchMapping`, `@DeleteMapping`, and `@RequestMapping` paths; literal class-level `@RequestMapping` prefixes |

FastAPI routes marked `include_in_schema=False` are omitted. Paths that need
runtime evaluation, including variables and concatenated expressions, are
intentionally skipped. JavaScript, TypeScript, and Go parsing is lexical and
does not execute or import the scanned project. Spring MVC's Java parsing is
lexical as well: unresolved path expressions, unsupported `@RequestMapping`
forms, and class mappings with unresolved prefixes are omitted. Gin groups with
dynamic prefixes are omitted, as are routes declared through unsupported call
forms.

The CLI, normalized `Route` model, source scanner, framework adapter, and
format-specific writers are separate modules so additional framework adapters
can be added without changing the output pipeline.
