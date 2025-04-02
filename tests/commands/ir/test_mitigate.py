"""
Unit tests for the ir mitigate command.
"""

import pytest
import argparse
from pathlib import Path
import json
from unittest.mock import patch, MagicMock, mock_open
import os

# Import the command function
from quantum_cli_sdk.commands.ir.mitigate import mitigate_circuit_command, SUPPORTED_TECHNIQUES

# --- Fixtures ---

@pytest.fixture
def mock_args(tmp_path: Path) -> argparse.Namespace:
    """Provides default mock arguments for the command."""
    input_file = tmp_path / "input.qasm"
    input_file.write_text("OPENQASM 2.0;")
    output_dir = tmp_path / "mitigated"
    output_file = output_dir / "output_mitigated.qasm"
    return argparse.Namespace(
        input_file=str(input_file),
        output_file=str(output_file),
        technique="zne",
        params=None,
        report=False
    )

# --- Test Functions ---

@patch('quantum_cli_sdk.commands.ir.mitigate.parse_qasm')
@patch('quantum_cli_sdk.commands.ir.mitigate.get_pass_manager')
@patch('quantum_cli_sdk.commands.ir.mitigate.circuit_to_qasm')
@patch('pathlib.Path.write_text')
@patch('pathlib.Path.mkdir')
@patch('json.dump')
def test_mitigate_command_basic_flow(
    mock_json_dump: MagicMock,
    mock_mkdir: MagicMock,
    mock_write_text: MagicMock,
    mock_circuit_to_qasm: MagicMock,
    mock_get_pass_manager: MagicMock,
    mock_parse_qasm: MagicMock,
    mock_args: argparse.Namespace
):
    """Test the basic successful flow of the mitigate command."""
    # --- Arrange ---
    # Expected Path objects that the command function will create
    expected_input_path = Path(mock_args.input_file)
    expected_output_path = Path(mock_args.output_file)
    expected_parent_path = expected_output_path.parent

    parsed_circuit_dict = {"version": "2.0", "operations": []}
    mock_parse_qasm.return_value = parsed_circuit_dict

    mock_pipeline = MagicMock()
    mock_mitigated_circuit = {"version": "2.0", "operations": [], "metadata": {"mitigation": {"technique": "ZNE"}}}
    mock_pipeline.run.return_value = mock_mitigated_circuit

    mock_pass_manager = MagicMock()
    mock_pass_manager.create_mitigation_pipeline.return_value = mock_pipeline
    mock_get_pass_manager.return_value = mock_pass_manager

    expected_qasm_output = "OPENQASM 2.0; ...mitigated..."
    mock_circuit_to_qasm.return_value = expected_qasm_output

    mock_args.technique = "zne"
    mock_args.report = False

    # --- Act ---
    mitigate_circuit_command(mock_args)

    # --- Assert ---
    # Check parse_qasm was called with the real input Path object
    mock_parse_qasm.assert_called_once_with(expected_input_path)
    mock_get_pass_manager.assert_called_once()
    mock_pass_manager.create_mitigation_pipeline.assert_called_once_with("zne", {})
    mock_pipeline.run.assert_called_once_with(parsed_circuit_dict, options={'mitigation_params': {}})
    mock_circuit_to_qasm.assert_called_once_with(mock_mitigated_circuit)

    # Check mkdir was called once with correct args
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    # Check write_text was called once
    mock_write_text.assert_called_once_with(expected_qasm_output)

    mock_json_dump.assert_not_called() # Report was false

@patch('quantum_cli_sdk.commands.ir.mitigate.parse_qasm')
@patch('quantum_cli_sdk.commands.ir.mitigate.get_pass_manager')
@patch('quantum_cli_sdk.commands.ir.mitigate.circuit_to_qasm')
@patch('pathlib.Path.write_text')
@patch('pathlib.Path.mkdir')
@patch('builtins.open', new_callable=mock_open)
@patch('json.dump')
def test_mitigate_command_with_report(
    mock_json_dump: MagicMock,
    mock_open_builtin: MagicMock,
    mock_mkdir: MagicMock,
    mock_write_text: MagicMock,
    mock_circuit_to_qasm: MagicMock,
    mock_get_pass_manager: MagicMock,
    mock_parse_qasm: MagicMock,
    mock_args: argparse.Namespace
):
    """Test the command flow when --report is specified."""
    # --- Arrange ---
    expected_input_path = Path(mock_args.input_file)
    expected_output_path = Path(mock_args.output_file)
    expected_parent_path = expected_output_path.parent
    expected_report_path = expected_parent_path / f"{expected_output_path.stem}_report.json"

    parsed_circuit_dict = {"version": "2.0"}
    mock_parse_qasm.return_value = parsed_circuit_dict
    mock_pipeline = MagicMock()
    mitigated_circuit_content = {"version": "2.0", "metadata": {"report_data": "some_report"}}
    mock_pipeline.run.return_value = mitigated_circuit_content
    mock_pass_manager = MagicMock()
    mock_pass_manager.create_mitigation_pipeline.return_value = mock_pipeline
    mock_get_pass_manager.return_value = mock_pass_manager

    expected_qasm_content = "QASM_CONTENT"
    mock_circuit_to_qasm.return_value = expected_qasm_content

    mock_args.technique = "pec"
    mock_args.report = True
    mock_args.params = '{"noise_model": "custom"}'
    expected_params = {"noise_model": "custom"}

    # --- Act ---
    mitigate_circuit_command(mock_args)

    # --- Assert ---
    # Check core logic calls
    mock_parse_qasm.assert_called_once_with(expected_input_path)
    mock_pass_manager.create_mitigation_pipeline.assert_called_once_with("pec", expected_params)
    mock_pipeline.run.assert_called_once_with(parsed_circuit_dict, options={'mitigation_params': expected_params})
    mock_circuit_to_qasm.assert_called_once_with(mitigated_circuit_content)

    # Check mkdir on parent directory
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    # Check write_text on main output file
    mock_write_text.assert_called_once_with(expected_qasm_content)

    # Check report file write using mock_open
    mock_open_builtin.assert_called_once_with(expected_report_path, 'w')
    mock_json_dump.assert_called_once()

def test_mitigate_command_invalid_technique(mock_args: argparse.Namespace):
    """Test that an invalid technique causes sys.exit(1)."""
    mock_args.technique = "invalid_tech"
    with patch('quantum_cli_sdk.commands.ir.mitigate.get_pass_manager') as mock_get_pm:
        mock_pm = MagicMock()
        mock_pm.create_mitigation_pipeline.side_effect = ValueError("Unknown mitigation technique")
        mock_get_pm.return_value = mock_pm
        # No need to patch Path methods if they are not reached
        with pytest.raises(SystemExit) as e:
            mitigate_circuit_command(mock_args)
        assert e.value.code == 1

def test_mitigate_command_invalid_params_json(mock_args: argparse.Namespace):
    """Test that invalid JSON in --params causes sys.exit(1)."""
    mock_args.params = '{"invalid_json":' # Malformed JSON
    # No need to patch Path methods if they are not reached
    with pytest.raises(SystemExit) as e:
        mitigate_circuit_command(mock_args)
    assert e.value.code == 1

def test_mitigate_command_params_not_dict(mock_args: argparse.Namespace):
    """Test that non-dict JSON in --params causes sys.exit(1)."""
    mock_args.params = '["list", "not_dict"]'
    with pytest.raises(SystemExit) as e:
        mitigate_circuit_command(mock_args)
    assert e.value.code == 1

@patch('quantum_cli_sdk.commands.ir.mitigate.parse_qasm')
def test_mitigate_command_parse_fail(mock_parse_qasm: MagicMock, mock_args: argparse.Namespace):
    """Test that failure during parsing causes sys.exit(1)."""
    mock_parse_qasm.return_value = None # Simulate parsing failure
    with pytest.raises(SystemExit) as e:
        mitigate_circuit_command(mock_args)
    assert e.value.code == 1

@patch('quantum_cli_sdk.commands.ir.mitigate.parse_qasm')
@patch('quantum_cli_sdk.commands.ir.mitigate.get_pass_manager')
def test_mitigate_command_pipeline_create_fail(
    mock_get_pass_manager: MagicMock,
    mock_parse_qasm: MagicMock,
    mock_args: argparse.Namespace
):
    """Test that failure during pipeline creation causes sys.exit(1)."""
    mock_parse_qasm.return_value = {"version": "2.0"}
    mock_pass_manager = MagicMock()
    mock_pass_manager.create_mitigation_pipeline.return_value = None # Simulate failure
    mock_get_pass_manager.return_value = mock_pass_manager
    
    with pytest.raises(SystemExit) as e:
        mitigate_circuit_command(mock_args)
    assert e.value.code == 1 

@patch('quantum_cli_sdk.commands.ir.mitigate.parse_qasm')
@patch('quantum_cli_sdk.commands.ir.mitigate.get_pass_manager')
@patch('quantum_cli_sdk.commands.ir.mitigate.circuit_to_qasm')
@patch('pathlib.Path.write_text')
@patch('pathlib.Path.mkdir')
def test_mitigate_command_qasm_conversion_failure(
    mock_mkdir: MagicMock,
    mock_write_text: MagicMock,
    mock_to_qasm: MagicMock,
    mock_get_pm: MagicMock,
    mock_parse: MagicMock,
    mock_args: argparse.Namespace
):
    """Test that failure during QASM conversion causes sys.exit(1)."""
    mock_parse.return_value = {"version": "2.0"}
    mock_to_qasm.side_effect = Exception("QASM conversion failed")
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = {"version": "2.0", "metadata": {}} # Assume run succeeds if reached
    mock_pm_instance = MagicMock()
    mock_pm_instance.create_mitigation_pipeline.return_value = mock_pipeline
    mock_get_pm.return_value = mock_pm_instance

    with pytest.raises(SystemExit) as e:
        mitigate_circuit_command(mock_args)
    assert e.value.code == 1
    # Check mkdir was NOT called because conversion failed before output write
    mock_mkdir.assert_not_called()
    # write_text should not be called
    mock_write_text.assert_not_called()

# Test for output write failure (e.g., permissions)
@patch('quantum_cli_sdk.commands.ir.mitigate.parse_qasm')
@patch('quantum_cli_sdk.commands.ir.mitigate.get_pass_manager')
@patch('quantum_cli_sdk.commands.ir.mitigate.circuit_to_qasm')
@patch('pathlib.Path.write_text', side_effect=IOError("Permission denied")) # Fail write_text
@patch('pathlib.Path.mkdir')
def test_mitigate_command_output_write_failure(
    mock_mkdir: MagicMock,
    mock_write_text: MagicMock,
    mock_to_qasm: MagicMock,
    mock_get_pm: MagicMock,
    mock_parse: MagicMock,
    mock_args: argparse.Namespace
):
    """Test that failure during output write causes sys.exit(1)."""
    expected_output_path = Path(mock_args.output_file)
    expected_parent_path = expected_output_path.parent
    expected_qasm_content = "SOME QASM"

    mock_parse.return_value = {"version": "2.0"}
    mock_to_qasm.return_value = expected_qasm_content
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = {"version": "2.0", "metadata": {}}
    mock_pm_instance = MagicMock()
    mock_pm_instance.create_mitigation_pipeline.return_value = mock_pipeline
    mock_get_pm.return_value = mock_pm_instance

    with pytest.raises(SystemExit) as e:
        mitigate_circuit_command(mock_args)
    assert e.value.code == 1
    # Check mkdir was called correctly
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    # Check write_text was attempted
    mock_write_text.assert_called_once()
    mock_write_text.assert_called_once_with(expected_qasm_content)

# Test for report write failure
@patch('quantum_cli_sdk.commands.ir.mitigate.parse_qasm')
@patch('quantum_cli_sdk.commands.ir.mitigate.get_pass_manager')
@patch('quantum_cli_sdk.commands.ir.mitigate.circuit_to_qasm')
@patch('pathlib.Path.write_text') # Mock main write
@patch('pathlib.Path.mkdir')
@patch('builtins.open', new_callable=mock_open)
@patch('json.dump', side_effect=IOError("Disk full")) # Fail json.dump
@patch('sys.exit') # Also patch sys.exit here
def test_mitigate_command_report_write_failure(
    mock_sys_exit: MagicMock, # Added mock for sys.exit
    mock_json_dump: MagicMock,
    mock_open_builtin: MagicMock,
    mock_mkdir: MagicMock,
    mock_write_text: MagicMock,
    mock_to_qasm: MagicMock,
    mock_get_pm: MagicMock,
    mock_parse: MagicMock,
    mock_args: argparse.Namespace,
    caplog # Capture log messages
):
    """Test that failure during report write does NOT cause sys.exit."""
    expected_output_path = Path(mock_args.output_file)
    expected_parent_path = expected_output_path.parent
    expected_report_path = expected_parent_path / f"{expected_output_path.stem}_report.json"
    expected_qasm_content = "SOME QASM"
    mitigated_circuit_content = {"version": "2.0", "metadata": {"report": "data"}}

    mock_args.report = True # Enable report
    mock_parse.return_value = {"version": "2.0"}
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = mitigated_circuit_content # Successful run
    mock_pm_instance = MagicMock()
    mock_pm_instance.create_mitigation_pipeline.return_value = mock_pipeline
    mock_get_pm.return_value = mock_pm_instance
    mock_to_qasm.return_value = expected_qasm_content

    # Run the command - DO NOT expect SystemExit
    mitigate_circuit_command(mock_args)

    # Assertions after the command execution
    # Check mkdir happened
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    # Check main write happened
    mock_write_text.assert_called_once_with(expected_qasm_content)
    # Check open for report was called
    mock_open_builtin.assert_called_once_with(expected_report_path, 'w')
    # Check json.dump was attempted (and failed due to side_effect)
    mock_json_dump.assert_called_once()
    
    # Crucially, check that sys.exit was NOT called
    mock_sys_exit.assert_not_called()

    # Optionally, check that the error was logged
    assert "Failed to write mitigation report" in caplog.text
    assert "Disk full" in caplog.text 