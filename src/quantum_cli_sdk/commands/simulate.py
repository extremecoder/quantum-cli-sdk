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

def run_simulation(source_file: str, backend: str, output: Optional[str] = None, shots: int = 1024, **kwargs):
    """
    Runs a simulation for the given QASM file on the specified backend.

    Args:
        source_file (str): Path to the OpenQASM file.
        backend (str): The simulation backend to use ('qiskit', 'cirq', 'braket').
        output (Optional[str]): Path to save the results JSON file. If None, prints to stdout.
        shots (int): Number of simulation shots.
        **kwargs: Additional backend-specific options.
    """
    logger.info(f"Received simulation request for {source_file} on backend {backend}")

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

            print("Simulation command completed.")
            # Successful completion, exit code 0 (default)
        else:
            # Simulation function returned None, indicating an error handled within it.
            logger.warning(f"Simulation failed for backend {backend}. Check previous logs/errors.")
            # The backend function should have printed an error message and potentially raised.
            # If it returns None without raising, exit here.
            print(f"Simulation on backend '{backend}' failed. See logs for details.", file=sys.stderr)
            sys.exit(1) # Explicitly exit with code 1 if simulation failed internally

    except FileNotFoundError:
        # Error handled specifically for file not found
        logger.error(f"Input file not found: {source_file}")
        print(f"Error: Input file not found: {source_file}", file=sys.stderr)
        sys.exit(1) # Exit with error code for file not found
    except ImportError as e:
        # Error handled specifically for missing libraries
        # The specific backend function should have printed a helpful message and raised this.
        logger.error(f"ImportError caught in run_simulation for backend '{backend}'. {e}")
        print(f"Error: Missing required library for backend '{backend}'. Please install necessary packages.", file=sys.stderr)
        sys.exit(1) # Exit with error code for missing dependency
    except Exception as e:
        # Catch-all for other unexpected errors during simulation setup or execution
        logger.exception(f"An unexpected error occurred during simulation: {e}")
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1) # Exit with generic error code

# Removed placeholder standardize_counts function
# Removed Example usage for standalone testing 