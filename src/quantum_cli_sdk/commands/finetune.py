"""
Fine-tune quantum circuits with hyperparameter optimization.
"""

import os
import sys
import logging
import json
import re
import itertools
import random
from pathlib import Path
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..config import get_config
from ..logging_config import setup_logger
from ..output_formatter import format_output

# Set up logger
logger = logging.getLogger(__name__)

# Default parameter ranges for hyperparameter search
DEFAULT_PARAMETER_RANGES = {
    "shots": [100, 500, 1000, 2000, 5000, 10000],
    "depth": [1, 2, 3, 4, 5],
    "entanglement": ["linear", "full", "circular"],
    "optimizer": ["COBYLA", "SPSA", "ADAM", "L_BFGS_B"],
    "maxiter": [100, 200, 500, 1000],
    "learning_rate": [0.01, 0.05, 0.1, 0.5]
}

def parse_qasm_parameters(circuit_file):
    """
    Parse parameters defined in a QASM file.
    
    Args:
        circuit_file (str): Path to the QASM file
        
    Returns:
        dict: Parameters found in the circuit
    """
    try:
        # Read QASM file
        with open(circuit_file, 'r') as f:
            content = f.read()
            
        # Find parameter definitions
        param_matches = re.finditer(r'parameter\s+(\w+)\s*=\s*([^;]+);', content)
        parameters = {}
        
        for match in param_matches:
            param_name = match.group(1)
            param_value = match.group(2).strip()
            
            # Try to convert to appropriate type
            try:
                if '.' in param_value:
                    parameters[param_name] = float(param_value)
                else:
                    parameters[param_name] = int(param_value)
            except ValueError:
                # Keep as string if not numeric
                parameters[param_name] = param_value
                
        logger.info(f"Found {len(parameters)} parameters in QASM file")
        return parameters
        
    except Exception as e:
        logger.error(f"Error parsing parameters from QASM file: {e}")
        return {}

def run_circuit_with_parameters(circuit_file, parameters, shots=1000, simulator="qiskit"):
    """
    Run a quantum circuit with given parameters and return metrics.
    
    Args:
        circuit_file (str): Path to the circuit file
        parameters (dict): Parameters to use for the circuit
        shots (int): Number of shots for the simulation
        simulator (str): Simulator to use
        
    Returns:
        dict: Results metrics
    """
    try:
        # For a real implementation, this would execute the circuit with the given parameters
        # and return the actual results. This is a simplified implementation.
        
        if simulator == "qiskit":
            # Import qiskit
            try:
                from qiskit import QuantumCircuit, Aer, execute
                import qiskit.quantum_info as qi
                
                # Read QASM file
                with open(circuit_file, 'r') as f:
                    qasm_content = f.read()
                    
                # Replace parameter placeholders with actual values
                for param_name, param_value in parameters.items():
                    qasm_content = qasm_content.replace(f"parameter {param_name}", f"{param_value}")
                    
                # Create circuit from QASM
                circuit = QuantumCircuit.from_qasm_str(qasm_content)
                
                # Add measurements if not present
                if not circuit.clbits:
                    circuit.measure_all()
                    
                # Run simulation
                simulator_backend = Aer.get_backend('qasm_simulator')
                job = execute(circuit, simulator_backend, shots=shots)
                result = job.result()
                
                # Calculate metrics
                counts = result.get_counts()
                total = sum(counts.values())
                probabilities = {k: v / total for k, v in counts.items()}
                
                # Calculate entropy as a metric of distribution quality
                entropy = -sum(p * np.log2(p) for p in probabilities.values() if p > 0)
                
                # Calculate number of unique outcomes
                unique_outcomes = len(counts)
                
                # Create a score combining entropy and unique outcomes
                score = entropy * np.log(unique_outcomes + 1)
                
                return {
                    "success": True,
                    "score": score,
                    "entropy": entropy,
                    "unique_outcomes": unique_outcomes,
                    "probabilities": probabilities,
                    "shots": shots,
                    "parameters": parameters
                }
                
            except ImportError:
                logger.error("Qiskit not installed")
                return {"success": False, "error": "Qiskit not installed"}
                
        else:
            # For other simulators we would implement similar logic
            logger.error(f"Simulator {simulator} not implemented in finetune")
            return {"success": False, "error": f"Simulator {simulator} not implemented"}
            
    except Exception as e:
        logger.error(f"Error running circuit with parameters: {e}")
        return {"success": False, "error": str(e)}

def grid_search(circuit_file, parameter_ranges, shots, simulator, num_top_results=5):
    """
    Perform grid search over parameter ranges.
    
    Args:
        circuit_file (str): Path to the circuit file
        parameter_ranges (dict): Ranges for each parameter
        shots (int): Base number of shots for simulation
        simulator (str): Simulator to use
        num_top_results (int): Number of top results to return
        
    Returns:
        list: Top results
    """
    # Generate all parameter combinations
    param_names = list(parameter_ranges.keys())
    param_values = list(parameter_ranges.values())
    
    # Count total combinations
    total_combinations = 1
    for values in param_values:
        total_combinations *= len(values)
        
    logger.info(f"Grid search with {total_combinations} parameter combinations")
    
    # Generate the combinations
    combinations = list(itertools.product(*param_values))
    
    # If too many combinations, sample a subset
    if total_combinations > 100:
        logger.info(f"Sampling 100 combinations out of {total_combinations}")
        combinations = random.sample(combinations, 100)
    
    # Run circuits with different parameters
    results = []
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        
        for combo in combinations:
            # Create parameter dictionary
            params = {param_names[i]: combo[i] for i in range(len(param_names))}
            
            # Submit to thread pool
            future = executor.submit(run_circuit_with_parameters, circuit_file, params, shots, simulator)
            futures.append((future, params))
            
        # Process results as they complete
        for i, (future, params) in enumerate(futures):
            try:
                result = future.result()
                if result["success"]:
                    results.append(result)
                    logger.info(f"Completed {i+1}/{len(futures)} with score {result.get('score', 0):.4f}")
                else:
                    logger.warning(f"Failed run {i+1}/{len(futures)}: {result.get('error')}")
            except Exception as e:
                logger.error(f"Error processing result {i+1}: {e}")
    
    # Sort by score (descending)
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    # Return top N results
    return results[:num_top_results]

def random_search(circuit_file, parameter_ranges, shots, simulator, num_trials=50, num_top_results=5):
    """
    Perform random search over parameter ranges.
    
    Args:
        circuit_file (str): Path to the circuit file
        parameter_ranges (dict): Ranges for each parameter
        shots (int): Base number of shots for simulation
        simulator (str): Simulator to use
        num_trials (int): Number of random combinations to try
        num_top_results (int): Number of top results to return
        
    Returns:
        list: Top results
    """
    logger.info(f"Random search with {num_trials} random parameter combinations")
    
    # Run circuits with random parameters
    results = []
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        
        for _ in range(num_trials):
            # Create random parameter dictionary
            params = {}
            for param_name, param_values in parameter_ranges.items():
                params[param_name] = random.choice(param_values)
            
            # Submit to thread pool
            future = executor.submit(run_circuit_with_parameters, circuit_file, params, shots, simulator)
            futures.append((future, params))
            
        # Process results as they complete
        for i, (future, params) in enumerate(futures):
            try:
                result = future.result()
                if result["success"]:
                    results.append(result)
                    logger.info(f"Completed {i+1}/{num_trials} with score {result.get('score', 0):.4f}")
                else:
                    logger.warning(f"Failed run {i+1}/{num_trials}: {result.get('error')}")
            except Exception as e:
                logger.error(f"Error processing result {i+1}: {e}")
    
    # Sort by score (descending)
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    # Return top N results
    return results[:num_top_results]

def finetune(source_file, dest_file=None, hyperparameter=None, parameters=None, search_method="random"):
    """
    Fine-tune a quantum circuit with hyperparameter optimization.
    
    Args:
        source_file (str): Path to the source circuit file
        dest_file (str, optional): Path to write optimization results
        hyperparameter (str, optional): Hyperparameter to focus on (e.g. "shots")
        parameters (str, optional): Comma-separated parameter values to try
        search_method (str): Search method ("grid", "random", "bayesian")
        
    Returns:
        bool: True if finetuning was successful
    """
    logger.info(f"Starting fine-tuning of {source_file}")
    
    # Ensure source file exists
    if not os.path.exists(source_file):
        logger.error(f"Source file {source_file} does not exist")
        return False
    
    # Determine destination file
    if not dest_file:
        dest_dir = os.path.join("results", "finetuning")
        os.makedirs(dest_dir, exist_ok=True)
        
        base_name = os.path.splitext(os.path.basename(source_file))[0]
        dest_file = os.path.join(dest_dir, f"{base_name}_finetuned.json")
    
    # Get configuration
    config = get_config()
    simulator = config.get_setting("simulator", "qiskit")
    base_shots = config.get_setting("shots", 1000)
    
    # Parse parameters from circuit
    circuit_params = parse_qasm_parameters(source_file)
    
    # Set up parameter ranges for finetuning
    param_ranges = {}
    
    # If hyperparameter is specified, focus on that one
    if hyperparameter:
        if hyperparameter == "shots":
            # Parse shots from parameters string or use defaults
            if parameters:
                try:
                    shots_values = [int(s.strip()) for s in parameters.split(",")]
                    param_ranges["shots"] = shots_values
                except ValueError:
                    logger.error("Invalid shots values provided")
                    param_ranges["shots"] = DEFAULT_PARAMETER_RANGES["shots"]
            else:
                param_ranges["shots"] = DEFAULT_PARAMETER_RANGES["shots"]
        else:
            # For other parameters, use provided values or defaults
            if parameters:
                param_values = [p.strip() for p in parameters.split(",")]
                
                # Try to convert to appropriate type based on existing parameter
                if hyperparameter in circuit_params:
                    if isinstance(circuit_params[hyperparameter], int):
                        param_values = [int(p) for p in param_values]
                    elif isinstance(circuit_params[hyperparameter], float):
                        param_values = [float(p) for p in param_values]
                        
                param_ranges[hyperparameter] = param_values
            elif hyperparameter in DEFAULT_PARAMETER_RANGES:
                param_ranges[hyperparameter] = DEFAULT_PARAMETER_RANGES[hyperparameter]
            else:
                logger.error(f"No values provided for hyperparameter {hyperparameter}")
                return False
    else:
        # If no specific hyperparameter, use reasonable defaults for common parameters
        param_ranges = {
            "shots": DEFAULT_PARAMETER_RANGES["shots"]
        }
        
        # Add circuit parameters if they exist
        for param_name in circuit_params:
            if param_name in DEFAULT_PARAMETER_RANGES:
                param_ranges[param_name] = DEFAULT_PARAMETER_RANGES[param_name]
    
    # Perform hyperparameter search
    if search_method == "grid":
        results = grid_search(source_file, param_ranges, base_shots, simulator)
    else:  # Default to random search
        results = random_search(source_file, param_ranges, base_shots, simulator)
        
    if not results:
        logger.error("No successful results from hyperparameter search")
        return False
    
    # Write results to destination file
    output_data = {
        "source_circuit": source_file,
        "search_method": search_method,
        "parameter_ranges": param_ranges,
        "top_results": results,
        "best_parameters": results[0]["parameters"],
        "best_score": results[0]["score"]
    }
    
    with open(dest_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Fine-tuning results written to {dest_file}")
    logger.info(f"Best parameters: {results[0]['parameters']}")
    logger.info(f"Best score: {results[0]['score']:.4f}")
    
    return True

if __name__ == "__main__":
    # This allows the module to be run directly for testing
    if len(sys.argv) < 2:
        print("Usage: finetune.py <source_file> [<dest_file>] [--hyperparameter name] [--parameters p1,p2,p3]")
        sys.exit(1)
    
    source = sys.argv[1]
    dest = None
    hyper = None
    params = None
    
    # Parse remaining arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--hyperparameter" and i+1 < len(sys.argv):
            hyper = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == "--parameters" and i+1 < len(sys.argv):
            params = sys.argv[i+1]
            i += 2
        else:
            dest = sys.argv[i]
            i += 1
    
    success = finetune(source, dest, hyper, params)
    sys.exit(0 if success else 1)
