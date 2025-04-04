"""
Commands for estimating quantum circuit resources.
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

def parse_qasm_file(filepath: str) -> Tuple[int, Dict[str, int], List[str]]:
    """
    Parse an OpenQASM file to extract qubit count and gate information.
    
    Args:
        filepath: Path to the OpenQASM file
    
    Returns:
        Tuple containing:
        - Number of qubits
        - Dictionary of gate counts
        - List of circuit lines for further analysis
    """
    try:
        # Read the QASM file
        with open(filepath, 'r') as file:
            content = file.read()
            
        # Extract all lines
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Extract qubit count from qreg declarations and track register names
        qubit_count = 0
        qreg_pattern = r'qreg\s+(\w+)\[(\d+)\]'
        register_names = []
        
        for line in lines:
            if 'qreg' in line:
                match = re.search(qreg_pattern, line)
                if match:
                    register_names.append(match.group(1))
                    qubit_count += int(match.group(2))
        
        # Count gates
        gate_counts = {
            "total": 0,
            "single_qubit": 0,
            "two_qubit": 0,
            "multi_qubit": 0,
            "h": 0,
            "x": 0,
            "y": 0,
            "z": 0,
            "cx": 0,
            "cz": 0,
            "swap": 0,
            "t": 0,
            "tdg": 0,
            "s": 0,
            "sdg": 0,
            "rx": 0,
            "ry": 0,
            "rz": 0,
            "u1": 0,
            "u2": 0,
            "u3": 0,
            "measure": 0,
            "barrier": 0,
            "other": 0
        }
        
        single_qubit_gates = ['h', 'x', 'y', 'z', 't', 'tdg', 's', 'sdg', 'rx', 'ry', 'rz', 'u1', 'u2', 'u3']
        two_qubit_gates = ['cx', 'cz', 'swap']
        
        # Custom gate definitions that we might encounter
        custom_gates = {}
        
        # Create patterns to detect register references in operation lines
        reg_patterns = []
        for reg_name in register_names:
            reg_patterns.append(f'{reg_name}\\[(\\d+)\\]')
        
        # Process each line
        for line in lines:
            # Skip QASM header, include statements, comments, qreg/creg declarations
            if line.startswith('OPENQASM') or line.startswith('include') or line.startswith('//') or 'qreg' in line or 'creg' in line:
                continue
                
            # Check for gate definitions
            if line.startswith('gate '):
                # Extract gate name
                gate_def_pattern = r'gate\s+(\w+)'
                match = re.search(gate_def_pattern, line)
                if match:
                    gate_name = match.group(1)
                    custom_gates[gate_name] = 'custom'
                continue
            
            # Count gates
            gate_found = False
            
            # Check for built-in gates
            for gate in single_qubit_gates + two_qubit_gates:
                # Regex to match the gate with word boundaries (not part of other words)
                gate_pattern = r'\b' + gate + r'\b'
                if re.search(gate_pattern, line):
                    gate_counts[gate] += 1
                    gate_counts["total"] += 1
                    
                    # Count the number of register references to determine if it's a single-qubit
                    # or multi-qubit operation, regardless of the gate name
                    qubit_ref_count = 0
                    for pattern in reg_patterns:
                        qubit_ref_count += len(re.findall(pattern, line))
                    
                    # Increment category count based on actual qubit references
                    if qubit_ref_count == 1:
                        gate_counts["single_qubit"] += 1
                    elif qubit_ref_count == 2:
                        gate_counts["two_qubit"] += 1
                    elif qubit_ref_count > 2:
                        gate_counts["multi_qubit"] += 1
                    
                    gate_found = True
                    break
            
            # Check for measure instructions
            if 'measure' in line:
                gate_counts["measure"] += 1
                gate_counts["total"] += 1
                gate_found = True
            
            # Check for barrier instructions
            if 'barrier' in line:
                gate_counts["barrier"] += 1
                gate_found = True  # Don't count barriers in total
            
            # Count custom gates or unrecognized operations
            if not gate_found and ';' in line:  # Make sure it's an operation line
                # It's an operation we didn't explicitly count
                gate_counts["other"] += 1
                gate_counts["total"] += 1
                
                # Count the number of register references to determine operation type
                qubit_ref_count = 0
                for pattern in reg_patterns:
                    qubit_ref_count += len(re.findall(pattern, line))
                
                if qubit_ref_count > 2:
                    gate_counts["multi_qubit"] += 1
                elif qubit_ref_count == 2:
                    gate_counts["two_qubit"] += 1
                elif qubit_ref_count == 1:
                    gate_counts["single_qubit"] += 1
        
        return qubit_count, gate_counts, lines
    
    except Exception as e:
        print(f"Error parsing QASM file: {e}", file=sys.stderr)
        return 0, {"total": 0}, []

def calculate_circuit_depth(lines: List[str], qubit_count: int) -> int:
    """
    Calculate the circuit depth (approximate).
    
    This is a simplified algorithm that works by tracking operations per qubit
    and determining the maximum path length.
    
    Args:
        lines: Circuit lines from the QASM file
        qubit_count: Number of qubits in the circuit
    
    Returns:
        Estimated circuit depth
    """
    # This is a simplified approach - in reality, circuit depth calculation
    # requires understanding of gate parallelism and dependencies
    
    # Track the last operation time (depth) for each qubit
    qubit_times = [0] * qubit_count
    
    # Extract all register names from qreg statements
    qreg_pattern = r'qreg\s+(\w+)\[(\d+)\]'
    register_names = []
    register_sizes = {}
    register_offset = {}  # To track offset of each register in the overall qubit array
    
    offset = 0
    for line in lines:
        if 'qreg' in line:
            match = re.search(qreg_pattern, line)
            if match:
                reg_name = match.group(1)
                reg_size = int(match.group(2))
                register_names.append(reg_name)
                register_sizes[reg_name] = reg_size
                register_offset[reg_name] = offset
                offset += reg_size
    
    # Create pattern to detect any qubit reference
    qubit_patterns = []
    for reg_name in register_names:
        qubit_patterns.append(f'{reg_name}\\[(\\d+)\\]')
    
    for line in lines:
        # Skip non-operation lines
        if not ';' in line or line.startswith('OPENQASM') or line.startswith('include') or 'qreg' in line or 'creg' in line:
            continue
        
        # Find all qubit references
        affected_qubits = []
        for i, pattern in enumerate(qubit_patterns):
            reg_name = register_names[i]
            matches = re.findall(pattern, line)
            for idx_str in matches:
                idx = int(idx_str)
                # Calculate global qubit index
                global_idx = register_offset[reg_name] + idx
                if global_idx < qubit_count:
                    affected_qubits.append(global_idx)
        
        if affected_qubits:
            # For gates involving multiple qubits, the new time is the max time of all involved qubits + 1
            current_max_time = max(qubit_times[idx] for idx in affected_qubits if idx < len(qubit_times))
            
            # Update times for all qubits involved in this operation
            for idx in affected_qubits:
                if idx < len(qubit_times):
                    qubit_times[idx] = current_max_time + 1
    
    # The circuit depth is the maximum time reached by any qubit
    return max(qubit_times) if qubit_times else 0

def calculate_t_depth(lines: List[str], qubit_count: int) -> int:
    """
    Calculate the T-depth of the circuit (T and T† gates).
    
    Args:
        lines: Circuit lines from the QASM file
        qubit_count: Number of qubits in the circuit
    
    Returns:
        T-depth of the circuit
    """
    # Track the last T-gate operation time for each qubit
    qubit_t_times = [0] * qubit_count
    
    # Track if we're currently in a T-gate layer for each qubit
    in_t_layer = [False] * qubit_count
    
    # Current overall T-depth
    t_depth = 0
    
    # Extract all register names from qreg statements
    qreg_pattern = r'qreg\s+(\w+)\[(\d+)\]'
    register_names = []
    register_sizes = {}
    register_offset = {}  # To track offset of each register in the overall qubit array
    
    offset = 0
    for line in lines:
        if 'qreg' in line:
            match = re.search(qreg_pattern, line)
            if match:
                reg_name = match.group(1)
                reg_size = int(match.group(2))
                register_names.append(reg_name)
                register_sizes[reg_name] = reg_size
                register_offset[reg_name] = offset
                offset += reg_size
    
    # Create pattern to detect any qubit reference
    qubit_patterns = []
    for reg_name in register_names:
        qubit_patterns.append(f'{reg_name}\\[(\\d+)\\]')
    
    # Create patterns for T and Tdg gates with various register names
    t_patterns = []
    for reg_name in register_names:
        t_patterns.append(rf'\b(t|tdg)\s+{reg_name}\[(\d+)\]')
    
    for line in lines:
        # Skip non-operation lines
        if not ';' in line or line.startswith('OPENQASM') or line.startswith('include') or 'qreg' in line or 'creg' in line:
            continue
        
        # Check if it's a T or T† gate for any register
        t_found = False
        for i, pattern in enumerate(t_patterns):
            reg_name = register_names[i]
            t_matches = re.search(pattern, line)
            
            if t_matches:
                # It's a T or T† gate
                t_found = True
                idx = int(t_matches.group(2))
                # Calculate global qubit index
                global_idx = register_offset[reg_name] + idx
                
                if global_idx < len(qubit_t_times):
                    if not in_t_layer[global_idx]:
                        # Starting a new T layer for this qubit
                        in_t_layer[global_idx] = True
                        qubit_t_times[global_idx] += 1
                        t_depth = max(t_depth, qubit_t_times[global_idx])
                break
        
        if not t_found:
            # It's not a T gate - find all qubit references to end any T layers
            affected_qubits = []
            for i, pattern in enumerate(qubit_patterns):
                reg_name = register_names[i]
                matches = re.findall(pattern, line)
                for idx_str in matches:
                    idx = int(idx_str)
                    # Calculate global qubit index
                    global_idx = register_offset[reg_name] + idx
                    if global_idx < qubit_count:
                        affected_qubits.append(global_idx)
            
            # For any qubit involved, end its T layer if it was in one
            for idx in affected_qubits:
                if idx < len(in_t_layer) and in_t_layer[idx]:
                    in_t_layer[idx] = False
    
    return t_depth

def estimate_error_probability(gate_counts: Dict[str, int], qubit_count: int) -> float:
    """
    Estimate the overall error probability based on gate counts and qubit number.
    
    Args:
        gate_counts: Dictionary of gate counts
        qubit_count: Number of qubits
    
    Returns:
        Estimated error probability
    """
    # These error rates are examples and would need to be adjusted based on 
    # real hardware characteristics
    single_qubit_error_rate = 0.001  # 0.1% error per single-qubit gate
    two_qubit_error_rate = 0.01      # 1% error per two-qubit gate
    multi_qubit_error_rate = 0.03    # 3% error per multi-qubit gate
    measurement_error_rate = 0.02    # 2% error per measurement
    
    # Calculate combined error probability using simple model
    # 1 - [(1 - single_error) ^ num_single] * [(1 - two_error) ^ num_two] * ...
    
    error_prob = 1.0
    error_prob *= (1 - single_qubit_error_rate) ** gate_counts.get("single_qubit", 0)
    error_prob *= (1 - two_qubit_error_rate) ** gate_counts.get("two_qubit", 0)
    error_prob *= (1 - multi_qubit_error_rate) ** gate_counts.get("multi_qubit", 0)
    error_prob *= (1 - measurement_error_rate) ** gate_counts.get("measure", 0)
    
    # Convert to error probability
    error_prob = 1.0 - error_prob
    
    # Cap at reasonable values
    return min(0.99, max(0.001, error_prob))

def estimate_runtime(gate_counts: Dict[str, int], circuit_depth: int, t_depth: int) -> Dict[str, str]:
    """
    Estimate runtime on different quantum platforms.
    
    Args:
        gate_counts: Dictionary of gate counts
        circuit_depth: Circuit depth
        t_depth: T-depth of the circuit
    
    Returns:
        Dictionary with estimated runtimes per platform
    """
    # These time estimates are examples and would need to be adjusted
    # based on real hardware characteristics
    
    # Superconducting qubits (like IBM, Google)
    # Typically: single-qubit gates ~20-50ns, two-qubit gates ~100-300ns
    superconducting_time_ns = (
        20 * gate_counts.get("single_qubit", 0) +
        150 * gate_counts.get("two_qubit", 0) +
        500 * gate_counts.get("multi_qubit", 0) +
        1000 * gate_counts.get("measure", 0)
    )
    
    # For fully parallelizable circuits, time is more dependent on depth
    superconducting_parallel_time_ns = circuit_depth * 150  # Assuming average gate time of 150ns
    
    # Use the smaller of the two estimates (but with a minimum reasonable time)
    superconducting_time_ns = min(superconducting_time_ns, max(1000, superconducting_parallel_time_ns))
    
    # Ion trap systems (like IonQ)
    # Typically: gates are slower but higher fidelity, ~10-100μs per gate
    ion_trap_time_us = (
        10 * gate_counts.get("single_qubit", 0) +
        50 * gate_counts.get("two_qubit", 0) +
        100 * gate_counts.get("multi_qubit", 0) +
        200 * gate_counts.get("measure", 0)
    )
    
    ion_trap_parallel_time_us = circuit_depth * 50  # Assuming average gate time of 50μs
    ion_trap_time_us = min(ion_trap_time_us, max(100, ion_trap_parallel_time_us))
    
    # Photonic systems
    # Very different architecture - often time is dominated by measurement
    photonic_time_us = 5 * circuit_depth + 50 * gate_counts.get("measure", 0)
    
    # Format the times with appropriate units
    runtime_estimates = {}
    
    if superconducting_time_ns < 1000:
        runtime_estimates["superconducting"] = f"~{superconducting_time_ns} ns"
    elif superconducting_time_ns < 1000000:
        runtime_estimates["superconducting"] = f"~{superconducting_time_ns/1000:.1f} μs"
    else:
        runtime_estimates["superconducting"] = f"~{superconducting_time_ns/1000000:.2f} ms"
        
    if ion_trap_time_us < 1000:
        runtime_estimates["ion_trap"] = f"~{ion_trap_time_us:.1f} μs"
    else:
        runtime_estimates["ion_trap"] = f"~{ion_trap_time_us/1000:.2f} ms"
        
    if photonic_time_us < 1000:
        runtime_estimates["photonic"] = f"~{photonic_time_us:.1f} μs"
    else:
        runtime_estimates["photonic"] = f"~{photonic_time_us/1000:.2f} ms"
    
    return runtime_estimates

def estimate_resources(source: str, dest: str = "results/resource_estimation") -> Optional[Dict[str, Any]]:
    """Estimate resources required for a quantum circuit.
    
    Args:
        source: Source file path (OpenQASM file)
        dest: Destination file for resource estimation results
    
    Returns:
        Dictionary with resource estimation metrics
    """
    try:
        # Ensure the output directory exists
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Loading circuit from {source}")
        
        # Parse the QASM file to get qubit count and gate information
        qubit_count, gate_counts, circuit_lines = parse_qasm_file(source)
        
        if qubit_count == 0:
            print(f"Error: Could not determine qubit count from {source}", file=sys.stderr)
            return None
            
        print(f"Analyzing circuit resource requirements")
        
        # Calculate circuit depth
        circuit_depth = calculate_circuit_depth(circuit_lines, qubit_count)
        
        # Calculate T-depth
        t_depth = calculate_t_depth(circuit_lines, qubit_count)
        
        # Estimate error probability
        error_probability = estimate_error_probability(gate_counts, qubit_count)
        
        # Estimate runtime on different platforms
        estimated_runtime = estimate_runtime(gate_counts, circuit_depth, t_depth)
        
        # Create the results dictionary
        results = {
            "circuit_name": Path(source).stem,
            "qubit_count": qubit_count,
            "gate_counts": gate_counts,
            "circuit_depth": circuit_depth,
            "critical_path_length": circuit_depth,  # Same as circuit depth in our simple model
            "t_depth": t_depth,
            "estimated_runtime": estimated_runtime,
            "error_probability_estimate": error_probability
        }
        
        # Save results to file
        with open(dest_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Resource estimation results saved to {dest}")
        
        return results
    except Exception as e:
        print(f"Error estimating circuit resources: {e}", file=sys.stderr)
        return None 