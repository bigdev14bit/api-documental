import argparse
import os
from scanner import DirectoryScanner
from parser import RouteParser
from writer import DocumentWriter



def main():
    # 1. Initialize the Command-Line Interface (CLI) configuration
    parser = argparse.ArgumentParser(
        description="🚀 Object-Oriented CLI Engine to auto-generate API documentation."
    )
    
    # Define the inputs our CLI accepts
    parser.add_argument(
        "target_dir", 
        type=str, 
        help="The path to the backend project folder you want to scan"
    )
    parser.add_argument(
        "--html-only", 
        action="store_true", 
        help="Only generate the HTML documentation explorer page"
    )
    parser.add_argument(
        "--md-only", 
        action="store_true", 
        help="Only generate the Markdown documentation table"
    )

    args = parser.parse_args()

    # Validate that the targeted directory actually exists before running the engine
    if not os.path.isdir(args.target_dir):
        print(f"❌ Error: The directory path '{args.target_dir}' does not exist.")
        return

    print("\n⚡ Starting Object-Oriented API Documenter Engine...")
    print(f"📁 Target Scan Folder: {os.path.abspath(args.target_dir)}")

    # 2. Instantiate our domain components
    scanner = DirectoryScanner(args.target_dir)
    route_parser = RouteParser()
    writer = DocumentWriter()

    # 3. Execute the data pipeline step-by-step
    print("🔍 Step 1: Scanning directory for valid code files...")
    target_files = scanner.scan_for_files()
    print(f"   -> Found {len(target_files)} valid backend source files.")

    print("🧠 Step 2: Processing and parsing API routing signatures...")
    all_discovered_routes = []
    for file_path in target_files:
        routes = route_parser.parse_file(file_path)
        all_discovered_routes.extend(routes)
    
    print(f"   -> Successfully extracted {len(all_discovered_routes)} API routes total.")

    # 4. Determine file output preferences based on user flags
    print("🎨 Step 3: Compiling output files...")
    
    # If no flags are passed, we generate both by default
    generate_all = not args.html_only and not args.md_only

    if args.md_only or generate_all:
        writer.write_markdown(all_discovered_routes)

    if args.html_only or generate_all:
        writer.write_html(all_discovered_routes)

    print("\n🏁 Process complete! Your profile-boosting portfolio artifacts are ready.\n")

if __name__ == "__main__":
    main()

