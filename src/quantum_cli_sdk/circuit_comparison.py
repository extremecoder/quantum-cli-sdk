#!/usr/bin/env python3
"""
Quantum Circuit Comparison module for analyzing differences between quantum circuits.

This module provides functionality to:
- Compare gate counts between two circuits
- Analyze circuit depth differences
- Assess theoretical performance metrics
- Generate detailed comparison reports
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class CircuitMetrics:
    """Represents the metrics of a quantum circuit."""
    
    def __init__(self, 
                 circuit_name: str,
                 qubit_count: int,
                 depth: int,
                 gate_counts: Dict[str, int],
                 connectivity_density: float = 0.0,
                 t_count: int = 0,
                 t_depth: int = 0,
                 measurement_count: int = 0):
        """
        Initialize circuit metrics.
        
        Args:
            circuit_name: Name of the circuit
            qubit_count: Number of qubits
            depth: Circuit depth
            gate_counts: Dictionary mapping gate types to counts
            connectivity_density: Measure of qubit connectivity (0-1)
            t_count: Number of T gates (relevant for fault tolerance)
            t_depth: T-depth of the circuit
            measurement_count: Number of measurement operations
        """
        self.circuit_name = circuit_name
        self.qubit_count = qubit_count
        self.depth = depth
        self.gate_counts = gate_counts
        self.connectivity_density = connectivity_density
        self.t_count = t_count
        self.t_depth = t_depth
        self.measurement_count = measurement_count
        
        # Calculate total gate count
        self.total_gate_count = sum(gate_counts.values())
        
        # Calculate 2-qubit gate percentage
        two_qubit_gates = sum([count for gate, count in gate_counts.items() 
                              if gate in ['cx', 'cz', 'swap', 'cp']])
        self.two_qubit_percentage = (two_qubit_gates / self.total_gate_count * 100) if self.total_gate_count > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary representation."""
        return {
            "circuit_name": self.circuit_name,
            "qubit_count": self.qubit_count,
            "depth": self.depth,
            "gate_counts": self.gate_counts,
            "total_gate_count": self.total_gate_count,
            "two_qubit_percentage": self.two_qubit_percentage,
            "connectivity_density": self.connectivity_density,
            "t_count": self.t_count,
            "t_depth": self.t_depth,
            "measurement_count": self.measurement_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CircuitMetrics':
        """Create CircuitMetrics from a dictionary."""
        return cls(
            circuit_name=data["circuit_name"],
            qubit_count=data["qubit_count"],
            depth=data["depth"],
            gate_counts=data["gate_counts"],
            connectivity_density=data.get("connectivity_density", 0.0),
            t_count=data.get("t_count", 0),
            t_depth=data.get("t_depth", 0),
            measurement_count=data.get("measurement_count", 0)
        )
    
    def __str__(self) -> str:
        """String representation of circuit metrics."""
        return (f"Circuit: {self.circuit_name}\n"
                f"Qubits: {self.qubit_count}\n"
                f"Depth: {self.depth}\n"
                f"Total gates: {self.total_gate_count}\n"
                f"2-qubit gate %: {self.two_qubit_percentage:.1f}%\n"
                f"T count: {self.t_count}\n"
                f"T depth: {self.t_depth}")


class CircuitComparator:
    """Compares two quantum circuits and analyzes their differences."""
    
    def __init__(self, metrics1: CircuitMetrics, metrics2: CircuitMetrics):
        """
        Initialize the comparator with two circuit metrics.
        
        Args:
            metrics1: Metrics of the first circuit
            metrics2: Metrics of the second circuit
        """
        self.metrics1 = metrics1
        self.metrics2 = metrics2
    
    def compare_gate_counts(self) -> Dict[str, Any]:
        """
        Compare gate counts between the two circuits.
        
        Returns:
            Dictionary with gate count comparison results
        """
        all_gates = set(list(self.metrics1.gate_counts.keys()) + list(self.metrics2.gate_counts.keys()))
        
        comparison = {}
        for gate in all_gates:
            count1 = self.metrics1.gate_counts.get(gate, 0)
            count2 = self.metrics2.gate_counts.get(gate, 0)
            diff = count2 - count1
            pct_change = ((count2 / count1) - 1) * 100 if count1 > 0 else float('inf')
            
            comparison[gate] = {
                "circuit1": count1,
                "circuit2": count2,
                "difference": diff,
                "percentage_change": pct_change if pct_change != float('inf') else None
            }
            
        return comparison
    
    def compare_resource_usage(self) -> Dict[str, Any]:
        """
        Compare overall resource usage between the two circuits.
        
        Returns:
            Dictionary with resource usage comparison results
        """
        return {
            "qubit_count": {
                "circuit1": self.metrics1.qubit_count,
                "circuit2": self.metrics2.qubit_count,
                "difference": self.metrics2.qubit_count - self.metrics1.qubit_count,
                "percentage_change": ((self.metrics2.qubit_count / self.metrics1.qubit_count) - 1) * 100 if self.metrics1.qubit_count > 0 else None
            },
            "depth": {
                "circuit1": self.metrics1.depth,
                "circuit2": self.metrics2.depth,
                "difference": self.metrics2.depth - self.metrics1.depth,
                "percentage_change": ((self.metrics2.depth / self.metrics1.depth) - 1) * 100 if self.metrics1.depth > 0 else None
            },
            "total_gate_count": {
                "circuit1": self.metrics1.total_gate_count,
                "circuit2": self.metrics2.total_gate_count,
                "difference": self.metrics2.total_gate_count - self.metrics1.total_gate_count,
                "percentage_change": ((self.metrics2.total_gate_count / self.metrics1.total_gate_count) - 1) * 100 if self.metrics1.total_gate_count > 0 else None
            },
            "two_qubit_percentage": {
                "circuit1": self.metrics1.two_qubit_percentage,
                "circuit2": self.metrics2.two_qubit_percentage,
                "difference": self.metrics2.two_qubit_percentage - self.metrics1.two_qubit_percentage
            },
            "t_count": {
                "circuit1": self.metrics1.t_count,
                "circuit2": self.metrics2.t_count,
                "difference": self.metrics2.t_count - self.metrics1.t_count,
                "percentage_change": ((self.metrics2.t_count / self.metrics1.t_count) - 1) * 100 if self.metrics1.t_count > 0 else None
            }
        }
    
    def estimate_performance_impact(self) -> Dict[str, Any]:
        """
        Estimate theoretical performance impact of the differences.
        
        Returns:
            Dictionary with performance impact estimates
        """
        # Simplified performance model
        # In a real implementation, this would use more sophisticated models
        
        # Estimate error probability
        error_scaling_factor = (
            (self.metrics2.depth / self.metrics1.depth if self.metrics1.depth > 0 else 1) *
            (self.metrics2.total_gate_count / self.metrics1.total_gate_count if self.metrics1.total_gate_count > 0 else 1) *
            (self.metrics2.two_qubit_percentage / self.metrics1.two_qubit_percentage if self.metrics1.two_qubit_percentage > 0 else 1)
        )
        
        # Estimate runtime
        runtime_scaling_factor = self.metrics2.depth / self.metrics1.depth if self.metrics1.depth > 0 else 1
        
        # Estimate memory requirements
        memory_scaling_factor = self.metrics2.qubit_count / self.metrics1.qubit_count if self.metrics1.qubit_count > 0 else 1
        
        return {
            "error_probability": {
                "relative_factor": error_scaling_factor,
                "interpretation": self._interpret_factor(error_scaling_factor, lower_is_better=True)
            },
            "runtime": {
                "relative_factor": runtime_scaling_factor,
                "interpretation": self._interpret_factor(runtime_scaling_factor, lower_is_better=True)
            },
            "memory_requirements": {
                "relative_factor": memory_scaling_factor,
                "interpretation": self._interpret_factor(memory_scaling_factor, lower_is_better=True)
            }
        }
    
    def generate_comparison_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive comparison report.
        
        Returns:
            Dictionary with complete comparison results
        """
        return {
            "circuit1": {
                "name": self.metrics1.circuit_name,
                "metrics": self.metrics1.to_dict()
            },
            "circuit2": {
                "name": self.metrics2.circuit_name,
                "metrics": self.metrics2.to_dict()
            },
            "gate_count_comparison": self.compare_gate_counts(),
            "resource_usage_comparison": self.compare_resource_usage(),
            "performance_impact": self.estimate_performance_impact(),
            "summary": self._generate_summary()
        }
    
    def _interpret_factor(self, factor: float, lower_is_better: bool = True) -> str:
        """
        Interpret a scaling factor as a qualitative assessment.
        
        Args:
            factor: Scaling factor
            lower_is_better: Whether lower values are better
            
        Returns:
            Qualitative interpretation
        """
        if abs(factor - 1.0) < 0.05:
            return "Negligible difference"
            
        if lower_is_better:
            if factor < 0.8:
                return "Significant improvement"
            elif factor < 0.95:
                return "Moderate improvement"
            elif factor > 1.2:
                return "Significant degradation"
            elif factor > 1.05:
                return "Moderate degradation"
        else:
            if factor > 1.2:
                return "Significant improvement"
            elif factor > 1.05:
                return "Moderate improvement"
            elif factor < 0.8:
                return "Significant degradation"
            elif factor < 0.95:
                return "Moderate degradation"
                
        return "Minimal impact"
    
    def _generate_summary(self) -> str:
        """
        Generate a textual summary of the comparison.
        
        Returns:
            Summary string
        """
        circuit1_name = self.metrics1.circuit_name
        circuit2_name = self.metrics2.circuit_name
        
        depth_diff = self.metrics2.depth - self.metrics1.depth
        depth_pct = ((self.metrics2.depth / self.metrics1.depth) - 1) * 100 if self.metrics1.depth > 0 else float('inf')
        
        gates_diff = self.metrics2.total_gate_count - self.metrics1.total_gate_count
        gates_pct = ((self.metrics2.total_gate_count / self.metrics1.total_gate_count) - 1) * 100 if self.metrics1.total_gate_count > 0 else float('inf')
        
        qubit_diff = self.metrics2.qubit_count - self.metrics1.qubit_count
        
        summary = f"Comparison of {circuit1_name} vs {circuit2_name}:\n"
        
        if depth_diff < 0:
            summary += f"- Depth reduced by {abs(depth_diff)} ({abs(depth_pct):.1f}%)\n"
        else:
            summary += f"- Depth increased by {depth_diff} ({depth_pct:.1f}%)\n"
            
        if gates_diff < 0:
            summary += f"- Gate count reduced by {abs(gates_diff)} ({abs(gates_pct):.1f}%)\n"
        else:
            summary += f"- Gate count increased by {gates_diff} ({gates_pct:.1f}%)\n"
            
        if qubit_diff < 0:
            summary += f"- Qubit count reduced by {abs(qubit_diff)}\n"
        elif qubit_diff > 0:
            summary += f"- Qubit count increased by {qubit_diff}\n"
        else:
            summary += f"- Qubit count unchanged\n"
            
        return summary


def extract_metrics_from_qasm(qasm_content: str, circuit_name: str) -> CircuitMetrics:
    """
    Extract metrics from a QASM circuit.
    
    Args:
        qasm_content: QASM circuit content
        circuit_name: Name of the circuit
        
    Returns:
        CircuitMetrics object
    """
    # Parse the QASM content
    lines = qasm_content.strip().split('\n')
    
    # Extract qubit count
    qubit_count = 0
    for line in lines:
        if "qreg" in line:
            # Parse qreg q[n];
            parts = line.split('[')
            if len(parts) > 1:
                qubit_count_str = parts[1].split(']')[0]
                try:
                    qubit_count = max(qubit_count, int(qubit_count_str))
                except ValueError:
                    pass
    
    # Count gates
    gate_counts = {}
    for line in lines:
        line = line.strip()
        if line.startswith('//') or line.startswith('OPENQASM') or line.startswith('include') or not line:
            continue
            
        # Extract gate type
        parts = line.split()
        if not parts:
            continue
            
        gate_type = parts[0]
        if gate_type in ['qreg', 'creg', 'barrier', 'include']:
            continue
            
        gate_counts[gate_type] = gate_counts.get(gate_type, 0) + 1
    
    # Calculate depth (simplified - in a real implementation, this would parse the circuit structure)
    # Just estimate based on total gates and qubits
    total_gates = sum(gate_counts.values())
    estimated_depth = int(total_gates / qubit_count) if qubit_count > 0 else total_gates
    
    # Count measurements
    measurement_count = gate_counts.get('measure', 0)
    
    # Count T gates for T-count and T-depth (simplified)
    t_count = gate_counts.get('t', 0) + gate_counts.get('tdg', 0)
    t_depth = int(t_count / qubit_count) if qubit_count > 0 else t_count
    
    # Simplified connectivity density
    connectivity_density = 0.5  # Placeholder
    
    return CircuitMetrics(
        circuit_name=circuit_name,
        qubit_count=qubit_count,
        depth=estimated_depth,
        gate_counts=gate_counts,
        connectivity_density=connectivity_density,
        t_count=t_count,
        t_depth=t_depth,
        measurement_count=measurement_count
    )


def compare_circuits(circuit1_path: str, circuit2_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Compare two quantum circuits and generate a report.
    
    Args:
        circuit1_path: Path to the first circuit file
        circuit2_path: Path to the second circuit file
        output_path: Path to save the comparison report (JSON)
        
    Returns:
        Comparison report as a dictionary
    """
    try:
        # Read circuit files
        with open(circuit1_path, 'r') as f:
            circuit1_content = f.read()
            
        with open(circuit2_path, 'r') as f:
            circuit2_content = f.read()
            
        # Extract circuit names from filenames
        circuit1_name = os.path.basename(circuit1_path)
        circuit2_name = os.path.basename(circuit2_path)
        
        # Extract metrics
        metrics1 = extract_metrics_from_qasm(circuit1_content, circuit1_name)
        metrics2 = extract_metrics_from_qasm(circuit2_content, circuit2_name)
        
        # Compare circuits
        comparator = CircuitComparator(metrics1, metrics2)
        report = comparator.generate_comparison_report()
        
        # Save report if output path is provided
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Comparison report saved to {output_path}")
            
        return report
        
    except Exception as e:
        logger.error(f"Failed to compare circuits: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }


def print_comparison_summary(report: Dict[str, Any]) -> None:
    """
    Print a human-readable summary of the comparison report.
    
    Args:
        report: Comparison report dictionary
    """
    if "error" in report:
        print(f"Error: {report['error']}")
        return
        
    circuit1 = report["circuit1"]["name"]
    circuit2 = report["circuit2"]["name"]
    
    print(f"\nComparison: {circuit1} vs {circuit2}")
    print("=" * 50)
    
    # Basic metrics
    metrics1 = report["circuit1"]["metrics"]
    metrics2 = report["circuit2"]["metrics"]
    
    print("\nBasic Metrics:")
    print(f"{'Metric':<20} {'Circuit 1':<12} {'Circuit 2':<12} {'Difference':<12} {'% Change':<10}")
    print("-" * 70)
    
    resource_usage = report["resource_usage_comparison"]
    
    for metric in ["qubit_count", "depth", "total_gate_count"]:
        values = resource_usage[metric]
        val1 = values["circuit1"]
        val2 = values["circuit2"]
        diff = values["difference"]
        pct = values.get("percentage_change")
        
        pct_str = f"{pct:.1f}%" if pct is not None else "N/A"
        print(f"{metric.replace('_', ' ').title():<20} {val1:<12} {val2:<12} {diff:<12} {pct_str:<10}")
    
    # Gate counts
    print("\nGate Count Comparison:")
    print(f"{'Gate Type':<15} {'Circuit 1':<12} {'Circuit 2':<12} {'Difference':<12}")
    print("-" * 60)
    
    gate_comparison = report["gate_count_comparison"]
    for gate, values in sorted(gate_comparison.items()):
        val1 = values["circuit1"]
        val2 = values["circuit2"]
        diff = values["difference"]
        print(f"{gate:<15} {val1:<12} {val2:<12} {diff:<12}")
    
    # Performance impact
    print("\nEstimated Performance Impact:")
    performance = report["performance_impact"]
    
    for metric, values in performance.items():
        factor = values["relative_factor"]
        interp = values["interpretation"]
        print(f"{metric.replace('_', ' ').title()}: {factor:.2f}x ({interp})")
    
    # Summary
    if "summary" in report:
        print("\nSummary:")
        print(report["summary"]) 