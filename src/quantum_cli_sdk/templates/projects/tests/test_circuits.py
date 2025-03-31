"""
Tests for quantum circuits.
"""

import sys
import unittest
from pathlib import Path

# Add the source directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from circuits import create_bell_circuit, create_grover_circuit, run_grover_search


class TestBellCircuit(unittest.TestCase):
    """Tests for the Bell state circuit."""

    def test_bell_creation(self):
        """Test that a Bell circuit can be created with the right qubit count."""
        circuit = create_bell_circuit(2)
        self.assertEqual(circuit["name"], "Bell State")
        self.assertEqual(circuit["qubits"], 2)
        self.assertEqual(len(circuit["gates"]), 2)
        
    def test_bell_gates(self):
        """Test that the Bell circuit has the correct gates."""
        circuit = create_bell_circuit(2)
        gates = circuit["gates"]
        
        # First gate should be Hadamard on qubit 0
        self.assertEqual(gates[0]["name"], "h")
        self.assertEqual(gates[0]["qubits"], [0])
        
        # Second gate should be CNOT between qubits 0 and 1
        self.assertEqual(gates[1]["name"], "cx")
        self.assertEqual(gates[1]["qubits"], [0, 1])
        
    def test_bell_invalid_qubit_count(self):
        """Test that the Bell circuit handles invalid qubit counts."""
        # In a real implementation, this might raise an error for < 2 qubits
        circuit = create_bell_circuit(1)
        self.assertEqual(circuit["qubits"], 1)


class TestGroverCircuit(unittest.TestCase):
    """Tests for the Grover search algorithm circuit."""
    
    def test_grover_creation(self):
        """Test that a Grover circuit can be created."""
        circuit = create_grover_circuit(3, 2)
        self.assertEqual(circuit["name"], "Grover's Search")
        self.assertEqual(circuit["qubits"], 3)
        self.assertEqual(circuit["target"], 2)
        
    def test_grover_gates(self):
        """Test that the Grover circuit has the correct gates."""
        circuit = create_grover_circuit(3, 2)
        gates = circuit["gates"]
        
        # Should have 3 gates (initialization, oracle, diffusion)
        self.assertEqual(len(gates), 3)
        
        # First gate should be Hadamard on all qubits
        self.assertEqual(gates[0]["name"], "h")
        self.assertEqual(gates[0]["qubits"], [0, 1, 2])
        
        # Second gate should be oracle
        self.assertEqual(gates[1]["name"], "oracle")
        self.assertEqual(gates[1]["qubits"], [0, 1, 2])
        self.assertEqual(gates[1]["params"]["marked_item"], 2)
        
        # Third gate should be diffusion
        self.assertEqual(gates[2]["name"], "diffusion")
        self.assertEqual(gates[2]["qubits"], [0, 1, 2])
        
    def test_grover_search_results(self):
        """Test that Grover's search returns the expected results format."""
        circuit = create_grover_circuit(3, 2)
        results = run_grover_search(circuit, shots=1000)
        
        # Check results structure
        self.assertIn("counts", results)
        self.assertIn("most_probable", results)
        
        # The most_probable outcome should be the target state
        target_state = format(circuit["target"], f"0{circuit['qubits']}b")
        self.assertEqual(results["most_probable"], target_state)
        
        # The target state should have the highest count
        counts = results["counts"]
        self.assertEqual(max(counts, key=counts.get), target_state)


if __name__ == "__main__":
    unittest.main() 