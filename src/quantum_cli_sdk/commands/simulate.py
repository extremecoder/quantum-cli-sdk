"""
Commands for simulating quantum circuits.
"""

import json
import sys
import time
import logging
from pathlib import Path
from typing import Optional

from ..cache import get_cache, CacheKey

# Set up logging
logger = logging.getLogger(__name__)

def simulate_circuit(simulator="qiskit", source="openqasm", shots=1024, dest="results/simulation", use_cache=False):
    """Simulate a quantum circuit using the specified simulator.
    
    Args:
        simulator: Simulator backend (qiskit, cirq, braket, or all)
        source: Source file path
        shots: Number of simulation shots
        dest: Destination file for simulation results
        use_cache: Whether to use cache for simulation results
    
    Returns:
        Simulation results or None if an error occurred
    """
    try:
        # Ensure the output directory exists
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        start_time = time.time()
        
        # Load the circuit code
        try:
            with open(source, 'r') as f:
                circuit_code = f.read()
            logger.info(f"Loaded circuit with {circuit_code.count(';')} operations from {source}")
        except FileNotFoundError:
            print(f"Error: Source file '{source}' not found", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Error loading circuit from {source}: {e}", file=sys.stderr)
            return None
        
        # Check if cache should be used
        if use_cache:
            cache = get_cache()
            # Create a cache key for this simulation
            cache_key = CacheKey(
                circuit_code=circuit_code,
                simulator=simulator,
                shots=shots,
                parameters={"source_file": source}  # Include source filename in key for debugging
            )
            
            # Check if we have cached results
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"Using cached simulation results for {simulator} simulation with {shots} shots")
                results = cached_result
                
                # Add cache info to the results
                results["cached"] = True
                results["cache_info"] = {
                    "hit_time": time.time() - start_time,
                    "original_execution_time": results.get("execution_time", 0),
                    "cached_at": time.strftime('%Y-%m-%d %H:%M:%S', 
                                             time.localtime(results.get("timestamp", time.time())))
                }
                
                # Save results to file
                with open(dest_path, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"Retrieved simulation results from cache in {results['cache_info']['hit_time']:.4f}s")
                print(f"Results saved to {dest}")
                
                return results
            else:
                logger.info(f"No cached results found for {simulator} simulation")
        
        # No cached results or cache disabled, perform actual simulation
        print(f"Simulating circuit using {simulator} simulator with {shots} shots...")
        
        # In a real implementation, we would determine which simulator to use and run the simulation
        # For now, we'll just create simulation-specific code based on the simulator parameter
        execution_time = 0
        results = None
        
        if simulator == "all":
            # Run all simulators and combine results
            simulators = ["qiskit", "cirq", "braket"]
            combined_results = {}
            
            for sim in simulators:
                sim_start = time.time()
                # Simulate for each backend
                time.sleep(0.5)  # Simulate work
                sim_end = time.time()
                
                combined_results[sim] = {
                    "counts": {"00": int(shots * 0.48), "11": int(shots * 0.48), 
                              "01": int(shots * 0.02), "10": int(shots * 0.02)},
                    "execution_time": sim_end - sim_start
                }
            
            results = {
                "simulator": "all",
                "shots": shots,
                "source": source,
                "results": combined_results,
                "execution_time": time.time() - start_time,
                "timestamp": time.time(),
                "cached": False
            }
        else:
            # Run single simulator
            sim_start = time.time()
            
            # Simulate work based on simulator type for demo purposes
            if simulator == "qiskit":
                time.sleep(0.5)  # Qiskit is medium speed in our simulation
            elif simulator == "cirq":
                time.sleep(0.7)  # Cirq is slower in our simulation
            elif simulator == "braket":
                time.sleep(0.3)  # Braket is faster in our simulation
            
            sim_end = time.time()
            execution_time = sim_end - sim_start
            
            # Create a dummy result for now
            results = {
                "simulator": simulator,
                "shots": shots,
                "source": source,
                "results": {"00": 512, "11": 512},  # Dummy Bell state results
                "execution_time": execution_time,
                "total_time": time.time() - start_time,
                "timestamp": time.time(),
                "cached": False
            }
        
        # Cache the results if caching is enabled
        if use_cache:
            logger.info(f"Caching simulation results for {simulator} simulation with {shots} shots")
            cache = get_cache()
            cache.put(cache_key, results)
        
        # Save results to file
        with open(dest_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Simulation completed in {execution_time:.4f}s")
        print(f"Results saved to {dest}")
        
        return results
    except Exception as e:
        print(f"Error simulating circuit: {e}", file=sys.stderr)
        return None 

# Define a simple result structure for now
class SimulationResult:
    def __init__(self, counts: dict, platform: str, shots: int, metadata: dict = None):
        self.counts = counts
        self.platform = platform
        self.shots = shots
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "shots": self.shots,
            "counts": self.counts,
            "metadata": self.metadata
        }

def run_qiskit_simulation(qasm_file: str, shots: int = 1024, **kwargs) -> SimulationResult:
    """
    Runs an OpenQASM 2.0 circuit file using the Qiskit Aer simulator.

    Args:
        qasm_file (str): Path to the OpenQASM 2.0 file.
        shots (int): Number of simulation shots.
        **kwargs: Additional options (e.g., noise model parameters - TBD).

    Returns:
        SimulationResult: An object containing the simulation results.

    Raises:
        FileNotFoundError: If the QASM file does not exist.
        ImportError: If qiskit or qiskit_aer is not installed.
        Exception: For errors during circuit loading or simulation.
    """
    logger.info(f"Attempting Qiskit simulation for: {qasm_file} with {shots} shots.")

    try:
        from qiskit import QuantumCircuit
        from qiskit_aer import AerSimulator
    except ImportError:
        logger.error("Qiskit or Qiskit Aer is not installed. Please install them to run simulations.")
        print("Error: Qiskit/Qiskit Aer not found. Run 'pip install qiskit qiskit-aer'", file=sys.stderr)
        raise # Re-raise the ImportError

    qasm_path = Path(qasm_file)
    if not qasm_path.is_file():
        logger.error(f"QASM file not found: {qasm_file}")
        raise FileNotFoundError(f"QASM file not found: {qasm_file}")

    try:
        # Load circuit from QASM file
        circuit = QuantumCircuit.from_qasm_file(str(qasm_path))
        logger.debug(f"Successfully loaded QASM file: {qasm_file}")
        logger.debug(f"Circuit details: {circuit.num_qubits} qubits, {circuit.num_clbits} classical bits, depth {circuit.depth()}")

        # Set up the simulator
        # TODO: Add noise model support based on kwargs
        simulator = AerSimulator()
        logger.debug("AerSimulator initialized.")

        # Run the simulation
        logger.info(f"Running simulation job...")
        job = simulator.run(circuit, shots=shots)
        result = job.result()
        counts = result.get_counts(circuit)
        logger.info(f"Simulation job completed successfully. Status: {result.status}")
        logger.debug(f"Raw counts: {counts}")

        # Format results
        # Qiskit counts are { '00': N, '11': M }, convert to standardized format if needed
        # For now, we'll keep Qiskit's format.

        sim_result = SimulationResult(
            counts=counts,
            platform="qiskit",
            shots=shots,
            metadata={"status": result.status}
        )
        logger.info("Simulation result object created.")
        return sim_result

    except FileNotFoundError as e: # Should be caught earlier, but handle again just in case
        logger.error(f"File not found error during simulation: {e}")
        raise
    except Exception as e:
        logger.error(f"An error occurred during Qiskit simulation: {e}", exc_info=True)
        print(f"Error during simulation: {e}", file=sys.stderr)
        raise # Re-raise the exception after logging


def run_simulation(source_file: str, backend: str, output: Optional[str] = None, shots: int = 1024, **kwargs):
    """
    Main function to dispatch simulation to the correct backend runner.

    Args:
        source_file (str): Path to the QASM circuit file.
        backend (str): The simulation backend ('qiskit', 'cirq', 'braket').
        output (Optional[str]): Path to save the results JSON file.
        shots (int): Number of simulation shots.
        **kwargs: Additional backend-specific options.

    Returns:
        Optional[dict]: The simulation results as a dictionary, or None if failed.
    """
    logger.info(f"Received simulation request for {source_file} on backend {backend}")

    result_obj = None
    try:
        if backend.lower() == 'qiskit':
            result_obj = run_qiskit_simulation(source_file, shots, **kwargs)
        # elif backend.lower() == 'cirq':
        #     # TODO: Implement Cirq runner call
        #     logger.warning("Cirq simulation not yet implemented.")
        #     pass
        # elif backend.lower() == 'braket':
        #     # TODO: Implement Braket runner call
        #     logger.warning("Braket simulation not yet implemented.")
        #     pass
        else:
            logger.error(f"Unsupported simulation backend: {backend}")
            print(f"Error: Backend '{backend}' is not supported for simulation.", file=sys.stderr)
            return None

        if result_obj:
            results_dict = result_obj.to_dict()
            logger.info(f"Simulation completed on {result_obj.platform}. Counts: {results_dict.get('counts')}")

            # Save results to file if output path is provided
            if output:
                output_path = Path(output)
                try:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'w') as f:
                        json.dump(results_dict, f, indent=2)
                    logger.info(f"Simulation results saved to: {output_path}")
                except Exception as e:
                    logger.error(f"Failed to save simulation results to {output_path}: {e}", exc_info=True)
                    print(f"Warning: Could not save results to {output}: {e}", file=sys.stderr)
            
            return results_dict # Return the results dictionary

    except FileNotFoundError:
        # Already logged in the specific runner
        print(f"Error: Input file not found: {source_file}", file=sys.stderr)
    except ImportError:
        # Already logged in the specific runner
         print(f"Error: Missing required library for backend '{backend}'. Please install.", file=sys.stderr)
    except Exception as e:
        # Logged in the specific runner or here if dispatch fails
        logger.error(f"Simulation failed for {source_file} on {backend}: {e}", exc_info=True)
        print(f"Error running simulation: {e}", file=sys.stderr)

    return None # Indicate failure


# Example usage for standalone testing
if __name__ == '__main__':
    # Simple test case requires a dummy QASM file
    test_qasm_content = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c[2];
    h q[0];
    cx q[0], q[1];
    measure q -> c;
    """
    test_qasm_file = "temp_bell.qasm"
    Path(test_qasm_file).write_text(test_qasm_content)

    print(f"Running test simulation for {test_qasm_file} on Qiskit...")
    logging.basicConfig(level=logging.INFO) # Setup basic logging for test
    
    test_output_file = "temp_bell_results.json"
    
    results = run_simulation(test_qasm_file, backend='qiskit', output=test_output_file, shots=100)

    if results:
        print(f"Test simulation successful. Results saved to {test_output_file}")
        print("Results:")
        print(json.dumps(results, indent=2))
    else:
        print("Test simulation failed.")

    # Clean up test file
    try:
        os.remove(test_qasm_file)
        if os.path.exists(test_output_file):
           os.remove(test_output_file)
    except OSError:
        pass 