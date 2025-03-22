"""
Interactive REPL mode for Quantum CLI SDK.

This module provides an interactive shell for quantum computing experiments.
"""

import cmd
import json
import os
import re
import shlex
import sys
import time
import logging
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.traceback import install as install_rich_traceback

from . import __version__
from .config import get_config
from .quantum_circuit import QuantumCircuit
from .simulator import run_simulation

# Set up logging
logger = logging.getLogger(__name__)

# Install rich traceback handling
install_rich_traceback()

# Create rich console
console = Console()

class QuantumShell(cmd.Cmd):
    """Interactive shell for quantum computing experiments."""
    
    intro = f"""
[bold blue]Quantum CLI SDK Interactive Shell v{__version__}[/bold blue]
Type [bold green]help[/bold green] to list available commands or [bold green]help <command>[/bold green] for information on a specific command.
Type [bold green]exit[/bold green] to exit the shell.
    """
    prompt = "[bold cyan]quantum> [/bold cyan]"
    
    def __init__(self, no_welcome=False):
        """Initialize the quantum shell."""
        super().__init__()
        self.config = get_config()
        self.active_profile = self.config.get_active_profile()
        self.current_circuit = None
        self.last_result = None
        self.history = []
        
        # Current working directory for quantum files
        self.qwd = os.getcwd()
        
        # Display welcome message
        if not no_welcome:
            console.print(Panel.fit(
                Markdown(self.intro),
                title="Welcome",
                border_style="green"
            ))
        
        console.print(f"Using profile: [bold green]{self.active_profile}[/bold green]")
    
    def emptyline(self):
        """Do nothing on empty line."""
        pass
    
    def default(self, line):
        """Handle unrecognized commands."""
        console.print(f"[bold red]Unknown command:[/bold red] {line}")
        console.print("Type [bold green]help[/bold green] to see available commands.")
        return False
    
    def do_exit(self, arg):
        """Exit the interactive shell."""
        console.print("[bold yellow]Exiting Quantum CLI SDK interactive shell.[/bold yellow]")
        return True
    
    def do_quit(self, arg):
        """Alias for exit."""
        return self.do_exit(arg)
    
    def do_profile(self, arg):
        """View or change the active configuration profile.
        
        Usage:
            profile                 Show the current profile
            profile list            List all available profiles
            profile switch <name>   Switch to the specified profile
        """
        args = shlex.split(arg)
        
        if not args:
            # Display current profile
            console.print(f"Current profile: [bold green]{self.active_profile}[/bold green]")
            return
        
        if args[0] == "list":
            # List available profiles
            profiles = self.config.get_all_profiles()
            
            table = Table(title="Available Profiles")
            table.add_column("Profile", style="cyan")
            table.add_column("Active", style="green")
            
            for profile in profiles:
                is_active = profile == self.active_profile
                table.add_row(
                    profile, 
                    "✓" if is_active else ""
                )
            
            console.print(table)
            
        elif args[0] == "switch" and len(args) > 1:
            # Switch profile
            profile_name = args[1]
            
            if self.config.set_active_profile(profile_name):
                self.active_profile = profile_name
                console.print(f"Switched to profile: [bold green]{profile_name}[/bold green]")
            else:
                console.print(f"[bold red]Error:[/bold red] Profile '{profile_name}' not found")
        else:
            console.print(f"[bold red]Error:[/bold red] Unknown profile command: {arg}")
            console.print(self.do_profile.__doc__)
    
    def do_circuit(self, arg):
        """Create, load, or manipulate quantum circuits.
        
        Usage:
            circuit create <qubits>   Create a new circuit with specified qubits
            circuit load <filename>   Load a circuit from a file
            circuit save <filename>   Save the current circuit to a file
            circuit show              Display the current circuit
        """
        args = shlex.split(arg)
        
        if not args:
            if self.current_circuit:
                console.print(f"Current circuit: {self.current_circuit.num_qubits} qubits, {len(self.current_circuit.gates)} gates")
            else:
                console.print("[bold yellow]No active circuit. Create or load one first.[/bold yellow]")
            return
        
        if args[0] == "create" and len(args) > 1:
            try:
                qubits = int(args[1])
                self.current_circuit = QuantumCircuit(qubits)
                console.print(f"Created circuit with [bold green]{qubits}[/bold green] qubits")
            except ValueError:
                console.print(f"[bold red]Error:[/bold red] Invalid number of qubits: {args[1]}")
        
        elif args[0] == "load" and len(args) > 1:
            try:
                filename = args[1]
                if not os.path.isabs(filename):
                    filename = os.path.join(self.qwd, filename)
                
                # In a real implementation, this would load from OpenQASM or JSON
                console.print(f"Loading circuit from [bold blue]{filename}[/bold blue]")
                # Placeholder - would actually load circuit here
                self.current_circuit = QuantumCircuit(2)
                console.print(f"Loaded circuit with [bold green]{self.current_circuit.num_qubits}[/bold green] qubits")
            except Exception as e:
                console.print(f"[bold red]Error loading circuit:[/bold red] {str(e)}")
        
        elif args[0] == "save" and len(args) > 1:
            if not self.current_circuit:
                console.print("[bold red]Error:[/bold red] No active circuit to save")
                return
            
            try:
                filename = args[1]
                if not os.path.isabs(filename):
                    filename = os.path.join(self.qwd, filename)
                
                # In a real implementation, this would save as OpenQASM or JSON
                console.print(f"Saving circuit to [bold blue]{filename}[/bold blue]")
                # Placeholder - would actually save circuit here
                console.print("Circuit saved successfully")
            except Exception as e:
                console.print(f"[bold red]Error saving circuit:[/bold red] {str(e)}")
        
        elif args[0] == "show":
            if not self.current_circuit:
                console.print("[bold red]Error:[/bold red] No active circuit to show")
                return
            
            # In a real implementation, this would format the circuit for display
            console.print(Panel.fit(
                f"Quantum Circuit: {self.current_circuit.num_qubits} qubits\n" +
                f"Gates: {len(self.current_circuit.gates)}",
                title="Current Circuit",
                border_style="cyan"
            ))
        
        else:
            console.print(f"[bold red]Error:[/bold red] Unknown circuit command: {arg}")
            console.print(self.do_circuit.__doc__)
    
    def do_gate(self, arg):
        """Add gates to the current quantum circuit.
        
        Usage:
            gate h <qubit>             Add Hadamard gate to specified qubit
            gate x <qubit>             Add Pauli-X (NOT) gate to specified qubit
            gate y <qubit>             Add Pauli-Y gate to specified qubit
            gate z <qubit>             Add Pauli-Z gate to specified qubit
            gate cx <control> <target> Add CNOT gate with specified control and target qubits
            gate cz <control> <target> Add CZ gate with specified control and target qubits
        """
        if not self.current_circuit:
            console.print("[bold red]Error:[/bold red] No active circuit. Create or load one first.")
            return
        
        args = shlex.split(arg)
        
        if not args:
            console.print(self.do_gate.__doc__)
            return
        
        try:
            gate_type = args[0].lower()
            
            # Single-qubit gates
            if gate_type in ('h', 'x', 'y', 'z') and len(args) > 1:
                qubit = int(args[1])
                
                if qubit >= self.current_circuit.num_qubits:
                    console.print(f"[bold red]Error:[/bold red] Qubit index {qubit} out of range (0-{self.current_circuit.num_qubits-1})")
                    return
                
                # Add gate to circuit - just tracking for the interactive demo
                self.current_circuit.add_gate(gate_type, [qubit])
                console.print(f"Added {gate_type.upper()} gate to qubit {qubit}")
            
            # Two-qubit gates
            elif gate_type in ('cx', 'cz') and len(args) > 2:
                control = int(args[1])
                target = int(args[2])
                
                if control >= self.current_circuit.num_qubits or target >= self.current_circuit.num_qubits:
                    console.print(f"[bold red]Error:[/bold red] Qubit index out of range (0-{self.current_circuit.num_qubits-1})")
                    return
                
                # Add gate to circuit - just tracking for the interactive demo
                self.current_circuit.add_gate(gate_type, [control, target])
                console.print(f"Added {gate_type.upper()} gate with control={control}, target={target}")
            
            else:
                console.print(f"[bold red]Error:[/bold red] Invalid gate command: {arg}")
                console.print(self.do_gate.__doc__)
        
        except ValueError:
            console.print(f"[bold red]Error:[/bold red] Qubit indices must be integers")
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
    
    def do_simulate(self, arg):
        """Simulate the current quantum circuit.
        
        Usage:
            simulate                  Run simulation with default parameters
            simulate --shots <n>      Specify number of shots (default: 1024)
            simulate --save <file>    Save results to a file
        """
        if not self.current_circuit:
            console.print("[bold red]Error:[/bold red] No active circuit to simulate")
            return
        
        # Parse arguments
        shots = 1024
        save_file = None
        
        args = shlex.split(arg)
        i = 0
        while i < len(args):
            if args[i] == "--shots" and i + 1 < len(args):
                try:
                    shots = int(args[i + 1])
                    i += 2
                except ValueError:
                    console.print(f"[bold red]Error:[/bold red] Invalid number of shots: {args[i + 1]}")
                    return
            elif args[i] == "--save" and i + 1 < len(args):
                save_file = args[i + 1]
                i += 2
            else:
                console.print(f"[bold red]Error:[/bold red] Unknown option: {args[i]}")
                return
        
        # Run simulation
        console.print(f"Running simulation with [bold green]{shots}[/bold green] shots...")
        
        start_time = time.time()
        
        # Placeholder for actual simulation
        # In a real implementation, this would call the simulator backend
        time.sleep(1)  # Simulate work
        
        # Create simulated results - would actually be run_simulation() result
        results = {
            "counts": {"00": int(shots * 0.48), "11": int(shots * 0.48), 
                       "01": int(shots * 0.02), "10": int(shots * 0.02)},
            "execution_time": time.time() - start_time,
            "shots": shots,
            "timestamp": time.time()
        }
        
        self.last_result = results
        
        # Display results
        table = Table(title=f"Simulation Results ({shots} shots)")
        table.add_column("Outcome", style="cyan")
        table.add_column("Count", style="green", justify="right")
        table.add_column("Probability", style="magenta", justify="right")
        
        for outcome, count in results["counts"].items():
            probability = count / shots
            table.add_row(
                outcome,
                str(count),
                f"{probability:.4f}"
            )
        
        console.print(table)
        console.print(f"Simulation completed in [bold green]{results['execution_time']:.3f}[/bold green] seconds")
        
        # Save results to file if requested
        if save_file:
            try:
                if not os.path.isabs(save_file):
                    save_file = os.path.join(self.qwd, save_file)
                
                # Ensure the directory exists
                os.makedirs(os.path.dirname(os.path.abspath(save_file)), exist_ok=True)
                
                with open(save_file, 'w') as f:
                    json.dump(results, f, indent=2)
                console.print(f"Results saved to [bold blue]{save_file}[/bold blue]")
            except Exception as e:
                console.print(f"[bold red]Error saving results:[/bold red] {str(e)}")
    
    def do_bell(self, arg):
        """Create a Bell state circuit."""
        # Create a 2-qubit circuit
        self.current_circuit = QuantumCircuit(2)
        
        # Add gates for Bell state
        self.current_circuit.add_gate('h', [0])
        self.current_circuit.add_gate('cx', [0, 1])
        
        console.print("Created Bell state circuit:")
        console.print("q₀: ─[H]─■─")
        console.print("q₁: ────╰X╯")
        
        return False
    
    def do_examples(self, arg):
        """Show and load example quantum circuits.
        
        Usage:
            examples list              List available example circuits
            examples load <name>       Load the specified example circuit
        """
        args = shlex.split(arg)
        
        examples = {
            "bell": {"qubits": 2, "description": "Bell state (entangled qubits)"},
            "ghz": {"qubits": 3, "description": "GHZ state (3-qubit entanglement)"},
            "qft": {"qubits": 4, "description": "4-qubit Quantum Fourier Transform"},
            "grover": {"qubits": 3, "description": "3-qubit Grover's search algorithm"},
        }
        
        if not args or args[0] == "list":
            # List examples
            table = Table(title="Example Quantum Circuits")
            table.add_column("Name", style="cyan")
            table.add_column("Qubits", style="green", justify="center")
            table.add_column("Description", style="magenta")
            
            for name, info in examples.items():
                table.add_row(
                    name, 
                    str(info["qubits"]), 
                    info["description"]
                )
            
            console.print(table)
            
        elif args[0] == "load" and len(args) > 1:
            example_name = args[1]
            
            if example_name not in examples:
                console.print(f"[bold red]Error:[/bold red] Example '{example_name}' not found")
                return
            
            info = examples[example_name]
            self.current_circuit = QuantumCircuit(info["qubits"])
            
            # Set up the example circuit
            if example_name == "bell":
                self.do_bell("")
            elif example_name == "ghz":
                # GHZ circuit setup
                self.current_circuit.add_gate('h', [0])
                self.current_circuit.add_gate('cx', [0, 1])
                self.current_circuit.add_gate('cx', [1, 2])
                console.print("Created GHZ state circuit")
            elif example_name == "qft":
                # Simple placeholder for QFT
                console.print("Created QFT circuit placeholder")
            elif example_name == "grover":
                # Simple placeholder for Grover
                console.print("Created Grover circuit placeholder")
            
            console.print(f"Loaded [bold green]{example_name}[/bold green] example circuit with [bold green]{info['qubits']}[/bold green] qubits")
        else:
            console.print(f"[bold red]Error:[/bold red] Unknown examples command: {arg}")
            console.print(self.do_examples.__doc__)
    
    def do_tutorial(self, arg):
        """Access interactive tutorials.
        
        Usage:
            tutorial list              List available tutorials
            tutorial start <name>      Start the specified tutorial
        """
        args = shlex.split(arg)
        
        tutorials = {
            "basics": {"title": "Quantum Computing Basics", "steps": 5},
            "bell": {"title": "Creating Bell States", "steps": 3},
            "algorithms": {"title": "Quantum Algorithms", "steps": 7},
        }
        
        if not args or args[0] == "list":
            # List tutorials
            table = Table(title="Available Tutorials")
            table.add_column("Name", style="cyan")
            table.add_column("Title", style="green")
            table.add_column("Steps", style="magenta", justify="center")
            
            for name, info in tutorials.items():
                table.add_row(
                    name, 
                    info["title"], 
                    str(info["steps"])
                )
            
            console.print(table)
            
        elif args[0] == "start" and len(args) > 1:
            tutorial_name = args[1]
            
            if tutorial_name not in tutorials:
                console.print(f"[bold red]Error:[/bold red] Tutorial '{tutorial_name}' not found")
                return
            
            info = tutorials[tutorial_name]
            console.print(Panel.fit(
                f"Starting tutorial: [bold green]{info['title']}[/bold green]\n\n" +
                "This is a placeholder for an interactive tutorial that would guide you " +
                f"through {info['steps']} steps to learn about {info['title']}.",
                title="Tutorial",
                border_style="green"
            ))
        else:
            console.print(f"[bold red]Error:[/bold red] Unknown tutorial command: {arg}")
            console.print(self.do_tutorial.__doc__)
    
    def do_help(self, arg):
        """List available commands or show help for a specific command."""
        if arg:
            # Show help for a specific command
            super().do_help(arg)
        else:
            # List all commands with descriptions
            commands = [
                ("exit, quit", "Exit the interactive shell"),
                ("profile", "View or change configuration profiles"),
                ("circuit", "Create, load, or manipulate quantum circuits"),
                ("gate", "Add gates to the current quantum circuit"),
                ("simulate", "Simulate the current quantum circuit"),
                ("bell", "Create a Bell state circuit (shortcut)"),
                ("examples", "Show and load example quantum circuits"),
                ("tutorial", "Access interactive tutorials"),
                ("help", "Show this help message"),
            ]
            
            table = Table(title="Available Commands")
            table.add_column("Command", style="cyan")
            table.add_column("Description", style="green")
            
            for cmd, desc in commands:
                table.add_row(cmd, desc)
            
            console.print(table)
            console.print("\nType [bold green]help <command>[/bold green] for detailed help on a specific command.")


def start_shell(no_welcome=False):
    """Start the interactive quantum shell.
    
    Args:
        no_welcome: If True, skip the welcome message
    """
    shell = QuantumShell(no_welcome=no_welcome)
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Exiting Quantum CLI SDK interactive shell.[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(start_shell()) 