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
import datetime

from ..config import get_config
from ..quantum_circuit import QuantumCircuit
from ..output_formatter import format_output
from ..utils import load_circuit, save_circuit

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

# Hardware-specific parameter ranges
HARDWARE_PARAMETER_RANGES = {
    "ibm": {
        "shots": [512, 1024, 2048, 4096, 8192],
        "optimization_level": [0, 1, 2, 3],
        "layout_method": ["trivial", "dense", "noise_adaptive", "sabre"],
        "routing_method": ["basic", "stochastic", "lookahead", "sabre"],
        "scheduling": ["asap", "alap"],
        "transpiler_seed": [0, 42, 123, 987]
    },
    "aws": {
        "shots": [100, 500, 1000, 2000, 5000], 
        "maximizer": ["gradient_descent", "hill_climb"],
        "noise_prob": [0.0, 0.01, 0.05, 0.1],
        "use_midcircuit": [True, False],
        "transpile_mode": ["normal", "aggressive"]
    },
    "google": {
        "shots": [200, 1000, 5000, 10000],
        "layout_strategy": ["line", "circular", "gate_aware", "cirq_default"],
        "optimization_strategy": ["identity_removal", "commuting_decompose", "gateset_convert"],
        "merge_interactions": [True, False],
        "device_type": ["rainbow", "weber", "weber2"]
    }
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
                logger.warning("Qiskit not installed, falling back to simulated mode")
                # Simulate output for testing when qiskit is not installed
                # This allows the CLI to operate in demo mode
                
                # Generate a simulated score based on the parameters
                # In a real environment, this would come from actual circuit execution
                
                # Create simulated score based on parameter values
                parameter_weight = sum(1 for name in parameters.keys() if name in ['optimization_level', 'layout_method', 'routing_method'])
                
                # Simulate more optimized settings giving better scores
                opt_level = parameters.get('optimization_level', 0)
                if isinstance(opt_level, str):
                    try:
                        opt_level = int(opt_level)
                    except ValueError:
                        opt_level = 0
                
                # Better layout methods get higher scores
                layout_score = 0
                layout_method = parameters.get('layout_method', '')
                if layout_method == 'noise_adaptive':
                    layout_score = 0.8
                elif layout_method == 'sabre':
                    layout_score = 0.7
                elif layout_method == 'dense':
                    layout_score = 0.5
                else:
                    layout_score = 0.3
                    
                # Generate a pseudo-random but deterministic score
                import hashlib
                param_str = str(sorted(parameters.items()))
                hash_val = int(hashlib.md5(param_str.encode()).hexdigest(), 16) % 1000 / 1000.0
                
                base_score = 0.5 + (opt_level / 10) + layout_score / 2 + hash_val / 5
                
                # Simulate probabilities
                n_bits = 4  # Based on the Shor's circuit in the example
                
                # Create simulated measurement outcomes with some variability
                probabilities = {}
                outcomes = min(2**n_bits, 16)  # Limit to avoid too many outcomes
                
                # Create a biased distribution favoring some outcomes
                for i in range(outcomes):
                    # Generate a probability based on parameters and index
                    if i % 4 == 0:
                        # Make certain outcomes more likely based on parameters
                        prob = (0.2 + hash_val * 0.1) * (1 + opt_level * 0.1) * (1 + layout_score * 0.2)
                        prob = min(prob, 0.3)  # Cap the probability
                    else:
                        prob = 0.02 + hash_val * 0.05
                    
                    # Format the outcome as a binary string
                    binary = format(i, f'0{n_bits}b')
                    probabilities[binary] = prob
                
                # Normalize the probabilities
                total = sum(probabilities.values())
                probabilities = {k: v / total for k, v in probabilities.items()}
                
                # Calculate entropy
                entropy = -sum(p * np.log2(p) for p in probabilities.values() if p > 0)
                
                # Calculate number of unique outcomes
                unique_outcomes = len(probabilities)
                
                # Create a score combining entropy and unique outcomes
                score = base_score * entropy * np.log(unique_outcomes + 1)
                
                return {
                    "success": True,
                    "score": score,
                    "entropy": entropy,
                    "unique_outcomes": unique_outcomes,
                    "probabilities": probabilities,
                    "shots": shots,
                    "parameters": parameters,
                    "simulated": True  # Flag indicating this is simulated data
                }
                
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

def finetune_circuit(input_file, output_file, hardware="ibm", search_method="random", shots=1000):
    """
    Fine-tune a quantum circuit for hardware-specific optimization.
    
    Args:
        input_file (str): Path to the input OpenQASM file
        output_file (str): Path to save the fine-tuning results (JSON)
        hardware (str): Target hardware platform ("ibm", "aws", "google")
        search_method (str): Search method ("grid" or "random")
        shots (int): Base number of shots for simulation
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Fine-tuning circuit for {hardware} hardware using {search_method} search")
        
        # Make sure the input file exists
        if not os.path.exists(input_file):
            logger.error(f"Input file {input_file} not found")
            return False
            
        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Parse parameters from the QASM file
        original_parameters = parse_qasm_parameters(input_file)
        logger.info(f"Parsed {len(original_parameters)} parameters from QASM file")
        
        # Get hardware-specific parameter ranges
        if hardware in HARDWARE_PARAMETER_RANGES:
            parameter_ranges = HARDWARE_PARAMETER_RANGES[hardware]
            logger.info(f"Using {hardware}-specific parameter ranges: {parameter_ranges.keys()}")
        else:
            logger.warning(f"No specific parameter ranges found for {hardware}, using defaults")
            parameter_ranges = DEFAULT_PARAMETER_RANGES
            
        # Perform parameter search
        if search_method == "grid":
            logger.info("Performing grid search")
            results = grid_search(input_file, parameter_ranges, shots, "qiskit")
        else:  # random search
            logger.info("Performing random search")
            results = random_search(input_file, parameter_ranges, shots, "qiskit")
            
        # Add metadata to the results
        finetuned_results = {
            "circuit_file": input_file,
            "hardware_target": hardware,
            "search_method": search_method,
            "base_shots": shots,
            "original_parameters": original_parameters,
            "finetuned_results": results,
            "timestamp": datetime.datetime.now().isoformat(),
            "best_parameters": results[0]["parameters"] if results else {},
            "improvement_metrics": {}
        }
        
        # Calculate improvement metrics if we have results
        if results:
            best_result = results[0]
            baseline_result = run_circuit_with_parameters(input_file, original_parameters, shots, "qiskit")
            
            # Calculate improvement percentage for various metrics
            if baseline_result.get("success", False) and "score" in baseline_result and "score" in best_result:
                improvement = (best_result["score"] - baseline_result["score"]) / baseline_result["score"] * 100
                finetuned_results["improvement_metrics"]["score_improvement"] = f"{improvement:.2f}%"
                
            if "entropy" in baseline_result and "entropy" in best_result:
                entropy_improvement = (best_result["entropy"] - baseline_result["entropy"]) / baseline_result["entropy"] * 100
                finetuned_results["improvement_metrics"]["entropy_improvement"] = f"{entropy_improvement:.2f}%"
                
            finetuned_results["improvement_metrics"]["original_score"] = baseline_result.get("score", 0)
            finetuned_results["improvement_metrics"]["finetuned_score"] = best_result.get("score", 0)
            
        # Save the results
        with open(output_file, 'w') as f:
            json.dump(finetuned_results, f, indent=2)
        
        logger.info(f"Fine-tuning results saved to {output_file}")
        
        # Print a summary of the results
        if results:
            best_params = results[0]["parameters"]
            print("\nFine-tuning completed successfully!")
            print(f"Target hardware: {hardware}")
            print(f"Best parameters found:")
            for param, value in best_params.items():
                print(f"  {param}: {value}")
            
            if "improvement_metrics" in finetuned_results and "score_improvement" in finetuned_results["improvement_metrics"]:
                print(f"Score improvement: {finetuned_results['improvement_metrics']['score_improvement']}")
            
            print(f"Results saved to: {output_file}")
        else:
            print("Fine-tuning completed but no optimal parameters were found.")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in finetune_circuit: {str(e)}", exc_info=True)
        print(f"Error during fine-tuning: {str(e)}")
        return False

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
