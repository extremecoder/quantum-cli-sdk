"""
Generate microservice wrapper for quantum circuits.
"""

import os
import sys
import logging
import json
import re
import shutil
import datetime
import zipfile
import tempfile
from pathlib import Path
import requests
import subprocess
from string import Template
from typing import Dict, List, Optional, Any, Union

from ..config import get_config
from ..output_formatter import format_output
from ..utils import load_config, run_docker_command

# Set up logger
logger = logging.getLogger(__name__)

# Path to templates directory
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "microservice")

# Quantum-ready Docker image with all frameworks pre-installed
QUANTUM_DOCKER_IMAGE = "quantum-cli-sdk/microservice-base:latest"

# Standard filename for the default circuit inside the generated service
DEFAULT_CIRCUIT_FILENAME_IN_SERVICE = "default_circuit.qasm"

def read_template(template_name):
    """
    Read a template file from the templates directory.
    
    Args:
        template_name (str): Name of the template file
        
    Returns:
        str: Template content, or None if file not found
    """
    template_path = os.path.join(TEMPLATES_DIR, template_name)
    try:
        with open(template_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Template file not found: {template_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading template {template_name} at {template_path}: {e}")
        return None

def extract_circuit_info(qasm_file):
    """
    Extract information about a quantum circuit from QASM file.
    
    Args:
        qasm_file (str): Path to the QASM file
        
    Returns:
        dict: Circuit information or None on failure
    """
    try:
        with open(qasm_file, 'r') as f:
            content = f.read()
            
        info = {
            "name": os.path.splitext(os.path.basename(qasm_file))[0],
            "qasm_version": None,
            "includes": [],
            "qreg_count": 0,
            "creg_count": 0,
            "parameters": [],
            "gate_types": set(),
            "has_measurements": False
        }
        
        version_match = re.search(r'OPENQASM\s+(\d+\.\d+);', content)
        if version_match:
            info["qasm_version"] = version_match.group(1)
            
        include_matches = re.findall(r'include\s+"([^\"]+)";', content)
        info["includes"] = include_matches
        
        qreg_matches = re.findall(r'qreg\s+(\w+)\[(\d+)\];', content)
        info["qreg_count"] = sum(int(size) for _, size in qreg_matches)
        
        creg_matches = re.findall(r'creg\s+(\w+)\[(\d+)\];', content)
        info["creg_count"] = sum(int(size) for _, size in creg_matches)
        
        # Improved parameter regex (handle potential spaces, different types?)
        # This is still basic and might miss complex cases.
        param_matches = re.findall(r'parameter\s+([a-zA-Z_]\w*)', content) 
        info["parameters"] = param_matches
        
        common_gates = ["h", "x", "y", "z", "cx", "rx", "ry", "rz", "u", "u1", "u2", "u3", "s", "sdg", "t", "tdg", "measure"]
        content_lower = content.lower()
        for gate in common_gates:
            # Use word boundaries and check for space/parenthesis after gate name
            pattern = r'\b' + gate + r'\b[\s\(]'
            if re.search(pattern, content_lower):
                info["gate_types"].add(gate)
                
        if "measure" in info["gate_types"]:
            info["has_measurements"] = True
            
        return info
        
    except FileNotFoundError:
        logger.error(f"Error extracting circuit info: File not found at {qasm_file}")
        return None
    except Exception as e:
        logger.error(f"Error extracting circuit info from {qasm_file}: {e}")
        return None

def generate_circuit_documentation(circuit_info):
    """
    Generate basic Markdown documentation for the circuit.
    """
    if not circuit_info:
         return "No circuit information available to generate documentation."

    name = circuit_info.get("name", "Unknown Circuit")
    qreg_count = circuit_info.get('qreg_count', 'N/A')
    creg_count = circuit_info.get('creg_count', 'N/A')
    gate_types = ', '.join(sorted(list(circuit_info.get('gate_types', set())))) or 'N/A'
    has_measurements = 'Yes' if circuit_info.get('has_measurements') else 'No'
    parameters = circuit_info.get('parameters', [])

    doc = f"""### Circuit: {name}

- **Qubits:** {qreg_count}
- **Classical Bits:** {creg_count}
- **Gate Types Used:** {gate_types}
- **Contains Measurements:** {has_measurements}
"""

    if parameters:
        doc += "\n**Parameters Found:**\n"
        for param in parameters:
            doc += f"- `{param}`\n"
    else:
        doc += "\n**Parameters Found:** None\n"
    
    return doc

def find_project_root_path(start_path):
    """Find the project root by searching upwards for requirements.txt.
    Returns the directory containing requirements.txt, or None if not found.
    """
    current = os.path.abspath(start_path)
    while True:
        req_path = os.path.join(current, 'requirements.txt')
        if os.path.exists(req_path):
            logger.debug(f"Found project root marker 'requirements.txt' at: {current}")
            return current
                
        parent = os.path.dirname(current)
        if parent == current:
            logger.debug(f"Reached filesystem root without finding requirements.txt starting from {start_path}")
            return None
        current = parent

def create_quantum_manifest(app_root, circuit_name=None):
    """
    Create a default quantum manifest file at the app root level if it doesn't exist.
    Avoids overwriting an existing manifest.
    
    Args:
        app_root (str): Application root directory
        circuit_name (str, optional): Name of the quantum circuit
        
    Returns:
        dict: Manifest data (either read or newly created)
    """
    manifest_path = os.path.join(app_root, "quantum_manifest.json")
    
    # If exists, try to load it first
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r') as f:
                manifest_data = json.load(f)
                logger.info(f"Loaded existing quantum manifest from {manifest_path}")
                return manifest_data
        except json.JSONDecodeError:
            logger.warning(f"Existing manifest file at {manifest_path} is corrupted. Creating a default one.")
        except Exception as e:
            logger.warning(f"Could not read existing manifest at {manifest_path}: {e}. Creating a default one.")

    # Default manifest structure if not loaded
    manifest_data = {
        "app_name": circuit_name or "quantum-app",
        "app_description": f"Quantum application wrapping the {circuit_name or 'default'} circuit.",
        "application_type": "microservice", # Changed from 'circuit'
        "author": "Quantum CLI SDK User",
        "version": "0.1.0",
        "application_source_type": "openqasm",
        "application_source_file": DEFAULT_CIRCUIT_FILENAME_IN_SERVICE, # Point to the standard internal name
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
        "quantum_cli_sdk_version": "(generated)", # Placeholder
        "preferred_hardware": "simulator",
        "compatible_hardware": ["simulator", "qiskit", "cirq", "braket"],
        "keywords": ["quantum", "microservice", circuit_name or "generated"],
        "license": "MIT",
        "readme": f"# {circuit_name or 'Quantum Microservice'}\n\nGenerated by quantum-cli-sdk. See service README.md for details."
    }
    
    # Write the default manifest to file
    try:
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)
        logger.info(f"Created default quantum manifest at {manifest_path}")
    except Exception as e:
        logger.error(f"Error creating default quantum manifest at {manifest_path}: {e}")
        # Return the data anyway, even if write failed
    
    return manifest_data

def load_quantum_manifest(app_root, circuit_name=None, extracted_data=None):
    """
    Load the quantum manifest file, or create a default one if not found.
    Prioritizes manifest from extracted zip, then app_root, then creates default.
    """
    manifest = None
    loaded_path = None
    
    # 1. Check extracted data (if from a zip)
    if extracted_data and "metadata_file" in extracted_data and extracted_data["metadata_file"]:
            metadata_file = extracted_data["metadata_file"]
            if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    if metadata_file.endswith('.json'):
                        manifest = json.load(f)
                        loaded_path = metadata_file
                        logger.info(f"Loaded quantum manifest from extracted zip: {loaded_path}")
                    else:
                        logger.warning(f"Unsupported metadata format in zip: {metadata_file}")
            except json.JSONDecodeError:
                 logger.warning(f"Manifest file from zip {metadata_file} is corrupted.")
        except Exception as e:
                logger.error(f"Error loading manifest from extracted zip {metadata_file}: {e}")
    
    # 2. Check app root (if not loaded from zip)
    if not manifest:
        manifest_path_app_root = os.path.join(app_root, "quantum_manifest.json")
        if os.path.exists(manifest_path_app_root):
            try:
                with open(manifest_path_app_root, 'r') as f:
                    manifest = json.load(f)
                    loaded_path = manifest_path_app_root
                    logger.info(f"Loaded quantum manifest from app root: {loaded_path}")
            except json.JSONDecodeError:
                 logger.warning(f"Manifest file from app root {manifest_path_app_root} is corrupted.")
            except Exception as e:
                logger.error(f"Error loading manifest from app root {manifest_path_app_root}: {e}")
    
    # 3. Create default if still not found
    if not manifest:
        logger.info("No existing manifest found, creating a default one.")
        manifest = create_quantum_manifest(app_root, circuit_name)
        loaded_path = os.path.join(app_root, "quantum_manifest.json") # Path where it *should* be
    
    # Return manifest data and the path it was loaded from (or intended path)
    return manifest, loaded_path 

def extract_zip_package(zip_path, output_dir):
    """
    Extract a zip package, finding QASM and manifest/metadata files.
    Handles potential errors during extraction.
    """
    try:
        logger.info(f"Extracting zip package: {zip_path} to {output_dir}")
        if not os.path.exists(zip_path):
            logger.error(f"Zip file not found: {zip_path}")
            return None
            
        os.makedirs(output_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
            
        circuit_files = []
        metadata_file = None
        description_file = None # Keep description finding simple

        for root, _, files in os.walk(output_dir):
            for file in files:
                file_lower = file.lower()
                full_path = os.path.join(root, file)
                
                if file_lower.endswith('.qasm'):
                    circuit_files.append(full_path)
                elif metadata_file is None and file_lower in ['metadata.json', 'info.json', 'circuit.json', 'quantum_manifest.json']:
                    metadata_file = full_path
                elif description_file is None and file_lower in ['description.md', 'readme.md', 'info.txt']:
                     description_file = full_path
                    
        if not circuit_files:
            logger.error(f"No QASM (.qasm) circuit files found in the zip package: {zip_path}")
            # Clean up potentially empty extraction dir?
            # shutil.rmtree(output_dir, ignore_errors=True)
            return None
            
        logger.info(f"Found {len(circuit_files)} QASM file(s) in zip.")
        if metadata_file: logger.info(f"Found metadata file: {metadata_file}")
        if description_file: logger.info(f"Found description file: {description_file}")
                    
        return {
            "circuit_files": circuit_files,
            "description_file": description_file,
            "metadata_file": metadata_file,
            "extract_dir": output_dir
        }
        
    except zipfile.BadZipFile:
         logger.error(f"Error: Provided file {zip_path} is not a valid zip archive.")
         return None
    except Exception as e:
        logger.error(f"Error extracting zip package {zip_path}: {e}")
        return None

def find_input_file(source_file, app_root):
    """
    Find the input file (QASM or ZIP), checking common locations.
    Returns absolute path if found, otherwise original path.
    """
    if not source_file: return None # Handle empty input case
    
    # 1. Check if it's absolute or exists relative to Current Working Directory
    if os.path.isabs(source_file) and os.path.exists(source_file):
        return source_file
    if not os.path.isabs(source_file) and os.path.exists(source_file):
         return os.path.abspath(source_file)

    # 2. Check relative to app_root (if different from CWD)
    app_root_abs = os.path.abspath(app_root)
    cwd_abs = os.path.abspath(os.getcwd())
    if app_root_abs != cwd_abs:
        path_rel_app_root = os.path.join(app_root_abs, source_file)
        if os.path.exists(path_rel_app_root):
            logger.debug(f"Found input file relative to app_root: {path_rel_app_root}")
            return path_rel_app_root

    # 3. Check in 'dist' directory relative to app_root
    dist_path = os.path.join(app_root_abs, "dist", source_file)
    if os.path.exists(dist_path):
        logger.info(f"Found input file in app_root/dist: {dist_path}")
        return dist_path
    
    # 4. Check in 'dist' directory with .zip extension
    if not source_file.lower().endswith('.zip'):
        zip_filename = f"{os.path.splitext(source_file)[0]}.zip"
        dist_zip_path = os.path.join(app_root_abs, "dist", zip_filename)
        if os.path.exists(dist_zip_path):
            logger.info(f"Found input zip file in app_root/dist: {dist_zip_path}")
            return dist_zip_path
    
    # 5. Check in default IR locations relative to app_root (base, optimized, mitigated)
    default_ir_dirs = [
        os.path.join(app_root_abs, "ir", "openqasm", "base"),
        os.path.join(app_root_abs, "ir", "openqasm", "optimized"),
        os.path.join(app_root_abs, "ir", "openqasm", "mitigated")
    ]
    for ir_dir in default_ir_dirs:
         path_in_ir = os.path.join(ir_dir, source_file)
         if os.path.exists(path_in_ir):
             logger.info(f"Found input file in default IR location: {path_in_ir}")
             return path_in_ir

    logger.warning(f"Could not find specified source file '{source_file}' in standard locations relative to app root '{app_root_abs}'. Returning original path.")
    return source_file # Return original path if not found

def generate_microservice(source_file=None, dest_dir=None, llm_url=None, port=8000, app_root=None):
    """
    Generate a microservice for the provided QASM circuit or packaged app.
    
    Args:
        source_file: Input QASM file or ZIP bundle 
        dest_dir: Destination directory (default: app_root/services/generated/microservice)
        llm_url: URL to an LLM for enhanced generation (if None, uses templates)
        port: Port number for the service to listen on
        app_root: Root of the application (used for resolving paths)
        
    Returns:
        bool: True if generation succeeded
    """
    # Ensure templates exist first
    if not setup_microservice_templates():
        logger.error("Failed to set up required microservice templates. Aborting.")
        return False
        
    # Also try to build the base Docker image
    if not create_base_docker_image():
         logger.warning(f"Failed to build base Docker image '{QUANTUM_DOCKER_IMAGE}'. Microservice may not work correctly.")
         
    # Override app_root to use current directory if not provided
    if not app_root:
        app_root = os.getcwd()
        logger.debug(f"app_root not provided, using current directory: {app_root}")

    # --- Determine Input Source File --- 
    actual_source_file = None
    if source_file is None:
        logger.info("Source file not provided, searching in default location ir/openqasm/mitigated/...")
        default_ir_dir = os.path.join(app_root, "ir", "openqasm", "mitigated")
        if os.path.isdir(default_ir_dir):
            qasm_files = [f for f in os.listdir(default_ir_dir) if f.lower().endswith('.qasm')]
            if len(qasm_files) == 1:
                actual_source_file = os.path.join(default_ir_dir, qasm_files[0])
                logger.info(f"Found default source file: {actual_source_file}")
            elif len(qasm_files) > 1:
                logger.error(f"Multiple .qasm files found in {default_ir_dir}: {qasm_files}. Specify input file.")
                return False
            else: 
                 logger.error(f"No .qasm files found in {default_ir_dir}. Provide source file.")
                 return False
        else:
            logger.error(f"Default IR directory not found: {default_ir_dir}. Provide source file.")
            return False
    else:
        # If source_file is provided, use it directly after validation
        # Remove the call to find_input_file
    if not os.path.exists(source_file):
             logger.error(f"Provided source file does not exist: {source_file}")
        return False
        # Check if it's absolute, make it absolute if not (relative to CWD)
        if not os.path.isabs(source_file):
             actual_source_file = os.path.abspath(source_file)
             logger.info(f"Resolved relative source file path to: {actual_source_file}")
        else:
            actual_source_file = source_file

    # --- Validate Input Source File --- 
    # This check might be redundant now but keeps validation logic together
    if not actual_source_file or not os.path.exists(actual_source_file):
        logger.error(f"Input source file '{source_file or 'default'}' could not be found or resolved to '{actual_source_file}'.")
        return False
    logger.info(f"Using source file: {actual_source_file}")
    file_ext = os.path.splitext(actual_source_file)[1].lower()
    if file_ext not in ['.qasm', '.zip']:
        logger.error(f"Unsupported file type '{file_ext}'. Requires .qasm or .zip")
        return False

    # --- Determine Destination Directory --- 
    if not dest_dir:
        dest_dir = os.path.join(app_root, "services", "generated", "microservice")
        logger.info(f"Output directory not specified, defaulting to: {dest_dir}")
    elif not os.path.isabs(dest_dir):
        dest_dir = os.path.join(app_root, dest_dir)
    dest_dir = os.path.abspath(dest_dir)
    try:
    os.makedirs(dest_dir, exist_ok=True)
        logger.info(f"Ensured microservice destination directory exists: {dest_dir}")
    except Exception as e:
        logger.error(f"Failed to create destination directory {dest_dir}: {e}")
        return False
    
    # --- Process Input File (QASM or ZIP) --- 
    circuit_info = None
    circuit_file_to_copy = None 
    manifest_data = None
    manifest_source_path = None
    extracted_data = None
    extract_dir = None # Define extract_dir outside if block
    
    if file_ext == '.zip':
        extract_dir = os.path.join(dest_dir, "_extracted_zip") # Temp extraction dir
        extracted_data = extract_zip_package(actual_source_file, extract_dir)
        if not extracted_data or not extracted_data["circuit_files"]:
            logger.error(f"Failed to extract valid QASM from zip: {actual_source_file}")
            return False
        circuit_file_to_copy = extracted_data["circuit_files"][0]
        logger.info(f"Using circuit file from zip: {circuit_file_to_copy}")
        circuit_info = extract_circuit_info(circuit_file_to_copy)
        manifest_data, manifest_source_path = load_quantum_manifest(app_root, 
                                                                      circuit_info.get("name") if circuit_info else None, 
                                                                      extracted_data)
    elif file_ext == '.qasm':
        circuit_file_to_copy = actual_source_file
        circuit_info = extract_circuit_info(circuit_file_to_copy)
        manifest_data, manifest_source_path = load_quantum_manifest(app_root, 
                                                                      circuit_info.get("name") if circuit_info else None)
    
    if not circuit_info: logger.error(f"Failed to extract circuit info from {circuit_file_to_copy}. Aborting."); return False
    if not manifest_data: logger.error("Failed to load/create quantum manifest. Aborting."); return False

    # --- Requirements Pinning (Revised Root Finding) --- 
    core_deps = ["fastapi", "uvicorn", "pydantic", "qiskit", "qiskit-aer", "cirq", "cirq-qasm", "amazon-braket-sdk", "matplotlib", "numpy"]
    pinned_requirements = []
    root_req_path = None
    
    # ALWAYS find root requirements.txt relative to this script's location
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up from src/quantum_cli_sdk/commands -> src/quantum_cli_sdk -> src -> project_root
        sdk_project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
        root_req_path = os.path.join(sdk_project_root, 'requirements.txt')
        if os.path.exists(root_req_path):
            logger.debug(f"Found SDK project requirements via script path: {root_req_path}")
        else:
             logger.warning(f"Could not find SDK requirements.txt at expected path: {root_req_path}. Using unpinned.")
             root_req_path = None # Ensure it's None if not found
    except Exception as e:
        logger.warning(f"Error determining SDK project root for requirements: {e}. Will use unpinned.")
        root_req_path = None
        
    if root_req_path: # Check if path was successfully found and exists
        logger.info(f"Reading SDK project requirements from: {root_req_path}")
        try:
            with open(root_req_path, 'r') as f: all_reqs = f.readlines()
            req_dict = {}
            for req in all_reqs:
                req_line = req.strip()
                if not req_line or req_line.startswith('#'): continue
                match = re.match(r"^([a-zA-Z0-9_-]+)", req_line)
                if match:
                    name = match.group(1).lower().replace('_', '-')
                    req_dict[name] = req_line 
            for dep in core_deps:
                norm_dep = dep.lower().replace('_', '-')
                if norm_dep in req_dict:
                    pinned_requirements.append(req_dict[norm_dep])
                else:
                    logger.warning(f"Dep '{dep}' not found in root {root_req_path}. Using unpinned name.")
                    pinned_requirements.append(dep)
        except Exception as e:
            logger.error(f"Error parsing root requirements {root_req_path}: {e}. Using unpinned.", exc_info=True)
            pinned_requirements = core_deps
    else:
        logger.warning(f"Project root requirements.txt not found. Using unpinned dependencies.")
        pinned_requirements = core_deps
    
    # Ensure cirq-qasm is explicitly included
    if "cirq-qasm" not in pinned_requirements:
        logger.info("Adding cirq-qasm to requirements (critical dependency)")
        pinned_requirements.append("cirq-qasm")
    
    logger.debug(f"Final requirements (before sorting): {pinned_requirements}")
    sorted_requirements = sorted(pinned_requirements)
    logger.debug(f"Final requirements (after sorting): {sorted_requirements}")
    requirements_content = "\n".join(sorted_requirements) + "\n"
    
    # Also explicitly write cirq-qasm to the requirements.txt file
    with open(os.path.join(dest_dir, "requirements.txt.debug"), 'w') as f:
        f.write("# Debug requirements.txt - generated directly\n")
        f.write("# All dependencies before sorting:\n")
        for req in pinned_requirements:
            f.write(f"{req}\n")
        f.write("\n# After sorting:\n")
        for req in sorted_requirements:
            f.write(f"{req}\n")
    
    # --- Write Pinned Requirements File --- 
    req_txt_path = os.path.join(dest_dir, "requirements.txt")
    try:
        # Make sure we explicitly add cirq-qasm to the requirements
        with open(req_txt_path, 'w') as f: 
            f.write(requirements_content)
            # Double-check that cirq-qasm is in the file
            if "cirq-qasm" not in requirements_content:
                f.write("cirq-qasm\n")
        logger.info(f"Generated {req_txt_path} with pinned versions.")
    except Exception as e:
        logger.error(f"Failed to write {req_txt_path}: {e}", exc_info=True)
        return False # Requirements are critical

    # --- Prepare Template Context --- 
    app_name = manifest_data.get("app_name", f"quantum-{circuit_info.get('name', 'service')}")
    template_context = {
        "app_name": app_name,
        "app_description": manifest_data.get("app_description", f"Quantum microservice for {circuit_info.get('name', 'default')} circuit"),
        "app_version": manifest_data.get("version", "0.1.0"),
        "generated_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "default_circuit_filename": DEFAULT_CIRCUIT_FILENAME_IN_SERVICE,
        "circuit_documentation": generate_circuit_documentation(circuit_info),
        "port": str(port),
        "author": manifest_data.get("author", "Quantum CLI SDK User"),
        "license_info": manifest_data.get("license", "MIT"),
        "keywords": ", ".join(manifest_data.get("keywords", [])),
        "quantum_docker_image": QUANTUM_DOCKER_IMAGE
    }

    # --- Generate Files from Template Files --- 
    files_to_generate = ["Dockerfile", "app.py", "README.md"]

    for template_basename in files_to_generate:
        # Use the established TEMPLATES_DIR constant
        template_path = os.path.join(TEMPLATES_DIR, f"{template_basename}.template")
        
        output_path = os.path.join(dest_dir, template_basename)
        
        # Read template content using the calculated path
        try:
            logger.debug(f"Attempting to read template: {template_path}")
            logger.debug(f"os.path.exists check: {os.path.exists(template_path)}")
            logger.debug(f"os.path.isfile check: {os.path.isfile(template_path)}")
            logger.debug(f"Template file stats: {os.stat(template_path) if os.path.exists(template_path) else 'N/A'}")
            with open(template_path, 'r') as f:
                template_content = f.read()
                logger.debug(f"Successfully read template: {template_basename}, length: {len(template_content)} chars")
        except FileNotFoundError:
            logger.error(f"Template file missing: {template_path}. Cannot generate {output_path}.")
            if template_basename == "app.py": return False
            continue
        except Exception as e:
            logger.error(f"Error reading template {template_path}: {e}", exc_info=True)
            if template_basename == "app.py": return False
            continue
            
        # Substitute and write the file (existing logic)
        try:
            file_content = Template(template_content).substitute(template_context)
        except KeyError as ke:
            logger.error(f"Template '{template_path}' is missing key: {ke}. Context keys: {template_context.keys()}")
            return False
        except Exception as e:
            logger.error(f"Error substituting template '{template_path}': {e}", exc_info=True)
            return False

        try:
            with open(output_path, 'w') as f: f.write(file_content)
            logger.info(f"Generated {output_path}")
        except Exception as e:
            logger.error(f"Failed to write generated file {output_path}: {e}", exc_info=True)
            if template_basename == "app.py": return False # app.py is critical

    # --- Copy Default Circuit and Manifest --- 
    circuits_dir = os.path.join(dest_dir, "circuits")
    os.makedirs(circuits_dir, exist_ok=True)
    destination_circuit_path = os.path.join(circuits_dir, DEFAULT_CIRCUIT_FILENAME_IN_SERVICE)
    try:
        shutil.copyfile(circuit_file_to_copy, destination_circuit_path)
        logger.info(f"Copied input circuit '{circuit_file_to_copy}' -> '{destination_circuit_path}'")
    except Exception as e:
        logger.error(f"FATAL: Failed to copy circuit to {destination_circuit_path}: {e}", exc_info=True)
        return False 
    
    manifest_dest_path = os.path.join(dest_dir, "quantum_manifest.json")
    try:
        with open(manifest_dest_path, 'w') as f: json.dump(manifest_data, f, indent=2)
        logger.info(f"Wrote manifest data to {manifest_dest_path}")
    except Exception as e:
        logger.error(f"Failed to write manifest to {manifest_dest_path}: {e}", exc_info=True)

    # --- Final Steps --- 
    if extracted_data and extract_dir and os.path.isdir(extract_dir):
         try: shutil.rmtree(extract_dir); logger.info(f"Cleaned up {extract_dir}")
         except Exception as e: logger.warning(f"Could not clean up {extract_dir}: {e}")

    logger.info(f"Microservice generation completed successfully in {dest_dir}")
    return True

def create_base_docker_image():
    """
    Build the base Docker image (quantum-cli-sdk/microservice-base:latest).
    Uses a temporary Dockerfile.
    Note: Assumes Docker daemon is running and accessible.
    """
    dockerfile_content = """FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ git && rm -rf /var/lib/apt/lists/*
# Pin base requirements here if possible, or rely on pre-built image
RUN pip install --no-cache-dir \
    fastapi~=0.100 \
    uvicorn[standard]~=0.23 \
    pydantic~=2.0 \
    qiskit==1.4.1 \
    qiskit-aer==0.16.4 \
    cirq~=1.2 \
    amazon-braket-sdk~=1.45 \
    matplotlib~=3.7 \
    numpy~=1.25
WORKDIR /app
CMD ["python"]
"""
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            dockerfile_path = os.path.join(temp_dir, "Dockerfile")
            with open(dockerfile_path, 'w') as f: f.write(dockerfile_content)
                
            logger.info(f"Attempting to build base Docker image: {QUANTUM_DOCKER_IMAGE}")
            # Remove invalid capture_output argument
            result_data = run_docker_command(
                 ["build", "-t", QUANTUM_DOCKER_IMAGE, "--progress=plain", "."],
                 cwd=temp_dir 
            )

            # Check result based on expected output of run_docker_command
            if isinstance(result_data, dict):
                 success = result_data.get("success", False)
                 stdout = result_data.get("stdout", "")
                 stderr = result_data.get("stderr", "")
                 if success:
                     logger.info(f"Base Docker image '{QUANTUM_DOCKER_IMAGE}' built successfully.")
                return True
            else:
                     logger.error(f"Failed to build base Docker image '{QUANTUM_DOCKER_IMAGE}'. Error: {stderr or stdout}")
                     return False
            elif isinstance(result_data, bool): # Handle simpler boolean return
                 if result_data:
                      logger.info(f"Base Docker image '{QUANTUM_DOCKER_IMAGE}' built successfully.")
                      return True
                 else:
                      logger.error(f"Failed to build base Docker image '{QUANTUM_DOCKER_IMAGE}'. Check Docker logs.")
                      return False
            else:
                 # Fallback if return type is unexpected
                 logger.warning(f"run_docker_command returned unexpected type: {type(result_data)}. Assuming failure.")
                 return False
                 
    except FileNotFoundError: # Handle case where docker command might not be found
        logger.error("Docker command not found. Cannot build base image. Is Docker installed and in PATH?")
                return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during base Docker image build: {e}", exc_info=True)
        return False

def setup_microservice_templates():
    """
    Ensure base template files exist, creating simple fallbacks if necessary.
    Reads/writes .template files now.
    Returns:
        bool: True if all essential templates exist or were created.
    """
    all_exist = True
        templates_dir = TEMPLATES_DIR
    logger.debug(f"Setting up templates in directory: {templates_dir}")
    
    try:
        os.makedirs(templates_dir, exist_ok=True)
        logger.debug(f"Templates directory created/exists: {templates_dir}")
    except Exception as e:
        logger.error(f"Failed to create templates directory {templates_dir}: {e}")
        return False

    # Define minimal fallback content for essential templates
    fallback_templates = {
        "Dockerfile.template": """FROM ${quantum_docker_image}
WORKDIR /app
COPY . .
COPY circuits/ ./circuits/
COPY quantum_manifest.json ./
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE ${port}
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "${port}"]
""",
        "README.md.template": """# ${app_name}

${app_description}
Version: ${app_version}

See API documentation in app.py or service logs for details.
Circuit: ${default_circuit_filename}

Run with Docker:
docker build -t ${app_name} .
docker run -p ${port}:${port} --rm ${app_name}
""",
        "app.py.template": """# Fallback app.py template
from fastapi import FastAPI
import os

app = FastAPI(title='${app_name}', version='${app_version}')

@app.get("/")
def read_root():
    return {"message": "${app_name} - Fallback Template. Please update template file."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", ${port})))
"""
    }

    for filename, fallback_content in fallback_templates.items():
        template_path = os.path.join(templates_dir, filename)
        logger.debug(f"Checking template: {template_path}, exists: {os.path.exists(template_path)}")
        
        if not os.path.exists(template_path):
            try:
                with open(template_path, 'w') as f:
                    f.write(fallback_content)
                logger.warning(f"Template '{filename}' was missing, created a minimal fallback version.")
    except Exception as e:
                logger.error(f"Failed to create fallback template {template_path}: {e}", exc_info=True)
                if filename == "app.py.template": all_exist = False # app.py is critical
        else:
            logger.debug(f"Template exists: {template_path}, size: {os.path.getsize(template_path)}")
    
    # Verify again after potential creation
    if not os.path.exists(os.path.join(templates_dir, "app.py.template")):
         logger.error("Critical template app.py.template is missing and could not be created.")
         all_exist = False
    
    # Add setup initialization flag
    template_init_flag = os.path.join(templates_dir, ".templates_initialized")
    try:
        with open(template_init_flag, 'w') as f:
            f.write("Templates initialized at " + datetime.datetime.now().isoformat())
        logger.debug(f"Template initialization flag created: {template_init_flag}")
    except Exception as e:
        logger.warning(f"Failed to create template initialization flag: {e}")

    return all_exist

if __name__ == "__main__":
    # Keep the simplified __main__ block for direct testing
    import argparse # Use argparse for better parsing
    print("--- Running microservice.py generation logic directly (for testing) ---")
    parser = argparse.ArgumentParser(description="Generate Microservice (Direct Script Run)")
    parser.add_argument("source_file", help="Path to source QASM or ZIP file.")
    parser.add_argument("dest_dir", nargs='?', default=None, help="Optional destination directory.")
    parser.add_argument("--port", type=int, default=8000, help="Port number for generated service.")
    parser.add_argument("--llm-url", default=None, help="LLM URL (optional)." )
    parser.add_argument("--app-root", default=None, help="App root override. Defaults to CWD.")
    args = parser.parse_args()

    app_root_main = args.app_root or os.getcwd()
    print(f"Source: {args.source_file}, Dest: {args.dest_dir or '(default)'}, Port: {args.port}, AppRoot: {app_root_main}")

    print("\nStarting microservice generation...")
    success = generate_microservice(
         source_file=args.source_file, 
         dest_dir=args.dest_dir, 
         llm_url=args.llm_url, 
         port=args.port, 
         app_root=app_root_main
    )
    
    print("--- Generation Test Complete ---")
    sys.exit(0 if success else 1)
