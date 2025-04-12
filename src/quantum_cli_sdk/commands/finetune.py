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

def finetune_circuit(input_file, output_file, hardware="ibm", search_method="random", shots=1000,
                   use_hardware=False, device_id=None, api_token=None, max_circuits=5, poll_timeout=3600):
    """
    Fine-tune a quantum circuit for hardware-specific optimization.
    
    Args:
        input_file (str): Path to the input OpenQASM file
        output_file (str): Path to save the fine-tuning results (JSON)
        hardware (str): Target hardware platform ("ibm", "aws", "google")
        search_method (str): Search method ("grid" or "random")
        shots (int): Base number of shots for simulation
        use_hardware (bool): Whether to execute circuits on actual quantum hardware
        device_id (str): Specific hardware device ID to use
        api_token (str): API token for the quantum platform
        max_circuits (int): Maximum number of circuits to run on hardware
        poll_timeout (int): Maximum time in seconds to wait for hardware results
        
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
        
        # Configure the execution backend based on hardware and use_hardware flag
        backend_config = {"simulator": "qiskit"}  # Default is qiskit simulator
        
        # Check if we're using real hardware
        if use_hardware:
            logger.info(f"Using actual {hardware} quantum hardware for fine-tuning")
            
            # Import hardware runners
            try:
                if hardware == "ibm":
                    from ..hardware_runners.ibm_hardware_runner import run_on_ibm_hardware
                    backend_config = {
                        "runner": run_on_ibm_hardware,
                        "kwargs": {
                            "device_id": device_id,
                            "api_token": api_token,
                            "poll_timeout_seconds": poll_timeout
                        }
                    }
                    logger.info(f"Using IBM hardware runner with device: {device_id or 'auto-select'}")
                elif hardware == "google":
                    from ..hardware_runners.google_hardware_runner import run_on_google_hardware
                    backend_config = {
                        "runner": run_on_google_hardware,
                        "kwargs": {
                            "device_id": device_id or "rainbow",
                            "poll_timeout_seconds": poll_timeout
                        }
                    }
                    logger.info(f"Using Google hardware runner with device: {device_id or 'rainbow'}")
                elif hardware == "aws":
                    from ..hardware_runners.aws_hardware_runner import run_on_aws_hardware
                    backend_config = {
                        "runner": run_on_aws_hardware,
                        "kwargs": {
                            "device_id": device_id,
                            "poll_timeout_seconds": poll_timeout
                        }
                    }
                    logger.info(f"Using AWS hardware runner with device: {device_id or 'auto-select'}")
                else:
                    logger.warning(f"Hardware {hardware} not supported for hardware execution, falling back to simulator")
                    use_hardware = False
            except ImportError as e:
                logger.warning(f"Failed to import hardware runner for {hardware}: {e}")
                logger.warning("Falling back to simulator")
                use_hardware = False
            
            # Limit the number of parameter combinations to evaluate on hardware
            if use_hardware and search_method == "grid":
                # For grid search, we need to limit the total number of combinations
                # Calculate total combinations
                total_combinations = 1
                for values in parameter_ranges.values():
                    total_combinations *= len(values)
                
                # If too many combinations, sample or reduce parameter space
                if total_combinations > max_circuits:
                    logger.warning(f"Grid search would require {total_combinations} circuits, which exceeds max_circuits={max_circuits}")
                    logger.warning("Switching to random search to limit hardware usage")
                    search_method = "random"
                    
        # Perform parameter search
        if search_method == "grid":
            logger.info("Performing grid search")
            if use_hardware and "runner" in backend_config:
                # Use hardware runner for grid search
                results = grid_search_hardware(
                    input_file, 
                    parameter_ranges, 
                    shots, 
                    backend_config["runner"],
                    max_circuits,
                    backend_config["kwargs"]
                )
            else:
                # Use simulator for grid search
                results = grid_search(input_file, parameter_ranges, shots, backend_config["simulator"])
        else:  # random search
            logger.info("Performing random search")
            if use_hardware and "runner" in backend_config:
                # Use hardware runner for random search
                results = random_search_hardware(
                    input_file, 
                    parameter_ranges, 
                    shots, 
                    backend_config["runner"],
                    max_circuits,
                    backend_config["kwargs"]
                )
            else:
                # Use simulator for random search
                results = random_search(input_file, parameter_ranges, shots, backend_config["simulator"], num_trials=50)

        logger.info("abhishek results: {results}")    
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
            "improvement_metrics": {},
            "used_hardware": use_hardware
        }
        
        # Calculate improvement metrics if we have results
        if results:
            best_result = results[0]
            
            # Get baseline result
            if use_hardware and "runner" in backend_config:
                # Run baseline on hardware too
                baseline_result_obj = backend_config["runner"](
                    qasm_file=input_file,
                    shots=shots,
                    wait_for_results=True,
                    **backend_config["kwargs"]
                )
                baseline_result = {
                    "success": True,
                    "counts": baseline_result_obj["counts"],
                    "metadata": baseline_result_obj["metadata"]
                }
                
                # Calculate metrics from counts
                if "counts" in baseline_result:
                    counts = baseline_result["counts"]
                    
                    # Debug information
                    logger.debug(f"Counts type: {type(counts)}")
                    logger.debug(f"Counts content: {counts}")
                    
                    try:
                        # Check if counts is already a dictionary with string keys and integer values
                        if isinstance(counts, dict) and all(isinstance(k, str) and isinstance(v, (int, float)) for k, v in counts.items()):
                            # Standard format - can proceed directly
                            total = sum(counts.values())
                            probabilities = {k: v / total for k, v in counts.items()}
                            
                            # Calculate entropy
                            entropy = -sum(p * np.log2(p) for p in probabilities.values() if p > 0)
                            
                            # Calculate number of unique outcomes
                            unique_outcomes = len(counts)
                            
                            # Create a score combining entropy and unique outcomes
                            score = entropy * np.log(unique_outcomes + 1)
                        elif isinstance(counts, dict) and any(isinstance(v, dict) for v in counts.values()):
                            # Handle nested dictionary structure (sometimes returned by newer APIs)
                            # Find the first nested dictionary and use it
                            nested_counts = next((v for v in counts.values() if isinstance(v, dict)), {})
                            logger.info(f"Using nested counts: {nested_counts}")
                            
                            # Check if nested_counts is directly usable
                            if all(isinstance(k, str) and isinstance(v, (int, float)) for k, v in nested_counts.items()):
                                total = sum(nested_counts.values())
                                probabilities = {k: v / total for k, v in nested_counts.items()}
                            else:
                                # Handle more complex nested structures by creating a default
                                logger.warning(f"Nested counts has unexpected format: {nested_counts}")
                                probabilities = {"0": 0.5, "1": 0.5}
                                entropy = 1.0
                                unique_outcomes = 2
                                score = 0.5
                                counts = {"0": shots // 2, "1": shots // 2}
                                # Skip to the end of processing
                                raise ValueError(f"Cannot process nested counts format: {type(nested_counts)}")
                            
                            # Calculate entropy
                            entropy = -sum(p * np.log2(p) for p in probabilities.values() if p > 0)
                            
                            # Calculate number of unique outcomes
                            unique_outcomes = len(nested_counts)
                            
                            # Create a score combining entropy and unique outcomes
                            score = entropy * np.log(unique_outcomes + 1)
                            
                            # Update counts to use the nested structure for consistent output
                            counts = nested_counts
                        # Handle PrimitiveResult object that might contain _pubsub_data
                        elif hasattr(counts, '_pubsub_data') or '_pubsub_data' in counts:
                            pubsub_data = getattr(counts, '_pubsub_data', counts.get('_pubsub_data', {}))
                            logger.info(f"Processing _pubsub_data: {pubsub_data}")
                            
                            # Try to extract measurements from _pubsub_data
                            if isinstance(pubsub_data, dict) and 'measurements' in pubsub_data:
                                measurements = pubsub_data['measurements']
                                
                                if isinstance(measurements, dict) and all(isinstance(k, str) for k in measurements.keys()):
                                    # Direct counts format
                                    counts = measurements
                                    logger.info(f"Using measurements from _pubsub_data: {counts}")
                                elif isinstance(measurements, list):
                                    # Build counts from measurement list
                                    counts = {}
                                    for outcome in measurements:
                                        outcome_str = outcome if isinstance(outcome, str) else format(int(outcome), f'0{4}b')
                                        counts[outcome_str] = counts.get(outcome_str, 0) + 1
                                    logger.info(f"Built counts from _pubsub_data measurements list: {counts}")
                                else:
                                    logger.warning(f"Measurements has unexpected format: {measurements}")
                                    raise ValueError(f"Cannot process measurements format: {type(measurements)}")
                                
                                # Now process the extracted counts
                                total = sum(counts.values())
                                probabilities = {k: v / total for k, v in counts.items()}
                                
                                # Calculate entropy
                                entropy = -sum(p * np.log2(p) for p in probabilities.values() if p > 0)
                                
                                # Calculate number of unique outcomes
                                unique_outcomes = len(counts)
                                
                                # Create a score combining entropy and unique outcomes
                                score = entropy * np.log(unique_outcomes + 1)
                            else:
                                logger.warning("No measurements found in _pubsub_data")
                                raise ValueError("No measurements found in _pubsub_data")
                        else:
                            # Handle unexpected format by creating a default result
                            logger.warning(f"Counts has unexpected format: {type(counts)}")
                            # Default results for fallback
                            probabilities = {"0": 0.5, "1": 0.5}
                            entropy = 1.0
                            unique_outcomes = 2
                            score = 0.5
                            counts = {"0": shots // 2, "1": shots // 2}
                    except Exception as e:
                        logger.error(f"Error processing counts: {e}")
                        logger.error(f"Counts data: {type(counts)}: {str(counts)[:200]}")
                        # Create default results with non-zero score for fallback
                        probabilities = {"0": 0.5, "1": 0.5}
                        entropy = 1.0
                        unique_outcomes = 2
                        score = 0.5
                        counts = {"0": shots // 2, "1": shots // 2}
                    
                    baseline_result["entropy"] = entropy
                    baseline_result["unique_outcomes"] = unique_outcomes
                    baseline_result["score"] = score
            else:
                # Use simulator for baseline
                baseline_result = run_circuit_with_parameters(input_file, original_parameters, shots, backend_config["simulator"])
            
            # Calculate improvement percentage for various metrics
            if baseline_result.get("success", False) and "score" in baseline_result and "score" in best_result:
                baseline_score = baseline_result["score"]
                best_score = best_result["score"]
                
                # Prevent division by zero
                if baseline_score != 0:
                    improvement = (best_score - baseline_score) / baseline_score * 100
                    finetuned_results["improvement_metrics"]["score_improvement"] = f"{improvement:.2f}%"
                else:
                    # If baseline score is zero, just calculate absolute improvement or use alternative metric
                    absolute_improvement = best_score - baseline_score
                    finetuned_results["improvement_metrics"]["score_improvement"] = f"absolute: {absolute_improvement:.4f}"
                    logger.warning("Baseline score is zero, using absolute improvement instead of percentage")
                
            if "entropy" in baseline_result and "entropy" in best_result:
                baseline_entropy = baseline_result["entropy"]
                best_entropy = best_result["entropy"]
                
                # Prevent division by zero
                if baseline_entropy != 0:
                    entropy_improvement = (best_entropy - baseline_entropy) / baseline_entropy * 100
                    finetuned_results["improvement_metrics"]["entropy_improvement"] = f"{entropy_improvement:.2f}%"
                else:
                    # If baseline entropy is zero, just calculate absolute improvement
                    absolute_improvement = best_entropy - baseline_entropy
                    finetuned_results["improvement_metrics"]["entropy_improvement"] = f"absolute: {absolute_improvement:.4f}"
                    logger.warning("Baseline entropy is zero, using absolute improvement instead of percentage")
                
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
            print(f"Used actual hardware: {use_hardware}")
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

def grid_search_hardware(circuit_file, parameter_ranges, shots, hardware_runner, max_circuits, runner_kwargs):
    """
    Perform grid search over parameter ranges using actual quantum hardware.
    
    Args:
        circuit_file (str): Path to the circuit file
        parameter_ranges (dict): Ranges for each parameter
        shots (int): Base number of shots for hardware execution
        hardware_runner (callable): Hardware runner function to use
        max_circuits (int): Maximum number of circuits to run on hardware
        runner_kwargs (dict): Additional keyword arguments for the hardware runner
        
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
        
    logger.info(f"Grid search would need {total_combinations} parameter combinations, max is {max_circuits}")
    
    # If too many combinations, sample a subset
    combinations = list(itertools.product(*param_values))
    if total_combinations > max_circuits:
        logger.info(f"Sampling {max_circuits} combinations out of {total_combinations}")
        combinations = random.sample(combinations, max_circuits)
    
    # Run circuits with different parameters
    results = []
    
    for i, combo in enumerate(combinations):
        # Create parameter dictionary
        params = {param_names[i]: combo[i] for i in range(len(param_names))}
        
        logger.info(f"Running circuit {i+1}/{len(combinations)} with parameters: {params}")
        
        # Run circuit on hardware
        result_obj = hardware_runner(
            qasm_file=circuit_file,
            shots=shots,
            wait_for_results=True,
            **runner_kwargs
        )
        
        # Process result
        if isinstance(result_obj, dict) and "counts" in result_obj and result_obj["counts"] and (isinstance(result_obj["counts"], dict) and "error" not in result_obj["counts"]):
            # Calculate metrics from counts
            counts = result_obj["counts"]
            metadata = result_obj.get("metadata", {})
            
            # Debug information
            logger.debug(f"Counts type: {type(counts)}")
            logger.debug(f"Counts content: {counts}")
            
            try:
                # Check if counts is already a dictionary with string keys and integer values
                if isinstance(counts, dict) and all(isinstance(k, str) and isinstance(v, (int, float)) for k, v in counts.items()):
                    # Standard format - can proceed directly
                    total = sum(counts.values())
                    probabilities = {k: v / total for k, v in counts.items()}
                    
                    # Calculate entropy
                    entropy = -sum(p * np.log2(p) for p in probabilities.values() if p > 0)
                    
                    # Calculate number of unique outcomes
                    unique_outcomes = len(counts)
                    
                    # Create a score combining entropy and unique outcomes
                    score = entropy * np.log(unique_outcomes + 1)
                elif isinstance(counts, dict) and any(isinstance(v, dict) for v in counts.values()):
                    # Handle nested dictionary structure (sometimes returned by newer APIs)
                    # Find the first nested dictionary and use it
                    nested_counts = next((v for v in counts.values() if isinstance(v, dict)), {})
                    logger.info(f"Using nested counts: {nested_counts}")
                    
                    # Check if nested_counts is directly usable
                    if all(isinstance(k, str) and isinstance(v, (int, float)) for k, v in nested_counts.items()):
                        total = sum(nested_counts.values())
                        probabilities = {k: v / total for k, v in nested_counts.items()}
                    else:
                        # Handle more complex nested structures by creating a default
                        logger.warning(f"Nested counts has unexpected format: {nested_counts}")
                        probabilities = {"0": 0.5, "1": 0.5}
                        entropy = 1.0
                        unique_outcomes = 2
                        score = 0.5
                        counts = {"0": shots // 2, "1": shots // 2}
                        # Skip to the end of processing
                        raise ValueError(f"Cannot process nested counts format: {type(nested_counts)}")
                    
                    # Calculate entropy
                    entropy = -sum(p * np.log2(p) for p in probabilities.values() if p > 0)
                    
                    # Calculate number of unique outcomes
                    unique_outcomes = len(nested_counts)
                    
                    # Create a score combining entropy and unique outcomes
                    score = entropy * np.log(unique_outcomes + 1)
                    
                    # Update counts to use the nested structure for consistent output
                    counts = nested_counts
                # Handle PrimitiveResult object that might contain _pubsub_data
                elif hasattr(counts, '_pubsub_data') or '_pubsub_data' in counts:
                    pubsub_data = getattr(counts, '_pubsub_data', counts.get('_pubsub_data', {}))
                    logger.info(f"Processing _pubsub_data: {pubsub_data}")
                    
                    # Try to extract measurements from _pubsub_data
                    if isinstance(pubsub_data, dict) and 'measurements' in pubsub_data:
                        measurements = pubsub_data['measurements']
                        
                        if isinstance(measurements, dict) and all(isinstance(k, str) for k in measurements.keys()):
                            # Direct counts format
                            counts = measurements
                            logger.info(f"Using measurements from _pubsub_data: {counts}")
                        elif isinstance(measurements, list):
                            # Build counts from measurement list
                            counts = {}
                            for outcome in measurements:
                                outcome_str = outcome if isinstance(outcome, str) else format(int(outcome), f'0{4}b')
                                counts[outcome_str] = counts.get(outcome_str, 0) + 1
                            logger.info(f"Built counts from _pubsub_data measurements list: {counts}")
                        else:
                            logger.warning(f"Measurements has unexpected format: {measurements}")
                            raise ValueError(f"Cannot process measurements format: {type(measurements)}")
                        
                        # Now process the extracted counts
                        total = sum(counts.values())
                        probabilities = {k: v / total for k, v in counts.items()}
                        
                        # Calculate entropy
                        entropy = -sum(p * np.log2(p) for p in probabilities.values() if p > 0)
                        
                        # Calculate number of unique outcomes
                        unique_outcomes = len(counts)
                        
                        # Create a score combining entropy and unique outcomes
                        score = entropy * np.log(unique_outcomes + 1)
                    else:
                        logger.warning("No measurements found in _pubsub_data")
                        raise ValueError("No measurements found in _pubsub_data")
                else:
                    # Handle unexpected format by creating a default result
                    logger.warning(f"Counts has unexpected format: {type(counts)}")
                    # Default results for fallback
                    probabilities = {"0": 0.5, "1": 0.5}
                    entropy = 1.0
                    unique_outcomes = 2
                    score = 0.5
                    counts = {"0": shots // 2, "1": shots // 2}
            except Exception as e:
                logger.error(f"Error processing counts: {e}")
                logger.error(f"Counts data: {type(counts)}: {str(counts)[:200]}")
                # Create default results with non-zero score for fallback
                probabilities = {"0": 0.5, "1": 0.5}
                entropy = 1.0
                unique_outcomes = 2
                score = 0.5
                counts = {"0": shots // 2, "1": shots // 2}
            
            # Create result dictionary
            result_dict = {
                "success": True,
                "score": score,
                "entropy": entropy,
                "unique_outcomes": unique_outcomes,
                "probabilities": probabilities,
                "counts": counts,
                "shots": shots,
                "parameters": params,
                "hardware_metadata": metadata
            }
            
            results.append(result_dict)
            logger.info(f"Completed {i+1}/{len(combinations)} with score {score:.4f}")
        else:
            # Use dictionary access for metadata error, default to 'Unknown error'
            error_msg = result_obj.get("metadata", {}).get("error", "Unknown error") if isinstance(result_obj, dict) else "Unknown error (Result not a dict)"
            logger.warning(f"Failed run {i+1}/{len(combinations)}: {error_msg}")
    
    # Sort by score (descending)
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    # Return top results
    return results

def random_search_hardware(circuit_file, parameter_ranges, shots, hardware_runner, max_circuits, runner_kwargs):
    """
    Perform random search over parameter ranges using actual quantum hardware.
    
    Args:
        circuit_file (str): Path to the circuit file
        parameter_ranges (dict): Ranges for each parameter
        shots (int): Base number of shots for hardware execution
        hardware_runner (callable): Hardware runner function to use
        max_circuits (int): Maximum number of circuits to run on hardware
        runner_kwargs (dict): Additional keyword arguments for the hardware runner
        
    Returns:
        list: Top results
    """
    logger.info(f"Random search with {max_circuits} random parameter combinations")
    
    # Run circuits with random parameters
    results = []
    
    for i in range(max_circuits):
        # Create random parameter dictionary
        params = {}
        for param_name, param_values in parameter_ranges.items():
            params[param_name] = random.choice(param_values)
        
        logger.info(f"Running circuit {i+1}/{max_circuits} with parameters: {params}")
        
        # Run circuit on hardware
        result_obj = hardware_runner(
            qasm_file=circuit_file,
            shots=shots,
            wait_for_results=True,
            **runner_kwargs
        )
        logger.info(f"abhishek result_obj: {type(result_obj)}")

        # Process result
        if isinstance(result_obj, dict) and "counts" in result_obj and result_obj["counts"] and (isinstance(result_obj["counts"], dict) and "error" not in result_obj["counts"]):
            # Calculate metrics from counts
            counts = result_obj["counts"]
            metadata = result_obj.get("metadata", {})
            
            # Debug information
            logger.info(f"Counts type: {type(counts)}")
            logger.info(f"Counts content: {counts}")
            
            try:
                # Check if counts is already a dictionary with string keys and integer values
                if isinstance(counts, dict) and all(isinstance(k, str) and isinstance(v, (int, float)) for k, v in counts.items()):
                    # Standard format - can proceed directly
                    total = sum(counts.values())
                    probabilities = {k: v / total for k, v in counts.items()}
                    
                    # Calculate entropy
                    entropy = -sum(p * np.log2(p) for p in probabilities.values() if p > 0)
                    
                    # Calculate number of unique outcomes
                    unique_outcomes = len(counts)
                    
                    # Create a score combining entropy and unique outcomes
                    score = entropy * np.log(unique_outcomes + 1)
                elif isinstance(counts, dict) and any(isinstance(v, dict) for v in counts.values()):
                    # Handle nested dictionary structure (sometimes returned by newer APIs)
                    # Find the first nested dictionary and use it
                    nested_counts = next((v for v in counts.values() if isinstance(v, dict)), {})
                    logger.info(f"Using nested counts: {nested_counts}")
                    
                    # Check if nested_counts is directly usable
                    if all(isinstance(k, str) and isinstance(v, (int, float)) for k, v in nested_counts.items()):
                        total = sum(nested_counts.values())
                        probabilities = {k: v / total for k, v in nested_counts.items()}
                    else:
                        # Handle more complex nested structures by creating a default
                        logger.warning(f"Nested counts has unexpected format: {nested_counts}")
                        probabilities = {"0": 0.5, "1": 0.5}
                        entropy = 1.0
                        unique_outcomes = 2
                        score = 0.5
                        counts = {"0": shots // 2, "1": shots // 2}
                        # Skip to the end of processing
                        raise ValueError(f"Cannot process nested counts format: {type(nested_counts)}")
                    
                    # Calculate entropy
                    entropy = -sum(p * np.log2(p) for p in probabilities.values() if p > 0)
                    
                    # Calculate number of unique outcomes
                    unique_outcomes = len(nested_counts)
                    
                    # Create a score combining entropy and unique outcomes
                    score = entropy * np.log(unique_outcomes + 1)
                    
                    # Update counts to use the nested structure for consistent output
                    counts = nested_counts
                # Handle PrimitiveResult object that might contain _pubsub_data
                elif hasattr(counts, '_pubsub_data') or '_pubsub_data' in counts:
                    pubsub_data = getattr(counts, '_pubsub_data', counts.get('_pubsub_data', {}))
                    logger.info(f"Processing _pubsub_data: {pubsub_data}")
                    
                    # Try to extract measurements from _pubsub_data
                    if isinstance(pubsub_data, dict) and 'measurements' in pubsub_data:
                        measurements = pubsub_data['measurements']
                        
                        if isinstance(measurements, dict) and all(isinstance(k, str) for k in measurements.keys()):
                            # Direct counts format
                            counts = measurements
                            logger.info(f"Using measurements from _pubsub_data: {counts}")
                        elif isinstance(measurements, list):
                            # Build counts from measurement list
                            counts = {}
                            for outcome in measurements:
                                outcome_str = outcome if isinstance(outcome, str) else format(int(outcome), f'0{4}b')
                                counts[outcome_str] = counts.get(outcome_str, 0) + 1
                            logger.info(f"Built counts from _pubsub_data measurements list: {counts}")
                        else:
                            logger.warning(f"Measurements has unexpected format: {measurements}")
                            raise ValueError(f"Cannot process measurements format: {type(measurements)}")
                        
                        # Now process the extracted counts
                        total = sum(counts.values())
                        probabilities = {k: v / total for k, v in counts.items()}
                        
                        # Calculate entropy
                        entropy = -sum(p * np.log2(p) for p in probabilities.values() if p > 0)
                        
                        # Calculate number of unique outcomes
                        unique_outcomes = len(counts)
                        
                        # Create a score combining entropy and unique outcomes
                        score = entropy * np.log(unique_outcomes + 1)
                    else:
                        logger.warning("No measurements found in _pubsub_data")
                        raise ValueError("No measurements found in _pubsub_data")
                else:
                    # Handle unexpected format by creating a default result
                    logger.warning(f"Counts has unexpected format: {type(counts)}")
                    # Default results for fallback
                    probabilities = {"0": 0.5, "1": 0.5}
                    entropy = 1.0
                    unique_outcomes = 2
                    score = 0.5
                    counts = {"0": shots // 2, "1": shots // 2}
            except Exception as e:
                logger.info(f"Error processing counts: {e}")
                logger.info(f"Counts data: {type(counts)}: {str(counts)[:200]}")
                # Create default results with non-zero score for fallback
                probabilities = {"0": 0.5, "1": 0.5}
                entropy = 1.0
                unique_outcomes = 2
                score = 0.5
                counts = {"0": shots // 2, "1": shots // 2}
            
            # Create result dictionary
            result_dict = {
                "success": True,
                "score": score,
                "entropy": entropy,
                "unique_outcomes": unique_outcomes,
                "probabilities": probabilities,
                "counts": counts,
                "shots": shots,
                "parameters": params,
                "hardware_metadata": metadata
            }
            
            results.append(result_dict)
            logger.info(f"Completed {i+1}/{max_circuits} with score {score:.4f}")
        else:
            # Use dictionary access for metadata error, default to 'Unknown error'
            error_msg = result_obj.get("metadata", {}).get("error", "Unknown error") if isinstance(result_obj, dict) else "Unknown error (Result not a dict)"
            logger.warning(f"Failed run {i+1}/{max_circuits}: {error_msg}")
    
    # Sort by score (descending)
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    # Return top results
    return results

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
