# Testing Quantum Circuits

This guide outlines comprehensive testing strategies for quantum circuits defined in OpenQASM files. Effective testing ensures circuits are correctly structured and behave as expected across different environments and conditions.

## Introduction

Quantum circuits require thorough testing due to their probabilistic nature and sensitivity to noise. This document outlines testing strategies accessible to computer science graduates, even without extensive quantum computing background. Each section includes explanations and concrete Python examples using Qiskit.

## Testing Categories

### 1. Circuit Structure Validation

These tests verify the static properties and structure of quantum circuits without executing them.

#### 1.1 Qubit/Clbit Count

**What:** Verify the circuit uses the expected number of quantum and classical bits.

**Why:** Incorrect qubit/clbit counts can indicate missing components or implementation errors.

**Example:**
```python
def test_qubit_clbit_count(qasm_file):
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Validate quantum and classical bit counts
    assert circuit.num_qubits == 4, f"Expected 4 qubits, found {circuit.num_qubits}"
    assert circuit.num_clbits == 4, f"Expected 4 classical bits, found {circuit.num_clbits}"
```

#### 1.2 Gate Set Analysis

**What:** Check if the circuit only uses gates from an allowed or expected set.

**Why:** Unexpected gates might indicate incorrect implementation or compatibility issues with target hardware.

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

#### 1.3 Circuit Depth

**What:** Ensure the circuit depth is within acceptable limits.

**Why:** Circuit depth affects execution time and error rates on real quantum hardware, which has coherence time limitations.

**Example:**
```python
def test_circuit_depth(qasm_file):
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Calculate circuit depth
    depth = circuit.depth()
    
    # Check against maximum allowed depth
    max_depth = 50  # Example constraint
    assert depth <= max_depth, f"Circuit depth ({depth}) exceeds maximum allowed ({max_depth})"
```

#### 1.4 Gate Count

**What:** Count specific types of gates in the circuit.

**Why:** Gate counts impact resource requirements and execution time. Two-qubit gates (like CNOT) are especially important as they're typically more error-prone.

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

#### 1.5 Measurement Operations

**What:** Verify measurements are correctly placed and target the right qubits/classical bits.

**Why:** Incorrect measurement placement can lead to wrong or incomplete results.

**Example:**
```python
def test_measurement_operations(qasm_file):
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Get all measurement instructions
    measure_ops = [op for op, qargs, cargs in circuit.data if op.name == 'measure']
    
    # Verify measurement count
    assert len(measure_ops) == 4, f"Expected 4 measurement operations, found {len(measure_ops)}"
    
    # Check if specific qubits are measured
    measured_qubits = {qargs[0].index for op, qargs, cargs in circuit.data 
                      if op.name == 'measure'}
    assert measured_qubits == {0, 1, 2, 3}, f"Not all required qubits are measured: {measured_qubits}"
```

### 2. Circuit Behavior Simulation

These tests validate the dynamic behavior of quantum circuits through simulation.

#### 2.1 Statevector Simulation

**What:** For smaller circuits, simulate the quantum state vector and compare with theoretical expectations.

**Why:** Validates the quantum state evolution through the circuit, showing if the circuit produces the expected quantum state.

**Example:**
```python
import numpy as np
from qiskit import Aer, transpile

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

#### 2.2 Measurement Outcome Distribution

**What:** Verify the distribution of measurement outcomes matches theoretical probabilities.

**Why:** Quantum circuits are probabilistic - this test ensures the probability distribution of results aligns with expected behavior.

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

### 3. Algorithm-Specific Functional Tests

These tests verify that quantum algorithms implemented by the circuits function correctly.

#### 3.1 Grover's Algorithm Testing

**What:** Verify that Grover's search algorithm correctly amplifies the probability of finding marked states.

**Why:** Grover's algorithm should quadratically speedup search - this test verifies the correct quantum amplification behavior.

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

#### 3.2 Quantum Fourier Transform Testing

**What:** Verify that QFT correctly transforms basis states to the Fourier basis.

**Why:** QFT is a fundamental quantum algorithm that enables many other algorithms - it must correctly transform quantum states.

**Example:**
```python
def test_qft_transformation(qasm_file):
    # Load QFT circuit
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Prepare input state |1⟩
    circuit_with_input = QuantumCircuit(circuit.num_qubits, circuit.num_clbits)
    circuit_with_input.x(0)  # Set first qubit to |1⟩
    circuit_with_input = circuit_with_input.compose(circuit)
    
    # Remove measurements for statevector simulation
    circuit_no_measure = circuit_with_input.remove_final_measurements(inplace=False)
    
    # Simulate
    simulator = Aer.get_backend('statevector_simulator')
    result = simulator.run(transpile(circuit_no_measure, simulator)).result()
    final_state = result.get_statevector()
    
    # For QFT, validate uniform magnitudes with varying phases
    magnitudes = np.abs(final_state)
    expected_mag = 1/np.sqrt(2**circuit.num_qubits)
    
    assert np.allclose(magnitudes, expected_mag, atol=1e-7), \
        "QFT output doesn't have uniform magnitudes as expected"
```

### 4. Equivalence Testing

These tests compare circuits against reference implementations to verify correctness.

#### 4.1 Reference Circuit Comparison

**What:** Compare the test circuit with a programmatically constructed reference circuit.

**Why:** Ensures that a circuit matches a known-good implementation of the same functionality.

**Example:**
```python
from qiskit.quantum_info import Operator

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
    
    test_unitary = Operator(test_no_measure)
    ref_unitary = Operator(ref_no_measure)
    
    # Check if unitaries are equivalent up to global phase
    assert test_unitary.equiv(ref_unitary), "Circuits are not equivalent"
```

### 5. Hardware Compatibility Tests

These tests ensure circuits are compatible with real quantum hardware constraints.

#### 5.1 Connectivity Constraints

**What:** Verify the circuit respects hardware coupling map constraints.

**Why:** Real quantum processors have limited qubit connectivity - two-qubit gates can only operate on physically connected qubits.

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

#### 5.2 Native Gate Set

**What:** Ensure the circuit uses only gates available in the target hardware's native gate set.

**Why:** Quantum processors support a limited set of native gates - other gates must be decomposed into supported ones.

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

### 6. Noise and Error Mitigation Tests

These tests examine circuit behavior under realistic noise conditions.

#### 6.1 Noise Model Simulation

**What:** Test circuit performance under simulated noise conditions.

**Why:** Real quantum hardware has noise - this test helps predict how the circuit will perform in real environments.

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
    
    # Simulate without noise for comparison
    result_ideal = simulator.run(transpile(circuit, simulator), shots=8192).result()
    counts_ideal = result_ideal.get_counts()
    
    # For a robust circuit, most frequent outcome should be the same with/without noise
    most_frequent_ideal = max(counts_ideal, key=counts_ideal.get)
    most_frequent_noise = max(counts_noise, key=counts_noise.get)
    
    assert most_frequent_ideal == most_frequent_noise, \
        f"Noise changes most frequent outcome from {most_frequent_ideal} to {most_frequent_noise}"
```

#### 6.2 Error Mitigation - Zero Noise Extrapolation

**What:** Test the effectiveness of zero-noise extrapolation for error mitigation.

**Why:** Error mitigation techniques can improve quantum circuit results - this test validates their effectiveness.

**Example:**
```python
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
    
    # No noise (ideal)
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

### 7. Parameterized Circuit Tests

These tests verify circuits with variable parameters behave correctly across parameter values.

#### 7.1 Parameter Sweeps

**What:** Test circuit behavior across different parameter values.

**Why:** Many quantum algorithms use parameterized circuits - this test ensures they work correctly for all relevant parameter values.

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

### 8. Error Correction Tests

These tests verify quantum error correction codes function correctly.

#### 8.1 Bit-Flip Code Validation

**What:** Test the effectiveness of quantum error correction codes.

**Why:** Error correction is essential for fault-tolerant quantum computing - this test verifies error correction codes can detect and correct errors.

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

### 9. Integration and End-to-End Tests

These tests validate that quantum circuits work correctly within larger quantum-classical algorithms.

#### 9.1 Quantum-Classical Integration

**What:** Test the integration between quantum circuits and classical processing.

**Why:** Many quantum algorithms are hybrid quantum-classical - this test verifies the entire workflow functions correctly.

**Example:**
```python
def test_vqe_quantum_classical_integration(vqe_ansatz, classical_optimizer, hamiltonian):
    """Test Variational Quantum Eigensolver (VQE) quantum-classical integration."""
    from qiskit.circuit import ParameterVector
    
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

### 10. Quantum State Tomography

These tests reconstruct quantum states from measurement data to verify circuit behavior.

#### 10.1 State Reconstruction and Validation

**What:** Reconstruct quantum states from measurement data and compare with theoretical expectations.

**Why:** Tomography provides a complete characterization of the quantum state, offering deeper validation than simple measurements.

**Example:**
```python
from qiskit.ignis.verification.tomography import state_tomography_circuits, StateTomographyFitter
from qiskit.quantum_info import state_fidelity, Statevector

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
    bell_state = Statevector.from_label('00') + Statevector.from_label('11')
    bell_state = bell_state.to_operator() / np.sqrt(2)
    
    # Calculate fidelity between reconstructed and expected state
    fidelity = state_fidelity(rho, bell_state)
    
    assert fidelity > 0.95, f"State tomography fidelity ({fidelity}) is below threshold"
```

### 11. Monte Carlo Simulations

These tests use statistical sampling methods to estimate quantum properties with confidence intervals.

#### 11.1 Statistical Sampling

**What:** Use Monte Carlo methods to estimate expectation values with confidence intervals.

**Why:** Accounts for quantum randomness by analyzing statistical distributions over multiple circuit executions.

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

### 12. Security and Adversarial Testing

These tests evaluate quantum circuits against security vulnerabilities and deliberate attacks.

#### 12.1 Quantum Cryptography Testing

**What:** Test quantum cryptographic protocols for security against specific attacks.

**Why:** Quantum cryptography promises security advantages, but implementation vulnerabilities can compromise these benefits.

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

#### 12.2 Fault Injection Testing

**What:** Deliberately introduce faults to test circuit robustness and error-handling.

**Why:** Understanding how circuits fail under specific error conditions helps design more fault-tolerant algorithms.

**Example:**
```python
from qiskit.providers.aer.noise import NoiseModel
from qiskit.providers.aer.noise.errors import depolarizing_error

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
    # For circuits with error correction, we expect better tolerance
    if 'bit_flip_code' in qasm_file:
        assert fault_tolerance_results['bit_flip'] > 0.7, \
            f"Bit-flip code failed to mitigate bit-flip errors, success rate: {fault_tolerance_results['bit_flip']}"
    
    # For standard circuits, we just record the fault tolerance profile
    print(f"Fault tolerance profile: {fault_tolerance_results}")
    
    # At minimum, ensure results were collected successfully
    assert len(fault_tolerance_results) == len(fault_types), "Failed to complete fault injection tests"
```

### 13. Noise Characterization

These tests characterize and analyze noise patterns in quantum systems.

#### 13.1 Hardware Noise Measurement

**What:** Measure and analyze noise characteristics of quantum hardware.

**Why:** Understanding the specific noise profile of hardware helps design better error mitigation strategies.

**Example:**
```python
def test_noise_characterization(backend_name):
    """Characterize noise properties of a quantum backend."""
    from qiskit import IBMQ
    from qiskit.providers.aer.noise import NoiseModel
    
    # Connect to IBMQ and get backend
    IBMQ.load_account()
    provider = IBMQ.get_provider()
    backend = provider.get_backend(backend_name)
    
    # Get backend properties
    properties = backend.properties()
    
    # Create a noise model based on backend properties
    noise_model = NoiseModel.from_backend(properties)
    
    # Analyze gate error rates
    gate_errors = {}
    for qubits, gate in properties.gates:
        for param in gate.parameters:
            if param.name == 'gate_error':
                gate_name = gate.gate
                qubit_str = '-'.join(map(str, qubits))
                gate_errors[f"{gate_name} {qubit_str}"] = param.value
    
    # Analyze readout errors
    readout_errors = {}
    for qubit, qubit_props in enumerate(properties.qubits):
        for param in qubit_props:
            if param.name == 'readout_error':
                readout_errors[qubit] = param.value
    
    # Calculate average error rates
    avg_single_gate_error = np.mean([err for name, err in gate_errors.items() if 'cx' not in name.lower()])
    avg_two_gate_error = np.mean([err for name, err in gate_errors.items() if 'cx' in name.lower()])
    avg_readout_error = np.mean(list(readout_errors.values()))
    
    # Create simple test circuit to verify noise model matches expectations
    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])
    
    # Run with noise model
    simulator = Aer.get_backend('qasm_simulator')
    result = simulator.run(
        transpile(circuit, simulator),
        noise_model=noise_model,
        shots=8192
    ).result()
    
    # Verify error rates are within expected ranges for the specific hardware
    assert avg_single_gate_error < 0.01, f"Single-qubit gate error too high: {avg_single_gate_error}"
    assert avg_two_gate_error < 0.05, f"Two-qubit gate error too high: {avg_two_gate_error}"
    assert avg_readout_error < 0.05, f"Readout error too high: {avg_readout_error}"
```

### 14. Quantum Subroutines Tests

These tests validate modular components of larger quantum algorithms.

#### 14.1 Module Testing

**What:** Test individual quantum subroutines that are used in larger algorithms.

**Why:** Modular testing helps isolate issues in complex quantum algorithms.

**Example:**
```python
def test_quantum_phase_estimation_subroutine(phase_estimation_circuit):
    """Test the Quantum Phase Estimation subroutine component."""
    # Define a unitary with known eigenvalue
    # Example: phase = 1/4 (corresponds to eigenvalue e^(2πi/4) = i)
    target_phase = 1/4
    
    # Create controlled-U gates that implement the eigenvalue
    def controlled_u_factory(num_qubits, target_qubit, control_qubit):
        qc = QuantumCircuit(num_qubits)
        qc.cp(2*np.pi*target_phase, control_qubit, target_qubit)
        return qc
    
    # Use the phase estimation circuit with our controlled-U
    qpe_circuit = phase_estimation_circuit(
        num_counting_qubits=3,
        unitary_factory=controlled_u_factory
    )
    
    # Run the circuit
    simulator = Aer.get_backend('qasm_simulator')
    result = simulator.run(transpile(qpe_circuit, simulator), shots=1024).result()
    counts = result.get_counts()
    
    # Calculate the estimated phase from measurement outcomes
    phases = {}
    for bitstring, count in counts.items():
        # Convert to phase (e.g., "010" -> 2/8 = 1/4)
        phase = int(bitstring, 2) / (2**len(bitstring))
        phases[phase] = phases.get(phase, 0) + count
    
    # Find the most common phase estimate
    estimated_phase = max(phases.items(), key=lambda x: x[1])[0]
    
    # Verify it's close to the target
    phase_tolerance = 1/(2**3)  # Depends on number of counting qubits
    assert abs(estimated_phase - target_phase) <= phase_tolerance, \
        f"Phase estimation subroutine failed: expected {target_phase}, got {estimated_phase}"
```

### 15. Logical Consistency Tests

These tests verify the logical correctness of quantum operations.

#### 15.1 Truth Table Validation

**What:** Verify quantum circuits implement correct logical operations using truth tables.

**Why:** Quantum circuits often implement classical logical functions - this verifies they do so correctly.

**Example:**
```python
def test_quantum_logic_truth_table(qasm_file):
    """Test if a quantum circuit implements the expected truth table."""
    # Load circuit implementing a quantum logic operation
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Define expected truth table (example: Toffoli/CCX gate)
    expected_truth_table = {
        '000': '000',
        '001': '001',
        '010': '010',
        '011': '011',
        '100': '100',
        '101': '101',
        '110': '111',  # Only this input flips the target
        '111': '110'   # Only this input flips the target
    }
    
    # Test each input state
    simulator = Aer.get_backend('qasm_simulator')
    
    for input_state, expected_output in expected_truth_table.items():
        # Create input state
        input_circuit = QuantumCircuit(3, 3)
        for i, bit in enumerate(input_state):
            if bit == '1':
                input_circuit.x(i)
                
        # Append test circuit
        full_circuit = input_circuit.compose(circuit)
        
        # Add measurements
        full_circuit.measure(range(3), range(3))
        
        # Run circuit
        result = simulator.run(transpile(full_circuit, simulator), shots=1024).result()
        counts = result.get_counts()
        
        # Get most frequent outcome
        most_frequent = max(counts, key=counts.get)
        
        # Check if output matches expected
        assert most_frequent == expected_output, \
            f"Input {input_state} produced {most_frequent}, expected {expected_output}"
```

### 16. Randomized Testing

These tests use random inputs to broadly test circuit robustness.

#### 16.1 Random Input Testing

**What:** Test circuits with randomly generated input states.

**Why:** Random testing can uncover edge cases and unexpected behaviors not covered by targeted tests.

**Example:**
```python
def test_random_input_states(qasm_file, num_random_tests=10):
    """Test circuit behavior with randomly generated input states."""
    # Load circuit
    circuit = QuantumCircuit.from_qasm_file(qasm_file)
    num_qubits = circuit.num_qubits
    
    # Set up simulator
    simulator = Aer.get_backend('statevector_simulator')
    
    # Run tests with different random inputs
    for test_num in range(num_random_tests):
        # Create a random statevector
        import random
        
        # Create random circuit to generate random state
        # This is one way to create physically valid random quantum states
        random_circuit = QuantumCircuit(num_qubits)
        
        # Apply random single-qubit rotations
        for qubit in range(num_qubits):
            # Random rotations around X, Y, Z axes
            random_circuit.rx(random.uniform(0, 2*np.pi), qubit)
            random_circuit.ry(random.uniform(0, 2*np.pi), qubit)
            random_circuit.rz(random.uniform(0, 2*np.pi), qubit)
        
        # Add some random entanglement
        for _ in range(num_qubits-1):
            control = random.randint(0, num_qubits-1)
            target = random.randint(0, num_qubits-1)
            if control != target:
                random_circuit.cx(control, target)
        
        # Simulate to get random input state
        result = simulator.run(transpile(random_circuit, simulator)).result()
        random_state = result.get_statevector()
        
        # Now run the test circuit with this input state
        test_circuit = QuantumCircuit(num_qubits)
        test_circuit.initialize(random_state, range(num_qubits))
        test_circuit = test_circuit.compose(circuit)
        
        # Run and verify the circuit doesn't crash with random input
        try:
            simulator.run(transpile(test_circuit, simulator)).result()
            # Test passes if no exception is raised
        except Exception as e:
            assert False, f"Circuit failed with random input on test {test_num}: {str(e)}"
```

### 17. Circuit Optimization Tests

These tests validate that circuit optimization techniques preserve functionality while improving efficiency.

#### 17.1 Transpilation Optimization

**What:** Verify circuit properties after optimization passes to ensure functionality is preserved.

**Why:** Circuit optimization can significantly reduce depth and gate count, but must maintain the same logical operation.

**Example:**
```python
def test_transpilation_optimization(qasm_file):
    """Test that circuit optimization preserves functionality."""
    # Load the original circuit
    original_circuit = QuantumCircuit.from_qasm_file(qasm_file)
    
    # Get original properties
    original_depth = original_circuit.depth()
    original_gate_count = sum(original_circuit.count_ops().values())
    
    # Run statevector simulation on original circuit (without measurements)
    original_without_measure = original_circuit.remove_final_measurements(inplace=False)
    simulator = Aer.get_backend('statevector_simulator')
    original_result = simulator.run(transpile(original_without_measure, simulator)).result()
    original_statevector = original_result.get_statevector()
    
    # Optimize circuit with aggressive settings
    from qiskit.transpiler import PassManager
    from qiskit.transpiler.passes import Unroller, Optimize1qGates, CXCancellation
    
    # Create optimization passes
    pass_manager = PassManager()
    pass_manager.append(Unroller(['u1', 'u2', 'u3', 'cx']))
    pass_manager.append(Optimize1qGates())
    pass_manager.append(CXCancellation())
    
    # Apply optimization
    optimized_circuit = pass_manager.run(original_without_measure)
    
    # Get optimized properties
    optimized_depth = optimized_circuit.depth()
    optimized_gate_count = sum(optimized_circuit.count_ops().values())
    
    # Run statevector simulation on optimized circuit
    optimized_result = simulator.run(transpile(optimized_circuit, simulator)).result()
    optimized_statevector = optimized_result.get_statevector()
    
    # Verify optimization reduced resources
    assert optimized_depth <= original_depth, \
        f"Optimization failed to reduce depth: original={original_depth}, optimized={optimized_depth}"
    
    # Verify functionality is preserved (statevectors should be equivalent up to global phase)
    from qiskit.quantum_info import Statevector
    original_sv = Statevector(original_statevector)
    optimized_sv = Statevector(optimized_statevector)
    
    assert original_sv.equiv(optimized_sv), \
        "Optimization changed circuit functionality"
    
    print(f"Optimization reduced depth from {original_depth} to {optimized_depth} " +
          f"and gate count from {original_gate_count} to {optimized_gate_count}")
```

#### 17.2 Gate Cancellation Verification

**What:** Verify that redundant gates are properly eliminated during optimization.

**Why:** Gate cancellation reduces circuit complexity without changing the overall unitary transformation.

**Example:**
```python
def test_gate_cancellation(qasm_file):
    """Test that optimization eliminates redundant gates."""
    # Create a circuit with known redundant gates
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.h(0)  # This should cancel with the previous Hadamard
    circuit.x(1)
    circuit.x(1)  # This should cancel with the previous X
    circuit.cx(0, 1)
    circuit.cx(0, 1)  # This should cancel with the previous CNOT
    
    # Count original gates
    original_ops = circuit.count_ops()
    
    # Apply optimization
    from qiskit.transpiler import PassManager
    from qiskit.transpiler.passes import Optimize1qGates, CXCancellation
    
    pass_manager = PassManager()
    pass_manager.append(Optimize1qGates())
    pass_manager.append(CXCancellation())
    
    optimized_circuit = pass_manager.run(circuit)
    
    # Count optimized gates
    optimized_ops = optimized_circuit.count_ops()
    
    # The optimized circuit should have eliminated all gates
    assert sum(optimized_ops.values()) == 0, \
        f"Gate cancellation failed, remaining gates: {optimized_ops}"
```

### 18. Edge Case Testing

These tests verify circuit behavior in extreme or unusual conditions.

#### 18.1 Qubit Capacity Tests

**What:** Test circuits at minimum and maximum qubit capacities.

**Why:** Edge cases like minimal or maximal resource usage can reveal scaling issues or unexpected behaviors.

**Example:**
```python
def test_qubit_capacity_limits():
    """Test circuit behavior at minimum and maximum qubit capacity."""
    # Test minimum case - single qubit circuit
    min_circuit = QuantumCircuit(1, 1)
    min_circuit.h(0)
    min_circuit.measure(0, 0)
    
    simulator = Aer.get_backend('qasm_simulator')
    min_result = simulator.run(transpile(min_circuit, simulator), shots=1024).result()
    min_counts = min_result.get_counts()
    
    # Verify single qubit circuit produces expected distribution
    assert set(min_counts.keys()) == {'0', '1'}, \
        f"Single qubit circuit produced unexpected outcomes: {min_counts}"
    
    # Test maximum case (for simulator, we'll use a reasonable large number)
    max_qubits = 20  # Most simulators can handle this, but it's large enough to catch issues
    
    try:
        # Create GHZ state with max qubits
        max_circuit = QuantumCircuit(max_qubits, max_qubits)
        max_circuit.h(0)
        for i in range(1, max_qubits):
            max_circuit.cx(0, i)
        max_circuit.measure(range(max_qubits), range(max_qubits))
        
        # Simulate with limited shots to avoid memory issues
        max_result = simulator.run(transpile(max_circuit, simulator), shots=10).result()
        
        # Just verify the simulation completed without error
        assert max_result.success, "Max qubit circuit simulation failed"
        
    except Exception as e:
        # If an error occurs, check if it's because of resource limits
        # This might be expected on some systems
        import re
        if re.search(r'memory|resource|limit', str(e), re.IGNORECASE):
            print(f"Expected resource limitation hit: {e}")
        else:
            raise  # Re-raise if it's an unexpected error
```

#### 18.2 Empty Circuit Tests

**What:** Validate behavior with empty gate sequences.

**Why:** Edge cases like empty circuits should be handled gracefully rather than causing errors.

**Example:**
```python
def test_empty_circuit_behavior():
    """Test behavior with empty gate sequences."""
    # Create completely empty circuit
    empty_circuit = QuantumCircuit(2, 2)
    
    # Add only measurements
    measurement_only = QuantumCircuit(2, 2)
    measurement_only.measure([0, 1], [0, 1])
    
    # Simulate both
    simulator = Aer.get_backend('qasm_simulator')
    
    empty_result = simulator.run(transpile(empty_circuit, simulator), shots=1024).result()
    # Empty circuit without measurements should still be valid
    assert empty_result.success, "Empty circuit simulation failed"
    
    measure_result = simulator.run(transpile(measurement_only, simulator), shots=1024).result()
    counts = measure_result.get_counts()
    
    # Measurement-only circuit should return all zeros (since qubits start in |0⟩ state)
    assert '00' in counts and counts['00'] == 1024, \
        f"Measurement-only circuit didn't return all zeros: {counts}"
```

### 19. Error Handling and Negative Tests

These tests verify that the system properly handles invalid inputs and edge cases.

#### 19.1 Invalid Gate Usage

**What:** Verify appropriate errors are raised when invalid gates or parameters are used.

**Why:** Robust error handling prevents silent failures and provides clear debugging information.

**Example:**
```python
def test_invalid_gate_usage():
    """Test error handling for invalid gate usage."""
    circuit = QuantumCircuit(2, 2)
    
    # Test cases that should raise exceptions
    error_cases = [
        # Lambda to create test case
        lambda: circuit.cx(0, 5),  # Qubit index out of range
        lambda: circuit.h(10),     # Qubit index out of range
        lambda: circuit.measure(0, 5),  # Classical bit index out of range
    ]
    
    # Verify each case raises appropriate exception
    for i, error_case in enumerate(error_cases):
        try:
            error_case()
            assert False, f"Test case {i} should have raised an exception"
        except Exception as e:
            # Verify exception contains informative message
            assert "index" in str(e).lower() or "out of range" in str(e).lower(), \
                f"Exception message not informative: {str(e)}"
```

#### 19.2 Malformed QASM File Tests

**What:** Test parsing failures with intentionally malformed QASM syntax.

**Why:** Proper error handling for invalid input prevents unexpected behavior and provides clear error messages.

**Example:**
```python
def test_malformed_qasm_handling():
    """Test error handling for malformed QASM files."""
    import tempfile
    import os
    
    # Create temporary files with malformed QASM
    test_cases = [
        # Missing semicolon
        "OPENQASM 2.0;\ninclude \"qelib1.h\";\nqreg q[2]\ncreg c[2];",
        
        # Invalid gate name
        "OPENQASM 2.0;\ninclude \"qelib1.h\";\nqreg q[2];\ncreg c[2];\ninvalidgate q[0];",
        
        # Unbalanced braces
        "OPENQASM 2.0;\ninclude \"qelib1.h\";\nqreg q[2];\ncreg c[2];\nh q[0];{",
    ]
    
    for i, case in enumerate(test_cases):
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.qasm', delete=False) as f:
            f.write(case)
            temp_filename = f.name
        
        try:
            # Attempt to load malformed file
            try:
                circuit = QuantumCircuit.from_qasm_file(temp_filename)
                assert False, f"Malformed QASM case {i} did not raise exception"
            except Exception as e:
                # Verify exception contains informative message
                assert "syntax" in str(e).lower() or "invalid" in str(e).lower() or "error" in str(e).lower(), \
                    f"Exception message not informative: {str(e)}"
        finally:
            # Clean up temp file
            os.unlink(temp_filename)
```

### 20. Performance and Scalability Tests

These tests assess computational efficiency and scaling behavior of quantum circuits.

#### 20.1 Execution Time Benchmarking

**What:** Measure and assert acceptable execution times for simulation.

**Why:** Performance benchmarks ensure circuit simulations remain feasible as complexity increases.

**Example:**
```python
def test_execution_time_scaling():
    """Test how simulation time scales with circuit complexity."""
    import time
    
    # Test increasing circuit sizes
    qubit_counts = [2, 4, 8, 12]
    execution_times = []
    
    simulator = Aer.get_backend('qasm_simulator')
    
    for n_qubits in qubit_counts:
        # Create GHZ circuit of increasing size
        circuit = QuantumCircuit(n_qubits, n_qubits)
        circuit.h(0)
        for i in range(1, n_qubits):
            circuit.cx(0, i)
        circuit.measure(range(n_qubits), range(n_qubits))
        
        # Transpile once before timing
        transpiled_circuit = transpile(circuit, simulator)
        
        # Time execution
        start_time = time.time()
        result = simulator.run(transpiled_circuit, shots=1024).result()
        end_time = time.time()
        
        execution_time = end_time - start_time
        execution_times.append(execution_time)
        
    # Verify execution completed successfully for all sizes
    assert len(execution_times) == len(qubit_counts), "Not all circuits executed successfully"
    
    # Check if execution time scales polynomially (not exponentially)
    # This is a simple heuristic - real scaling analysis would be more sophisticated
    if len(qubit_counts) >= 3:
        # Calculate scaling factor between largest and smallest circuit
        scaling_factor = execution_times[-1] / execution_times[0]
        size_ratio = qubit_counts[-1] / qubit_counts[0]
        
        # If scaling is worse than O(2^n), print warning
        if scaling_factor > size_ratio**3:
            print(f"Warning: Execution time may be scaling poorly. " +
                  f"Time increased by {scaling_factor}x for a {size_ratio}x increase in qubits.")
```

#### 20.2 Memory Usage Monitoring

**What:** Monitor memory consumption during circuit simulation.

**Why:** Memory usage analysis helps identify potential scalability bottlenecks.

**Example:**
```python
def test_memory_usage():
    """Monitor memory usage during circuit simulation."""
    try:
        import psutil
        import os
        
        # Current process
        process = psutil.Process(os.getpid())
        
        # Create a medium size circuit
        n_qubits = 10
        circuit = QuantumCircuit(n_qubits)
        
        # Add a series of gates
        for i in range(n_qubits):
            circuit.h(i)
        
        for i in range(n_qubits-1):
            circuit.cx(i, i+1)
        
        # Measure initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run statevector simulation (memory intensive)
        simulator = Aer.get_backend('statevector_simulator')
        result = simulator.run(transpile(circuit, simulator)).result()
        
        # Measure peak memory
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Calculate theoretical memory for statevector
        # Each amplitude is a complex number (16 bytes) and there are 2^n amplitudes
        theoretical_memory = (2**n_qubits) * 16 / 1024 / 1024  # MB
        
        print(f"Memory usage increased by {memory_increase:.2f} MB")
        print(f"Theoretical statevector size: {theoretical_memory:.2f} MB")
        
        # This test is informational rather than assertive
        # Simple sanity check that memory usage isn't outlandishly high
        assert memory_increase < theoretical_memory * 10, \
            f"Memory usage ({memory_increase} MB) far exceeds theoretical statevector size ({theoretical_memory} MB)"
            
    except ImportError:
        print("Skipping memory test - psutil not available")
```

### 21. Visualization and Metadata Tests

These tests verify that circuit visualization and metadata functions work correctly.

#### 21.1 Circuit Drawing Tests

**What:** Verify circuit drawing functions execute without errors.

**Why:** Circuit visualization is crucial for debugging and understanding quantum algorithms.

**Example:**
```python
def test_circuit_visualization():
    """Test that circuit visualization functions work correctly."""
    # Create a test circuit
    circuit = QuantumCircuit(3, 3)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.measure_all()
    
    # Test text drawing
    try:
        text_drawing = circuit.draw(output='text')
        assert isinstance(text_drawing, str), "Text drawing should return a string"
        assert len(text_drawing) > 0, "Text drawing should not be empty"
    except Exception as e:
        assert False, f"Text drawing failed: {str(e)}"
    
    # Test ASCII drawing
    try:
        ascii_drawing = circuit.draw(output='ascii')
        assert isinstance(ascii_drawing, str), "ASCII drawing should return a string"
        assert len(ascii_drawing) > 0, "ASCII drawing should not be empty"
    except Exception as e:
        assert False, f"ASCII drawing failed: {str(e)}"
    
    # Test matplotlib drawing (if available)
    try:
        import matplotlib
        matplotlib_drawing = circuit.draw(output='mpl')
        assert matplotlib_drawing is not None, "Matplotlib drawing should return a Figure"
    except ImportError:
        print("Skipping matplotlib test - matplotlib not available")
    except Exception as e:
        assert False, f"Matplotlib drawing failed: {str(e)}"
```

#### 21.2 Metadata Preservation

**What:** Verify that circuit metadata is correctly preserved throughout operations.

**Why:** Metadata helps track circuit provenance, purpose, and properties.

**Example:**
```python
def test_metadata_preservation():
    """Test that circuit metadata is preserved during operations."""
    # Create circuit with metadata
    circuit = QuantumCircuit(2, 2, name="Test Circuit")
    
    # Add custom metadata
    circuit.metadata = {
        'author': 'Test Author',
        'purpose': 'Testing',
        'version': '1.0',
        'description': 'A test circuit with metadata'
    }
    
    # Add gates
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure_all()
    
    # Operations that should preserve metadata
    operations = [
        # Function, expected metadata keys
        (lambda c: c.inverse(), ['author', 'purpose', 'version']),
        (lambda c: transpile(c, basis_gates=['u1', 'u2', 'u3', 'cx']), ['name']),
        (lambda c: c.copy(), ['author', 'purpose', 'version', 'description']),
    ]
    
    for op_func, expected_keys in operations:
        # Apply operation
        result_circuit = op_func(circuit)
        
        # Check if metadata exists
        assert hasattr(result_circuit, 'metadata'), "Metadata attribute was lost"
        
        # Check if required metadata was preserved
        for key in expected_keys:
            assert key in result_circuit.metadata, f"Metadata key '{key}' was lost"
```

### 22. Benchmarking Tests

These tests compare quantum algorithm performance against classical alternatives or established benchmarks.

#### 22.1 Classical Algorithm Comparison

**What:** Compare quantum circuit performance with classical counterparts.

**Why:** Benchmarking helps quantify quantum advantage and verify correct implementation.

**Example:**
```python
def test_quantum_vs_classical_search():
    """Compare Grover's search against classical search for a marked item."""
    import random
    import time
    
    # Problem size
    n_bits = 6  # Small for simulation purposes
    search_space_size = 2**n_bits
    
    # Randomly select a marked item
    marked_item = random.randint(0, search_space_size-1)
    marked_binary = format(marked_item, f'0{n_bits}b')
    
    # Classical search
    classical_start = time.time()
    
    # Simulate a classical search by checking items one by one
    found = False
    checks = 0
    for i in range(search_space_size):
        checks += 1
        if i == marked_item:
            found = True
            break
    
    classical_time = time.time() - classical_start
    classical_checks = checks
    
    # Quantum search (Grover's algorithm)
    quantum_start = time.time()
    
    # Build oracle for the marked item
    from qiskit.circuit.library import PhaseOracle
    oracle_expr = ' & '.join([f'{"" if marked_binary[i] == "1" else "~"}x{i}' for i in range(n_bits)])
    oracle = PhaseOracle(oracle_expr)
    
    # Create Grover's algorithm circuit
    from qiskit.algorithms import Grover, AmplificationProblem
    problem = AmplificationProblem(oracle, is_good_state=lambda x: x == marked_binary)
    grover = Grover()
    
    # Run search
    simulator = Aer.get_backend('qasm_simulator')
    result = grover.run(simulator, problem)
    
    quantum_time = time.time() - quantum_start
    
    # Check if correct item was found
    top_measurement = max(result.circuit_results[0].items(), key=lambda x: x[1])[0]
    quantum_correct = (top_measurement == marked_binary)
    
    # Calculate number of oracle calls (theoretical)
    import math
    quantum_oracle_calls = int(math.pi/4 * math.sqrt(search_space_size))
    
    # Compare results
    print(f"Classical search: {classical_checks} checks, {classical_time:.4f} seconds")
    print(f"Quantum search: ~{quantum_oracle_calls} oracle calls, {quantum_time:.4f} seconds")
    
    # Verify quantum algorithm found correct answer
    assert quantum_correct, f"Quantum search found incorrect answer: {top_measurement} vs {marked_binary}"
    
    # For small problems, classical might actually be faster due to simulation overhead
    # But quantum should use fewer oracle queries
    assert quantum_oracle_calls < classical_checks, \
        f"Quantum algorithm used more queries ({quantum_oracle_calls}) than classical ({classical_checks})"
```

### 23. State Preparation Tests

These tests validate correct preparation of specific quantum states.

#### 23.1 State Initialization Validation

**What:** Verify correct preparation of specific quantum states.

**Why:** Many quantum algorithms require precise state initialization as a starting point.

**Example:**
```python
def test_state_preparation():
    """Test preparation of specific quantum states."""
    # Test cases: state name, preparation function, expected statevector
    test_cases = [
        # Bell state |00⟩ + |11⟩ / √2
        (
            "Bell",
            lambda: QuantumCircuit(2).compose(
                QuantumCircuit(2).h(0).cx(0, 1)
            ),
            np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)])
        ),
        
        # GHZ state |000⟩ + |111⟩ / √2
        (
            "GHZ",
            lambda: QuantumCircuit(3).compose(
                QuantumCircuit(3).h(0).cx(0, 1).cx(1, 2)
            ),
            np.array([1/np.sqrt(2), 0, 0, 0, 0, 0, 0, 1/np.sqrt(2)])
        ),
        
        # W state |100⟩ + |010⟩ + |001⟩ / √3
        (
            "W-state",
            lambda: QuantumCircuit(3).compose(
                QuantumCircuit(3)
                .ry(2 * np.arccos(1/np.sqrt(3)), 0)
                .cx(0, 1)
                .x(0)
                .ccx(0, 1, 2)
                .x(0)
            ),
            np.array([0, 1/np.sqrt(3), 1/np.sqrt(3), 0, 1/np.sqrt(3), 0, 0, 0])
        ),
    ]
    
    simulator = Aer.get_backend('statevector_simulator')
    
    for name, prep_func, expected in test_cases:
        # Create and simulate circuit
        circuit = prep_func()
        result = simulator.run(transpile(circuit, simulator)).result()
        state = result.get_statevector()
        
        # Check if prepared state matches expected
        assert np.allclose(state, expected, atol=1e-7), \
            f"{name} state preparation failed. Got {state}, expected {expected}"
```

### 24. Backwards Compatibility Tests

These tests verify compatibility with previous versions of quantum frameworks and standards.

#### 24.1 QASM Version Compatibility

**What:** Test compatibility across different OpenQASM versions.

**Why:** As standards evolve, circuits should maintain backwards compatibility with older versions.

**Example:**
```python
def test_qasm_version_compatibility():
    """Test compatibility between different OpenQASM versions."""
    # Create a simple circuit
    original_circuit = QuantumCircuit(2, 2)
    original_circuit.h(0)
    original_circuit.cx(0, 1)
    original_circuit.measure([0, 1], [0, 1])
    
    # Export to QASM 2.0
    qasm2_str = original_circuit.qasm()
    
    # Verify it contains QASM 2.0 header
    assert "OPENQASM 2.0;" in qasm2_str, "QASM export doesn't contain proper 2.0 header"
    
    # Import back from QASM 2.0
    try:
        from qiskit import qasm2, qasm3
        
        imported_circuit = QuantumCircuit.from_qasm_str(qasm2_str)
        
        # Verify the circuits are equivalent
        assert original_circuit.depth() == imported_circuit.depth(), \
            "Imported circuit has different depth"
        assert original_circuit.count_ops() == imported_circuit.count_ops(), \
            "Imported circuit has different gate counts"
            
        # Try to convert to QASM 3.0 if supported
        try:
            qasm3_str = qasm3.dumps(original_circuit)
            assert "OPENQASM 3" in qasm3_str, "QASM 3.0 export doesn't contain proper header"
            
            # Verify we can convert back to a circuit if the parser is available
            if hasattr(qasm3, 'loads'):
                circuit_from_qasm3 = qasm3.loads(qasm3_str)
                assert isinstance(circuit_from_qasm3, QuantumCircuit), \
                    "Failed to import from QASM 3.0"
        except (ImportError, AttributeError):
            print("QASM 3.0 export/import not fully supported in this Qiskit version")
            
    except ImportError:
        print("Skipping some QASM compatibility tests - required modules not available")
```

## Best Practices

1. **Test Isolation:** Ensure tests are independent and don't affect each other
2. **Deterministic Testing:** Make tests reproducible with fixed random seeds when appropriate
3. **Comprehensive Coverage:** Include tests from multiple categories for robust validation
4. **Continuous Integration:** Automate tests to run on code changes
5. **Progressive Complexity:** Start with simple tests and progressively add complexity
6. **Hardware-in-the-Loop Testing:** Include real quantum hardware in testing pipelines when possible
7. **Statistical Awareness:** Account for the probabilistic nature of quantum measurements with appropriate statistical analysis

## Conclusion

Effective testing of quantum circuits requires a multi-faceted approach covering static analysis, simulation, hardware compatibility, and algorithm-specific behavior. The examples in this guide provide a starting point for developing a comprehensive test suite for quantum circuits, adaptable to different quantum algorithms and applications.
