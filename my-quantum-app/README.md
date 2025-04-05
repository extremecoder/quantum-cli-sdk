# my-quantum-app

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
- **.gitignore**: Specifies intentionally untracked files for Git.
- **README.md**: This file.
- **requirements.txt**: Project dependencies (install using `pip install -r requirements.txt`).

## Getting Started

1.  **Set up Environment**: Ensure you have Python 3.10+ and potentially a virtual environment.
2.  **Install Dependencies**: `pip install -r requirements.txt` (add `quantum-cli-sdk` and your quantum framework like `qiskit` here).
3.  **Develop Circuits**: Place your quantum circuit source files (e.g., `.py`) in `source/circuits/`.
4.  **Run Pipeline**: Use `quantum-cli-sdk` commands or push changes to trigger the `.github/workflows/e2e-pipeline.yml` pipeline.

