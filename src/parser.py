import re

class RouteParser:
    def __init__(self):
        """Initializes the engine with deterministic regex patterns for routing."""
        # This pattern catches: @app.get("/endpoint") or @app.post("/api/v1/data")
        self.python_route_pattern = r'@app\.(get|post|put|delete)\("([^"]+)"\)'

    def parse_file(self, file_path: str) -> list:
        """
        Reads a single source file line-by-line.
        Extracts HTTP methods and endpoints matching the route pattern.
        """
        routes_found = []
        
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    # Strip whitespace from the line for faster evaluation
                    clean_line = line.strip()
                    
                    # Search the line for our regex pattern
                    match = re.search(self.python_route_pattern, clean_line)
                    
                    if match:
                        # Extract the data from our two regex capture groups
                        http_method = match.group(1).upper() # Converts 'get' to 'GET'
                        endpoint_path = match.group(2)        # Extracts the raw URL string
                        
                        # Package the metadata cleanly
                        route_data = {
                            "method": http_method,
                            "endpoint": endpoint_path,
                            "source_file": file_path
                        }
                        routes_found.append(route_data)
                        
        except Exception as e:
            # Captures file corruption, syntax reading issues, or permission errors safely
            print(f"⚠️ Error parsing file {file_path}: {e}")
            
        return routes_found

