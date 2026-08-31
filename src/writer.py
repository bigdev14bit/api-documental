import os

class DocumentWriter:
    def __init__(self):
        """Initializes the document writing component."""
        pass

    def write_markdown(self, routes: list, output_path: str = "API_DOCUMENTATION.md") -> None:
        """Compiles the parsed routes into a clean Markdown table structure."""
        if not routes:
            print("⚠️ No routes found to write into Markdown.")
            return

        markdown_content = [
            "# 📖 Automated API Documentation\n",
            "> This document was generated automatically by the Object-Oriented API Documenter.\n",
            "| HTTP Method | API Endpoint URL | Source Code File Location |",
            "| :--- | :--- | :--- |"
        ]

        for route in routes:
            # Color code HTTP methods for readability inside markdown preview interfaces
            method = f"**{route['method']}**"
            line = f"| {method} | `{route['endpoint']}` | `{route['source_file']}` |"
            markdown_content.append(line)

        try:
            with open(output_path, "w", encoding="utf-8") as file:
                file.write("\n".join(markdown_content))
            print(f"✅ Success: Markdown documentation generated at -> {output_path}")
        except Exception as e:
            print(f"⚠️ Error writing Markdown file: {e}")

    def write_html(self, routes: list, output_path: str = "api_doc.html") -> None:
        """Compiles the parsed routes into a single standalone HTML/CSS page with a sleek dark theme."""
        if not routes:
            print("⚠️ No routes found to write into HTML.")
            return

        # Starting our semantic HTML page structure with high contrast embedded CSS styling
        html_start = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Live Documentation Explorer</title>
    <style>
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-blue: #38bdf8;
            --method-get: #10b981;
            --method-post: #3b82f6;
            --method-delete: #ef4444;
            --method-put: #f59e0b;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-main);
            margin: 0;
            padding: 2rem;
            line-height: 1.5;
        }
        .container {
            max-width: 1100px;
            margin: 0 auto;
        }
        header {
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--bg-secondary);
            padding-bottom: 1rem;
        }
        h1 { margin: 0 0 0.5rem 0; font-size: 2.2rem; color: var(--text-main); }
        .subtitle { color: var(--text-muted); margin: 0; }
        .route-card {
            background-color: var(--bg-secondary);
            border-radius: 8px;
            padding: 1rem 1.5rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 1.5rem;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        }
        .badge {
            font-family: monospace;
            font-weight: bold;
            font-size: 0.9rem;
            padding: 0.4rem 0.8rem;
            border-radius: 4px;
            min-width: 70px;
            text-align: center;
            color: #ffffff;
        }
        .GET { background-color: var(--method-get); }
        .POST { background-color: var(--method-post); }
        .DELETE { background-color: var(--method-delete); }
        .PUT { background-color: var(--method-put); }
        
        .endpoint {
            font-family: monospace;
            font-size: 1.1rem;
            color: var(--accent-blue);
            flex-grow: 1;
        }
        .source-location {
            font-size: 0.85rem;
            color: var(--text-muted);
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📖 API Endpoint Explorer</h1>
            <p class="subtitle">System Architecture Blueprint • Auto-Generated Artifact</p>
        </header>
        <main>
"""

        # Generate structural card layouts dynamically for every parsed route object
        card_content = []
        for route in routes:
            badge_class = route['method'] # GET, POST, etc.
            card = f"""            <div class="route-card">
                <span class="badge {badge_class}">{route['method']}</span>
                <span class="endpoint">{route['endpoint']}</span>
                <span class="source-location">{route['source_file']}</span>
            </div>"""
            card_content.append(card)

        html_end = """        </main>
    </div>
</body>
</html>"""

        # Merge the structural design arrays together
        full_html = html_start + "\n".join(card_content) + "\n" + html_end

        try:
            with open(output_path, "w", encoding="utf-8") as file:
                file.write(full_html)
            print(f"✅ Success: HTML mini-frontend generated at -> {output_path}")
        except Exception as e:
            print(f"⚠️ Error writing HTML file: {e}")

