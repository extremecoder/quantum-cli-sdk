"""
Validate quantum circuit files (OpenQASM, QIR, etc.).
"""

import os
import sys
import logging
import json
from pathlib import Path

from ..config import get_config
from ..logging_config import setup_logger
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
            
        # Check for basic QASM structure
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check if it starts with QASM version declaration
        if not qasm_content.strip().startswith("OPENQASM"):
            validation_results["valid"] = False
            validation_results["errors"].append("Missing OPENQASM version declaration")
        
        # Check for include statements
        if "include" not in qasm_content:
            validation_results["warnings"].append("No include statements found, may be missing standard libraries")
            
        # Check for qreg declarations
        if "qreg" not in qasm_content:
            validation_results["valid"] = False
            validation_results["errors"].append("No quantum register (qreg) declarations found")
            
        # Additional syntax validation would happen here
        # For a complete implementation, we would parse the QASM grammar
        
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
