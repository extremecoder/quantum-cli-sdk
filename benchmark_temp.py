#!/usr/bin/env python3

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('benchmark_cli')

# Import the benchmark function
from quantum_cli_sdk.commands.benchmark import benchmark

def main():
    """Run benchmark command manually."""
    if len(sys.argv) < 2:
        print("Usage: python benchmark_temp.py <qasm_file> [output_file]")
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
        output_file = os.path.join(output_dir, f"{base_name}_benchmark.json")
    
    logger.info(f"Running benchmark on {qasm_file}")
    logger.info(f"Output will be saved to {output_file}")
    
    success = benchmark(qasm_file, output_file)
    
    if success:
        logger.info(f"Benchmark completed successfully. Results saved to {output_file}")
        return 0
    else:
        logger.error("Benchmark failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 