"""
Security scan for quantum circuits to identify potential vulnerabilities.
"""

import os
import sys
import logging
import json
from pathlib import Path
import re

from ..config import get_config
from ..output_formatter import format_output

PROJECT_ROOT = Path.cwd()

# Set up logger
logger = logging.getLogger(__name__)

# Define known security patterns to search for
SECURITY_PATTERNS = {
    "unencrypted_data": {
        "pattern": r"classical_data\s*=\s*(['\"])(?!encrypted:).*?\1",
        "description": "Potentially unencrypted classical data found",
        "severity": "HIGH"
    },
    "unsecured_api_key": {
        "pattern": r"api_key\s*=\s*['\"]([\w\d]+)['\"]",
        "description": "Hardcoded API key detected",
        "severity": "CRITICAL"
    },
    "oracle_vulnerability": {
        "pattern": r"oracle\s+\w+\s*\([^)]*\)\s*{[^}]*}",
        "description": "Oracle implementation may be vulnerable to attacks",
        "severity": "MEDIUM"
    },
    "measurement_timing": {
        "pattern": r"(measure|creg)\s+(?!.*barrier)",
        "description": "Measurement without barrier may be vulnerable to timing attacks",
        "severity": "LOW"
    }
}

def scan_for_patterns(content, patterns):
    """
    Scan content for security patterns.
    
    Args:
        content (str): The content to scan
        patterns (dict): Dictionary of patterns to check
        
    Returns:
        list: List of findings
    """
    findings = []
    
    for name, pattern_info in patterns.items():
        matches = re.finditer(pattern_info["pattern"], content)
        for match in matches:
            findings.append({
                "name": name,
                "description": pattern_info["description"],
                "severity": pattern_info["severity"],
                "line_number": content[:match.start()].count('\n') + 1,
                "matched_text": match.group(0)
            })
    
    return findings

def scan_qasm_file(source_path: Path):
    """
    Scan an OpenQASM file for security issues.
    
    Args:
        source_path (Path): Path object for the OpenQASM file.
        
    Returns:
        dict: Scan results with findings, risk score, and risk level.
    """
    logger.info(f"Scanning OpenQASM file for security issues: {source_path}")
    source_file = str(source_path) # For messages

    scan_results = {
        "findings": [],
        "risk_score": 0,
        "risk_level": "LOW" # Default to LOW if no findings
    }

    try:
        with source_path.open('r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for known security patterns using regex
        pattern_findings = scan_for_patterns(content, SECURITY_PATTERNS)
        scan_results["findings"].extend(pattern_findings)
        
        # Additional QASM-specific security checks (can be expanded)
        # 1. Check for lack of quantum noise protection or error handling context
        if "noise_model" not in content and "error_correction" not in content and "mitigation" not in content:
            scan_results["findings"].append({
                "name": "no_error_awareness",
                "description": "No explicit error correction, noise model, or mitigation context detected",
                "severity": "MEDIUM",
                "line_number": None,
                "matched_text": None
            })
            
        # 2. Check for potentially sensitive quantum state preparation (example)
        # This is a very basic check and might need refinement based on context
        # state_prep_matches = re.finditer(r"(initialize|state_preparation)\s+", content, re.IGNORECASE)
        # for match in state_prep_matches:
        #     scan_results["findings"].append({
        #         "name": "potentially_sensitive_state_prep",
        #         "description": "Quantum state preparation might embed sensitive classical data if not handled carefully",
        #         "severity": "LOW",
        #         "line_number": content[:match.start()].count('\n') + 1,
        #         "matched_text": match.group(0)
        #     })

        # 3. Check for unrestricted measurements (could leak info)
        # Example: Measurement immediately followed by conditional logic without controls
        # measurement_matches = re.finditer(r"measure\s+\w+\s*->\s*\w+\s*;\s*if\s*\(", content)
        # for match in measurement_matches:
        #     scan_results["findings"].append({
        #         "name": "uncontrolled_conditional_measurement",
        #         "description": "Measurement possibly used in uncontrolled conditional logic, potential side-channel",
        #         "severity": "MEDIUM",
        #         "line_number": content[:match.start()].count('\n') + 1,
        #         "matched_text": match.group(0).split('\n')[0] # Show relevant part
        #     })
        
        # Calculate overall risk score (simple averaging, could be more sophisticated)
        severity_scores = {"CRITICAL": 100, "HIGH": 75, "MEDIUM": 50, "LOW": 25, "ERROR": 0}
        
        if scan_results["findings"]:
            total_score = sum(severity_scores.get(finding["severity"], 0) for finding in scan_results["findings"])
            num_findings = len(scan_results["findings"])
            scan_results["risk_score"] = round(total_score / num_findings, 2) if num_findings > 0 else 0
            
            # Determine risk level based on the highest severity found or average score
            max_severity_score = max((severity_scores.get(f["severity"], 0) for f in scan_results["findings"]), default=0)
            if max_severity_score >= severity_scores["CRITICAL"]:
                 scan_results["risk_level"] = "CRITICAL"
            elif max_severity_score >= severity_scores["HIGH"]:
                 scan_results["risk_level"] = "HIGH"
            elif max_severity_score >= severity_scores["MEDIUM"]:
                 scan_results["risk_level"] = "MEDIUM"
            else:
                 scan_results["risk_level"] = "LOW"
        else:
            # No findings, risk is LOW
            scan_results["risk_score"] = 0
            scan_results["risk_level"] = "LOW"
            
        return scan_results
        
    except FileNotFoundError:
        logger.error(f"Source file not found during scan: {source_file}")
        return {"findings": [{"name": "file_not_found", "description": f"File not found: {source_file}", "severity": "ERROR"}], "risk_score": 0, "risk_level": "ERROR"}
    except Exception as e:
        logger.exception(f"Error scanning OpenQASM file: {source_file}") # Use logger.exception
        return {
            "findings": [{"name": "scan_error", "description": f"Error scanning file: {str(e)}", "severity": "ERROR"}],
            "risk_score": 0,
            "risk_level": "ERROR"
        }

def security_scan(source_file=None, dest_file=None):
    """
    Perform a security scan on a quantum circuit. Assumes execution from project root.
    Defaults source to the first .qasm file in <project_root>/ir/openqasm/base 
    and destination to <project_root>/results/security/<source_stem>_scan_results.json if not provided.

    Args:
        source_file (str, optional): Path (relative or absolute) to the source file.
                                     Defaults to first .qasm in ir/openqasm/base.
        dest_file (str, optional): Path (relative or absolute) to write scan results (JSON).
                                    Defaults to results/security/<source_stem>_scan_results.json.

    Returns:
        bool: True if no critical or high severity issues were found, False otherwise.
              Returns False if critical errors occur (e.g., file not found).
    """
    logger.info("Starting security scan (assuming execution from project root)...")

    # --- Determine Source Path --- 
    resolved_source_path = None
    if source_file is None:
        default_source_dir = PROJECT_ROOT / "ir" / "openqasm" / "base"
        logger.info(f"Source file not provided. Looking in default directory: {default_source_dir}")
        if default_source_dir.is_dir():
            try:
                qasm_files = sorted(list(default_source_dir.glob('*.qasm')))
                if qasm_files:
                    source_file = str(qasm_files[0].relative_to(PROJECT_ROOT))
                    resolved_source_path = qasm_files[0]
                    logger.info(f"Using default source file: {source_file}")
                else:
                    logger.error(f"No .qasm files found in default source directory: {default_source_dir}")
                    print(f"Error: No .qasm files found in {default_source_dir}. Please create one or specify --source.", file=sys.stderr)
                    return False # Indicate failure
            except OSError as e:
                 logger.error(f"Error accessing default source directory {default_source_dir}: {e}")
                 print(f"Error: Could not access {default_source_dir}. Check permissions.", file=sys.stderr)
                 return False # Indicate failure
        else:
            logger.error(f"Default source directory not found: {default_source_dir}")
            print(f"Error: Default source directory {default_source_dir} not found and no source file specified.", file=sys.stderr)
            return False # Indicate failure
    else:
        logger.info(f"Using provided source file: {source_file}")
        try:
            provided_path = Path(source_file)
            resolved_source_path = provided_path if provided_path.is_absolute() else PROJECT_ROOT / provided_path
        except TypeError:
             logger.error("Internal error: Invalid source_file path provided.")
             print("Error: Invalid source file path.", file=sys.stderr)
             return False # Indicate failure

    # --- Verify Source Path --- 
    if resolved_source_path is None or not resolved_source_path.is_file():
        error_path = resolved_source_path if resolved_source_path else source_file
        logger.error(f"Source file does not exist or is not a file: {error_path}")
        print(f"Error: Source file {error_path} not found or is not a regular file.", file=sys.stderr)
        return False # Indicate failure

    # --- Determine Destination Path --- 
    dest_path = None
    if dest_file is None:
        try:
            # Specific subdir for security scan results
            default_dest_dir = PROJECT_ROOT / "results" / "security" # Changed from security_scan
            default_dest_dir.mkdir(parents=True, exist_ok=True)
             # Clearer filename using source stem
            dest_filename = resolved_source_path.stem + "_scan_results.json" # Clearer filename
            dest_path = default_dest_dir / dest_filename
            logger.info(f"Destination file not provided. Using default: {dest_path.relative_to(PROJECT_ROOT)}")
        except OSError as e:
             logger.error(f"Could not create default destination directory {default_dest_dir}: {e}")
             print(f"Error: Could not create directory {default_dest_dir}. Check permissions.", file=sys.stderr)
             # Continue without writing file? Or fail? Let's fail for now.
             return False
    else:
        logger.info(f"Using provided destination file: {dest_file}")
        provided_dest_path = Path(dest_file)
        dest_path = provided_dest_path if provided_dest_path.is_absolute() else PROJECT_ROOT / provided_dest_path
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
             logger.error(f"Could not create destination directory {dest_path.parent} for specified file {dest_path}: {e}")
             print(f"Error: Could not create directory {dest_path.parent}. Check permissions.", file=sys.stderr)
             return False # Indicate failure

    # --- Perform Scan --- 
    file_ext = resolved_source_path.suffix.lower()
    results = {}
    if file_ext == '.qasm':
        results = scan_qasm_file(resolved_source_path)
    # Add elif for other file types if needed
    # elif file_ext == '.py': # Example: scan python source for different patterns
    #    results = scan_python_file(resolved_source_path)
    else:
        error_msg = f"Unsupported file type for security scanning: {file_ext} in file {resolved_source_path}"
        logger.error(error_msg)
        print(f"Error: Unsupported file type '{file_ext}'. Only .qasm is currently supported for scanning.", file=sys.stderr)
        results = {"findings": [{"name": "unsupported_type", "description": error_msg, "severity": "ERROR"}], "risk_score": 0, "risk_level": "ERROR"}
        # Allow writing the error result below, but indicate failure overall

    # --- Log Findings Summary --- 
    scan_findings = results.get("findings", [])
    if not scan_findings or all(f["severity"] == "ERROR" for f in scan_findings):
        if any(f["severity"] == "ERROR" for f in scan_findings):
             logger.error("Security scan encountered an error.")
        else:
             logger.info("Security scan completed. No security issues found.")
    else:
        num_issues = len([f for f in scan_findings if f["severity"] != "ERROR"]) # Count non-error findings
        logger.warning(f"Security scan found {num_issues} potential issue(s).")
        logger.warning(f"Overall risk level: {results.get('risk_level', 'UNKNOWN')}")
        # Optionally log details (can be verbose)
        # for i, finding in enumerate(scan_findings):
        #     if finding["severity"] == "ERROR": continue
        #     severity = finding["severity"]
        #     log_func = logger.critical if severity == "CRITICAL" else \
        #               logger.error if severity == "HIGH" else \
        #               logger.warning if severity == "MEDIUM" else \
        #               logger.info # LOW
        #     log_func(f"  - Finding #{i+1}: [{severity}] {finding['name']} - {finding['description']}")
        #     if finding.get("line_number"):
        #         log_func(f"    Line {finding['line_number']}: {finding.get('matched_text', '').strip()}")

    # --- Write Results --- 
    if dest_path:
        try:
            with dest_path.open('w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Security scan results written to {dest_path.relative_to(PROJECT_ROOT)}")
        except IOError as e:
            logger.error(f"Failed to write security scan results to {dest_path}: {e}")
            print(f"Error: Could not write results to {dest_path}. Check permissions.", file=sys.stderr)
            # Don't fail the whole command just because writing failed, but log it.

    # --- Determine Return Status --- 
    # Return True only if scan ran successfully (no ERROR findings) 
    # AND no critical or high severity issues were found.
    scan_successful = not any(finding["severity"] == "ERROR" for finding in scan_findings)
    has_critical_or_high = any(finding["severity"] in ["CRITICAL", "HIGH"] for finding in scan_findings)
    
    return scan_successful and not has_critical_or_high

if __name__ == "__main__":
    # Direct execution for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    num_args = len(sys.argv)
    source_arg = sys.argv[1] if num_args > 1 else None
    dest_arg = sys.argv[2] if num_args > 2 else None

    print("-" * 20)
    if source_arg is None:
        print("INFO: No source file provided. Attempting to use default from './ir/openqasm/base'.")
    if dest_arg is None:
         print("INFO: No destination file provided. Attempting to use default in './results/security'.")
    print("-" * 20)

    success = security_scan(source_file=source_arg, dest_file=dest_arg)
    
    print("-" * 20)
    if success:
        print("RESULT: Security scan completed. No critical or high severity issues found.")
        sys.exit(0)
    else:
        # Check if failure was due to scan error vs high severity findings
        # Re-run scan to get results (inefficient, better to pass results out)
        # For simplicity here, just print a general failure message
        print("RESULT: Security scan failed or found critical/high severity issues.")
        sys.exit(1)
