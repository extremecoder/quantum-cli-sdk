"""
Commands for quantum circuit creation and manipulation.
"""

import json
import sys
from pathlib import Path

from ..quantum_circuit import QuantumCircuit

def create_circuit(num_qubits, output_file=None):
    """Create a new quantum circuit.
    
    Args:
        num_qubits: Number of qubits in the circuit
        output_file: Optional file path to save the circuit
    """
    try:
        # Create a new circuit
        circuit = QuantumCircuit(num_qubits)
        
        print(f"Created a quantum circuit with {num_qubits} qubits.")
        
        # Save to file if specified
        if output_file:
            path = Path(output_file)
            with open(path, 'w') as f:
                json.dump(circuit.to_dict(), f, indent=2)
            print(f"Circuit saved to {output_file}")
        
        return circuit
    except Exception as e:
        print(f"Error creating circuit: {e}", file=sys.stderr)
        return None
