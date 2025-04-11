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
import importlib.resources # Added for accessing package data
import json
# Remove unused typing import: from typing import Optional, List, Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

# Define the assumed relative path within the package for the source pipeline file
# This path assumes the file is stored relative to the 'quantum_cli_sdk' package directory
PIPELINE_SUBPATH_PARTS = ["templates", "workflows", "e2e-pipeline.yml"]

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

This project is structured to work with the standard Quantum CLI SDK E2E pipeline.

## Project Structure

- **.github/workflows**: Contains CI/CD pipeline definitions (e.g., `e2e-pipeline.yml`).
- **dist**: Default output directory for packaged applications (`quantum-cli package create`).
- **ir/openqasm**: Stores Intermediate Representation (OpenQASM) files.
  - `*.qasm`: Base IR generated from source.
  - `optimized/*.qasm`: Optimized IR.
  - `mitigated/*.qasm`: Error-mitigated IR.
- **results**: Contains output data from various pipeline stages.
  - `validation/`: Validation results (`quantum-cli ir validate`).
  - `security/`: Security scan reports (`quantum-cli security scan`).
  - `simulation/`: Simulation results (`quantum-cli run simulate`).
    - `base/{{platform}}/*.json`
    - `optimized/{{platform}}/*.json`
    - `mitigated/{{platform}}/*.json`
  - `analysis/`: Circuit analysis results.
    - `resources/*.json`: Resource estimation (`quantum-cli analyze resources`).
    - `cost/*.json`: Cost estimation (`quantum-cli analyze cost`).
    - `benchmark/*.json`: Benchmarking results (`quantum-cli analyze benchmark`).
    - `finetuning/*.json`: Fine-tuning results (`quantum-cli ir finetune`).
  - `tests/`: Test execution results.
    - `unit/*.json`: Unit test results (`quantum-cli test run`).
    - `service/*.json`: Service test results (`quantum-cli service test-run`).
- **services**: Contains generated microservice code and tests.
  - `generated/{{circuit_name}}`: Generated service source code (`quantum-cli service generate`).
  - `generated/{{circuit_name}}/tests/`: Generated service tests (`quantum-cli service test-generate`).
- **source/circuits**: Location for your original quantum circuit source files (e.g., Python scripts).
- **tests**: Contains generated test code.
  - `generated/*.py`: Generated unit tests (`quantum-cli test generate`).
- **.gitignore**: Specifies intentionally untracked files for Git.
- **quantum_manifest.json**: Project metadata and configuration for quantum microservices.
- **README.md**: This file.
- **requirements.txt**: Project dependencies (install using `pip install -r requirements.txt`).

## Getting Started

1.  **Set up Environment**: Ensure you have Python 3.10+ and potentially a virtual environment.
2.  **Install Dependencies**: `pip install -r requirements.txt` (add `quantum-cli-sdk` and your quantum framework like `qiskit` here).
3.  **Develop Circuits**: Place your quantum circuit source files (e.g., `.py`) in `source/circuits/`.
4.  **Run Pipeline**: Use `quantum-cli-sdk` commands or push changes to trigger the `.github/workflows/e2e-pipeline.yml` pipeline.

"""

DEFAULT_REQUIREMENTS = """\
# Add project dependencies here
# Essential:
# quantum-cli-sdk

# Choose your framework(s):
# qiskit>=1.0.0
# cirq-core>=1.0.0
# amazon-braket-sdk>=1.60.0

# For running tests generated by the pipeline:
# pytest
"""

# Default pipeline content (used as fallback if reading from package data fails)
DEFAULT_PIPELINE_YML = """\
# --- PLACEHOLDER CONTENT ---
# This content is used if the init command failed to read the actual pipeline template
# from the SDK's package data. Please ensure the SDK is installed correctly
# and includes the pipeline file at: quantum_cli_sdk/{'/'.join(PIPELINE_SUBPATH_PARTS)}
name: Placeholder E2E Pipeline

on: [push]

jobs:
  placeholder:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "***********************************************************"
          echo "WARNING: Using placeholder e2e-pipeline.yml."
          echo "The 'quantum-cli init' command could not find the pipeline template in the SDK package data."
          echo "Expected location relative to SDK install: quantum_cli_sdk/{'/'.join(PIPELINE_SUBPATH_PARTS)}"
          echo "Please ensure the SDK is installed correctly."
          echo "***********************************************************"
          exit 1 # Optionally fail the job if the placeholder is used
"""

# Define the standard Quantum App template structure directly
QUANTUM_APP_TEMPLATE = {
    "name": "Standard Quantum Application",
    "description": "A standard quantum application structure aligned with the E2E pipeline.",
    "files": [
        {"name": ".gitignore", "content": DEFAULT_GITIGNORE},
        {"name": "README.md", "content": DEFAULT_README},
        {"name": "requirements.txt", "content": DEFAULT_REQUIREMENTS},
        # The actual content for e2e-pipeline.yml will be loaded dynamically
        # The 'content' key here provides the fallback placeholder
        {"name": ".github/workflows/e2e-pipeline.yml", "content": DEFAULT_PIPELINE_YML},
    ],
    "dirs": [
        ".github/workflows",
        "dist", # For package output
        "ir/openqasm/base", # Base IR
        "ir/openqasm/optimized", # Optimized IR
        "ir/openqasm/mitigated", # Mitigated IR
        "results/validation",
        "results/security",
        "results/simulation/base", # Platform subdirs created by pipeline
        "results/simulation/optimized",
        "results/simulation/mitigated",
        "results/analysis/resources",
        "results/analysis/cost",
        "results/analysis/benchmark",
        "results/analysis/finetuning",
        "results/tests/unit",
        "source/circuits", # User's source code
        "tests" # For generated unit tests
    ]
}

def init_project(project_dir: str = ".", overwrite: bool = False) -> bool:
    """
    Initialize a new quantum computing project using the standard Quantum App structure.

    Args:
        project_dir: Directory to create the project in (default: current directory).
        overwrite: Whether to overwrite existing files/directories (default: False).

    Returns:
        True if successful, False otherwise.
    """
    template = QUANTUM_APP_TEMPLATE
    template_name = "quantum_app"

    project_path = Path(project_dir).resolve()
    project_name = project_path.name

    # Directory existence checks (as before)
    if project_path.exists() and any(project_path.iterdir()) and not overwrite:
        logger.error(f"Project directory {project_path} already exists and is not empty. Use --overwrite to proceed.")
        print(f"Error: Project directory '{project_path}' already exists and is not empty.", file=sys.stderr)
        print("Use --overwrite option to initialize anyway.", file=sys.stderr)
        return False
    elif project_path.exists() and not project_path.is_dir():
         logger.error(f"Path {project_path} exists but is not a directory.")
         print(f"Error: Path '{project_path}' exists but is not a directory.", file=sys.stderr)
         return False

    project_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Initializing project '{project_name}' using template '{template_name}' in {project_path}")

    try:
        # Create directories (as before, including .gitkeep)
        for dir_path in template["dirs"]:
            full_dir_path = project_path / dir_path
            if full_dir_path.exists() and not overwrite:
                 if full_dir_path.is_dir():
                     logger.warning(f"Directory {full_dir_path} already exists. Skipping creation.")
                     continue
                 else:
                     logger.error(f"Path {full_dir_path} exists but is not a directory. Cannot create directory.")
                     print(f"Error: Path '{full_dir_path}' exists but is not a directory.", file=sys.stderr)
                     return False
            full_dir_path.mkdir(parents=True, exist_ok=True)
            if not any(f for f in full_dir_path.iterdir() if f.name != '.gitkeep'):
                 (full_dir_path / ".gitkeep").touch(exist_ok=True)
            logger.debug(f"Ensured directory exists: {full_dir_path}")

        # Create files
        for file_info in template["files"]:
            file_path = project_path / file_info["name"]
            content = file_info["content"]

            # --- Special handling for e2e-pipeline.yml --- Start
            if file_info["name"] == ".github/workflows/e2e-pipeline.yml":
                pipeline_content_loaded = False
                try:
                    # Correct way to access nested package data using Traversable
                    package_root = importlib.resources.files('quantum_cli_sdk')
                    pipeline_file_traversable = package_root
                    for part in PIPELINE_SUBPATH_PARTS:
                        pipeline_file_traversable = pipeline_file_traversable.joinpath(part)

                    if pipeline_file_traversable.is_file():
                        content = pipeline_file_traversable.read_text(encoding='utf-8')
                        pipeline_content_loaded = True
                        logger.info(f"Loaded pipeline template from package data: quantum_cli_sdk/{'/'.join(PIPELINE_SUBPATH_PARTS)}")
                    else:
                         logger.warning(f"Pipeline template path exists but is not a file: quantum_cli_sdk/{'/'.join(PIPELINE_SUBPATH_PARTS)}")
                except ModuleNotFoundError:
                     logger.error(f"Package 'quantum_cli_sdk' not found. Cannot load pipeline template.")
                except FileNotFoundError:
                    logger.warning(f"Could not find pipeline template in package data at 'quantum_cli_sdk/{'/'.join(PIPELINE_SUBPATH_PARTS)}'. Using default placeholder content.")
                except Exception as e:
                    logger.error(f"Error reading pipeline template from package data: {e}. Using default placeholder content.", exc_info=True)

                if not pipeline_content_loaded:
                    logger.warning(f"Writing placeholder content to {file_path}")
            # --- Special handling for e2e-pipeline.yml --- End

            # Handle README.md formatting (as before)
            elif file_info["name"] == "README.md":
                try:
                    content = content.format(project_name=project_name)
                except KeyError as e:
                    logger.error(f"README template formatting error (unexpected placeholder: {e}). Using raw template.", exc_info=True)

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # File existence checks (as before)
            if file_path.exists() and not overwrite:
                logger.warning(f"File {file_path} already exists. Skipping.")
                continue
            elif file_path.exists() and file_path.is_dir():
                 logger.error(f"Path {file_path} exists but is a directory. Cannot create file.")
                 print(f"Error: Path '{file_path}' exists but is a directory.", file=sys.stderr)
                 return False

            # Write the file content (either default, formatted, or loaded)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.debug(f"Created file: {file_path}")
            except IOError as e:
                 logger.error(f"Failed to write file {file_path}: {e}")
                 print(f"Error: Failed to write file '{file_path}': {e}", file=sys.stderr)
                 return False
        
        # Create quantum_manifest.json
        manifest_path = project_path / "quantum_manifest.json"
        if manifest_path.exists() and not overwrite:
            logger.warning(f"Quantum manifest {manifest_path} already exists. Skipping.")
        else:
            try:
                # Import the create_quantum_manifest function from microservice module
                try:
                    from .microservice import create_quantum_manifest
                    # Create the manifest file
                    create_quantum_manifest(app_root=str(project_path), circuit_name=project_name)
                    logger.info(f"Created quantum manifest at {manifest_path}")
                except ImportError:
                    # If import fails, create manifest directly
                    logger.warning("Could not import create_quantum_manifest. Creating manifest directly.")
                    default_manifest = {
                        "app_name": project_name,
                        "app_description": f"Quantum application for {project_name}",
                        "application_type": "circuit",
                        "author": "Quantum CLI SDK User",
                        "version": "0.1.0",
                        "application_source_type": "openqasm",
                        "application_source_file": f"{project_name}.qasm",
                        "input": {
                            "format": "json",
                            "parameters": {
                                "shots": 1024,
                                "simulator": "qiskit"
                            }
                        },
                        "expected_output": {
                            "format": "json",
                            "example": {
                                "counts": {"00": 512, "11": 512},
                                "execution_time": 0.05
                            }
                        },
                        "quantum_cli_sdk_version": "latest",
                        "preferred_hardware": "simulator",
                        "compatible_hardware": ["simulator", "qiskit", "cirq", "braket"],
                        "keywords": ["quantum", "circuit"],
                        "license": "MIT",
                        "readme": f"# {project_name}\n\nQuantum circuit project generated by quantum-cli-sdk."
                    }
                    
                    with open(manifest_path, 'w', encoding='utf-8') as f:
                        json.dump(default_manifest, f, indent=2)
                    logger.info(f"Created quantum manifest (direct method) at {manifest_path}")
            except Exception as e:
                logger.error(f"Failed to create quantum manifest: {e}")
                print(f"Warning: Failed to create quantum manifest: {e}", file=sys.stderr)
                # Continue execution - manifest is helpful but not critical

        print(f"Successfully initialized {template['name']} project '{project_name}' in {project_path}")
        print(f"To get started, navigate to the project directory:")
        # Prefer relative path for cd command if possible
        try:
            relative_path = project_path.relative_to(Path.cwd())
        except ValueError:
            relative_path = project_path # Use absolute if not under cwd
        print(f"  cd {relative_path}")
        return True

    except OSError as e:
        logger.error(f"OS error during project initialization: {e}")
        print(f"Error: Could not create project structure. {e}", file=sys.stderr)
        return False
    except Exception as e:
        logger.error(f"Unexpected error during project initialization: {e}", exc_info=True)
        print(f"Error: An unexpected error occurred. {e}", file=sys.stderr)
        return False

# Test block
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    test_dir_name = "test_quantum_app_init"
    test_dir_path = Path(test_dir_name)

    if test_dir_path.exists():
        print(f"Cleaning up previous test directory: {test_dir_name}")
        shutil.rmtree(test_dir_path)

    print(f"\nTesting standard quantum_app initialization:")
    success = init_project(project_dir=test_dir_name)
    if success:
        print(f"Test project created successfully at {test_dir_path.resolve()}")
        # Check pipeline content
        try:
            pipeline_file = test_dir_path / ".github/workflows/e2e-pipeline.yml"
            if pipeline_file.exists():
                pipeline_content = pipeline_file.read_text(encoding='utf-8')
                if "PLACEHOLDER CONTENT" in pipeline_content:
                     print("WARNING: Initialized pipeline contains PLACEHOLDER content. Package data likely missing or path incorrect.")
                     print(f"         Expected relative path in package: quantum_cli_sdk/{'/'.join(PIPELINE_SUBPATH_PARTS)}")
                else:
                     print("INFO: Initialized pipeline appears to contain actual content from package data.")
            else:
                print("ERROR: Pipeline file was not created.")
        except Exception as e:
            print(f"ERROR: Could not read or check generated pipeline file: {e}")
    else:
        print("Test project initialization failed.")

    if success:
        print(f"\nTesting standard quantum_app initialization with --overwrite:")
        overwrite_success = init_project(project_dir=test_dir_name, overwrite=True)
        if overwrite_success:
            print(f"Test project overwritten successfully at {test_dir_path.resolve()}")
        else:
            print("Test project overwrite initialization failed.")

    if test_dir_path.exists():
        print(f"\nCleaning up final test directory: {test_dir_name}")
        shutil.rmtree(test_dir_path) 