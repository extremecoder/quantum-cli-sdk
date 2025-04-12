"""
Validate quantum circuit files (OpenQASM, QIR, etc.).
"""

import os
import sys
import logging
import json
from pathlib import Path
import re

from ..config import get_config
from ..output_formatter import format_output

# Set up logger
logger = logging.getLogger(__name__)

def validate_qasm_syntax(source_file):
    """
    Validate OpenQASM syntax.
    
    Args:
        source_file (str): Path to OpenQASM file
        
    Returns:
        dict: Validation results
    """
    logger.info(f"Validating OpenQASM syntax for {source_file}")
    
    try:
        with open(source_file, 'r') as f:
            qasm_content = f.read()
            
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "details": {
                "version": None,
                "includes": [],
                "registers": {
                    "quantum": [],
                    "classical": []
                },
                "gates": [],
                "measurements": []
            }
        }
        
        # Split into lines and remove comments
        lines = [line.split('//')[0].strip() for line in qasm_content.split('\n')]
        lines = [line for line in lines if line]  # Remove empty lines
        
        # Check version declaration
        if not lines[0].startswith("OPENQASM"):
            validation_results["valid"] = False
            validation_results["errors"].append("Missing OPENQASM version declaration")
        else:
            version_match = re.match(r"OPENQASM\s+(\d+\.\d+)", lines[0])
            if version_match:
                validation_results["details"]["version"] = version_match.group(1)
            else:
                validation_results["warnings"].append("Invalid version declaration format")
        
        # Track register declarations
        qreg_pattern = re.compile(r"qreg\s+(\w+)\[(\d+)\]")
        creg_pattern = re.compile(r"creg\s+(\w+)\[(\d+)\]")
        
        # Track gate declarations and usages
        gate_declarations = set()
        gate_usage = set()
        
        for line in lines[1:]:  # Skip version declaration
            # Check for include statements
            if line.startswith("include"):
                include_match = re.match(r'include\s+"([^"]+)"', line)
                if include_match:
                    validation_results["details"]["includes"].append(include_match.group(1))
                else:
                    validation_results["warnings"].append("Invalid include statement format")
            
            # Check for register declarations
            qreg_match = qreg_pattern.match(line)
            if qreg_match:
                reg_name, size = qreg_match.groups()
                validation_results["details"]["registers"]["quantum"].append({
                    "name": reg_name,
                    "size": int(size)
                })
            
            creg_match = creg_pattern.match(line)
            if creg_match:
                reg_name, size = creg_match.groups()
                validation_results["details"]["registers"]["classical"].append({
                    "name": reg_name,
                    "size": int(size)
                })
            
            # Check for gate declarations
            if line.startswith("gate"):
                gate_match = re.match(r"gate\s+(\w+)\s+", line)
                if gate_match:
                    gate_declarations.add(gate_match.group(1))
            
            # Check for gate usage
            gate_usage_match = re.match(r"(\w+)\s+", line)
            if gate_usage_match and not line.startswith(("qreg", "creg", "gate", "include", "measure")):
                gate_name = gate_usage_match.group(1)
                if gate_name not in gate_declarations and gate_name not in ["h", "x", "y", "z", "cx", "ccx", "swap"]:
                    validation_results["warnings"].append(f"Using undeclared gate: {gate_name}")
                gate_usage.add(gate_name)
            
            # Check for measurements
            if line.startswith("measure"):
                measure_match = re.match(r"measure\s+(\w+)\s*->\s*(\w+)", line)
                if measure_match:
                    validation_results["details"]["measurements"].append({
                        "quantum": measure_match.group(1),
                        "classical": measure_match.group(2)
                    })
                else:
                    validation_results["warnings"].append("Invalid measure statement format")
        
        # Validate register usage
        qreg_names = {reg["name"] for reg in validation_results["details"]["registers"]["quantum"]}
        creg_names = {reg["name"] for reg in validation_results["details"]["registers"]["classical"]}
        
        for measurement in validation_results["details"]["measurements"]:
            if measurement["quantum"] not in qreg_names:
                validation_results["errors"].append(f"Invalid quantum register in measure: {measurement['quantum']}")
            if measurement["classical"] not in creg_names:
                validation_results["errors"].append(f"Invalid classical register in measure: {measurement['classical']}")
        
        # Check for basic circuit requirements
        if not validation_results["details"]["registers"]["quantum"]:
            validation_results["valid"] = False
            validation_results["errors"].append("No quantum registers declared")
        
        if not validation_results["details"]["registers"]["classical"]:
            validation_results["warnings"].append("No classical registers declared")
        
        if not validation_results["details"]["measurements"]:
            validation_results["warnings"].append("No measurement operations found")
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Error validating OpenQASM file: {e}")
        return {
            "valid": False,
            "errors": [f"Error reading or parsing file: {str(e)}"],
            "warnings": []
        }

def validate_circuit(source_file=None, dest_file=None, llm_url=None):
    """
    Validate a quantum circuit file. Assumes execution from project root.
    Defaults source to the first .qasm file in <project_root>/ir/openqasm/base 
    and destination to <project_root>/results/validation/ if not provided.

    Args:
        source_file (str, optional): Path to the circuit file. Defaults to first .qasm in ir/openqasm/base.
        dest_file (str, optional): Path to write validation results (JSON). Defaults to results/validation/<source_stem>.json.
        llm_url (str, optional): URL to LLM service for enhanced validation.

    Returns:
        bool: True if validation passed (no errors found), False otherwise.
    """
    logger.info("Starting validation (assuming execution from project root)...")

    # Use current working directory as project root
    project_root = Path.cwd()
    
    # --- Determine Source Path ---
    resolved_source_path = None # Will hold the final resolved Path object
    if source_file is None:
        default_source_dir = project_root / "ir" / "openqasm" / "base"
        logger.info(f"Source file not provided. Looking in default directory: {default_source_dir}")
        if default_source_dir.is_dir():
            try:
                # Find .qasm files, sort for consistency, take the first one
                qasm_files = sorted(list(default_source_dir.glob('*.qasm')))
                if qasm_files:
                    # Assign the relative path string back to source_file
                    source_file = str(qasm_files[0].relative_to(project_root))
                    logger.info(f"Using default source file: {source_file}")
                    # Also set the resolved path directly since we found it
                    resolved_source_path = qasm_files[0]
                else:
                    logger.error(f"No .qasm files found in default source directory: {default_source_dir}")
                    print(f"Error: No .qasm files found in {default_source_dir}. Please create one or specify --source.", file=sys.stderr)
                    return False
            except OSError as e:
                 logger.error(f"Error accessing default source directory {default_source_dir}: {e}")
                 print(f"Error: Could not access {default_source_dir}. Check permissions.", file=sys.stderr)
                 return False
        else:
            # If default dir doesn't exist, it's an error condition if no source was specified
            logger.error(f"Default source directory not found: {default_source_dir}")
            print(f"Error: Default source directory {default_source_dir} not found and no source file specified.", file=sys.stderr)
            return False
    else:
         # If a source file was provided explicitly
         logger.info(f"Using provided source file: {source_file}")
         # Resolve it relative to project root if not absolute
         provided_path = Path(source_file)
         resolved_source_path = provided_path if provided_path.is_absolute() else project_root / provided_path

    # --- Verify Source Path ---
    # This check handles cases where source_path remained None (e.g. error finding default) 
    # or resolved path is not a file
    if resolved_source_path is None or not resolved_source_path.is_file():
        logger.error(f"Source file does not exist or is not a file: {resolved_source_path or source_file}") # Log resolved path if available
        print(f"Error: Source file {resolved_source_path or source_file} not found or is not a regular file.", file=sys.stderr)
        return False

    # Default destination file logic
    if dest_file is None:
        try:
            default_dest_dir = project_root / "results" / "validation"
            default_dest_dir.mkdir(parents=True, exist_ok=True)
            # Use the name from the potentially resolved source_path
            dest_filename = resolved_source_path.stem + ".json" # Use .json extension for results
            dest_file = str(default_dest_dir / dest_filename) # Relative path from project root
            logger.info(f"Destination file not provided. Using default: {dest_file}")
        except OSError as e:
             logger.error(f"Could not create default destination directory {default_dest_dir}: {e}")
             print(f"Error: Could not create directory {default_dest_dir}. Check permissions.", file=sys.stderr)
             return False # Cannot proceed without a place to write results if default is chosen
    else:
        logger.info(f"Using provided destination file: {dest_file}")
        # Ensure destination directory exists if specified, resolve relative to project root
        dest_path_resolved = project_root / dest_file if not Path(dest_file).is_absolute() else Path(dest_file)
        try:
            dest_dir = dest_path_resolved.parent
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file = str(dest_path_resolved) # Use the resolved path string
        except OSError as e:
             logger.error(f"Could not create destination directory {dest_dir} for specified file {dest_file}: {e}")
             print(f"Error: Could not create directory {dest_dir}. Check permissions.", file=sys.stderr)
             return False # Cannot proceed if specified destination dir cannot be created

    # Determine file type from source_path path object
    file_ext = resolved_source_path.suffix.lower()

    # Validate based on file type
    if file_ext == '.qasm':
        results = validate_qasm_syntax(resolved_source_path)
    # Add elif blocks here for other supported formats (e.g., .qir)
    # elif file_ext == '.qir':
    #     results = validate_qir(source_path) 
    else:
        logger.error(f"Unsupported file type: {file_ext} for file {resolved_source_path}")
        print(f"Error: Unsupported file type '{file_ext}'. Only .qasm is currently supported.", file=sys.stderr)
        return False

    # Use LLM for enhanced validation if URL provided
    if llm_url:
        logger.info(f"Using LLM at {llm_url} for enhanced validation")
        # Placeholder for actual LLM call implementation
        # try:
        #     llm_insights = call_llm_service(llm_url, source_path)
        #     results["llm_insights"] = llm_insights 
        # except Exception as e:
        #     logger.warning(f"Failed to get LLM insights: {e}")
        #     results["llm_insights"] = {"error": str(e)}
        pass # Remove pass when LLM logic is added

    # Output validation results status
    if results.get("valid", False):
        logger.info("Validation successful.")
    else:
        logger.error("Validation failed.")
        if results.get("errors"):
            logger.error("Errors:")
            for error in results["errors"]:
                logger.error(f"  - {error}")

    if results.get("warnings"):
        logger.warning("Warnings:")
        for warning in results["warnings"]:
            logger.warning(f"  - {warning}")

    # Write results to destination file
    try:
        with open(dest_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Validation results written to {dest_file}")
    except IOError as e:
        logger.error(f"Failed to write results to {dest_file}: {e}")
        print(f"Error: Could not write results to {dest_file}. Check permissions.", file=sys.stderr)
        # Decide if this should cause the function to return False
        # return False # Uncomment if write failure should mean overall failure

    return results.get("valid", False) # Return the validity status


if __name__ == "__main__":
    # This allows the module to be run directly for testing
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s') # Basic logging for direct run
    
    # Very basic argument parsing for direct execution
    source = sys.argv[1] if len(sys.argv) > 1 else None
    dest = sys.argv[2] if len(sys.argv) > 2 else None
    llm = sys.argv[3] if len(sys.argv) > 3 else None
    
    if source is None:
        # If running directly without args, explain default behavior or exit
        print("Running with default source/destination logic.")
        # Alternatively, force providing source:
        # print("Usage: python -m quantum_cli_sdk.commands.validate [<source_file> [<dest_file> [<llm_url>]]]")
        # sys.exit(1)

    success = validate_circuit(source, dest, llm)
    
    if success:
        print("Validation completed successfully.")
        sys.exit(0)
    else:
        print("Validation failed.")
        sys.exit(1)
