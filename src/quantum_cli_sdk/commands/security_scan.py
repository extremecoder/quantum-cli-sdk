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
from ..logging_config import setup_logger
from ..output_formatter import format_output

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

def scan_qasm_file(source_file):
    """
    Scan an OpenQASM file for security issues.
    
    Args:
        source_file (str): Path to OpenQASM file
        
    Returns:
        dict: Scan results
    """
    logger.info(f"Scanning OpenQASM file for security issues: {source_file}")
    
    try:
        with open(source_file, 'r') as f:
            content = f.read()
            
        # Check for known security patterns
        findings = scan_for_patterns(content, SECURITY_PATTERNS)
        
        # Additional QASM-specific security checks
        # 1. Check for lack of quantum noise protection
        if "noise_model" not in content and "error_correction" not in content:
            findings.append({
                "name": "no_error_protection",
                "description": "No error correction or noise protection detected",
                "severity": "MEDIUM",
                "line_number": None,
                "matched_text": None
            })
            
        # 2. Check for potentially sensitive quantum state preparation
        state_prep_matches = re.finditer(r"state\s+([a-zA-Z0-9_]+)", content)
        for match in state_prep_matches:
            findings.append({
                "name": "sensitive_state_preparation",
                "description": "Quantum state preparation may contain sensitive data",
                "severity": "LOW",
                "line_number": content[:match.start()].count('\n') + 1,
                "matched_text": match.group(0)
            })
        
        # Calculate overall risk score (0-100)
        severity_scores = {
            "CRITICAL": 100,
            "HIGH": 75,
            "MEDIUM": 50,
            "LOW": 25
        }
        
        if findings:
            risk_score = sum(severity_scores.get(finding["severity"], 0) for finding in findings) / len(findings)
        else:
            risk_score = 0
            
        return {
            "findings": findings,
            "risk_score": risk_score,
            "risk_level": "HIGH" if risk_score >= 75 else "MEDIUM" if risk_score >= 40 else "LOW"
        }
        
    except Exception as e:
        logger.error(f"Error scanning OpenQASM file: {e}")
        return {
            "findings": [{
                "name": "scan_error",
                "description": f"Error scanning file: {str(e)}",
                "severity": "ERROR",
                "line_number": None,
                "matched_text": None
            }],
            "risk_score": 0,
            "risk_level": "ERROR"
        }

def security_scan(source_file, dest_file=None):
    """
    Perform a security scan on a quantum circuit.
    
    Args:
        source_file (str): Path to the source file
        dest_file (str, optional): Path to write scan results
        
    Returns:
        bool: True if no critical or high severity issues were found
    """
    logger.info(f"Starting security scan of {source_file}")
    
    # Ensure source file exists
    if not os.path.exists(source_file):
        logger.error(f"Source file {source_file} does not exist")
        return False
    
    # Determine file type
    file_ext = os.path.splitext(source_file)[1].lower()
    
    # Scan based on file type
    if file_ext == '.qasm':
        results = scan_qasm_file(source_file)
    else:
        logger.error(f"Unsupported file type for security scanning: {file_ext}")
        return False
    
    # Log findings
    if not results["findings"]:
        logger.info("No security issues found")
    else:
        logger.warning(f"Security scan found {len(results['findings'])} issue(s)")
        logger.warning(f"Overall risk level: {results['risk_level']}")
        
        for i, finding in enumerate(results["findings"]):
            severity = finding["severity"]
            log_func = logger.critical if severity == "CRITICAL" else \
                      logger.error if severity == "HIGH" else \
                      logger.warning if severity == "MEDIUM" else \
                      logger.info
                      
            log_func(f"Finding #{i+1}: {finding['name']} - {finding['description']}")
            if finding["line_number"]:
                log_func(f"  Line {finding['line_number']}: {finding['matched_text']}")
    
    # Write results to destination file if specified
    if dest_file:
        dest_path = Path(dest_file)
        dest_dir = dest_path.parent
        
        # Create directory if it doesn't exist
        if not dest_dir.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)
            
        with open(dest_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Security scan results written to {dest_file}")
    
    # Return True only if no critical or high severity issues were found
    has_critical_or_high = any(finding["severity"] in ["CRITICAL", "HIGH"] for finding in results["findings"])
    return not has_critical_or_high

if __name__ == "__main__":
    # This allows the module to be run directly for testing
    if len(sys.argv) < 2:
        print("Usage: security_scan.py <source_file> [<dest_file>]")
        sys.exit(1)
        
    source = sys.argv[1]
    dest = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = security_scan(source, dest)
    sys.exit(0 if success else 1)
