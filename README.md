# Quantum CLI SDK

A comprehensive command-line interface and software development kit for quantum computing, providing a powerful set of tools for quantum circuit creation, simulation, and analysis.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [Core Features](#core-features)
  - [Project Scaffolding](#project-scaffolding)
  - [Interactive Mode](#interactive-mode)
  - [Rich Progress Indicators](#rich-progress-indicators)
  - [Multi-format Output](#multi-format-output)
  - [Logger Configuration](#logger-configuration)
- [Additional Features](#additional-features)
  - [Circuit Manipulation](#circuit-manipulation)
  - [Simulation](#simulation)
  - [Visualization](#visualization)
  - [Versioning](#versioning)
  - [Marketplace](#marketplace)
  - [Sharing](#sharing)
  - [Hardware Selection](#hardware-selection)
  - [Job Management](#job-management)
  - [Configuration Management](#configuration-management)
  - [Dependency Management](#dependency-management)
- [SDK Usage](#sdk-usage)
- [Development](#development)
- [License](#license)

## Installation

```bash
pip install quantum-cli-sdk
```

## Quick Start

### Initialize a new quantum project

```bash
# Create a new quantum project in the directory 'my_quantum_project'
# If no directory name is provided, it initializes in the current directory.
quantum-cli init create my_quantum_project
```

### Create and run a quantum circuit

```bash
# Create a basic quantum circuit
quantum-cli circuit create --qubits 2 --output circuit.json

# Run a quantum simulation
quantum-cli run --circuit circuit.json --shots 1024 --output results.json
```

### Use interactive mode

```bash
# Start the interactive quantum shell
quantum-cli interactive
```

## Command Reference

### Project Initialization

```bash
# Create a new quantum project using the default template
# Initializes in the current directory if <directory_name> is omitted.
quantum-cli init create [<directory_name>] [--overwrite]
```

### Circuit Commands

```bash
# Create a new quantum circuit
quantum-cli circuit create --qubits <NUM_QUBITS> [--output OUTPUT_FILE]

# Run a quantum circuit simulation
quantum-cli run --circuit <CIRCUIT_FILE> [--shots SHOTS] [--output OUTPUT_FILE]

# Generate intermediate representation
quantum-cli generate-ir --source <SOURCE_FILE> [--dest DEST_FILE] [--format {qasm,qiskit,cirq}]
```

### Simulation Commands

```bash
# Simulate a quantum circuit
quantum-cli simulate --source <SOURCE_FILE> [--dest DEST_FILE] [--simulator {qiskit,cirq,braket,all}] [--shots SHOTS] [--use-cache] [--visualize]

# Run on quantum hardware
quantum-cli hw-run --source <SOURCE_FILE> [--dest DEST_FILE] [--platform {ibm,aws,gcp,azure}] [--device DEVICE] [--shots SHOTS] [--credentials CREDENTIALS_FILE]

# Estimate resources for a circuit
quantum-cli estimate-resources --source <SOURCE_FILE> [--dest DEST_FILE] [--detailed] [--target {generic,ibm,aws,gcp,azure}]

# Calculate cost of running a circuit
quantum-cli calculate-cost --source <SOURCE_FILE> [--platform {ibm,aws,gcp,azure,all}] [--shots SHOTS] [--currency CURRENCY] [--output-format {text,json,csv}] [--output-file OUTPUT_FILE]
```

### Template Commands

```bash
# List available templates
quantum-cli template list

# Get a template
quantum-cli template get <TEMPLATE_NAME> [--dest DEST_FILE]
```

### Error Mitigation Commands

```bash
# Apply error mitigation
quantum-cli mitigate --source <SOURCE_FILE> [--dest DEST_FILE] [--technique {zne,pec,cdr,dd}] [--noise-model NOISE_MODEL_FILE]
```

### Visualization Commands

```bash
# Visualize a quantum circuit
quantum-cli visualize circuit --source <SOURCE_FILE> [--output OUTPUT_FILE] [--format {text,latex,mpl,html}]

# Visualize simulation results
quantum-cli visualize results --source <SOURCE_FILE> [--output OUTPUT_FILE] [--type {histogram,statevector,hinton,qsphere}] [--interactive]
```

### Versioning Commands

```bash
# Initialize version control for quantum circuits
quantum-cli version init [--repo-path REPO_PATH]

# Commit a circuit version
quantum-cli version commit --circuit-file <CIRCUIT_FILE> [--message MESSAGE] [--repo-path REPO_PATH]

# Get circuit version details
quantum-cli version get --circuit-name <CIRCUIT_NAME> --version-id <VERSION_ID> [--repo-path REPO_PATH]

# List circuit versions
quantum-cli version list --circuit-name <CIRCUIT_NAME> [--repo-path REPO_PATH]

# Checkout a specific circuit version
quantum-cli version checkout --circuit-name <CIRCUIT_NAME> --version-id <VERSION_ID> [--output-file OUTPUT_FILE] [--repo-path REPO_PATH]
```

### Marketplace Commands

```bash
# Browse available algorithms
quantum-cli marketplace browse [--tag TAG] [--sort-by SORT_BY]

# Search for algorithms
quantum-cli marketplace search <QUERY>

# Get algorithm details
quantum-cli marketplace get <ALGORITHM_ID>

# Download an algorithm
quantum-cli marketplace download <ALGORITHM_ID> [--output-path OUTPUT_PATH]

# Publish an algorithm
quantum-cli marketplace publish --name <NAME> --description <DESCRIPTION> --circuit-file <CIRCUIT_FILE> [--version VERSION] [--tags TAGS] [--price PRICE] [--docs DOCS_FILE]

# Submit a review
quantum-cli marketplace review <ALGORITHM_ID> --rating <RATING> --comment <COMMENT>

# Configure marketplace settings
quantum-cli marketplace configure [--api-key API_KEY] [--profile PROFILE]
```

### Sharing Commands

```bash
# Share a quantum circuit
quantum-cli share --circuit-file <CIRCUIT_FILE> --with <EMAIL> [--permission {view,edit,admin}] [--message MESSAGE]

# List my shared circuits
quantum-cli share list-mine

# List circuits shared with me
quantum-cli share list-shared

# Get shared circuit details
quantum-cli share details <SHARE_ID>

# Update sharing permissions
quantum-cli share update <SHARE_ID> --with <EMAIL> --permission <PERMISSION>

# Remove a collaborator
quantum-cli share remove <SHARE_ID> --collaborator <EMAIL>

# Unshare a circuit
quantum-cli share unshare <SHARE_ID>

# Get activity history
quantum-cli share activity <SHARE_ID>

# Search shared circuits
quantum-cli share search <QUERY>
```

### Comparison Commands

```bash
# Compare two quantum circuits
quantum-cli compare --circuit1 <CIRCUIT1> --circuit2 <CIRCUIT2> [--detailed] [--metrics METRICS] [--visualize]
```

### Hardware Selection Commands

```bash
# Find suitable quantum hardware
quantum-cli find-hardware --circuit <CIRCUIT_FILE> [--criteria {overall,performance,cost,availability}] [--provider PROVIDER] [--min-qubits MIN_QUBITS] [--max-cost MAX_COST] [--output-format {text,json,markdown}]
```

### Job Management Commands

```bash
# List quantum jobs
quantum-cli jobs list [--status {all,pending,running,completed,failed}] [--platform PLATFORM] [--limit LIMIT] [--storage-path STORAGE_PATH]

# Get job details
quantum-cli jobs get <JOB_ID> [--storage-path STORAGE_PATH]

# Cancel a job
quantum-cli jobs cancel <JOB_ID> [--storage-path STORAGE_PATH]

# Monitor job status
quantum-cli jobs monitor <JOB_ID> [--interval INTERVAL] [--storage-path STORAGE_PATH]
```

### Configuration Commands

```bash
# Get configuration value
quantum-cli config get <PATH>

# Set configuration value
quantum-cli config set <PATH> <VALUE>

# Print configuration
quantum-cli config print

# Show default parameters
quantum-cli config defaults [--command COMMAND]

# List configuration profiles
quantum-cli config profile list

# Create a new profile
quantum-cli config profile create <NAME> [--description DESCRIPTION]

# Switch to a profile
quantum-cli config profile switch <NAME>

# Delete a profile
quantum-cli config profile delete <NAME>

# Export configuration
quantum-cli config export <OUTPUT_FILE>

# Import configuration
quantum-cli config import <INPUT_FILE> [--overwrite]
```

### Dependency Commands

```bash
# Check dependencies
quantum-cli deps check [--requirements REQUIREMENTS_FILE]

# Generate dependency report
quantum-cli deps report --output <OUTPUT_FILE> [--format {text,json,markdown}] [--requirements REQUIREMENTS_FILE]

# Get install command for missing packages
quantum-cli deps install-cmd [--requirements REQUIREMENTS_FILE]

# Verify a specific package
quantum-cli deps verify <PACKAGE> [--version VERSION]
```

## Core Features

### Project Scaffolding

The Quantum CLI SDK provides a powerful project scaffolding system that allows you to quickly bootstrap quantum computing projects with best practices and recommended structure.

```bash
# List available project templates
quantum-cli init list

# Create a new quantum project
quantum-cli init create advanced --dir my_quantum_project
```

Available templates:
- **Basic** - A simple quantum computing project with basic circuit creation and simulation
- **Advanced** - A comprehensive project with error mitigation, visualization, and hardware execution
- **Algorithm** - A project focused on implementing and optimizing quantum algorithms

Each template includes:
- Pre-configured directory structure
- Example circuits and algorithms
- Utility functions for common tasks
- Documentation and README files
- Required dependencies

### Interactive Mode

The interactive mode provides a user-friendly command-line shell environment for exploring quantum computing concepts.

```bash
# Start the interactive shell
quantum-cli interactive
```

Features:
- **Rich Terminal Interface** - Color-coded output, formatted tables, and unicode circuit diagrams
- **Command History** - Navigate previous commands with up/down arrows
- **Tab Completion** - Auto-complete commands, options, and arguments
- **Built-in Help** - Detailed help for all commands with usage examples
- **Circuit Building** - Incrementally build circuits gate by gate with immediate visualization
- **Real-time Simulation** - Run simulations and see results without leaving the shell

### Rich Progress Indicators

For long-running operations, the SDK provides detailed progress indicators to keep you informed.

```python
from quantum_cli_sdk.progress import progress_bar, spinner, detailed_progress

# Simple progress bar
with progress_bar(total=100, desc="Processing circuit") as bar:
    for i in range(100):
        # Do work
        bar.update()

# Spinner for indeterminate progress
with spinner(desc="Running simulation") as spnr:
    # Do long-running work
    spnr.update()

# Detailed progress with substeps
with detailed_progress(total=3, desc="Optimizing circuit") as prog:
    prog.set_status("Analyzing circuit structure")
    # Do first step
    prog.update(1)
    
    prog.set_status("Applying optimization passes")
    prog.update_substep("Simplifying gates", 5, 10)
    # Do more work
    prog.update_substep("Simplifying gates", 5, 10)
    prog.update(1)
    
    prog.set_status("Finalizing optimized circuit")
    # Do final step
    prog.update(1)
```

Features:
- **Progress Bars** - Visual indicators of completion percentage
- **Spinners** - Animated indicators for indeterminate progress
- **Detailed Status** - Textual status updates with substep tracking
- **Statistics** - Rate, elapsed time, and estimated time remaining
- **Customizable Appearance** - Different styles and formats

### Multi-format Output

The SDK provides consistent formatting of command output in various formats, making it easier to integrate with other tools and workflows.

```python
from quantum_cli_sdk.output_formatter import format_output, save_output, OutputFormat

# Format data as JSON
json_output = format_output(data, format="json")

# Format data as a table in Markdown
md_output = format_output(data, format="markdown")

# Save output to a file in a format inferred from the extension
save_output(data, "results.yaml")
```

Supported formats:
- **TEXT** - Human-readable text output
- **JSON** - Structured JSON for programmatic processing
- **YAML** - Human-readable structured format
- **CSV** - Tabular data for spreadsheet applications
- **MARKDOWN** - Formatted text for documentation

### Logger Configuration

The SDK includes an enhanced logging system with fine-grained control over logging levels and destinations.

```python
from quantum_cli_sdk.logging_config import configure_logging, get_logger, set_level

# Configure basic logging
configure_logging(console_level="INFO", file_level="DEBUG", log_file="quantum.log")

# Get a module-specific logger
logger = get_logger("circuit")

# Set module-specific log level
set_level("simulator", "DEBUG")

# Add a rotating log file
add_rotating_log_file("detailed.log", level="DEBUG", max_bytes=10*1024*1024, backup_count=5)
```

Features:
- **Multiple Log Destinations** - Console and multiple file outputs
- **Module-specific Log Levels** - Different verbosity for different components
- **Rotating File Logs** - Size-based and time-based log rotation
- **Configurable Formats** - Customizable log message formats
- **Configuration Profiles** - Save and load logging configurations

## Additional Features

### Circuit Manipulation

Create, modify, and analyze quantum circuits using a variety of tools and representations.

```bash
# Create a quantum circuit
quantum-cli circuit create --qubits 3 --output my_circuit.json

# Generate OpenQASM representation
quantum-cli generate-ir --source my_circuit.json --dest my_circuit.qasm --format qasm
```

### Simulation

Simulate quantum circuits using different backend simulators and approaches.

```bash
# Simulate a circuit with 1024 shots
quantum-cli simulate --source my_circuit.json --shots 1024 --simulator qiskit --dest results.json
```

### Visualization

Visualize quantum circuits and simulation results in various formats.

```bash
# Visualize a circuit
quantum-cli visualize circuit --source my_circuit.json --format mpl --output circuit.png

# Visualize simulation results as a histogram
quantum-cli visualize results --source results.json --type histogram --output histogram.png
```

### Versioning

Track changes to quantum circuits with built-in version control.

```bash
# Initialize version control
quantum-cli version init

# Commit a circuit version
quantum-cli version commit --circuit-file my_circuit.json --message "Initial version"
```

### Marketplace

Discover, share, and collaborate on quantum algorithms through the quantum marketplace.

```bash
# Browse available algorithms
quantum-cli marketplace browse --tag optimization

# Download an algorithm
quantum-cli marketplace download algorithm-123 --output-path ./algorithms/
```

### Sharing

Share your quantum circuits with collaborators and manage permissions.

```bash
# Share a circuit with a collaborator
quantum-cli share --circuit-file my_circuit.json --with colleague@example.com --permission edit
```

### Hardware Selection

Find and select appropriate quantum hardware for your circuits.

```bash
# Find suitable quantum hardware for a circuit
quantum-cli find-hardware --circuit my_circuit.json --criteria performance
```

### Job Management

Manage and monitor quantum computing jobs across different platforms.

```bash
# List all jobs
quantum-cli jobs list

# Monitor a specific job
quantum-cli jobs monitor job-456
```

### Configuration Management

Manage configuration settings and profiles for the Quantum CLI SDK.

```bash
# Create a new configuration profile
quantum-cli config profile create azure --description "Azure Quantum settings"

# Set a configuration value
quantum-cli config set default_parameters.simulate.shots 2048
```

### Dependency Management

Analyze and manage dependencies for quantum computing projects.

```bash
# Generate a dependency report
quantum-cli deps report --output deps_report.md --format markdown
```

## SDK Usage

The Quantum CLI SDK can also be used programmatically in Python applications:

```python
from quantum_cli_sdk import QuantumCircuit, run_simulation
from quantum_cli_sdk.visualizer import visualize_circuit
from quantum_cli_sdk.output_formatter import format_output

# Create a Bell state circuit
circuit = QuantumCircuit(2)
circuit.h(0)  # Apply Hadamard gate to qubit 0
circuit.cx(0, 1)  # Apply CNOT gate with control qubit 0 and target qubit 1

# Run simulation
results = run_simulation(circuit, shots=1024)

# Visualize circuit
fig = visualize_circuit(circuit)
fig.savefig("bell_state.png")

# Format results as JSON
json_results = format_output(results, format="json")
print(json_results)
```

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
