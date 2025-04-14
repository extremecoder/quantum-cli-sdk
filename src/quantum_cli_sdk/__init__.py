"""
Quantum SDK - A command-line interface and software development kit for quantum computing.
"""

__version__ = "0.3.5"

from .quantum_circuit import QuantumCircuit
from .simulator import run_simulation
from .config import get_config, initialize_config
from .cache import get_cache, initialize_cache
from .transpiler import get_pass_manager, initialize_transpiler
from .plugin_system import discover_plugins, register_command_plugin, get_registered_command_plugins

__all__ = [
    'QuantumCircuit',
    'run_simulation',
    'get_config',
    'initialize_config',
    'get_cache',
    'initialize_cache',
    'get_pass_manager',
    'initialize_transpiler',
    'discover_plugins',
    'register_command_plugin',
    'get_registered_command_plugins',
]
