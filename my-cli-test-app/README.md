# my-cli-test-app

A quantum application initialized with the Quantum CLI SDK.

This project is structured to work with the standard Quantum CLI SDK E2E pipeline.

## Project Structure

- **.github/workflows**: Contains CI/CD pipeline definitions (e.g., `e2e-pipeline.yml`).
- **dist**: Default output directory for packaged applications (`quantum-cli package create`).
- **ir/openqasm**: Stores Intermediate Representation (OpenQASM) files.
  - `*.qasm`: Base IR generated from source.
  - `optimized/*.qasm`: Optimized IR.
  - `mitigated/*.qasm`: Error-mitigated IR.
- **results**: Contains output data from various pipeline stages.
  - `validation/`: Validation results (`quantum-cli ir validate`).
  - `security/`: Security scan reports (`quantum-cli security scan`).
  - `simulation/`: Simulation results (`quantum-cli run simulate`).
    - `base/{platform}/*.json`
    - `optimized/{platform}/*.json`
    - `mitigated/{platform}/*.json`
  - `analysis/`: Circuit analysis results.
    - `resources/*.json`: Resource estimation (`quantum-cli analyze resources`).
    - `cost/*.json`: Cost estimation (`quantum-cli analyze cost`).
    - `benchmark/*.json`: Benchmarking results (`quantum-cli analyze benchmark`).
    - `finetuning/*.json`: Fine-tuning results (`quantum-cli ir finetune`).
  - `tests/`: Test execution results.
    - `unit/*.json`: Unit test results (`quantum-cli test run`).
    - `service/*.json`: Service test results (`quantum-cli service test-run`).
- **services**: Contains generated microservice code and tests.
  - `generated/{circuit_name}`: Generated service source code (`quantum-cli service generate`).
  - `generated/{circuit_name}/tests/`: Generated service tests (`quantum-cli service test-generate`).
- **source/circuits**: Location for your original quantum circuit source files (e.g., Python scripts).
- **tests**: Contains generated test code.
  - `generated/*.py`: Generated unit tests (`quantum-cli test generate`).
  - `generated/README.md`: Documentation for the test suite.
  - `generated/run_all_tests.py`: Script to run all tests.
  - `generated/utils.py`: Utility functions for tests.
- **.gitignore**: Specifies intentionally untracked files for Git.
- **README.md**: This file.
- **requirements.txt**: Project dependencies (install using `pip install -r requirements.txt`).

## Getting Started

1.  **Set up Environment**: Ensure you have Python 3.10+ and potentially a virtual environment.
2.  **Install Dependencies**: `pip install -r requirements.txt` (add `quantum-cli-sdk` and your quantum framework like `qiskit` here).
3.  **Develop Circuits**: Place your quantum circuit source files (e.g., `.py`) in `source/circuits/`.
4.  **Run Pipeline**: Use `quantum-cli-sdk` commands or push changes to trigger the `.github/workflows/e2e-pipeline.yml` pipeline.

## Test Suite

This project includes a comprehensive test suite for the Shor's algorithm quantum circuit implementation:

- **Location**: All tests are in the `tests/generated/` directory
- **Framework**: Tests use `pytest` and `qiskit-aer` for quantum simulation
- **Compatibility**: The test suite is compatible with Qiskit 1.0+

### Test Files

- `test_shors_factoring.py`: Basic tests for circuit structure and behavior
- `test_shors_advanced.py`: Advanced tests for quantum state analysis and optimization
- `utils.py`: Utility functions for testing
- `run_all_tests.py`: Script to run all tests at once

### Running Tests

Run all tests with:

```bash
cd my-cli-test-app
python tests/generated/run_all_tests.py
```

Or run specific test files:

```bash
pytest tests/generated/test_shors_factoring.py -v
```

For more details on the test suite, see the [tests README](tests/generated/README.md).

## Benchmark Results

This project includes benchmark results for the Shor's factoring algorithm implementation:

- **Location**: Benchmark results are stored in the `results/benchmark/` directory
- **Files**: 
  - `shors_factoring_15_compatible_benchmark.json`: Overall benchmark report
  - `shors_factoring_15_compatible_benchmark_direct.json`: Raw circuit performance metrics
  - `shors_factoring_15_compatible_cost_estimation.json`: Cost estimation across multiple platforms

### Key Metrics

The Shor's factoring circuit (N=15) demonstrates:
- **Circuit Depth**: 13 layers of operations
- **Qubits**: 8 qubits total (4 period + 4 target)
- **Gates**: 27 total gates, including 14 two-qubit gates
- **Execution Time**: ~0.57 seconds for 1000 shots on simulator

### Running Benchmarks

You can run benchmarks with:

```bash
quantum-cli analyze benchmark ir/openqasm/shors_factoring_15_compatible.qasm --shots 1000 --output results/benchmark/shors_factoring_15_compatible_benchmark.json
```

The benchmarking results provide insights into circuit optimization potential, execution efficiency, and cross-platform performance.

## Fine-tuning Results

This project includes fine-tuning results for the Shor's factoring algorithm implementation, optimized for IBM hardware:

- **Location**: Fine-tuning results are stored in the `results/analysis/finetuning/` directory
- **Files**: 
  - `shors_factoring_15_finetuned.json`: Hardware-specific optimization parameters and results

### Hardware-Specific Parameters

The fine-tuning process found the following optimal parameters for IBM hardware:
- **Optimization Level**: 3 (maximum)
- **Layout Method**: sabre (best for complex circuits)
- **Routing Method**: lookahead (minimizes SWAP gates)
- **Scheduling**: asap (as soon as possible execution)
- **Transpiler Seed**: 42 (optimal random seed for deterministic results)

The optimized parameters achieved a **95.24%** performance improvement over the baseline configuration.

### Running Fine-tuning

You can run fine-tuning with:

```bash
quantum-cli ir finetune --input-file ir/openqasm/shors_factoring_15_compatible.qasm --output-file results/analysis/finetuning/shors_factoring_15_finetuned.json --hardware ibm --search random --shots 1024
```

The fine-tuning process uses hyperparameter optimization to identify the best hardware-specific settings for your quantum circuit, maximizing its performance on the target hardware.

