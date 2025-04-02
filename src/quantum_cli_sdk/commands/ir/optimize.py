"""
Argparse command handler for optimizing quantum circuits (Intermediate Representation).
"""

import argparse
import logging
from pathlib import Path
import json
import sys

from quantum_cli_sdk.transpiler import (
    get_pass_manager,
    parse_qasm,
    circuit_to_qasm,
    estimate_circuit_depth,
    OPTIMIZATION_LEVELS
)
# from quantum_cli_sdk.output_formatter import format_output # Keep for potential future use

# Set up logger
logger = logging.getLogger(__name__)

def optimize_circuit_command(args: argparse.Namespace):
    """
    Handles the 'ir optimize' command logic using argparse namespace.

    Reads an OpenQASM file, applies specified optimization passes based on the
    chosen level, and outputs the optimized circuit either to a file or stdout.
    Also prints statistics about the optimization process.

    Args:
        args (argparse.Namespace): Parsed arguments from argparse.
                                   Expected attributes: input_file, output_file, level, 
                                                      target_depth, format
    """
    input_file = Path(args.input_file)
    output_file = Path(args.output_file) if args.output_file else None
    level = args.level
    target_depth = args.target_depth
    output_format = args.format

    logger.info(f"Starting circuit optimization for '{input_file}' with level {level}.")

    # 1. Parse the input QASM file
    print(f"Parsing input file: {input_file}...", file=sys.stderr) # Use stderr for status messages
    parsed_circuit = parse_qasm(input_file)
    if not parsed_circuit:
        logger.error("Failed to parse input QASM file.")
        print("Error: Could not parse the input QASM file. Check logs for details.", file=sys.stderr)
        sys.exit(1)

    original_ops = len(parsed_circuit.get('operations', []))
    original_depth = estimate_circuit_depth(parsed_circuit)
    logger.info(f"Parsed circuit with {original_ops} operations, estimated depth {original_depth}.")

    # 2. Get PassManager and create optimization pipeline
    try:
        pass_manager = get_pass_manager()
        pipeline = pass_manager.create_pipeline(
            optimization_level=level,
            target_depth=target_depth
        )
        print(f"Created optimization pipeline: {pipeline.name}", file=sys.stderr)
        print(f"Running {len(pipeline.stages)} optimization stage(s)...", file=sys.stderr)
    except Exception as e:
        logger.error(f"Failed to create optimization pipeline: {e}", exc_info=True)
        print(f"Error: Could not create optimization pipeline: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Run the pipeline
    try:
        # Pass options needed for specific passes like DepthOptimization
        run_options = {'target_depth': target_depth}
        optimized_circuit = pipeline.run(parsed_circuit, options=run_options)
        print("Optimization pipeline finished.", file=sys.stderr)
    except Exception as e:
        logger.error(f"Error running optimization pipeline: {e}", exc_info=True)
        print(f"Error: Optimization pipeline failed during execution: {e}", file=sys.stderr)
        sys.exit(1)

    if not optimized_circuit:
        logger.error("Optimization pipeline returned an empty result.")
        print("Error: Optimization failed, pipeline returned no result.", file=sys.stderr)
        sys.exit(1)

    # 4. Convert optimized circuit back to QASM
    try:
        optimized_qasm = circuit_to_qasm(optimized_circuit)
    except Exception as e:
        logger.error(f"Failed to convert optimized circuit back to QASM: {e}", exc_info=True)
        print("Error: Could not convert optimized circuit to QASM format.", file=sys.stderr)
        sys.exit(1)

    # 5. Output the result
    if output_file:
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(optimized_qasm)
            print(f"Optimized circuit saved to: {output_file}", file=sys.stderr)
        except IOError as e:
            logger.error(f"Failed to write output file '{output_file}': {e}")
            print(f"Error: Could not write output file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Print QASM to stdout
        print(optimized_qasm)

    # 6. Print statistics (to stderr, as QASM goes to stdout if no output file)
    optimized_ops = len(optimized_circuit.get('operations', []))
    optimized_depth = estimate_circuit_depth(optimized_circuit)
    
    gate_reduction = original_ops - optimized_ops
    gate_reduction_pct = (gate_reduction / original_ops * 100) if original_ops > 0 else 0
    depth_reduction = original_depth - optimized_depth
    depth_reduction_pct = (depth_reduction / original_depth * 100) if original_depth > 0 else 0

    stats = {
        "optimization_level": level,
        "original_gate_count": original_ops,
        "optimized_gate_count": optimized_ops,
        "gate_reduction": gate_reduction,
        "gate_reduction_percentage": round(gate_reduction_pct, 2),
        "original_estimated_depth": original_depth,
        "optimized_estimated_depth": optimized_depth,
        "depth_reduction": depth_reduction,
        "depth_reduction_percentage": round(depth_reduction_pct, 2),
    }

    print("\n--- Optimization Statistics ---", file=sys.stderr)
    if output_format == 'json':
        print(json.dumps(stats, indent=2), file=sys.stderr)
    else: # format == 'text'
        print(f"Optimization Level: {level} ({OPTIMIZATION_LEVELS.get(level, 'Unknown')})", file=sys.stderr)
        print(f"Gate Count: {original_ops} -> {optimized_ops} (Reduced by {gate_reduction}, {stats['gate_reduction_percentage']}%)", file=sys.stderr)
        print(f"Estimated Depth: {original_depth} -> {optimized_depth} (Reduced by {depth_reduction}, {stats['depth_reduction_percentage']}%)", file=sys.stderr)

    logger.info(f"Optimization complete. Stats: {stats}")

# Example of how this would be called from cli.py handle_ir_commands:
# if args.ir_cmd == 'optimize':
#     from .commands.ir import optimize as ir_optimize_mod
#     ir_optimize_mod.optimize_circuit_command(args) 