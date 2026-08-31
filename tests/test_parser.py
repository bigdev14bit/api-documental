import os
import shutil
import unittest
from src.parser import RouteParser

class TestRouteParser(unittest.TestCase):

    def setUp(self):
        """Creates a temporary file containing valid and invalid route styles for testing."""
        self.test_dir = "temp_parser_env"
        os.makedirs(self.test_dir, exist_ok=True)
        self.mock_file_path = os.path.join(self.test_dir, "mock_server.py")
        
        # Injecting real-looking code containing valid routes and random junk lines
        mock_code = """
        from fastapi import FastAPI
        app = FastAPI()

        @app.get("/api/v1/health")
        def health_check():
            return {"status": "ok"}

        # This is a comment, it should be ignored
        print("Hello World")

        @app.post("/api/v1/users")
        def create_user():
            pass
            
        @app.delete("/api/v1/items/delete")
        def remove_item():
            pass
        """
        with open(self.mock_file_path, "w", encoding="utf-8") as f:
            f.write(mock_code.strip())

    def tearDown(self):
        """Cleans up and deletes the temporary files after the test runs."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_parser_extracts_correct_http_methods_and_endpoints(self):
        """Verifies that RouteParser extracts valid routes precisely and maps them correctly."""
        # Arrange: Setup parser instance
        parser = RouteParser()
        
        # Act: Process the fake python server file
        discovered_routes = parser.parse_file(self.mock_file_path)
        
        # Assert: We expect exactly 3 routes to be extracted from our mock code
        self.assertEqual(len(discovered_routes), 3)
        
        # Validate the first route details
        self.assertEqual(discovered_routes[0]["method"], "GET")
        self.assertEqual(discovered_routes[0]["endpoint"], "/api/v1/health")
        self.assertEqual(discovered_routes[0]["source_file"], self.mock_file_path)
        
        # Validate the remaining HTTP methods to ensure no pattern mismatches
        self.assertEqual(discovered_routes[1]["method"], "POST")
        self.assertEqual(discovered_routes[2]["method"], "DELETE")

if __name__ == "__main__":
    unittest.main()
