"""
Benchmark plugin for the Quantum CLI SDK.

This plugin adds a benchmark command that measures performance characteristics
of quantum circuits across different simulators.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from quantum_cli_sdk.plugin_system import CommandPlugin, register_command_plugin
from quantum_cli_sdk.cache import get_cache, CacheKey

# Set up logging
logger = logging.getLogger(__name__)

class BenchmarkCommand(CommandPlugin):
    """Plugin that adds a benchmark command to compare simulator performance."""
    
    @property
    def name(self) -> str:
        """Get the name of the command."""
        return "bench"
    
    @property
    def description(self) -> str:
        """Get the description of the command."""
        return "Benchmark quantum circuit performance across different simulators"
    
    def setup_parser(self, parser):
        """Set up the argument parser for this command.
        
        Args:
            parser: ArgumentParser instance for this command
        """
        parser.add_argument("--source", type=str, required=True,
                           help="Source circuit file to benchmark")
        parser.add_argument("--simulators", type=str, default="qiskit,cirq,braket",
                           help="Comma-separated list of simulators to benchmark")
        parser.add_argument("--shots", type=int, default=1024,
                           help="Number of shots for each simulator run")
        parser.add_argument("--iterations", type=int, default=3,
                           help="Number of iterations to run for each simulator")
        parser.add_argument("--dest", type=str, default="results/benchmark.json",
                           help="Destination file for benchmark results")
        parser.add_argument("--plot", action="store_true",
                           help="Generate performance comparison plot")
    
    def execute(self, args) -> int:
        """Execute the command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        try:
            # Ensure the destination directory exists
            dest_path = Path(args.dest)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load the circuit
            try:
                with open(args.source, 'r') as f:
                    circuit_code = f.read()
                print(f"Loaded circuit from {args.source}")
            except FileNotFoundError:
                print(f"Error: Source file '{args.source}' not found")
                return 1
            except Exception as e:
                print(f"Error loading circuit from {args.source}: {e}")
                return 1
            
            # Parse simulator list
            simulators = [s.strip() for s in args.simulators.split(",")]
            print(f"Benchmarking circuit on {len(simulators)} simulators: {', '.join(simulators)}")
            
            # Run benchmarks
            results = {}
            
            for simulator in simulators:
                simulator_results = []
                print(f"Benchmarking {simulator} simulator...")
                
                for i in range(args.iterations):
                    start_time = time.time()
                    
                    # Simulate running the circuit
                    # In a real implementation, this would call the actual simulator
                    time.sleep(0.5)  # Simulate work
                    
                    end_time = time.time()
                    execution_time = end_time - start_time
                    
                    simulator_results.append({
                        "iteration": i + 1,
                        "execution_time": execution_time,
                        "shots": args.shots,
                    })
                    
                    print(f"  Iteration {i+1}/{args.iterations}: {execution_time:.4f}s")
                
                # Calculate statistics
                times = [r["execution_time"] for r in simulator_results]
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                
                results[simulator] = {
                    "iterations": simulator_results,
                    "statistics": {
                        "average_time": avg_time,
                        "min_time": min_time,
                        "max_time": max_time,
                        "shots": args.shots,
                    }
                }
                
                print(f"  Average execution time: {avg_time:.4f}s")
            
            # Save results to file
            benchmark_results = {
                "source": args.source,
                "shots": args.shots,
                "iterations": args.iterations,
                "simulators": results,
            }
            
            with open(dest_path, 'w') as f:
                json.dump(benchmark_results, f, indent=2)
            
            print(f"Benchmark results saved to {args.dest}")
            
            # Generate plot if requested
            if args.plot:
                try:
                    import matplotlib.pyplot as plt
                    import numpy as np
                    
                    # Extract average times for each simulator
                    simulators_list = list(results.keys())
                    avg_times = [results[s]["statistics"]["average_time"] for s in simulators_list]
                    
                    # Create bar chart
                    plt.figure(figsize=(10, 6))
                    plt.bar(simulators_list, avg_times, color='skyblue')
                    plt.xlabel('Simulator')
                    plt.ylabel('Average Execution Time (s)')
                    plt.title('Quantum Simulator Performance Comparison')
                    plt.grid(axis='y', linestyle='--', alpha=0.7)
                    
                    # Add values on top of bars
                    for i, v in enumerate(avg_times):
                        plt.text(i, v + 0.01, f"{v:.4f}s", ha='center')
                    
                    # Save plot
                    plot_path = dest_path.with_suffix('.png')
                    plt.savefig(plot_path)
                    plt.close()
                    
                    print(f"Performance comparison plot saved to {plot_path}")
                except ImportError:
                    print("Matplotlib not available. Skipping plot generation.")
                except Exception as e:
                    print(f"Error generating plot: {e}")
            
            return 0
            
        except Exception as e:
            print(f"Error benchmarking circuit: {e}")
            return 1


# Register the plugin when this module is imported
def register():
    """Register the plugin with the CLI."""
    register_command_plugin(BenchmarkCommand())

# Call register function automatically
register() 