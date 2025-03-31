"""
Visualization utilities for quantum circuits.
"""

def visualize_circuit(circuit):
    """
    Visualize a quantum circuit.
    
    Args:
        circuit: The quantum circuit to visualize
        
    Returns:
        None, prints visualization to console
    """
    # In a real implementation, this would create a visual representation
    # using matplotlib, qiskit.visualization, etc.
    print(f"\nVisualizing circuit: {circuit['name']}")
    print(f"Number of qubits: {circuit['qubits']}")
    print("Circuit structure:")
    
    # Create a simple ASCII art representation
    for i in range(circuit['qubits']):
        line = f"q{i}: |0⟩ "
        line += "-" * 10
        print(line)
        
    print("\nGates:")
    for gate in circuit['gates']:
        target_qubits = gate['qubits']
        if 'params' in gate:
            params_str = ", ".join([f"{k}={v}" for k, v in gate['params'].items()])
            print(f"  {gate['name']} on qubits {target_qubits} with params: {params_str}")
        else:
            print(f"  {gate['name']} on qubits {target_qubits}")
    
    print("\nNote: In a real project, this would generate a proper circuit diagram.")


def plot_results(results, figsize=(10, 6)):
    """
    Plot the results of a quantum circuit execution.
    
    Args:
        results: Dictionary containing the results
        figsize: Figure size (default: (10, 6))
        
    Returns:
        None, displays the plot
    """
    # In a real implementation, this would create a matplotlib or plotly visualization
    print(f"\nPlotting measurement results:")
    
    if 'counts' in results:
        counts = results['counts']
        # Sort by state value
        sorted_counts = dict(sorted(counts.items()))
        
        # Print a simple ASCII bar chart
        max_count = max(counts.values())
        scale = 40.0 / max_count if max_count > 0 else 1
        
        print("\nMeasurement outcomes:")
        print("-" * 50)
        for state, count in sorted_counts.items():
            bar_length = int(count * scale)
            bar = '#' * bar_length
            percentage = (count / sum(counts.values())) * 100
            print(f"{state}: {bar} {count} ({percentage:.1f}%)")
        print("-" * 50)
        
        if 'most_probable' in results:
            print(f"\nMost probable outcome: {results['most_probable']}")
    else:
        print("No count data found in results")
        
    print("\nNote: In a real project, this would generate a proper histogram.") 