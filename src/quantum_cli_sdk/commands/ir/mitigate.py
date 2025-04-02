"""
Argparse command handler for applying error mitigation to quantum circuits.
"""

import argparse
import logging
from pathlib import Path
import json
import sys
import random # For placeholder report

from quantum_cli_sdk.transpiler import (
    get_pass_manager,
    parse_qasm,
    circuit_to_qasm
)

# Set up logger
logger = logging.getLogger(__name__)

# Supported techniques (maps CLI option to pass manager key)
SUPPORTED_TECHNIQUES = ["zne", "pec", "cdr", "dd"]

def mitigate_circuit_command(args: argparse.Namespace):
    """
    Handles the 'ir mitigate' command logic.

    Args:
        args (argparse.Namespace): Parsed arguments. Expects:
            - input_file (str): Path to the input QASM file (often optimized).
            - output_file (str): Path to save the mitigated QASM file.
            - technique (str): Mitigation technique to apply.
            - params (str, optional): JSON string of technique-specific parameters.
            - report (bool): Whether to generate a mitigation report.
    """
    input_file = Path(args.input_file)
    output_file = Path(args.output_file)
    technique = args.technique.lower()
    generate_report = args.report
    
    if technique not in SUPPORTED_TECHNIQUES:
        print(f"Error: Unsupported mitigation technique '{args.technique}'. Supported: {SUPPORTED_TECHNIQUES}", file=sys.stderr)
        sys.exit(1)
        
    # Parse technique-specific parameters from JSON string
    mitigation_params = {}
    if args.params:
        try:
            mitigation_params = json.loads(args.params)
            if not isinstance(mitigation_params, dict):
                 raise ValueError("Parameters must be a JSON object (dictionary).")
            print(f"Using custom parameters: {mitigation_params}", file=sys.stderr)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format for --params: {e}", file=sys.stderr)
            sys.exit(1)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    logger.info(f"Starting circuit mitigation for '{input_file}' using {technique}.")

    # 1. Parse the input QASM file
    print(f"Parsing input file: {input_file}...", file=sys.stderr)
    parsed_circuit = parse_qasm(input_file)
    if not parsed_circuit:
        logger.error("Failed to parse input QASM file.")
        print("Error: Could not parse the input QASM file.", file=sys.stderr)
        sys.exit(1)

    # 2. Get PassManager and create mitigation pipeline
    try:
        pass_manager = get_pass_manager()
        pipeline = pass_manager.create_mitigation_pipeline(technique, mitigation_params)
        if not pipeline:
            # Error already logged by create_mitigation_pipeline
            sys.exit(1)
        print(f"Created mitigation pipeline: {pipeline.name}", file=sys.stderr)
    except Exception as e:
        logger.error(f"Failed to create mitigation pipeline: {e}", exc_info=True)
        print(f"Error: Could not create mitigation pipeline: {e}", file=sys.stderr)
        sys.exit(1)
        
    # 3. Run the pipeline
    try:
        # Pass mitigation_params within the options dictionary
        run_options = {'mitigation_params': mitigation_params}
        mitigated_circuit = pipeline.run(parsed_circuit, options=run_options)
        print("Mitigation pipeline finished.", file=sys.stderr)
    except Exception as e:
        logger.error(f"Error running mitigation pipeline: {e}", exc_info=True)
        print(f"Error: Mitigation pipeline failed during execution: {e}", file=sys.stderr)
        sys.exit(1)

    if not mitigated_circuit:
        logger.error("Mitigation pipeline returned an empty result.")
        print("Error: Mitigation failed, pipeline returned no result.", file=sys.stderr)
        sys.exit(1)

    # 4. Convert mitigated circuit back to QASM
    try:
        # Placeholder passes currently add metadata, not QASM comments
        # We might want to adjust passes to add comments OR adjust the writer
        # For now, write the circuit which might just look like the input + metadata
        mitigated_qasm = circuit_to_qasm(mitigated_circuit)
    except Exception as e:
        logger.error(f"Failed to convert mitigated circuit back to QASM: {e}", exc_info=True)
        print("Error: Could not convert mitigated circuit to QASM format.", file=sys.stderr)
        sys.exit(1)

    # 5. Output the result
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(mitigated_qasm)
        print(f"Mitigated circuit saved to: {output_file}", file=sys.stderr)
    except IOError as e:
        logger.error(f"Failed to write output file '{output_file}': {e}")
        print(f"Error: Could not write output file: {e}", file=sys.stderr)
        sys.exit(1)

    # 6. Generate report if requested (using placeholders)
    if generate_report:
        report_path = output_file.parent / f"{output_file.stem}_report.json"
        try:
            report = {
                "original_circuit": str(input_file),
                "mitigated_circuit": str(output_file),
                "technique": technique,
                "parameters": mitigation_params,
                "notes": "Mitigation implemented via placeholder pass.",
                "expected_improvement_placeholder": {
                    "error_reduction_estimate": f"{random.uniform(5, 50):.1f}%",
                    "fidelity_increase_estimate": f"{random.uniform(2, 20):.1f}%"
                }
            }
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Mitigation report saved to {report_path}", file=sys.stderr)
        except IOError as e:
            logger.error(f"Failed to write mitigation report '{report_path}': {e}")
            print(f"Error: Could not write mitigation report: {e}", file=sys.stderr)
            # Don't exit, saving report is secondary

    logger.info(f"Mitigation using {technique} complete.") 