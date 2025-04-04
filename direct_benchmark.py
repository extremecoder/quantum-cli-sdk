#!/usr/bin/env python3

import os
import sys
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('direct_benchmark')

# Import run_benchmark directly
from quantum_cli_sdk.commands.benchmark import run_benchmark

def main():
    """Run benchmark directly and save raw results."""
    if len(sys.argv) < 2:
        print("Usage: python direct_benchmark.py <qasm_file> [output_file] [shots]")
        sys.exit(1)
    
    qasm_file = sys.argv[1]
    
    # Define default output path if not provided
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # Create output directory if it doesn't exist
        output_dir = os.path.join("results", "benchmark")
        os.makedirs(output_dir, exist_ok=True)
        
        # Default output filename based on input filename
        base_name = os.path.basename(qasm_file).replace('.qasm', '')
        output_file = os.path.join(output_dir, f"{base_name}_benchmark_direct.json")
    
    # Set shots if provided
    shots = 1000
    if len(sys.argv) >= 4:
        shots = int(sys.argv[3])
    
    logger.info(f"Running direct benchmark on {qasm_file} with {shots} shots")
    logger.info(f"Output will be saved to {output_file}")
    
    # Run benchmark directly
    benchmark_result = run_benchmark(None, shots, qasm_file)
    
    if benchmark_result:
        # Save raw benchmark result to file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(benchmark_result, f, indent=2)
        
        logger.info(f"Direct benchmark completed successfully. Results saved to {output_file}")
        
        # Print circuit metrics
        if "circuit" in benchmark_result:
            circuit = benchmark_result["circuit"]
            logger.info(f"Circuit: {circuit.get('name', 'unknown')}")
            logger.info(f"  Qubits: {circuit.get('qubits', 0)}")
            logger.info(f"  Depth: {circuit.get('depth', 0)}")
            logger.info(f"  Gates: {circuit.get('gates', {}).get('total', 0)}")
        
        return 0
    else:
        logger.error("Benchmark failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 