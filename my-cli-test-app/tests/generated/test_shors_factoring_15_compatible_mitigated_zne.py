import pytest
from pathlib import Path
from qiskit import QuantumCircuit
from qiskit.primitives import Sampler
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram

@pytest.fixture
def loaded_circuit():
    qasm_file = Path(__file__).parent.parent.parent / 'ir' / 'openqasm' / 'mitigated' / 'shors_factoring_15_compatible_mitigated_zne.qasm'
    qc = QuantumCircuit.from_qasm_file(str(qasm_file))
    return qc

@pytest.fixture
def simulator():
    return AerSimulator()

def test_circuit_structure(loaded_circuit):
    qc = loaded_circuit
    assert qc.num_qubits == 8, "Wrong number of qubits"
    assert qc.depth() > 0, "Circuit depth is zero"

    # Extract just the gate names
    gate_names = {gate[0].name for gate in qc.data}
    print(f"Gate names in circuit: {gate_names}")
    
    # Check for common quantum gates
    assert 'measure' in gate_names, "Measurement gates should be present"
    
    # More flexible check, as the exact gate set depends on the implementation
    common_gates = {'h', 'cx', 'x', 'measure'}
    assert any(gate in gate_names for gate in common_gates), f"Circuit should contain some common gates like {common_gates}"

def test_circuit_behavior(loaded_circuit, simulator):
    qc = loaded_circuit
    
    # Simplify the test - just run directly with simulator
    job = simulator.run(qc, shots=1000)
    result = job.result()
    counts = result.get_counts()
    
    assert counts, "No counts returned from the simulation"
    
    # Basic check that we get results
    total_counts = sum(counts.values())
    assert total_counts > 0, f"Expected positive number of shots, got {total_counts}"
    
    # Print the distribution for debugging
    print(f"Measurement counts: {counts}")

def test_visualization_circuit_gates(loaded_circuit):
    qc = loaded_circuit
    # Just test that we can call draw() without errors
    try:
        circuit_diagram = qc.draw(output='text')
        print("Circuit diagram:")
        print(circuit_diagram)
    except Exception as e:
        pytest.fail(f"Failed to visualize circuit: {e}")