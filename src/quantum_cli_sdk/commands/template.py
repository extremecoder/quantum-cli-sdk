"""
Commands for managing quantum circuit templates.
"""

import json
import sys
import os
import shutil
from pathlib import Path

# Directory where templates are stored
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

# Sample templates
TEMPLATES = {
    "bell": {
        "name": "Bell State",
        "description": "Creates a maximally entangled Bell state between two qubits",
        "qubits": 2,
        "file": "bell.qasm"
    },
    "ghz": {
        "name": "GHZ State",
        "description": "Creates a GHZ state, a type of maximally entangled state for 3+ qubits",
        "qubits": 3,
        "file": "ghz.qasm"
    },
    "qft": {
        "name": "Quantum Fourier Transform",
        "description": "Implements a Quantum Fourier Transform, fundamental for many quantum algorithms",
        "qubits": 4,
        "file": "qft.qasm"
    },
    "grover": {
        "name": "Grover's Algorithm",
        "description": "Template for Grover's search algorithm",
        "qubits": 4,
        "file": "grover.qasm"
    },
    "qpe": {
        "name": "Quantum Phase Estimation",
        "description": "Implements Quantum Phase Estimation, used in many quantum algorithms",
        "qubits": 5,
        "file": "qpe.qasm"
    }
}

def list_templates():
    """List all available templates.
    
    Returns:
        List of available templates with their descriptions
    """
    try:
        print("Available quantum circuit templates:")
        print("=" * 50)
        for key, template in TEMPLATES.items():
            print(f"{key}: {template['name']}")
            print(f"  Description: {template['description']}")
            print(f"  Qubits: {template['qubits']}")
            print("-" * 50)
        return TEMPLATES
    except Exception as e:
        print(f"Error listing templates: {e}", file=sys.stderr)
        return None

def get_template(template_name, dest="."):
    """Get a specific template and save it to the specified location.
    
    Args:
        template_name: Name of the template to get
        dest: Destination directory or file
    
    Returns:
        Path to the saved template file, or None if error
    """
    try:
        if template_name not in TEMPLATES:
            print(f"Template '{template_name}' not found. Use 'template list' to see available templates.", file=sys.stderr)
            return None
        
        template = TEMPLATES[template_name]
        print(f"Getting template: {template['name']}")
        
        # Create template directory if it doesn't exist
        if not TEMPLATE_DIR.exists():
            TEMPLATE_DIR.mkdir(parents=True)
        
        # For now, generate a sample template file
        # In a real implementation, you would load this from predefined files
        source_content = f"""// {template['name']}
// {template['description']}
OPENQASM 2.0;
include "qelib1.inc";

// Circuit with {template['qubits']} qubits
qreg q[{template['qubits']}];
creg c[{template['qubits']}];

// Sample implementation
{sample_circuit_content(template_name, template['qubits'])}
"""
        
        # Determine destination path
        dest_path = Path(dest)
        if dest_path.is_dir():
            dest_path = dest_path / template["file"]
        
        # Save template to file
        with open(dest_path, 'w') as f:
            f.write(source_content)
        
        print(f"Template saved to {dest_path}")
        return dest_path
    except Exception as e:
        print(f"Error getting template: {e}", file=sys.stderr)
        return None

def apply_template(template_name, params=None, dest="circuit.qasm"):
    """Apply a template with customized parameters.
    
    Args:
        template_name: Name of the template to apply
        params: Dictionary of parameters to customize the template
        dest: Destination file for the customized circuit
    
    Returns:
        Path to the customized circuit file, or None if error
    """
    try:
        if template_name not in TEMPLATES:
            print(f"Template '{template_name}' not found. Use 'template list' to see available templates.", file=sys.stderr)
            return None
        
        template = TEMPLATES[template_name]
        print(f"Applying template: {template['name']}")
        
        # Get the template content
        temp_path = get_template(template_name, "temp_template.qasm")
        if not temp_path:
            return None
        
        with open(temp_path, 'r') as f:
            content = f.read()
        
        # Apply parameters if provided
        if params:
            # Here you would implement parameter substitution
            # For now, just add a comment with the parameters
            param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
            content = content.replace("// Sample implementation", f"// Sample implementation with parameters: {param_str}")
        
        # Save to destination
        dest_path = Path(dest)
        with open(dest_path, 'w') as f:
            f.write(content)
        
        # Clean up temporary file
        os.remove(temp_path)
        
        print(f"Customized template saved to {dest_path}")
        return dest_path
    except Exception as e:
        print(f"Error applying template: {e}", file=sys.stderr)
        return None

def sample_circuit_content(template_name, qubits):
    """Generate sample circuit content based on template name.
    
    Args:
        template_name: Name of the template
        qubits: Number of qubits
    
    Returns:
        String with sample QASM code
    """
    if template_name == "bell":
        return """// Bell state preparation
h q[0];
cx q[0], q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];"""
    
    elif template_name == "ghz":
        cx_gates = "\n".join([f"cx q[0], q[{i}];" for i in range(1, qubits)])
        measures = "\n".join([f"measure q[{i}] -> c[{i}];" for i in range(qubits)])
        return f"""// GHZ state preparation
h q[0];
{cx_gates}
{measures}"""
    
    elif template_name == "qft":
        # Simplified QFT implementation
        return """// Simplified QFT implementation
h q[0];
h q[1];
cu1(pi/2) q[1], q[0];
h q[2];
cu1(pi/4) q[2], q[0];
cu1(pi/2) q[2], q[1];
h q[3];
cu1(pi/8) q[3], q[0];
cu1(pi/4) q[3], q[1];
cu1(pi/2) q[3], q[2];
// Measurements would go here"""
    
    elif template_name == "grover":
        return """// Simplified Grover's algorithm for 2-qubit search
// Initialize
h q[0];
h q[1];
// Oracle (marks |11⟩)
x q[0];
x q[1];
h q[2];
ccx q[0], q[1], q[2];
h q[2];
x q[0];
x q[1];
// Diffusion
h q[0];
h q[1];
x q[0];
x q[1];
h q[1];
cx q[0], q[1];
h q[1];
x q[0];
x q[1];
h q[0];
h q[1];
// Measurement
measure q[0] -> c[0];
measure q[1] -> c[1];"""
    
    elif template_name == "qpe":
        return """// Simplified Quantum Phase Estimation
// Phase register (3 qubits) and target register (2 qubits)
// Initialize phase register
h q[0];
h q[1];
h q[2];
// Initialize target register in |1⟩
x q[3];
// Controlled unitary operations (simplified)
cu1(pi/4) q[0], q[3];
cu1(pi/2) q[1], q[3];
cu1(pi) q[2], q[3];
// Inverse QFT on phase register
h q[2];
cu1(-pi/2) q[1], q[2];
h q[1];
cu1(-pi/2) q[0], q[1];
cu1(-pi/4) q[0], q[2];
h q[0];
// Measurement of phase register
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];"""
    
    else:
        # Generic circuit
        hadamards = "\n".join([f"h q[{i}];" for i in range(qubits)])
        measures = "\n".join([f"measure q[{i}] -> c[{i}];" for i in range(qubits)])
        return f"""// Generic circuit
{hadamards}
{measures}""" 