import numpy as np
from qiskit import QuantumCircuit
from typing import Dict, List, Tuple, Union

def calculate_expectation(counts: Dict[str, int]) -> float:
    """
    Calculate expectation value of Z on first qubit from measurement counts.
    
    Args:
        counts: Dictionary of measurement results and frequencies
        
    Returns:
        Expectation value <Z> = P(0) - P(1) for first qubit
    """
    prob_0 = sum(counts.get(b, 0) for b in counts if b[0] == '0')
    prob_1 = sum(counts.get(b, 0) for b in counts if b[0] == '1')
    total = prob_0 + prob_1
    
    if total == 0:
        return 0
    
    return (prob_0 - prob_1) / total

def distribution_entropy(counts: Dict[str, int]) -> float:
    """
    Calculate Shannon entropy of a measurement distribution.
    
    Args:
        counts: Dictionary of measurement results and frequencies
        
    Returns:
        Entropy of the distribution in bits
    """
    total_shots = sum(counts.values())
    probabilities = [count / total_shots for count in counts.values()]
    entropy = -sum(p * np.log2(p) for p in probabilities if p > 0)
    return entropy

def check_periods_for_n15(bitstring: str, tolerance: float = 0.1) -> bool:
    """
    Check if a measurement could correspond to a valid period for factoring N=15.
    
    Args:
        bitstring: Measurement result as binary string
        tolerance: Fractional tolerance for period match
        
    Returns:
        True if measurement is consistent with a valid period, False otherwise
    """
    # Convert to integer
    measured = int(bitstring, 2)
    n_bits = len(bitstring)
    possible_periods = [1, 2, 4, 8]  # Potential periods for N=15
    
    # Due to the nature of QFT, the measured value needs further processing
    # For an ideal measurement corresponding to period r, we'd get s/r for some s < r
    for period in possible_periods:
        # Check if measurement is close to s/r for any s < r
        for s in range(1, period):
            expected = (s * 2**n_bits) / period
            # Allow some numerical tolerance
            if abs(measured - expected) <= tolerance * 2**n_bits:
                return True
    return False

def create_noise_model(p_1q: float = 0.01, p_2q: float = 0.05, gates_1q: List[str] = None, gates_2q: List[str] = None):
    """
    Create a basic noise model with depolarizing errors.
    
    Args:
        p_1q: Error probability for single-qubit gates
        p_2q: Error probability for two-qubit gates
        gates_1q: List of single-qubit gate names to apply errors to
        gates_2q: List of two-qubit gate names to apply errors to
        
    Returns:
        NoiseModel instance with configured errors
    """
    try:
        from qiskit_aer.noise import NoiseModel
        from qiskit_aer.noise.errors import depolarizing_error
        
        noise_model = NoiseModel()
        
        if gates_1q:
            error_1q = depolarizing_error(p_1q, 1)
            for gate in gates_1q:
                noise_model.add_all_qubit_quantum_error(error_1q, gate)
        
        if gates_2q:
            error_2q = depolarizing_error(p_2q, 2)
            for gate in gates_2q:
                noise_model.add_all_qubit_quantum_error(error_2q, gate)
        
        return noise_model
    except ImportError:
        raise ImportError("qiskit_aer with noise module is required for noise modeling")

def total_variation_distance(counts1: Dict[str, int], counts2: Dict[str, int]) -> float:
    """
    Calculate the total variation distance between two measurement distributions.
    
    Args:
        counts1: First measurement distribution
        counts2: Second measurement distribution
        
    Returns:
        Total variation distance (0 to 1)
    """
    total1 = sum(counts1.values())
    total2 = sum(counts2.values())
    
    # All possible outcomes
    all_outcomes = set(counts1.keys()).union(counts2.keys())
    
    # Calculate TVD = 1/2 * sum_i |P(i) - Q(i)|
    tvd = 0.5 * sum(
        abs(counts1.get(outcome, 0) / total1 - counts2.get(outcome, 0) / total2)
        for outcome in all_outcomes
    )
    
    return tvd 