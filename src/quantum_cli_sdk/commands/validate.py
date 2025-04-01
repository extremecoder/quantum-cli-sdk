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

def validate_circuit(source_file, dest_file=None, llm_url=None):
    """
    Validate a quantum circuit file.
    
    Args:
        source_file (str): Path to the circuit file
        dest_file (str, optional): Path to write validation results
        llm_url (str, optional): URL to LLM service for enhanced validation
        
    Returns:
        bool: True if validation passed, False otherwise
    """
    logger.info(f"Starting validation of {source_file}")
    
    # Ensure source file exists
    if not os.path.exists(source_file):
        logger.error(f"Source file {source_file} does not exist")
        return False
    
    # Determine file type
    file_ext = os.path.splitext(source_file)[1].lower()
    
    # Validate based on file type
    if file_ext == '.qasm':
        results = validate_qasm_syntax(source_file)
    else:
        logger.error(f"Unsupported file type: {file_ext}")
        return False
    
    # Use LLM for enhanced validation if URL provided
    if llm_url:
        logger.info(f"Using LLM at {llm_url} for enhanced validation")
        # This would be implemented to call an LLM service
        # results["llm_insights"] = call_llm_service(llm_url, source_file)
        
    # Output validation results
    if results["valid"]:
        logger.info("Validation passed")
    else:
        logger.error("Validation failed with errors:")
        for error in results["errors"]:
            logger.error(f"  - {error}")
            
    if results["warnings"]:
        logger.warning("Validation warnings:")
        for warning in results["warnings"]:
            logger.warning(f"  - {warning}")
    
    # Write results to destination file if specified
    if dest_file:
        dest_path = Path(dest_file)
        dest_dir = dest_path.parent
        
        # Create directory if it doesn't exist
        if not dest_dir.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)
            
        with open(dest_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Validation results written to {dest_file}")
    
    return results["valid"]

if __name__ == "__main__":
    # This allows the module to be run directly for testing
    if len(sys.argv) < 2:
        print("Usage: validate.py <source_file> [<dest_file>] [<llm_url>]")
        sys.exit(1)
        
    source = sys.argv[1]
    dest = sys.argv[2] if len(sys.argv) > 2 else None
    llm = sys.argv[3] if len(sys.argv) > 3 else None
    
    success = validate_circuit(source, dest, llm)
    sys.exit(0 if success else 1)
