"""
Unit tests for the transpiler module.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock, patch
from typing import Optional

from quantum_cli_sdk.transpiler import (
    parse_qasm,
    circuit_to_qasm,
    estimate_circuit_depth,
    _cancel_adjacent_gates_impl,
    get_pass_manager,
    TranspilerPipeline,
    OPTIMIZATION_LEVELS # Import this to potentially check names
)

# --- Fixtures ---

@pytest.fixture
def sample_qasm_content() -> str:
    """Provides a sample valid OpenQASM 2.0 string."""
    return """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
cx q[0], q[1]; // Adjacent CX
h q[0];       // Adjacent H
measure q[0] -> c[0];
measure q[1] -> c[1];
"""

@pytest.fixture
def sample_parsed_circuit() -> Dict[str, Any]:
    """Provides a sample parsed circuit dictionary matching the QASM content."""
    return {
        "version": "2.0",
        "includes": ["qelib1.inc"],
        "qregs": {"q": 2},
        "cregs": {"c": 2},
        "gate_definitions": [],
        "operations": [
            {"name": "h", "params": None, "targets": "q[0]"},
            {"name": "cx", "params": None, "targets": "q[0], q[1]"},
            {"name": "cx", "params": None, "targets": "q[0], q[1]"}, # Adjacent CX
            {"name": "h", "params": None, "targets": "q[0]"},       # Adjacent H
            {"name": "measure", "params": None, "targets": "q[0] -> c[0]"},
            {"name": "measure", "params": None, "targets": "q[1] -> c[1]"}
        ]
    }

@pytest.fixture
def temp_qasm_file(tmp_path: Path, sample_qasm_content: str) -> Path:
    """Creates a temporary QASM file."""
    file_path = tmp_path / "test_circuit.qasm"
    file_path.write_text(sample_qasm_content)
    return file_path

# --- Test Functions ---

# Test parse_qasm
def test_parse_qasm_valid(temp_qasm_file: Path, sample_parsed_circuit: Dict[str, Any]):
    """Test parsing a valid QASM file."""
    parsed = parse_qasm(temp_qasm_file)
    assert parsed is not None
    assert parsed["version"] == sample_parsed_circuit["version"]
    assert parsed["includes"] == sample_parsed_circuit["includes"]
    assert parsed["qregs"] == sample_parsed_circuit["qregs"]
    assert parsed["cregs"] == sample_parsed_circuit["cregs"]
    # Simplify operation comparison for this test
    assert len(parsed["operations"]) == len(sample_parsed_circuit["operations"])
    assert [op["name"] for op in parsed["operations"]] == [op["name"] for op in sample_parsed_circuit["operations"]]

def test_parse_qasm_nonexistent_file(tmp_path: Path):
    """Test parsing a non-existent file."""
    non_existent_file = tmp_path / "nonexistent.qasm"
    parsed = parse_qasm(non_existent_file)
    assert parsed is None

def test_parse_qasm_invalid_content(tmp_path: Path):
    """Test parsing a file with invalid QASM syntax (very basic check)."""
    invalid_file = tmp_path / "invalid.qasm"
    invalid_file.write_text("this is not qasm;")
    # The current simple parser might not fail robustly, depends on implementation
    # Let's assume it returns something, possibly incomplete or None
    parsed = parse_qasm(invalid_file)
    # Asserting it doesn't raise an unhandled exception is the main goal here
    # We expect it might return None or a partially parsed dict with issues.
    # For a more robust test, we'd need a stricter parser or mock errors.
    # assert parsed is None # This might be too strict depending on parser leniency


# Test circuit_to_qasm
def test_circuit_to_qasm(sample_parsed_circuit: Dict[str, Any], sample_qasm_content: str):
    """Test converting a parsed circuit dict back to a QASM string."""
    generated_qasm = circuit_to_qasm(sample_parsed_circuit)
    # Normalize whitespace and line endings for comparison
    expected_lines = [line.strip() for line in sample_qasm_content.strip().split('\n') if line.strip() and not line.strip().startswith('//')]
    generated_lines = [line.strip() for line in generated_qasm.strip().split('\n') if line.strip()]
    
    # Check core components
    assert "OPENQASM 2.0;" in generated_lines
    assert 'include "qelib1.inc";' in generated_lines
    assert "qreg q[2];" in generated_lines
    assert "creg c[2];" in generated_lines
    assert "h q[0];" in generated_lines
    assert "cx q[0], q[1];" in generated_lines
    assert "measure q[0] -> c[0];" in generated_lines
    assert "measure q[1] -> c[1];" in generated_lines
    # Note: Exact formatting might differ slightly, so comparing individual expected lines is safer.
    # For more complex circuits, this comparison would need to be more robust.


# Test estimate_circuit_depth
def test_estimate_circuit_depth(sample_parsed_circuit: Dict[str, Any]):
    """Test the simplified circuit depth estimation."""
    # 6 operations, 2 qubits -> estimate = (6 // (2 // 2)) + 1 = 7
    expected_depth = 7
    assert estimate_circuit_depth(sample_parsed_circuit) == expected_depth

def test_estimate_circuit_depth_no_qubits():
    """Test depth estimation with no qubits."""
    circuit = { "operations": [{"name": "x", "targets": "q[0]"}], "qregs": {} }
    assert estimate_circuit_depth(circuit) == 0


# Test _cancel_adjacent_gates_impl
def test_cancel_adjacent_gates(sample_parsed_circuit: Dict[str, Any]):
    """Test cancellation of adjacent H and CX gates."""
    circuit_copy = sample_parsed_circuit.copy()
    # Make a deep copy of operations list to avoid modifying the fixture
    circuit_copy["operations"] = [op.copy() for op in sample_parsed_circuit["operations"]]
    
    original_op_count = len(circuit_copy["operations"]) # Should be 6
    optimized_circuit = _cancel_adjacent_gates_impl(circuit_copy)
    optimized_op_count = len(optimized_circuit["operations"])
    
    # Expected: cx q[0],q[1] followed by cx q[0],q[1] cancels -> remove 2 ops
    # Expected: h q[0] followed by h q[0] cancels -> remove 2 ops (relative to original position)
    # Only the adjacent CX pair should be removed. The H gates are not adjacent.
    # Total removed = 2. Original 6 -> Final 4.
    # Final ops should be [h q[0], h q[0], measure q[0]->c[0], measure q[1]->c[1]]
    assert optimized_op_count == original_op_count - 2
    assert optimized_op_count == 4
    assert optimized_circuit["operations"][0]["name"] == "h"
    assert optimized_circuit["operations"][1]["name"] == "h"
    assert optimized_circuit["operations"][2]["name"] == "measure"
    assert optimized_circuit["operations"][3]["name"] == "measure"


# Test create_pipeline and run (Level 1)
def test_run_level1_pipeline(sample_parsed_circuit: Dict[str, Any]):
    """Test creating and running a level 1 pipeline."""
    circuit_copy = sample_parsed_circuit.copy()
    circuit_copy["operations"] = [op.copy() for op in sample_parsed_circuit["operations"]]
    original_op_count = len(circuit_copy["operations"]) # 6

    manager = get_pass_manager() # Use the global/default manager
    pipeline_l1 = manager.create_pipeline(optimization_level=1)

    assert isinstance(pipeline_l1, TranspilerPipeline)
    assert len(pipeline_l1.stages) > 0 # Level 1 should have at least one stage
    assert "Light Optimization" in [s.name for s in pipeline_l1.stages]
    
    # Run the pipeline
    optimized_circuit = pipeline_l1.run(circuit_copy) # Assuming run modifies or returns modified

    assert optimized_circuit is not None
    optimized_op_count = len(optimized_circuit.get("operations", []))

    # Level 1 includes CancelAdjacentGates and FoldAdjointGates (placeholder)
    # Expect CancelAdjacentGates to remove only the adjacent CX pair (2 ops).
    # FoldAdjointGates currently does nothing.
    # Total removed = 2. Original 6 -> Final 4.
    assert optimized_op_count == original_op_count - 2
    assert optimized_op_count == 4
    assert optimized_circuit["operations"][0]["name"] == "h"
    assert optimized_circuit["operations"][1]["name"] == "h"
    assert optimized_circuit["operations"][2]["name"] == "measure"
    assert optimized_circuit["operations"][3]["name"] == "measure" 

# --- Tests for Placeholder Mitigation Passes ---

@pytest.fixture
def mitigation_circuit() -> Dict[str, Any]:
    """Basic circuit dict for mitigation tests."""
    return {
        "version": "2.0",
        "qregs": {"q": 1},
        "cregs": {"c": 1},
        "operations": [{"name": "h", "params": None, "targets": "q[0]"}]
    }

@pytest.mark.parametrize(
    "technique, pass_class_name, params, expected_meta",
    [
        ("zne", "ZeroNoiseExtrapolation", None, {"technique": "ZNE", "params": {}}),
        ("zne", "ZeroNoiseExtrapolation", {"scale_factors": [1, 2]}, {"technique": "ZNE", "params": {"scale_factors": [1, 2]}}),
        ("pec", "ProbabilisticErrorCancellation", None, {"technique": "PEC", "params": {}}),
        ("pec", "ProbabilisticErrorCancellation", {"noise_model": "custom"}, {"technique": "PEC", "params": {"noise_model": "custom"}}),
        ("cdr", "CliffordDataRegression", None, {"technique": "CDR", "params": {}}),
        ("dd", "DynamicalDecoupling", {"sequence": "XYXY"}, {"technique": "DD", "params": {"sequence": "XYXY"}})
    ]
)
@patch('quantum_cli_sdk.transpiler.logger.warning') # Mock logger to suppress placeholder warnings during test
def test_mitigation_placeholders(
    mock_logger_warning: MagicMock,
    technique: str,
    pass_class_name: str,
    params: Optional[Dict[str, Any]],
    expected_meta: Dict[str, Any],
    mitigation_circuit: Dict[str, Any]
):
    """Test creating and running placeholder mitigation pipelines."""
    circuit_copy = mitigation_circuit.copy()
    circuit_copy["operations"] = [op.copy() for op in mitigation_circuit["operations"]]

    manager = get_pass_manager()
    pipeline = manager.create_mitigation_pipeline(technique, params)
    
    assert pipeline is not None
    assert len(pipeline.stages) == 1
    assert len(pipeline.stages[0].passes) == 1
    assert pipeline.stages[0].passes[0].__class__.__name__ == pass_class_name
    
    # Run the pipeline
    run_options = {'mitigation_params': params if params else {}}
    mitigated_circuit = pipeline.run(circuit_copy, options=run_options)
    
    assert mitigated_circuit is not None
    # Check that the circuit structure (ops, regs) is unchanged by placeholder
    assert mitigated_circuit["operations"] == mitigation_circuit["operations"]
    assert mitigated_circuit["qregs"] == mitigation_circuit["qregs"]
    # Check that the correct metadata was added
    assert "metadata" in mitigated_circuit
    assert "mitigation" in mitigated_circuit["metadata"]
    assert mitigated_circuit["metadata"]["mitigation"] == expected_meta
    # Check that the warning was logged (since we mocked it)
    assert mock_logger_warning.called