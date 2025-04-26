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
- [Detailed Developer Workflow](#detailed-developer-workflow)
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
    # Using default paths (source/circuits/ to ir/openqasm/base/)
    quantum-cli ir generate
    
    # Or with explicit paths
    quantum-cli ir generate --source source/circuits/my_circuit.py --dest ir/openqasm/base/my_circuit.qasm
    
    # Using LLM for generation
    quantum-cli ir generate --use-llm
    ```

3.  **Simulate the circuit using Qiskit backend:**
    ```bash
    quantum-cli run simulate ir/openqasm/base/my_circuit.qasm --backend qiskit --shots 1024 --output results/simulation/base/my_circuit_qiskit.json
    ```

4.  **Simulate the circuit using Cirq backend:**
    ```bash
    quantum-cli run simulate ir/openqasm/base/my_circuit.qasm --backend cirq --shots 1024 --output results/simulation/base/my_circuit_cirq.json
    ```

5.  **Simulate the circuit using Braket backend:**
    ```bash
    quantum-cli run simulate ir/openqasm/base/my_circuit.qasm --backend braket --shots 1000 --output results/simulation/base/my_circuit_braket.json
    ```

6.  **Visualize the circuit:**
    ```bash
    quantum-cli visualize circuit --source ir/openqasm/base/my_circuit.qasm --output results/analysis/circuit_visualization.png
    ```

7.  **Visualize the simulation results:**
    ```bash
    quantum-cli visualize results --source results/simulation/base/my_circuit_qiskit.json --output results/analysis/results_histogram.png
    ```

8.  **Analyze quantum circuit resources:**
    ```bash
    quantum-cli analyze resources ir/openqasm/base/my_circuit.qasm --output results/analysis/resources/my_circuit_resources.json --format text
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
- `--dest`: Destination file path for the generated OpenQASM IR (default: ir/openqasm/base/)
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
- `--input-file`: Path to the input OpenQASM file (required)
- `--output-file`: Path to save the optimized OpenQASM file (required)
- `--level`: Optimization level (0=None, 1=Light, 2=Medium, 3=Heavy) (default: 2)
- `--target-depth`: Target circuit depth (relevant for optimization level 3)
- `--format`: Output format for statistics (choices: 'text', 'json') (default: 'text')

#### `quantum-cli ir mitigate --input-file <qasm_file> --output-file <mitigated_qasm> --technique <technique> [--params <params_json>] [--report]`
Apply error mitigation to a quantum circuit.

**Arguments:**
- `--input-file`: Path to the input OpenQASM file (usually optimized) (required)
- `--output-file`: Path to save the mitigated OpenQASM file (required)
- `--technique`: Error mitigation technique to apply (required)
- `--params`: JSON string with technique-specific parameters (e.g., '{"scale_factors": [1, 2, 3]}')
- `--report`: Generate a JSON report about the mitigation process

#### `quantum-cli ir finetune --input-file <qasm_file> --output-file <json_file> [--hardware <hardware_platform>] [--search <method>] [--shots <n>] [--use-hardware] [--device-id <id>] [--api-token <token>] [--max-circuits <n>] [--poll-timeout <seconds>]`
Fine-tune circuit based on analysis results and hardware constraints.

**Arguments:**
- `--input-file`: Path to the input IR file (usually mitigated) (required)
- `--output-file`: Path to save fine-tuning results (JSON) (required)
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
- `--input-file`: Path to the input mitigated IR file (e.g., .qasm) (required)
- `--output-dir`: Directory to save the generated Python test files (default: tests/generated)
- `--llm-provider`: LLM provider to use for test generation (e.g., 'openai', 'togetherai')
- `--llm-model`: Specific LLM model name (requires --llm-provider)

#### `quantum-cli test run <test_path> [--output <json_file>] [--simulator <simulator>] [--shots <n>]`
Run generated test file(s).

**Arguments:**
- `test_path`: Path to the test file or directory containing tests (required)
- `--output`: Path to save test results summary (JSON) (default: results/tests/unit/test_summary.json)
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

## Detailed Developer Workflow

This section outlines the typical end-to-end workflow for developing, testing, and deploying a quantum application using the Quantum CLI SDK. This process leverages the various commands to transform source code into a verified, optimized, and potentially deployable artifact. The entire pipeline is often automated via the CI/CD workflow defined in `.github/workflows/e2e-pipeline.yml`.

1.  **Initialize Project:**
    -   Start by creating the standard project structure using `quantum-cli init create <app-name>`. This sets up essential directories like `source/`, `ir/`, `tests/`, `results/`, `services/`, and `.github/workflows/`.
    -   `cd <app-name>`

2.  **Develop Circuit:**
    -   Write your quantum circuit logic in Python within the `source/circuits/` directory using supported frameworks (e.g., Qiskit).

3.  **IR Generation & Processing Pipeline:**
    -   **Generate Base IR:** Convert Python code to OpenQASM 2.0:
        `quantum-cli ir generate --source source/circuits/my_circuit.py --dest ir/openqasm/base/my_circuit.qasm`
    -   **Validate IR:** Check the syntax and semantics:
        `quantum-cli ir validate ir/openqasm/base/my_circuit.qasm --output results/validation/my_circuit.json`
    -   **Security Scan:** Analyze the base IR for vulnerabilities:
        `quantum-cli security scan ir/openqasm/base/my_circuit.qasm --output results/security/my_circuit.json`
    -   **(Optional) Simulate Base IR:** Perform an initial check:
        `quantum-cli run simulate ir/openqasm/base/my_circuit.qasm --backend qiskit --output results/simulation/base/my_circuit_qiskit.json`
    -   **Optimize IR:** Improve circuit efficiency:
        `quantum-cli ir optimize --input-file ir/openqasm/base/my_circuit.qasm --output-file ir/openqasm/optimized/my_circuit.qasm`
    -   **Mitigate Errors:** Apply techniques to handle hardware noise (using optimized IR):
        `quantum-cli ir mitigate --input-file ir/openqasm/optimized/my_circuit.qasm --output-file ir/openqasm/mitigated/my_circuit.qasm --technique <method>`
    -   **(Recommended) Simulate Final IR:** Simulate the final processed IR (e.g., mitigated):
        `quantum-cli run simulate ir/openqasm/mitigated/my_circuit.qasm --backend qiskit --output results/simulation/mitigated/my_circuit_qiskit.json`

4.  **Comprehensive Testing:**
    -   **Generate Tests:** Create an extensive suite (>24 types) covering various validation aspects using the *final stage* IR (e.g., mitigated):
        `quantum-cli test generate --input-file ir/openqasm/mitigated/my_circuit.qasm --output-dir tests/generated`
    -   **Run Tests:** Execute the full test suite:
        `quantum-cli test run tests/generated/ --output results/tests/unit/test_summary.json`

5.  **Analysis & Benchmarking:**
    -   **Estimate Resources:** Calculate qubits, gates, depth, etc.:
        `quantum-cli analyze resources ir/openqasm/mitigated/my_circuit.qasm --output results/analysis/resources/my_circuit.json`
    -   **Estimate Cost:** Predict execution cost on platforms:
        `quantum-cli analyze cost ir/openqasm/mitigated/my_circuit.qasm --platform all --output results/analysis/cost/my_circuit.json`
    -   **Benchmark:** Compare performance across backends:
        `quantum-cli analyze benchmark ir/openqasm/mitigated/my_circuit.qasm --output results/analysis/benchmark/my_circuit.json`

6.  **Fine-tuning (Post-Analysis):**
    -   **(Optional) Fine-tune:** Optimize for specific hardware using insights from analysis (using mitigated IR):
        `quantum-cli ir finetune --input-file ir/openqasm/mitigated/my_circuit.qasm --output-file results/analysis/finetuning/my_circuit.json --hardware <target>`

7.  **(Optional) Microservice Generation:**
    -   **Generate Service:** Create a containerized API wrapper:
        `quantum-cli service generate --input-file ir/openqasm/mitigated/my_circuit.qasm --output-dir services/generated/microservice`
    -   **Generate Service Tests:** Create API integration tests (Note: LLM is *not* used here):
        `quantum-cli service test-generate --service-dir services/generated/microservice --output-dir services/generated/microservice/tests/`
    -   **Run Service Tests:** Execute the service tests:
        `quantum-cli service test run services/generated/microservice/tests/ --output results/tests/service/test_summary.json`
    -   **Build Service Image:** Build the Docker container:
        `quantum-cli service build services/generated/microservice --tag my_circuit_api:latest`

8.  **Packaging & Publishing:**
    -   **Package Application:** Bundle artifacts into a zip file:
        `quantum-cli package create . --output dist/<app-name>-<version>.zip`
    -   **Upload Package:** Upload the zip to Quantum Hub staging:
        `quantum-cli hub upload dist/<app-name>-<version>.zip` (Note the upload identifier returned)
    -   **Publish Application:** Publish using the identifier from the upload step:
        `quantum-cli hub publish <upload_identifier> --target registry` (or `--target marketplace`)

9.  **CI/CD Automation:**
    -   The `.github/workflows/e2e-pipeline.yml` file defines the GitHub Actions workflow that automates steps 3 through 8 (or a subset thereof) upon code changes, ensuring consistent execution and validation.

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
│       ├── base/                # Base IR generated from source (ir generate)
│       ├── optimized/           # Optimized IR (ir optimize)
│       └── mitigated/           # Error-mitigated IR (ir mitigate)
│
├── results/                     # Contains output data from various pipeline stages
│   ├── validation/              # Validation results (ir validate)
│   ├── security/                # Security scan reports (security scan)
│   ├── simulation/              # Simulation results (run simulate)
│   │   ├── base/                # Raw simulation results
│   │   ├── optimized/           # Simulation of optimized circuits
│   │   └── mitigated/           # Simulation of error-mitigated circuits
│   │
│   ├── analysis/                # Circuit analysis results
│   │   ├── resources/           # Resource estimation (analyze resources)
│   │   ├── cost/                # Cost estimation (analyze cost)
│   │   ├── benchmark/           # Benchmarking results (analyze benchmark)
│   │   └── finetuning/          # Fine-tuning results (ir finetune)
│   │
│   └── tests/                   # Test execution results summaries
│       ├── unit/                # Unit test summaries (test run)
│       └── service/             # Service test summaries (service test run)
│
├── services/                    # Contains generated microservice code
│   └── generated/               # Base dir for generated services
│       └── microservice/        # The generated microservice directory
│           ├── app/             # Service code (e.g., FastAPI)
│           ├── tests/           # Generated service integration tests (service test-generate)
│           └── Dockerfile       # Container definition
│
├── source/
│   └── circuits/                # Location for your original quantum circuit source files (*.py)
│
├── tests/                       # Contains generated test code for quantum circuits
│   └── generated/               # Generated quantum circuit unit/integration tests (test generate)
│       └── test_*.py            # Individual test files
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
    # Using default paths
    quantum-cli ir generate
    
    # Explicitly specifying paths
    quantum-cli ir generate --source source/circuits/my_circuit.py --dest ir/openqasm/base/my_circuit.qasm
    
    # Using LLM
    quantum-cli ir generate --use-llm
    ```

3.  **Generate IR using an LLM (Together AI example):**
    ```bash
    # Ensure TOGETHER_API_KEY environment variable is set
    quantum-cli ir generate --source source/circuits/my_circuit.py --dest ir/openqasm/base/my_circuit_llm.qasm --llm-provider togetherai --llm-model mistralai/Mixtral-8x7B-Instruct-v0.1
    ```

4.  **Validate the generated IR:**
    ```bash
    quantum-cli ir validate ir/openqasm/base/my_circuit.qasm --output-file results/validation/my_circuit.json
    ```

5.  **Scan the IR for security issues:**
    ```bash
    quantum-cli security scan ir/openqasm/base/my_circuit.qasm --output-file results/security/my_circuit.json
    ```

6.  **Simulate the circuit using Qiskit backend:**
    ```bash
    quantum-cli run simulate ir/openqasm/base/my_circuit.qasm --backend qiskit --shots 2048 --output results/simulation/base/my_circuit_qiskit.json
    ```

7.  **Simulate the circuit using Cirq backend:**
    ```bash
    quantum-cli run simulate ir/openqasm/base/my_circuit.qasm --backend cirq --shots 1024 --output results/simulation/base/my_circuit_cirq.json
    ```

8.  **Simulate the circuit using Braket backend:**
    ```bash
    quantum-cli run simulate ir/openqasm/base/my_circuit.qasm --backend braket --shots 1000 --output results/simulation/base/my_circuit_braket.json
    ```

9.  **Optimize the circuit:**
    ```bash
    quantum-cli ir optimize --input-file ir/openqasm/base/my_circuit.qasm --output-file ir/openqasm/optimized/my_circuit.qasm --level 2
    ```

10.  **Simulate the optimized circuit using Qiskit backend:**
    ```bash
    quantum-cli run simulate ir/openqasm/optimized/my_circuit.qasm --backend qiskit --shots 2048 --output results/simulation/optimized/my_circuit_qiskit.json
    ```

11.  **Simulate the optimized circuit using Cirq backend:**
    ```bash
    quantum-cli run simulate ir/openqasm/optimized/my_circuit.qasm --backend cirq --shots 1024 --output results/simulation/optimized/my_circuit_cirq.json
    ```

12.  **Simulate the optimized circuit using Braket backend:**
    ```bash
    quantum-cli run simulate ir/openqasm/optimized/my_circuit.qasm --backend braket --shots 1000 --output results/simulation/optimized/my_circuit_braket.json
    ```

13. **Mitigate errors:**
    ```bash
    quantum-cli ir mitigate --input-file ir/openqasm/optimized/my_circuit.qasm --output-file ir/openqasm/mitigated/my_circuit.qasm --technique zne
    ```
14.  **Simulate the mitigated circuit using Qiskit backend:**
    ```bash
    quantum-cli run simulate ir/openqasm/mitigated/my_circuit.qasm --backend qiskit --shots 2048 --output results/simulation/mitigated/my_circuit_qiskit.json
    ```

15.  **Simulate the mitigated circuit using Cirq backend:**
    ```bash
    quantum-cli run simulate ir/openqasm/mitigated/my_circuit.qasm --backend cirq --shots 1024 --output results/simulation/mitigated/my_circuit_cirq.json
    ```

16.  **Simulate the mitigated circuit using Braket backend:**
    ```bash
    quantum-cli run simulate ir/openqasm/mitigated/my_circuit.qasm --backend braket --shots 1000 --output results/simulation/mitigated/my_circuit_braket.json

17. **Generate tests for the mitigated quantum circuit:**
    ```bash
    quantum-cli test generate --input-file ir/openqasm/mitigated/my_circuit.qasm --output-dir tests/generated
    ```

18. **Run generated tests:**
    ```bash
    quantum-cli test run tests/generated/ --output results/tests/unit/test_summary.json
    ```

11. **Visualize the mitigated circuit:**
    ```bash
    quantum-cli visualize circuit --source ir/openqasm/mitigated/my_circuit.qasm --output results/analysis/circuit_mitigated_visualization.png
    ```

12. **Visualize the simulation results (using base simulation results):**
    ```bash
    quantum-cli visualize results --source results/simulation/base/my_circuit_qiskit.json --output results/analysis/results_histogram.png
    ```

13. **Analyze quantum circuit resources (using mitigated circuit):**
    ```bash
    quantum-cli analyze resources ir/openqasm/mitigated/my_circuit.qasm --output results/analysis/resources/my_circuit_resources.json --format text
    ```
    This command estimates resource requirements including qubit count, gate counts, circuit depth, T-depth, and runtime estimates across different quantum hardware platforms.

14. **Estimate quantum circuit execution costs (using mitigated circuit):**
    ```bash
    quantum-cli analyze cost ir/openqasm/mitigated/my_circuit.qasm --resource-file results/analysis/resources/my_circuit_resources.json --platform all --shots 1000 --output results/analysis/cost/my_circuit_cost.json
    ```
    This command estimates the execution costs across various quantum hardware platforms (IBM, AWS, Google, IONQ, Rigetti) based on the circuit's structure and required shots.

15. **Benchmark quantum circuit performance (using mitigated circuit):**
    ```bash
    quantum-cli analyze benchmark ir/openqasm/mitigated/my_circuit.qasm --output results/analysis/benchmark/my_circuit_benchmark.json
    ```
    This command benchmarks the circuit's performance, providing metrics on execution time, transpilation quality, and resource efficiency across different quantum platforms.


18. **Fine-tune circuit for hardware-specific optimization (using mitigated circuit):**
    
    Running on simulator
    ```bash
    quantum-cli ir finetune --input-file ir/openqasm/mitigated/my_circuit.qasm --output-file results/analysis/finetune/my_circuit_finetune_results.json --hardware ibm --search random --shots 1024
    ```

    Running on hardware
    ```bash
    quantum-cli ir finetune --input-file ir/openqasm/mitigated/my_circuit.qasm --output-file results/analysis/finetune/my_circuit_finetuned.json --hardware ibm --search random --shots 1024 --use-hardware --device-id ibmq_manila
    ```

    This command fine-tunes a quantum circuit for specific hardware targets, using hyperparameter optimization to find the best transpiler settings, optimization levels, and other hardware-specific parameters.

19. **Generate Microservice (using mitigated circuit):**
    ```bash
    quantum-cli service generate --input-file ir/openqasm/mitigated/my_circuit.qasm --output-dir services/generated/microservice
    ```

20. **Run Microservice Tests:**
    ```bash
    quantum-cli service test run microservice
    ```

21. **Package the Application:**
    ```bash
    quantum-cli package create --source-dir microservice --format zip --config quantum_manifest.json --output-path dist/quantum-app-2.0.0.zip --app-name quantum-app --version 2.0.0 --app-description "Quantum application for my_circuit"
    ```

22. **Upload to Hub:**
    ```bash
    # Assume this outputs an ID like 'upload-xyz-789'
    quantum-cli hub upload dist/my-quantum-app-v1.0.zip
    ```

23. **Publish to Hub Registry:**
    ```bash
    quantum-cli hub publish upload-xyz-789 --target registry
    ```

24. **Publish to Hub Marketplace:**
    ```bash
    quantum-cli hub publish upload-xyz-789 --target marketplace
    ```    

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
