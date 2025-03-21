"""
Quantum circuit simulator.
"""

import numpy as np
from collections import Counter
from typing import Dict, List, Optional, Union

from .quantum_circuit import QuantumCircuit

# Define common gates as numpy arrays
GATE_OPERATIONS = {
    # Pauli gates
    'x': np.array([[0, 1], [1, 0]], dtype=complex),
    'y': np.array([[0, -1j], [1j, 0]], dtype=complex),
    'z': np.array([[1, 0], [0, -1]], dtype=complex),
    
    # Hadamard gate
    'h': 1/np.sqrt(2) * np.array([[1, 1], [1, -1]], dtype=complex),
    
    # Phase gates
    's': np.array([[1, 0], [0, 1j]], dtype=complex),
    't': np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex),
}

def run_simulation(circuit: QuantumCircuit, shots: int = 1024) -> Dict[str, int]:
    """Run a simulation of the quantum circuit.
    
    Args:
        circuit: Quantum circuit to simulate
        shots: Number of measurement shots
    
    Returns:
        Dict[str, int]: Measurement results as a dictionary mapping bit strings to counts
    """
    # Initialize the quantum state as |0...0⟩
    state_size = 2 ** circuit.num_qubits
    state_vector = np.zeros(state_size, dtype=complex)
    state_vector[0] = 1.0  # |0...0⟩ state
    
    # Apply all gates in the circuit
    for gate_op in circuit.gates:
        gate_name = gate_op['gate']
        targets = gate_op['targets']
        params = gate_op['params']
        
        if gate_name in ['x', 'y', 'z', 'h', 's', 't']:
            state_vector = apply_single_qubit_gate(state_vector, GATE_OPERATIONS[gate_name], targets[0], circuit.num_qubits)
        elif gate_name == 'cx':
            state_vector = apply_cnot_gate(state_vector, targets[0], targets[1], circuit.num_qubits)
        elif gate_name == 'cz':
            state_vector = apply_cz_gate(state_vector, targets[0], targets[1], circuit.num_qubits)
        elif gate_name in ['rx', 'ry', 'rz']:
            angle = params[0]
            if gate_name == 'rx':
                gate = np.array([
                    [np.cos(angle/2), -1j*np.sin(angle/2)],
                    [-1j*np.sin(angle/2), np.cos(angle/2)]
                ], dtype=complex)
            elif gate_name == 'ry':
                gate = np.array([
                    [np.cos(angle/2), -np.sin(angle/2)],
                    [np.sin(angle/2), np.cos(angle/2)]
                ], dtype=complex)
            elif gate_name == 'rz':
                gate = np.array([
                    [np.exp(-1j*angle/2), 0],
                    [0, np.exp(1j*angle/2)]
                ], dtype=complex)
            state_vector = apply_single_qubit_gate(state_vector, gate, targets[0], circuit.num_qubits)
    
    # Perform measurement
    probabilities = np.abs(state_vector) ** 2
    results = np.random.choice(state_size, size=shots, p=probabilities)
    counts = Counter(results)
    
    # Convert to binary representation
    binary_counts = {}
    for state, count in counts.items():
        # Convert to binary and pad with leading zeros
        binary = format(state, f'0{circuit.num_qubits}b')
        binary_counts[binary] = count
    
    return binary_counts

def apply_single_qubit_gate(state_vector: np.ndarray, gate: np.ndarray, target: int, num_qubits: int) -> np.ndarray:
    """Apply a single-qubit gate to the state vector.
    
    Args:
        state_vector: Current state vector
        gate: 2x2 gate matrix
        target: Target qubit
        num_qubits: Total number of qubits
    
    Returns:
        np.ndarray: New state vector after gate application
    """
    target_factor = 2 ** target
    
    # Reshape the state vector to apply the gate
    new_state = np.zeros_like(state_vector)
    
    for i in range(len(state_vector)):
        # Determine if the target qubit is 0 or 1 for this basis state
        bit_val = (i // target_factor) % 2
        
        # Calculate index for the state with the flipped bit
        if bit_val == 0:
            idx_other = i + target_factor  # Flip from |0⟩ to |1⟩
        else:
            idx_other = i - target_factor  # Flip from |1⟩ to |0⟩
            
        # Apply gate elements
        if bit_val == 0:
            new_state[i] += gate[0, 0] * state_vector[i]
            new_state[idx_other] += gate[1, 0] * state_vector[i]
        else:
            new_state[idx_other] += gate[0, 1] * state_vector[i]
            new_state[i] += gate[1, 1] * state_vector[i]
    
    return new_state

def apply_cnot_gate(state_vector: np.ndarray, control: int, target: int, num_qubits: int) -> np.ndarray:
    """Apply a CNOT gate to the state vector.
    
    Args:
        state_vector: Current state vector
        control: Control qubit
        target: Target qubit
        num_qubits: Total number of qubits
    
    Returns:
        np.ndarray: New state vector after gate application
    """
    # Make a copy to avoid modifying the original
    new_state = np.zeros_like(state_vector)
    
    # Calculate the factors for bit manipulation
    control_factor = 2 ** control
    target_factor = 2 ** target
    
    # Process each basis state
    for i in range(len(state_vector)):
        # Check if control bit is set
        control_bit = (i // control_factor) % 2
        
        if control_bit == 0:
            # If control is 0, do nothing (copy the amplitude)
            new_state[i] = state_vector[i]
        else:
            # If control is 1, flip the target bit
            target_bit = (i // target_factor) % 2
            
            # Calculate the new index with flipped target bit
            flipped_idx = i
            if target_bit == 0:
                # Add target_factor to set the bit
                flipped_idx += target_factor
            else:
                # Subtract target_factor to clear the bit
                flipped_idx -= target_factor
                
            # Copy the amplitude to the flipped position
            new_state[flipped_idx] = state_vector[i]
    
    return new_state

def apply_cz_gate(state_vector: np.ndarray, control: int, target: int, num_qubits: int) -> np.ndarray:
    """Apply a CZ gate to the state vector.
    
    Args:
        state_vector: Current state vector
        control: Control qubit
        target: Target qubit
        num_qubits: Total number of qubits
    
    Returns:
        np.ndarray: New state vector after gate application
    """
    control_factor = 2 ** control
    target_factor = 2 ** target
    
    new_state = np.copy(state_vector)
    
    for i in range(len(state_vector)):
        # Determine if both the control and target qubits are 1 for this basis state
        control_val = (i // control_factor) % 2
        target_val = (i // target_factor) % 2
        
        if control_val == 1 and target_val == 1:
            # Apply phase flip (-1) to the amplitude when both qubits are 1
            new_state[i] = -state_vector[i]
    
    return new_state
