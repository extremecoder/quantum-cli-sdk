#!/usr/bin/env python3
"""
Command-line interface for Quantum CLI SDK.
"""

import argparse
import json
import sys
import logging
import os
from pathlib import Path
import datetime

from . import __version__

# Import command modules or specific functions
from .commands import run
from .commands import generate_ir as ir_generate_mod
from .commands import validate as ir_validate_mod
from .commands import template
from .commands import init
from .commands import security_scan as security_scan_mod
from .commands import simulate as simulate_mod
from .commands.ir import optimize as ir_optimize_mod
from .commands.ir import mitigate as ir_mitigate_mod
from .commands import generate_tests as test_generate_mod
from .commands import estimate_resources as analyze_resources_mod
from .commands import calculate_cost
from .commands import benchmark as analyze_benchmark_mod
from .commands import finetune as ir_finetune_mod
# from .commands import hw_run
# from .commands import mitigate
# from .commands import optimize as ir_optimize_mod
# from .commands import mitigate as ir_mitigate_mod
# from .commands import finetune as ir_finetune_mod
# from .commands import resources as analyze_resources_mod
# from .commands import cost as analyze_cost_mod
# from .commands import benchmark as analyze_benchmark_mod
# from .commands import test_cmd as test_mod
# from .commands import service as service_mod
# from .commands import package as package_mod
# from .commands import hub as hub_mod

from .config import get_config, initialize_config
from .cache import get_cache, initialize_cache
from .transpiler import get_pass_manager, initialize_transpiler
from .plugin_system import discover_plugins, register_command_plugin, get_registered_command_plugins
from .plugin_system import setup_plugin_subparsers, execute_plugin_command
from .interactive import start_shell
from .visualizer import visualize_circuit_command, visualize_results_command
from .versioning import init_repo, commit_circuit, get_circuit_version, list_circuit_versions, checkout_version
from .marketplace import browse_marketplace, search_marketplace, get_algorithm_details, download_algorithm, publish_algorithm, submit_review, configure_marketplace
from .sharing import share_circuit, list_my_shared_circuits, list_shared_with_me, get_shared_circuit_details, update_share_permissions, remove_collaborator, unshare_circuit, get_activity_history, search_shared_circuits, SharingPermission
from .simulator import run_simulation
from . import circuit_comparison
from . import hardware_selector
from . import job_management
from . import config_manager
from . import dependency_analyzer
from . import progress
from . import output_formatter
from . import logging_config
from .utils import find_first_file

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_sdk():
    """Initialize the SDK components."""
    # Initialize configuration
    config = initialize_config()
    
    # Set log level based on active profile
    log_level = config.get_setting("log_level", "INFO")
    numeric_level = getattr(logging, log_level.upper(), None)
    if isinstance(numeric_level, int):
        logging.getLogger().setLevel(numeric_level)
        logger.info(f"Set log level to {log_level}")
    
    # Initialize cache with settings from config
    cache_dir = config.get_setting("cache_dir", ".quantum_cache")
    cache_enabled = config.get_setting("caching", True)
    max_age = config.get_setting("cache_max_age", None)  # In seconds, None means no expiration
    
    if cache_enabled:
        cache = initialize_cache(cache_dir, max_age)
        logger.info(f"Cache initialized in {cache_dir}" + 
                   (f" with {max_age}s expiration" if max_age else " with no expiration"))
    else:
        logger.info("Caching is disabled in the current profile")
    
    # Initialize transpiler with optimization level from config
    opt_level = config.get_setting("optimization_level", 1)
    transpiler = initialize_transpiler()
    logger.info(f"Transpiler initialized with optimization level {opt_level}")
    
    # Discover and load plugins from configured paths
    plugin_paths = config.get_plugin_paths()
    home_plugin_dir = os.path.expanduser("~/.quantum-cli/plugins")
    
    # Always check home directory for plugins if not explicitly included
    if home_plugin_dir not in plugin_paths and os.path.isdir(home_plugin_dir):
        plugin_paths.append(home_plugin_dir)
    
    # Add current directory for plugins if not explicitly included
    if os.getcwd() not in plugin_paths:
        plugin_paths.append(os.getcwd())
    
    if plugin_paths:
        try:
            num_plugins = discover_plugins(plugin_paths)
            if num_plugins > 0:
                logger.info(f"Discovered {num_plugins} plugins from: {', '.join(plugin_paths)}")
            else:
                logger.debug(f"No plugins found in: {', '.join(plugin_paths)}")
        except Exception as e:
            logger.error(f"Error discovering plugins: {e}")
    
    return config

def setup_init_commands(subparsers):
    """Setup project initialization commands."""
    # Project initialization commands
    init_parser = subparsers.add_parser("init", help="Initialize a new quantum project")
    init_subparsers = init_parser.add_subparsers(dest="init_cmd", help="Init command")
    
    # List available templates
    list_parser = init_subparsers.add_parser("list", help="List available project templates")
    
    # Create a new project
    create_parser = init_subparsers.add_parser("create", help="Create a new quantum project in the specified directory (default: current directory)")
    create_parser.add_argument("directory", nargs='?', default='.', help="Directory name for the new project (default: current directory)")
    create_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")

def setup_security_commands(subparsers):
    """Setup security scanning commands."""
    security_parser = subparsers.add_parser("security", help="Commands for security analysis")
    security_subparsers = security_parser.add_subparsers(dest="security_cmd", help="Security command", required=True)

    # security scan
    scan_parser = security_subparsers.add_parser("scan", help="Scan an IR file for potential security issues (default source: ir/openqasm/base/*.qasm)")
    scan_parser.add_argument("input_file", nargs='?', default=None, help="Path to the IR file to scan (e.g., OpenQASM). If omitted, uses the first .qasm file found in ./ir/openqasm/base/")
    scan_parser.add_argument("--output-file", "-o", default=None, help="Optional output file for scan results (JSON). Default: results/security/<input_stem>_scan_results.json")


def setup_ir_commands(subparsers):
    """Setup Intermediate Representation (IR) commands."""
    ir_parser = subparsers.add_parser("ir", help="Commands for managing Intermediate Representation (IR)")
    ir_subparsers = ir_parser.add_subparsers(dest="ir_cmd", help="IR command", required=True)

    # ir generate
    generate_parser = ir_subparsers.add_parser("generate", help="Generate IR (OpenQASM 2.0) from source code")
    generate_parser.add_argument("--source", required=False, help="Source Python file path containing circuit definition (default: source/circuits)")
    generate_parser.add_argument("--dest", required=False, help="Destination file path for the generated OpenQASM IR (default: ir/base)")
    # Add LLM arguments
    generate_parser.add_argument("--use-llm", action="store_true", help="Use LLM for IR generation")
    generate_parser.add_argument("--llm-provider", help="LLM provider to use for generation (default: 'togetherai')")
    generate_parser.add_argument("--llm-model", help="Specific LLM model name to use (default: 'mistralai/Mixtral-8x7B-Instruct-v0.1')")

    # ir validate
    validate_parser = ir_subparsers.add_parser("validate", help="Validate IR file syntax and semantics (default source: ir/base/*.qasm)")
    validate_parser.add_argument("input_file", nargs='?', default=None, help="Path to the IR file to validate (e.g., .qasm). If omitted, uses the first .qasm file found in ./ir/base/")
    validate_parser.add_argument("--output-file", "-o", required=False, default=None, help="Optional output file for validation results (JSON). Default: results/validation/<input_stem>.json")
    validate_parser.add_argument("--llm-url", help="Optional URL to LLM service for enhanced validation")

    # ir optimize
    optimize_parser = ir_subparsers.add_parser("optimize", help="Optimize the quantum circuit IR")
    optimize_parser.add_argument("--input-file", '-i', required=False, help="Path to the input OpenQASM file")
    optimize_parser.add_argument("--output-file", '-o', default=None, help="Path to save the optimized OpenQASM file. Prints to stdout if not specified.")
    optimize_parser.add_argument("--level", '-l', type=int, default=2, choices=[0, 1, 2, 3], help="Optimization level (0=None, 1=Light, 2=Medium, 3=Heavy)")
    optimize_parser.add_argument("--target-depth", '-d', type=int, default=None, help="Target circuit depth (relevant for optimization level 3)")
    optimize_parser.add_argument("--format", default='text', choices=['text', 'json'], help='Output format for statistics.')

    # ir mitigate
    mitigate_parser = ir_subparsers.add_parser("mitigate", help="Apply error mitigation techniques to the IR")
    mitigate_parser.add_argument("--input-file", '-i', required=True, help="Path to the input OpenQASM file (usually optimized)")
    mitigate_parser.add_argument("--output-file", '-o', required=True, help="Path to save the mitigated OpenQASM file")
    mitigate_parser.add_argument("--technique", '-t', required=True, choices=ir_mitigate_mod.SUPPORTED_TECHNIQUES, help="Error mitigation technique to apply.")
    mitigate_parser.add_argument("--params", '-p', default=None, help="JSON string containing technique-specific parameters (e.g., '{\"scale_factors\": [1, 2, 3]}')")
    mitigate_parser.add_argument("--report", action='store_true', help="Generate a JSON report about the mitigation process.")

    # ir finetune
    finetune_parser = ir_subparsers.add_parser("finetune", help="Fine-tune circuit based on analysis results and hardware constraints")
    finetune_parser.add_argument("--input-file", '-i', nargs='?', default=None, help="Path to the input IR file (usually mitigated). If omitted, searches in ir/openqasm/mitigated/ and uses the first .qasm file found.")
    finetune_parser.add_argument("--output-file", '-o', default=None, help="Path to save fine-tuning results (JSON). If omitted, defaults to results/finetune/<input_stem>_finetune_results.json")
    finetune_parser.add_argument("--hardware", choices=["ibm", "aws", "google"], default="ibm", help="Target hardware platform for fine-tuning")
    finetune_parser.add_argument("--search", choices=["grid", "random"], default="random", help="Search method for hyperparameter optimization")
    finetune_parser.add_argument("--shots", type=int, default=1000, help="Number of shots for simulation during fine-tuning")
    finetune_parser.add_argument("--use-hardware", action="store_true", help="Execute circuits on actual quantum hardware instead of simulators")
    finetune_parser.add_argument("--device-id", help="Specific hardware device ID to use (e.g., 'ibmq_manila' for IBM)")
    finetune_parser.add_argument("--api-token", help="API token for the quantum platform (if not using configured credentials)")
    finetune_parser.add_argument("--max-circuits", type=int, default=5, help="Maximum number of circuits to run on hardware (to control costs)")
    finetune_parser.add_argument("--poll-timeout", type=int, default=3600, help="Maximum time in seconds to wait for hardware results")

def setup_run_commands(subparsers):
    """Setup commands for running circuits (simulation, hardware)."""
    run_parser = subparsers.add_parser("run", help="Run quantum circuits on simulators or hardware")
    run_subparsers = run_parser.add_subparsers(dest="run_cmd", help="Run command", required=True)

    # run simulate
    simulate_parser = run_subparsers.add_parser("simulate", help="Run a circuit on a simulator")
    simulate_parser.add_argument("qasm_file", nargs='?', help="Path to the OpenQASM file to simulate (default: uses first .qasm file in ir/openqasm/base)")
    simulate_parser.add_argument("--backend", choices=['qiskit', 'cirq', 'braket'], default='qiskit', help="Simulation backend to use (default: qiskit)")
    simulate_parser.add_argument("--output", help="Optional output file for simulation results (JSON)")
    simulate_parser.add_argument("--shots", type=int, default=1024, help="Number of simulation shots")
    # Add other simulation options later (e.g., --noise-model)

    # run hw (placeholder)
    # hw_parser = run_subparsers.add_parser("hw", help="Run a quantum circuit on hardware (placeholder)")
    # hw_parser.add_argument("ir_file", help="Path to the input IR file")
    # hw_parser.add_argument("--platform", required=True, help="Target hardware platform (e.g., ibm, aws, google)")
    # hw_parser.add_argument("--device", required=True, help="Specific hardware device name")
    # hw_parser.add_argument("--shots", type=int, default=1024, help="Number of shots")
    # hw_parser.add_argument("--output", required=True, help="Path to save hardware execution results (JSON)")
    # Add credentials, job management flags later

def setup_test_commands(subparsers):
    """Setup commands for testing quantum circuits."""
    test_parser = subparsers.add_parser("test", help="Generate and run tests for quantum circuits")
    test_subparsers = test_parser.add_subparsers(dest="test_cmd", help="Test command", required=True)

    # test generate
    generate_parser = test_subparsers.add_parser("generate", help="Generate test code from an IR file using LLM")
    generate_parser.add_argument("--input-file", "-i", required=False, default=None, help="Path to the input mitigated IR file (e.g., .qasm). If omitted, searches in ir/openqasm/mitigated/ and uses the first file found.")
    generate_parser.add_argument("--output-dir", "-o", default="tests/generated", help="Directory to save the generated Python test files (default: tests/generated)")
    generate_parser.add_argument("--llm-provider", default="google", choices=["togetherai", "google"], help="LLM provider to use for test generation (default: togetherai)")
    generate_parser.add_argument("--llm-model", help="Specific LLM model name (e.g., 'mistralai/Mixtral-8x7B-Instruct-v0.1' for togetherai, 'gemini-1.5-pro-latest' for google)")

    # test run - implemented based on existing test function
    run_parser = test_subparsers.add_parser("run", help="Run generated test file(s)")
    run_parser.add_argument("test_file", nargs='?', default=None, help="Path to the test file or directory containing tests. If omitted, searches in tests/generated/ and runs the first .py file found.")
    run_parser.add_argument("--output", help="Path to save test results (JSON)")
    run_parser.add_argument("--simulator", choices=["qiskit", "cirq", "braket", "all"], default="qiskit", 
                           help="Simulator to use for running tests (applicable if test_file is a circuit file)")
    run_parser.add_argument("--shots", type=int, default=1024, 
                           help="Number of shots for simulation (applicable if test_file is a circuit file)")


def setup_analyze_commands(subparsers):
    """Setup commands for circuit analysis."""
    analyze_parser = subparsers.add_parser("analyze", help="Analyze quantum circuit properties")
    analyze_subparsers = analyze_parser.add_subparsers(dest="analyze_cmd", help="Analysis command", required=True)

    # analyze resources
    resources_parser = analyze_subparsers.add_parser("resources", help="Estimate resource requirements (qubits, gates)")
    resources_parser.add_argument("ir_file", nargs='?', default=None, help="Path to the input IR file (OpenQASM). If omitted, searches in ir/openqasm/mitigated/ and uses the first .qasm file found.")
    resources_parser.add_argument("--output", default=None, help="Path to save resource estimation results (JSON). If omitted, defaults to results/analysis/resources/<ir_stem>_resources.json")
    resources_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    # analyze cost 
    cost_parser = analyze_subparsers.add_parser("cost", help="Estimate execution cost on different platforms")
    cost_parser.add_argument("ir_file", nargs='?', default=None, help="Path to the input IR file (OpenQASM). If omitted, searches in ir/openqasm/mitigated/ and uses the first .qasm file found.")
    cost_parser.add_argument("--resource-file", help="Path to resource estimation file (optional input)")
    cost_parser.add_argument("--output", default=None, help="Path to save cost estimation results (JSON). If omitted, defaults to results/analysis/cost/<ir_stem>_cost.json")
    cost_parser.add_argument("--platform", choices=["all", "ibm", "aws", "google"], default="all", 
                           help="Target platform for cost estimation")
    cost_parser.add_argument("--shots", type=int, default=1000, help="Number of shots for execution")
    cost_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    # analyze benchmark
    benchmark_parser = analyze_subparsers.add_parser("benchmark", help="Benchmark circuit performance")
    benchmark_parser.add_argument("ir_file", nargs='?', default=None, help="Path to the input IR file (OpenQASM). If omitted, searches in ir/openqasm/mitigated/ and uses the first .qasm file found.")
    benchmark_parser.add_argument("--output", default=None, help="Path to save benchmark results (JSON). If omitted, defaults to results/analysis/benchmark/<ir_stem>_benchmark.json")
    benchmark_parser.set_defaults(func=lambda args: analyze_benchmark_mod.benchmark(args.ir_file, args.output))

def setup_visualization_commands(subparsers):
    """Setup visualization commands."""
    vis_parser = subparsers.add_parser("visualize", help="Visualize circuits or results")
    vis_subparsers = vis_parser.add_subparsers(dest="visualize_cmd", help="Visualization command", required=True)

    # visualize circuit
    vis_circuit_parser = vis_subparsers.add_parser("circuit", help="Visualize a quantum circuit")
    vis_circuit_parser.add_argument("--source", required=True, help="Path to the circuit file (QASM or other supported format)")
    vis_circuit_parser.add_argument("--output", help="Output file path (e.g., .png, .txt, .html)")
    vis_circuit_parser.add_argument("--format", choices=["text", "mpl", "latex", "html"], default="mpl", help="Output format")

    # visualize results
    vis_results_parser = vis_subparsers.add_parser("results", help="Visualize simulation or hardware results")
    vis_results_parser.add_argument("--source", required=True, help="Path to the results file (JSON)")
    vis_results_parser.add_argument("--output", help="Output file path (e.g., .png)")
    vis_results_parser.add_argument("--type", choices=["histogram", "statevector", "hinton", "qsphere"], default="histogram", help="Type of plot")
    vis_results_parser.add_argument("--interactive", action="store_true", help="Show interactive plot")

def setup_service_commands(subparsers):
    """Setup commands for microservice management."""
    service_parser = subparsers.add_parser("service", help="Generate and test microservice wrappers")
    service_subparsers = service_parser.add_subparsers(dest="service_cmd", help="Service command", required=True)

    # service generate
    generate_parser = service_subparsers.add_parser("generate", help="Generate microservice code from an IR file or zip package")
    generate_parser.add_argument("input_file", nargs='?', default=None, help="Path to the input IR file (QASM) or ZIP package. If omitted, searches in ir/openqasm/mitigated/")
    generate_parser.add_argument("--output-dir", help="Directory to save the generated microservice code (default: services/generated/<basename>)")
    generate_parser.add_argument("--llm-url", help="URL to LLM service for enhanced code generation")
    generate_parser.add_argument("--port", type=int, default=8889, help="Port number for the microservice (default: 8889)")
    generate_parser.add_argument("--app-root", help="Root directory of the application (default: current directory)")
    generate_parser.add_argument("--base-image", help="Custom Docker base image to use (default: quantum-cli-sdk/microservice-base:latest)")

    # service run (new command for running a microservice)
    run_parser = service_subparsers.add_parser("run", help="Run a generated microservice using Docker with format: <project_root>-quantum-app")
    run_parser.add_argument("service_dir", help="Path to the generated microservice directory (containing Dockerfile)")
    run_parser.add_argument("--port", type=int, default=8889, help="Port number for the microservice (default: 8889)")
    run_parser.add_argument("--detach", action="store_true", help="Run the service in detached mode (background)")
    run_parser.add_argument("--env", "-e", action="append", help="Environment variables to pass to the container (format: KEY=VALUE). Can be used multiple times.")

    # service test-generate (placeholder)
    test_generate_parser = service_subparsers.add_parser("test-generate", help="Generate tests for a microservice")
    test_generate_parser.add_argument("service_dir", help="Path to the generated microservice directory")
    test_generate_parser.add_argument("--output", help="Directory to save the generated service tests (e.g., service_dir/tests)")

    # service test-run (placeholder)
    test_run_parser = service_subparsers.add_parser("test-run", help="Run tests for a microservice (requires Docker)")
    test_run_parser.add_argument("service_dir", help="Path to the generated microservice directory")
    test_run_parser.add_argument("--test-dir", help="Path to the directory containing service tests")
    test_run_parser.add_argument("--output", help="Path to save service test results (JSON)")
    test_run_parser.add_argument("--blocking", action="store_true", help="Run in blocking mode (wait for completion)")

def setup_package_commands(subparsers):
    """Setup commands for application packaging."""
    package_parser = subparsers.add_parser("package", help="Package quantum applications")
    package_subparsers = package_parser.add_subparsers(dest="package_cmd", help="Package command", required=True)

    # package create
    create_parser = package_subparsers.add_parser("create", help="Create a distributable application package")
    create_parser.add_argument("--source-dir", required=True, help="Path to the source directory")
    create_parser.add_argument("--output-path", help="Path to save the output package (e.g., .zip file)")
    create_parser.add_argument("--format", choices=["zip", "tar", "wheel"], default="zip", help="Package format (default: zip)")
    create_parser.add_argument("--config", help="Path to package configuration file")
    create_parser.add_argument("--app-name", help="Application name (overrides config)")
    create_parser.add_argument("--version", help="Package version (overrides config)")
    create_parser.add_argument("--app-description", help="Application description (overrides config)")
    create_parser.add_argument("--author", help="Package author (overrides config)")
    create_parser.add_argument("--license", help="Package license (overrides config)")
    create_parser.add_argument("--requirements", help="Comma-separated list of requirements (overrides config)")
    create_parser.add_argument("--include", help="Comma-separated list of file patterns to include (overrides config)")
    create_parser.add_argument("--exclude", help="Comma-separated list of file patterns to exclude (overrides config)")

    # package info
    info_parser = package_subparsers.add_parser("info", help="Show information about a package")
    info_parser.add_argument("package_path", help="Path to the package file")
    info_parser.add_argument("--format", choices=["text", "json", "yaml"], default="text", help="Output format")

    # package extract
    extract_parser = package_subparsers.add_parser("extract", help="Extract a package to a directory")
    extract_parser.add_argument("package_path", help="Path to the package file")
    extract_parser.add_argument("--output-dir", help="Directory to extract to (default: current directory)")
    extract_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")

def setup_hub_commands(subparsers):
    """Setup commands for Quantum Hub interaction."""
    hub_parser = subparsers.add_parser("hub", help="Interact with the Quantum Hub")
    hub_subparsers = hub_parser.add_subparsers(dest="hub_cmd", help="Hub command")

    # hub publish (placeholder)
    # publish_parser = hub_subparsers.add_parser("publish", help="Publish a packaged application to the Hub")
    # publish_parser.add_argument("package_path", help="Path to the application package file (.zip)")
    # publish_parser.add_argument("--username", help="Quantum Hub username (or use env var/config)")
    # publish_parser.add_argument("--token", help="Quantum Hub API token (or use env var/config)")
    # Add other metadata flags if needed (e.g., --description, --tags)

def setup_job_commands(subparsers):
    """Setup job management commands."""
    # Job management commands
    jobs_parser = subparsers.add_parser("jobs", help="Manage quantum execution jobs")
    jobs_subparsers = jobs_parser.add_subparsers(dest="jobs_cmd", help="Jobs command")
    
    # List jobs
    list_parser = jobs_subparsers.add_parser("list", help="List jobs")
    list_parser.add_argument("--status", help="Filter by status (comma-separated)")
    list_parser.add_argument("--provider", help="Filter by provider")
    list_parser.add_argument("--backend", help="Filter by backend")
    list_parser.add_argument("--days", type=int, default=7, help="Show jobs from the last N days")
    list_parser.add_argument("--storage-path", help="Jobs storage path", default=config_manager.get_default_param("jobs", "storage_path"))
    
    # Get job details
    get_parser = jobs_subparsers.add_parser("get", help="Get job details")
    get_parser.add_argument("job_id", help="Job ID")
    get_parser.add_argument("--storage-path", help="Jobs storage path", default=config_manager.get_default_param("jobs", "storage_path"))
    
    # Get job results
    results_parser = jobs_subparsers.add_parser("results", help="Get job results")
    results_parser.add_argument("job_id", help="Job ID")
    results_parser.add_argument("--output-file", help="Output file path")
    results_parser.add_argument("--output-format", help="Output format", choices=["text", "json", "csv"], default="text")
    results_parser.add_argument("--storage-path", help="Jobs storage path", default=config_manager.get_default_param("jobs", "storage_path"))
    
    # Cancel job
    cancel_parser = jobs_subparsers.add_parser("cancel", help="Cancel a job")
    cancel_parser.add_argument("job_id", help="Job ID")
    cancel_parser.add_argument("--storage-path", help="Jobs storage path", default=config_manager.get_default_param("jobs", "storage_path"))
    
    # Monitor jobs
    monitor_parser = jobs_subparsers.add_parser("monitor", help="Monitor jobs")
    monitor_parser.add_argument("--job-id", help="Specific job ID to monitor")
    monitor_parser.add_argument("--status", help="Filter by status (comma-separated)")
    monitor_parser.add_argument("--interval", type=int, help="Update interval in seconds", 
                               default=config_manager.get_default_param("jobs", "monitor_interval"))
    monitor_parser.add_argument("--storage-path", help="Jobs storage path", default=config_manager.get_default_param("jobs", "storage_path"))


def setup_versioning_commands(subparsers):
    """Setup versioning-related commands."""
    # Versioning commands
    version_parser = subparsers.add_parser("version", help="Manage quantum circuit versions")
    version_subparsers = version_parser.add_subparsers(dest="version_cmd", help="Version command")
    
    # Initialize repository
    init_parser = version_subparsers.add_parser("init", help="Initialize a version control repository")
    init_parser.add_argument("--repo-path", help="Path to repository", default=config_manager.get_default_param("version", "repo_path"))
    
    # Commit circuit version
    commit_parser = version_subparsers.add_parser("commit", help="Commit a new circuit version")
    commit_parser.add_argument("--repo-path", help="Path to repository", default=config_manager.get_default_param("version", "repo_path"))
    commit_parser.add_argument("--author", help="Author name", default=config_manager.get_config_value("user.name"))
    commit_parser.add_argument("--circuit-name", required=True, help="Name of the circuit")
    commit_parser.add_argument("--circuit-file", required=True, help="Path to circuit file")
    commit_parser.add_argument("--message", required=True, help="Commit message")
    
    # Get specific version
    get_parser = version_subparsers.add_parser("get", help="Get a specific circuit version")
    get_parser.add_argument("--repo-path", help="Path to repository", default=config_manager.get_default_param("version", "repo_path"))
    get_parser.add_argument("--circuit-name", required=True, help="Name of the circuit")
    get_parser.add_argument("--version-id", required=True, help="Version ID")
    get_parser.add_argument("--output-file", help="Output file path")
    
    # List versions
    list_parser = version_subparsers.add_parser("list", help="List circuit versions")
    list_parser.add_argument("--repo-path", help="Path to repository", default=config_manager.get_default_param("version", "repo_path"))
    list_parser.add_argument("--circuit-name", help="Name of the circuit")
    
    # Checkout version
    checkout_parser = version_subparsers.add_parser("checkout", help="Checkout a specific circuit version")
    checkout_parser.add_argument("--repo-path", help="Path to repository", default=config_manager.get_default_param("version", "repo_path"))
    checkout_parser.add_argument("--circuit-name", required=True, help="Name of the circuit")
    checkout_parser.add_argument("--version-id", required=True, help="Version ID")
    checkout_parser.add_argument("--output-file", help="Output file path")

def setup_marketplace_commands(subparsers):
    """Setup marketplace-related commands."""
    # Marketplace commands
    marketplace_parser = subparsers.add_parser("marketplace", help="Quantum algorithm marketplace")
    marketplace_subparsers = marketplace_parser.add_subparsers(dest="marketplace_cmd", help="Marketplace command")
    
    # Browse algorithms
    browse_parser = marketplace_subparsers.add_parser("browse", help="Browse available algorithms")
    browse_parser.add_argument("--tag", help="Filter by tag")
    browse_parser.add_argument("--sort-by", help="Sort by field", default=config_manager.get_default_param("marketplace", "sort_by"))
    
    # Search algorithms
    search_parser = marketplace_subparsers.add_parser("search", help="Search for algorithms")
    search_parser.add_argument("query", help="Search query")
    
    # Get algorithm details
    get_parser = marketplace_subparsers.add_parser("get", help="Get algorithm details")
    get_parser.add_argument("algorithm_id", help="Algorithm ID")
    
    # Download algorithm
    download_parser = marketplace_subparsers.add_parser("download", help="Download an algorithm")
    download_parser.add_argument("algorithm_id", help="Algorithm ID")
    download_parser.add_argument("--output-path", help="Output path")
    
    # Publish algorithm
    publish_parser = marketplace_subparsers.add_parser("publish", help="Publish an algorithm")
    publish_parser.add_argument("--name", required=True, help="Algorithm name")
    publish_parser.add_argument("--description", required=True, help="Algorithm description")
    publish_parser.add_argument("--circuit-file", required=True, help="Path to circuit file")
    publish_parser.add_argument("--version", help="Version", default="1.0.0")
    publish_parser.add_argument("--tags", help="Tags (comma-separated)")
    publish_parser.add_argument("--requirements", help="Requirements (comma-separated)")
    publish_parser.add_argument("--example-usage", help="Example usage")
    
    # Submit review
    review_parser = marketplace_subparsers.add_parser("review", help="Submit a review")
    review_parser.add_argument("algorithm_id", help="Algorithm ID")
    review_parser.add_argument("--rating", required=True, type=int, choices=range(1, 6), help="Rating (1-5)")
    review_parser.add_argument("--comment", help="Review comment")
    
    # Configure marketplace
    configure_parser = marketplace_subparsers.add_parser("configure", help="Configure marketplace settings")
    configure_parser.add_argument("--api-key", help="API key")
    configure_parser.add_argument("--endpoint", help="API endpoint URL")

def setup_sharing_commands(subparsers):
    """Setup sharing-related commands."""
    # Sharing commands
    sharing_parser = subparsers.add_parser("share", help="Share quantum circuits")
    sharing_subparsers = sharing_parser.add_subparsers(dest="sharing_cmd", help="Sharing command")
    
    # Share circuit
    circuit_parser = sharing_subparsers.add_parser("circuit", help="Share a circuit")
    circuit_parser.add_argument("--repo-path", help="Path to repository", default=config_manager.get_default_param("version", "repo_path"))
    circuit_parser.add_argument("--circuit-name", required=True, help="Name of the circuit")
    circuit_parser.add_argument("--version-id", help="Version ID (latest if not specified)")
    circuit_parser.add_argument("--description", help="Description")
    circuit_parser.add_argument("--storage-path", help="Storage path", default=config_manager.get_default_param("share", "storage_path"))
    circuit_parser.add_argument("--recipients", required=True, help="Recipients (comma-separated emails)")
    circuit_parser.add_argument("--permission", help="Permission level", choices=["read_only", "read_write", "admin"], default=config_manager.get_default_param("share", "permission"))
    circuit_parser.add_argument("--tags", help="Tags (comma-separated)")
    
    # List shared circuits
    list_parser = sharing_subparsers.add_parser("list", help="List shared circuits")
    list_parser.add_argument("--shared-by-me", action="store_true", help="List circuits shared by me")
    list_parser.add_argument("--shared-with-me", action="store_true", help="List circuits shared with me")
    list_parser.add_argument("--storage-path", help="Storage path", default=config_manager.get_default_param("share", "storage_path"))
    
    # Get shared circuit
    get_parser = sharing_subparsers.add_parser("get", help="Get a shared circuit")
    get_parser.add_argument("--share-id", required=True, help="Share ID")
    get_parser.add_argument("--output-file", help="Output file path")
    get_parser.add_argument("--storage-path", help="Storage path", default=config_manager.get_default_param("share", "storage_path"))
    
    # Update permissions
    permissions_parser = sharing_subparsers.add_parser("permissions", help="Update permissions")
    permissions_parser.add_argument("--share-id", required=True, help="Share ID")
    permissions_parser.add_argument("--collaborator", required=True, help="Collaborator email")
    permissions_parser.add_argument("--permission", required=True, help="Permission level", choices=["read_only", "read_write", "admin"])
    permissions_parser.add_argument("--storage-path", help="Storage path", default=config_manager.get_default_param("share", "storage_path"))
    
    # Remove collaborator
    remove_collaborator_parser = sharing_subparsers.add_parser("remove-collaborator", help="Remove a collaborator")
    remove_collaborator_parser.add_argument("--share-id", required=True, help="Share ID")
    remove_collaborator_parser.add_argument("--collaborator", required=True, help="Collaborator email")
    remove_collaborator_parser.add_argument("--storage-path", help="Storage path", default=config_manager.get_default_param("share", "storage_path"))
    
    # Unshare circuit
    unshare_parser = sharing_subparsers.add_parser("unshare", help="Unshare a circuit")
    unshare_parser.add_argument("--share-id", required=True, help="Share ID")
    unshare_parser.add_argument("--storage-path", help="Storage path", default=config_manager.get_default_param("share", "storage_path"))
    
    # Get activity history
    activity_parser = sharing_subparsers.add_parser("activity", help="Get activity history")
    activity_parser.add_argument("--share-id", required=True, help="Share ID")
    activity_parser.add_argument("--storage-path", help="Storage path", default=config_manager.get_default_param("share", "storage_path"))
    
    # Search shared circuits
    search_parser = sharing_subparsers.add_parser("search", help="Search shared circuits")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--storage-path", help="Storage path", default=config_manager.get_default_param("share", "storage_path"))

def setup_compare_commands(subparsers):
    """Setup circuit comparison commands."""
    # Circuit comparison commands
    compare_parser = subparsers.add_parser("compare", help="Compare quantum circuits")
    compare_parser.add_argument("--circuit1", required=True, help="Path to first circuit file")
    compare_parser.add_argument("--circuit2", required=True, help="Path to second circuit file")
    compare_parser.add_argument("--output-format", help="Output format", choices=["text", "json", "markdown"], 
                               default=config_manager.get_default_param("compare", "output_format"))
    compare_parser.add_argument("--output-file", help="Output file path")
    compare_parser.add_argument("--detailed", action="store_true", help="Show detailed comparison")
    compare_parser.add_argument("--metrics", help="Specific metrics to compare (comma-separated)")
    compare_parser.add_argument("--visualize", action="store_true", help="Visualize the comparison")

def setup_hardware_commands(subparsers):
    """Setup hardware selection commands."""
    # Hardware selection commands
    hardware_parser = subparsers.add_parser("find-hardware", help="Find suitable quantum hardware")
    hardware_parser.add_argument("--circuit", required=True, help="Path to circuit file")
    hardware_parser.add_argument("--criteria", help="Selection criteria", choices=["overall", "performance", "cost", "availability"],
                                default=config_manager.get_default_param("find-hardware", "criteria"))
    hardware_parser.add_argument("--provider", help="Filter by provider (comma-separated)")
    hardware_parser.add_argument("--min-qubits", type=int, help="Minimum number of qubits")
    hardware_parser.add_argument("--max-cost", type=float, help="Maximum cost")
    hardware_parser.add_argument("--output-format", help="Output format", choices=["text", "json", "markdown"], default="text")
    hardware_parser.add_argument("--output-file", help="Output file path")
    hardware_parser.add_argument("--top", type=int, default=3, help="Number of recommendations to show")
    hardware_parser.add_argument("--update-catalog", action="store_true", help="Update hardware catalog before searching")


def setup_config_commands(subparsers):
    """Setup configuration commands."""
    # Configuration commands
    config_parser = subparsers.add_parser("config", help="Manage configuration and default parameters")
    config_subparsers = config_parser.add_subparsers(dest="config_cmd", help="Configuration command")
    
    # Get config value
    get_parser = config_subparsers.add_parser("get", help="Get configuration value")
    get_parser.add_argument("path", help="Configuration path (e.g., 'default_parameters.run.shots')")
    
    # Set config value
    set_parser = config_subparsers.add_parser("set", help="Set configuration value")
    set_parser.add_argument("path", help="Configuration path (e.g., 'default_parameters.run.shots')")
    set_parser.add_argument("value", help="Configuration value")
    
    # Print configuration
    print_parser = config_subparsers.add_parser("print", help="Print configuration")
    
    # Default parameters
    default_parser = config_subparsers.add_parser("defaults", help="Manage default parameters")
    default_parser.add_argument("--command", help="Show defaults for specific command")
    
    # Profile management
    profile_parser = config_subparsers.add_parser("profile", help="Manage configuration profiles")
    profile_subparsers = profile_parser.add_subparsers(dest="profile_cmd", help="Profile command")
    
    # List profiles
    list_profile_parser = profile_subparsers.add_parser("list", help="List available profiles")
    
    # Create profile
    create_profile_parser = profile_subparsers.add_parser("create", help="Create a new profile")
    create_profile_parser.add_argument("name", help="Profile name")
    create_profile_parser.add_argument("--description", help="Profile description")
    
    # Load profile
    load_profile_parser = profile_subparsers.add_parser("load", help="Load a profile")
    load_profile_parser.add_argument("name", help="Profile name")
    
    # Delete profile
    delete_profile_parser = profile_subparsers.add_parser("delete", help="Delete a profile")
    delete_profile_parser.add_argument("name", help="Profile name")
    
    # Export/import configuration
    export_parser = config_subparsers.add_parser("export", help="Export configuration")
    export_parser.add_argument("output_file", help="Output file path")
    
    import_parser = config_subparsers.add_parser("import", help="Import configuration")
    import_parser.add_argument("input_file", help="Input file path")
    import_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing configuration")

def setup_dependency_commands(subparsers):
    """Setup dependency analysis commands."""
    # Dependency analysis commands
    deps_parser = subparsers.add_parser("deps", help="Analyze dependencies")
    deps_subparsers = deps_parser.add_subparsers(dest="deps_cmd", help="Dependency command")
    
    # Check dependencies
    check_parser = deps_subparsers.add_parser("check", help="Check dependencies")
    check_parser.add_argument("--requirements", "-r", help="Path to requirements file")
    
    # Generate dependency report
    report_parser = deps_subparsers.add_parser("report", help="Generate dependency report")
    report_parser.add_argument("--output", "-o", required=True, help="Output file path")
    report_parser.add_argument("--format", "-f", choices=["text", "json", "markdown"], default="text", help="Report format")
    report_parser.add_argument("--requirements", "-r", help="Path to requirements file")
    
    # Get install command
    install_parser = deps_subparsers.add_parser("install-cmd", help="Get install command for missing packages")
    install_parser.add_argument("--requirements", "-r", help="Path to requirements file")
    
    # Verify specific package
    verify_parser = deps_subparsers.add_parser("verify", help="Verify a specific package")
    verify_parser.add_argument("package", help="Package name")
    verify_parser.add_argument("--version", "-v", help="Required version specification")



def setup_template_commands(subparsers):
    """Setup template management commands (Placeholder)."""
    template_parser = subparsers.add_parser("template", help="Manage circuit templates (Placeholder)")
    template_subparsers = template_parser.add_subparsers(dest="template_cmd", help="Template command")

    # Placeholder subcommands (can be uncommented/implemented later)
    # list_parser = template_subparsers.add_parser("list", help="List available templates")
    # get_parser = template_subparsers.add_parser("get", help="Get a template")
    # get_parser.add_argument("name", help="Template name")
    # get_parser.add_argument("--dest", "-d", help="Destination file")



def main():
    """Main entry point for the Quantum CLI SDK."""
    config = initialize_sdk()

    parser = argparse.ArgumentParser(description="Quantum CLI SDK")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    # Global argument for profile selection
    parser.add_argument("--profile", help="Specify configuration profile to use", default="default")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Setup command groups based on pipeline stages
    setup_ir_commands(subparsers)
    setup_run_commands(subparsers)      # Includes simulate
    setup_analyze_commands(subparsers)  # Placeholders commented
    setup_test_commands(subparsers)     # Uncommented
    setup_service_commands(subparsers)  # Placeholders commented
    setup_package_commands(subparsers)  # Placeholders commented
    setup_hub_commands(subparsers)      # Placeholders commented

    # Setup other command groups
    setup_init_commands(subparsers)
    setup_compare_commands(subparsers)
    setup_config_commands(subparsers)
    setup_dependency_commands(subparsers)
    setup_hardware_commands(subparsers) # Keeping for now, maybe integrate into run/analyze?
    setup_job_commands(subparsers)
    setup_marketplace_commands(subparsers)
    setup_sharing_commands(subparsers)
    setup_template_commands(subparsers)
    setup_versioning_commands(subparsers)
    setup_visualization_commands(subparsers)
    setup_security_commands(subparsers)

    # Setup interactive mode command
    interactive_parser = subparsers.add_parser("interactive", help="Start interactive shell")

    # Discover and setup plugin commands
    setup_plugin_subparsers(subparsers)

    # Parse arguments
    if len(sys.argv) <= 1:
        # If no command is provided, print help and exit
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    # Load the specified profile
    if args.profile != "default":
         try:
             config_manager.switch_profile(args.profile)
             logger.info(f"Switched to profile: {args.profile}")
             # Re-initialize components based on new profile settings if necessary
             config = initialize_sdk() 
         except ValueError as e:
             print(f"Error switching profile: {e}", file=sys.stderr)
             sys.exit(1)

    # --- Command Dispatch Logic --- 

    if args.command == "ir":
        handle_ir_commands(args)
    elif args.command == "run":
        handle_run_commands(args)
    elif args.command == "analyze":
        handle_analyze_commands(args)
    elif args.command == "test":
        handle_test_commands(args)
    elif args.command == "service":
        # Restore the call to the service command handler
        handle_service_commands(args)
    elif args.command == "package":
        handle_package_commands(args)
    elif args.command == "hub":
        # handle_hub_commands(args) # Commented out
        print(f"Command group '{args.command}' is not fully implemented yet.", file=sys.stderr)
        parser.print_help(sys.stderr)
        sys.exit(1)
    elif args.command == "init":
        handle_init_commands(args)
    elif args.command == "version":
        handle_versioning_commands(args)
    elif args.command == "marketplace":
        handle_marketplace_commands(args)
    elif args.command == "share":
        handle_sharing_commands(args)
    elif args.command == "compare":
        handle_compare_commands(args)
    elif args.command == "hardware": # Keep old hardware command handler for now
        handle_hardware_commands(args)
    elif args.command == "jobs":
        handle_job_commands(args)
    elif args.command == "config":
        handle_config_commands(args)
    elif args.command == "deps":
        handle_dependency_commands(args)
    elif args.command == "visualize":
        handle_visualization_commands(args)
    elif args.command == "interactive":
        start_shell()
    elif args.command == "security":
        handle_security_commands(args)
    else:
        # Check if it's a plugin command
        if args.command in get_registered_command_plugins():
            execute_plugin_command(args.command, args)
        else:
            # If the command is not recognized and not a plugin, show help
            print(f"Error: Unknown command '{args.command}'", file=sys.stderr)
            parser.print_help(sys.stderr)
            sys.exit(1)

    # Explicitly exit with 0 for success
    sys.exit(0)

# --- Command Handler Functions ---

def handle_security_commands(args):
    """Handle security subcommands."""
    if args.security_cmd == "scan":
        if hasattr(security_scan_mod, 'security_scan'):
            # Pass the potentially None source_file and dest_file
            success = security_scan_mod.security_scan(source_file=args.input_file, dest_file=args.output_file)
            # The security_scan function returns True if no critical/high issues are found
            print(f"Security scan completed.{' No critical or high severity issues found.' if success else ' Issues found.'}")
            sys.exit(0) # Exit 0 regardless of findings, but success indicates severity level
        else:
            logger.error("security_scan function not found. Cannot execute command.")
            print("Error: Command implementation missing.", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Error: Unknown security command '{args.security_cmd}'", file=sys.stderr)
        sys.exit(1)

def handle_ir_commands(args):
    """Handle ir subcommands."""
    if args.ir_cmd == "generate":
        # Pass LLM args to the generate_ir function
        if hasattr(ir_generate_mod, 'generate_ir'):
             success = ir_generate_mod.generate_ir(args.source, args.dest, args.use_llm, args.llm_provider, args.llm_model)
             sys.exit(0 if success else 1)
        else:
             logger.error("generate_ir function not found in the corresponding module. Cannot execute command.")
             print("Error: Command implementation missing.", file=sys.stderr)
             sys.exit(1)
    elif args.ir_cmd == "validate":
        if hasattr(ir_validate_mod, 'validate_circuit'):
             success = ir_validate_mod.validate_circuit(args.input_file, args.output_file, args.llm_url)
             sys.exit(0 if success else 1)
        else:
             logger.error("validate_circuit function not found in the corresponding module. Cannot execute command.")
             print("Error: Command implementation missing.", file=sys.stderr)
             sys.exit(1)
    elif args.ir_cmd == "optimize":
        if hasattr(ir_optimize_mod, 'optimize_circuit_command'):
            ir_optimize_mod.optimize_circuit_command(args)
        else:
             logger.error("optimize_circuit_command function not found. Cannot execute command.")
             print("Error: Command implementation missing.", file=sys.stderr)
             sys.exit(1)
    elif args.ir_cmd == "mitigate":
        # Call the refactored command function
        if hasattr(ir_mitigate_mod, 'mitigate_circuit_command'):
            ir_mitigate_mod.mitigate_circuit_command(args)
            # The command function handles sys.exit internally
        else:
            logger.error("mitigate_circuit_command function not found. Cannot execute command.")
            print("Error: Command implementation missing.", file=sys.stderr)
            sys.exit(1)
    elif args.ir_cmd == "finetune":
        if hasattr(ir_finetune_mod, 'finetune_circuit'):
            
            # Determine input file path
            input_file_path: Path | None = None
            if args.input_file is None:
                default_ir_dir = Path("ir/openqasm/mitigated") # Assuming mitigated is the right default for finetune
                logger.info(f"No input file specified for finetune. Searching in {default_ir_dir}...")
                input_file_path = find_first_file(default_ir_dir, "*.qasm")
                if not input_file_path:
                    logger.error(f"No .qasm file found in {default_ir_dir}. Please specify an input file.")
                    print(f"Error: No input file specified and no default found in {default_ir_dir}.", file=sys.stderr)
                    sys.exit(1)
                logger.info(f"Using default input file for finetune: {input_file_path}")
            else:
                input_file_path = Path(args.input_file)
                if not input_file_path.is_file():
                     logger.error(f"Specified input file not found: {input_file_path}")
                     print(f"Error: Input file not found: {input_file_path}", file=sys.stderr)
                     sys.exit(1)

            # Determine output file path
            output_file_path: Path | None = None
            if args.output_file is None:
                default_output_dir = Path("results/finetune")
                default_output_dir.mkdir(parents=True, exist_ok=True)
                output_filename = f"{input_file_path.stem}_finetune_results.json"
                output_file_path = default_output_dir / output_filename
                logger.info(f"No output file specified for finetune. Defaulting to: {output_file_path}")
            else:
                output_file_path = Path(args.output_file)
                output_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                # Call the finetune function - adjust args based on actual function signature
                success = ir_finetune_mod.finetune_circuit(
                    input_file=str(input_file_path), 
                    output_file=str(output_file_path),
                    hardware=args.hardware,
                    search_method=args.search,
                    shots=args.shots,
                    use_hardware=args.use_hardware,
                    device_id=args.device_id,
                    api_token=args.api_token,
                    max_circuits=args.max_circuits,
                    poll_timeout=args.poll_timeout
                    # Add/remove/rename args as needed based on finetune_circuit definition
                )
                # Assuming finetune_circuit returns True/False or raises exception
                sys.exit(0 if success else 1)
            except Exception as e:
                 logger.error(f"Finetuning failed for {input_file_path}: {e}", exc_info=True)
                 print(f"Error during finetuning: {e}", file=sys.stderr)
                 sys.exit(1)
        else:
            logger.error("finetune_circuit function not found. Cannot execute command.")
            print("Error: Command implementation missing.", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Error: Unknown ir command '{args.ir_cmd}'", file=sys.stderr)
        sys.exit(1)

def handle_run_commands(args):
    """Handle run subcommands (simulate, hw)."""
    if args.run_cmd == "simulate":
        # Use run_simulation directly
        success = simulate_mod.run_simulation(
            source_file=args.qasm_file,
            backend=args.backend,
            output=args.output,
            shots=args.shots
        )
        sys.exit(0 if success else 1)
    # Add handlers for other run commands (e.g., run hw) when implemented
    else:
        print(f"Error: Unknown run command '{args.run_cmd}'", file=sys.stderr)
        # Consider finding the parent parser to print help for the 'run' command
        # parser.print_help(sys.stderr) # This prints help for the main command
        sys.exit(1)

def handle_test_commands(args):
    """Handle test subcommands."""
    if args.test_cmd == "generate":
        if hasattr(test_generate_mod, 'generate_tests'):
            success = test_generate_mod.generate_tests(
                input_file=args.input_file,
                output_dir=args.output_dir,
                llm_provider=args.llm_provider,
                llm_model=args.llm_model
            )
            sys.exit(0 if success else 1)
        else:
            logger.error("generate_tests function not found in test_generate_mod. Cannot execute command.")
            print("Error: Command implementation missing.", file=sys.stderr)
            sys.exit(1)
    elif args.test_cmd == "run":
        if hasattr(test_generate_mod, 'run_tests'):
            success = test_generate_mod.run_tests(
                test_file=args.test_file,
                output_file=args.output,
                simulator=args.simulator,
                shots=args.shots
            )
            sys.exit(0 if success else 1)
        else:
            logger.error("run_tests function not found in test_generate_mod. Cannot execute command.")
            print("Error: Command implementation missing.", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Error: Unknown test command '{args.test_cmd}'", file=sys.stderr)
        # Consider finding the parent parser to print help for the 'test' command
        sys.exit(1)


def handle_analyze_commands(args):
    """Handle analyze subcommands."""
    if args.analyze_cmd == "resources":
        if hasattr(analyze_resources_mod, 'estimate_resources'):
            
            # Determine input file path
            input_file_path: Path | None = None
            if args.ir_file is None:
                default_ir_dir = Path("ir/openqasm/mitigated")
                logger.info(f"No IR file specified. Searching in {default_ir_dir}...")
                input_file_path = find_first_file(default_ir_dir, "*.qasm")
                if not input_file_path:
                    logger.error(f"No .qasm file found in {default_ir_dir}. Please specify an input file.")
                    print(f"Error: No input file specified and no default found in {default_ir_dir}.", file=sys.stderr)
                    sys.exit(1)
                logger.info(f"Using default input file: {input_file_path}")
            else:
                input_file_path = Path(args.ir_file)
                if not input_file_path.is_file():
                     logger.error(f"Specified input file not found: {input_file_path}")
                     print(f"Error: Input file not found: {input_file_path}", file=sys.stderr)
                     sys.exit(1)
            
            # Determine output file path
            output_file_path: Path | None = None
            if args.output is None:
                default_output_dir = Path("results/analysis/resources")
                default_output_dir.mkdir(parents=True, exist_ok=True) 
                output_filename = f"{input_file_path.stem}_resources.json"
                output_file_path = default_output_dir / output_filename
                logger.info(f"No output file specified. Defaulting to: {output_file_path}")
            else:
                output_file_path = Path(args.output)
                output_file_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                # Call the resource estimation function
                # Assume it handles output based on dest and potentially internal logic
                # It might print to console AND save to dest
                results_data = analyze_resources_mod.estimate_resources(
                    source=str(input_file_path), 
                    dest=str(output_file_path)
                )
                # The function might return the data or None/True/False
                # If it returns data and format is json, maybe print?
                if args.format == "json" and results_data:
                     try:
                         print(json.dumps(results_data, indent=2))
                     except TypeError:
                         # Handle case where results_data is not JSON serializable (e.g., boolean)
                         logger.debug("estimate_resources returned non-JSON data, relying on function's own output.")
                
                # We assume success if no exception was raised
                logger.info(f"Resource estimation process completed for {input_file_path}. Output expected at {output_file_path}")
                sys.exit(0) 
            except Exception as e:
                 logger.error(f"Resource estimation failed for {input_file_path}: {e}", exc_info=True)
                 print(f"Error during resource estimation: {e}", file=sys.stderr)
                 sys.exit(1)
        else:
            logger.error("estimate_resources function not found. Cannot execute command.")
            print("Error: Command implementation missing.", file=sys.stderr)
            sys.exit(1)
    elif args.analyze_cmd == "cost":
        if hasattr(calculate_cost, 'calculate_cost'):
            
            # Determine input file path
            input_file_path: Path | None = None
            if args.ir_file is None:
                default_ir_dir = Path("ir/openqasm/mitigated")
                logger.info(f"No IR file specified for cost analysis. Searching in {default_ir_dir}...")
                input_file_path = find_first_file(default_ir_dir, "*.qasm")
                if not input_file_path:
                    logger.error(f"No .qasm file found in {default_ir_dir}. Please specify an input file.")
                    print(f"Error: No input file specified and no default found in {default_ir_dir}.", file=sys.stderr)
                    sys.exit(1)
                logger.info(f"Using default input file for cost analysis: {input_file_path}")
            else:
                input_file_path = Path(args.ir_file)
                if not input_file_path.is_file():
                     logger.error(f"Specified input file not found: {input_file_path}")
                     print(f"Error: Input file not found: {input_file_path}", file=sys.stderr)
                     sys.exit(1)

            # Determine output file path
            output_file_path: Path | None = None
            if args.output is None:
                default_output_dir = Path("results/analysis/cost")
                default_output_dir.mkdir(parents=True, exist_ok=True)
                output_filename = f"{input_file_path.stem}_cost.json"
                output_file_path = default_output_dir / output_filename
                logger.info(f"No output file specified for cost analysis. Defaulting to: {output_file_path}")
            else:
                output_file_path = Path(args.output)
                output_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                # Call the cost calculation function
                # Assume it handles saving to dest and printing summary
                results = calculate_cost.calculate_cost(
                    source=str(input_file_path),
                    resource_file=args.resource_file, 
                    dest=str(output_file_path),
                    platform=args.platform,
                    shots=args.shots,
                    output_format=args.format 
                )
                
                # Minimal handling here: maybe print JSON if requested and returned
                if args.format == "json" and results:
                    try: print(json.dumps(results, indent=2))
                    except TypeError: logger.debug("calculate_cost returned non-JSON data")
                # Rely on calculate_cost for text summary printout
                                
                # Success
                sys.exit(0)
            except Exception as e:
                logger.error(f"Cost calculation failed for {input_file_path}: {e}", exc_info=True)
                print(f"Error during cost calculation: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            logger.error("calculate_cost function not found. Cannot execute command.")
            print("Error: Command implementation missing.", file=sys.stderr)
            sys.exit(1)
    elif args.analyze_cmd == "benchmark":
        if hasattr(analyze_benchmark_mod, 'benchmark'):
            
            # Determine input file path
            input_file_path: Path | None = None
            if args.ir_file is None:
                default_ir_dir = Path("ir/openqasm/mitigated")
                logger.info(f"No IR file specified for benchmark. Searching in {default_ir_dir}...")
                input_file_path = find_first_file(default_ir_dir, "*.qasm")
                if not input_file_path:
                    logger.error(f"No .qasm file found in {default_ir_dir}. Please specify an input file.")
                    print(f"Error: No input file specified and no default found in {default_ir_dir}.", file=sys.stderr)
                    sys.exit(1)
                logger.info(f"Using default input file for benchmark: {input_file_path}")
            else:
                input_file_path = Path(args.ir_file)
                if not input_file_path.is_file():
                     logger.error(f"Specified input file not found: {input_file_path}")
                     print(f"Error: Input file not found: {input_file_path}", file=sys.stderr)
                     sys.exit(1)

            # Determine output file path
            output_file_path: Path | None = None
            if args.output is None:
                default_output_dir = Path("results/analysis/benchmark")
                default_output_dir.mkdir(parents=True, exist_ok=True)
                output_filename = f"{input_file_path.stem}_benchmark.json"
                output_file_path = default_output_dir / output_filename
                logger.info(f"No output file specified for benchmark. Defaulting to: {output_file_path}")
            else:
                output_file_path = Path(args.output)
                output_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                # Call the benchmark function with CORRECT argument names
                success = analyze_benchmark_mod.benchmark(
                    source_file=str(input_file_path), 
                    dest_file=str(output_file_path)
                )
                sys.exit(0 if success else 1)
            except Exception as e:
                 logger.error(f"Benchmark failed for {input_file_path}: {e}", exc_info=True)
                 print(f"Error during benchmark: {e}", file=sys.stderr)
                 sys.exit(1)
        else:
            logger.error("benchmark function not found. Cannot execute command.")
            print("Error: Command implementation missing.", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Command 'analyze {args.analyze_cmd}' is not implemented yet.", file=sys.stderr)
        sys.exit(1)

def handle_init_commands(args):
    """Handle init subcommands."""
    from .commands import init as init_mod
    
    if args.init_cmd == "list":
        # List available templates
        # For now just return with success - we only have one template 
        print("Available templates:\n  - quantum_app: Standard Quantum Application (default)")
        sys.exit(0)
    elif args.init_cmd == "create":
        # Create new project
        if hasattr(init_mod, 'init_project'):
            success = init_mod.init_project(
                project_dir=args.directory,
                overwrite=args.overwrite if hasattr(args, 'overwrite') else False
            )
            sys.exit(0 if success else 1)
        else:
            logger.error("init_project function not found in the init module. Cannot execute command.")
            print("Error: Command implementation missing.", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Error: Unknown init command '{args.init_cmd}'", file=sys.stderr)
        sys.exit(1)

def handle_service_commands(args):
    """Handle service subcommands."""
    if args.service_cmd == "generate":
        from .commands import microservice
        
        # First ensure templates are set up
        if hasattr(microservice, 'setup_microservice_templates'):
            microservice.setup_microservice_templates()
        
        # Create base Docker image if needed and the function exists
        if hasattr(microservice, 'create_base_docker_image'):
            microservice.create_base_docker_image()
        
        # Generate the microservice
        if hasattr(microservice, 'generate_microservice'):
            # Determine app root directory
            app_root = os.path.abspath(args.app_root) if hasattr(args, 'app_root') and args.app_root else os.getcwd()
            logger.info(f"Using application root: {app_root}") # Log the determined app root
            
            # Parse output directory - Let generate_microservice handle the default
            output_dir = args.output_dir
            # Remove the block that calculates default output_dir based on args.input_file
            # if not output_dir:
            #     # Default to services/generated/<basename> relative to app root
            #     basename = os.path.splitext(os.path.basename(args.input_file))[0]
            #     output_dir = os.path.join(app_root, "services", "generated", basename)
            
            # Set custom Docker base image if provided
            if hasattr(args, 'base_image') and args.base_image:
                microservice.QUANTUM_DOCKER_IMAGE = args.base_image
            
            # Generate the microservice
            success = microservice.generate_microservice(
                source_file=args.input_file, # Correct: pass the value from the parsed args
                dest_dir=output_dir, # Pass None if omitted, function will handle default
                llm_url=args.llm_url,
                port=args.port,
                app_root=app_root # Explicitly pass the determined app_root
            )
            
            if success:
                # Read the final destination directory from the function if needed, or rely on its logging
                logger.info(f"Microservice generation initiated.") # Changed log message slightly
                print(f"Microservice generation initiated.") # Changed print message slightly
            
            sys.exit(0 if success else 1)
        else:
            logger.error("generate_microservice function not found in microservice module. Cannot execute command.")
            print("Error: Command implementation missing.", file=sys.stderr)
            sys.exit(1)
    
    elif args.service_cmd == "run":
        # Run the microservice with Docker
        from quantum_cli_sdk.utils import run_docker_command
        
        service_dir_abs = os.path.abspath(args.service_dir)
        if not os.path.exists(service_dir_abs):
            logger.error(f"Service directory not found: {service_dir_abs}")
            print(f"Error: Service directory not found: {service_dir_abs}", file=sys.stderr)
            sys.exit(1)
        
        # Check for Dockerfile in the service directory
        dockerfile_path = os.path.join(service_dir_abs, "Dockerfile")
        if not os.path.exists(dockerfile_path):
            logger.error(f"Dockerfile not found in: {service_dir_abs}")
            print(f"Error: Dockerfile not found in: {service_dir_abs}", file=sys.stderr)
            sys.exit(1)
        
        # Build the Docker image
        project_root = os.path.basename(os.path.dirname(service_dir_abs))
        image_name = f"{project_root}-as-quantum-service"
        image_tag = "latest"
        build_cmd = ["build", "-t", f"{image_name}:{image_tag}", service_dir_abs]
        
        logger.info(f"Building Docker image: {image_name}:{image_tag}")
        print(f"Building Docker image: {image_name}:{image_tag}")
        
        build_result = run_docker_command(build_cmd)
        if not build_result.get("success", False):
            logger.error(f"Failed to build Docker image: {build_result.get('stderr', '')}")
            print(f"Error: Failed to build Docker image\n{build_result.get('stderr', '')}", file=sys.stderr)
            sys.exit(1)
        
        # Run the Docker container
        port = args.port if hasattr(args, 'port') else 8889
        run_cmd = ["run", "-p", f"{port}:{port}"]
        
        if hasattr(args, 'detach') and args.detach:
            run_cmd.append("-d")

        # Add environment variables if specified
        if hasattr(args, 'env') and args.env:
            for env_var in args.env:
                run_cmd.extend(["-e", env_var])
        
        # Automatically pass IBM_QUANTUM_TOKEN from environment if it exists
        ibm_token = os.environ.get("IBM_QUANTUM_TOKEN")
        if ibm_token:
            run_cmd.extend(["-e", f"IBM_QUANTUM_TOKEN={ibm_token}"])
            logger.info("Passing IBM_QUANTUM_TOKEN from environment to container")
            # Create a sanitized command for logging that doesn't reveal the token
            log_cmd = run_cmd.copy()
            for i, item in enumerate(log_cmd):
                if item.startswith("IBM_QUANTUM_TOKEN="):
                    log_cmd[i] = "IBM_QUANTUM_TOKEN=********"
        else:
            logger.warning("IBM_QUANTUM_TOKEN not found in environment, quantum hardware access may be limited")
            log_cmd = run_cmd.copy()
        
        run_cmd.extend([f"{image_name}:{image_tag}"])
        log_cmd.extend([f"{image_name}:{image_tag}"])
        
        logger.info(f"Running Docker container: {' '.join(log_cmd)}")
        print(f"Starting microservice container...")
        
        run_result = run_docker_command(run_cmd)
        if not run_result.get("success", False):
            logger.error(f"Failed to run Docker container: {run_result.get('stderr', '')}")
            print(f"Error: Failed to run Docker container\n{run_result.get('stderr', '')}", file=sys.stderr)
            sys.exit(1)
        
        container_id = run_result.get("stdout", "").strip()
        if hasattr(args, 'detach') and args.detach and container_id:
            print(f"Microservice started in detached mode with container ID: {container_id}")
        
        print(f"Microservice running at http://localhost:{port}")
    
    elif args.service_cmd == "test-generate":
        from .commands import generate_microservice_tests
        
        if hasattr(generate_microservice_tests, 'generate_microservice_tests'):
            success = generate_microservice_tests.generate_microservice_tests(
                microservice_dir=args.service_dir,
                output_dir=args.output
            )
            sys.exit(0 if success else 1)
        else:
            logger.error("generate_microservice_tests function not found. Cannot execute command.")
            print("Error: Command implementation missing.", file=sys.stderr)
            sys.exit(1)
    
    elif args.service_cmd == "test-run":
        from .commands import run_microservice_tests
        
        if hasattr(run_microservice_tests, 'run_microservice_tests'):
            success = run_microservice_tests.run_microservice_tests(
                microservice_dir=args.service_dir,
                test_dir=args.test_dir,
                output_file=args.output,
                blocking=args.blocking if hasattr(args, 'blocking') else False
            )
            sys.exit(0 if success else 1)
        else:
            logger.error("run_microservice_tests function not found. Cannot execute command.")
            print("Error: Command implementation missing.", file=sys.stderr)
            sys.exit(1)
    
    else:
        print(f"Error: Unknown service command '{args.service_cmd}'", file=sys.stderr)
        sys.exit(1)

def handle_config_commands(args):
    """Handle configuration commands."""
    from . import config as config_mod
    
    if args.config_cmd == "get":
        # Get configuration value
        value = config_mod.get_config().get_setting(args.path)
        if value is not None:
            print(value)
        else:
            print(f"Configuration value not found: {args.path}", file=sys.stderr)
            sys.exit(1)
    elif args.config_cmd == "set":
        # Set configuration value
        if args.path.startswith("quantum_providers."):
            # Handle provider configuration
            parts = args.path.split(".")
            if len(parts) == 3:  # quantum_providers.provider.key
                provider = parts[1]
                key = parts[2]
                config_mod.get_config().set_provider_config(provider, key, args.value)
                config_mod.get_config().save_config()
            else:
                print(f"Invalid provider configuration path: {args.path}", file=sys.stderr)
                sys.exit(1)
        else:
            # Handle other configuration settings
            config_mod.get_config().set_setting(args.path, args.value)
            config_mod.get_config().save_config()
    elif args.config_cmd == "print":
        # Print entire configuration
        print(json.dumps(config_mod.get_config()._config, indent=2))
    elif args.config_cmd == "defaults":
        # Print default parameters
        if args.command:
            print(json.dumps(config_mod.get_config().get_profile_config().get("default_parameters", {}).get(args.command, {}), indent=2))
        else:
            print(json.dumps(config_mod.get_config().get_profile_config().get("default_parameters", {}), indent=2))
    elif args.config_cmd == "profile":
        if args.profile_cmd == "list":
            # List available profiles
            profiles = config_mod.get_config().get_all_profiles()
            active = config_mod.get_config().get_active_profile()
            print("Available profiles:")
            for profile in profiles:
                print(f"  {profile}{'*' if profile == active else ''}")
        elif args.profile_cmd == "create":
            # Create new profile
            if config_mod.get_config().create_profile(args.name):
                print(f"Created profile: {args.name}")
            else:
                sys.exit(1)
        elif args.profile_cmd == "load":
            # Load profile
            if config_mod.get_config().set_active_profile(args.name):
                print(f"Loaded profile: {args.name}")
            else:
                sys.exit(1)
        elif args.profile_cmd == "delete":
            # Delete profile
            if config_mod.get_config().delete_profile(args.name):
                print(f"Deleted profile: {args.name}")
            else:
                sys.exit(1)
        else:
            print(f"Unknown profile command: {args.profile_cmd}", file=sys.stderr)
            sys.exit(1)
    elif args.config_cmd == "export":
        # Export configuration
        try:
            with open(args.output_file, 'w') as f:
                json.dump(config_mod.get_config()._config, f, indent=2)
            print(f"Configuration exported to: {args.output_file}")
        except Exception as e:
            print(f"Failed to export configuration: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.config_cmd == "import":
        # Import configuration
        try:
            with open(args.input_file, 'r') as f:
                config_data = json.load(f)
            config_mod.get_config()._update_config(config_data)
            config_mod.get_config().save_config()
            print(f"Configuration imported from: {args.input_file}")
        except Exception as e:
            print(f"Failed to import configuration: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Unknown config command: {args.config_cmd}", file=sys.stderr)
        sys.exit(1)

def handle_package_commands(args):
    """Handle package subcommands."""
    if args.package_cmd == "create":
        from .commands import package as package_mod
        
        # Convert comma-separated strings to lists if provided
        requirements = args.requirements.split(',') if args.requirements else None
        include = args.include.split(',') if args.include else None
        exclude = args.exclude.split(',') if args.exclude else None
        
        # Create config overrides
        config_overrides = {}
        if args.app_name: config_overrides['app_name'] = args.app_name
        if args.version: config_overrides['version'] = args.version
        if args.app_description: config_overrides['app_description'] = args.app_description
        if args.author: config_overrides['author'] = args.author
        if args.license: config_overrides['license'] = args.license
        if requirements: config_overrides['requirements'] = requirements
        if include: config_overrides['include'] = include
        if exclude: config_overrides['exclude'] = exclude
        
        # Call the package function
        result = package_mod.package(
            source_dir=args.source_dir,
            output_path=args.output_path,
            format=args.format,
            config_file=args.config,
            config_overrides=config_overrides
        )
        
        if result:
            print(f"Package created: {result}")
            sys.exit(0)
        else:
            print("Failed to create package", file=sys.stderr)
            sys.exit(1)
            
    elif args.package_cmd == "info":
        from .commands import package as package_mod
        
        # Extract package info
        info = package_mod.extract_package_info(args.package_path)
        if not info:
            print("Failed to extract package information", file=sys.stderr)
            sys.exit(1)
            
        # Format output
        if args.format == "json":
            print(json.dumps(info, indent=2))
        elif args.format == "yaml":
            import yaml
            print(yaml.dump(info))
        else:  # text format
            print(f"Package: {info.get('name', 'Unknown')}")
            print(f"Version: {info.get('version', 'Unknown')}")
            print(f"Description: {info.get('description', 'None')}")
            print(f"Author: {info.get('author', 'Unknown')}")
            print(f"License: {info.get('license', 'Unknown')}")
            print(f"Entrypoint: {info.get('entrypoint', 'None')}")
            print("\nRequirements:")
            for req in info.get('requirements', []):
                print(f"  - {req}")
            print("\nFiles:")
            for file in info.get('files', []):
                print(f"  - {file}")
                
        sys.exit(0)
        
    elif args.package_cmd == "extract":
        from .commands import package as package_mod
        
        # Determine output directory
        output_dir = args.output_dir if args.output_dir else os.getcwd()
        
        # Extract package
        success = package_mod.extract_package(
            package_path=args.package_path,
            output_dir=output_dir,
            overwrite=args.overwrite
        )
        
        if success:
            print(f"Package extracted to: {output_dir}")
            sys.exit(0)
        else:
            print("Failed to extract package", file=sys.stderr)
            sys.exit(1)
            
    else:
        print(f"Error: Unknown package command '{args.package_cmd}'", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
