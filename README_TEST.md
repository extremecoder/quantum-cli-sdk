Okay, let's break down the types of test cases you can write for a quantum circuit defined in an OpenQASM file. These tests help ensure the circuit is correctly structured and behaves as expected.

Here are several categories of tests:

1.  **Circuit Structure Validation:**
    *   **Qubit/Clbit Count:** Verify that the circuit uses the expected number of quantum bits (`num_qubits`) and classical bits (`num_clbits`).
    *   **Gate Set:** Check if the circuit only uses gates from an allowed or expected set (e.g., standard gates like `H`, `CX`, `U3`, `measure`, or custom defined gates).
    *   **Circuit Depth:** Measure the depth of the circuit and assert it's within expected bounds (useful for hardware constraints).
    *   **Gate Count:** Count specific types of gates (e.g., number of CNOTs) if relevant for resource estimation or complexity analysis.
    *   **Measurement Operations:** Ensure measurements are placed correctly, targeting the right qubits and storing results in the expected classical bits.
    *   **Absence of Classical Control (if expected):** Verify that gates are not classically controlled if the algorithm doesn't require it.
    *   **QASM Syntax:** While often implicitly checked when loading the file (e.g., `QuantumCircuit.from_qasm_file` will raise errors on invalid syntax), you could have a test explicitly confirming the file parses correctly against a specific OpenQASM version standard.

2.  **Circuit Behavior Simulation:**
    *   **Statevector Simulation:** For smaller circuits, use a `statevector_simulator`. Prepare a known input state, run the simulation, and compare the resulting statevector to a theoretically calculated expected statevector.
    *   **Measurement Outcome Distribution:** Use a `qasm_simulator` to run the circuit multiple times (shots).
        *   **Probability Checks:** Compare the resulting probability distribution (`counts`) of measured bitstrings against the expected theoretical probabilities. This is crucial for verifying probabilistic algorithms.
        *   **Deterministic Checks:** For circuits designed to produce a specific output state with high probability (e.g., initializing a state, simple arithmetic), verify that the most frequent outcome matches the expected one.
        *   **Specific Input States:** Test the circuit's behavior with various initial states (e.g., all |0>, all |1>, superposition states) and verify the outputs.

3.  **Algorithm-Specific Functional Tests:**
    *   If the QASM circuit implements a specific algorithm (like Grover's search, Shor's factoring, VQE ansatz, etc.), design tests to verify its core function.
        *   **Example (Shor's):** Does the circuit, when run, yield results that allow factoring the target number with appropriate probability?
        *   **Example (Grover's):** Does the simulation show a high probability of measuring the marked state(s)?

4.  **Equivalence Testing:**
    *   Compare the loaded circuit against a programmatically generated reference circuit that *should* be equivalent. Qiskit's `Operator` class can be used to get the unitary matrix for each circuit and compare them (within numerical tolerance). This is computationally intensive for larger circuits.

5.  **Visualization Checks (Qualitative):**
    *   Generate a drawing of the circuit (`qc.draw()`). While hard to automate assertions on the visual output itself, you can test that the drawing function executes without errors. This helps catch issues that might only be apparent visually. (As seen in your `test_visualization_circuit_gates` example).

The test file you provided (`test_shors_factoring_15_compatible_mitigated_zne.py`) already demonstrates good examples of **Circuit Structure Validation** (`test_circuit_structure`) and **Circuit Behavior Simulation** (`test_circuit_behavior`). You can expand on these based on the specific properties and goals of your quantum circuit.



Based on the README_TEST.md file, here are the types of test cases you can write for an OpenQASM-based quantum circuit:

1. **Circuit Structure Validation**:
   - Qubit/clbit count verification
   - Gate set validation
   - Circuit depth measurement
   - Gate count analysis
   - Measurement operations placement
   - Classical control verification
   - QASM syntax checking

2. **Circuit Behavior Simulation**:
   - Statevector simulation for smaller circuits
   - Measurement outcome distribution tests
   - Probability distribution verification
   - Deterministic output checking
   - Testing with various initial states

3. **Algorithm-Specific Functional Tests**:
   - Tests specific to the quantum algorithm being implemented
   - Verification of expected outcomes for algorithms like Grover's, Shor's, etc.

4. **Equivalence Testing**:
   - Comparing with programmatically generated reference circuits
   - Unitary matrix comparison using Qiskit's Operator class

5. **Visualization Checks**:
   - Testing that circuit drawing functions work without errors



Here are additional test cases missing from the list:

1. **Hardware-Specific Compatibility Tests**:
   - Testing compliance with hardware connectivity constraints
   - Gate fidelity validation on specific quantum processors
   - Testing transpiled circuits against target hardware

2. **Noise Simulation Tests**:
   - Circuit performance under different noise models
   - Error mitigation technique validation
   - Robustness against decoherence

3. **Parameterized Circuit Tests**:
   - Testing circuits with variable parameters
   - Gradient calculation verification
   - Parameter optimization validation

4. **Circuit Optimization Tests**:
   - Circuit transpilation validation
   - Gate cancellation verification
   - Circuit depth reduction verification

5. **Edge Case Testing**:
   - Zero-qubit circuits
   - Maximum qubit capacity
   - Empty gate sequences
   - Boundary condition handling

6. **Integration Tests**:
   - Hybrid quantum-classical workflow validation
   - Testing circuit as part of larger algorithms
   - API integration with classical systems


The provided `README_TEST.md` covers many important categories, but there are still some additional test cases and categories that could enhance your testing strategy:

### ✅ **Missing Test Categories and Cases:**

### 1. **Error Handling and Negative Tests**
- **Invalid Gate Usage:** Verify that the circuit correctly raises errors when invalid gates or parameters are used.
- **Incorrect Qubit/Clbit Indexing:** Ensure proper exceptions are raised when referencing non-existent qubits or classical bits.
- **Malformed QASM Files:** Explicitly test parsing failures with intentionally malformed QASM syntax.

### 2. **Parameterized Circuit Tests**
- **Parameter Bounds:** Test circuits with parameters at their boundary values (e.g., angles at \(0\), \(2\pi\), negative angles).
- **Parameter Sweeps:** Verify circuit behavior across a range of parameter values.

### 3. **Noise and Error Mitigation Tests**
- **Noise Model Integration:** Simulate circuits under realistic noise models (e.g., depolarizing, amplitude damping).
- **Error Mitigation Techniques:** Validate effectiveness of error mitigation methods (e.g., Zero Noise Extrapolation, Measurement Error Mitigation).

### 4. **Hardware Compatibility and Transpilation Tests**
- **Transpilation Validation:** Ensure circuits transpile correctly to specific hardware backends.
- **Hardware Constraints:** Verify circuits adhere to hardware-specific constraints (e.g., coupling maps, gate sets).

### 5. **Performance and Scalability Tests**
- **Execution Time:** Measure and assert acceptable execution times for simulation and transpilation.
- **Resource Usage:** Monitor memory and CPU usage during circuit simulation and transpilation.

### 6. **Integration and End-to-End Tests**
- **Quantum-Classical Integration:** Test integration points between quantum circuits and classical post-processing logic.
- **End-to-End Workflow:** Validate the entire workflow from circuit definition, transpilation, execution, to result analysis.

### 7. **Regression Tests**
- **Regression Suite:** Maintain tests that ensure previously fixed bugs or issues do not reoccur.

### 8. **Documentation and Metadata Tests**
- **Circuit Metadata:** Verify that circuit metadata (e.g., annotations, comments, author information) is correctly parsed and preserved.

Adding these categories and test cases will significantly enhance the robustness, reliability, and maintainability of your quantum circuit testing strategy.




# Testing Quantum Circuits

This guide outlines comprehensive testing strategies for quantum circuits defined in OpenQASM files. Effective testing ensures circuits are correctly structured and behave as expected across different environments and conditions.

## Testing Categories

### 1. Circuit Structure Validation

Tests that verify the static properties and composition of quantum circuits:

- **Qubit/Clbit Count:** Verify that the circuit uses the expected number of quantum bits (`num_qubits`) and classical bits (`num_clbits`).
- **Gate Set Analysis:** Check if the circuit only uses gates from an allowed or expected set (e.g., standard gates like `H`, `CX`, `U3`).
- **Circuit Depth:** Measure the depth of the circuit and assert it's within expected bounds (critical for hardware constraints).
- **Gate Count:** Count specific types of gates (e.g., number of CNOTs) for resource estimation or complexity analysis.
- **Measurement Operations:** Ensure measurements are correctly placed, targeting the right qubits and storing results in the expected classical bits.
- **Classical Control Verification:** Validate that classical control flow is implemented correctly (or absent if not required).
- **QASM Syntax:** Confirm the file parses correctly against the target OpenQASM version standard.

### 2. Circuit Behavior Simulation

Tests that validate dynamic behavior through simulation:

- **Statevector Simulation:** For smaller circuits, prepare known input states and compare resulting statevectors against theoretical calculations.
- **Measurement Outcome Distribution:** Run the circuit multiple times (shots) using a `qasm_simulator` to check:
  - **Probability Distribution:** Compare measured bitstring probabilities against expected theoretical distributions
  - **Deterministic Outcomes:** Verify that circuits designed for specific outputs produce expected results
  - **Input State Variation:** Test circuit behavior with various initial states (e.g., |0⟩, |1⟩, superpositions)

### 3. Algorithm-Specific Functional Tests

Tests tailored to the quantum algorithm implemented by the circuit:

- **Algorithm Correctness:** Verify the core function of specific algorithms:
  - **Grover's Search:** Confirm high probability of measuring marked states
  - **Shor's Algorithm:** Validate results allow factoring with appropriate probability
  - **VQE:** Check convergence to ground state energy
- **Expected Outputs:** Validate that algorithm-specific output patterns match theoretical predictions

### 4. Equivalence Testing

Tests that compare circuits against reference implementations:

- **Reference Circuit Comparison:** Compare against programmatically generated reference circuits
- **Unitary Matrix Equivalence:** Use Qiskit's `Operator` class to compare unitary matrices of circuits (within numerical tolerance)
- **Transformation Invariance:** Verify that circuit behavior remains consistent after valid transformations

### 5. Hardware Compatibility Tests

Tests that ensure circuits can run on target quantum hardware:

- **Connectivity Constraints:** Verify compliance with hardware coupling maps
- **Native Gate Set:** Confirm circuit uses only gates available on target hardware
- **Transpilation Validation:** Ensure circuits transpile correctly to specific hardware backends
- **Gate Fidelity:** Validate gates against known fidelity metrics for target processors

### 6. Noise and Error Mitigation Tests

Tests for circuit robustness under realistic conditions:

- **Noise Model Simulation:** Test circuit performance under various noise models (depolarizing, amplitude damping)
- **Error Mitigation Effectiveness:** Validate techniques like Zero Noise Extrapolation and Measurement Error Mitigation
- **Decoherence Robustness:** Test circuit behavior with varying T1/T2 times
- **Shot Noise Analysis:** Verify results stability across different numbers of shots

### 7. Parameterized Circuit Tests

Tests for circuits with variable parameters:

- **Parameter Bounds:** Test circuits with parameters at boundary values (e.g., angles at 0, 2π, negative angles)
- **Parameter Sweeps:** Verify circuit behavior across ranges of parameter values
- **Gradient Calculation:** Validate parameter shift rules and gradient computation
- **Optimization Trajectories:** Test parameter optimization convergence patterns

### 8. Circuit Optimization Tests

Tests that validate circuit optimization techniques:

- **Transpilation Optimization:** Verify circuit properties after optimization passes
- **Gate Cancellation:** Confirm redundant gates are properly eliminated
- **Circuit Depth Reduction:** Validate depth minimization while preserving functionality
- **Resource Estimation:** Compare resource requirements before and after optimization

### 9. Edge Case Testing

Tests that verify behavior in extreme or unusual conditions:

- **Qubit Capacity:** Test circuits at minimum and maximum qubit capacities
- **Empty Sequences:** Validate behavior with empty gate sequences
- **Boundary Conditions:** Check circuit behavior at computational limits
- **Malformed Inputs:** Explicitly test error handling with invalid inputs

### 10. Error Handling and Negative Tests

Tests that verify proper error responses:

- **Invalid Gate Usage:** Verify appropriate errors for invalid gates or parameters
- **Incorrect Indexing:** Ensure proper exceptions when referencing non-existent qubits/clbits
- **Malformed QASM Files:** Test parsing failures with intentionally malformed syntax
- **Resource Limits:** Verify graceful handling when exceeding available resources

### 11. Performance and Scalability Tests

Tests that measure computational efficiency:

- **Execution Time:** Benchmark and assert acceptable execution times
- **Memory Usage:** Monitor memory consumption during simulation
- **Scaling Behavior:** Measure how performance scales with circuit size
- **Resource Utilization:** Profile CPU/GPU usage during simulation

### 12. Integration and End-to-End Tests

Tests that validate complete workflows:

- **Quantum-Classical Integration:** Test integration between quantum circuits and classical processing
- **End-to-End Workflows:** Validate complete pipelines from circuit definition to result analysis
- **API Integration:** Test interoperability with classical systems and frameworks
- **Hybrid Algorithm Verification:** Validate quantum-classical hybrid algorithms

### 13. Visualization and Metadata Tests

Tests for supplementary features:

- **Circuit Visualization:** Verify circuit drawing functions work correctly
- **Metadata Preservation:** Confirm circuit metadata (annotations, comments) is preserved
- **Documentation Validation:** Verify that circuit documentation matches implementation
- **Result Visualization:** Test plotting and visualization of circuit outcomes

## Best Practices

- **Test Isolation:** Ensure tests are independent and don't affect each other
- **Deterministic Testing:** Make tests reproducible with fixed random seeds when appropriate
- **Comprehensive Coverage:** Include tests from multiple categories for robust validation
- **Continuous Integration:** Automate tests to run on code changes
- **Regression Testing:** Maintain tests for previously fixed issues to prevent recurrence

## Example Test Implementation

```python
def test_circuit_structure(qasm_file):
    """Test the structure of a circuit loaded from a QASM file."""
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Basic structure validation
    assert circuit.num_qubits == 4, "Circuit should use 4 qubits"
    assert circuit.num_clbits == 4, "Circuit should use 4 classical bits"
    
    # Gate set validation
    gate_counts = circuit.count_ops()
    assert 'h' in gate_counts, "Circuit should contain Hadamard gates"
    assert gate_counts.get('cx', 0) > 0, "Circuit should contain CNOT gates"
    
    # Circuit depth check
    assert circuit.depth() <= 50, "Circuit depth exceeds hardware constraints"
```

Implementing these test categories will significantly enhance the robustness, reliability, and maintainability of your quantum circuits.



The image shows several testing categories that aren't explicitly covered in our current testing list. Here are the key additions needed:

1. **Adversarial Testing** - Testing quantum algorithms against worst-case inputs or adversarial conditions

2. **Benchmarking Tests**:
   - **Against Classical Algorithms** - Comparing quantum circuit performance with classical counterparts
   - **Standard Benchmarks** - Using established quantum computing benchmarks for comparison

3. **State Preparation Tests** - Specifically focused on validating quantum state initialization 

4. **Error Correction Tests** - Going beyond error mitigation to test actual quantum error correction codes

5. **Quantum Subroutines Tests** - Testing modular components of larger quantum algorithms

6. **Logical Consistency Tests** - Verifying logical operations and consistency of quantum logic

7. **Backwards Compatibility Tests** - Testing compatibility with previous versions of quantum frameworks

8. **Monte Carlo Simulations** - Using statistical sampling methods specifically for quantum circuit testing

9. **Randomized Testing** - Applying random inputs and configurations to test circuit robustness



Here's the updated comprehensive list including all testing categories:

```markdown
# Testing Quantum Circuits

This guide outlines comprehensive testing strategies for quantum circuits defined in OpenQASM files. Effective testing ensures circuits are correctly structured and behave as expected across different environments and conditions.

## Testing Categories

### 1. Circuit Structure Validation
- **Qubit/Clbit Count:** Verify that the circuit uses the expected number of quantum bits (`num_qubits`) and classical bits (`num_clbits`).
- **Gate Set Analysis:** Check if the circuit only uses gates from an allowed or expected set.
- **Circuit Depth:** Measure the depth of the circuit and assert it's within expected bounds.
- **Gate Count:** Count specific types of gates for resource estimation or complexity analysis.
- **Measurement Operations:** Ensure measurements are correctly placed and targeted.
- **Classical Control Verification:** Validate that classical control flow is implemented correctly.
- **QASM Syntax:** Confirm the file parses correctly against the target OpenQASM version standard.

### 2. Circuit Behavior Simulation
- **Statevector Simulation:** Compare resulting statevectors against theoretical calculations.
- **Measurement Outcome Distribution:** Verify probability distributions match theoretical expectations.
- **Deterministic Outcomes:** Verify that circuits designed for specific outputs produce expected results.
- **Input State Variation:** Test circuit behavior with various initial states.

### 3. Algorithm-Specific Functional Tests
- **Algorithm Correctness:** Verify the core function of specific algorithms (Grover's, Shor's, VQE, etc.).
- **Expected Outputs:** Validate that algorithm-specific output patterns match theoretical predictions.

### 4. Equivalence Testing
- **Reference Circuit Comparison:** Compare against programmatically generated reference circuits.
- **Unitary Matrix Equivalence:** Compare unitary matrices of circuits within numerical tolerance.
- **Transformation Invariance:** Verify that circuit behavior remains consistent after valid transformations.

### 5. Hardware Compatibility Tests
- **Connectivity Constraints:** Verify compliance with hardware coupling maps.
- **Native Gate Set:** Confirm circuit uses only gates available on target hardware.
- **Transpilation Validation:** Ensure circuits transpile correctly to specific hardware backends.
- **Gate Fidelity:** Validate gates against known fidelity metrics for target processors.

### 6. Noise and Error Mitigation Tests
- **Noise Model Simulation:** Test circuit performance under various noise models.
- **Error Mitigation Effectiveness:** Validate techniques like Zero Noise Extrapolation.
- **Decoherence Robustness:** Test circuit behavior with varying T1/T2 times.
- **Shot Noise Analysis:** Verify results stability across different numbers of shots.

### 7. Parameterized Circuit Tests
- **Parameter Bounds:** Test circuits with parameters at boundary values.
- **Parameter Sweeps:** Verify circuit behavior across ranges of parameter values.
- **Gradient Calculation:** Validate parameter shift rules and gradient computation.
- **Optimization Trajectories:** Test parameter optimization convergence patterns.

### 8. Circuit Optimization Tests
- **Transpilation Optimization:** Verify circuit properties after optimization passes.
- **Gate Cancellation:** Confirm redundant gates are properly eliminated.
- **Circuit Depth Reduction:** Validate depth minimization while preserving functionality.
- **Resource Estimation:** Compare resource requirements before and after optimization.

### 9. Edge Case Testing
- **Qubit Capacity:** Test circuits at minimum and maximum qubit capacities.
- **Empty Sequences:** Validate behavior with empty gate sequences.
- **Boundary Conditions:** Check circuit behavior at computational limits.
- **Malformed Inputs:** Explicitly test error handling with invalid inputs.

### 10. Error Handling and Negative Tests
- **Invalid Gate Usage:** Verify appropriate errors for invalid gates or parameters.
- **Incorrect Indexing:** Ensure proper exceptions when referencing non-existent qubits/clbits.
- **Malformed QASM Files:** Test parsing failures with intentionally malformed syntax.
- **Resource Limits:** Verify graceful handling when exceeding available resources.

### 11. Performance and Scalability Tests
- **Execution Time:** Benchmark and assert acceptable execution times.
- **Memory Usage:** Monitor memory consumption during simulation.
- **Scaling Behavior:** Measure how performance scales with circuit size.
- **Resource Utilization:** Profile CPU/GPU usage during simulation.
- **Comparative Benchmark Analysis:** Compare against baseline performance metrics.

### 12. Integration and End-to-End Tests
- **Quantum-Classical Integration:** Test integration between quantum circuits and classical processing.
- **End-to-End Workflows:** Validate complete pipelines from circuit definition to result analysis.
- **API Integration:** Test interoperability with classical systems and frameworks.
- **Hybrid Algorithm Verification:** Validate quantum-classical hybrid algorithms.
- **Data Exchange Validation:** Ensure proper data flow between classical and quantum components.
- **Synchronization Testing:** Verify timing and coordination between system components.

### 13. Visualization and Metadata Tests
- **Circuit Visualization:** Verify circuit drawing functions work correctly.
- **Metadata Preservation:** Confirm circuit metadata is preserved.
- **Documentation Validation:** Verify that circuit documentation matches implementation.
- **Result Visualization:** Test plotting and visualization of circuit outcomes.

### 14. Adversarial Testing
- **Worst-Case Inputs:** Test circuits against worst-case input states.
- **Edge Condition Handling:** Verify behavior under adversarial conditions.
- **Resilience Testing:** Evaluate algorithm robustness against targeted perturbations.

### 15. Benchmarking Tests
- **Classical Algorithm Comparison:** Compare quantum circuit performance with classical counterparts.
- **Standard Quantum Benchmarks:** Use established quantum computing benchmarks.
- **Cross-Framework Benchmarking:** Compare performance across different quantum frameworks.

### 16. State Preparation Tests
- **Initialization Validation:** Verify correct preparation of specific quantum states.
- **Fidelity Measurement:** Quantify the fidelity of prepared states.
- **State Evolution:** Track state changes throughout circuit execution.

### 17. Quantum State Tomography
- **Automated State Reconstruction:** Reconstruct quantum states from measurement data.
- **Validation Against Expected States:** Compare reconstructed states with theoretical predictions.
- **Tomography Protocol Testing:** Verify the tomography procedure itself.

### 18. Noise Characterization
- **Hardware Noise Measurement:** Measure and analyze noise characteristics of quantum hardware.
- **Automated Noise Pattern Detection:** Identify and classify noise patterns.
- **Noise Spectroscopy:** Analyze frequency-dependent noise properties.
- **Cross-Talk Analysis:** Measure and characterize inter-qubit interference.

### 19. Error Correction Tests
- **Code Validation:** Test quantum error correction codes.
- **Syndrome Measurement:** Verify syndrome detection and processing.
- **Fault Tolerance:** Test threshold behavior of error correction methods.
- **Recovery Operations:** Validate error recovery procedures.

### 20. Quantum Subroutines Tests
- **Module Testing:** Validate modular components of larger quantum algorithms.
- **Interface Validation:** Test inputs/outputs of quantum subroutines.
- **Composition Testing:** Verify correct behavior when subroutines are combined.

### 21. Logical Consistency Tests
- **Logical Operation Verification:** Test quantum logic gates and operations.
- **Truth Table Validation:** Verify logical operations match expected truth tables.
- **Logical State Evolution:** Track logical states through circuit execution.

### 22. Backwards Compatibility Tests
- **Framework Version Testing:** Ensure compatibility with previous quantum framework versions.
- **QASM Version Compatibility:** Test compatibility across different OpenQASM versions.
- **Hardware Generation Compatibility:** Verify circuits work across hardware generations.

### 23. Monte Carlo Simulations
- **Statistical Sampling:** Apply Monte Carlo methods to quantum circuit testing.
- **Convergence Analysis:** Verify results converge to expected values.
- **Uncertainty Quantification:** Measure confidence intervals for simulation results.

### 24. Randomized Testing
- **Random Input States:** Test with randomly generated input states.
- **Random Circuit Generation:** Test randomly constructed circuit variations.
- **Stochastic Parameter Selection:** Verify behavior with randomly selected parameters.

## Best Practices

- **Test Isolation:** Ensure tests are independent and don't affect each other.
- **Deterministic Testing:** Make tests reproducible with fixed random seeds when appropriate.
- **Comprehensive Coverage:** Include tests from multiple categories for robust validation.
- **Continuous Integration:** Automate tests to run on code changes.
- **Regression Testing:** Maintain tests for previously fixed issues to prevent recurrence.
- **Progressive Complexity:** Start with simple tests and progressively add complexity.
- **Hardware-in-the-Loop Testing:** Include real quantum hardware in testing pipelines when possible.

## Example Test Implementation

```python
def test_circuit_structure(qasm_file):
    """Test the structure of a circuit loaded from a QASM file."""
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Basic structure validation
    assert circuit.num_qubits == 4, "Circuit should use 4 qubits"
    assert circuit.num_clbits == 4, "Circuit should use 4 classical bits"
    
    # Gate set validation
    gate_counts = circuit.count_ops()
    assert 'h' in gate_counts, "Circuit should contain Hadamard gates"
    assert gate_counts.get('cx', 0) > 0, "Circuit should contain CNOT gates"
    
    # Circuit depth check
    assert circuit.depth() <= 50, "Circuit depth exceeds hardware constraints"
```

Implementing these comprehensive test categories will significantly enhance the robustness, reliability, and maintainability of your quantum circuits.
```




# Comprehensive Guide to Testing Quantum Circuits

This guide provides detailed testing strategies for quantum circuits with concrete examples for each category.

## 1. Circuit Structure Validation

### 1.1 Qubit/Clbit Count
**Description:** Verify the circuit uses the expected number of quantum and classical bits.

**Example:**
```python
def test_qubit_clbit_count(qasm_file):
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Validate quantum and classical bit counts
    assert circuit.num_qubits == 4, f"Expected 4 qubits, found {circuit.num_qubits}"
    assert circuit.num_clbits == 4, f"Expected 4 classical bits, found {circuit.num_clbits}"
```

### 1.2 Gate Set Analysis
**Description:** Validate that the circuit only uses gates from an allowed or expected set.

**Example:**
```python
def test_gate_set(qasm_file):
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Get operation counts
    ops = circuit.count_ops()
    
    # Define allowed gates
    allowed_gates = {'h', 'cx', 'x', 'measure', 'barrier'}
    
    # Check all operations are in allowed set
    for gate in ops:
        assert gate in allowed_gates, f"Unauthorized gate '{gate}' found in circuit"
    
    # Check required gates are present
    assert 'h' in ops, "Circuit should contain at least one Hadamard gate"
    assert 'cx' in ops, "Circuit should contain at least one CNOT gate"
```

### 1.3 Circuit Depth
**Description:** Ensure the circuit depth is within constraints, which is crucial for hardware implementation.

**Example:**
```python
def test_circuit_depth(qasm_file):
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Calculate circuit depth
    depth = circuit.depth()
    
    # Check against maximum allowed depth
    max_depth = 50  # Example constraint
    assert depth <= max_depth, f"Circuit depth ({depth}) exceeds maximum allowed ({max_depth})"
    
    # Check if depth is within expected range
    min_depth = 5  # Example minimum expected depth
    assert depth >= min_depth, f"Circuit depth ({depth}) is less than minimum expected ({min_depth})"
```

### 1.4 Gate Count
**Description:** Count specific gates to ensure resource requirements are within expected bounds.

**Example:**
```python
def test_gate_count(qasm_file):
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    ops = circuit.count_ops()
    
    # Check CNOT count (important for resource estimation)
    cx_count = ops.get('cx', 0)
    assert cx_count <= 20, f"Too many CNOT gates ({cx_count}), maximum allowed is 20"
    
    # Check total gate count
    total_gates = sum(ops.values())
    assert total_gates <= 100, f"Total gate count ({total_gates}) exceeds maximum allowed (100)"
```

### 1.5 Measurement Operations
**Description:** Verify measurements are correctly placed and target the right qubits/classical bits.

**Example:**
```python
def test_measurement_operations(qasm_file):
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Get all instructions
    measure_ops = [op for op, qargs, cargs in circuit.data if op.name == 'measure']
    
    # Verify measurement count
    assert len(measure_ops) == 4, f"Expected 4 measurement operations, found {len(measure_ops)}"
    
    # Check if specific qubits are measured
    measured_qubits = {qargs[0].index for op, qargs, cargs in circuit.data 
                      if op.name == 'measure'}
    assert measured_qubits == {0, 1, 2, 3}, f"Not all required qubits are measured: {measured_qubits}"
```

## 2. Circuit Behavior Simulation

### 2.1 Statevector Simulation
**Description:** For smaller circuits, simulate the statevector and compare with theoretical expectations.

**Example:**
```python
from qiskit import Aer, transpile
import numpy as np

def test_statevector_simulation(qasm_file):
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Remove measurement to get pure statevector
    circuit_without_measure = circuit.remove_final_measurements(inplace=False)
    
    # Run statevector simulation
    simulator = Aer.get_backend('statevector_simulator')
    transpiled = transpile(circuit_without_measure, simulator)
    result = simulator.run(transpiled).result()
    statevector = result.get_statevector()
    
    # For example, testing a Bell state |00⟩ + |11⟩ / √2
    expected_sv = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)])
    assert np.allclose(statevector, expected_sv, atol=1e-7), \
        f"Statevector {statevector} doesn't match expected {expected_sv}"
```

### 2.2 Measurement Outcome Distribution
**Description:** Verify the distribution of measurement outcomes matches theoretical probabilities.

**Example:**
```python
def test_measurement_distribution(qasm_file):
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Run on QASM simulator with many shots
    simulator = Aer.get_backend('qasm_simulator')
    transpiled = transpile(circuit, simulator)
    result = simulator.run(transpiled, shots=8192).result()
    counts = result.get_counts()
    
    # For a Bell state, expect roughly equal '00' and '11' counts
    total_shots = sum(counts.values())
    prob_00 = counts.get('00', 0) / total_shots
    prob_11 = counts.get('11', 0) / total_shots
    
    # Allow for statistical fluctuations (3 sigma for 8192 shots gives ~3.3% tolerance)
    tolerance = 0.033
    assert abs(prob_00 - 0.5) < tolerance, f"Probability of '00' ({prob_00}) differs from expected (0.5)"
    assert abs(prob_11 - 0.5) < tolerance, f"Probability of '11' ({prob_11}) differs from expected (0.5)"
```

### 2.3 Deterministic Outcomes
**Description:** For circuits designed to produce specific outputs, verify the most frequent outcome.

**Example:**
```python
def test_deterministic_outcome(qasm_file):
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Run simulation
    simulator = Aer.get_backend('qasm_simulator')
    transpiled = transpile(circuit, simulator)
    result = simulator.run(transpiled, shots=1024).result()
    counts = result.get_counts()
    
    # Find most frequent outcome
    most_frequent = max(counts, key=counts.get)
    
    # For a circuit implementing X gates on all qubits, expect all 1s
    expected = '1' * circuit.num_clbits
    assert most_frequent == expected, \
        f"Most frequent outcome '{most_frequent}' doesn't match expected '{expected}'"
```

## 3. Algorithm-Specific Functional Tests

### 3.1 Algorithm Correctness - Grover's Algorithm
**Description:** Verify that Grover's search correctly amplifies the probability of finding marked states.

**Example:**
```python
def test_grovers_search(qasm_file):
    # Load Grover's search circuit targeting state '101'
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Run simulation
    simulator = Aer.get_backend('qasm_simulator')
    transpiled = transpile(circuit, simulator)
    result = simulator.run(transpiled, shots=1024).result()
    counts = result.get_counts()
    
    # Calculate probability of finding the marked state '101'
    total_shots = sum(counts.values())
    marked_state_prob = counts.get('101', 0) / total_shots
    
    # For 3 qubits with 1 iteration, theoretical probability is ~78.1%
    assert marked_state_prob > 0.7, \
        f"Probability of finding marked state '101' ({marked_state_prob}) is too low"
```

### 3.2 Algorithm Correctness - Quantum Fourier Transform
**Description:** Verify that QFT correctly transforms basis states to the Fourier basis.

**Example:**
```python
def test_qft_transformation(qasm_file):
    # Load QFT circuit
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Prepare input state |1⟩ (or modify circuit to initialize this)
    circuit_with_input = QuantumCircuit(circuit.num_qubits, circuit.num_clbits)
    circuit_with_input.x(0)  # Set first qubit to |1⟩
    circuit_with_input = circuit_with_input.compose(circuit)
    
    # Remove measurements for statevector
    circuit_no_measure = circuit_with_input.remove_final_measurements(inplace=False)
    
    # Simulate
    simulator = Aer.get_backend('statevector_simulator')
    result = simulator.run(transpile(circuit_no_measure, simulator)).result()
    final_state = result.get_statevector()
    
    # For 3-qubit QFT on |1⟩, expected amplitudes have specific phase pattern
    # Simplified check: ensure uniform magnitudes with varying phases
    magnitudes = np.abs(final_state)
    expected_mag = 1/np.sqrt(2**circuit.num_qubits)
    
    assert np.allclose(magnitudes, expected_mag, atol=1e-7), \
        "QFT output doesn't have uniform magnitudes as expected"
```

## 4. Equivalence Testing

### 4.1 Reference Circuit Comparison
**Description:** Compare the test circuit with a programmatically constructed reference circuit.

**Example:**
```python
def test_circuit_equivalence(qasm_file):
    # Load test circuit
    test_circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Construct reference Bell state circuit
    ref_circuit = QuantumCircuit(2, 2)
    ref_circuit.h(0)
    ref_circuit.cx(0, 1)
    ref_circuit.measure([0, 1], [0, 1])
    
    # Compare circuits using unitary matrices (removing measurements)
    test_no_measure = test_circuit.remove_final_measurements(inplace=False)
    ref_no_measure = ref_circuit.remove_final_measurements(inplace=False)
    
    from qiskit.quantum_info import Operator
    test_unitary = Operator(test_no_measure)
    ref_unitary = Operator(ref_no_measure)
    
    # Check if unitaries are equivalent up to global phase
    assert test_unitary.equiv(ref_unitary), "Circuits are not equivalent"
```

### 4.2 Unitary Matrix Equivalence
**Description:** Compare the unitary matrices of circuits to verify they implement the same transformation.

**Example:**
```python
from qiskit.quantum_info import Operator
import numpy as np

def test_unitary_equivalence(qasm_file):
    # Load circuit
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    circuit_no_measure = circuit.remove_final_measurements(inplace=False)
    
    # Get circuit unitary
    unitary = Operator(circuit_no_measure).data
    
    # Define expected unitary (e.g., for a Hadamard gate)
    expected_unitary = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
    
    # Compare unitaries (allowing for global phase difference)
    def unitaries_equivalent(U1, U2, tol=1e-7):
        # Check dimensions
        if U1.shape != U2.shape:
            return False
        # Find potential global phase
        ratio = U1[0, 0] / U2[0, 0]
        phase = np.angle(ratio)
        U2_adj = U2 * np.exp(1j * phase)
        return np.allclose(U1, U2_adj, atol=tol)
    
    assert unitaries_equivalent(unitary, expected_unitary), \
        "Circuit unitary doesn't match expected transformation"
```

## 5. Hardware Compatibility Tests

### 5.1 Connectivity Constraints
**Description:** Verify the circuit respects hardware coupling map constraints.

**Example:**
```python
def test_connectivity_constraints(qasm_file):
    # Load circuit
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Define coupling map (example for IBM Falcon architecture)
    coupling_map = [
        [0, 1], [1, 0], [1, 2], [2, 1], [2, 3], [3, 2], [3, 4], [4, 3]
    ]
    
    # Check all two-qubit gates respect connectivity
    for instr, qargs, _ in circuit.data:
        if len(qargs) == 2:  # Two-qubit gate
            q1, q2 = qargs[0].index, qargs[1].index
            assert [q1, q2] in coupling_map, \
                f"Two-qubit gate between {q1} and {q2} violates coupling constraints"
```

### 5.2 Native Gate Set
**Description:** Ensure the circuit uses only gates available in the target hardware's native gate set.

**Example:**
```python
def test_native_gate_set(qasm_file):
    # Load circuit
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Define IBM hardware native gates
    native_gates = {'id', 'rz', 'sx', 'x', 'cx', 'reset', 'measure', 'barrier'}
    
    # Check all gates are in native set
    for instr, _, _ in circuit.data:
        gate_name = instr.name
        assert gate_name in native_gates, \
            f"Gate '{gate_name}' is not in the native gate set {native_gates}"
```

## 6. Noise and Error Mitigation Tests

### 6.1 Noise Model Simulation
**Description:** Test circuit performance under realistic noise conditions.

**Example:**
```python
from qiskit.providers.aer.noise import NoiseModel
from qiskit.providers.aer.noise.errors import depolarizing_error, ReadoutError

def test_noise_resilience(qasm_file):
    # Load circuit
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Create noise model
    noise_model = NoiseModel()
    
    # Add depolarizing error to all gates
    depol_error = depolarizing_error(0.01, 1)  # 1% error on single-qubit gates
    depol_error_2 = depolarizing_error(0.05, 2)  # 5% error on two-qubit gates
    
    # Add readout error
    read_err = ReadoutError([[0.95, 0.05], [0.05, 0.95]])  # 5% chance of flipping 0→1 or 1→0
    
    # Add errors to noise model
    noise_model.add_all_qubit_quantum_error(depol_error, ['u1', 'u2', 'u3', 'x', 'h'])
    noise_model.add_all_qubit_quantum_error(depol_error_2, ['cx'])
    noise_model.add_all_qubit_readout_error(read_err)
    
    # Simulate with noise
    simulator = Aer.get_backend('qasm_simulator')
    result_noise = simulator.run(
        transpile(circuit, simulator),
        noise_model=noise_model,
        shots=8192
    ).result()
    counts_noise = result_noise.get_counts()
    
    # Simulate without noise
    result_ideal = simulator.run(transpile(circuit, simulator), shots=8192).result()
    counts_ideal = result_ideal.get_counts()
    
    # For a robust circuit, most frequent outcome should be the same with/without noise
    most_frequent_ideal = max(counts_ideal, key=counts_ideal.get)
    most_frequent_noise = max(counts_noise, key=counts_noise.get)
    
    assert most_frequent_ideal == most_frequent_noise, \
        f"Noise changes most frequent outcome from {most_frequent_ideal} to {most_frequent_noise}"
```

### 6.2 Error Mitigation - Zero Noise Extrapolation
**Description:** Test the effectiveness of zero-noise extrapolation for error mitigation.

**Example:**
```python
from qiskit.providers.aer.noise import NoiseModel
from qiskit.providers.aer.noise.errors import depolarizing_error

def test_zero_noise_extrapolation(qasm_file):
    # Load circuit
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Define noise model with depolarizing error
    noise_model = NoiseModel()
    error = depolarizing_error(0.01, 1)  # 1% error rate
    noise_model.add_all_qubit_quantum_error(error, ['u1', 'u2', 'u3', 'x', 'h'])
    
    # Run with different noise scaling factors
    simulator = Aer.get_backend('qasm_simulator')
    transpiled = transpile(circuit, simulator)
    
    # No noise
    result_ideal = simulator.run(transpiled, shots=8192).result()
    expectation_ideal = calculate_expectation(result_ideal.get_counts())
    
    # Scale 1x (base noise)
    result_noise_1x = simulator.run(transpiled, noise_model=noise_model, shots=8192).result()
    expectation_1x = calculate_expectation(result_noise_1x.get_counts())
    
    # Scale 2x (doubled noise)
    noise_model_2x = NoiseModel()
    error_2x = depolarizing_error(0.02, 1)  # 2% error rate
    noise_model_2x.add_all_qubit_quantum_error(error_2x, ['u1', 'u2', 'u3', 'x', 'h'])
    result_noise_2x = simulator.run(transpiled, noise_model=noise_model_2x, shots=8192).result()
    expectation_2x = calculate_expectation(result_noise_2x.get_counts())
    
    # Zero-noise extrapolation (linear)
    # Using the formula: E_mitigated = 2*E_1x - E_2x
    extrapolated = 2*expectation_1x - expectation_2x
    
    # Check if extrapolation improves accuracy
    error_raw = abs(expectation_ideal - expectation_1x)
    error_mitigated = abs(expectation_ideal - extrapolated)
    
    assert error_mitigated < error_raw, \
        f"ZNE didn't improve accuracy: raw error={error_raw}, mitigated error={error_mitigated}"

def calculate_expectation(counts):
    """Calculate expectation value of Z on first qubit."""
    prob_0 = sum(counts.get(b, 0) for b in counts if b[0] == '0')
    prob_1 = sum(counts.get(b, 0) for b in counts if b[0] == '1')
    total = prob_0 + prob_1
    return (prob_0 - prob_1) / total  # <Z> = P(0) - P(1)
```

## 7. Parameterized Circuit Tests

### 7.1 Parameter Sweeps
**Description:** Test circuit behavior across different parameter values.

**Example:**
```python
from qiskit.circuit import Parameter

def test_parameter_sweep(circuit_template_function):
    """Test a parameterized rotation gate with different angles."""
    # Create a parameterized circuit
    theta = Parameter('θ')
    
    # Build parametric circuit (e.g., from a template function)
    circuit = circuit_template_function(theta)
    
    # Test multiple parameter values
    angles = [0, np.pi/4, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi]
    results = {}
    
    simulator = Aer.get_backend('statevector_simulator')
    
    for angle in angles:
        # Bind parameter
        bound_circuit = circuit.bind_parameters({theta: angle})
        
        # Simulate
        result = simulator.run(transpile(bound_circuit, simulator)).result()
        statevector = result.get_statevector()
        
        # Store result
        results[angle] = statevector
    
    # Verify parameter = 0 gives |0⟩ state
    assert np.allclose(results[0], [1, 0]), f"θ=0 should give |0⟩, got {results[0]}"
    
    # Verify parameter = π gives |1⟩ state
    assert np.allclose(results[np.pi], [0, 1]), f"θ=π should give |1⟩, got {results[np.pi]}"
    
    # Verify parameter = π/2 gives (|0⟩+|1⟩)/√2
    expected_superposition = np.array([1, 1]) / np.sqrt(2)
    assert np.allclose(results[np.pi/2], expected_superposition), \
        f"θ=π/2 should give |+⟩, got {results[np.pi/2]}"
```

## 8. Quantum State Tomography

### 8.1 Automated State Reconstruction
**Description:** Reconstruct quantum states from measurement data and validate against expected states.

**Example:**
```python
from qiskit.ignis.verification.tomography import state_tomography_circuits, StateTomographyFitter

def test_state_tomography(qasm_file):
    # Load circuit that prepares the quantum state
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Remove any existing measurements
    circuit_no_measure = circuit.remove_final_measurements(inplace=False)
    
    # Generate tomography circuits
    qubits = list(range(circuit_no_measure.num_qubits))
    tomo_circuits = state_tomography_circuits(circuit_no_measure, qubits)
    
    # Run tomography circuits
    simulator = Aer.get_backend('qasm_simulator')
    transpiled_circuits = transpile(tomo_circuits, simulator)
    results = simulator.run(transpiled_circuits, shots=8192).result()
    
    # Perform state tomography
    tomo_fitter = StateTomographyFitter(results, tomo_circuits)
    rho = tomo_fitter.fit()
    
    # Define expected state (e.g., Bell state)
    from qiskit.quantum_info import state_fidelity, Statevector
    bell_state = Statevector.from_label('00') + Statevector.from_label('11')
    bell_state = bell_state.to_operator() / np.sqrt(2)
    
    # Calculate fidelity between reconstructed and expected state
    fidelity = state_fidelity(rho, bell_state)
    
    assert fidelity > 0.95, f"State tomography fidelity ({fidelity}) is below threshold"
```

## 9. Error Correction Tests

### 9.1 Bit-Flip Code Validation
**Description:** Test the effectiveness of quantum error correction codes.

**Example:**
```python
def test_bit_flip_code(bit_flip_encode_circuit, bit_flip_syndrome_circuit, bit_flip_recover_circuit):
    """Test 3-qubit bit-flip code against single bit-flip errors."""
    # Create full error correction process
    # 1. Encode logical |0⟩ using 3 physical qubits
    qc_encode = bit_flip_encode_circuit()
    
    # 2. Apply controlled bit-flip error to first qubit
    qc_with_error = qc_encode.copy()
    qc_with_error.x(0)  # Bit flip on first qubit
    
    # 3. Detect error syndrome
    qc_syndrome = bit_flip_syndrome_circuit()
    qc_full = qc_with_error.compose(qc_syndrome)
    
    # 4. Apply recovery operation
    qc_recovery = bit_flip_recover_circuit()
    qc_full = qc_full.compose(qc_recovery)
    
    # 5. Decode (reverse encoding)
    qc_decode = qc_encode.inverse()
    qc_full = qc_full.compose(qc_decode)
    
    # Simulate
    simulator = Aer.get_backend('statevector_simulator')
    final_state = simulator.run(transpile(qc_full, simulator)).result().get_statevector()
    
    # Check that we recovered |0⟩ state
    assert np.allclose(final_state, [1, 0]), \
        f"Error correction failed to recover |0⟩ state, got {final_state}"
```

## 10. Monte Carlo Simulations

### 10.1 Statistical Sampling
**Description:** Use Monte Carlo methods to estimate and validate quantum circuit properties.

**Example:**
```python
def test_monte_carlo_estimation(qasm_file):
    """Use Monte Carlo to estimate expectation value with confidence intervals."""
    # Load circuit
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Setup simulator
    simulator = Aer.get_backend('qasm_simulator')
    transpiled = transpile(circuit, simulator)
    
    # Define number of trials and shots per trial
    n_trials = 30
    shots_per_trial = 1024
    
    # Run multiple trials
    z_expectation_values = []
    
    for _ in range(n_trials):
        result = simulator.run(transpiled, shots=shots_per_trial).result()
        counts = result.get_counts()
        
        # Calculate <Z> for first qubit
        z_val = calculate_expectation(counts)
        z_expectation_values.append(z_val)
    
    # Calculate mean and standard error
    mean_z = np.mean(z_expectation_values)
    std_error = np.std(z_expectation_values, ddof=1) / np.sqrt(n_trials)
    
    # Define expected value and confidence level (95%)
    expected_z = 0.7  # Example expected value
    confidence_factor = 1.96  # 95% confidence
    
    # Check if expected value falls within confidence interval
    confidence_interval = (mean_z - confidence_factor*std_error, 
                           mean_z + confidence_factor*std_error)
    
    assert confidence_interval[0] <= expected_z <= confidence_interval[1], \
        f"Expected <Z>={expected_z} falls outside 95% CI {confidence_interval}"
```

## 11. Integration and End-to-End Tests

### 11.1 Quantum-Classical Integration
**Description:** Test the integration between quantum circuits and classical processing.

**Example:**
```python
def test_vqe_quantum_classical_integration(vqe_ansatz, classical_optimizer, hamiltonian):
    """Test Variational Quantum Eigensolver (VQE) quantum-classical integration."""
    # Define VQE ansatz circuit with parameters
    num_params = 6
    params = ParameterVector('theta', num_params)
    ansatz = vqe_ansatz(params)
    
    # Setup simulator
    simulator = Aer.get_backend('qasm_simulator')
    
    # Define cost function (energy calculation)
    def cost_function(parameter_values):
        # Bind parameters
        bound_circuit = ansatz.bind_parameters(
            {params[i]: parameter_values[i] for i in range(num_params)}
        )
        
        # Run quantum simulation
        transpiled = transpile(bound_circuit, simulator)
        result = simulator.run(transpiled, shots=4096).result()
        counts = result.get_counts()
        
        # Calculate energy from measurement results
        energy = calculate_energy(counts, hamiltonian)
        return energy
    
    # Run classical optimization
    initial_params = np.random.random(num_params) * 2 * np.pi
    opt_results = classical_optimizer(cost_function, initial_params)
    
    # Verify optimization converged
    assert opt_results.success, "Classical optimization failed to converge"
    
    # Verify final energy is close to ground state
    ground_state_energy = -1.0  # Example expected ground state
    final_energy = opt_results.fun
    
    assert abs(final_energy - ground_state_energy) < 0.1, \
        f"VQE energy ({final_energy}) not close to ground state ({ground_state_energy})"
```

This comprehensive guide provides detailed examples for the most important quantum circuit testing categories. Each example demonstrates specific testing techniques that can be adapted to your quantum circuits.



## 12. Adversarial and Security Tests

### 12.1 Quantum Cryptography Testing
**Description:** Test quantum cryptographic protocols for security and resistance to attacks.

**Example:**
```python
def test_bb84_protocol_security(qasm_file):
    """Test the BB84 quantum key distribution protocol against intercept-resend attacks."""
    # Load BB84 implementation circuit
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Normal execution simulation (no attack)
    simulator = Aer.get_backend('qasm_simulator')
    result_normal = simulator.run(transpile(circuit, simulator), shots=1024).result()
    counts_normal = result_normal.get_counts()
    
    # Simulate an intercept-resend attack by an eavesdropper
    # Create a modified circuit that represents the attack
    attack_circuit = circuit.copy()
    
    # Implement intercept-resend attack
    # Example: Add intermediate measurements and reset operations 
    # at the midpoint of the protocol
    midpoint = len(attack_circuit.data) // 2
    
    # Insert eavesdropper operations
    # Measure in random basis, then reinitialize
    for i in range(circuit.num_qubits):
        # Add random basis measurement (computational or Hadamard)
        if np.random.random() > 0.5:
            attack_circuit.h(i)
        attack_circuit.measure(i, i)
        attack_circuit.reset(i)
        # Re-prepare in the measured state (imperfect)
        # This simulates Eve trying to hide her presence
    
    # Simulate with attack
    result_attack = simulator.run(transpile(attack_circuit, simulator), shots=1024).result()
    counts_attack = result_attack.get_counts()
    
    # Compute quantum bit error rate (QBER)
    qber = compute_qber(counts_normal, counts_attack)
    
    # BB84 should detect eavesdropping via increased error rate
    assert qber > 0.15, f"Intercept-resend attack not detected, QBER too low: {qber}"
    
def compute_qber(counts_normal, counts_attack):
    """Compute quantum bit error rate between normal execution and attacked execution."""
    # Simplified QBER calculation for illustration
    # In a real implementation, would compare specific bits where bases match
    
    # Extract most frequent outcomes
    normal_outcome = max(counts_normal, key=counts_normal.get)
    attack_outcome = max(counts_attack, key=counts_attack.get)
    
    # Count bit differences
    bit_errors = sum(n != a for n, a in zip(normal_outcome, attack_outcome))
    
    # Calculate error rate
    return bit_errors / len(normal_outcome)
```

### 12.2 Fault Injection Testing
**Description:** Deliberately introduce faults to test robustness and error-handling capabilities.

**Example:**
```python
def test_fault_injection_robustness(qasm_file):
    """Test circuit robustness against deliberately injected faults."""
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Define fault injection points and types
    fault_types = [
        'bit_flip',      # X error
        'phase_flip',    # Z error
        'bit_phase_flip' # Y error
    ]
    
    # Baseline simulation without faults
    simulator = Aer.get_backend('qasm_simulator')
    result_normal = simulator.run(transpile(circuit, simulator), shots=4096).result()
    counts_normal = result_normal.get_counts()
    baseline_output = max(counts_normal, key=counts_normal.get)
    
    # Test circuit against each fault type
    fault_tolerance_results = {}
    
    for fault_type in fault_types:
        # Track success rate across multiple fault locations
        success_rates = []
        
        # Try fault at each location (each qubit, each gate)
        for qubit_idx in range(circuit.num_qubits):
            # Create a custom noise model for this fault
            noise_model = NoiseModel()
            
            # Configure the fault based on type
            if fault_type == 'bit_flip':
                # 100% probability X error on the target qubit
                error = depolarizing_error(1.0, 1)
                noise_model.add_quantum_error(error, ['x'], [qubit_idx])
            elif fault_type == 'phase_flip':
                # 100% probability Z error on the target qubit
                error = depolarizing_error(1.0, 1)
                noise_model.add_quantum_error(error, ['z'], [qubit_idx])
            elif fault_type == 'bit_phase_flip':
                # 100% probability Y error on the target qubit
                error = depolarizing_error(1.0, 1)
                noise_model.add_quantum_error(error, ['y'], [qubit_idx])
            
            # Run circuit with injected fault
            result_fault = simulator.run(
                transpile(circuit, simulator),
                noise_model=noise_model,
                shots=4096
            ).result()
            counts_fault = result_fault.get_counts()
            
            # Calculate success rate (probability of still getting correct output)
            correct_output_count = counts_fault.get(baseline_output, 0)
            success_rate = correct_output_count / 4096
            success_rates.append(success_rate)
        
        # Store average success rate for this fault type
        fault_tolerance_results[fault_type] = sum(success_rates) / len(success_rates)
    
    # Assess overall fault tolerance
    # For circuits with no inherent error correction, we expect poor tolerance
    # For circuits with error correction, we expect better tolerance
    
    # Example: For a circuit with bit-flip code, we expect better tolerance to bit flips
    if 'bit_flip_code' in qasm_file:
        assert fault_tolerance_results['bit_flip'] > 0.7, \
            f"Bit-flip code failed to mitigate bit-flip errors, success rate: {fault_tolerance_results['bit_flip']}"
    
    # For standard circuits, we just record the fault tolerance profile
    print(f"Fault tolerance profile: {fault_tolerance_results}")
    
    # At minimum, ensure results were collected successfully
    assert len(fault_tolerance_results) == len(fault_types), "Failed to complete fault injection tests"
```

### 12.3 Side-Channel Attack Testing
**Description:** Test resistance to side-channel attacks that attempt to extract information through timing, power, or other physical measurements.

**Example:**
```python
def test_constant_time_execution(qasm_file):
    """Test if circuit execution time is independent of secret data (timing side-channel)."""
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Create variations of the circuit with different inputs
    # Particularly inputs that should represent different "secret" values
    variations = []
    
    # For each qubit, create a variation with that qubit initialized to |1⟩
    for i in range(min(5, circuit.num_qubits)):  # Limit to first 5 qubits for practicality
        variation = QuantumCircuit(circuit.num_qubits, circuit.num_clbits)
        variation.x(i)  # Set qubit i to |1⟩
        variation = variation.compose(circuit)
        variations.append(variation)
    
    # Add base circuit (all |0⟩ inputs)
    variations.append(circuit)
    
    # Transpile all variations
    simulator = Aer.get_backend('qasm_simulator')
    transpiled_variations = [transpile(v, simulator) for v in variations]
    
    # Measure execution time for each variation
    import time
    execution_times = []
    
    for tv in transpiled_variations:
        start_time = time.time()
        # Run multiple times to get a stable measurement
        for _ in range(10):
            simulator.run(tv, shots=100).result()
        end_time = time.time()
        execution_times.append((end_time - start_time) / 10)  # Average time
    
    # Calculate statistical properties
    mean_time = np.mean(execution_times)
    std_dev = np.std(execution_times)
    
    # Assert that execution times are similar (within 2 standard deviations)
    max_deviation = max(abs(t - mean_time) for t in execution_times)
    
    assert max_deviation < 2 * std_dev, \
        f"Execution time varies significantly based on input, potential timing side-channel. Max deviation: {max_deviation}s"
```

### 12.4 Quantum Oracle Security Testing
**Description:** Test quantum oracles used in algorithms like Grover's search to ensure they don't leak additional information.

**Example:**
```python
def test_oracle_information_leakage(oracle_circuit_function):
    """Test if a quantum oracle leaks more information than intended."""
    # Create a Grover oracle for a specific marked state
    marked_state = '101'  # The secret we want to find
    oracle = oracle_circuit_function(marked_state)
    
    # Create a circuit that applies the oracle to a uniform superposition
    n_qubits = len(marked_state)
    circuit = QuantumCircuit(n_qubits)
    
    # Create uniform superposition
    circuit.h(range(n_qubits))
    
    # Apply oracle once
    circuit = circuit.compose(oracle)
    
    # We want to ensure a single oracle query doesn't give too much information
    # Measure the state
    circuit.measure_all()
    
    # Simulate
    simulator = Aer.get_backend('qasm_simulator')
    result = simulator.run(transpile(circuit, simulator), shots=8192).result()
    counts = result.get_counts()
    
    # Calculate probability of each outcome
    total_shots = sum(counts.values())
    probabilities = {state: count/total_shots for state, count in counts.items()}
    
    # For a secure oracle, probability of finding the marked state in one query 
    # should be close to random guessing (1/2^n)
    marked_prob = probabilities.get(marked_state, 0)
    random_guess_prob = 1 / (2**n_qubits)
    
    # Allow for some statistical fluctuation
    margin = 3 * np.sqrt(random_guess_prob * (1 - random_guess_prob) / total_shots)  # 3-sigma
    
    assert abs(marked_prob - random_guess_prob) <= margin, \
        f"Oracle leaks information: marked state probability {marked_prob} differs significantly from random {random_guess_prob}"
```

These examples demonstrate how to test quantum circuits for security vulnerabilities and their robustness against deliberately introduced faults. Such tests are crucial for quantum algorithms used in cryptography, secure communications, and other applications where security and reliability are paramount.
