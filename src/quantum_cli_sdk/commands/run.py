"""
Commands for running quantum simulations.
"""

import json
import sys
from pathlib import Path

from ..quantum_circuit import QuantumCircuit
from ..simulator import run_simulation

def run_simulation_cmd(circuit_file=None, shots=1024, output_file=None):
    """Run a simulation on a quantum circuit.
    
    Args:
        circuit_file: File containing the circuit description
        shots: Number of measurement shots
        output_file: Optional file path to save the results
    """
    try:
        if circuit_file:
            # Load circuit from file
            path = Path(circuit_file)
            if not path.exists():
                print(f"Error: Circuit file {circuit_file} not found", file=sys.stderr)
                return None
            
            with open(path, 'r') as f:
                circuit_data = json.load(f)
            
            circuit = QuantumCircuit.from_dict(circuit_data)
            print(f"Loaded circuit with {circuit.num_qubits} qubits from {circuit_file}")
        else:
            # Create a default Bell state circuit
            circuit = QuantumCircuit(2)
            circuit.h(0)
            circuit.cx(0, 1)
            print("No circuit specified. Created a Bell state circuit.")
        
        # Run the simulation
        print(f"Running simulation with {shots} shots...")
        results = run_simulation(circuit, shots)
        
        # Print results
        print("\nMeasurement results:")
        for state, count in results.items():
            probability = count / shots
            print(f"  |{state}⟩: {count} ({probability:.2%})")
        
        # Save to file if specified
        if output_file:
            path = Path(output_file)
            with open(path, 'w') as f:
                json.dump({"results": results, "shots": shots}, f, indent=2)
            print(f"\nResults saved to {output_file}")
        
        return results
    except Exception as e:
        print(f"Error running simulation: {e}", file=sys.stderr)
        return None
