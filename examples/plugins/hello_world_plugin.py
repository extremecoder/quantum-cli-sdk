"""
Example plugin for the Quantum CLI SDK.

This plugin adds a simple 'hello-world' command to the CLI.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from quantum_cli_sdk.plugin_system import CommandPlugin, register_command_plugin

class HelloWorldCommand(CommandPlugin):
    """Example command plugin that prints a hello world message."""
    
    @property
    def name(self) -> str:
        """Get the name of the command."""
        return "hello-world"
    
    @property
    def description(self) -> str:
        """Get the description of the command."""
        return "Print a hello world message with quantum-themed greeting"
    
    def setup_parser(self, parser):
        """Set up the argument parser for this command.
        
        Args:
            parser: ArgumentParser instance for this command
        """
        parser.add_argument("--name", type=str, default="Quantum Developer",
                           help="Name to greet")
        parser.add_argument("--qubits", type=int, default=3,
                           help="Number of qubits in greeting visualization")
        parser.add_argument("--output", type=str,
                           help="Output file to save the greeting")
    
    def execute(self, args) -> int:
        """Execute the command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        # Create a quantum-themed greeting
        greeting = f"Hello, {args.name}! Welcome to the quantum realm."
        
        # Add a simple ASCII art visualization of qubits
        qubit_art = ""
        for i in range(args.qubits):
            qubit_art += f"Qubit {i}: |0⟩ + |1⟩\n"
        
        # Full message
        message = f"""
╭──────────────────────────────────────╮
│ {greeting.center(42)} │
│                                      │
{qubit_art.center(52)}
│                                      │
│ {"Superposition achieved!".center(42)} │
╰──────────────────────────────────────╯
"""
        
        # Print the message
        print(message)
        
        # Save to file if requested
        if args.output:
            try:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                result = {
                    "greeting": greeting,
                    "qubits": args.qubits,
                    "message": message,
                    "timestamp": str(Path.now)
                }
                
                with open(output_path, 'w') as f:
                    json.dump(result, f, indent=2)
                
                print(f"Greeting saved to {args.output}")
                
            except Exception as e:
                print(f"Error saving greeting to file: {e}")
                return 1
        
        return 0


# Register the plugin when this module is imported
def register():
    """Register the plugin with the CLI."""
    register_command_plugin(HelloWorldCommand())

# Call register function automatically
register() 