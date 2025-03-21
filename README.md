# Quantum CLI SDK

A command-line interface and software development kit for quantum computing.

## Installation

```bash
pip install quantum-cli-sdk
```

## Usage

### Command Line Interface

```bash
# Display help message
quantum-cli --help

# Create a basic quantum circuit
quantum-cli circuit create --qubits 2

# Run a quantum simulation
quantum-cli run --shots 1024 --output results.json
```

### SDK Usage

```python
from quantum_sdk import QuantumCircuit, run_simulation

# Create a circuit
circuit = QuantumCircuit(2)
circuit.h(0)  # Apply Hadamard gate to qubit 0
circuit.cx(0, 1)  # Apply CNOT gate with control qubit 0 and target qubit 1

# Run simulation
results = run_simulation(circuit, shots=1024)
print(results)
```

## Features

- Intuitive command-line interface for quantum operations
- Comprehensive SDK for quantum circuit creation and manipulation
- Quantum gate operations and measurement capabilities
- Simulation of quantum circuits
- Extensible architecture for custom quantum components

## Development

To set up the development environment:

```bash
pip install -e ".[dev]"
```

To run tests:

```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
