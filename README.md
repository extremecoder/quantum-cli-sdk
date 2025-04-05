# Quantum CLI SDK

A comprehensive command-line interface and software development kit for quantum computing, providing a powerful set of tools for quantum circuit creation, simulation, and analysis.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
  - [Project Initialization](#project-initialization)
  - [IR Generation and Management](#ir-generation-and-management)
  - [Circuit Simulation](#circuit-simulation)
  - [Circuit Analysis](#circuit-analysis)
  - [Testing](#testing)
  - [Visualization](#visualization)
  - [Configuration and Utilities](#configuration-and-utilities)
- [Project Structure](#project-structure)
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
    quantum-cli init create my-quantum-app
    cd my-quantum-app
    ```

2.  **Generate IR from a Python circuit (e.g., Qiskit):**
    ```bash
    # Using default paths (source/circuits/ to ir/base/)
    quantum-cli ir generate
    
    # Or with explicit paths
    quantum-cli ir generate --source source/circuits/my_circuit.py --dest ir/openqasm/my_circuit.qasm
    
    # Using LLM for generation
    quantum-cli ir generate --use-llm
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
    quantum-cli visualize circuit --source ir/openqasm/my_circuit.qasm --output results/visualization/circuit.png
    ```

7.  **Visualize the simulation results:**
    ```bash
    quantum-cli visualize results --source results/simulation/base/my_circuit_qiskit.json --output results/visualization/results_hist.png
    ```

8.  **Analyze quantum circuit resources:**
    ```bash
    quantum-cli analyze resources ir/openqasm/my_circuit.qasm --output results/resource_estimation/my_circuit_resources.json --format text
    ```

## Command Reference

### Project Initialization

#### `quantum-cli init list`
List available project templates.

**Output:**
- Displays all available project templates (currently only "quantum_app")

#### `quantum-cli init create [directory] [--overwrite]`
Create a new quantum project in the specified directory.

**Arguments:**
- `directory`: Directory name for the new project (default: current directory)
- `--overwrite`: Overwrite existing files if the directory is not empty

### IR Generation and Management

#### `quantum-cli ir generate [--source <py_file>] [--dest <qasm_file>] [--use-llm] [--llm-provider <provider>] [--llm-model <model>]`
Generates OpenQASM 2.0 IR from a Python source file.

**Arguments:**
- `--source`: Source Python file path containing circuit definition (default: source/circuits)
- `--dest`: Destination file path for the generated OpenQASM IR (default: ir/base)
- `--use-llm`: Use LLM for IR generation
- `--llm-provider`: LLM provider to use for generation (default: 'togetherai')
- `--llm-model`: Specific LLM model name to use (default: 'mistralai/Mixtral-8x7B-Instruct-v0.1')

#### `quantum-cli ir validate <input_file> [--output <json_file>] [--llm-url <url>]`
Validates the syntax and structure of an OpenQASM 2.0 file.

**Arguments:**
- `input_file`: Path to the IR file to validate (e.g., .qasm) (required)
- `--output`: Optional output file for validation results (JSON)
- `--llm-url`: Optional URL to LLM service for enhanced validation

#### `quantum-cli ir optimize --input-file <qasm_file> --output-file <optimized_qasm> [--level <0-3>] [--target-depth <depth>] [--format <format>]`
Optimize quantum circuit for better performance.

**Arguments:**
- `--input-file`, `-i`: Path to the input OpenQASM file (required)
- `--output-file`, `-o`: Path to save the optimized OpenQASM file
- `--level`, `-l`: Optimization level (0=None, 1=Light, 2=Medium, 3=Heavy) (default: 2)
- `--target-depth`, `-d`: Target circuit depth (relevant for optimization level 3)
- `--format`: Output format for statistics (choices: 'text', 'json') (default: 'text')

#### `quantum-cli ir mitigate --input-file <qasm_file> --output-file <mitigated_qasm> --technique <technique> [--params <params>] [--report]`
Apply error mitigation to a quantum circuit.

**Arguments:**
- `--input-file`, `-i`: Path to the input OpenQASM file (usually optimized) (required)
- `--output-file`, `-o`: Path to save the mitigated OpenQASM file (required)
- `--technique`, `-t`: Error mitigation technique to apply (required)
- `--params`, `-p`: JSON string with technique-specific parameters (e.g., '{"scale_factors": [1, 2, 3]}')
- `--report`: Generate a JSON report about the mitigation process

#### `quantum-cli ir finetune --input-file <qasm_file> --output-file <json_file> [--hardware <platform>] [--search <method>] [--shots <n>] [--use-hardware] [--device-id <id>] [--api-token <token>] [--max-circuits <n>] [--poll-timeout <seconds>]`
Fine-tune circuit based on analysis results and hardware constraints.

**Arguments:**
- `--input-file`, `-i`: Path to the input IR file (usually mitigated) (required)
- `--output-file`, `-o`: Path to save fine-tuning results (JSON) (required)
- `--hardware`: Target hardware platform for fine-tuning (choices: "ibm", "aws", "google") (default: "ibm")
- `--search`: Search method for hyperparameter optimization (choices: "grid", "random") (default: "random")
- `--shots`: Number of shots for simulation during fine-tuning (default: 1000)
- `--use-hardware`: Execute circuits on actual quantum hardware instead of simulators
- `--device-id`: Specific hardware device ID to use (e.g., 'ibmq_manila' for IBM)
- `--api-token`: API token for the quantum platform (if not using configured credentials)
- `--max-circuits`: Maximum number of circuits to run on hardware (to control costs) (default: 5)
- `--poll-timeout`: Maximum time in seconds to wait for hardware results (default: 3600)

### Circuit Simulation

#### `quantum-cli run simulate <qasm_file> --backend <backend> [--output <json_file>] [--shots <n>]`
Runs a QASM circuit on a specified simulator backend.

**Arguments:**
- `qasm_file`: Path to the OpenQASM file to simulate (required)
- `--backend`: Simulation backend to use (choices: 'qiskit', 'cirq', 'braket') (required)
- `--output`: Optional output file for simulation results (JSON)
- `--shots`: Number of simulation shots (default: 1024)

### Circuit Analysis

#### `quantum-cli analyze resources <ir_file> [--output <json_file>] [--format <format>]`
Estimates resource requirements for a quantum circuit.

**Arguments:**
- `ir_file`: Path to the input IR file (OpenQASM) (required)
- `--output`: Path to save resource estimation results (JSON)
- `--format`: Output format (choices: "text", "json") (default: "text")

#### `quantum-cli analyze cost <ir_file> [--resource-file <json_file>] [--output <json_file>] [--platform <platform>] [--shots <n>] [--format <format>]`
Estimate execution cost on different platforms.

**Arguments:**
- `ir_file`: Path to the input IR file (required)
- `--resource-file`: Path to resource estimation file (optional input)
- `--output`: Path to save cost estimation results (JSON)
- `--platform`: Target platform for cost estimation (choices: "all", "ibm", "aws", "google") (default: "all")
- `--shots`: Number of shots for execution (default: 1000)
- `--format`: Output format (choices: "text", "json") (default: "text")

#### `quantum-cli analyze benchmark <ir_file> --output <json_file> [--shots <n>]`
Benchmark circuit performance.

**Arguments:**
- `ir_file`: Path to the input IR file (required)
- `--output`: Path to save benchmark results (JSON) (required)
- `--shots`: Number of shots for simulation (default: 1000)

### Security Analysis

#### `quantum-cli security scan <ir_file> [--output <json_file>]`
Scans an IR file for potential security issues.

**Arguments:**
- `ir_file`: Path to the IR file to scan (e.g., OpenQASM) (required)
- `--output`: Optional output file for scan results (JSON)

### Testing

#### `quantum-cli test generate --input-file <ir_file> [--output-dir <dir>] [--llm-provider <provider>] [--llm-model <model>]`
Generate test code from an IR file using LLM.

**Arguments:**
- `--input-file`, `-i`: Path to the input mitigated IR file (e.g., .qasm) (required)
- `--output-dir`, `-o`: Directory to save the generated Python test files (default: tests/generated)
- `--llm-provider`: LLM provider to use for test generation (e.g., 'openai', 'togetherai')
- `--llm-model`: Specific LLM model name (requires --llm-provider)

#### `quantum-cli test run <test_file> [--output <json_file>] [--simulator <simulator>] [--shots <n>]`
Run generated test file(s).

**Arguments:**
- `test_file`: Path to the test file or directory containing tests (required)
- `--output`: Path to save test results (JSON)
- `--simulator`: Simulator to use for running tests (choices: "qiskit", "cirq", "braket", "all") (default: "qiskit")
- `--shots`: Number of shots for simulation (applicable if test_file is a circuit file) (default: 1024)

### Visualization

#### `quantum-cli visualize circuit --source <circuit_file> [--output <image_file>] [--format <format>]`
Visualize a quantum circuit.

**Arguments:**
- `--source`: Path to the circuit file (QASM or other supported format) (required)
- `--output`: Output file path (e.g., .png, .txt, .html)
- `--format`: Output format (choices: "text", "mpl", "latex", "html") (default: "mpl")

#### `quantum-cli visualize results --source <results_file> [--output <image_file>] [--type <type>] [--interactive]`
Visualize simulation or hardware results.

**Arguments:**
- `--source`: Path to the results file (JSON) (required)
- `--output`: Output file path (e.g., .png)
- `--type`: Type of plot (choices: "histogram", "statevector", "hinton", "qsphere") (default: "histogram")
- `--interactive`: Show interactive plot

### Configuration and Utilities

#### `quantum-cli config get <path>`
Get configuration value.

**Arguments:**
- `path`: Configuration path (e.g., 'default_parameters.run.shots') (required)

#### `quantum-cli config set <path> <value>`
Set configuration value.

**Arguments:**
- `path`: Configuration path (e.g., 'default_parameters.run.shots') (required)
- `value`: Configuration value (required)

#### `quantum-cli interactive`
Starts an interactive shell session for running quantum commands.

## Project Structure

When you initialize a new project using `quantum-cli init create <project_name>`, the following directory structure is created:

```
my-quantum-app/                  # Your project root directory
├── .github/
│   └── workflows/               # CI/CD pipeline definitions
│       └── e2e-pipeline.yml     # End-to-end quantum pipeline workflow
│
├── dist/                        # Default output directory for packaged applications
│
├── ir/
│   └── openqasm/                # Stores Intermediate Representation (OpenQASM) files
│       ├── *.qasm               # Base IR generated from source
│       ├── optimized/           # Optimized IR
│       └── mitigated/           # Error-mitigated IR
│
├── results/                     # Contains output data from various pipeline stages
│   ├── validation/              # Validation results (quantum-cli ir validate)
│   ├── security/                # Security scan reports (quantum-cli security scan)
│   ├── simulation/              # Simulation results (quantum-cli run simulate)
│   │   ├── base/                # Raw simulation results
│   │   ├── optimized/           # Simulation of optimized circuits
│   │   └── mitigated/           # Simulation of error-mitigated circuits
│   │
│   ├── analysis/                # Circuit analysis results
│   │   ├── resources/           # Resource estimation (quantum-cli analyze resources)
│   │   ├── cost/                # Cost estimation (quantum-cli analyze cost)
│   │   ├── benchmark/           # Benchmarking results (quantum-cli analyze benchmark)
│   │   └── finetuning/          # Fine-tuning results (quantum-cli ir finetune)
│   │
│   └── tests/                   # Test execution results
│       ├── unit/                # Unit test results (quantum-cli test run)
│       └── service/             # Service test results
│
├── services/                    # Contains generated microservice code and tests
│   └── generated/               # Base dir for generated services
│
├── source/
│   └── circuits/                # Location for your original quantum circuit source files
│
├── tests/
│   └── generated/               # Contains generated test code
│
├── .gitignore                   # Standard gitignore file for Python/quantum projects
├── README.md                    # Project description and documentation
└── requirements.txt             # Project dependencies
```

This structure is designed to work seamlessly with the Quantum CLI SDK commands and provides a standard layout for organizing your quantum computing projects.

## Example Usage

1.  **Initialize a new project:**
    ```bash
    quantum-cli init create my-quantum-app
    cd my-quantum-app
    ```

2.  **Generate IR from a Python circuit (e.g., Qiskit):**
    ```bash
    quantum-cli ir generate
    
    quantum-cli ir generate --source source/circuits/my_circuit.py --dest ir/openqasm/my_circuit.qasm
    
    quantum-cli ir generate --use-llm
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
    quantum-cli visualize circuit --source ir/openqasm/my_circuit.qasm --output results/visualization/circuit.png
    ```

10. **Visualize the simulation results:**
    ```bash
    quantum-cli visualize results --source results/simulation/base/my_circuit_qiskit.json --output results/visualization/results_hist.png
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
    quantum-cli test generate --input-file ir/openqasm/my_circuit.qasm --output-dir tests/generated
    ```

15. **Run generated tests:**
    ```bash
    quantum-cli test run tests/generated/run_all_tests.py
    ```

16. **Fine-tune circuit for hardware-specific optimization:**
    ```bash
    quantum-cli ir finetune --input-file ir/openqasm/mitigated/my_circuit_mitigated.qasm --output-file results/analysis/finetuning/my_circuit_finetuned.json --hardware ibm --search random --shots 1024
    ```
    This command fine-tunes a quantum circuit for specific hardware targets, using hyperparameter optimization to find the best transpiler settings, optimization levels, and other hardware-specific parameters.

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
