"""
Tests for the simulation command.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Assume the CLI entry point is properly configured in setup.py or similar
# If not, we might need to invoke cli.main() directly.
# For now, let's use subprocess or a Click CliRunner approach.
from click.testing import CliRunner

# Assuming your main CLI function is in src/quantum_cli_sdk/cli.py
# Adjust the import path if necessary
from quantum_cli_sdk.cli import main
from quantum_cli_sdk.commands.simulate import SimulationResult

# Fixture for the CliRunner
@pytest.fixture
def runner():
    return CliRunner()

# Fixture to create a dummy QASM file
@pytest.fixture
def bell_qasm_file(tmp_path): 
    qasm_content = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c[2];
    h q[0];
    cx q[0], q[1];
    measure q -> c;
    """
    p = tmp_path / "bell.qasm"
    p.write_text(qasm_content)
    return str(p)

# Test the basic simulation command with Qiskit
def test_simulate_qiskit_success(runner, bell_qasm_file, tmp_path):
    """Test successful simulation using qiskit backend."""
    output_file = tmp_path / "qiskit_results.json"
    args = [
        "run",
        "simulate",
        bell_qasm_file,
        "--backend",
        "qiskit",
        "--output",
        str(output_file),
        "--shots",
        "100" # Use fewer shots for faster tests
    ]
    result = runner.invoke(main, args)
    
    print(f"CLI Output:\n{result.output}")
    print(f"CLI Exception: {result.exception}")
    if result.exception:
        import traceback
        traceback.print_exception(type(result.exception), result.exception, result.exc_info[2])

    assert result.exit_code == 0, f"CLI exited with code {result.exit_code}"
    assert output_file.exists(), "Output JSON file was not created"
    assert "Simulation command completed." in result.output

    # Check content of the output file
    with open(output_file, 'r') as f:
        data = json.load(f)
        assert data["platform"] == "qiskit"
        assert data["shots"] == 100
        assert "counts" in data
        # Check if counts roughly represent a Bell state (00 and 11 should dominate)
        assert isinstance(data["counts"], dict)
        total_counts = sum(data["counts"].values())
        assert total_counts == 100
        # This is probabilistic, so we check if the target states have counts
        assert data["counts"].get("00", 0) > 0 
        assert data["counts"].get("11", 0) > 0

# Test simulation command when QASM file does not exist
def test_simulate_file_not_found(runner, tmp_path):
    """Test simulation with a non-existent QASM file."""
    non_existent_file = tmp_path / "not_a_file.qasm"
    args = [
        "run",
        "simulate",
        str(non_existent_file),
        "--backend",
        "qiskit",
        "--shots",
        "10"
    ]
    result = runner.invoke(main, args)
    
    print(f"CLI Output:\n{result.output}")
    
    assert result.exit_code != 0, "CLI should exit with non-zero code for file not found"
    # Check stderr for the error message (Click sends errors to stderr via echo)
    assert f"Error: Input file not found: {non_existent_file}" in result.output 

# Test simulation command with an unsupported backend
def test_simulate_unsupported_backend(runner, bell_qasm_file):
    """Test simulation with an unsupported backend name."""
    args = [
        "run",
        "simulate",
        bell_qasm_file,
        "--backend",
        "nonexistent_backend",
        "--shots",
        "10"
    ]
    result = runner.invoke(main, args)
    
    print(f"CLI Output:\n{result.output}")
    
    # ArgumentParser/Click should catch the invalid choice
    assert result.exit_code != 0
    assert "Invalid value for '--backend'" in result.output # Click specific error message

# Test simulation when Qiskit is not installed (Mocking ImportError)
@patch('quantum_cli_sdk.commands.simulate.AerSimulator') # Mock the class
@patch('quantum_cli_sdk.commands.simulate.QuantumCircuit') # Mock the class
def test_simulate_qiskit_not_installed(mock_qc, mock_aer, runner, bell_qasm_file):
    """Test simulation behavior when qiskit/aer are not importable."""
    # Configure the mocks to raise ImportError when accessed
    mock_qc.side_effect = ImportError("No module named 'qiskit'")
    mock_aer.side_effect = ImportError("No module named 'qiskit_aer'")

    args = [
        "run",
        "simulate",
        bell_qasm_file,
        "--backend",
        "qiskit",
        "--shots",
        "10"
    ]
    result = runner.invoke(main, args)
    
    print(f"CLI Output:\n{result.output}")
    
    assert result.exit_code != 0
    assert "Error: Missing required library for backend 'qiskit'" in result.output

# Test simulation output directly to stdout (no --output)
def test_simulate_qiskit_stdout(runner, bell_qasm_file):
    """Test simulation outputting results to stdout when --output is not used."""
    args = [
        "run",
        "simulate",
        bell_qasm_file,
        "--backend",
        "qiskit",
        "--shots",
        "50" # Fewer shots
    ]
    result = runner.invoke(main, args)
    
    print(f"CLI Output:\n{result.output}")

    assert result.exit_code == 0
    assert "Simulation Results:" in result.output
    assert "Simulation command completed." in result.output
    
    # Check if counts are printed (basic check for JSON structure)
    assert '"00":' in result.output
    assert '"11":' in result.output 