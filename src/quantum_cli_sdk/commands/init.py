"""
Project scaffolding command for Quantum CLI SDK.

This module provides functionality to initialize new quantum computing projects
with the proper folder structure and starter files based on the standard Quantum App layout.
"""

import os
import sys
import shutil
import logging
from pathlib import Path
# Remove unused typing import: from typing import Optional, List, Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

# Define default content for files
DEFAULT_GITIGNORE = """\
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/version info into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# PEP 582; used by PDM, PEP 582 proposal
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static analysis results
.pytype/

# Cython debug symbols
cython_debug/
"""

DEFAULT_README = """\
# {project_name}

A quantum application initialized with the Quantum CLI SDK.

## Project Structure

- **.github/workflows**: CI/CD pipeline configurations.
- **dist**: Build distribution artifacts.
- **ir/openqasm**: Intermediate Representation (OpenQASM) files after processing steps.
- **microservice**: Dockerized API wrapper for the quantum application.
- **results**: Output data from simulations, analysis, etc.
- **source/circuits**: Original quantum circuit source code.
- **tests**: Unit and integration tests for the quantum application.
- **.gitignore**: Specifies intentionally untracked files that Git should ignore.
- **README.md**: This file.
- **requirements.txt**: Project dependencies.

## Getting Started

1.  Set up your Python environment.
2.  Install dependencies: `pip install -r requirements.txt`
3.  Develop your circuits in `source/circuits/`.
4.  Use `quantum-cli-sdk` commands to process, test, and deploy.
"""

DEFAULT_REQUIREMENTS = """\
# Add project dependencies here
# Example:
# qiskit>=1.0.0
# cirq>=1.0.0
# amazon-braket-sdk>=1.60.0
"""

DEFAULT_DOCKERFILE = """\
# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the microservice requirements file into the container at /app
COPY microservice/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the microservice source code and other necessary files into the container at /app
# Adjust the COPY instructions based on your microservice structure
COPY microservice/src/ ./src
COPY ir/ ./ir
# Add other COPY lines if your microservice needs access to other parts of the project

# Make port 80 available to the world outside this container (if applicable)
# EXPOSE 80

# Define environment variable
ENV NAME QuantumMicroservice

# Run the application when the container launches
# Replace main.py with the entry point of your microservice
# CMD ["python", "src/main.py"]
"""

DEFAULT_PIPELINE_YML = """\
name: Basic CI/CD Pipeline

on: [push, pull_request]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        # Add commands to install test dependencies if needed
    - name: Run placeholder step
      run: echo "Replace with build, lint, test steps"
      # Example: Linting
      # run: pylint src/ tests/
      # Example: Testing
      # run: pytest tests/
"""

# Define the standard Quantum App template structure directly
QUANTUM_APP_TEMPLATE = {
    "name": "Standard Quantum Application",
    "description": "A standard quantum application structure including IR processing, microservice, results, source, and tests.",
    "files": [
        {"name": ".gitignore", "content": DEFAULT_GITIGNORE},
        {"name": "README.md", "content": DEFAULT_README},
        {"name": "requirements.txt", "content": DEFAULT_REQUIREMENTS},
        {"name": ".github/workflows/e2e-enhanced-pipeline.yml", "content": DEFAULT_PIPELINE_YML},
        {"name": ".github/workflows/e2e-pipeline.yml", "content": DEFAULT_PIPELINE_YML},
        {"name": "microservice/Dockerfile", "content": DEFAULT_DOCKERFILE},
        {"name": "microservice/requirements.txt", "content": DEFAULT_REQUIREMENTS},
    ],
    "dirs": [
        ".github/workflows",
        "dist",
        "ir/openqasm/adapted",
        "ir/openqasm/finetuned",
        "ir/openqasm/mitigated",
        "ir/openqasm/optimized",
        "microservice/src",
        "microservice/tests",
        "results/benchmarking",
        "results/cost_estimation",
        "results/finetuning",
        "results/resource_estimation",
        "results/security",
        "results/simulation/base",
        "results/simulation/mitigated",
        "results/simulation/optimized",
        "results/tests",
        "results/validation",
        "source/circuits",
        "tests",
    ]
}

# Removed TEMPLATES dictionary and TEMPLATE_DIR constant

# Removed list_templates function

# Removed _ensure_template_dir function

# Removed _create_template_file function


def init_project(project_dir: str = ".", overwrite: bool = False) -> bool:
    """
    Initialize a new quantum computing project using the standard Quantum App structure.
    
    Args:
        project_dir: Directory to create the project in (default: current directory).
        overwrite: Whether to overwrite existing files/directories (default: False).
        
    Returns:
        True if successful, False otherwise.
    """
    # Use the single defined template
    template = QUANTUM_APP_TEMPLATE
    template_name = "quantum_app" # For logging purposes

    project_path = Path(project_dir).resolve()
    project_name = project_path.name

    # Check if project directory exists and is not empty (unless overwrite is True)
    if project_path.exists() and any(project_path.iterdir()) and not overwrite:
        logger.error(f"Project directory {project_path} already exists and is not empty. Use --overwrite to proceed.")
        print(f"Error: Project directory '{project_path}' already exists and is not empty.", file=sys.stderr)
        print("Use --overwrite option to initialize anyway.", file=sys.stderr)
        return False
    elif project_path.exists() and not project_path.is_dir():
         logger.error(f"Path {project_path} exists but is not a directory.")
         print(f"Error: Path '{project_path}' exists but is not a directory.", file=sys.stderr)
         return False


    # Create project directory if it doesn't exist
    project_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Initializing project '{project_name}' using template '{template_name}' in {project_path}")

    try:
        # Create directories
        for dir_path in template["dirs"]:
            full_dir_path = project_path / dir_path
            # Check if path exists and if overwrite is False
            if full_dir_path.exists() and not overwrite:
                 if full_dir_path.is_dir():
                     logger.warning(f"Directory {full_dir_path} already exists. Skipping creation.")
                     continue # Skip directory creation, but might still add .gitkeep
                 else:
                     logger.error(f"Path {full_dir_path} exists but is not a directory. Cannot create directory.")
                     print(f"Error: Path '{full_dir_path}' exists but is not a directory.", file=sys.stderr)
                     return False # Stop initialization if a file blocks a directory

            full_dir_path.mkdir(parents=True, exist_ok=True)
            # Create a .gitkeep file in empty directories to ensure they are tracked by Git
            # Check again if it's empty *after* ensuring the directory exists
            if not any(f for f in full_dir_path.iterdir() if f.name != '.gitkeep'):
                 (full_dir_path / ".gitkeep").touch(exist_ok=True) # Allow touching existing .gitkeep
            logger.debug(f"Ensured directory exists: {full_dir_path}")

        # Create files
        for file_info in template["files"]:
            file_path = project_path / file_info["name"]
            content = file_info["content"]
            if file_info["name"] == "README.md":
                content = content.format(project_name=project_name) # Customize README title

            # Create parent directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if file_path.exists() and not overwrite:
                logger.warning(f"File {file_path} already exists. Skipping.")
                continue
            elif file_path.exists() and file_path.is_dir():
                 logger.error(f"Path {file_path} exists but is a directory. Cannot create file.")
                 print(f"Error: Path '{file_path}' exists but is a directory.", file=sys.stderr)
                 return False # Stop initialization if a directory blocks a file


            with open(file_path, 'w') as f:
                f.write(content)
            logger.debug(f"Created file: {file_path}")

        print(f"Successfully initialized {template['name']} project '{project_name}' in {project_path}")
        print(f"To get started, navigate to the project directory:")
        print(f"  cd {project_path.relative_to(Path.cwd())}")
        return True

    except OSError as e:
        logger.error(f"OS error during project initialization: {e}")
        print(f"Error: Could not create project structure. {e}", file=sys.stderr)
        # Consider adding cleanup logic here: remove partially created structure
        return False
    except Exception as e:
        logger.error(f"Unexpected error during project initialization: {e}", exc_info=True)
        print(f"Error: An unexpected error occurred. {e}", file=sys.stderr)
        # Consider adding cleanup logic here
        return False

# Example usage (can be removed or kept for direct script execution testing)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    # Create a dummy project directory for testing
    test_project_dir = Path("./test_quantum_app_init")
    # Clean up previous test run if necessary
    if test_project_dir.exists():
        print(f"Removing existing test directory: {test_project_dir}")
        shutil.rmtree(test_project_dir)

    print("Testing standard quantum_app initialization:")
    success = init_project(project_dir=str(test_project_dir), overwrite=False) # Test without overwrite first
    if success:
        print(f"Test project created successfully at {test_project_dir.resolve()}")
        # Optional: Keep the directory for inspection
        # print("Test directory left for inspection.")
        # Optional: Clean up immediately
        # shutil.rmtree(test_project_dir)
        # print("Cleaned up test directory.")
    else:
        print("Test project initialization failed.")

    # Test overwrite scenario
    print("Testing standard quantum_app initialization with --overwrite:")
    # Ensure the directory exists to test overwrite
    test_project_dir.mkdir(exist_ok=True)
    (test_project_dir / "existing_file.txt").touch()

    success_overwrite = init_project(project_dir=str(test_project_dir), overwrite=True)
    if success_overwrite:
         print(f"Test project overwritten successfully at {test_project_dir.resolve()}")
         # Clean up the test directory afterwards
         # shutil.rmtree(test_project_dir)
         # print("Cleaned up test directory.")
    else:
        print("Test project overwrite initialization failed.")
        
    # Cleanup final test directory
    if test_project_dir.exists():
        print(f"Cleaning up final test directory: {test_project_dir}")
        shutil.rmtree(test_project_dir) 