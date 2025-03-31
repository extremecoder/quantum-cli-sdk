import os
import sys
import shutil
import tempfile
from pathlib import Path
import unittest

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quantum_cli_sdk.commands import init

class TestInitCommand(unittest.TestCase):
    """Test cases for the init command."""

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up the temporary directory after testing."""
        shutil.rmtree(self.temp_dir)
    
    def test_list_templates(self):
        """Test that listing templates returns a dictionary."""
        templates = init.list_templates()
        self.assertIsInstance(templates, dict)
        self.assertIn("basic", templates)
        self.assertIn("advanced", templates)
        self.assertIn("algorithm", templates)
    
    def test_init_project_basic(self):
        """Test initializing a basic project."""
        result = init.init_project("basic", self.temp_dir)
        self.assertTrue(result)
        
        # Check that the directories were created
        for dir_name in ["circuits", "utils", "results"]:
            dir_path = Path(self.temp_dir) / dir_name
            self.assertTrue(dir_path.exists(), f"Directory {dir_name} not created")
        
        # Check that the files were created
        for file_name in ["main.py", "README.md", "requirements.txt"]:
            file_path = Path(self.temp_dir) / file_name
            self.assertTrue(file_path.exists(), f"File {file_name} not created")
    
    def test_init_invalid_template(self):
        """Test initializing with an invalid template name."""
        result = init.init_project("nonexistent", self.temp_dir)
        self.assertFalse(result)
    
    def test_init_existing_files(self):
        """Test initializing when files already exist."""
        # Create a file that would be created by the init command
        file_path = Path(self.temp_dir) / "main.py"
        with open(file_path, "w") as f:
            f.write("# Existing content")
        
        # Initialize without overwrite
        result = init.init_project("basic", self.temp_dir, overwrite=False)
        self.assertTrue(result)
        
        # Check that the original file was not changed
        with open(file_path, "r") as f:
            content = f.read()
        self.assertEqual(content, "# Existing content")
        
        # Initialize with overwrite
        result = init.init_project("basic", self.temp_dir, overwrite=True)
        self.assertTrue(result)
        
        # Check that the file was overwritten
        with open(file_path, "r") as f:
            content = f.read()
        self.assertNotEqual(content, "# Existing content")

if __name__ == "__main__":
    unittest.main() 