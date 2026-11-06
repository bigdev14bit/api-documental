# API Documenter

API Documenter statically scans Python source files and generates Markdown or
HTML documentation for FastAPI-style routes. It parses source with Python's
AST and never imports or executes the scanned project.

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

## Supported routes

The initial adapter recognizes literal-path FastAPI-style decorators such as
`@app.get("/users")`, `@router.post(path="/users")`, and
`@app.api_route("/users", methods=["GET", "POST"])`. Routes marked
`include_in_schema=False` are omitted. Dynamic paths that cannot be resolved
without running code are intentionally skipped.

The CLI, normalized `Route` model, source scanner, framework adapter, and
format-specific writers are separate modules so additional framework adapters
can be added without changing the output pipeline.
