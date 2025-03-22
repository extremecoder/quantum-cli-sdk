# Quantum CLI SDK User Guide

Welcome to the Quantum CLI SDK! This user guide will help you get started with using the Quantum CLI SDK for your quantum computing projects.

## Table of Contents

1. [Installation](#installation)
2. [Getting Started](#getting-started)
3. [Interactive Mode](#interactive-mode)
4. [Working with Circuits](#working-with-circuits)
5. [Simulation](#simulation)
6. [Templates](#templates)
7. [Error Mitigation](#error-mitigation)
8. [Resource Estimation](#resource-estimation)
9. [Cost Calculation](#cost-calculation)
10. [Configuration Profiles](#configuration-profiles)
11. [Plugin System](#plugin-system)
12. [Advanced Features](#advanced-features)
13. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installing from PyPI

```bash
pip install quantum-cli-sdk
```

### Installing from Source

```bash
git clone https://github.com/yourusername/quantum-cli-sdk.git
cd quantum-cli-sdk
pip install -e .
```

## Getting Started

The Quantum CLI SDK provides a command-line interface for quantum computing tasks. After installation, you can access it via the `quantum-cli` command:

```bash
# Check the version
quantum-cli --version

# Get help
quantum-cli --help
```

### Basic Command Structure

The CLI follows a structured command format:

```
quantum-cli <command> [subcommand] [options]
```

For example:

```bash
quantum-cli circuit create --qubits 3 --output my_circuit.qasm
```

## Interactive Mode

The interactive mode provides a user-friendly shell environment for working with quantum circuits:

```bash
quantum-cli interactive
```

In interactive mode, you can:

- Create and manipulate quantum circuits
- Add gates
- Run simulations
- Access examples and tutorials
- View and change configuration profiles

### Interactive Mode Commands

Here are some key commands available in interactive mode:

```
help                # List all available commands
circuit create 3    # Create a 3-qubit circuit
gate h 0            # Add a Hadamard gate to qubit 0
gate cx 0 1         # Add a CNOT gate with control qubit 0 and target qubit 1
simulate            # Run a simulation of the current circuit
examples list       # List available example circuits
examples load bell  # Load the Bell state example
tutorial list       # List available tutorials
exit                # Exit interactive mode
```

## Working with Circuits

The `circuit` command allows you to create, manipulate, and save quantum circuits.

### Creating a Circuit

```bash
quantum-cli circuit create --qubits 3 --output my_circuit.qasm
```

This creates a 3-qubit circuit and saves it to `my_circuit.qasm`.

### Running a Circuit

```bash
quantum-cli run --circuit my_circuit.qasm --shots 1024 --output results.json
```

This runs the circuit with 1024 shots and saves the results to `results.json`.

## Simulation

The `simulate` command allows you to simulate quantum circuits using different backends.

```bash
quantum-cli simulate --simulator qiskit --shots 1024 --source my_circuit.qasm --dest results.json
```

Available simulators:
- `qiskit`: IBM Qiskit simulator
- `cirq`: Google Cirq simulator
- `braket`: Amazon Braket simulator
- `all`: Run simulation on all available backends

### Caching Simulation Results

To use the simulation cache:

```bash
quantum-cli simulate --source my_circuit.qasm --use-cache
```

To view cache statistics:

```bash
quantum-cli cache stats
```

To clear the cache:

```bash
quantum-cli cache clear
```

## Templates

The Quantum CLI SDK provides a collection of quantum circuit templates that you can use as starting points for your quantum applications.

### Listing Available Templates

```bash
quantum-cli template list
```

### Getting a Template

```bash
quantum-cli template get bell --dest bell.qasm
```

### Applying a Template with Parameters

```bash
quantum-cli template apply qft --params n=4 --dest qft.qasm
```

## Error Mitigation

The `mitigate` command applies error mitigation techniques to quantum circuits:

```bash
quantum-cli mitigate --technique zne --source noisy_circuit.qasm --dest mitigated.qasm
```

Available techniques:
- `zne`: Zero Noise Extrapolation
- `pec`: Probabilistic Error Cancellation
- `cdr`: Clifford Data Regression
- `dd`: Dynamical Decoupling

## Resource Estimation

The `estimate-resources` command analyzes quantum circuits to estimate required resources:

```bash
quantum-cli estimate-resources --source my_circuit.qasm --dest resource_report.json --detailed
```

## Cost Calculation

The `calculate-cost` command estimates the cost of running a quantum circuit on different platforms:

```bash
quantum-cli calculate-cost --source my_circuit.qasm --platform all --shots 1000
```

## Configuration Profiles

The Quantum CLI SDK uses configuration profiles to manage settings for different environments.

### Listing Profiles

```bash
quantum-cli config list-profiles
```

### Showing a Profile Configuration

```bash
quantum-cli config show-profile --profile dev
```

### Creating a New Profile

```bash
quantum-cli config create-profile prod --base dev
```

### Setting Configuration Values

```bash
quantum-cli config set log_level DEBUG --profile dev
quantum-cli config set-provider ibm token YOUR_TOKEN
```

### Using a Different Profile

```bash
quantum-cli --profile prod simulate --source my_circuit.qasm
```

## Plugin System

The Quantum CLI SDK supports a plugin system that allows you to extend its functionality.

### Adding a Plugin Directory

```bash
quantum-cli config add-plugin-path ~/quantum-plugins
```

### Using a Plugin Command

Once plugins are installed, they'll appear in the help output and can be used like built-in commands:

```bash
quantum-cli bench --source my_circuit.qasm --simulators qiskit,cirq
```

## Advanced Features

### Transpiler Optimization

```bash
quantum-cli optimize --source my_circuit.qasm --dest optimized.qasm --pipeline efficient
```

### Listing Transpiler Passes

```bash
quantum-cli transpiler list-passes
```

### Listing Pipeline Templates

```bash
quantum-cli transpiler list-pipelines
```

### Hardware Execution

```bash
quantum-cli hw-run --platform ibm --device ibmq_santiago --source my_circuit.qasm --shots 1024
```

## Troubleshooting

### Common Issues

1. **Installation Problems**
   ```bash
   pip install --upgrade quantum-cli-sdk
   ```

2. **Config File Issues**
   ```bash
   # Create a new config file
   quantum-cli config create-profile default
   ```

3. **Log Level**
   ```bash
   # Increase log verbosity
   quantum-cli config set log_level DEBUG
   ```

### Getting Help

If you encounter issues not covered in this guide:

1. Check the documentation:
   ```bash
   quantum-cli --help
   quantum-cli <command> --help
   ```

2. Visit the official repository: [https://github.com/yourusername/quantum-cli-sdk](https://github.com/yourusername/quantum-cli-sdk)

3. File an issue: [https://github.com/yourusername/quantum-cli-sdk/issues](https://github.com/yourusername/quantum-cli-sdk/issues) 