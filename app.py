# --- Backend Availability & SDK Import Handling ---
QISKIT_AVAILABLE = False
qiskit = None
QuantumCircuit = None
qasm2_loads = None
QASM2ParseError = None
AerSimulator = None
SDK_BACKENDS_AVAILABLE = True # Assume True initially, set False on critical import error

try:
    # Try importing Qiskit
    import qiskit
    from qiskit import QuantumCircuit
    from qiskit.qasm2 import loads as qasm2_loads, QASM2ParseError
    try:
        # Correct import for Qiskit 1.0+
        from qiskit_aer import AerSimulator
        QISKIT_AVAILABLE = True
    except ImportError:
        logger.warning("qiskit installed, but qiskit-aer not found or failed to import. Qiskit backend unavailable.")
except ImportError:
    logger.debug("Qiskit not available.")
    pass

CIRQ_AVAILABLE = False
cirq = None
# Rely on cirq.contrib.qasm_import instead
try:
    import cirq
    # Verify that cirq.contrib.qasm_import is available
    from cirq.contrib import qasm_import
    CIRQ_AVAILABLE = True
except ImportError:
    logger.debug("Cirq not available.")
    pass

BRAKET_AVAILABLE = False
// ... existing code ... 