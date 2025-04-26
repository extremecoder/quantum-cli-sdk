"""
Package quantum applications for distribution.
"""

import os
import sys
import logging
import json
import shutil
import zipfile
import tarfile
import yaml
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime

from ..config import get_config
from ..utils import find_files, create_archive, setup_logger
from ..output_formatter import format_output
from ..dependency_analyzer import analyze_dependencies

# Set up logger
logger = logging.getLogger(__name__)

# Default package config
DEFAULT_PACKAGE_CONFIG = {
    "app_name": "quantum-app",
    "version": "0.1.0",
    "app_description": "Quantum application package",
    "author": "",
    "license": "MIT",
    "format": "zip",
    "include": [
        "*.qasm",
        "*.py",
        "README.md",
        "LICENSE",
        "config/*.json",
        "circuits/*.qasm"
    ],
    "exclude": [
        "__pycache__/",
        "*.pyc",
        "*.log",
        "*.tmp",
        ".git/",
        ".vscode/",
        ".idea/"
    ],
    "entrypoint": "main.py",
    "requirements": [
        "qiskit>=0.34.0",
        "numpy>=1.20.0"
    ],
    "metadata": {
        "quantum_sdk_version": "0.1.0",
        "target_platform": "any"
    }
}

def find_config_file(directory):
    """
    Find package configuration file in the directory.
    
    Args:
        directory (str): Directory to search in
        
    Returns:
        str: Path to config file, or None if not found
    """
    # Check for package configuration files in various formats
    config_names = ["quantum_manifest.json","quantum.yaml", "quantum.yml", "quantum.json", "package.yaml", "package.yml", "package.json"]
    
    for config_name in config_names:
        config_path = os.path.join(directory, config_name)
        if os.path.exists(config_path):
            return config_path
            
    return None

def load_config(config_path):
    """
    Load configuration from a file.
    
    Args:
        config_path (str): Path to config file
        
    Returns:
        dict: Configuration data
    """
    logger.info(f"Loading configuration from {config_path}")
    
    try:
        # Determine file type from extension
        ext = os.path.splitext(config_path)[1].lower()
        
        if ext in ['.yaml', '.yml']:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        elif ext == '.json':
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            logger.warning(f"Unsupported config file format: {ext}")
            return DEFAULT_PACKAGE_CONFIG
            
        # Merge with default config
        merged_config = DEFAULT_PACKAGE_CONFIG.copy()
        merged_config.update(config)
        
        return merged_config
        
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return DEFAULT_PACKAGE_CONFIG

def find_files(source_dir, include_patterns, exclude_patterns):
    """
    Find files matching include patterns and not matching exclude patterns.
    
    Args:
        source_dir (str): Source directory
        include_patterns (list): List of glob patterns to include
        exclude_patterns (list): List of glob patterns to exclude
        
    Returns:
        list: List of matching file paths
    """
    import glob
    
    matching_files = []
    source_path = Path(source_dir)
    
    # Process include patterns
    for pattern in include_patterns:
        pattern_path = os.path.join(source_dir, pattern)
        for file_path in glob.glob(pattern_path, recursive=True):
            if os.path.isfile(file_path):
                relative_path = os.path.relpath(file_path, source_dir)
                matching_files.append(relative_path)
    
    # Filter out excluded patterns
    filtered_files = []
    for file_path in matching_files:
        excluded = False
        for pattern in exclude_patterns:
            # Convert glob pattern to regex pattern
            import fnmatch
            if fnmatch.fnmatch(file_path, pattern):
                excluded = True
                break
        
        if not excluded:
            filtered_files.append(file_path)
    
    return filtered_files

def create_zip_package(source_dir, output_path, files, config):
    """
    Create a ZIP package from files.
    
    Args:
        source_dir (str): Source directory
        output_path (str): Output ZIP file path
        files (list): List of files to include
        config (dict): Package configuration
        
    Returns:
        bool: True if successful
    """
    try:
        logger.info(f"Creating ZIP package: {output_path}")
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add files
            for file_path in files:
                full_path = os.path.join(source_dir, file_path)
                if os.path.isfile(full_path):
                    zipf.write(full_path, arcname=file_path)
                    logger.debug(f"Added: {file_path}")
            
            # Add manifest
            manifest = create_manifest(config, files)
            zipf.writestr("quantum_manifest.json", json.dumps(manifest, indent=2))
            
            # Add requirements.txt if specified in config
            if "requirements" in config and config["requirements"]:
                requirements_content = "\n".join(config["requirements"])
                zipf.writestr("requirements.txt", requirements_content)
        
        logger.info(f"Package created successfully: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating ZIP package: {e}")
        return False

def create_tarball_package(source_dir, output_path, files, config):
    """
    Create a tarball package from files.
    
    Args:
        source_dir (str): Source directory
        output_path (str): Output tarball file path
        files (list): List of files to include
        config (dict): Package configuration
        
    Returns:
        bool: True if successful
    """
    try:
        logger.info(f"Creating tarball package: {output_path}")
        
        with tarfile.open(output_path, "w:gz") as tar:
            # Add files
            for file_path in files:
                full_path = os.path.join(source_dir, file_path)
                if os.path.isfile(full_path):
                    tar.add(full_path, arcname=file_path)
                    logger.debug(f"Added: {file_path}")
            
            # Add manifest
            manifest = create_manifest(config, files)
            manifest_path = os.path.join(tempfile.gettempdir(), "quantum_manifest.json")
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            tar.add(manifest_path, arcname="quantum_manifest.json")
            os.unlink(manifest_path)
            
            # Add requirements.txt if specified in config
            if "requirements" in config and config["requirements"]:
                requirements_path = os.path.join(tempfile.gettempdir(), "requirements.txt")
                with open(requirements_path, 'w') as f:
                    f.write("\n".join(config["requirements"]))
                tar.add(requirements_path, arcname="requirements.txt")
                os.unlink(requirements_path)
        
        logger.info(f"Package created successfully: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating tarball package: {e}")
        return False

def create_wheel_package(source_dir, output_path, files, config):
    """
    Create a Python wheel package.
    
    Args:
        source_dir (str): Source directory
        output_path (str): Output directory
        files (list): List of files to include
        config (dict): Package configuration
        
    Returns:
        bool: True if successful
    """
    try:
        logger.info(f"Creating wheel package in: {output_path}")
        
        # Create temporary package directory
        package_dir = os.path.join(tempfile.gettempdir(), config["app_name"].replace('-', '_'))
        os.makedirs(package_dir, exist_ok=True)
        
        # Create package structure
        src_dir = os.path.join(package_dir, config["app_name"].replace('-', '_'))
        os.makedirs(src_dir, exist_ok=True)
        
        # Copy files
        for file_path in files:
            full_path = os.path.join(source_dir, file_path)
            if os.path.isfile(full_path):
                dest_path = os.path.join(src_dir, file_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(full_path, dest_path)
                logger.debug(f"Copied: {file_path}")
        
        # Create __init__.py
        init_path = os.path.join(src_dir, "__init__.py")
        with open(init_path, 'w') as f:
            f.write(f"""# {config['app_name']} package
__version__ = "{config['version']}"
__author__ = "{config['author']}"
__description__ = "{config['app_description']}"
""")
        
        # Create manifest
        manifest = create_manifest(config, files)
        manifest_path = os.path.join(src_dir, "quantum_manifest.json")
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Create setup.py
        setup_path = os.path.join(package_dir, "setup.py")
        with open(setup_path, 'w') as f:
            f.write(f"""from setuptools import setup, find_packages

setup(
    name="{config['app_name']}",
    version="{config['version']}",
    author="{config['author']}",
    description="{config['app_description']}",
    packages=find_packages(),
    include_package_data=True,
    install_requires={repr(config['requirements'])},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: {config['license']} License",
        "Operating System :: OS Independent",
    ],
)
""")
        
        # Create MANIFEST.in
        manifest_in_path = os.path.join(package_dir, "MANIFEST.in")
        with open(manifest_in_path, 'w') as f:
            f.write("include */quantum_manifest.json\n")
            
            # Include all non-Python files
            for file_path in files:
                if not file_path.endswith('.py'):
                    f.write(f"include */{file_path}\n")
        
        # Run setuptools to build wheel
        try:
            subprocess.run(
                [sys.executable, "setup.py", "bdist_wheel"],
                cwd=package_dir,
                check=True,
                capture_output=True
            )
            
            # Copy wheel to output directory
            dist_dir = os.path.join(package_dir, "dist")
            wheel_files = os.listdir(dist_dir)
            
            if wheel_files:
                wheel_path = os.path.join(dist_dir, wheel_files[0])
                shutil.copy2(wheel_path, output_path)
                logger.info(f"Wheel package created: {os.path.join(output_path, wheel_files[0])}")
                return True
            else:
                logger.error("No wheel files found in dist directory")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error building wheel: {e.stderr.decode()}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating wheel package: {e}")
        return False
    finally:
        # Clean up temporary directory
        if os.path.exists(package_dir):
            shutil.rmtree(package_dir)

def create_manifest(config, files):
    """
    Create package manifest.
    
    Args:
        config (dict): Package configuration (parsed from source manifest)
        files (list): List of included files
        
    Returns:
        dict: Manifest data
    """
    import copy
    manifest = copy.deepcopy(config)
    # Remove unwanted fields
    for field in [
        "entrypoint", "requirements", "metadata", "include", "exclude", 
        "files", "quantum_sdk_version"
    ]:
        manifest.pop(field, None)
    return manifest

def extract_package_info(package_path):
    """
    Extract information from a package.
    
    Args:
        package_path (str): Path to the package file
        
    Returns:
        dict: Package information, or None if extraction failed
    """
    try:
        ext = os.path.splitext(package_path)[1].lower()
        
        if ext == '.zip':
            with zipfile.ZipFile(package_path, 'r') as zipf:
                if 'quantum_manifest.json' in zipf.namelist():
                    manifest_data = zipf.read('quantum_manifest.json')
                    return json.loads(manifest_data)
                    
        elif ext == '.gz' or ext == '.tar.gz':
            with tarfile.open(package_path, 'r:gz') as tar:
                if 'quantum_manifest.json' in tar.getnames():
                    manifest_file = tar.extractfile('quantum_manifest.json')
                    return json.loads(manifest_file.read())
                    
        elif ext == '.whl':
            with zipfile.ZipFile(package_path, 'r') as zipf:
                for name in zipf.namelist():
                    if name.endswith('quantum_manifest.json'):
                        manifest_data = zipf.read(name)
                        return json.loads(manifest_data)
                        
        logger.error(f"Manifest not found in package: {package_path}")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting package info: {e}")
        return None

def extract_package(package_path, output_dir, overwrite=False):
    """
    Extract a package to a directory.
    
    Args:
        package_path (str): Path to the package file
        output_dir (str): Directory to extract to
        overwrite (bool): Whether to overwrite existing files
        
    Returns:
        bool: True if extraction was successful
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        ext = os.path.splitext(package_path)[1].lower()
        
        if ext == '.zip':
            with zipfile.ZipFile(package_path, 'r') as zipf:
                # Check for existing files if not overwriting
                if not overwrite:
                    for name in zipf.namelist():
                        dest_path = os.path.join(output_dir, name)
                        if os.path.exists(dest_path):
                            logger.error(f"File already exists: {dest_path}")
                            return False
                
                # Extract all files
                zipf.extractall(output_dir)
                
        elif ext == '.gz' or ext == '.tar.gz':
            with tarfile.open(package_path, 'r:gz') as tar:
                # Check for existing files if not overwriting
                if not overwrite:
                    for name in tar.getnames():
                        dest_path = os.path.join(output_dir, name)
                        if os.path.exists(dest_path):
                            logger.error(f"File already exists: {dest_path}")
                            return False
                
                # Extract all files
                tar.extractall(output_dir)
                
        elif ext == '.whl':
            with zipfile.ZipFile(package_path, 'r') as zipf:
                # Check for existing files if not overwriting
                if not overwrite:
                    for name in zipf.namelist():
                        dest_path = os.path.join(output_dir, name)
                        if os.path.exists(dest_path):
                            logger.error(f"File already exists: {dest_path}")
                            return False
                
                # Extract all files
                zipf.extractall(output_dir)
                
        else:
            logger.error(f"Unsupported package format: {ext}")
            return False
            
        logger.info(f"Package extracted to: {output_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Error extracting package: {e}")
        return False

def package(source_dir, output_path=None, format=None, config_file=None, config_overrides=None):
    """
    Package a quantum application.
    
    Args:
        source_dir (str): Source directory
        output_path (str, optional): Output package path
        format (str, optional): Package format (zip, tar, wheel)
        config_file (str, optional): Path to config file
        config_overrides (dict, optional): Config overrides
        
    Returns:
        str: Path to created package
    """
    # Set up logger with DEBUG level since this is a development tool
    setup_logger(level=logging.DEBUG)
    
    logger.info(f"Packaging quantum application from {source_dir}")
    
    # Ensure source directory exists
    if not os.path.isdir(source_dir):
        logger.error(f"Source directory does not exist: {source_dir}")
        return None
    
    # Find or use provided config file
    if config_file:
        config_path = config_file
    else:
        config_path = find_config_file(source_dir)
    
    # Load configuration
    if config_path and os.path.isfile(config_path):
        config = load_config(config_path)
    else:
        logger.warning("No configuration file found, using defaults")
        config = DEFAULT_PACKAGE_CONFIG.copy()
    
    # Apply overrides if provided
    if config_overrides:
        config.update(config_overrides)
    
    # Override format if specified
    if format:
        config["format"] = format
    
    # Determine output path
    if not output_path:
        package_name = f"{config['app_name']}-{config['version']}"
        
        if config["format"] == "zip":
            output_path = os.path.join(os.getcwd(), f"{package_name}.zip")
        elif config["format"] == "tar":
            output_path = os.path.join(os.getcwd(), f"{package_name}.tar.gz")
        elif config["format"] == "wheel":
            output_path = os.getcwd()
        else:
            logger.error(f"Unsupported package format: {config['format']}")
            return None
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path) if config["format"] != "wheel" else output_path
    os.makedirs(output_dir, exist_ok=True)
    
    # Find files to include
    files = find_files(source_dir, config["include"], config["exclude"])
    
    if not files:
        logger.warning("No files matched the include patterns")
    
    # Create package based on format
    if config["format"] == "zip":
        success = create_zip_package(source_dir, output_path, files, config)
    elif config["format"] == "tar":
        success = create_tarball_package(source_dir, output_path, files, config)
    elif config["format"] == "wheel":
        success = create_wheel_package(source_dir, output_path, files, config)
    else:
        logger.error(f"Unsupported package format: {config['format']}")
        return None
    
    if success:
        return output_path
    else:
        return None

if __name__ == "__main__":
    # This allows the module to be run directly for testing
    if len(sys.argv) < 2:
        print("Usage: package.py <source_dir> [<output_path>] [--format <format>] [--config <config_file>]")
        sys.exit(1)
    
    # Parse arguments
    source = sys.argv[1]
    output = None
    format = None
    config = None
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--format" and i+1 < len(sys.argv):
            format = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == "--config" and i+1 < len(sys.argv):
            config = sys.argv[i+1]
            i += 2
        else:
            output = sys.argv[i]
            i += 1
    
    # Run packaging
    result = package(source, output, format, config)
    
    if result:
        print(f"Package created: {result}")
        sys.exit(0)
    else:
        print("Failed to create package")
        sys.exit(1)
