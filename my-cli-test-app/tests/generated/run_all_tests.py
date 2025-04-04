#!/usr/bin/env python3
"""
Run all tests for the Shor's algorithm QASM file.
This script executes the complete test suite and reports the results.
"""

import os
import sys
import pytest
import time

def main():
    """Run all tests and report results."""
    start_time = time.time()
    
    # Get the directory of this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Collect the test files
    test_files = [
        os.path.join(current_dir, 'test_shors_factoring.py'),
        os.path.join(current_dir, 'test_shors_advanced.py')
    ]
    
    # Print header
    print("\n" + "="*80)
    print("COMPREHENSIVE QUANTUM CIRCUIT TESTING FOR SHOR'S ALGORITHM")
    print("="*80)
    print(f"Testing file: {os.path.abspath(os.path.join(current_dir, '../../ir/openqasm/shors_factoring_15_compatible.qasm'))}")
    print("-"*80)
    
    # Run the tests with pytest
    args = [
        '-v',          # Verbose output
        '--no-header', # No pytest header
    ] + test_files
    
    exit_code = pytest.main(args)
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    # Print footer with summary
    print("\n" + "-"*80)
    print(f"Test run completed in {elapsed_time:.2f} seconds")
    print(f"Exit code: {exit_code}")
    
    if exit_code == 0:
        print("All tests PASSED! The Shor's algorithm circuit implementation is valid.")
    else:
        print("Some tests FAILED. Please review the test output for details.")
    
    print("="*80 + "\n")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 