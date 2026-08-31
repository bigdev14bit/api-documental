import os

class DirectoryScanner:
    def __init__(self, target_dir: str):
        """Initializes the scanner with a specific target directory path."""
        self.target_dir = target_dir
        
        # Directories that should never be searched (saves time and prevents crashes)
        self.ignored_dirs = {
            '.git', 
            '__pycache__', 
            'node_modules', 
            'venv', 
            '.venv', 
            'env',
            '.vscode'
        }
        
        # File extensions our documenter knows how to handle
        self.valid_extensions = {'.py', '.js'}

    def scan_for_files(self) -> list:
        """
        Crawls the target directory recursively.
        Filters out ignored paths and returns a list of valid source file paths.
        """
        valid_files = []
        
        # os.walk automatically loops through folders, sub-folders, and files
        for root, dirs, files in os.walk(self.target_dir):
            
            # OOP Tip: Modifying dirs in-place tells os.walk to completely 
            # skip crawling into those ignored directories.
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            
            for file in files:
                # Check the file extension (e.g., .py or .js)
                _, ext = os.path.splitext(file)
                if ext in self.valid_extensions:
                    # Construct the full absolute path to the file
                    full_path = os.path.join(root, file)
                    valid_files.append(full_path)
                    
        return valid_files

