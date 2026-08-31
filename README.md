# 🛠️ Object-Oriented API Documenter

An automated command-line tool that scans your backend source files, parses API routing signatures using deterministic regular expressions, and builds elegant Markdown and HTML documentation instantly. No AI API keys required.

---

## 🎯 Why This Project Exists

Writing and maintaining API documentation by hand is slow and prone to human error. This tool solves that developer headache by converting your actual routing code into documentation automatically. 

By utilizing **Object-Oriented Programming (OOP)** and strict modular design, this codebase demonstrates production-level software architecture, automated testing practices, and clean CLI tooling.

---

## 🏗️ System Architecture

The application is split into highly isolated modules to maintain a strict separation of concerns:

```text
api-documenter/
├── src/                  
│   ├── main.py           # CLI Controller (argparse gateway)
│   ├── scanner.py        # File Crawler (directory tree navigation)
│   ├── parser.py         # Pattern Matcher (Regex extraction engine)
│   └── writer.py         # Document Builder (Markdown & HTML compiler)
└── tests/                
    └── test_parser.py    # Automated Suite (Unit validation)
```

1. **The Controller (`main.py`):** Coordinates user flags and directs the data pipeline.
2. **The Scanner (`scanner.py`):** Safely crawls directories while filtering out junk paths like `.git` and `__pycache__`.
3. **The Parser (`parser.py`):** Evaluates code lines deterministically using optimized regular expressions.
4. **The Writer (`writer.py`):** Uses structured string building to compile markdown tables and clean, dark-themed HTML files.

---

## 🚀 Planned Features & Roadmap

- [ ] **Recursive File Scanner:** Smart traversal that skips hidden system folders.
- [ ] **Regex Routing Parser:** Support for Python frameworks (FastAPI/Flask) and Node.js (Express).
- [ ] **Markdown Generator:** Clean, tabular API overview summaries.
- [ ] **Mini-Frontend Export:** Single-file standalone HTML layout with a built-in dark mode theme.
- [ ] **Robust Test Suite:** Comprehensive edge-case handling using Python's `unittest` framework.

---

## 💻 Tech Stack & Ecosystem

- **Language:** Python 🐍
- **Core Modules:** `re` (Regular Expressions), `argparse` (CLI parsing), `os` (File System operations)
- **Testing:** `unittest`
- **Frontend Assets:** Core HTML5 & Semantic CSS3 for the standalone documentation layout

---

