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
from .quantum_circuit import QuantumCircuit
from .simulator import run_simulation
from .commands import run
from .commands import generate_ir, simulate, hw_run, estimate_resources, template, mitigate, calculate_cost, init
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
from . import circuit_comparison
from . import hardware_selector
from . import job_management
from . import config_manager
from . import dependency_analyzer
from . import progress
from . import output_formatter
from . import logging_config

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

def main():
    """Main entry point for the CLI."""
    # Parse arguments
    parser = argparse.ArgumentParser(description=f"Quantum CLI SDK v{__version__}")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--profile", help="Configuration profile to use")
    
    # Add subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Run simulation
    run_parser = subparsers.add_parser("run", help="Run a quantum circuit")
    run_parser.add_argument("--circuit", "-c", required=True, help="Path to circuit file")
    run_parser.add_argument("--shots", "-s", type=int, default=1024, help="Number of shots")
    run_parser.add_argument("--output", "-o", help="Output file path")
    
    # Generate IR command
    ir_parser = subparsers.add_parser("generate-ir", help="Generate intermediate representation")
    ir_parser.add_argument("--source", "-s", required=True, help="Source circuit file")
    ir_parser.add_argument("--dest", "-d", help="Destination IR file")
    ir_parser.add_argument("--format", "-f", choices=["qasm", "qiskit", "cirq"], default="qasm", help="Output format")
    
    # Simulate command
    simulate_parser = subparsers.add_parser("simulate", help="Simulate a quantum circuit")
    simulate_parser.add_argument("--source", "-s", required=True, help="Source circuit file")
    simulate_parser.add_argument("--dest", "-d", help="Destination results file")
    simulate_parser.add_argument("--simulator", choices=["qiskit", "cirq", "braket", "all"], 
                                default=config_manager.get_default_param("simulate", "simulator"), 
                                help="Simulator backend")
    simulate_parser.add_argument("--shots", type=int, 
                               default=config_manager.get_default_param("simulate", "shots"), 
                               help="Number of shots")
    simulate_parser.add_argument("--use-cache", action="store_true", help="Use simulation cache if available")
    simulate_parser.add_argument("--visualize", action="store_true", help="Visualize results")
    
    # Hardware run command
    hw_run_parser = subparsers.add_parser("hw-run", help="Run on quantum hardware")
    hw_run_parser.add_argument("--source", "-s", required=True, help="Source circuit file")
    hw_run_parser.add_argument("--dest", "-d", help="Destination results file")
    hw_run_parser.add_argument("--platform", choices=["ibm", "aws", "gcp", "azure"], 
                              default=config_manager.get_default_param("hw-run", "platform"), 
                              help="Hardware platform")
    hw_run_parser.add_argument("--device", help="Target quantum device")
    hw_run_parser.add_argument("--shots", type=int, 
                               default=config_manager.get_default_param("hw-run", "shots"), 
                               help="Number of shots")
    hw_run_parser.add_argument("--credentials", help="Path to credentials file")
    
    # Estimate resources command
    estimate_parser = subparsers.add_parser("estimate-resources", help="Estimate resources for a circuit")
    estimate_parser.add_argument("--source", "-s", required=True, help="Source circuit file")
    estimate_parser.add_argument("--dest", "-d", help="Destination report file")
    estimate_parser.add_argument("--detailed", action="store_true", 
                                default=config_manager.get_default_param("estimate-resources", "detailed"),
                                help="Include detailed breakdown")
    estimate_parser.add_argument("--target", choices=["generic", "ibm", "aws", "gcp", "azure"], 
                               default=config_manager.get_default_param("estimate-resources", "target"),
                               help="Target architecture")
    
    # Calculate cost command
    cost_parser = subparsers.add_parser("calculate-cost", help="Calculate cost of running a circuit")
    cost_parser.add_argument("--source", "-s", required=True, help="Source circuit file")
    cost_parser.add_argument("--platform", choices=["ibm", "aws", "gcp", "azure", "all"], 
                            default=",".join(config_manager.get_default_param("calculate-cost", "providers")),
                            help="Hardware platform(s)")
    cost_parser.add_argument("--shots", type=int, default=1000, help="Number of shots")
    cost_parser.add_argument("--currency", default=config_manager.get_default_param("calculate-cost", "currency"), 
                            help="Currency (USD, EUR, etc.)")
    cost_parser.add_argument("--output-format", choices=["text", "json", "csv"], default="text", help="Output format")
    cost_parser.add_argument("--output-file", help="Output file path")
    
    # Template commands
    template_parser = subparsers.add_parser("template", help="Manage circuit templates")
    template_subparsers = template_parser.add_subparsers(dest="template_cmd", help="Template command")
    
    # List templates
    list_parser = template_subparsers.add_parser("list", help="List available templates")
    
    # Get template
    get_parser = template_subparsers.add_parser("get", help="Get a template")
    get_parser.add_argument("template", help="Template name")
    get_parser.add_argument("--dest", "-d", help="Destination file")
    
    # Error mitigation commands
    mitigate_parser = subparsers.add_parser("mitigate", help="Apply error mitigation")
    mitigate_parser.add_argument("--source", "-s", required=True, help="Source circuit or results file")
    mitigate_parser.add_argument("--dest", "-d", help="Destination file")
    mitigate_parser.add_argument("--technique", choices=["zne", "pec", "cdr", "dd"], 
                               default=config_manager.get_default_param("mitigate", "method"),
                               help="Mitigation technique")
    mitigate_parser.add_argument("--noise-model", help="Path to noise model file")
    
    # Interactive mode command
    interactive_parser = subparsers.add_parser("interactive", help="Start interactive shell")
    
    # Visualize command
    visualize_parser = subparsers.add_parser("visualize", help="Visualize circuit or results")
    visualize_subparsers = visualize_parser.add_subparsers(dest="visualize_cmd", help="Visualization type")
    
    # Visualize circuit
    circuit_viz_parser = visualize_subparsers.add_parser("circuit", help="Visualize a quantum circuit")
    circuit_viz_parser.add_argument("--source", "-s", required=True, help="Source circuit file")
    circuit_viz_parser.add_argument("--output", "-o", help="Output file path")
    circuit_viz_parser.add_argument("--format", choices=["text", "latex", "mpl", "html"], default="text", help="Output format")
    
    # Visualize results
    results_viz_parser = visualize_subparsers.add_parser("results", help="Visualize simulation results")
    results_viz_parser.add_argument("--source", "-s", required=True, help="Source results file")
    results_viz_parser.add_argument("--output", "-o", help="Output file path")
    results_viz_parser.add_argument("--type", choices=["histogram", "statevector", "hinton", "qsphere"], default="histogram", help="Visualization type")
    results_viz_parser.add_argument("--interactive", action="store_true", help="Generate interactive visualization")
    
    # Setup additional command parsers
    setup_versioning_commands(subparsers)
    setup_marketplace_commands(subparsers)
    setup_sharing_commands(subparsers)
    setup_compare_commands(subparsers)
    setup_hardware_commands(subparsers)
    setup_job_commands(subparsers)
    setup_config_commands(subparsers)
    setup_dependency_commands(subparsers)
    setup_init_commands(subparsers)
    
    # Initialize SDK components
    initialize_sdk()
    
    # Discover and register plugins
    discover_plugins()
    
    # Set up plugin subparsers
    setup_plugin_subparsers(subparsers)
    
    # Parse arguments
    args = parser.parse_args()
    
    # If profile is specified, set it as the active profile
    if args.profile:
        config = get_config()
        if not config.set_active_profile(args.profile):
            logger.error(f"Profile '{args.profile}' not found")
            return 1
    
    # Handle commands
    if args.command == "run":
        run.run_circuit(args.circuit, args.shots, args.output)
    
    elif args.command == "generate-ir":
        generate_ir.generate_ir(args.source, args.dest, args.format)
    
    elif args.command == "simulate":
        simulate.simulate_circuit(args.source, args.dest, args.simulator, args.shots, args.use_cache, args.visualize)
    
    elif args.command == "hw-run":
        hw_run.run_on_hardware(args.source, args.dest, args.platform, args.device, args.shots, args.credentials)
    
    elif args.command == "estimate-resources":
        estimate_resources.estimate_resources(args.source, args.dest, args.detailed, args.target)
    
    elif args.command == "calculate-cost":
        calculate_cost.calculate_cost(args.source, args.platform.split(','), args.shots, args.currency, args.output_format, args.output_file)
    
    elif args.command == "template":
        if args.template_cmd == "list":
            template.list_templates()
        elif args.template_cmd == "get":
            template.get_template(args.template, args.dest)
        else:
            template_parser.print_help()
    
    elif args.command == "mitigate":
        mitigate.apply_mitigation(args.source, args.dest, args.technique, args.noise_model)
    
    elif args.command == "interactive":
        start_shell()
    
    elif args.command == "visualize":
        if args.visualize_cmd == "circuit":
            visualize_circuit_command(args.source, args.output, args.format)
        elif args.visualize_cmd == "results":
            visualize_results_command(args.source, args.output, args.type, args.interactive)
        else:
            visualize_parser.print_help()
    
    elif args.command == "version":
        handle_versioning_commands(args)
    
    elif args.command == "marketplace":
        handle_marketplace_commands(args)
    
    elif args.command == "share":
        handle_sharing_commands(args)
    
    elif args.command == "compare":
        handle_compare_commands(args)
        
    elif args.command == "find-hardware":
        handle_hardware_commands(args)
        
    elif args.command == "jobs":
        handle_job_commands(args)
        
    elif args.command == "config":
        handle_config_commands(args)
        
    elif args.command == "deps":
        handle_dependency_commands(args)
    
    elif args.command == "init":
        handle_init_commands(args)
        
    # Handle plugin commands
    elif args.command in get_registered_command_plugins():
        execute_plugin_command(args.command, args)
    
    else:
        parser.print_help()
    
    return 0

def handle_versioning_commands(args):
    """Handle versioning commands."""
    if args.version_cmd == "init":
        init_repo(args.repo_path)
    elif args.version_cmd == "commit":
        commit_circuit(args.repo_path, args.circuit_name, args.circuit_file, args.message, args.author)
    elif args.version_cmd == "get":
        get_circuit_version(args.repo_path, args.circuit_name, args.version_id, args.output_file)
    elif args.version_cmd == "list":
        list_circuit_versions(args.repo_path, args.circuit_name)
    elif args.version_cmd == "checkout":
        checkout_version(args.repo_path, args.circuit_name, args.version_id, args.output_file)
    else:
        logger.error("Please specify a versioning command")
        sys.exit(1)

def handle_marketplace_commands(args):
    """Handle marketplace commands."""
    if args.marketplace_cmd == "browse":
        browse_marketplace(args.tag, args.sort_by)
    elif args.marketplace_cmd == "search":
        search_marketplace(args.query)
    elif args.marketplace_cmd == "get":
        get_algorithm_details(args.algorithm_id)
    elif args.marketplace_cmd == "download":
        download_algorithm(args.algorithm_id, args.output_path)
    elif args.marketplace_cmd == "publish":
        tags = args.tags.split(",") if args.tags else []
        requirements = args.requirements.split(",") if args.requirements else []
        publish_algorithm(args.name, args.description, args.circuit_file, 
                         args.version, tags, requirements, args.example_usage)
    elif args.marketplace_cmd == "review":
        submit_review(args.algorithm_id, args.rating, args.comment)
    elif args.marketplace_cmd == "configure":
        configure_marketplace(args.api_key, args.endpoint)
    else:
        logger.error("Please specify a marketplace command")
        sys.exit(1)

def handle_sharing_commands(args):
    """Handle sharing commands."""
    if args.sharing_cmd == "circuit":
        recipients = args.recipients.split(",")
        tags = args.tags.split(",") if args.tags else []
        share_circuit(args.repo_path, args.circuit_name, args.version_id, 
                     args.description, args.storage_path, recipients, args.permission, tags)
    elif args.sharing_cmd == "list":
        if args.shared_by_me:
            list_my_shared_circuits(args.storage_path)
        elif args.shared_with_me:
            list_shared_with_me(args.storage_path)
        else:
            # Default to showing both
            list_my_shared_circuits(args.storage_path)
            print("\n")
            list_shared_with_me(args.storage_path)
    elif args.sharing_cmd == "get":
        get_shared_circuit_details(args.share_id, args.output_file, args.storage_path)
    elif args.sharing_cmd == "permissions":
        update_share_permissions(args.share_id, args.collaborator, args.permission, args.storage_path)
    elif args.sharing_cmd == "remove-collaborator":
        remove_collaborator(args.share_id, args.collaborator, args.storage_path)
    elif args.sharing_cmd == "unshare":
        unshare_circuit(args.share_id, args.storage_path)
    elif args.sharing_cmd == "activity":
        get_activity_history(args.share_id, args.storage_path)
    elif args.sharing_cmd == "search":
        search_shared_circuits(args.query, args.storage_path)
    else:
        logger.error("Please specify a sharing command")
        sys.exit(1)

def handle_compare_commands(args):
    """Handle circuit comparison commands."""
    metrics = args.metrics.split(",") if args.metrics else None
    compare_circuits(args.circuit1, args.circuit2, args.output_format, 
                    args.output_file, args.detailed, metrics, args.visualize)

def handle_hardware_commands(args):
    """Handle hardware selection commands."""
    providers = args.provider.split(",") if args.provider else None
    find_compatible_hardware(args.circuit, args.criteria, providers, 
                            args.min_qubits, args.max_cost, args.output_format,
                            args.output_file, args.top, args.update_catalog)

def handle_job_commands(args):
    """Handle job management commands."""
    if args.jobs_cmd == "list":
        statuses = args.status.split(",") if args.status else None
        list_jobs(statuses, args.provider, args.backend, args.days, args.storage_path)
    elif args.jobs_cmd == "get":
        get_job_details(args.job_id, args.storage_path)
    elif args.jobs_cmd == "results":
        get_job_results(args.job_id, args.output_file, args.output_format, args.storage_path)
    elif args.jobs_cmd == "cancel":
        cancel_job(args.job_id, args.storage_path)
    elif args.jobs_cmd == "monitor":
        statuses = args.status.split(",") if args.status else None
        monitor_jobs(args.job_id, statuses, args.interval, args.storage_path)
    else:
        logger.error("Please specify a jobs command")
        sys.exit(1)

def handle_config_commands(args):
    """Handle configuration commands."""
    if args.config_cmd == "get":
        value = get_config_value(args.path)
        if value is not None:
            print(value)
        else:
            print(f"Configuration value not found: {args.path}")
            sys.exit(1)
    elif args.config_cmd == "set":
        # Convert string to appropriate type
        value = args.value
        if value.lower() == "true":
            value = True
        elif value.lower() == "false":
            value = False
        elif value.isdigit():
            value = int(value)
        elif value.replace(".", "", 1).isdigit():
            value = float(value)
            
        if set_config_value(args.path, value):
            print(f"Configuration value set: {args.path} = {value}")
        else:
            print(f"Failed to set configuration value: {args.path}")
            sys.exit(1)
    elif args.config_cmd == "print":
        print_config()
    elif args.config_cmd == "defaults":
        print_default_params(args.command)
    elif args.config_cmd == "profile":
        if args.profile_cmd == "list":
            profiles = list_profiles()
            active = get_active_profile()
            print("Available profiles:")
            for profile in profiles:
                if profile == active:
                    print(f"* {profile} (active)")
                else:
                    print(f"  {profile}")
        elif args.profile_cmd == "create":
            if create_profile(args.name, args.description):
                print(f"Profile created: {args.name}")
            else:
                print(f"Failed to create profile: {args.name}")
                sys.exit(1)
        elif args.profile_cmd == "load":
            if load_profile(args.name):
                print(f"Profile loaded: {args.name}")
            else:
                print(f"Failed to load profile: {args.name}")
                sys.exit(1)
        elif args.profile_cmd == "delete":
            if delete_profile(args.name):
                print(f"Profile deleted: {args.name}")
            else:
                print(f"Failed to delete profile: {args.name}")
                sys.exit(1)
        else:
            logger.error("Please specify a profile command")
            sys.exit(1)
    elif args.config_cmd == "export":
        if export_config(args.output_file):
            print(f"Configuration exported to: {args.output_file}")
        else:
            print(f"Failed to export configuration")
            sys.exit(1)
    elif args.config_cmd == "import":
        if import_config(args.input_file, args.overwrite):
            print(f"Configuration imported from: {args.input_file}")
        else:
            print(f"Failed to import configuration")
            sys.exit(1)
    else:
        logger.error("Please specify a configuration command")
        sys.exit(1)

def handle_dependency_commands(args):
    """Handle dependency analysis commands."""
    if args.deps_cmd == "check":
        exit_code = check_dependencies(args.requirements)
        sys.exit(exit_code)
    elif args.deps_cmd == "report":
        if save_dependency_report(args.output, args.format, args.requirements):
            print(f"Dependency report saved to {args.output}")
        else:
            print("Failed to save dependency report")
            sys.exit(1)
    elif args.deps_cmd == "install-cmd":
        install_cmd = get_install_command(args.requirements)
        if install_cmd:
            print(install_cmd)
        else:
            print("No missing packages found")
    elif args.deps_cmd == "verify":
        if verify_specific_package(args.package, args.version):
            print(f"Package {args.package} OK")
        else:
            print(f"Package {args.package} verification failed")
            sys.exit(1)
    else:
        logger.error("Please specify a dependency command")
        sys.exit(1)

def handle_init_commands(args):
    """Handle init commands."""
    if args.init_cmd == "list":
        # Assuming init.list_templates() exists or is handled elsewhere
        print("Listing templates... (Placeholder)") # Placeholder if list_templates was removed
        # init.list_templates() # Uncomment if function exists
    elif args.init_cmd == "create":
        # Use the positional 'directory' argument for the project path
        project_dir_to_use = args.directory
        init.init_project(project_dir=project_dir_to_use, overwrite=args.overwrite)
    else:
        print("Use 'init list' to see available templates or 'init create <directory_name>' to create a new project.", file=sys.stderr)

if __name__ == "__main__":
    sys.exit(main())
