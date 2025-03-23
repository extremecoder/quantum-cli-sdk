"""
Optimize quantum circuits to reduce depth, gate count, and improve performance.
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
from ..transpiler import get_pass_manager

# Set up logger
logger = logging.getLogger(__name__)

# Define optimization levels
OPTIMIZATION_LEVELS = {
    0: "No optimization",
    1: "Light optimization: gate cancellation, adjoint folding",
    2: "Medium optimization: commutation analysis, gate simplification",
    3: "Heavy optimization: resynthesis of subcircuits, template matching, qubit remapping"
}

def parse_qasm(source_file):
    """
    Parse OpenQASM file into a structured format.
    
    Args:
        source_file (str): Path to OpenQASM file
        
    Returns:
        dict: Parsed circuit structure
    """
    try:
        with open(source_file, 'r') as f:
            content = f.read()
            
        # This is a simplified parser for demonstration
        # In a real implementation, we would use a proper QASM parser
        
        # Extract header information
        version_match = re.search(r'OPENQASM\s+(\d+\.\d+);', content)
        version = version_match.group(1) if version_match else None
        
        # Extract include statements
        includes = re.findall(r'include\s+"([^"]+)";', content)
        
        # Extract quantum registers
        qreg_matches = re.findall(r'qreg\s+(\w+)\[(\d+)\];', content)
        qregs = {name: int(size) for name, size in qreg_matches}
        
        # Extract classical registers
        creg_matches = re.findall(r'creg\s+(\w+)\[(\d+)\];', content)
        cregs = {name: int(size) for name, size in creg_matches}
        
        # Extract gate definitions
        gate_defs = re.findall(r'gate\s+(\w+)\s+([^{]+){([^}]+)}', content)
        
        # Extract circuit operations
        operation_pattern = r'([a-zA-Z0-9_]+)(?:\(([^)]*)\))?\s+([^;]+);'
        operations = re.findall(operation_pattern, content)
        
        circuit_structure = {
            "version": version,
            "includes": includes,
            "qregs": qregs,
            "cregs": cregs,
            "gate_definitions": [{"name": name, "params": params.strip(), "body": body.strip()} 
                                for name, params, body in gate_defs],
            "operations": [{"name": name, "params": params, "qubits": qubits.strip()} 
                          for name, params, qubits in operations 
                          if name not in ["qreg", "creg", "include", "OPENQASM", "gate"]]
        }
        
        logger.info(f"Successfully parsed QASM file with {len(circuit_structure['operations'])} operations")
        return circuit_structure
        
    except Exception as e:
        logger.error(f"Error parsing QASM file: {e}")
        return None

def optimize_circuit(circuit, num_qubits, target_depth=None, optimization_level=2):
    """
    Apply optimizations to the circuit structure.
    
    Args:
        circuit (dict): Circuit structure
        num_qubits (int): Number of qubits in the circuit
        target_depth (int, optional): Target circuit depth
        optimization_level (int): Optimization level (0-3)
        
    Returns:
        dict: Optimized circuit structure with stats
    """
    logger.info(f"Applying optimization level {optimization_level}: {OPTIMIZATION_LEVELS[optimization_level]}")
    
    original_operations = len(circuit["operations"])
    original_depth = estimate_circuit_depth(circuit)
    
    # Get optimization passes based on level
    pass_manager = get_pass_manager(optimization_level)
    
    # Apply optimizations based on the level
    if optimization_level >= 1:
        # Level 1: Simple gate cancellation and adjoint folding
        circuit = cancel_adjacent_gates(circuit)
        circuit = fold_adjoint_gates(circuit)
        
    if optimization_level >= 2:
        # Level 2: Commutation analysis and gate simplification
        circuit = commutation_optimization(circuit)
        circuit = simplify_gate_sequences(circuit)
        
    if optimization_level >= 3:
        # Level 3: Advanced optimizations
        if target_depth:
            circuit = depth_optimization(circuit, target_depth)
        circuit = template_matching_optimization(circuit)
        circuit = qubit_remapping_optimization(circuit, num_qubits)
    
    # Calculate improvement statistics
    optimized_operations = len(circuit["operations"])
    optimized_depth = estimate_circuit_depth(circuit)
    
    gate_reduction = original_operations - optimized_operations
    gate_reduction_pct = (gate_reduction / original_operations) * 100 if original_operations > 0 else 0
    
    depth_reduction = original_depth - optimized_depth
    depth_reduction_pct = (depth_reduction / original_depth) * 100 if original_depth > 0 else 0
    
    circuit["optimization_stats"] = {
        "original_gate_count": original_operations,
        "optimized_gate_count": optimized_operations,
        "gate_reduction": gate_reduction,
        "gate_reduction_percentage": gate_reduction_pct,
        "original_depth": original_depth,
        "optimized_depth": optimized_depth,
        "depth_reduction": depth_reduction,
        "depth_reduction_percentage": depth_reduction_pct,
        "optimization_level": optimization_level
    }
    
    logger.info(f"Optimization reduced gate count by {gate_reduction_pct:.1f}% ({gate_reduction} gates)")
    logger.info(f"Optimization reduced circuit depth by {depth_reduction_pct:.1f}% (from {original_depth} to {optimized_depth})")
    
    return circuit

def estimate_circuit_depth(circuit):
    """
    Estimate the depth of a circuit.
    This is a simplified implementation.
    
    Args:
        circuit (dict): Circuit structure
        
    Returns:
        int: Estimated circuit depth
    """
    # In a real implementation, this would construct a proper DAG
    # and calculate the longest path through the circuit
    return len(circuit["operations"]) // 2 + 1

def cancel_adjacent_gates(circuit):
    """
    Cancel adjacent gates that would cancel each other out.
    
    Args:
        circuit (dict): Circuit structure
        
    Returns:
        dict: Optimized circuit structure
    """
    # Implementation of gate cancellation logic
    # For demonstration purposes, this is simplified
    new_operations = []
    skip_next = False
    
    for i in range(len(circuit["operations"])):
        if skip_next:
            skip_next = False
            continue
            
        if i < len(circuit["operations"]) - 1:
            current_op = circuit["operations"][i]
            next_op = circuit["operations"][i+1]
            
            # Check if operations cancel out (e.g., H followed by H)
            if (current_op["name"] == next_op["name"] and 
                current_op["qubits"] == next_op["qubits"] and
                current_op["name"] in ["h", "x", "y", "z"]):
                skip_next = True
                continue
                
        new_operations.append(circuit["operations"][i])
    
    circuit["operations"] = new_operations
    return circuit

def fold_adjoint_gates(circuit):
    """Fold adjoint gates (simplified implementation)"""
    # Implementation of adjoint folding
    return circuit

def commutation_optimization(circuit):
    """Optimize based on gate commutation rules (simplified implementation)"""
    # Implementation of commutation-based optimization
    return circuit

def simplify_gate_sequences(circuit):
    """Simplify known gate sequences (simplified implementation)"""
    # Implementation of gate sequence simplification
    return circuit

def depth_optimization(circuit, target_depth):
    """Optimize circuit to reach target depth (simplified implementation)"""
    # Implementation of depth optimization
    return circuit

def template_matching_optimization(circuit):
    """Apply template matching optimization (simplified implementation)"""
    # Implementation of template matching
    return circuit

def qubit_remapping_optimization(circuit, num_qubits):
    """Optimize qubit mapping (simplified implementation)"""
    # Implementation of qubit remapping
    return circuit

def circuit_to_qasm(circuit):
    """
    Convert circuit structure back to OpenQASM format.
    
    Args:
        circuit (dict): Circuit structure
        
    Returns:
        str: OpenQASM representation
    """
    qasm_lines = []
    
    # Add version
    qasm_lines.append(f'OPENQASM {circuit["version"]};')
    
    # Add includes
    for include in circuit["includes"]:
        qasm_lines.append(f'include "{include}";')
    
    # Add quantum registers
    for name, size in circuit["qregs"].items():
        qasm_lines.append(f'qreg {name}[{size}];')
    
    # Add classical registers
    for name, size in circuit["cregs"].items():
        qasm_lines.append(f'creg {name}[{size}];')
    
    # Add gate definitions
    for gate in circuit["gate_definitions"]:
        qasm_lines.append(f'gate {gate["name"]} {gate["params"]} {{')
        qasm_lines.append(f'  {gate["body"]}')
        qasm_lines.append('}')
    
    # Add operations
    for op in circuit["operations"]:
        params_str = f'({op["params"]})' if op["params"] else ''
        qasm_lines.append(f'{op["name"]}{params_str} {op["qubits"]};')
    
    return '\n'.join(qasm_lines)

def optimize(source_file, dest_file=None, numqubit=None, depth=None):
    """
    Optimize a quantum circuit.
    
    Args:
        source_file (str): Path to the source circuit file
        dest_file (str, optional): Path to write the optimized circuit
        numqubit (int, optional): Number of qubits constraint
        depth (int, optional): Target circuit depth
        
    Returns:
        bool: True if optimization was successful
    """
    logger.info(f"Starting circuit optimization of {source_file}")
    
    # Ensure source file exists
    if not os.path.exists(source_file):
        logger.error(f"Source file {source_file} does not exist")
        return False
    
    # Determine file type
    file_ext = os.path.splitext(source_file)[1].lower()
    
    if file_ext != '.qasm':
        logger.error(f"Unsupported file type for optimization: {file_ext}")
        return False
    
    # Get configuration
    config = get_config()
    optimization_level = config.get_setting("optimization_level", 2)
    
    # Parse the circuit
    circuit = parse_qasm(source_file)
    if not circuit:
        return False
    
    # Determine number of qubits if not specified
    if not numqubit:
        numqubit = sum(size for _, size in circuit["qregs"].items())
        logger.info(f"Using {numqubit} qubits from circuit definition")
    
    # Optimize the circuit
    optimized_circuit = optimize_circuit(circuit, numqubit, depth, optimization_level)
    
    # Generate QASM for the optimized circuit
    optimized_qasm = circuit_to_qasm(optimized_circuit)
    
    # Determine destination path
    if not dest_file:
        base, ext = os.path.splitext(source_file)
        dest_file = f"{base}_optimized{ext}"
    
    # Write optimized circuit to file
    dest_path = Path(dest_file)
    dest_dir = dest_path.parent
    
    # Create directory if it doesn't exist
    if not dest_dir.exists():
        dest_dir.mkdir(parents=True, exist_ok=True)
        
    with open(dest_file, 'w') as f:
        f.write(optimized_qasm)
    
    # Also write optimization report
    report_file = os.path.splitext(dest_file)[0] + "_report.json"
    with open(report_file, 'w') as f:
        json.dump(optimized_circuit["optimization_stats"], f, indent=2)
    
    logger.info(f"Optimized circuit written to {dest_file}")
    logger.info(f"Optimization report written to {report_file}")
    
    # Log optimization summary
    stats = optimized_circuit["optimization_stats"]
    logger.info("Optimization Summary:")
    logger.info(f"  - Gates: {stats['original_gate_count']} → {stats['optimized_gate_count']} ({stats['gate_reduction_percentage']:.1f}% reduction)")
    logger.info(f"  - Depth: {stats['original_depth']} → {stats['optimized_depth']} ({stats['depth_reduction_percentage']:.1f}% reduction)")
    
    return True

if __name__ == "__main__":
    # This allows the module to be run directly for testing
    if len(sys.argv) < 2:
        print("Usage: optimize.py <source_file> [<dest_file>] [--numqubit <num>] [--depth <depth>]")
        sys.exit(1)
    
    source = sys.argv[1]
    dest = None
    numqubit = None
    depth = None
    
    # Parse remaining arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--numqubit" and i+1 < len(sys.argv):
            numqubit = int(sys.argv[i+1])
            i += 2
        elif sys.argv[i] == "--depth" and i+1 < len(sys.argv):
            depth = int(sys.argv[i+1])
            i += 2
        else:
            dest = sys.argv[i]
            i += 1
    
    success = optimize(source, dest, numqubit, depth)
    sys.exit(0 if success else 1)
