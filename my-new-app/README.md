# my-new-app

A quantum application initialized with the Quantum CLI SDK.

## Project Structure

- **.github/workflows**: CI/CD pipeline configurations.
- **dist**: Build distribution artifacts.
- **ir/openqasm**: Intermediate Representation (OpenQASM) files after processing steps.
- **microservice**: Dockerized API wrapper for the quantum application.
- **results**: Output data from simulations, analysis, etc.
- **source/circuits**: Original quantum circuit source code.
- **tests**: Unit and integration tests for the quantum application.
- **.gitignore**: Specifies intentionally untracked files that Git should ignore.
- **README.md**: This file.
- **requirements.txt**: Project dependencies.

## Getting Started

1.  Set up your Python environment.
2.  Install dependencies: `pip install -r requirements.txt`
3.  Develop your circuits in `source/circuits/`.
4.  Use `quantum-cli-sdk` commands to process, test, and deploy.
