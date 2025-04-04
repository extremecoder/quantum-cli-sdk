# Quantum Circuit Test Suite

This directory contains a comprehensive test suite for validating the Shor's algorithm quantum circuit implemented in OpenQASM.

## Overview

The tests are based on the comprehensive testing strategies outlined in `README_TEST.md` in the root directory. They cover a wide range of validation approaches including:

1. Circuit Structure Validation
2. Circuit Behavior Simulation
3. Algorithm-Specific Functional Tests
4. Hardware Compatibility Tests
5. Noise and Error Mitigation Tests
6. Visualization and Metadata Tests
7. Randomized Testing
8. Edge Case Testing
9. Performance and Scalability Tests
10. Circuit Optimization Tests
11. Backwards Compatibility Tests

## Test Files

- `test_shors_factoring.py`: Core tests for the Shor's algorithm circuit
- `test_shors_advanced.py`: Advanced tests focusing on specialized test categories
- `utils.py`: Utility functions for quantum circuit testing
- `run_all_tests.py`: Script to execute the full test suite

## Running the Tests

To run all tests:

```bash
cd my-cli-test-app
python tests/generated/run_all_tests.py
```

To run a specific test file:

```bash
pytest tests/generated/test_shors_factoring.py -v
```

## Test Environment Requirements

The tests require:
- Python 3.7+
- Qiskit
- pytest
- numpy
- matplotlib (for visualization tests)
- psutil (for memory usage tests)

## Expected Results

When running these tests against a correctly implemented Shor's factoring algorithm for N=15, all tests should pass. The circuit should:

1. Have the correct structure with period and target registers
2. Produce measurement results consistent with the periodic nature of modular exponentiation
3. Be robust under reasonable levels of noise
4. Be optimizable without losing functionality
5. Be compatible with standard quantum hardware connectivity constraints
6. Scale reasonably with increasing shot count

## Adding More Tests

New test categories can be added by following the patterns established in the existing test files. Each test function should be prefixed with `test_` and should test a specific aspect of the quantum circuit.

# Shor's Algorithm Test Suite

This directory contains a comprehensive test suite for the Shor's algorithm quantum circuit implementation located at `../ir/openqasm/shors_factoring_15_compatible.qasm`.

## Overview

The tests in this directory validate the functionality, correctness, and performance of the Shor's algorithm quantum circuit. The tests follow the testing strategies outlined in `README_TEST.md` at the root of the project, including:

1. Circuit Structure Validation
2. Circuit Behavior Simulation
3. Algorithm-Specific Functional Tests
4. Equivalence Testing
5. Hardware Compatibility Tests
6. Noise and Error Mitigation Tests
7. Parameterized Circuit Tests
8. Integration and End-to-End Tests
9. Quantum State Tomography
10. Monte Carlo Simulations
11. Security and Adversarial Testing
12. Circuit Optimization Tests
13. Parameterized Circuit Tests
14. Random Input Tests
15. Logical Consistency Tests
16. OpenQASM Compatibility Tests

## Test Files

The test suite consists of the following files:

- `test_shors_factoring.py`: Basic tests for circuit structure, behavior simulation, and algorithm-specific functionality
- `test_shors_advanced.py`: Advanced tests including quantum state analysis, optimization, and Monte Carlo simulations
- `utils.py`: Utility functions for testing, including functions for period checking and noise modeling
- `run_all_tests.py`: Script to run all tests and report results

## Qiskit 1.0+ Compatibility

This test suite has been updated to be compatible with Qiskit 1.0+. Key changes include:

1. Updated imports:
   - `AerSimulator` is now imported from `qiskit_aer` instead of `qiskit.providers.aer`
   - Noise model components are imported from `qiskit_aer.noise`

2. Circuit handling and manipulation:
   - When copying operations between circuits, we now convert qubit references to indices
   - The data structure for circuits has changed, requiring updates to how we access instructions

3. Statevector simulation:
   - Updated to use `save_state=True` flag and proper data retrieval from results
   - Replaced direct statevector tests with distribution-based tests

4. Visualization updates:
   - The `output='ascii'` option is no longer supported, replaced with `output='text'`
   - Drawing outputs are now objects that need to be converted to strings

5. Parameter handling:
   - Updated the threshold in parameterized circuit tests to account for different behavior

6. Classical register handling:
   - Updated how classical registers are added to circuits

## Running the Tests

To run the full test suite:

```bash
python run_all_tests.py
```

Or to run individual test files:

```bash
pytest test_shors_factoring.py -v
pytest test_shors_advanced.py -v
```

## Expected Results

All tests should pass, demonstrating that the Shor's algorithm circuit:

1. Has the correct structure (gate count, depth, measurements)
2. Produces a non-uniform distribution of results consistent with period finding
3. Shows quantum correlations in the output
4. Is sensitive to perturbations
5. Benefits from optimization
6. Can be modified with parameters
7. Functions correctly with different input states
8. Produces results consistent with the mathematical expectations for period finding in factoring N=15
9. Requires proper initialization of the target register
10. Can accommodate mid-circuit measurements

## Requirements

- Python 3.8+
- Qiskit 1.0+
- qiskit-aer
- pytest
- numpy

## Note on Warnings

The test suite may generate a large number of deprecation warnings during execution. These are related to ongoing changes in the Qiskit codebase and can be safely ignored. 