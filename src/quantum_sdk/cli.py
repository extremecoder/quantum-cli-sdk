#!/usr/bin/env python3
"""
Command-line interface for Quantum SDK.
"""

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .quantum_circuit import QuantumCircuit
from .simulator import run_simulation
from .commands import circuit, run

def main():
    """Main entry point for the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Quantum CLI SDK - A command-line interface and SDK for quantum computing."
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Circuit creation command
    circuit_parser = subparsers.add_parser("circuit", help="Quantum circuit operations")
    circuit_subparsers = circuit_parser.add_subparsers(dest="subcommand", help="Circuit subcommands")
    
    # Create circuit subcommand
    create_parser = circuit_subparsers.add_parser("create", help="Create a quantum circuit")
    create_parser.add_argument("--qubits", type=int, default=2, help="Number of qubits in the circuit")
    create_parser.add_argument("--output", type=str, help="Output file to save the circuit")
    
    # Run simulation command
    run_parser = subparsers.add_parser("run", help="Run a quantum simulation")
    run_parser.add_argument("--circuit", type=str, help="Circuit file to run")
    run_parser.add_argument("--shots", type=int, default=1024, help="Number of shots for the simulation")
    run_parser.add_argument("--output", type=str, help="Output file to save the results")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle commands
    if args.command == "circuit" and args.subcommand == "create":
        circuit.create_circuit(args.qubits, args.output)
    elif args.command == "run":
        run.run_simulation_cmd(args.circuit, args.shots, args.output)
    else:
        parser.print_help()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
