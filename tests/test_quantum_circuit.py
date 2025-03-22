"""
Tests for the QuantumCircuit class.
"""

import pytest
import numpy as np
from quantum_cli_sdk import QuantumCircuit, run_simulation

def test_circuit_creation():
    """Test quantum circuit creation."""
    circuit = QuantumCircuit(2)
    assert circuit.num_qubits == 2
    assert len(circuit.gates) == 0

def test_circuit_gates():
    """Test adding gates to a circuit."""
    circuit = QuantumCircuit(2)
    
    # Add Hadamard gate to qubit 0
    circuit.h(0)
    assert len(circuit.gates) == 1
    assert circuit.gates[0]['gate'] == 'h'
    assert circuit.gates[0]['targets'] == [0]
    
    # Add CNOT gate
    circuit.cx(0, 1)
    assert len(circuit.gates) == 2
    assert circuit.gates[1]['gate'] == 'cx'
    assert circuit.gates[1]['targets'] == [0, 1]

def test_bell_state_simulation():
    """Test simulation of a Bell state."""
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    
    # Run simulation with many shots to get stable statistics
    results = run_simulation(circuit, shots=10000)
    
    # A Bell state should have roughly equal probabilities for |00⟩ and |11⟩
    # and zero probability for |01⟩ and |10⟩
    assert '00' in results
    assert '11' in results
    assert results.get('01', 0) == 0
    assert results.get('10', 0) == 0
    
    # Check probabilities are roughly equal (within 10%)
    p00 = results['00'] / 10000
    p11 = results['11'] / 10000
    assert abs(p00 - 0.5) < 0.1
    assert abs(p11 - 0.5) < 0.1

def test_circuit_serialization():
    """Test circuit serialization to/from dict."""
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    
    # Convert to dict
    circuit_dict = circuit.to_dict()
    
    # Create a new circuit from the dict
    new_circuit = QuantumCircuit.from_dict(circuit_dict)
    
    # Verify the new circuit has the same properties
    assert new_circuit.num_qubits == circuit.num_qubits
    assert len(new_circuit.gates) == len(circuit.gates)
    
    # Check gates are the same
    for i, gate in enumerate(circuit.gates):
        assert new_circuit.gates[i]['gate'] == gate['gate']
        assert new_circuit.gates[i]['targets'] == gate['targets']
