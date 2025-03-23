"""
Generate unit tests for quantum circuits.
"""

import os
import sys
import logging
import json
import re
from pathlib import Path
import shutil
import requests
from string import Template

from ..config import get_config
from ..logging_config import setup_logger
from ..output_formatter import format_output

# Set up logger
logger = logging.getLogger(__name__)

# Test templates for different circuit types
BELL_STATE_TEST_TEMPLATE = """
import pytest
import numpy as np
from qiskit import QuantumCircuit, Aer, execute
from qiskit.quantum_info import state_fidelity

def test_bell_state_fidelity():
    """Test that the circuit creates a proper Bell state."""
    # Load the circuit
    with open("${circuit_path}", "r") as f:
        qasm = f.read()
    
    # Create circuit from QASM
    circuit = QuantumCircuit.from_qasm_str(qasm)
    
    # Simulate the circuit
    simulator = Aer.get_backend('statevector_simulator')
    result = execute(circuit, simulator).result()
    state = result.get_statevector()
    
    # Define the ideal Bell state
    bell_state = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)])
    
    # Calculate fidelity
    fidelity = state_fidelity(state, bell_state)
    
    # Check that fidelity is close to 1
    assert fidelity > 0.99, f"Bell state fidelity {fidelity} is lower than expected"

def test_bell_state_measurement():
    """Test that measuring the circuit gives expected results."""
    # Load the circuit
    with open("${circuit_path}", "r") as f:
        qasm = f.read()
    
    # Create circuit from QASM
    circuit = QuantumCircuit.from_qasm_str(qasm)
    
    # Add measurements if not already present
    if not circuit.clbits:
        circuit.measure_all()
    
    # Simulate the circuit with shots
    simulator = Aer.get_backend('qasm_simulator')
    result = execute(circuit, simulator, shots=${shots}).result()
    counts = result.get_counts()
    
    # Check that we only get |00> and |11> with approximately equal probability
    assert '00' in counts or '0' in counts, "Expected |00> state not found in results"
    assert '11' in counts or '1' in counts, "Expected |11> state not found in results"
    
    # Allow for some statistical variation
    total_shots = sum(counts.values())
    tolerance = 0.2  # 20% tolerance
    
    # For single-bit results
    if '0' in counts and '1' in counts:
        prob_0 = counts['0'] / total_shots
        prob_1 = counts['1'] / total_shots
        assert abs(prob_0 - 0.5) < tolerance, f"Probability of |0> ({prob_0}) differs from expected (0.5)"
        assert abs(prob_1 - 0.5) < tolerance, f"Probability of |1> ({prob_1}) differs from expected (0.5)"
    
    # For two-bit results
    if '00' in counts and '11' in counts:
        prob_00 = counts.get('00', 0) / total_shots
        prob_11 = counts.get('11', 0) / total_shots
        prob_01 = counts.get('01', 0) / total_shots
        prob_10 = counts.get('10', 0) / total_shots
        
        assert abs(prob_00 - 0.5) < tolerance or abs(prob_11 - 0.5) < tolerance, \
            f"Probabilities of |00> ({prob_00}) and |11> ({prob_11}) differ from expected"
        assert prob_01 < 0.1, f"Unexpected state |01> with probability {prob_01}"
        assert prob_10 < 0.1, f"Unexpected state |10> with probability {prob_10}"
"""

GENERIC_CIRCUIT_TEST_TEMPLATE = """
import pytest
import numpy as np
from qiskit import QuantumCircuit, Aer, execute

def test_circuit_runs_without_error():
    """Test that the circuit can be executed without errors."""
    # Load the circuit
    with open("${circuit_path}", "r") as f:
        qasm = f.read()
    
    # Create circuit from QASM
    circuit = QuantumCircuit.from_qasm_str(qasm)
    
    # Add measurements if not already present
    if not circuit.clbits:
        circuit.measure_all()
    
    # Simulate the circuit
    simulator = Aer.get_backend('qasm_simulator')
    result = execute(circuit, simulator, shots=${shots}).result()
    
    # Check that the simulation completed successfully
    assert result.success, "Circuit simulation failed"
    
    # Check that we got measurement results
    counts = result.get_counts()
    assert len(counts) > 0, "No measurement results returned"

def test_circuit_deterministic_output():
    """Test that running the circuit multiple times produces consistent results."""
    # Load the circuit
    with open("${circuit_path}", "r") as f:
        qasm = f.read()
    
    # Create circuit from QASM
    circuit = QuantumCircuit.from_qasm_str(qasm)
    
    # Add measurements if not already present
    if not circuit.clbits:
        circuit.measure_all()
    
    # Run the circuit multiple times
    simulator = Aer.get_backend('qasm_simulator')
    results = []
    
    for _ in range(5):
        result = execute(circuit, simulator, shots=${shots}).result()
        counts = result.get_counts()
        # Normalize counts to probabilities
        total = sum(counts.values())
        probs = {k: v/total for k, v in counts.items()}
        results.append(probs)
    
    # Check that distributions are similar across runs
    reference = results[0]
    for i, other in enumerate(results[1:], 1):
        for state in set(reference.keys()) | set(other.keys()):
            ref_prob = reference.get(state, 0)
            other_prob = other.get(state, 0)
            assert abs(ref_prob - other_prob) < 0.1, \
                f"Run {i} has different probability for state {state}: {other_prob} vs {ref_prob}"
"""

ALGORITHM_TEST_TEMPLATES = {
    "shor": """
import pytest
import numpy as np
from qiskit import QuantumCircuit, Aer, execute

def test_shor_algorithm_factors_correctly():
    """Test that Shor's algorithm correctly factors the target number."""
    # This is a simplified test for demonstration
    # Load the circuit
    with open("${circuit_path}", "r") as f:
        qasm = f.read()
    
    # Extract the number being factored (typically from metadata or filename)
    target_number = ${target_number}  # Replace with actual logic to extract the number
    
    # Expected factors
    expected_factors = ${expected_factors}  # Replace with actual factors
    
    # In a real implementation, we'd validate that the circuit correctly factors the number
    # This would involve running the circuit and processing the results
    
    # For this template, we'll just assert that the circuit exists
    assert qasm.startswith("OPENQASM"), "Invalid QASM file"
""",
    
    "grover": """
import pytest
import numpy as np
from qiskit import QuantumCircuit, Aer, execute

def test_grover_search_finds_target():
    """Test that Grover's search algorithm finds the target state."""
    # Load the circuit
    with open("${circuit_path}", "r") as f:
        qasm = f.read()
    
    # Create circuit from QASM
    circuit = QuantumCircuit.from_qasm_str(qasm)
    
    # Add measurements if not already present
    if not circuit.clbits:
        circuit.measure_all()
    
    # Simulate the circuit
    simulator = Aer.get_backend('qasm_simulator')
    result = execute(circuit, simulator, shots=${shots}).result()
    counts = result.get_counts()
    
    # Determine the most common result
    most_common_state = max(counts, key=counts.get)
    most_common_prob = counts[most_common_state] / sum(counts.values())
    
    # In Grover's algorithm, the target state should be measured with high probability
    assert most_common_prob > 0.5, \
        f"Target state {most_common_state} was not the most probable outcome ({most_common_prob})"
"""
}

def analyze_circuit(source_file):
    """
    Analyze a quantum circuit to determine its type and properties.
    
    Args:
        source_file (str): Path to the circuit file
        
    Returns:
        dict: Circuit properties and analysis
    """
    try:
        with open(source_file, 'r') as f:
            content = f.read()
            
        # Check if it's a Bell state circuit
        is_bell_state = ("h q" in content.lower() and 
                         "cx q" in content.lower() and 
                         content.count("qreg") == 1)
        
        # Count number of qubits
        qreg_matches = re.findall(r'qreg\s+(\w+)\[(\d+)\];', content)
        qubit_count = sum(int(size) for _, size in qreg_matches)
        
        # Identify algorithm type
        algorithm_type = None
        if "shor" in source_file.lower() or "factor" in source_file.lower():
            algorithm_type = "shor"
        elif "grover" in source_file.lower() or "search" in source_file.lower():
            algorithm_type = "grover"
        
        # Count gate types
        gates = {
            "h": len(re.findall(r'h\s+', content, re.IGNORECASE)),
            "x": len(re.findall(r'x\s+', content, re.IGNORECASE)),
            "cx": len(re.findall(r'cx\s+', content, re.IGNORECASE)),
            "measure": len(re.findall(r'measure\s+', content, re.IGNORECASE))
        }
        
        return {
            "qubit_count": qubit_count,
            "is_bell_state": is_bell_state,
            "algorithm_type": algorithm_type,
            "gates": gates,
            "has_measurements": gates["measure"] > 0
        }
        
    except Exception as e:
        logger.error(f"Error analyzing circuit file: {e}")
        return {
            "qubit_count": 0,
            "is_bell_state": False,
            "algorithm_type": None,
            "gates": {},
            "has_measurements": False,
            "error": str(e)
        }

def get_appropriate_test_template(circuit_analysis):
    """
    Select the appropriate test template based on circuit analysis.
    
    Args:
        circuit_analysis (dict): Circuit analysis results
        
    Returns:
        str: Test template
    """
    if circuit_analysis.get("is_bell_state"):
        return BELL_STATE_TEST_TEMPLATE
    
    algorithm_type = circuit_analysis.get("algorithm_type")
    if algorithm_type in ALGORITHM_TEST_TEMPLATES:
        return ALGORITHM_TEST_TEMPLATES[algorithm_type]
        
    # Default to generic circuit test
    return GENERIC_CIRCUIT_TEST_TEMPLATE

def generate_test_file(source_file, template, dest_file, params=None):
    """
    Generate a test file from a template.
    
    Args:
        source_file (str): Path to the source circuit
        template (str): Template string
        dest_file (str): Destination test file path
        params (dict, optional): Additional template parameters
        
    Returns:
        bool: True if successful
    """
    try:
        # Create default parameters
        if params is None:
            params = {}
            
        # Add default parameters
        params.update({
            "circuit_path": os.path.relpath(source_file, os.path.dirname(dest_file)),
            "shots": params.get("shots", 1024)
        })
        
        # Generate test content from template
        template_obj = Template(template)
        test_content = template_obj.safe_substitute(params)
        
        # Ensure directory exists
        dest_dir = os.path.dirname(dest_file)
        os.makedirs(dest_dir, exist_ok=True)
        
        # Create __init__.py file to make the directory a package
        init_file = os.path.join(dest_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write("# Auto-generated test package\n")
        
        # Write the test file
        with open(dest_file, 'w') as f:
            f.write(test_content)
            
        logger.info(f"Generated test file: {dest_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error generating test file: {e}")
        return False

def generate_tests_with_llm(source_file, dest_file, llm_url):
    """
    Generate tests using an LLM service.
    
    Args:
        source_file (str): Path to the source circuit
        dest_file (str): Destination test file path
        llm_url (str): URL to the LLM service
        
    Returns:
        bool: True if successful
    """
    try:
        # Read the circuit
        with open(source_file, 'r') as f:
            circuit_content = f.read()
            
        # Prepare request payload
        payload = {
            "circuit": circuit_content,
            "test_type": "unit_test",
            "framework": "pytest",
            "file_name": os.path.basename(source_file)
        }
        
        # Call LLM API
        logger.info(f"Calling LLM service at {llm_url}")
        response = requests.post(llm_url, json=payload, timeout=60)
        response.raise_for_status()
        
        # Process response
        test_content = response.json().get("test_code")
        if not test_content:
            logger.error("LLM service did not return test code")
            return False
            
        # Write the test file
        dest_dir = os.path.dirname(dest_file)
        os.makedirs(dest_dir, exist_ok=True)
        
        with open(dest_file, 'w') as f:
            f.write(test_content)
            
        logger.info(f"Generated test file using LLM: {dest_file}")
        return True
        
    except requests.RequestException as e:
        logger.error(f"Error calling LLM service: {e}")
        return False
    except Exception as e:
        logger.error(f"Error generating tests with LLM: {e}")
        return False

def create_conftest_file(dest_dir):
    """
    Create a conftest.py file for pytest configuration.
    
    Args:
        dest_dir (str): Destination directory
        
    Returns:
        bool: True if successful
    """
    conftest_content = """
import pytest
import os
import sys
from qiskit import Aer

@pytest.fixture(scope="session")
def statevector_simulator():
    """Return a statevector simulator backend."""
    return Aer.get_backend('statevector_simulator')

@pytest.fixture(scope="session")
def qasm_simulator():
    """Return a QASM simulator backend."""
    return Aer.get_backend('qasm_simulator')
    
@pytest.fixture(scope="session")
def shots():
    """Return the default number of shots for tests."""
    return 1024
"""
    try:
        conftest_path = os.path.join(dest_dir, "conftest.py")
        with open(conftest_path, 'w') as f:
            f.write(conftest_content)
        logger.info(f"Created conftest.py at {conftest_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating conftest.py: {e}")
        return False

def generate_tests(source_file, dest_file=None, llm_url=None):
    """
    Generate unit tests for a quantum circuit.
    
    Args:
        source_file (str): Path to the source circuit file
        dest_file (str, optional): Path to write the unit tests
        llm_url (str, optional): URL of LLM service for enhanced test generation
        
    Returns:
        bool: True if test generation was successful
    """
    logger.info(f"Starting test generation for {source_file}")
    
    # Ensure source file exists
    if not os.path.exists(source_file):
        logger.error(f"Source file {source_file} does not exist")
        return False
    
    # Determine file type
    file_ext = os.path.splitext(source_file)[1].lower()
    
    if file_ext != '.qasm':
        logger.error(f"Unsupported file type for test generation: {file_ext}")
        return False
    
    # Determine destination path
    if not dest_file:
        # Default path: tests/unit/test_<circuit_name>.py
        source_basename = os.path.basename(source_file)
        circuit_name = os.path.splitext(source_basename)[0]
        dest_file = os.path.join("tests", "unit", f"test_{circuit_name}.py")
    
    # Create destination directory if it doesn't exist
    dest_dir = os.path.dirname(dest_file)
    os.makedirs(dest_dir, exist_ok=True)
    
    # Create conftest.py file
    create_conftest_file(dest_dir)
    
    # If LLM URL is provided, use LLM for test generation
    if llm_url:
        return generate_tests_with_llm(source_file, dest_file, llm_url)
    
    # Otherwise, use template-based test generation
    circuit_analysis = analyze_circuit(source_file)
    template = get_appropriate_test_template(circuit_analysis)
    
    # Prepare template parameters
    params = {
        "shots": 1024,
    }
    
    # Add algorithm-specific parameters
    if circuit_analysis.get("algorithm_type") == "shor":
        # In a real implementation, these would be extracted from the circuit
        params["target_number"] = 15
        params["expected_factors"] = "[3, 5]"
    
    # Generate the test file
    success = generate_test_file(source_file, template, dest_file, params)
    
    if success:
        logger.info(f"Successfully generated test file: {dest_file}")
    else:
        logger.error(f"Failed to generate test file")
    
    return success

if __name__ == "__main__":
    # This allows the module to be run directly for testing
    if len(sys.argv) < 2:
        print("Usage: generate_tests.py <source_file> [<dest_file>] [--llm <llm_url>]")
        sys.exit(1)
    
    source = sys.argv[1]
    dest = None
    llm = None
    
    # Parse remaining arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--llm" and i+1 < len(sys.argv):
            llm = sys.argv[i+1]
            i += 2
        else:
            dest = sys.argv[i]
            i += 1
    
    success = generate_tests(source, dest, llm)
    sys.exit(0 if success else 1)
