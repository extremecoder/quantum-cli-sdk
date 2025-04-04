# Quantum CLI SDK

A comprehensive command-line interface and software development kit for quantum computing, providing a powerful set of tools for quantum circuit creation, simulation, and analysis.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Overview](#command-overview)
- [Example Usage](#example-usage)
- [Test Suite](#test-suite)
- [Development](#development)
- [License](#license)

## Installation

```bash
pip install quantum-cli-sdk
```

## Quick Start

1.  **Initialize a new quantum project:**
    ```bash
    quantum-cli init my-quantum-app
    cd my-quantum-app
    ```

2.  **Generate IR from a Python circuit (e.g., Qiskit):**
    ```bash
    # Assuming you have a circuit definition in source/circuits/my_circuit.py
    quantum-cli ir generate --source source/circuits/my_circuit.py --dest ir/openqasm/my_circuit.qasm 
    ```

3.  **Simulate the circuit using Qiskit backend:**
    ```bash
    quantum-cli run simulate ir/openqasm/my_circuit.qasm --backend qiskit --shots 1024 --output results/simulation/my_circuit_qiskit.json
    ```

4.  **Simulate the circuit using Cirq backend:**
    ```bash
    quantum-cli run simulate ir/openqasm/my_circuit.qasm --backend cirq --shots 1024 --output results/simulation/base/my_circuit_cirq.json
    ```

5.  **Simulate the circuit using Braket backend:**
    ```bash
    quantum-cli run simulate ir/openqasm/my_circuit.qasm --backend braket --shots 1000 --output results/simulation/base/my_circuit_braket.json
    ```

6.  **Visualize the circuit:**
    ```bash
    quantum-cli visualize circuit ir/openqasm/my_circuit.qasm --output results/visualization/circuit.png
    ```

7.  **Visualize the simulation results:**
    ```bash
    quantum-cli visualize results results/simulation/base/my_circuit_qiskit.json --output results/visualization/results_hist.png
    ```

8.  **Generate and run tests for a quantum circuit:**
    ```bash
    quantum-cli test generate ir/openqasm/my_circuit.qasm --output tests/generated
    quantum-cli test run tests/generated/run_all_tests.py
    ```

## Command Overview

*   `quantum-cli init <project_name>`: Initializes a new quantum project structure.
*   `quantum-cli ir generate --source <py_file> --dest <qasm_file> [--llm-provider <provider>] [--llm-model <model>]`: Generates OpenQASM 2.0 IR from a Python source file, optionally using an LLM.
*   `quantum-cli ir validate <qasm_file> [--output <json_file>]`: Validates the syntax and structure of an OpenQASM 2.0 file.
*   `quantum-cli security scan <qasm_file> [--output <json_file>]`: Scans an OpenQASM 2.0 file for potential security issues.
*   `quantum-cli ir optimize --input-file <qasm_file> --output-file <optimized_qasm> [--level <0-3>]`: Optimize quantum circuit for better performance.
*   `quantum-cli ir mitigate --input-file <qasm_file> --output-file <mitigated_qasm> --technique <technique>`: Apply error mitigation to a quantum circuit.
*   `quantum-cli ir finetune --input-file <qasm_file> --output-file <json_file> [--hardware <ibm|aws|google>] [--search <grid|random>] [--shots <n>]`: Fine-tune a circuit for hardware-specific optimization.
*   `quantum-cli run simulate <qasm_file> --backend <backend_name> [--output <json_file>] [--shots <n>]`: Runs a QASM circuit on a specified simulator backend (`qiskit`, `cirq`, `braket`).
*   `quantum-cli analyze resources <qasm_file> [--output <json_file>] [--format <text|json>]`: Analyzes quantum circuit to estimate resource requirements including qubit count, gate counts, circuit depth, and estimated runtime.
*   `quantum-cli analyze cost <qasm_file> [--resource-file <json_file>] [--output <json_file>] [--platform <all|ibm|aws|google>] [--shots <n>] [--format <text|json>]`: Estimates execution costs for running the quantum circuit on various hardware platforms.
*   `quantum-cli analyze benchmark <qasm_file> [--output <json_file>] [--shots <n>]`: Benchmarks quantum circuit to evaluate performance metrics and compare across platforms.
*   `quantum-cli template list`: Lists available project templates.
*   `quantum-cli template use <template_name> --dest <destination>`: Creates files from a template.
*   `quantum-cli visualize circuit <qasm_file> [--output <image_file>] [--style <style>]`: Visualizes a quantum circuit from a QASM file.
*   `quantum-cli visualize results <json_file> [--output <image_file>]`: Visualizes simulation results from a JSON file.
*   `quantum-cli test generate <qasm_file> --output <dir>`: Generates test suite for quantum circuits.
*   `quantum-cli test run <test_file>`: Runs generated tests for quantum circuits.
*   `quantum-cli version`: Displays the SDK version.
*   `quantum-cli interactive`: Starts an interactive shell session.
*   `quantum-cli config ...`: Manage configuration and profiles.
*   `quantum-cli deps ...`: Analyze Python package dependencies.
*   `quantum-cli marketplace ...`: Commands for interacting with the Quantum Marketplace.
*   `quantum-cli versioning ...`: Commands for version controlling circuits.
*   `quantum-cli share ...`: Commands for sharing circuits and results.
*   `quantum-cli compare ...`: Compare quantum circuits.
*   `quantum-cli find-hardware ...`: Find suitable quantum hardware.
*   `quantum-cli jobs ...`: Manage quantum execution jobs.

*Note: Some commands listed under `marketplace`, `versioning`, `share`, `compare`, `find-hardware`, `jobs` and analysis/optimization/testing commands under `ir`, `run`, `analyze`, `test` are placeholders or under development.*

## Example Usage

1.  **Initialize a new project:**
    ```bash
    quantum-cli init my-quantum-app
    cd my-quantum-app
    ```

2.  **Generate IR from a Python circuit (e.g., Qiskit):**
    ```bash
    quantum-cli ir generate --source source/circuits/my_circuit.py --dest ir/openqasm/my_circuit.qasm 
    ```

3.  **Generate IR using an LLM (Together AI example):**
    ```bash
    # Ensure TOGETHER_API_KEY environment variable is set
    quantum-cli ir generate --source source/circuits/my_circuit.py --dest ir/openqasm/my_circuit_llm.qasm --llm-provider togetherai --llm-model mistralai/Mixtral-8x7B-Instruct-v0.1
    ```

4.  **Validate the generated IR:**
    ```bash
    quantum-cli ir validate ir/openqasm/my_circuit.qasm --output results/validation/my_circuit.json
    ```

5.  **Scan the IR for security issues:**
    ```bash
    quantum-cli security scan ir/openqasm/my_circuit.qasm --output results/security/my_circuit.json
    ```

6.  **Simulate the circuit using Qiskit backend:**
    ```bash
    quantum-cli run simulate ir/openqasm/my_circuit.qasm --backend qiskit --shots 2048 --output results/simulation/base/my_circuit_qiskit.json
    ```

7.  **Simulate the circuit using Cirq backend:**
    ```bash
    quantum-cli run simulate ir/openqasm/my_circuit.qasm --backend cirq --shots 1024 --output results/simulation/base/my_circuit_cirq.json
    ```

8.  **Simulate the circuit using Braket backend:**
    ```bash
    quantum-cli run simulate ir/openqasm/my_circuit.qasm --backend braket --shots 1000 --output results/simulation/base/my_circuit_braket.json
    ```

9.  **Visualize the circuit:**
    ```bash
    quantum-cli visualize circuit ir/openqasm/my_circuit.qasm --output results/visualization/circuit.png
    ```

10. **Visualize the simulation results:**
    ```bash
    quantum-cli visualize results results/simulation/base/my_circuit_qiskit.json --output results/visualization/results_hist.png
    ```

11. **Analyze quantum circuit resources:**
    ```bash
    quantum-cli analyze resources ir/openqasm/my_circuit.qasm --output results/resource_estimation/my_circuit_resources.json --format text
    ```
    This command estimates resource requirements including qubit count, gate counts, circuit depth, T-depth, and runtime estimates across different quantum hardware platforms.

12. **Estimate quantum circuit execution costs:**
    ```bash
    quantum-cli analyze cost ir/openqasm/my_circuit.qasm --platform all --shots 1000 --output results/cost_estimation/my_circuit_cost.json
    ```
    This command estimates the execution costs across various quantum hardware platforms (IBM, AWS, Google, IONQ, Rigetti) based on the circuit's structure and required shots.

13. **Benchmark quantum circuit performance:**
    ```bash
    quantum-cli analyze benchmark ir/openqasm/my_circuit.qasm --shots 1000 --output results/benchmark/my_circuit_benchmark.json
    ```
    This command benchmarks the circuit's performance, providing metrics on execution time, transpilation quality, and resource efficiency across different quantum platforms.

14. **Generate tests for a quantum circuit:**
    ```bash
    quantum-cli test generate ir/openqasm/my_circuit.qasm --output tests/generated
    ```

15. **Run generated tests:**
    ```bash
    cd my-quantum-app
    python tests/generated/run_all_tests.py
    ```

16. **Fine-tune circuit for hardware-specific optimization:**
    ```bash
    quantum-cli ir finetune --input-file ir/openqasm/mitigated/my_circuit_mitigated.qasm --output-file results/analysis/finetuning/my_circuit_finetuned.json --hardware ibm --search random --shots 1024
    ```
    This command fine-tunes a quantum circuit for specific hardware targets, using hyperparameter optimization to find the best transpiler settings, optimization levels, and other hardware-specific parameters. Results include recommended parameters and performance improvement metrics.

## Test Suite

The SDK provides capabilities for generating and running comprehensive test suites for quantum circuits:

### Test Generation

The `quantum-cli test generate` command creates a test suite for an OpenQASM circuit file. The generated tests include:

- **Circuit Structure Validation**: Tests for qubit count, gate set, circuit depth, and measurement operations
- **Circuit Behavior Simulation**: Tests for statevector simulation and measurement distribution
- **Algorithm-Specific Tests**: Tests tailored to the specific quantum algorithm (e.g., Shor's factoring algorithm)
- **Advanced Tests**: Noise simulation, parameterization, quantum correlation analysis

### Test Structure

Generated tests follow a standard structure:
- `test_*_factoring.py`: Basic tests for circuit structure and behavior
- `test_*_advanced.py`: Advanced tests for quantum state analysis and optimization
- `utils.py`: Utility functions for testing
- `run_all_tests.py`: Script to run all tests at once
- `README.md`: Documentation for the test suite

### Qiskit 1.0+ Compatibility

All generated tests are compatible with Qiskit 1.0+, with specific updates to:

1. Use `qiskit_aer` instead of `qiskit.providers.aer`
2. Handle the updated API for quantum circuit operations
3. Support new simulation and visualization methods
4. Properly handle qubit indexing and register manipulation

### Example: Shor's Algorithm Test Suite

The repository includes a complete test suite for Shor's factoring algorithm:

- Tests verify correct period finding for factoring N=15
- Validates quantum correlations in the output
- Checks circuit behavior under noise and perturbations
- Ensures correct circuit structure (gate count, depth, measurements)

For details, see the example in `my-cli-test-app/tests/generated/README.md`.

## Development

To set up the development environment:

```bash
# Clone the repository
git clone https://github.com/quantum-org/quantum-cli-sdk.git
cd quantum-cli-sdk

# Install in development mode with development dependencies
pip install -e ".[dev]"
```

To run tests:

```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Commands

The Quantum CLI SDK supports the following commands:

### IR Commands

The following commands operate on IR files:

- `ir finetune`: Fine-tune a quantum circuit for hardware-specific optimization
  - `--input-file`: Path to the input OpenQASM file
  - `--output-file`: Path to save the fine-tuning results (JSON)
  - `--hardware`: Target hardware platform (ibm, aws, google)
  - `--search-method`: Search method (grid or random)
  - `--shots`: Base number of shots for simulation
  - `--use-hardware`: Enable execution on actual quantum hardware
  - `--device-id`: Specific hardware device ID to use
  - `--api-token`: API token for the quantum platform
  - `--max-circuits`: Maximum number of circuits to run on hardware (default: 5)
  - `--poll-timeout`: Maximum time in seconds to wait for hardware results (default: 3600)

## Fine-tuning

Fine-tuning is a process of optimizing the transpiler and hardware-specific parameters for a given quantum circuit to improve its performance on a specific quantum hardware platform. Unlike training machine learning models, quantum circuit fine-tuning focuses on finding the optimal configuration of the toolchain that converts your high-level circuit to the hardware's native gates and topology.

### How Fine-tuning Works

1. **Parameter space definition**: The system defines ranges for hardware-specific parameters such as:
   - Optimization level (0-3)
   - Layout method (sabre, dense, noise_adaptive, etc.)
   - Routing method (basic, lookahead, stochastic, etc.)
   - Scheduling method (asap, alap)
   - Transpiler seed values

2. **Parameter exploration**: The fine-tuner explores this space using either:
   - Grid search: Systematically trying parameter combinations
   - Random search: Randomly sampling parameter combinations

3. **Execution and evaluation**: For each parameter set, the system:
   - Runs the circuit (either on a simulator or real hardware if `--use-hardware` is specified)
   - Calculates performance metrics (entropy of results, unique outcomes, etc.)
   - Ranks the parameter sets based on performance

4. **Baseline comparison**: The best parameter set is compared against a baseline run with default parameters to quantify the improvement.

5. **Results output**: The system outputs the optimal parameters and their impact on performance.

When using simulators, we can explore more parameter combinations. With real hardware (using the `--use-hardware` flag), the system limits exploration to the number specified in `--max-circuits` to control costs and execution time.

The main difference between simulator-based and hardware-based fine-tuning is that hardware-based fine-tuning provides more accurate results for actual quantum hardware but at higher cost and longer execution times.

### Example Usage

```bash
# Fine-tune using simulator
quantum-cli ir finetune --input-file circuit.qasm --output-file results.json --hardware ibm --search-method random

# Fine-tune using actual hardware
quantum-cli ir finetune --input-file circuit.qasm --output-file results.json --hardware ibm --search-method random --use-hardware --max-circuits 5
```

## Hardware Execution

The CLI supports running quantum circuits on actual quantum hardware from IBM Quantum, Google Quantum, and AWS Braket. To use this feature:

1. Install the appropriate SDK:
   - IBM Quantum: `pip install qiskit qiskit-ibmq-provider`
   - Google Quantum: `pip install cirq cirq-google`
   - AWS Braket: `pip install amazon-braket-sdk`

2. Set up your credentials:
   - IBM Quantum: Configure with `qiskit-ibmq-provider` or provide API token
   - Google Quantum: Set up Google Cloud authentication
   - AWS Braket: Configure AWS credentials through AWS CLI or environment variables

3. Use the `--use-hardware` flag with commands that support hardware execution:
   ```
   quantum-cli ir finetune --input-file circuit.qasm --output-file results.json --hardware ibm --use-hardware --device-id ibmq_manila
   ```

Hardware execution is supported for the following commands:
- `ir finetune`: Run fine-tuning on actual quantum hardware
- `ir run`: Run a circuit on quantum hardware

When using hardware execution, consider the following:
- Running on real hardware may incur costs depending on your provider
- Hardware execution is significantly slower than simulation
- The `--max-circuits` parameter limits the number of circuits to run on hardware
- The `--poll-timeout` parameter sets the maximum time to wait for results

For fine-tuning on hardware, the CLI automatically limits the number of parameter combinations to evaluate based on the `--max-circuits` setting to prevent excessive hardware usage.
