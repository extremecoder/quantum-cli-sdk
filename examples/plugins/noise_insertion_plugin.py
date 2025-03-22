"""
Example transpiler plugin for the Quantum CLI SDK.

This plugin adds a transpiler pass that inserts random noise into quantum circuits.
"""

import random
from typing import Dict, Any, Optional

from quantum_cli_sdk.transpiler import TranspilerPass, TranspilerPassType
from quantum_cli_sdk.plugin_system import register_transpiler_plugin

class NoiseInsertionPass(TranspilerPass):
    """Transpiler pass that inserts random noise gates into a quantum circuit."""
    
    def __init__(self, noise_probability=0.05, seed=None):
        """Initialize the noise insertion pass.
        
        Args:
            noise_probability: Probability of inserting a noise gate after each gate
            seed: Random seed for reproducibility
        """
        self.noise_probability = noise_probability
        self.seed = seed
        self.rng = random.Random(seed)
    
    @property
    def pass_type(self) -> TranspilerPassType:
        """Get the type of the pass."""
        return TranspilerPassType.ERROR_MITIGATION
    
    @property
    def description(self) -> str:
        """Get the description of the pass."""
        return f"Inserts random noise gates into the circuit with probability {self.noise_probability}"
    
    def run(self, circuit: Any, options: Optional[Dict[str, Any]] = None) -> Any:
        """Run the transpiler pass on a circuit.
        
        Args:
            circuit: The quantum circuit to transform
            options: Optional parameters for the pass
            
        Returns:
            Transformed quantum circuit
        """
        # Override probability if specified in options
        if options and 'noise_probability' in options:
            noise_probability = float(options['noise_probability'])
        else:
            noise_probability = self.noise_probability
        
        # This is a placeholder implementation
        # In a real plugin, you would need to handle the specific circuit representation
        # (e.g., Qiskit, Cirq, etc.) and insert appropriate noise gates
        print(f"Inserting random noise into circuit with probability {noise_probability}")
        print(f"Original circuit operations: {getattr(circuit, 'op_count', 'unknown')}")
        
        # For now, we'll just return the original circuit
        # In a real implementation, you would modify the circuit
        return circuit


# Register the plugin when this module is imported
def register():
    """Register the plugin with the CLI."""
    register_transpiler_plugin(NoiseInsertionPass)

# Call register function automatically
register() 