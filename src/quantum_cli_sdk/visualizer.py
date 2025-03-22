"""
Visualization module for quantum circuits and results.

This module provides functions for visualizing quantum circuits and simulation results
in various formats, including text, ASCII, and graphical representations.
"""

import json
import math
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# For terminal output
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax

# For image export (when matplotlib is available)
try:
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# For web-based visualizations (when plotly is available)
try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# Set up logging
logger = logging.getLogger(__name__)

# Console for rich output
console = Console()

class CircuitVisualizer:
    """Visualizer for quantum circuits."""
    
    @staticmethod
    def text_diagram(circuit, style="unicode") -> str:
        """Generate a text diagram of the circuit.
        
        Args:
            circuit: The quantum circuit to visualize
            style: Style to use ("unicode", "ascii", or "qasm")
            
        Returns:
            Text representation of the circuit
        """
        if not hasattr(circuit, "gates") or not hasattr(circuit, "num_qubits"):
            return "Invalid circuit object"
        
        # Get circuit data
        num_qubits = circuit.num_qubits
        gates = circuit.gates if hasattr(circuit, "gates") else []
        
        # Characters for drawing
        if style == "unicode":
            h_line = "─"
            v_line = "│"
            cross = "┼"
            corner_bl = "└"
            corner_tl = "┌"
            corner_br = "┘"
            corner_tr = "┐"
            control = "●"
            target_l = "╰"
            target_r = "╯"
            target_x = "X"
        else:  # ASCII style
            h_line = "-"
            v_line = "|"
            cross = "+"
            corner_bl = "+"
            corner_tl = "+"
            corner_br = "+"
            corner_tr = "+"
            control = "o"
            target_l = "+"
            target_r = "+"
            target_x = "X"
        
        # Initialize circuit grid
        grid = [[" " for _ in range(50)] for _ in range(num_qubits * 2 - 1)]
        
        # Add qubit lines
        for i in range(num_qubits):
            row = i * 2
            grid[row] = [h_line] * 50
            # Add qubit label
            label = f"q{i}: "
            for j, char in enumerate(label):
                grid[row][j] = char
        
        # Position for the first gate
        gate_pos = len("q0: ")
        
        # Add gates to the grid
        for gate in gates:
            gate_type = gate["type"]
            qubits = gate["qubits"]
            
            if len(qubits) == 1:
                # Single-qubit gate
                q = qubits[0]
                row = q * 2
                
                # Draw gate box
                gate_label = gate_type.upper()
                box_width = max(3, len(gate_label) + 2)
                
                grid[row][gate_pos] = corner_tl
                grid[row][gate_pos + box_width - 1] = corner_tr
                
                for i in range(1, box_width - 1):
                    grid[row][gate_pos + i] = h_line
                
                # Add gate label
                label_pos = gate_pos + (box_width - len(gate_label)) // 2
                for i, char in enumerate(gate_label):
                    grid[row][label_pos + i] = char
                
                gate_pos += box_width
                
            elif len(qubits) == 2 and gate_type in ["cx", "cz"]:
                # Two-qubit gate
                control, target = qubits
                
                # Ensure control is above target for visual clarity
                if control > target:
                    # Don't swap, just draw differently
                    top, bottom = target, control
                    control_on_bottom = True
                else:
                    top, bottom = control, target
                    control_on_bottom = False
                
                # Draw vertical line connecting qubits
                for i in range(top * 2 + 1, bottom * 2):
                    grid[i][gate_pos] = v_line
                
                # Draw control point
                if control_on_bottom:
                    grid[bottom * 2][gate_pos] = control
                else:
                    grid[top * 2][gate_pos] = control
                
                # Draw target point
                if gate_type == "cx":
                    if control_on_bottom:
                        grid[top * 2][gate_pos - 1] = target_l
                        grid[top * 2][gate_pos + 1] = target_r
                        grid[top * 2][gate_pos] = target_x
                    else:
                        grid[bottom * 2][gate_pos - 1] = target_l
                        grid[bottom * 2][gate_pos + 1] = target_r
                        grid[bottom * 2][gate_pos] = target_x
                else:  # cz
                    if control_on_bottom:
                        grid[top * 2][gate_pos] = control
                    else:
                        grid[bottom * 2][gate_pos] = control
                
                gate_pos += 3
        
        # Convert grid to string
        result = []
        for row in grid:
            result.append("".join(row[:gate_pos + 2]))
        
        return "\n".join(result)
    
    @staticmethod
    def print_circuit(circuit, style="unicode"):
        """Print a circuit diagram to the console.
        
        Args:
            circuit: The quantum circuit to visualize
            style: Style to use ("unicode", "ascii", or "qasm")
        """
        diagram = CircuitVisualizer.text_diagram(circuit, style)
        
        if style == "qasm":
            # For QASM style, use syntax highlighting
            syntax = Syntax(diagram, "qasm", theme="monokai", line_numbers=False)
            console.print(syntax)
        else:
            # For other styles, use a panel
            panel = Panel.fit(
                diagram,
                title="Quantum Circuit",
                border_style="cyan"
            )
            console.print(panel)
    
    @staticmethod
    def save_circuit_image(circuit, filename, figsize=(10, 6), dpi=100):
        """Save a circuit diagram as an image.
        
        Args:
            circuit: The quantum circuit to visualize
            filename: The output filename
            figsize: Figure size (width, height) in inches
            dpi: Resolution in dots per inch
            
        Returns:
            True if successful, False otherwise
        """
        if not HAS_MATPLOTLIB:
            logger.warning("Matplotlib is required for saving circuit images. Please install it with: pip install matplotlib")
            return False
        
        try:
            diagram = CircuitVisualizer.text_diagram(circuit, style="unicode")
            
            # Create figure and axis
            fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
            
            # Hide axes
            ax.axis('off')
            
            # Add text
            ax.text(0.1, 0.5, diagram, fontfamily='monospace', fontsize=12, verticalalignment='center')
            
            # Save figure
            fig.savefig(filename, bbox_inches='tight', pad_inches=0.5)
            plt.close(fig)
            
            logger.info(f"Circuit diagram saved to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving circuit image: {e}")
            return False


class ResultsVisualizer:
    """Visualizer for quantum simulation results."""
    
    @staticmethod
    def print_histogram(results, title="Simulation Results"):
        """Print a histogram of measurement outcomes to the console.
        
        Args:
            results: The simulation results dictionary
            title: Title for the histogram
        """
        if not isinstance(results, dict) or "counts" not in results:
            console.print("[bold red]Invalid results format. Expected dictionary with 'counts' key.[/bold red]")
            return
        
        counts = results["counts"]
        shots = results.get("shots", sum(counts.values()))
        
        # Create table
        table = Table(title=f"{title} ({shots} shots)")
        table.add_column("Outcome", style="cyan")
        table.add_column("Count", style="green", justify="right")
        table.add_column("Probability", style="magenta", justify="right")
        table.add_column("Histogram", style="blue")
        
        # Maximum bar length (characters)
        max_bar_length = 40
        max_count = max(counts.values()) if counts else 0
        
        # Sort outcomes
        sorted_outcomes = sorted(counts.keys())
        
        for outcome in sorted_outcomes:
            count = counts[outcome]
            probability = count / shots
            
            # Calculate bar length
            if max_count > 0:
                bar_length = int((count / max_count) * max_bar_length)
            else:
                bar_length = 0
            
            # Create bar
            bar = "█" * bar_length
            
            table.add_row(
                outcome,
                str(count),
                f"{probability:.4f}",
                bar
            )
        
        console.print(table)
    
    @staticmethod
    def save_histogram(results, filename, figsize=(10, 6), title="Simulation Results", color="skyblue"):
        """Save a histogram of measurement outcomes as an image.
        
        Args:
            results: The simulation results dictionary
            filename: The output filename
            figsize: Figure size (width, height) in inches
            title: Title for the histogram
            color: Bar color
            
        Returns:
            True if successful, False otherwise
        """
        if not HAS_MATPLOTLIB:
            logger.warning("Matplotlib is required for saving histograms. Please install it with: pip install matplotlib")
            return False
        
        if not isinstance(results, dict) or "counts" not in results:
            logger.error("Invalid results format. Expected dictionary with 'counts' key.")
            return False
        
        try:
            counts = results["counts"]
            shots = results.get("shots", sum(counts.values()))
            
            # Sort outcomes
            sorted_outcomes = sorted(counts.keys())
            values = [counts[outcome] for outcome in sorted_outcomes]
            probabilities = [v / shots for v in values]
            
            # Create figure and axis
            fig, ax = plt.subplots(figsize=figsize)
            
            # Create histogram
            x = np.arange(len(sorted_outcomes))
            ax.bar(x, probabilities, color=color, alpha=0.7)
            
            # Add labels and title
            ax.set_xlabel('Outcomes')
            ax.set_ylabel('Probability')
            ax.set_title(f"{title} ({shots} shots)")
            
            # Set ticks
            ax.set_xticks(x)
            ax.set_xticklabels(sorted_outcomes, rotation=45 if len(sorted_outcomes) > 6 else 0)
            
            # Add grid
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Add values on top of bars
            for i, v in enumerate(probabilities):
                ax.text(i, v + 0.01, f"{v:.3f}", ha='center')
            
            # Adjust layout
            fig.tight_layout()
            
            # Save figure
            fig.savefig(filename)
            plt.close(fig)
            
            logger.info(f"Histogram saved to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving histogram: {e}")
            return False
    
    @staticmethod
    def save_interactive_histogram(results, filename, title="Simulation Results"):
        """Save an interactive histogram of measurement outcomes.
        
        Args:
            results: The simulation results dictionary
            filename: The output filename (HTML)
            title: Title for the histogram
            
        Returns:
            True if successful, False otherwise
        """
        if not HAS_PLOTLY:
            logger.warning("Plotly is required for interactive histograms. Please install it with: pip install plotly")
            return False
        
        if not isinstance(results, dict) or "counts" not in results:
            logger.error("Invalid results format. Expected dictionary with 'counts' key.")
            return False
        
        try:
            counts = results["counts"]
            shots = results.get("shots", sum(counts.values()))
            
            # Sort outcomes
            sorted_outcomes = sorted(counts.keys())
            values = [counts[outcome] for outcome in sorted_outcomes]
            probabilities = [v / shots for v in values]
            
            # Create figure
            fig = go.Figure()
            
            # Add bars
            fig.add_trace(go.Bar(
                x=sorted_outcomes,
                y=probabilities,
                text=[f"{p:.4f}" for p in probabilities],
                textposition='auto',
                marker_color='royalblue',
                opacity=0.75
            ))
            
            # Update layout
            fig.update_layout(
                title=f"{title} ({shots} shots)",
                xaxis_title="Outcomes",
                yaxis_title="Probability",
                yaxis=dict(range=[0, 1.05 * max(probabilities)]),
                template="plotly_white",
                margin=dict(l=50, r=50, b=100, t=100, pad=4)
            )
            
            # Save to HTML
            fig.write_html(filename)
            logger.info(f"Interactive histogram saved to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving interactive histogram: {e}")
            return False
    
    @staticmethod
    def save_bloch_sphere(results, filename, figsize=(8, 8)):
        """Save a Bloch sphere representation of a single qubit state.
        
        Args:
            results: The simulation results dictionary (for a single qubit)
            filename: The output filename
            figsize: Figure size (width, height) in inches
            
        Returns:
            True if successful, False otherwise
        """
        if not HAS_MATPLOTLIB:
            logger.warning("Matplotlib is required for Bloch sphere visualization. Please install it with: pip install matplotlib")
            return False
        
        if not isinstance(results, dict) or "counts" not in results:
            logger.error("Invalid results format. Expected dictionary with 'counts' key.")
            return False
        
        # Verify this is a single-qubit state
        counts = results["counts"]
        outcomes = list(counts.keys())
        
        if not all(len(outcome) == 1 for outcome in outcomes):
            logger.error("Bloch sphere visualization requires a single-qubit state.")
            return False
        
        try:
            shots = results.get("shots", sum(counts.values()))
            
            # Calculate probabilities
            p0 = counts.get("0", 0) / shots
            p1 = counts.get("1", 0) / shots
            
            # Create figure and 3D axis
            fig = plt.figure(figsize=figsize)
            ax = fig.add_subplot(111, projection='3d')
            
            # Draw the Bloch sphere
            u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
            x = np.cos(u) * np.sin(v)
            y = np.sin(u) * np.sin(v)
            z = np.cos(v)
            ax.plot_wireframe(x, y, z, color="gray", alpha=0.2)
            
            # Draw axes
            ax.quiver(0, 0, 0, 1.5, 0, 0, color='r', arrow_length_ratio=0.1, linewidth=2)
            ax.quiver(0, 0, 0, 0, 1.5, 0, color='g', arrow_length_ratio=0.1, linewidth=2)
            ax.quiver(0, 0, 0, 0, 0, 1.5, color='b', arrow_length_ratio=0.1, linewidth=2)
            
            # Add axes labels
            ax.text(1.7, 0, 0, "$x$", color='r')
            ax.text(0, 1.7, 0, "$y$", color='g')
            ax.text(0, 0, 1.7, "$|0\\rangle$", color='b')
            ax.text(0, 0, -1.7, "$|1\\rangle$", color='b')
            
            # Calculate state vector (assuming a pure state)
            theta = 2 * np.arccos(np.sqrt(p0))
            phi = 0  # We can't determine phi from just probabilities
            
            # Draw the state vector
            x_state = np.sin(theta) * np.cos(phi)
            y_state = np.sin(theta) * np.sin(phi)
            z_state = np.cos(theta)
            
            ax.quiver(0, 0, 0, x_state, y_state, z_state, color='purple', 
                     arrow_length_ratio=0.1, linewidth=3)
            
            # Customize view
            ax.set_box_aspect([1, 1, 1])
            ax.set_axis_off()
            
            # Add title
            plt.title(f"Bloch Sphere Representation\n|0⟩: {p0:.4f}, |1⟩: {p1:.4f}")
            
            # Save figure
            plt.savefig(filename)
            plt.close(fig)
            
            logger.info(f"Bloch sphere visualization saved to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving Bloch sphere visualization: {e}")
            return False


def print_circuit(circuit, style="unicode"):
    """Print a circuit diagram to the console.
    
    Args:
        circuit: The quantum circuit to visualize
        style: Style to use ("unicode", "ascii", or "qasm")
    """
    CircuitVisualizer.print_circuit(circuit, style)


def print_results(results, title="Simulation Results"):
    """Print simulation results to the console.
    
    Args:
        results: The simulation results dictionary
        title: Title for the results
    """
    ResultsVisualizer.print_histogram(results, title)


def save_circuit_image(circuit, filename, figsize=(10, 6), dpi=100):
    """Save a circuit diagram as an image.
    
    Args:
        circuit: The quantum circuit to visualize
        filename: The output filename
        figsize: Figure size (width, height) in inches
        dpi: Resolution in dots per inch
        
    Returns:
        True if successful, False otherwise
    """
    return CircuitVisualizer.save_circuit_image(circuit, filename, figsize, dpi)


def save_results_image(results, filename, figsize=(10, 6), title="Simulation Results", interactive=False):
    """Save simulation results as an image.
    
    Args:
        results: The simulation results dictionary
        filename: The output filename
        figsize: Figure size (width, height) in inches
        title: Title for the results
        interactive: Whether to create an interactive HTML visualization
        
    Returns:
        True if successful, False otherwise
    """
    if interactive:
        return ResultsVisualizer.save_interactive_histogram(results, filename, title)
    else:
        return ResultsVisualizer.save_histogram(results, filename, figsize, title)


def visualize_circuit_command(args):
    """Command-line handler for circuit visualization.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Load circuit
        from .quantum_circuit import QuantumCircuit
        
        if args.source:
            try:
                with open(args.source, 'r') as f:
                    circuit_data = json.load(f)
                
                # Create circuit from data
                circuit = QuantumCircuit(circuit_data.get("num_qubits", 2))
                
                # Add gates
                for gate in circuit_data.get("gates", []):
                    circuit.add_gate(gate["type"], gate["qubits"])
                
                logger.info(f"Loaded circuit with {circuit.num_qubits} qubits from {args.source}")
                
            except FileNotFoundError:
                logger.error(f"Circuit file not found: {args.source}")
                return 1
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON format in circuit file: {args.source}")
                return 1
            except Exception as e:
                logger.error(f"Error loading circuit: {e}")
                return 1
        else:
            # Create a sample circuit
            circuit = QuantumCircuit(2)
            circuit.add_gate("h", [0])
            circuit.add_gate("cx", [0, 1])
            logger.info("Created sample Bell state circuit")
        
        # Print circuit to console
        if not args.no_display:
            print_circuit(circuit, style=args.style)
        
        # Save circuit image
        if args.output:
            success = save_circuit_image(circuit, args.output, 
                                        figsize=(args.width, args.height),
                                        dpi=args.dpi)
            if success:
                console.print(f"Circuit diagram saved to [bold blue]{args.output}[/bold blue]")
            else:
                logger.error(f"Failed to save circuit image to {args.output}")
                return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Error visualizing circuit: {e}")
        return 1


def visualize_results_command(args):
    """Command-line handler for results visualization.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Load results
        if args.source:
            try:
                with open(args.source, 'r') as f:
                    results = json.load(f)
                
                logger.info(f"Loaded results from {args.source}")
                
            except FileNotFoundError:
                logger.error(f"Results file not found: {args.source}")
                return 1
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON format in results file: {args.source}")
                return 1
            except Exception as e:
                logger.error(f"Error loading results: {e}")
                return 1
        else:
            # Create sample results
            results = {
                "counts": {"00": 500, "11": 500, "01": 12, "10": 12},
                "shots": 1024,
                "execution_time": 0.5
            }
            logger.info("Created sample Bell state results")
        
        # Print results to console
        if not args.no_display:
            print_results(results, title=args.title)
        
        # Save results image
        if args.output:
            success = save_results_image(
                results, 
                args.output,
                figsize=(args.width, args.height),
                title=args.title,
                interactive=args.interactive
            )
            
            if success:
                console.print(f"Results visualization saved to [bold blue]{args.output}[/bold blue]")
            else:
                logger.error(f"Failed to save results visualization to {args.output}")
                return 1
        
        # Save Bloch sphere visualization (single-qubit only)
        if args.bloch and len(next(iter(results["counts"].keys()))) == 1:
            bloch_output = args.bloch_output or str(Path(args.output).with_name(f"{Path(args.output).stem}_bloch{Path(args.output).suffix}"))
            success = ResultsVisualizer.save_bloch_sphere(
                results,
                bloch_output,
                figsize=(args.width, args.height)
            )
            
            if success:
                console.print(f"Bloch sphere visualization saved to [bold blue]{bloch_output}[/bold blue]")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error visualizing results: {e}")
        return 1 