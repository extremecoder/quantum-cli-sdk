"""
Benchmark quantum circuits and analyze performance metrics.
"""

import os
import sys
import logging
import json
import csv
import time
import glob
import re
from pathlib import Path
import datetime
import matplotlib.pyplot as plt
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from ..config import get_config
from ..quantum_circuit import QuantumCircuit
from ..output_formatter import format_output
from ..benchmark_runner import BenchmarkRunner

# Set up logger
logger = logging.getLogger(__name__)

def load_results(source_path):
    """
    Load results from a file or directory.
    
    Args:
        source_path (str): Path to results file or directory
        
    Returns:
        list: List of loaded result objects
    """
    try:
        results = []
        
        if os.path.isfile(source_path):
            # Load single file
            with open(source_path, 'r') as f:
                try:
                    data = json.load(f)
                    results.append(data)
                    logger.info(f"Loaded results from {source_path}")
                except json.JSONDecodeError:
                    logger.error(f"Could not parse JSON from {source_path}")
                    return []
                    
        elif os.path.isdir(source_path):
            # Load all JSON files in directory
            json_files = glob.glob(os.path.join(source_path, "**", "*.json"), recursive=True)
            
            if not json_files:
                logger.error(f"No JSON files found in {source_path}")
                return []
                
            for file_path in json_files:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                        # Add file path to data for reference
                        data["_file_path"] = file_path
                        
                        # Skip files that don't look like results
                        if not isinstance(data, dict) or not any(key in data for key in ["counts", "results", "success"]):
                            logger.debug(f"Skipping {file_path} - doesn't appear to be a results file")
                            continue
                            
                        results.append(data)
                        
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse JSON from {file_path}")
                except Exception as e:
                    logger.warning(f"Error loading {file_path}: {e}")
                    
            logger.info(f"Loaded {len(results)} result files from {source_path}")
        else:
            logger.error(f"Source path {source_path} does not exist")
            
        return results
        
    except Exception as e:
        logger.error(f"Error loading results: {e}")
        return []

def extract_metrics(results):
    """
    Extract key metrics from results.
    
    Args:
        results (list): List of result objects (can be from loaded files or run_benchmark)
        
    Returns:
        dict: Dictionary of extracted metrics
    """
    metrics = {
        "num_results": len(results),
        "simulators": set(),
        "platforms": set(),
        "total_shots": 0,
        "success_rate": 0,
        "error_rate": 0,
        "execution_times": [],
        "circuit_depths": [],
        "circuit_widths": [], # Keep width if needed, though run_benchmark doesn't provide it
        "gate_counts": {},
        "distribution_fidelities": [],
        "detailed_metrics": []
    }
    
    num_successful = 0
    
    for result in results:
        is_run_benchmark_format = "circuit" in result and "execution" in result and "metrics" in result

        # Track simulator or platform
        simulator = "unknown"
        if is_run_benchmark_format:
            simulator = result["execution"].get("backend", "qiskit_aer") # Default if run_benchmark was used
            metrics["simulators"].add(simulator)
        elif "simulator" in result:
            simulator = result["simulator"]
            metrics["simulators"].add(simulator)
        elif "platform" in result:
            simulator = result["platform"] # Use platform if simulator missing
            metrics["platforms"].add(simulator)
            
        # Track shots
        shots = 0
        if is_run_benchmark_format:
            shots = result["execution"].get("shots", 0)
        elif "shots" in result:
            shots = result["shots"]
        metrics["total_shots"] += shots
            
        # Track success
        success = False
        if is_run_benchmark_format:
            success = result["metrics"].get("success", False)
        elif "success" in result:
             success = result.get("success", False)
        if success:    
            num_successful += 1
            
        # Track execution time
        execution_time = 0
        if is_run_benchmark_format:
            execution_time = result["execution"].get("time_seconds", 0)
        elif "execution_time" in result:
             execution_time = result["execution_time"]
        metrics["execution_times"].append(execution_time)
            
        # Track circuit metrics
        circuit_depth = 0
        circuit_width = 0 # run_benchmark doesn't provide width currently
        gate_counts = {}
        if is_run_benchmark_format:
            cm = result["circuit"]
            circuit_depth = cm.get("depth", 0)
            circuit_width = cm.get("qubits", 0) # Use qubit count as width proxy
            gate_counts = cm.get("gates", {}).get("by_type", {}) # Get detailed counts
            # Add total if available
            if "total" in cm.get("gates", {}):
                 gate_counts['total'] = cm["gates"]["total"]
        elif "circuit_metrics" in result:
            cm = result["circuit_metrics"]
            circuit_depth = cm.get("depth", 0)
            circuit_width = cm.get("width", 0)
            gate_counts = cm.get("gate_counts", {})
        
        metrics["circuit_depths"].append(circuit_depth)
        metrics["circuit_widths"].append(circuit_width)
        for gate, count in gate_counts.items():
            metrics["gate_counts"][gate] = metrics["gate_counts"].get(gate, 0) + count
                    
        # Track fidelity if available (run_benchmark doesn't provide distribution fidelity)
        fidelity = 0
        if "fidelity" in result: # Check top level for loaded results
            fidelity = result["fidelity"]
            metrics["distribution_fidelities"].append(fidelity)
            
        # Add to detailed metrics
        detailed = {
            "source": result.get("_file_path", "direct_run"), # Indicate if it was run directly
            "simulator": simulator,
            "shots": shots,
            "success": success,
            "execution_time": execution_time,
            "circuit_depth": circuit_depth,
            "circuit_width": circuit_width,
            "fidelity": fidelity
        }
        metrics["detailed_metrics"].append(detailed)
    
    # Calculate success and error rates
    if results:
        metrics["success_rate"] = num_successful / len(results)
        metrics["error_rate"] = 1 - metrics["success_rate"]
    
    # Convert sets to lists for JSON serialization
    metrics["simulators"] = list(metrics["simulators"])
    metrics["platforms"] = list(metrics["platforms"])
    
    return metrics

def run_benchmark(source_path, shots=1000):
    """
    Run a benchmark directly on a circuit file.
    
    Args:
        source_path (str): Path to circuit file to benchmark
        shots (int): Number of shots
        
    Returns:
        dict: Benchmark results or None on error
    """
    try:
        # Import required modules
        try:
            import qiskit
            from qiskit import QuantumCircuit, transpile
            from qiskit.converters import circuit_to_dag
            from qiskit_aer import Aer
            from qiskit_aer import AerSimulator
            import time
        except ImportError as e:
            logger.error(f"Qiskit import error: {e}")
            return None
        
        circuit_file_path = Path(source_path) # Use Path object
        if not circuit_file_path.is_file():
             logger.error(f"Circuit file not found: {source_path}")
             return None

        # Load circuit from file using source_path
        with open(circuit_file_path, 'r') as f:
            qasm = f.read()
        
        # Create circuit from QASM
        try:
            circuit = QuantumCircuit.from_qasm_str(qasm)
        except Exception as e:
            logger.error(f"Error loading QASM circuit from {source_path}: {e}")
            return None
            
        # Get circuit metrics
        num_qubits = circuit.num_qubits
        depth = circuit.depth()
        num_gates = sum(circuit.count_ops().values())
        
        # Count by gate type
        gate_counts = circuit.count_ops()
        
        # Calculate single qubit and two qubit gates
        single_qubit_gates = sum(count for gate, count in gate_counts.items() 
                               if gate in ['h', 'x', 'y', 'z', 's', 't', 'rx', 'ry', 'rz'])
        two_qubit_gates = sum(count for gate, count in gate_counts.items() 
                             if gate in ['cx', 'cz', 'swap', 'cp'])
        
        # Measure execution time
        start_time = time.time()
        
        # Transpile for simulation
        transpiled_circuit = transpile(circuit, basis_gates=['u1', 'u2', 'u3', 'cx'])
        
        # Run simulation
        try:
            simulator = AerSimulator()
            job = simulator.run(transpiled_circuit, shots=shots)
            result = job.result()
            
            # Get counts
            counts = result.get_counts()
            execution_time = time.time() - start_time
            
            # Prepare benchmark results using source_path for name
            benchmark_result = {
                "circuit": {
                    "name": circuit_file_path.stem, # Use stem from Path object
                    "qubits": num_qubits,
                    "depth": depth,
                    "gates": {
                        "total": num_gates,
                        "single_qubit": single_qubit_gates,
                        "two_qubit": two_qubit_gates,
                        "by_type": gate_counts
                    }
                },
                "execution": {
                    "backend": "qiskit_aer",
                    "shots": shots,
                    "time_seconds": execution_time
                },
                "metrics": {
                    "success": True,
                    "transpiled_depth": transpiled_circuit.depth(),
                    "transpiled_gates": sum(transpiled_circuit.count_ops().values()),
                }
            }
            
            return benchmark_result
            
        except Exception as e:
            logger.error(f"Error during simulation for {source_path}: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Error in run_benchmark for {source_path}: {e}")
        return None

def create_visualizations(metrics, dest_dir):
    """
    Create benchmark visualization plots.
    
    Args:
        metrics (dict): Extracted metrics
        dest_dir (str): Destination directory
        
    Returns:
        list: Paths to created visualization files
    """
    try:
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        
        created_files = []
        
        # Create output directory
        os.makedirs(dest_dir, exist_ok=True)
        
        # 1. Execution Time Distribution
        if metrics["execution_times"]:
            plt.figure(figsize=(10, 6))
            plt.hist(metrics["execution_times"], bins=20)
            plt.xlabel("Execution Time (s)")
            plt.ylabel("Frequency")
            plt.title("Distribution of Execution Times")
            plt.grid(True, alpha=0.3)
            
            time_plot_path = os.path.join(dest_dir, "execution_time_distribution.png")
            plt.savefig(time_plot_path)
            plt.close()
            
            created_files.append(time_plot_path)
            
        # 2. Circuit Depth Distribution
        if metrics["circuit_depths"]:
            plt.figure(figsize=(10, 6))
            plt.hist(metrics["circuit_depths"], bins=20)
            plt.xlabel("Circuit Depth")
            plt.ylabel("Frequency")
            plt.title("Distribution of Circuit Depths")
            plt.grid(True, alpha=0.3)
            
            depth_plot_path = os.path.join(dest_dir, "circuit_depth_distribution.png")
            plt.savefig(depth_plot_path)
            plt.close()
            
            created_files.append(depth_plot_path)
            
        # 3. Gate Counts
        if metrics["gate_counts"]:
            plt.figure(figsize=(12, 8))
            gates = list(metrics["gate_counts"].keys())
            counts = list(metrics["gate_counts"].values())
            
            # Sort by count (descending)
            sorted_data = sorted(zip(gates, counts), key=lambda x: x[1], reverse=True)
            gates, counts = zip(*sorted_data)
            
            plt.bar(gates, counts)
            plt.xlabel("Gate Type")
            plt.ylabel("Count")
            plt.title("Gate Usage Distribution")
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            gates_plot_path = os.path.join(dest_dir, "gate_counts.png")
            plt.savefig(gates_plot_path)
            plt.close()
            
            created_files.append(gates_plot_path)
            
        # 4. Success vs Error rate
        plt.figure(figsize=(8, 8))
        plt.pie(
            [metrics["success_rate"], metrics["error_rate"]], 
            labels=["Success", "Error"],
            autopct="%1.1f%%",
            colors=["#4CAF50", "#F44336"]
        )
        plt.title("Success vs Error Rate")
        
        success_plot_path = os.path.join(dest_dir, "success_rate.png")
        plt.savefig(success_plot_path)
        plt.close()
        
        created_files.append(success_plot_path)
        
        # 5. Simulator/Platform Distribution
        all_platforms = metrics["simulators"] + metrics["platforms"]
        if all_platforms:
            platform_counts = {}
            for result in metrics["detailed_metrics"]:
                platform = result["simulator"]
                if platform not in platform_counts:
                    platform_counts[platform] = 0
                platform_counts[platform] += 1
                
            plt.figure(figsize=(10, 6))
            platforms = list(platform_counts.keys())
            counts = list(platform_counts.values())
            
            plt.bar(platforms, counts)
            plt.xlabel("Simulator/Platform")
            plt.ylabel("Count")
            plt.title("Distribution by Simulator/Platform")
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            platform_plot_path = os.path.join(dest_dir, "platform_distribution.png")
            plt.savefig(platform_plot_path)
            plt.close()
            
            created_files.append(platform_plot_path)
            
        logger.info(f"Created {len(created_files)} visualization plots in {dest_dir}")
        return created_files
        
    except Exception as e:
        logger.error(f"Error creating visualizations: {e}")
        return []

def write_benchmark_report(metrics, visualizations, dest_file):
    """
    Write a comprehensive benchmark report.
    
    Args:
        metrics (dict): Extracted metrics
        visualizations (list): Paths to visualization files
        dest_file (str): Destination file path
        
    Returns:
        bool: True if successful
    """
    try:
        # Create report data
        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "metrics": metrics,
            "visualizations": [os.path.basename(v) for v in visualizations]
        }
        
        # Calculate summary statistics
        summary = {
            "num_results": metrics["num_results"],
            "success_rate": metrics["success_rate"],
            "platforms_used": metrics["simulators"] + metrics["platforms"],
            "total_shots": metrics["total_shots"]
        }
        
        # Add average metrics where available
        if metrics["execution_times"]:
            summary["avg_execution_time"] = sum(metrics["execution_times"]) / len(metrics["execution_times"])
            
        if metrics["circuit_depths"]:
            summary["avg_circuit_depth"] = sum(metrics["circuit_depths"]) / len(metrics["circuit_depths"])
            
        if metrics["circuit_widths"]:
            summary["avg_circuit_width"] = sum(metrics["circuit_widths"]) / len(metrics["circuit_widths"])
            
        if metrics["distribution_fidelities"]:
            summary["avg_fidelity"] = sum(metrics["distribution_fidelities"]) / len(metrics["distribution_fidelities"])
            
        report["summary"] = summary
        
        # Write JSON report
        with open(dest_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        # Also write a CSV file with detailed metrics
        csv_path = os.path.splitext(dest_file)[0] + ".csv"
        with open(csv_path, 'w', newline='') as f:
            if metrics["detailed_metrics"]:
                fieldnames = metrics["detailed_metrics"][0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(metrics["detailed_metrics"])
                
        logger.info(f"Benchmark report written to {dest_file}")
        logger.info(f"Detailed metrics CSV written to {csv_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error writing benchmark report: {e}")
        return False

def benchmark(source_file, dest_file=None):
    """
    Benchmark quantum circuits and analyze performance.
    
    Args:
        source_file (str): Path to the source results or circuit file
        dest_file (str, optional): Path to write benchmark report
        
    Returns:
        bool: True if benchmarking was successful
    """
    logger.info(f"Starting benchmarking of {source_file}")
    
    # Ensure source file/directory exists
    if not os.path.exists(source_file):
        logger.error(f"Source file/directory {source_file} does not exist")
        return False
    
    # Determine if this is a circuit file or results file/directory
    is_circuit = False
    if os.path.isfile(source_file) and source_file.endswith((".qasm", ".json")):
        with open(source_file, 'r') as f:
            content = f.read(100)  # Read first 100 chars to check
            if content.strip().startswith("OPENQASM"):
                is_circuit = True
    
    # Determine destination path
    if not dest_file:
        dest_dir = os.path.join("reports", "benchmarking")
        os.makedirs(dest_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_file = os.path.join(dest_dir, f"benchmark_report_{timestamp}.json")
    
    # Create visualization directory
    viz_dir = os.path.join(os.path.dirname(dest_file), "visualizations")
    
    # Run benchmark or load results
    results = []
    if is_circuit:
        logger.info(f"Running benchmark on circuit file: {source_file}")
        benchmark_result = run_benchmark(source_path=source_file, shots=1000)
        
        if benchmark_result:
            results.append(benchmark_result)
        else:
            logger.error("Failed to run benchmark on circuit")
            return False
    else:
        # Load existing results
        results = load_results(source_file)
        
        if not results:
            logger.error("No results found to benchmark")
            return False
    
    # Extract metrics
    metrics = extract_metrics(results)
    
    # Create visualizations
    visualizations = create_visualizations(metrics, viz_dir)
    
    # Generate report
    success = write_benchmark_report(metrics, visualizations, dest_file)
    
    if success:
        logger.info(f"Benchmarking completed successfully, report at {dest_file}")
        
        # Log key metrics
        logger.info("Key Metrics:")
        logger.info(f"  - Number of results: {metrics['num_results']}")
        logger.info(f"  - Success rate: {metrics['success_rate']:.2%}")
        logger.info(f"  - Total shots: {metrics['total_shots']}")
        
        if metrics["execution_times"]:
            avg_time = sum(metrics["execution_times"]) / len(metrics["execution_times"])
            logger.info(f"  - Average execution time: {avg_time:.4f}s")
            
        if metrics["circuit_depths"]:
            avg_depth = sum(metrics["circuit_depths"]) / len(metrics["circuit_depths"])
            logger.info(f"  - Average circuit depth: {avg_depth:.1f}")
    
    return success

if __name__ == "__main__":
    # This allows the module to be run directly for testing
    if len(sys.argv) < 2:
        print("Usage: benchmark.py <source_file> [<dest_file>]")
        sys.exit(1)
    
    source = sys.argv[1]
    dest = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = benchmark(source, dest)
    sys.exit(0 if success else 1)
