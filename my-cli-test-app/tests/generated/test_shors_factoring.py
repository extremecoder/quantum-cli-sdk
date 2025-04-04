import os
import pytest
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Operator, Statevector
from qiskit_aer import AerSimulator

# Path to the QASM file
QASM_FILE = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 
    '../../ir/openqasm/shors_factoring_15_compatible.qasm'
))

# Ensure the QASM file exists
def test_qasm_file_exists():
    """Verify that the QASM file exists."""
    assert os.path.exists(QASM_FILE), f"QASM file not found at {QASM_FILE}"

#############################################
# 1. Circuit Structure Validation Tests
#############################################

def test_qubit_clbit_count():
    """Verify the circuit uses the expected number of quantum and classical bits."""
    circuit = QuantumCircuit.from_qasm_file(QASM_FILE)
    
    # In the Shor's factoring circuit, we should have:
    # - 4 qubits for period register
    # - 4 qubits for target register
    # - 4 classical bits for measurement
    assert circuit.num_qubits == 8, f"Expected 8 qubits, found {circuit.num_qubits}"
    assert circuit.num_clbits == 4, f"Expected 4 classical bits, found {circuit.num_clbits}"

def test_gate_set():
    """Check if the circuit only uses gates from an allowed or expected set."""
    circuit = QuantumCircuit.from_qasm_file(QASM_FILE)
    
    # Get operation counts
    ops = circuit.count_ops()
    
    # Define allowed gates (based on the QASM file contents)
    allowed_gates = {'h', 'x', 'cx', 'swap', 'cz', 'measure'}
    
    # Check all operations are in allowed set
    for gate in ops:
        assert gate in allowed_gates, f"Unauthorized gate '{gate}' found in circuit"
    
    # Check required gates are present for Shor's algorithm
    assert 'h' in ops, "Circuit should contain Hadamard gates for quantum Fourier transform"
    assert 'cx' in ops, "Circuit should contain CNOT gates for modular exponentiation"

def test_circuit_depth():
    """Ensure the circuit depth is within acceptable limits."""
    circuit = QuantumCircuit.from_qasm_file(QASM_FILE)
    
    # Calculate circuit depth
    depth = circuit.depth()
    
    # Define a reasonable maximum depth for this circuit
    max_depth = 50  # Adjust based on expected complexity
    assert depth <= max_depth, f"Circuit depth ({depth}) exceeds maximum allowed ({max_depth})"
    
    # Also verify the depth is sufficient for a meaningful Shor's implementation
    min_depth = 10
    assert depth >= min_depth, f"Circuit depth ({depth}) is suspiciously shallow for Shor's algorithm"

def test_gate_count():
    """Count specific types of gates in the circuit."""
    circuit = QuantumCircuit.from_qasm_file(QASM_FILE)
    ops = circuit.count_ops()
    
    # Check CNOT count (important for resource estimation)
    cx_count = ops.get('cx', 0)
    assert cx_count >= 4, f"Too few CNOT gates ({cx_count}) for Shor's algorithm implementation"
    
    # Check Hadamard count (important for superposition creation)
    h_count = ops.get('h', 0)
    assert h_count >= 4, f"Too few Hadamard gates ({h_count}) for quantum Fourier transform"
    
    # Check total gate count
    total_gates = sum(ops.values())
    assert 15 <= total_gates <= 100, f"Total gate count ({total_gates}) outside expected range for Shor's factoring of 15"

def test_measurement_operations():
    """Verify measurements are correctly placed and target the right qubits/classical bits."""
    circuit = QuantumCircuit.from_qasm_file(QASM_FILE)
    
    # In Qiskit 1.0+, we need to use the structured attributes
    measured_qubits = set()
    measure_count = 0
    
    for instruction in circuit.data:
        if instruction.operation.name == 'measure':
            measure_count += 1
            # Get the qubit index differently in Qiskit 1.0+
            measured_qubits.add(circuit.qubits.index(instruction.qubits[0]))
    
    # Verify measurement count - we expect 4 for the period register
    assert measure_count == 4, f"Expected 4 measurement operations, found {measure_count}"
    
    # In the specific QASM file, period[0-3] should be measured
    expected_measured = {0, 1, 2, 3}  # Based on period register qubits
    assert measured_qubits == expected_measured, f"Expected to measure qubits {expected_measured}, but measured {measured_qubits}"

#############################################
# 2. Circuit Behavior Simulation Tests
#############################################

def test_circuit_simulation():
    """Test that the circuit executes without errors and returns a valid result."""
    circuit = QuantumCircuit.from_qasm_file(QASM_FILE)
    
    # Run on QASM simulator
    simulator = AerSimulator()
    transpiled = transpile(circuit, simulator)
    
    # The test passes if the simulation completes without error
    try:
        result = simulator.run(transpiled, shots=1024).result()
        counts = result.get_counts()
        
        # Verify we got a valid counts dictionary with expected format
        assert isinstance(counts, dict), "Result counts is not a dictionary"
        assert len(counts) > 0, "No measurement results returned"
        
        # All keys should be 4-bit strings (for the 4 measured qubits)
        for bitstring in counts.keys():
            assert len(bitstring) == 4, f"Expected 4-bit measurement results, got {bitstring}"
    
    except Exception as e:
        pytest.fail(f"Circuit simulation failed with error: {str(e)}")

def test_result_distribution():
    """Verify the circuit produces a distribution of results consistent with Shor's algorithm."""
    circuit = QuantumCircuit.from_qasm_file(QASM_FILE)
    
    # Run on QASM simulator with many shots
    simulator = AerSimulator()
    transpiled = transpile(circuit, simulator)
    result = simulator.run(transpiled, shots=8192).result()
    counts = result.get_counts()
    
    # Shor's algorithm should produce a non-uniform distribution with preference
    # for states that encode the period of the modular function
    
    # Calculate entropy of distribution as a simple check
    total_shots = sum(counts.values())
    probabilities = [count / total_shots for count in counts.values()]
    entropy = -sum(p * np.log2(p) for p in probabilities if p > 0)
    
    # A uniform distribution over 2^4 = 16 possibilities would have entropy = 4
    # A completely deterministic result would have entropy = 0
    # For Shor's, we expect something in between
    assert 1.5 < entropy < 4.0, f"Distribution entropy {entropy} outside expected range for Shor's algorithm"

#############################################
# 3. Algorithm-Specific Functional Tests
#############################################

def test_period_finding():
    """Verify that the circuit is capable of finding periods for Shor's algorithm."""
    circuit = QuantumCircuit.from_qasm_file(QASM_FILE)
    
    # Run multiple times to check if results are consistent with periods for factoring 15
    simulator = AerSimulator()
    transpiled = transpile(circuit, simulator)
    result = simulator.run(transpiled, shots=8192).result()
    counts = result.get_counts()
    
    # For N=15, valid periods include 4 (for a=2 or a=8), 2 (for a=4 or a=11), etc.
    # We don't know which 'a' was used in this implementation, but we can verify
    # the results are consistent with some valid period
    
    # Extract the most common result
    most_common = max(counts, key=counts.get)
    
    # Function to verify if measured value corresponds to a potential period
    def is_valid_period_measurement(bitstring, n=15):
        """Check if a measurement could correspond to a valid period for factoring n=15."""
        # Convert to integer
        measured = int(bitstring, 2)
        possible_periods = [1, 2, 4, 8]  # Potential periods for N=15
        
        # Due to the nature of QFT, the measured value needs further processing
        # For an ideal measurement corresponding to period r, we'd get s/r for some s < r
        for period in possible_periods:
            # Check if measurement is close to s/r for any s < r
            for s in range(1, period):
                expected = (s * 2**len(bitstring)) / period
                # Allow some numerical tolerance
                if abs(measured - expected) <= 0.1 * 2**len(bitstring):
                    return True
        return False
    
    # Verify at least some top results correspond to potentially valid periods
    top_results = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
    valid_period_percentage = sum(1 for bitstring, count in top_results 
                                if is_valid_period_measurement(bitstring)) / len(top_results)
    
    assert valid_period_percentage > 0.3, "Less than 30% of top measurements correspond to potential periods"

#############################################
# 4. Hardware Compatibility Tests
#############################################

def test_connectivity_constraints():
    """Verify the circuit can be mapped to hardware with connectivity constraints."""
    circuit = QuantumCircuit.from_qasm_file(QASM_FILE)
    
    # Define a realistic coupling map (like IBM Falcon topology)
    coupling_map = [
        [0, 1], [1, 0], [1, 2], [2, 1], [2, 3], [3, 2], [3, 4], [4, 3],
        [4, 5], [5, 4], [5, 6], [6, 5], [6, 7], [7, 6]
    ]
    
    # Try to transpile the circuit to the target topology
    try:
        transpiled_circuit = transpile(circuit, 
                                      basis_gates=['id', 'sx', 'x', 'rz', 'cx'],
                                      coupling_map=coupling_map,
                                      optimization_level=1)
        
        # Verify transpilation succeeded
        assert isinstance(transpiled_circuit, QuantumCircuit), "Transpilation failed"
        
        # Success if transpilation completes without error
    
    except Exception as e:
        pytest.fail(f"Failed to transpile circuit to target topology: {str(e)}")

#############################################
# 5. Noise and Error Mitigation Tests
#############################################

def test_noise_resilience():
    """Test circuit performance under simulated noise conditions."""
    circuit = QuantumCircuit.from_qasm_file(QASM_FILE)
    
    # Create a noisy simulator with default noise model
    try:
        from qiskit_aer.noise import NoiseModel
        from qiskit_aer.noise.errors import depolarizing_error
        
        # Create a basic noise model
        noise_model = NoiseModel()
        
        # Add depolarizing error
        # Using a mild error rate to check if the circuit produces meaningful results
        p_1 = 0.01  # 1% error on single-qubit gates
        p_2 = 0.05  # 5% error on two-qubit gates
        
        # Get available gates from the circuit
        ops = circuit.count_ops()
        gates_1q = [g for g in ops.keys() if g in ['x', 'h', 'rz', 'id']]
        gates_2q = [g for g in ops.keys() if g in ['cx', 'cz', 'swap']]
        
        # Add errors to the model
        if gates_1q:
            error_1q = depolarizing_error(p_1, 1)
            for gate in gates_1q:
                noise_model.add_all_qubit_quantum_error(error_1q, gate)
        
        if gates_2q:
            error_2q = depolarizing_error(p_2, 2)
            for gate in gates_2q:
                noise_model.add_all_qubit_quantum_error(error_2q, gate)
        
        # Simulate with and without noise
        simulator = AerSimulator()
        noisy_simulator = AerSimulator(noise_model=noise_model)
        
        # Without noise
        result_ideal = simulator.run(transpile(circuit, simulator), shots=4096).result()
        counts_ideal = result_ideal.get_counts()
        
        # With noise
        result_noise = noisy_simulator.run(transpile(circuit, noisy_simulator), shots=4096).result()
        counts_noise = result_noise.get_counts()
        
        # Calculate distribution similarity using a basic metric
        total_ideal = sum(counts_ideal.values())
        total_noise = sum(counts_noise.values())
        
        # Calculate total variation distance
        all_outcomes = set(counts_ideal.keys()).union(counts_noise.keys())
        tvd = 0.5 * sum(abs(counts_ideal.get(outcome, 0) / total_ideal - 
                          counts_noise.get(outcome, 0) / total_noise)
                      for outcome in all_outcomes)
        
        # For a robust circuit under mild noise, TVD should not be too large
        assert tvd < 0.5, f"Circuit is highly sensitive to noise (TVD = {tvd})"
    
    except ImportError:
        pytest.skip("Noise model functionality not available in this Qiskit version")

#############################################
# 6. Visualization and Metadata Tests
#############################################

def test_circuit_drawing():
    """Test that circuit visualization functions work correctly."""
    circuit = QuantumCircuit.from_qasm_file(QASM_FILE)
    
    # Test text drawing - in Qiskit 1.0+ the output is no longer a string
    # but instead a TextDrawing object that can be converted to string
    try:
        # Just test that drawing completes without error
        text_drawing = circuit.draw(output='text')
        text_str = str(text_drawing)
        
        assert len(text_str) > 0, "Text drawing should not be empty"
        
        # Verify the drawing contains expected elements
        assert "period" in text_str, "Drawing should show period register"
        assert "target" in text_str, "Drawing should show target register"
        assert "reg_measure" in text_str, "Drawing should show measurement register"
    except Exception as e:
        pytest.fail(f"Text drawing failed: {str(e)}")
    
    # In Qiskit 1.0+, 'ascii' output format is no longer supported
    # The only valid options are 'text', 'latex', 'latex_source', and 'mpl'
    try:
        # Use 'text' format again but with different settings
        text_drawing2 = circuit.draw(output='text', fold=40)  # With different folding setting
        text_str2 = str(text_drawing2)
        assert len(text_str2) > 0, "Second text drawing should not be empty"
    except Exception as e:
        pytest.fail(f"Alternative text drawing failed: {str(e)}")

#############################################
# 7. Error Handling and Negative Tests
#############################################

def test_invalid_operations():
    """Test that the circuit handles invalid operations appropriately."""
    circuit = QuantumCircuit.from_qasm_file(QASM_FILE)
    
    # Try operations that should cause errors
    with pytest.raises(Exception) as excinfo:
        # Apply a gate to a non-existent qubit
        circuit.h(100)
    assert "index" in str(excinfo.value).lower() or "out of range" in str(excinfo.value).lower(), \
        "Should raise appropriate error for invalid qubit index"
    
    with pytest.raises(Exception) as excinfo:
        # Measure to a non-existent classical bit
        circuit.measure(0, 100)
    assert "index" in str(excinfo.value).lower() or "out of range" in str(excinfo.value).lower(), \
        "Should raise appropriate error for invalid classical bit index"

#############################################
# 8. Performance Tests
#############################################

def test_execution_time():
    """Test the circuit execution time is reasonable."""
    import time
    
    circuit = QuantumCircuit.from_qasm_file(QASM_FILE)
    simulator = AerSimulator()
    transpiled = transpile(circuit, simulator)
    
    # Measure execution time
    start_time = time.time()
    result = simulator.run(transpiled, shots=1024).result()
    end_time = time.time()
    
    execution_time = end_time - start_time
    
    # The execution time should be reasonable
    assert execution_time < 5.0, f"Circuit execution took too long: {execution_time} seconds"
    
    # Just for information
    print(f"\nExecution time: {execution_time:.4f} seconds for {circuit.depth()} depth circuit")

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 