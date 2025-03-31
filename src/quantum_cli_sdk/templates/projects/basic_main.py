#!/usr/bin/env python3
"""
Main module for basic quantum project.
"""

import sys
from pathlib import Path

# Add source directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import project components
from circuits import create_bell_circuit, create_grover_circuit, run_grover_search
from utilities import visualize_circuit, plot_results, apply_readout_error_mitigation
from api import setup_routes


def run_bell_example():
    """Run a Bell state example."""
    print("\n=== Bell State Example ===")
    
    # Create a Bell state circuit
    circuit = create_bell_circuit(num_qubits=2)
    
    # Visualize the circuit
    visualize_circuit(circuit)
    
    # In a real example, this would run the circuit
    print("\nSimulating Bell state circuit execution...")
    results = {
        "counts": {"00": 12, "01": 0, "10": 0, "11": 1012},
        "most_probable": "11"
    }
    
    # Plot the results
    plot_results(results)


def run_grover_example():
    """Run a Grover's algorithm example."""
    print("\n=== Grover's Algorithm Example ===")
    
    # Create a Grover circuit to search for value 6
    circuit = create_grover_circuit(num_qubits=3, marked_item=6)
    
    # Visualize the circuit
    visualize_circuit(circuit)
    
    # Run the circuit simulation
    results = run_grover_search(circuit, shots=1024)
    
    # Plot the results
    plot_results(results)
    
    # Apply error mitigation
    mitigated_results = apply_readout_error_mitigation(results)
    
    # Plot mitigated results
    print("\nAfter error mitigation:")
    plot_results(mitigated_results)


def setup_api():
    """Set up a simple web API for the quantum circuits."""
    print("\n=== Setting up Quantum API ===")
    app = setup_routes(None)
    
    print(f"\nAPI created with name: {app['name']} v{app['version']}")
    print(f"Available routes:")
    for route in app["routes"]:
        print(f"  {route['method']} {route['path']} - {route['description']}")
    
    print("\nIn a real application, this would start a web server.")
    print("You could then access the API at: http://localhost:8000")


def main():
    """Main function for the quantum project."""
    print("Quantum project initialized successfully!")
    
    # Run Bell state example
    run_bell_example()
    
    # Run Grover's algorithm example
    run_grover_example()
    
    # Setup API
    setup_api()
    
    print("\nAll examples completed successfully.")


if __name__ == "__main__":
    main() 