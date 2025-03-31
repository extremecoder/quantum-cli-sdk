"""
Run trial evaluations of quantum circuits with different parameters.
"""

import os
import sys
import logging
import json
import random
import time
import numpy as np
from pathlib import Path

from ..config import get_config
from ..trial_manager import TrialManager
from ..output_formatter import format_output
from ..utils import load_config, validate_config

# Set up logger
logger = logging.getLogger(__name__)

def parse_qasm_file(circuit_file):
    """
    Parse QASM file and extract parameters if any.
    
    Args:
        circuit_file (str): Path to circuit file
    
    Returns:
        tuple: (circuit_content, parameters)
    """
    try:
        with open(circuit_file, 'r') as f:
            content = f.read()
            
        # Extract parameters defined in the circuit
        import re
        param_pattern = r'parameter\s+([a-zA-Z0-9_]+)'
        parameters = re.findall(param_pattern, content)
        
        return content, parameters
    except Exception as e:
        logger.error(f"Error parsing QASM file: {e}")
        return None, []

def generate_random_parameters(parameters, num_trials=5):
    """
    Generate random parameter values for trials.
    
    Args:
        parameters (list): List of parameter names
        num_trials (int): Number of trial configurations to generate
    
    Returns:
        list: List of parameter dictionaries
    """
    if not parameters:
        return [{}]
        
    trials = []
    for _ in range(num_trials):
        trial_params = {}
        for param in parameters:
            # Generate a random value between 0 and 2π
            trial_params[param] = round(random.uniform(0, 2 * np.pi), 4)
        trials.append(trial_params)
        
    return trials

def apply_parameters_to_circuit(circuit_content, parameters):
    """
    Apply parameter values to circuit content.
    
    Args:
        circuit_content (str): QASM circuit content
        parameters (dict): Parameter values
    
    Returns:
        str: Updated circuit content
    """
    updated_content = circuit_content
    
    for param_name, param_value in parameters.items():
        # Replace parameter declarations with values
        pattern = f'parameter\\s+{param_name}'
        replacement = f'// parameter {param_name} = {param_value}'
        updated_content = re.sub(pattern, replacement, updated_content)
        
        # Replace parameter references with values
        pattern = f'{param_name}'
        replacement = str(param_value)
        # Only replace in mathematical contexts (avoid replacing variable names elsewhere)
        updated_content = re.sub(f'([^a-zA-Z0-9_]){pattern}([^a-zA-Z0-9_])', f'\\1{replacement}\\2', updated_content)
        
    return updated_content

def run_circuit_trial(circuit_content, simulator="qiskit", shots=1024):
    """
    Run a circuit trial using the specified simulator.
    
    Args:
        circuit_content (str): QASM circuit content
        simulator (str): Simulator to use (qiskit, cirq, braket)
        shots (int): Number of shots
    
    Returns:
        dict: Results of the simulation
    """
    try:
        import tempfile
        
        # Write the circuit content to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.qasm', delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(circuit_content)
        
        try:
            # Run the circuit using the specified simulator
            if simulator == "qiskit":
                from qiskit import QuantumCircuit, Aer, execute
                
                # Load circuit from file
                circuit = QuantumCircuit.from_qasm_str(circuit_content)
                
                # Add measurements if not present
                if not circuit.clbits:
                    circuit.measure_all()
                
                # Run simulation
                simulator_backend = Aer.get_backend('qasm_simulator')
                job = execute(circuit, simulator_backend, shots=shots)
                result = job.result()
                
                # Process results
                counts = result.get_counts()
                
                # Calculate metrics
                entropy = 0
                for outcome, count in counts.items():
                    probability = count / shots
                    entropy -= probability * np.log2(probability)
                
                unique_outcomes = len(counts)
                most_common = max(counts.items(), key=lambda x: x[1])[0]
                
                return {
                    "counts": counts,
                    "entropy": float(entropy),
                    "unique_outcomes": unique_outcomes,
                    "most_common": most_common,
                    "shots": shots
                }
                
            elif simulator == "cirq":
                import cirq
                import cirq_qasm
                
                # Parse QASM
                parser = cirq_qasm.QasmParser()
                circuit = parser.parse(circuit_content)
                
                # Run simulation
                simulator = cirq.Simulator()
                result = simulator.run(circuit, repetitions=shots)
                
                # Process results
                measurements = result.measurements
                if not measurements:
                    # For circuits without explicit measurements
                    counts = {"0": shots}
                    entropy = 0
                    unique_outcomes = 1
                    most_common = "0"
                else:
                    # Convert measurements to counts
                    key = list(measurements.keys())[0]
                    bitstrings = []
                    for bits in measurements[key]:
                        bitstring = ''.join(str(int(b)) for b in bits)
                        bitstrings.append(bitstring)
                    
                    # Count unique bitstrings
                    counts = {}
                    for bitstring in bitstrings:
                        if bitstring not in counts:
                            counts[bitstring] = 0
                        counts[bitstring] += 1
                    
                    # Calculate metrics
                    entropy = 0
                    for outcome, count in counts.items():
                        probability = count / shots
                        entropy -= probability * np.log2(probability)
                    
                    unique_outcomes = len(counts)
                    most_common = max(counts.items(), key=lambda x: x[1])[0]
                
                return {
                    "counts": counts,
                    "entropy": float(entropy),
                    "unique_outcomes": unique_outcomes,
                    "most_common": most_common,
                    "shots": shots
                }
                
            elif simulator == "braket":
                from braket.circuits import Circuit
                from braket.devices import LocalSimulator
                
                # Create circuit from QASM
                circuit = Circuit.from_openqasm(circuit_content)
                
                # Run simulation
                device = LocalSimulator()
                task = device.run(circuit, shots=shots)
                result = task.result()
                
                # Process results
                counts = result.measurement_counts
                
                # Calculate metrics
                entropy = 0
                for outcome, count in counts.items():
                    probability = count / shots
                    entropy -= probability * np.log2(probability)
                
                unique_outcomes = len(counts)
                most_common = max(counts.items(), key=lambda x: x[1])[0]
                
                return {
                    "counts": counts,
                    "entropy": float(entropy),
                    "unique_outcomes": unique_outcomes,
                    "most_common": most_common,
                    "shots": shots
                }
                
            else:
                logger.error(f"Unsupported simulator: {simulator}")
                return {"error": f"Unsupported simulator: {simulator}"}
                
        finally:
            # Clean up temporary file
            os.remove(tmp_path)
            
    except ImportError as e:
        logger.error(f"Missing dependency for {simulator} simulator: {e}")
        return {"error": f"Missing dependency: {e}"}
    except Exception as e:
        logger.error(f"Error running circuit: {e}")
        return {"error": f"Error running circuit: {e}"}

def run_trials(circuit_file, num_trials=5, simulator="qiskit", shots=1024, output_file=None):
    """
    Run multiple trials with different parameter values.
    
    Args:
        circuit_file (str): Path to circuit file
        num_trials (int): Number of trials to run
        simulator (str): Simulator to use
        shots (int): Number of shots per trial
        output_file (str): Output file for results
    
    Returns:
        bool: True if successful
    """
    logger.info(f"Running {num_trials} trials for {circuit_file} with {simulator} simulator")
    
    # Parse circuit file
    circuit_content, parameters = parse_qasm_file(circuit_file)
    if circuit_content is None:
        return False
    
    # If no parameters, just run once
    if not parameters:
        logger.info("No parameters found in circuit. Running a single trial.")
        num_trials = 1
    
    # Generate parameter values for trials
    trial_params = generate_random_parameters(parameters, num_trials)
    
    # Run trials
    results = []
    for i, params in enumerate(trial_params):
        logger.info(f"Running trial {i+1}/{num_trials} with parameters: {params}")
        
        # Apply parameters to circuit
        if params:
            updated_circuit = apply_parameters_to_circuit(circuit_content, params)
        else:
            updated_circuit = circuit_content
        
        # Run circuit
        start_time = time.time()
        trial_result = run_circuit_trial(updated_circuit, simulator, shots)
        end_time = time.time()
        
        # Add metadata
        trial_result.update({
            "trial_id": i+1,
            "parameters": params,
            "execution_time": round(end_time - start_time, 3),
            "simulator": simulator
        })
        
        results.append(trial_result)
        
        # Log results
        if "error" in trial_result:
            logger.error(f"Trial {i+1} failed: {trial_result['error']}")
        else:
            logger.info(f"Trial {i+1} completed in {trial_result['execution_time']}s")
            logger.info(f"Entropy: {trial_result['entropy']}, Unique outcomes: {trial_result['unique_outcomes']}")
    
    # Find best trial based on entropy (higher is better)
    if results and all("entropy" in r for r in results):
        best_trial = max(results, key=lambda x: x.get("entropy", 0))
        logger.info(f"Best trial: {best_trial['trial_id']} with entropy {best_trial['entropy']}")
        
        # Mark best trial
        for r in results:
            r["is_best"] = (r["trial_id"] == best_trial["trial_id"])
    
    # Write results
    if output_file:
        try:
            with open(output_file, 'w') as f:
                json.dump({
                    "circuit_file": circuit_file,
                    "num_trials": num_trials,
                    "simulator": simulator,
                    "shots": shots,
                    "parameters": parameters,
                    "results": results
                }, f, indent=2)
            logger.info(f"Results written to {output_file}")
        except Exception as e:
            logger.error(f"Error writing results: {e}")
            return False
    else:
        # Print results
        print(json.dumps({
            "circuit_file": circuit_file,
            "num_trials": num_trials,
            "simulator": simulator,
            "shots": shots,
            "parameters": parameters,
            "results": results
        }, indent=2))
    
    return True

def trial(circuit_file, num_trials=5, simulator="qiskit", shots=1024, output_file=None):
    """
    Run trial evaluations of a quantum circuit.
    
    Args:
        circuit_file (str): Path to circuit file
        num_trials (int): Number of trials to run
        simulator (str): Simulator to use (qiskit, cirq, braket)
        shots (int): Number of shots per trial
        output_file (str): Output file for results
    
    Returns:
        bool: True if successful
    """
    # Set up logger
    setup_logger()
    
    logger.info(f"Running trial evaluations for {circuit_file}")
    
    # Check if file exists
    if not os.path.exists(circuit_file):
        logger.error(f"Circuit file does not exist: {circuit_file}")
        return False
    
    # Run trials
    return run_trials(circuit_file, num_trials, simulator, shots, output_file)

if __name__ == "__main__":
    # This allows the module to be run directly for testing
    if len(sys.argv) < 2:
        print("Usage: trial.py <circuit_file> [--trials <num_trials>] [--simulator <simulator>] [--shots <shots>] [--output <output_file>]")
        sys.exit(1)
    
    # Parse arguments
    circuit_file = sys.argv[1]
    num_trials = 5
    simulator = "qiskit"
    shots = 1024
    output_file = None
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--trials" and i+1 < len(sys.argv):
            num_trials = int(sys.argv[i+1])
            i += 2
        elif sys.argv[i] == "--simulator" and i+1 < len(sys.argv):
            simulator = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == "--shots" and i+1 < len(sys.argv):
            shots = int(sys.argv[i+1])
            i += 2
        elif sys.argv[i] == "--output" and i+1 < len(sys.argv):
            output_file = sys.argv[i+1]
            i += 2
        else:
            i += 1
    
    # Run trial
    success = trial(circuit_file, num_trials, simulator, shots, output_file)
    sys.exit(0 if success else 1) 