"""
Commands for simulating quantum circuits.
"""

import json
import sys
import time
import logging
from pathlib import Path
from typing import Optional
import os
import inspect
import click

# Removed cache import as it's likely unused in the main dispatcher now
# from ..cache import get_cache, CacheKey

# Import backend functions from their new location
from .simulation_backends.qiskit_backend import run_qiskit_simulation
from .simulation_backends.cirq_backend import run_cirq_simulation
from .simulation_backends.braket_backend import run_braket_simulation

# Import SimulationResult from the new models module
from ..models import SimulationResult

# Set up logging
logger = logging.getLogger(__name__)

# Removed simulate_circuit function as it seemed like a duplicate/older version

# Removed run_qiskit_simulation, run_cirq_simulation, run_braket_simulation functions
# They are now imported from simulation_backends

def run_simulation(source_file: str, backend: Optional[str] = None, output: Optional[str] = None, shots: int = 1024, **kwargs):
    """
    Runs a simulation for the given QASM file on the specified backend.

    Args:
        source_file (str): Path to the OpenQASM file. If not provided, looks in <approot>/ir/openqasm/base.
        backend (Optional[str]): The simulation backend to use ('qiskit', 'cirq', 'braket'). Defaults to 'qiskit'.
        output (Optional[str]): Path to save the results JSON file. If None, uses <approot>/results/simulation/base.
        shots (int): Number of simulation shots.
        **kwargs: Additional backend-specific options.
    """
    # Set default backend to qiskit if none provided
    if not backend:
        backend = "qiskit"
        logger.info("No backend specified, using default backend: qiskit")

    logger.info(f"Received simulation request for {source_file} on backend {backend}")

    # Get the app root directory (current working directory)
    app_root = Path.cwd()

    # Handle default source file path
    if not source_file:
        source_dir = app_root / "ir" / "openqasm" / "base"
        if not source_dir.exists():
            raise FileNotFoundError(f"Default source directory not found: {source_dir}")
        # List available .qasm files
        qasm_files = list(source_dir.glob("*.qasm"))
        if not qasm_files:
            raise FileNotFoundError(f"No .qasm files found in {source_dir}")
        # Use the first .qasm file found
        source_file = str(qasm_files[0])
        logger.info(f"Using default source file: {source_file}")

    # Handle default output path
    if not output:
        # Create default output directory
        output_dir = app_root / "results" / "simulation" / "base"
        output_dir.mkdir(parents=True, exist_ok=True)
        # Use source filename for the output
        source_filename = Path(source_file).stem
        output = str(output_dir / f"{source_filename}_{backend}_results.json")
        logger.info(f"Using default output path: {output}")

    sim_result: Optional[SimulationResult] = None # Type hint clarifies return might be None
    start_time = time.time()

    try:
        # Ensure the source file exists *before* calling backend functions
        qasm_path = Path(source_file)
        if not qasm_path.is_file():
            raise FileNotFoundError(f"Input file not found: {source_file}")

        if backend == "qiskit":
            sim_result = run_qiskit_simulation(source_file, shots, **kwargs)
        elif backend == "cirq":
            sim_result = run_cirq_simulation(source_file, shots, **kwargs)
        elif backend == "braket":
            # Pass kwargs for potential future use
            sim_result = run_braket_simulation(source_file, shots, **kwargs)
        else:
            # This case should ideally be caught by argparse choices, but handle defensively
            logger.error(f"Unsupported simulation backend specified: {backend}")
            print(f"Error: Unsupported simulation backend: {backend}", file=sys.stderr)
            # Consider exiting or returning a specific error status/object
            sys.exit(1) # Keep exit for CLI context

        if sim_result:
            # Log counts/probabilities appropriately
            result_type = sim_result.metadata.get("result_type", "counts")
            logger.info(f"Simulation completed on {backend}. Result type: {result_type}. Results: {sim_result.counts}")
            
            results_dict = sim_result.to_dict()
            total_time = time.time() - start_time
            results_dict["metadata"]["total_cli_execution_time_sec"] = total_time
            # Add source file info for clarity
            results_dict["metadata"]["source_file"] = source_file

            if output:
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with open(output_path, 'w') as f:
                        json.dump(results_dict, f, indent=2)
                    logger.info(f"Simulation results saved to: {output}")
                    print(f"Simulation results saved to: {output}") # Also inform user on console
                except IOError as e:
                     logger.error(f"Failed to write results to {output}: {e}")
                     print(f"Error: Failed to write results to {output}. {e}", file=sys.stderr)
                     # Print to stdout as fallback
                     print("\nSimulation Results (failed to write to file):")
                     print(json.dumps(results_dict, indent=2))
                     sys.exit(1) # Exit with error if writing failed
            else:
                # Print results to stdout if no output file is specified
                print("\nSimulation Results:")
                print(json.dumps(results_dict, indent=2))
            return True
        return False
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        print(f"Error: Simulation failed: {e}", file=sys.stderr)
        return False

# Add alias for backward compatibility with CLI
def simulate_circuit(qasm_file: str, backend_name: str, output_file: Optional[str] = None, num_shots: int = 1024) -> bool:
    """
    Alias for run_simulation to maintain backward compatibility with CLI.
    
    Args:
        qasm_file (str): Path to the OpenQASM file.
        backend_name (str): The simulation backend to use.
        output_file (Optional[str]): Path to save the results JSON file.
        num_shots (int): Number of simulation shots.
        
    Returns:
        bool: True if simulation was successful, False otherwise.
    """
    return run_simulation(
        source_file=qasm_file,
        backend=backend_name,
        output=output_file,
        shots=num_shots
    )

# Removed placeholder standardize_counts function
# Removed Example usage for standalone testing 