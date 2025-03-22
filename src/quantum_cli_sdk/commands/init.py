"""
Project scaffolding command for Quantum CLI SDK.

This module provides functionality to initialize new quantum computing projects
with the proper folder structure and starter files.
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

# Project templates
TEMPLATES = {
    "basic": {
        "name": "Basic Quantum Project",
        "description": "A simple quantum computing project with basic circuit creation and simulation",
        "files": [
            {"name": "main.py", "template": "basic_main.py"},
            {"name": "circuits/bell.py", "template": "circuits/basic_bell.py"},
            {"name": "circuits/__init__.py", "template": "circuits/init.py"},
            {"name": "utils/__init__.py", "template": "utils/init.py"},
            {"name": "utils/visualization.py", "template": "utils/basic_visualization.py"},
            {"name": "README.md", "template": "basic_readme.md"},
            {"name": "requirements.txt", "template": "basic_requirements.txt"},
        ],
        "dirs": ["circuits", "utils", "results"]
    },
    "advanced": {
        "name": "Advanced Quantum Project",
        "description": "A comprehensive quantum computing project with error mitigation, visualization, and hardware execution",
        "files": [
            {"name": "main.py", "template": "advanced_main.py"},
            {"name": "circuits/bell.py", "template": "circuits/advanced_bell.py"},
            {"name": "circuits/ghz.py", "template": "circuits/advanced_ghz.py"},
            {"name": "circuits/qft.py", "template": "circuits/advanced_qft.py"},
            {"name": "circuits/__init__.py", "template": "circuits/init.py"},
            {"name": "utils/__init__.py", "template": "utils/init.py"},
            {"name": "utils/visualization.py", "template": "utils/advanced_visualization.py"},
            {"name": "utils/error_mitigation.py", "template": "utils/error_mitigation.py"},
            {"name": "tests/__init__.py", "template": "tests/init.py"},
            {"name": "tests/test_circuits.py", "template": "tests/test_circuits.py"},
            {"name": "README.md", "template": "advanced_readme.md"},
            {"name": "requirements.txt", "template": "advanced_requirements.txt"},
            {"name": "setup.py", "template": "advanced_setup.py"},
            {"name": "quantum_config.yaml", "template": "advanced_config.yaml"},
        ],
        "dirs": ["circuits", "utils", "tests", "results", "data"]
    },
    "algorithm": {
        "name": "Quantum Algorithm Project",
        "description": "A project focused on implementing and optimizing quantum algorithms",
        "files": [
            {"name": "main.py", "template": "algorithm_main.py"},
            {"name": "algorithms/__init__.py", "template": "algorithms/init.py"},
            {"name": "algorithms/grover.py", "template": "algorithms/grover.py"},
            {"name": "algorithms/shor.py", "template": "algorithms/shor.py"},
            {"name": "algorithms/vqe.py", "template": "algorithms/vqe.py"},
            {"name": "utils/__init__.py", "template": "utils/init.py"},
            {"name": "utils/visualization.py", "template": "utils/advanced_visualization.py"},
            {"name": "README.md", "template": "algorithm_readme.md"},
            {"name": "requirements.txt", "template": "algorithm_requirements.txt"},
            {"name": "quantum_config.yaml", "template": "algorithm_config.yaml"},
        ],
        "dirs": ["algorithms", "utils", "results", "benchmarks"]
    }
}

# Template files directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "projects"


def list_templates() -> Dict[str, Dict[str, Any]]:
    """List all available project templates.
    
    Returns:
        Dictionary of available templates with their descriptions
    """
    try:
        print("Available quantum project templates:")
        print("=" * 60)
        for key, template in TEMPLATES.items():
            print(f"{key}: {template['name']}")
            print(f"  Description: {template['description']}")
            print("-" * 60)
        return TEMPLATES
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        return {}


def _ensure_template_dir() -> None:
    """Ensure template directory exists."""
    if not TEMPLATE_DIR.exists():
        TEMPLATE_DIR.mkdir(parents=True)
        logger.info(f"Created template directory: {TEMPLATE_DIR}")


def _create_template_file(template_name: str, dest_path: Path, template_file: str) -> None:
    """
    Create a file from a template.
    
    Args:
        template_name: Name of the project template (basic, advanced, etc.)
        dest_path: Destination path for the file
        template_file: Template file name
    """
    # For now, use placeholder content
    # In a real implementation, you would load from actual template files
    
    content = f"# Quantum CLI SDK Project: {template_name}\n"
    
    if template_file.endswith("main.py"):
        content = """#!/usr/bin/env python3
'''
Main module for quantum project.
'''

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    '''Main function.'''
    print("Quantum project initialized successfully!")
    
if __name__ == "__main__":
    main()
"""
    
    elif template_file.endswith("bell.py"):
        content = """'''
Bell state preparation circuit.
'''

def create_bell_circuit(num_qubits=2):
    '''
    Create a Bell state circuit.
    
    Args:
        num_qubits: Number of qubits (default: 2)
        
    Returns:
        Bell state circuit
    '''
    # In a real implementation, this would create an actual quantum circuit
    print(f"Creating Bell state with {num_qubits} qubits")
    
    # Placeholder for circuit creation
    circuit = {
        "name": "Bell State",
        "qubits": num_qubits,
        "gates": [
            {"name": "h", "qubits": [0]},
            {"name": "cx", "qubits": [0, 1]}
        ]
    }
    
    return circuit
"""
    
    elif template_file.endswith("requirements.txt"):
        content = """# Project dependencies
quantum-cli-sdk>=1.0.0
matplotlib>=3.5.0
numpy>=1.20.0
pytest>=7.0.0
"""
    
    elif template_file.endswith("README.md"):
        content = f"""# {template_name.capitalize()} Quantum Project

This project was generated using Quantum CLI SDK's project scaffolding tool.

## Setup

1. Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the main script:
```
python main.py
```

## Project Structure

- `main.py`: Entry point for the application
- `circuits/`: Quantum circuit definitions
- `utils/`: Utility functions
- `results/`: Directory for saving results

## License

MIT
"""
    elif "init.py" in template_file:
        content = """'''
Package initialization.
'''

# Import key components for easier access
"""
    
    # Create parent directory if it doesn't exist
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    # Write content to file
    with open(dest_path, 'w') as f:
        f.write(content)
    
    logger.debug(f"Created file: {dest_path}")


def init_project(template_name: str, project_dir: str = ".", overwrite: bool = False) -> bool:
    """
    Initialize a new quantum computing project.
    
    Args:
        template_name: Name of the template to use (basic, advanced, algorithm)
        project_dir: Directory to create the project in (default: current directory)
        overwrite: Whether to overwrite existing files (default: False)
        
    Returns:
        True if successful, False otherwise
    """
    if template_name not in TEMPLATES:
        logger.error(f"Template '{template_name}' not found. Use 'init list' to see available templates.")
        return False
    
    template = TEMPLATES[template_name]
    project_path = Path(project_dir).resolve()
    
    logger.info(f"Initializing {template['name']} project in {project_path}")
    
    try:
        # Check if project directory exists and create if necessary
        project_path.mkdir(exist_ok=True)
        
        # Create directories
        for dir_name in template.get("dirs", []):
            dir_path = project_path / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True)
                logger.debug(f"Created directory: {dir_path}")
        
        # Create files
        for file_info in template.get("files", []):
            file_path = project_path / file_info["name"]
            
            if file_path.exists() and not overwrite:
                logger.warning(f"File already exists, skipping: {file_path}")
                continue
            
            _create_template_file(template_name, file_path, file_info["template"])
        
        logger.info(f"Project initialized successfully in {project_path}")
        print(f"\nProject '{template['name']}' initialized successfully in {project_path}")
        print("\nNext steps:")
        print("1. Review the generated files and customize them for your project")
        print("2. Install dependencies with: pip install -r requirements.txt")
        print("3. Start developing your quantum application!")
        
        return True
    
    except Exception as e:
        logger.error(f"Error initializing project: {e}")
        return False 