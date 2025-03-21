"""
Quantum circuit implementation.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Union

class QuantumCircuit:
    """Represents a quantum circuit with gates and measurements."""
    
    def __init__(self, num_qubits: int):
        """Initialize a quantum circuit with specified number of qubits.
        
        Args:
            num_qubits: Number of qubits in the circuit
        """
        self.num_qubits = num_qubits
        self.gates = []
        self._validate_num_qubits()
    
    def _validate_num_qubits(self):
        """Validate the number of qubits."""
        if not isinstance(self.num_qubits, int) or self.num_qubits <= 0:
            raise ValueError("Number of qubits must be a positive integer")
    
    def _validate_qubit_index(self, qubit_index: int):
        """Validate a qubit index is within range.
        
        Args:
            qubit_index: Index of the qubit to validate
        
        Raises:
            ValueError: If qubit_index is invalid
        """
        if not isinstance(qubit_index, int) or qubit_index < 0 or qubit_index >= self.num_qubits:
            raise ValueError(f"Qubit index must be between 0 and {self.num_qubits - 1}")
    
    def add_gate(self, gate_name: str, targets: List[int], params: Optional[List[float]] = None):
        """Add a gate to the circuit.
        
        Args:
            gate_name: Name of the gate
            targets: List of target qubits
            params: Optional parameters for parameterized gates
        """
        for qubit in targets:
            self._validate_qubit_index(qubit)
        
        self.gates.append({
            'gate': gate_name,
            'targets': targets.copy(),
            'params': params.copy() if params else None
        })
        
        return self
    
    def h(self, qubit: int):
        """Apply Hadamard gate to the specified qubit.
        
        Args:
            qubit: Target qubit
        
        Returns:
            self: For method chaining
        """
        return self.add_gate('h', [qubit])
    
    def x(self, qubit: int):
        """Apply Pauli-X (NOT) gate to the specified qubit.
        
        Args:
            qubit: Target qubit
        
        Returns:
            self: For method chaining
        """
        return self.add_gate('x', [qubit])
    
    def y(self, qubit: int):
        """Apply Pauli-Y gate to the specified qubit.
        
        Args:
            qubit: Target qubit
        
        Returns:
            self: For method chaining
        """
        return self.add_gate('y', [qubit])
    
    def z(self, qubit: int):
        """Apply Pauli-Z gate to the specified qubit.
        
        Args:
            qubit: Target qubit
        
        Returns:
            self: For method chaining
        """
        return self.add_gate('z', [qubit])
    
    def cx(self, control: int, target: int):
        """Apply CNOT (Controlled-X) gate.
        
        Args:
            control: Control qubit
            target: Target qubit
        
        Returns:
            self: For method chaining
        """
        return self.add_gate('cx', [control, target])
    
    def cz(self, control: int, target: int):
        """Apply Controlled-Z gate.
        
        Args:
            control: Control qubit
            target: Target qubit
        
        Returns:
            self: For method chaining
        """
        return self.add_gate('cz', [control, target])
    
    def rx(self, qubit: int, angle: float):
        """Apply rotation around X-axis.
        
        Args:
            qubit: Target qubit
            angle: Rotation angle in radians
        
        Returns:
            self: For method chaining
        """
        return self.add_gate('rx', [qubit], [angle])
    
    def ry(self, qubit: int, angle: float):
        """Apply rotation around Y-axis.
        
        Args:
            qubit: Target qubit
            angle: Rotation angle in radians
        
        Returns:
            self: For method chaining
        """
        return self.add_gate('ry', [qubit], [angle])
    
    def rz(self, qubit: int, angle: float):
        """Apply rotation around Z-axis.
        
        Args:
            qubit: Target qubit
            angle: Rotation angle in radians
        
        Returns:
            self: For method chaining
        """
        return self.add_gate('rz', [qubit], [angle])
    
    def to_dict(self):
        """Convert the circuit to a dictionary representation.
        
        Returns:
            dict: Dictionary representation of the circuit
        """
        return {
            'num_qubits': self.num_qubits,
            'gates': self.gates
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create a circuit from a dictionary representation.
        
        Args:
            data: Dictionary representation of a circuit
        
        Returns:
            QuantumCircuit: The created circuit
        """
        circuit = cls(data['num_qubits'])
        for gate in data['gates']:
            circuit.add_gate(gate['gate'], gate['targets'], gate['params'])
        return circuit
    
    def __str__(self):
        """Return a string representation of the circuit.
        
        Returns:
            str: String representation
        """
        result = f"QuantumCircuit({self.num_qubits} qubits, {len(self.gates)} gates)\n"
        for i, gate in enumerate(self.gates):
            params_str = f", params={gate['params']}" if gate['params'] else ""
            result += f"  {i}: {gate['gate']} on qubits {gate['targets']}{params_str}\n"
        return result
