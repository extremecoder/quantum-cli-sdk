"""
Run tests for quantum circuits.
"""

import os
import sys
import logging
import json
import subprocess
from pathlib import Path
import tempfile
import shutil

from ..config import get_config
from ..quantum_circuit import QuantumCircuit
from ..output_formatter import format_output
from ..test_framework import run_tests

# Set up logger
logger = logging.getLogger(__name__)

def run_pytest(test_dir, source_path=None, verbose=True, xml_report=None):
    """
    Run pytest for quantum circuit tests.
    
    Args:
        test_dir (str): Directory containing tests
        source_path (str, optional): Path to source circuits for import
        verbose (bool): Whether to run in verbose mode
        xml_report (str, optional): Path to write XML report
        
    Returns:
        dict: Test results
    """
    try:
        # Build pytest command
        cmd = ["pytest"]
        
        # Add verbosity
        if verbose:
            cmd.append("-v")
            
        # Add XML report if specified
        if xml_report:
            cmd.append(f"--junitxml={xml_report}")
            
        # Add test directory
        cmd.append(test_dir)
        
        # Set environment variables for tests to find source circuits
        env = os.environ.copy()
        if source_path:
            env["QUANTUM_SOURCE_PATH"] = os.path.abspath(source_path)
            
        logger.info(f"Running tests with command: {' '.join(cmd)}")
        
        # Run pytest
        process = subprocess.run(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Parse output
        output = process.stdout
        
        # Check exit code
        is_success = process.returncode == 0
        
        # Extract test summary information
        test_info = {
            "success": is_success,
            "exit_code": process.returncode,
            "output": output,
            "error": process.stderr if process.stderr else None
        }
        
        # Try to parse more details
        if "collected" in output:
            try:
                # Extract number of tests
                collected_line = [line for line in output.split("\n") if "collected" in line][0]
                test_count = int(collected_line.split("collected ")[1].split(" ")[0])
                test_info["total_tests"] = test_count
                
                # Count passed/failed/skipped tests
                test_info["passed"] = output.count("PASSED")
                test_info["failed"] = output.count("FAILED")
                test_info["skipped"] = output.count("SKIPPED")
                test_info["errors"] = output.count("ERROR")
            except (IndexError, ValueError) as e:
                logger.warning(f"Could not parse test summary: {e}")
                
        return test_info
        
    except Exception as e:
        logger.error(f"Error running pytest: {e}")
        return {
            "success": False,
            "error": str(e),
            "output": None,
            "exit_code": -1
        }

def run_simulator_test(simulator, circuit_path, output_path, shots=1024):
    """
    Run a simulator-based test on a circuit.
    
    Args:
        simulator (str): Simulator to use (qiskit, cirq, braket)
        circuit_path (str): Path to circuit file
        output_path (str): Path to write results
        shots (int): Number of shots
        
    Returns:
        bool: True if test passed
    """
    try:
        # Import simulator modules based on requested simulator
        if simulator == "qiskit":
            from qiskit import QuantumCircuit, Aer, execute
            
            # Read circuit
            with open(circuit_path, 'r') as f:
                qasm = f.read()
                
            # Create circuit
            circuit = QuantumCircuit.from_qasm_str(qasm)
            
            # Add measurements if not present
            if not circuit.clbits:
                circuit.measure_all()
                
            # Run simulation
            backend = Aer.get_backend('qasm_simulator')
            result = execute(circuit, backend, shots=shots).result()
            
            # Check execution status
            if not result.success:
                logger.error("Qiskit simulation failed")
                return False
                
            # Get counts and save to output file
            counts = result.get_counts()
            with open(output_path, 'w') as f:
                json.dump({
                    "simulator": "qiskit",
                    "shots": shots,
                    "counts": {k: v for k, v in counts.items()},
                    "success": True
                }, f, indent=2)
                
            logger.info(f"Qiskit simulation test passed, results saved to {output_path}")
            return True
            
        elif simulator == "cirq":
            try:
                import cirq
                import cirq_qasm
                
                # Read circuit
                with open(circuit_path, 'r') as f:
                    qasm = f.read()
                    
                # Create circuit from QASM using converter
                qasm_converter = cirq_qasm.QasmParser()
                circuit = qasm_converter.parse(qasm)
                
                # Run simulation
                simulator = cirq.Simulator()
                result = simulator.run(circuit, repetitions=shots)
                
                # Save results
                with open(output_path, 'w') as f:
                    json.dump({
                        "simulator": "cirq",
                        "shots": shots,
                        "counts": {str(k): v for k, v in result.histogram(key='all').items()},
                        "success": True
                    }, f, indent=2)
                    
                logger.info(f"Cirq simulation test passed, results saved to {output_path}")
                return True
                
            except ImportError:
                logger.error("Cirq or cirq_qasm not installed")
                return False
                
        elif simulator == "braket":
            try:
                from braket.circuits import Circuit
                from braket.devices import LocalSimulator
                
                # Read circuit as QASM
                with open(circuit_path, 'r') as f:
                    qasm = f.read()
                    
                # Create circuit from QASM (simplified conversion)
                # Note: In a real implementation, use a proper QASM to Braket converter
                circuit = Circuit.from_openqasm(qasm)
                
                # Run simulation
                device = LocalSimulator()
                task = device.run(circuit, shots=shots)
                result = task.result()
                
                # Save results
                measurement_counts = result.measurement_counts
                with open(output_path, 'w') as f:
                    json.dump({
                        "simulator": "braket",
                        "shots": shots,
                        "counts": measurement_counts,
                        "success": True
                    }, f, indent=2)
                    
                logger.info(f"Braket simulation test passed, results saved to {output_path}")
                return True
                
            except ImportError:
                logger.error("Braket SDK not installed")
                return False
                
        else:
            logger.error(f"Unsupported simulator: {simulator}")
            return False
            
    except Exception as e:
        logger.error(f"Error running {simulator} simulation test: {e}")
        
        # Write error report
        try:
            with open(output_path, 'w') as f:
                json.dump({
                    "simulator": simulator,
                    "shots": shots,
                    "success": False,
                    "error": str(e)
                }, f, indent=2)
        except Exception as write_err:
            logger.error(f"Could not write error report: {write_err}")
            
        return False

def test(source=None, dest=None, simulator="qiskit", shots=1024):
    """
    Run tests for quantum circuits.
    
    Args:
        source (str, optional): Path to the source circuit or test directory
        dest (str, optional): Path to write test results
        simulator (str): Simulator to use (qiskit, cirq, braket, all)
        shots (int): Number of shots for simulation
        
    Returns:
        bool: True if all tests passed
    """
    logger.info(f"Starting quantum tests with simulator(s): {simulator}")
    
    # Determine test mode based on source path
    if not source:
        # Default to looking for unit tests
        source = os.path.join("tests", "unit")
        
    # Create destination directory if not specified
    if not dest:
        dest = os.path.join("results", "tests", "unit")
        
    # Create directory if it doesn't exist
    os.makedirs(dest, exist_ok=True)
    
    # Determine test mode
    if os.path.isdir(source) and (
        os.path.exists(os.path.join(source, "conftest.py")) or
        any(f.startswith("test_") and f.endswith(".py") for f in os.listdir(source))
    ):
        # This is a directory containing pytest test files
        logger.info(f"Running pytest tests from directory: {source}")
        
        # Run pytest
        xml_report = os.path.join(dest, "test_report.xml")
        test_results = run_pytest(source, None, True, xml_report)
        
        # Save JSON summary
        summary_path = os.path.join(dest, "test_summary.json")
        with open(summary_path, 'w') as f:
            json.dump(test_results, f, indent=2)
            
        logger.info(f"Test summary written to {summary_path}")
        
        # Print summary
        if test_results.get("success"):
            logger.info(f"All tests passed ({test_results.get('passed', 0)} tests)")
        else:
            logger.error(f"Tests failed: {test_results.get('failed', 0)} failures, "
                        f"{test_results.get('errors', 0)} errors")
            
        return test_results.get("success", False)
        
    elif os.path.isfile(source) and source.endswith((".qasm", ".json")):
        # This is a single circuit file to test
        logger.info(f"Running simulator tests on circuit: {source}")
        
        # Determine simulators to use
        simulators = ["qiskit", "cirq", "braket"] if simulator == "all" else [simulator]
        
        # Track overall success
        all_success = True
        
        # Run tests with each simulator
        for sim in simulators:
            # Determine output file
            output_file = os.path.join(
                dest, 
                f"{os.path.splitext(os.path.basename(source))[0]}_{sim}_results.json"
            )
            
            # Run simulator test
            success = run_simulator_test(sim, source, output_file, shots)
            
            if not success:
                logger.error(f"Test with {sim} simulator failed")
                all_success = False
        
        return all_success
        
    else:
        logger.error(f"Invalid source for testing: {source}")
        return False

if __name__ == "__main__":
    # This allows the module to be run directly for testing
    if len(sys.argv) < 2:
        print("Usage: test.py <source> [<dest>] [--simulator {qiskit,cirq,braket,all}] [--shots N]")
        sys.exit(1)
    
    # Parse arguments
    source = sys.argv[1]
    
    dest = None
    simulator = "qiskit"
    shots = 1024
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--simulator" and i+1 < len(sys.argv):
            simulator = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == "--shots" and i+1 < len(sys.argv):
            shots = int(sys.argv[i+1])
            i += 2
        else:
            dest = sys.argv[i]
            i += 1
    
    success = test(source, dest, simulator, shots)
    sys.exit(0 if success else 1)
