# Example Usage

This document provides examples of how to use the quantum computing functionality provided by this project.

## Bell State Example

The Bell state (also known as an EPR pair) is one of the simplest examples of entanglement in quantum mechanics. It represents a quantum state of two qubits that cannot be expressed as a product of states of individual qubits.

### Code Example

```python
from circuits import create_bell_circuit
from utilities import visualize_circuit, plot_results

# Create a Bell state circuit
circuit = create_bell_circuit(num_qubits=2)

# Visualize the circuit
visualize_circuit(circuit)

# In a real application, you would run the circuit on a simulator or real hardware
# Here we're using placeholder results
results = {
    "counts": {"00": 12, "01": 0, "10": 0, "11": 1012},
    "most_probable": "11"
}

# Plot the results
plot_results(results)
```

## Grover's Search Algorithm Example

Grover's algorithm is a quantum algorithm for searching an unsorted database with N entries in O(√N) time. This provides a quadratic speedup over classical search algorithms.

### Code Example

```python
from circuits import create_grover_circuit, run_grover_search
from utilities import visualize_circuit, plot_results, apply_readout_error_mitigation

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
plot_results(mitigated_results)
```

## Error Mitigation Example

Error mitigation techniques aim to reduce the impact of noise on quantum computations, allowing for more accurate results without the overhead of full quantum error correction.

### Code Example

```python
from circuits import create_bell_circuit
from utilities import apply_zne, apply_readout_error_mitigation

# Create a Bell state circuit
circuit = create_bell_circuit(num_qubits=2)

# Apply Zero-Noise Extrapolation to mitigate errors
mitigated_circuit = apply_zne(circuit, scale_factors=[1.0, 2.0, 3.0])

# Run the original and mitigated circuits (simulated here)
original_results = {
    "counts": {"00": 50, "01": 200, "10": 150, "11": 624}
}

# Apply readout error mitigation to the results
mitigated_results = apply_readout_error_mitigation(original_results)

# Compare results (in a real application)
print(f"Original probability of '11': {original_results['counts']['11'] / 1024:.3f}")
print(f"Mitigated probability of '11': {mitigated_results['counts']['11'] / 1024:.3f}")
```

## API Usage Example

The project includes a web API that allows you to run quantum circuits through HTTP requests.

### Python Client Example

```python
import requests
import time
import json

# Define the base URL for the API
BASE_URL = "http://localhost:8000"

# List available circuits
response = requests.get(f"{BASE_URL}/circuits")
circuits = response.json()["data"]
print(f"Available circuits: {[circuit['id'] for circuit in circuits]}")

# Get details for a specific circuit
bell_response = requests.get(f"{BASE_URL}/circuits/bell")
bell_details = bell_response.json()["data"]
print(f"Bell circuit details: {bell_details}")

# Run a circuit
run_payload = {
    "circuit_id": "bell",
    "shots": 1024
}
run_response = requests.post(f"{BASE_URL}/run", json=run_payload)
job_data = run_response.json()["data"]
job_id = job_data["job_id"]
print(f"Job submitted with ID: {job_id}")

# Wait for the job to complete
time.sleep(2)  # In a real application, this would be a polling loop

# Get the results
results_response = requests.get(f"{BASE_URL}/results/{job_id}")
results = results_response.json()["data"]["results"]
print(json.dumps(results, indent=2))
```