import os
import shutil
import unittest
from src.scanner import DirectoryScanner

class TestDirectoryScanner(unittest.TestCase):
    
    def setUp(self):
        """Creates a temporary directory structure before each test runs."""
        self.test_dir = "temp_test_env"
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Create a valid Python file inside the test dir
        self.valid_file_path = os.path.join(self.test_dir, "app.py")
        with open(self.valid_file_path, "w") as f:
            f.write("# Fake backend code")
            
        # Create an ignored directory (e.g., node_modules) with a file inside it
        self.ignored_dir_path = os.path.join(self.test_dir, "node_modules")
        os.makedirs(self.ignored_dir_path, exist_ok=True)
        
        self.invalid_file_path = os.path.join(self.ignored_dir_path, "index.js")
        with open(self.invalid_file_path, "w") as f:
            f.write("// Fake node module code")

    def tearDown(self):
        """Cleans up and deletes the temporary directory after each test finishes."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_scanner_finds_valid_files_and_ignores_junk(self):
        """Verifies that DirectoryScanner grabs valid extensions and skips ignored dirs."""
        # Arrange: Initialize our production scanner pointing to our fake test directory
        scanner = DirectoryScanner(self.test_dir)
        
        # Act: Run the scanning engine
        found_files = scanner.scan_for_files()
        
        # Assert: We expect exactly 1 valid file (app.py) and 0 files from node_modules
        self.assertEqual(len(found_files), 1)
        
        # Check that the file found is indeed our valid file path
        # Using os.path.normpath to make sure the file slashes match perfectly on all operating systems
        self.assertEqual(os.path.normpath(found_files[0]), os.path.normpath(self.valid_file_path))

if __name__ == "__main__":
    unittest.main()
