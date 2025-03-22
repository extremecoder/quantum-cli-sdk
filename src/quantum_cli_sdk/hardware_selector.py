#!/usr/bin/env python3
"""
Quantum Hardware Selector module for recommending optimal hardware for quantum circuits.

This module provides functionality to:
- Analyze circuit characteristics
- Match circuits to suitable quantum hardware
- Recommend optimal quantum processors
- Provide detailed compatibility reports
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Union

from .circuit_comparison import extract_metrics_from_qasm, CircuitMetrics

logger = logging.getLogger(__name__)

class QuantumHardware:
    """Represents a quantum hardware platform."""
    
    def __init__(self, 
                 hardware_id: str,
                 name: str,
                 provider: str,
                 qubit_count: int,
                 connectivity_type: str,
                 connectivity_density: float,
                 max_circuit_depth: int,
                 supported_gates: List[str],
                 gate_fidelities: Dict[str, float],
                 readout_error_rates: float,
                 availability: float,
                 location: str,
                 t1_time: float = 0.0,
                 t2_time: float = 0.0,
                 queue_time: float = 0.0,
                 access_model: str = "cloud",
                 cost_per_circuit: Optional[float] = None,
                 benchmarks: Optional[Dict[str, Any]] = None,
                 features: Optional[List[str]] = None,
                 notes: Optional[str] = None):
        """
        Initialize quantum hardware details.
        
        Args:
            hardware_id: Unique identifier for the hardware
            name: Name of the quantum processor
            provider: Quantum hardware provider
            qubit_count: Number of qubits
            connectivity_type: Connectivity architecture (e.g., 'full', 'grid', 'linear')
            connectivity_density: Measure of qubit connectivity (0-1)
            max_circuit_depth: Maximum supported circuit depth
            supported_gates: List of supported gate types
            gate_fidelities: Dictionary mapping gate types to fidelities
            readout_error_rates: Readout error rate
            availability: Hardware availability (0-1)
            location: Geographic location of the hardware
            t1_time: T1 relaxation time in microseconds
            t2_time: T2 coherence time in microseconds
            queue_time: Average queue time in minutes
            access_model: Access model (e.g., 'cloud', 'on-prem')
            cost_per_circuit: Cost per circuit execution
            benchmarks: Performance benchmarks
            features: Special features of the hardware
            notes: Additional notes
        """
        self.hardware_id = hardware_id
        self.name = name
        self.provider = provider
        self.qubit_count = qubit_count
        self.connectivity_type = connectivity_type
        self.connectivity_density = connectivity_density
        self.max_circuit_depth = max_circuit_depth
        self.supported_gates = supported_gates
        self.gate_fidelities = gate_fidelities
        self.readout_error_rates = readout_error_rates
        self.availability = availability
        self.location = location
        self.t1_time = t1_time
        self.t2_time = t2_time
        self.queue_time = queue_time
        self.access_model = access_model
        self.cost_per_circuit = cost_per_circuit
        self.benchmarks = benchmarks or {}
        self.features = features or []
        self.notes = notes
        
        # Calculate average gate fidelity
        self.avg_gate_fidelity = sum(gate_fidelities.values()) / len(gate_fidelities) if gate_fidelities else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "hardware_id": self.hardware_id,
            "name": self.name,
            "provider": self.provider,
            "qubit_count": self.qubit_count,
            "connectivity_type": self.connectivity_type,
            "connectivity_density": self.connectivity_density,
            "max_circuit_depth": self.max_circuit_depth,
            "supported_gates": self.supported_gates,
            "gate_fidelities": self.gate_fidelities,
            "avg_gate_fidelity": self.avg_gate_fidelity,
            "readout_error_rates": self.readout_error_rates,
            "availability": self.availability,
            "location": self.location,
            "t1_time": self.t1_time,
            "t2_time": self.t2_time,
            "queue_time": self.queue_time,
            "access_model": self.access_model,
            "cost_per_circuit": self.cost_per_circuit,
            "benchmarks": self.benchmarks,
            "features": self.features,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuantumHardware':
        """Create a QuantumHardware from a dictionary."""
        return cls(
            hardware_id=data["hardware_id"],
            name=data["name"],
            provider=data["provider"],
            qubit_count=data["qubit_count"],
            connectivity_type=data["connectivity_type"],
            connectivity_density=data["connectivity_density"],
            max_circuit_depth=data["max_circuit_depth"],
            supported_gates=data["supported_gates"],
            gate_fidelities=data["gate_fidelities"],
            readout_error_rates=data["readout_error_rates"],
            availability=data["availability"],
            location=data["location"],
            t1_time=data.get("t1_time", 0.0),
            t2_time=data.get("t2_time", 0.0),
            queue_time=data.get("queue_time", 0.0),
            access_model=data.get("access_model", "cloud"),
            cost_per_circuit=data.get("cost_per_circuit"),
            benchmarks=data.get("benchmarks", {}),
            features=data.get("features", []),
            notes=data.get("notes")
        )
    
    def __str__(self) -> str:
        """String representation of the hardware."""
        return (f"{self.name} ({self.provider}) - {self.qubit_count} qubits, "
                f"{self.avg_gate_fidelity:.4f} avg fidelity")


class HardwareSelector:
    """Selects optimal quantum hardware for a given circuit."""
    
    def __init__(self, hardware_catalog_path: Optional[str] = None):
        """
        Initialize the hardware selector.
        
        Args:
            hardware_catalog_path: Path to the hardware catalog file
        """
        self.hardware_catalog_path = hardware_catalog_path or os.path.join(
            os.path.dirname(__file__), "data", "hardware_catalog.json"
        )
        
        # Load hardware catalog
        self.hardware_catalog = self._load_hardware_catalog()
    
    def _load_hardware_catalog(self) -> Dict[str, QuantumHardware]:
        """
        Load the hardware catalog from a file.
        
        Returns:
            Dictionary mapping hardware IDs to QuantumHardware objects
        """
        catalog = {}
        
        # If the catalog file doesn't exist, use default hardware entries
        if not os.path.exists(self.hardware_catalog_path):
            logger.warning(f"Hardware catalog not found at {self.hardware_catalog_path}, using default entries")
            catalog = self._create_default_catalog()
        else:
            try:
                with open(self.hardware_catalog_path, 'r') as f:
                    data = json.load(f)
                    
                for hw_entry in data.get("hardware", []):
                    hw = QuantumHardware.from_dict(hw_entry)
                    catalog[hw.hardware_id] = hw
                    
                logger.info(f"Loaded {len(catalog)} hardware entries from catalog")
                
            except Exception as e:
                logger.error(f"Failed to load hardware catalog: {e}")
                catalog = self._create_default_catalog()
        
        return catalog
    
    def _create_default_catalog(self) -> Dict[str, QuantumHardware]:
        """
        Create a default hardware catalog with representative entries.
        
        Returns:
            Dictionary mapping hardware IDs to QuantumHardware objects
        """
        # Create sample hardware entries representing different providers
        catalog = {}
        
        # IBM Quantum processor (superconducting)
        ibm_processor = QuantumHardware(
            hardware_id="ibm-127",
            name="IBM Eagle",
            provider="IBM Quantum",
            qubit_count=127,
            connectivity_type="heavy-hex",
            connectivity_density=0.02,
            max_circuit_depth=100,
            supported_gates=["id", "x", "y", "z", "h", "s", "sdg", "t", "tdg", "rx", "ry", "rz", "cx", "cz", "ccx"],
            gate_fidelities={
                "single_qubit": 0.9995,
                "cx": 0.99,
                "measure": 0.97
            },
            readout_error_rates=0.03,
            availability=0.95,
            location="New York, USA",
            t1_time=100.0,
            t2_time=80.0,
            queue_time=30.0,
            cost_per_circuit=0.0001,
            features=["dynamic circuits", "mid-circuit measurements"]
        )
        catalog[ibm_processor.hardware_id] = ibm_processor
        
        # Google Quantum processor (superconducting)
        google_processor = QuantumHardware(
            hardware_id="google-sycamore",
            name="Sycamore",
            provider="Google Quantum AI",
            qubit_count=53,
            connectivity_type="grid",
            connectivity_density=0.15,
            max_circuit_depth=20,
            supported_gates=["id", "x", "y", "z", "h", "s", "t", "rx", "ry", "rz", "cx", "cz"],
            gate_fidelities={
                "single_qubit": 0.9995,
                "cx": 0.995,
                "measure": 0.96
            },
            readout_error_rates=0.04,
            availability=0.85,
            location="Santa Barbara, USA",
            t1_time=15.0,
            t2_time=10.0,
            queue_time=60.0,
            cost_per_circuit=None,  # Not directly available
            features=["quantum supremacy tests"]
        )
        catalog[google_processor.hardware_id] = google_processor
        
        # Rigetti processor (superconducting)
        rigetti_processor = QuantumHardware(
            hardware_id="rigetti-aspen-m-3",
            name="Aspen-M-3",
            provider="Rigetti Computing",
            qubit_count=80,
            connectivity_type="8q-octagonal",
            connectivity_density=0.04,
            max_circuit_depth=50,
            supported_gates=["id", "rx", "ry", "rz", "cz"],
            gate_fidelities={
                "single_qubit": 0.992,
                "cz": 0.93,
                "measure": 0.94
            },
            readout_error_rates=0.06,
            availability=0.9,
            location="Berkeley, USA",
            t1_time=20.0,
            t2_time=15.0,
            queue_time=15.0,
            cost_per_circuit=0.00015,
            features=["parametric compilation"]
        )
        catalog[rigetti_processor.hardware_id] = rigetti_processor
        
        # IonQ processor (trapped ion)
        ionq_processor = QuantumHardware(
            hardware_id="ionq-harmony",
            name="Harmony",
            provider="IonQ",
            qubit_count=11,
            connectivity_type="full",
            connectivity_density=1.0,
            max_circuit_depth=250,
            supported_gates=["id", "x", "y", "z", "h", "s", "t", "rx", "ry", "rz", "cx"],
            gate_fidelities={
                "single_qubit": 0.9997,
                "cx": 0.97,
                "measure": 0.975
            },
            readout_error_rates=0.025,
            availability=0.92,
            location="College Park, USA",
            t1_time=10000.0,  # Long coherence times for trapped ions
            t2_time=1000.0,
            queue_time=120.0,
            cost_per_circuit=0.0003,
            features=["all-to-all connectivity"]
        )
        catalog[ionq_processor.hardware_id] = ionq_processor
        
        # Quantinuum processor (trapped ion)
        quantinuum_processor = QuantumHardware(
            hardware_id="quantinuum-h1-2",
            name="H1-2",
            provider="Quantinuum",
            qubit_count=12,
            connectivity_type="full",
            connectivity_density=1.0,
            max_circuit_depth=300,
            supported_gates=["id", "x", "y", "z", "h", "s", "t", "rx", "ry", "rz", "cx", "cz", "ccx"],
            gate_fidelities={
                "single_qubit": 0.9998,
                "cx": 0.985,
                "measure": 0.98
            },
            readout_error_rates=0.02,
            availability=0.9,
            location="Colorado, USA",
            t1_time=5000.0,
            t2_time=2000.0,
            queue_time=180.0,
            cost_per_circuit=0.0005,
            features=["mid-circuit measurement", "qubit reuse"]
        )
        catalog[quantinuum_processor.hardware_id] = quantinuum_processor
        
        # Xanadu processor (photonic)
        xanadu_processor = QuantumHardware(
            hardware_id="xanadu-borealis",
            name="Borealis",
            provider="Xanadu",
            qubit_count=216,  # Modes for photonic
            connectivity_type="programmable",
            connectivity_density=0.1,
            max_circuit_depth=24,
            supported_gates=["squeeze", "displace", "beamsplitter", "rotation", "cubic"],
            gate_fidelities={
                "squeeze": 0.99,
                "beamsplitter": 0.99,
                "rotation": 0.995,
                "measure": 0.96
            },
            readout_error_rates=0.04,
            availability=0.85,
            location="Toronto, Canada",
            t1_time=None,  # Not applicable for photonic
            t2_time=None,
            queue_time=45.0,
            cost_per_circuit=0.0002,
            features=["gaussian boson sampling", "continuous variables"]
        )
        catalog[xanadu_processor.hardware_id] = xanadu_processor
        
        logger.info(f"Created default catalog with {len(catalog)} hardware entries")
        return catalog
    
    def analyze_circuit_requirements(self, circuit_metrics: CircuitMetrics) -> Dict[str, Any]:
        """
        Analyze the requirements of a circuit.
        
        Args:
            circuit_metrics: Metrics of the circuit
            
        Returns:
            Dictionary with circuit requirements
        """
        # Extract key requirements from circuit metrics
        requirements = {
            "min_qubits": circuit_metrics.qubit_count,
            "min_depth": circuit_metrics.depth,
            "required_gates": list(circuit_metrics.gate_counts.keys()),
            "two_qubit_gate_percentage": circuit_metrics.two_qubit_percentage,
            "t_count": circuit_metrics.t_count,
            "connectivity_requirements": "linear" if circuit_metrics.connectivity_density < 0.1 else 
                                        "grid" if circuit_metrics.connectivity_density < 0.5 else 
                                        "full"
        }
        
        # Estimate required fidelity based on circuit complexity
        total_gates = circuit_metrics.total_gate_count
        if total_gates < 10:
            requirements["estimated_required_fidelity"] = 0.9
        elif total_gates < 50:
            requirements["estimated_required_fidelity"] = 0.95
        elif total_gates < 100:
            requirements["estimated_required_fidelity"] = 0.99
        else:
            requirements["estimated_required_fidelity"] = 0.999
            
        # Estimate if the circuit needs fault tolerance
        requirements["needs_fault_tolerance"] = (
            circuit_metrics.depth > 100 or 
            total_gates > 200 or 
            circuit_metrics.t_count > 50
        )
        
        return requirements
    
    def score_hardware_for_circuit(self, 
                                  hardware: QuantumHardware, 
                                  requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score the compatibility of hardware with circuit requirements.
        
        Args:
            hardware: Quantum hardware to evaluate
            requirements: Circuit requirements
            
        Returns:
            Dictionary with compatibility scores
        """
        scores = {}
        
        # Check qubit count requirement
        qubit_score = 1.0 if hardware.qubit_count >= requirements["min_qubits"] else 0.0
        scores["qubit_count"] = qubit_score
        
        # Check circuit depth requirement
        depth_ratio = min(1.0, hardware.max_circuit_depth / max(1, requirements["min_depth"]))
        scores["circuit_depth"] = depth_ratio
        
        # Check gate support
        required_gates = set(requirements["required_gates"])
        supported_gates = set(hardware.supported_gates)
        if required_gates:
            gate_support_ratio = len(required_gates.intersection(supported_gates)) / len(required_gates)
        else:
            gate_support_ratio = 1.0
        scores["gate_support"] = gate_support_ratio
        
        # Check fidelity requirements
        fidelity_ratio = min(1.0, hardware.avg_gate_fidelity / requirements["estimated_required_fidelity"])
        scores["fidelity"] = fidelity_ratio
        
        # Check connectivity requirements
        required_connectivity = requirements["connectivity_requirements"]
        connectivity_score = 0.0
        
        if required_connectivity == "linear":
            # Any connectivity type works for linear requirements
            connectivity_score = 1.0
        elif required_connectivity == "grid":
            # Grid or full connectivity works for grid requirements
            if hardware.connectivity_type in ["grid", "heavy-hex", "full"]:
                connectivity_score = 1.0
            else:
                connectivity_score = 0.5
        elif required_connectivity == "full":
            # Only full connectivity works for full requirements
            if hardware.connectivity_type == "full":
                connectivity_score = 1.0
            else:
                # Score based on connectivity density
                connectivity_score = hardware.connectivity_density
                
        scores["connectivity"] = connectivity_score
        
        # Calculate overall score
        weights = {
            "qubit_count": 0.3,
            "circuit_depth": 0.2,
            "gate_support": 0.2,
            "fidelity": 0.2,
            "connectivity": 0.1
        }
        
        overall_score = sum(scores[key] * weights[key] for key in weights)
        scores["overall"] = overall_score
        
        # Determine if hardware is compatible
        scores["is_compatible"] = (
            qubit_score > 0 and 
            depth_ratio > 0 and 
            gate_support_ratio > 0.8 and 
            overall_score > 0.6
        )
        
        return scores
    
    def find_compatible_hardware(self, circuit_metrics: CircuitMetrics) -> List[Dict[str, Any]]:
        """
        Find hardware compatible with a given circuit.
        
        Args:
            circuit_metrics: Metrics of the circuit
            
        Returns:
            List of dictionaries with hardware info and compatibility scores
        """
        # Analyze circuit requirements
        requirements = self.analyze_circuit_requirements(circuit_metrics)
        
        # Score all hardware options
        results = []
        for hw_id, hardware in self.hardware_catalog.items():
            scores = self.score_hardware_for_circuit(hardware, requirements)
            
            if scores["is_compatible"]:
                results.append({
                    "hardware": hardware.to_dict(),
                    "scores": scores,
                    "requirements": requirements
                })
                
        # Sort by overall score (descending)
        results.sort(key=lambda x: x["scores"]["overall"], reverse=True)
        
        return results
    
    def recommend_hardware(self, circuit_path: str) -> Dict[str, Any]:
        """
        Recommend hardware for a given circuit.
        
        Args:
            circuit_path: Path to the circuit file
            
        Returns:
            Dictionary with hardware recommendations
        """
        try:
            # Read circuit file
            with open(circuit_path, 'r') as f:
                circuit_content = f.read()
                
            # Extract circuit name from filename
            circuit_name = os.path.basename(circuit_path)
            
            # Extract metrics
            metrics = extract_metrics_from_qasm(circuit_content, circuit_name)
            
            # Find compatible hardware
            results = self.find_compatible_hardware(metrics)
            
            # Create recommendation report
            if results:
                top_recommendation = results[0]
                
                report = {
                    "circuit": {
                        "name": circuit_name,
                        "metrics": metrics.to_dict()
                    },
                    "top_recommendation": {
                        "hardware": top_recommendation["hardware"],
                        "compatibility_score": top_recommendation["scores"]["overall"],
                        "strengths": self._get_hardware_strengths(top_recommendation),
                        "limitations": self._get_hardware_limitations(top_recommendation)
                    },
                    "all_recommendations": results,
                    "requirements": results[0]["requirements"]
                }
            else:
                report = {
                    "circuit": {
                        "name": circuit_name,
                        "metrics": metrics.to_dict()
                    },
                    "error": "No compatible hardware found",
                    "requirements": self.analyze_circuit_requirements(metrics)
                }
                
            return report
            
        except Exception as e:
            logger.error(f"Failed to recommend hardware: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def _get_hardware_strengths(self, result: Dict[str, Any]) -> List[str]:
        """
        Identify strengths of the hardware for the given circuit.
        
        Args:
            result: Hardware result with scores
            
        Returns:
            List of strength descriptions
        """
        strengths = []
        scores = result["scores"]
        hardware = result["hardware"]
        
        if scores["qubit_count"] == 1.0 and hardware["qubit_count"] >= result["requirements"]["min_qubits"] * 1.5:
            strengths.append(f"Ample qubit count ({hardware['qubit_count']} qubits available)")
            
        if scores["circuit_depth"] == 1.0 and hardware["max_circuit_depth"] >= result["requirements"]["min_depth"] * 2:
            strengths.append(f"High circuit depth capacity ({hardware['max_circuit_depth']} depth supported)")
            
        if scores["gate_support"] > 0.9:
            strengths.append("Excellent gate support")
            
        if hardware["avg_gate_fidelity"] > 0.998:
            strengths.append(f"Very high gate fidelity ({hardware['avg_gate_fidelity']:.4f})")
        elif hardware["avg_gate_fidelity"] > 0.99:
            strengths.append(f"Good gate fidelity ({hardware['avg_gate_fidelity']:.4f})")
            
        if scores["connectivity"] > 0.9:
            strengths.append(f"Excellent connectivity ({hardware['connectivity_type']})")
            
        if hardware["t1_time"] > 100:
            strengths.append(f"Long coherence time (T1={hardware['t1_time']} µs)")
            
        if hardware["availability"] > 0.95:
            strengths.append(f"High availability ({hardware['availability']:.0%})")
            
        # Add any special features that might be relevant
        if hardware["features"]:
            strengths.append(f"Special features: {', '.join(hardware['features'])}")
            
        return strengths
    
    def _get_hardware_limitations(self, result: Dict[str, Any]) -> List[str]:
        """
        Identify limitations of the hardware for the given circuit.
        
        Args:
            result: Hardware result with scores
            
        Returns:
            List of limitation descriptions
        """
        limitations = []
        scores = result["scores"]
        hardware = result["hardware"]
        requirements = result["requirements"]
        
        if hardware["qubit_count"] < requirements["min_qubits"] * 1.2:
            limitations.append(f"Limited qubit headroom ({hardware['qubit_count']} qubits available)")
            
        if hardware["max_circuit_depth"] < requirements["min_depth"] * 1.5:
            limitations.append(f"Limited circuit depth capacity ({hardware['max_circuit_depth']} max depth)")
            
        if scores["gate_support"] < 0.9:
            missing_gates = set(requirements["required_gates"]) - set(hardware["supported_gates"])
            if missing_gates:
                limitations.append(f"Missing gate support for: {', '.join(missing_gates)}")
            else:
                limitations.append("Some gate support limitations")
                
        if hardware["avg_gate_fidelity"] < 0.99:
            limitations.append(f"Moderate gate fidelity ({hardware['avg_gate_fidelity']:.4f})")
            
        if scores["connectivity"] < 0.8:
            limitations.append(f"Connectivity limitations ({hardware['connectivity_type']})")
            
        if hardware["readout_error_rates"] > 0.05:
            limitations.append(f"High readout error ({hardware['readout_error_rates']:.2%})")
            
        if hardware["queue_time"] > 60:
            limitations.append(f"Long queue times (~{hardware['queue_time']} minutes)")
            
        if hardware["availability"] < 0.9:
            limitations.append(f"Limited availability ({hardware['availability']:.0%})")
            
        return limitations


def find_hardware(circuit_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Find optimal hardware for a quantum circuit.
    
    Args:
        circuit_path: Path to the circuit file
        output_path: Path to save the recommendation report (JSON)
        
    Returns:
        Hardware recommendation report as a dictionary
    """
    try:
        selector = HardwareSelector()
        report = selector.recommend_hardware(circuit_path)
        
        # Save report if output path is provided
        if output_path and "error" not in report:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Hardware recommendation report saved to {output_path}")
            
        return report
        
    except Exception as e:
        logger.error(f"Failed to find optimal hardware: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }


def print_hardware_recommendation(report: Dict[str, Any]) -> None:
    """
    Print a human-readable hardware recommendation.
    
    Args:
        report: Hardware recommendation report
    """
    if "error" in report:
        print(f"Error: {report['error']}")
        return
        
    circuit_name = report["circuit"]["name"]
    metrics = report["circuit"]["metrics"]
    
    print(f"\nHardware Recommendation for: {circuit_name}")
    print("=" * 50)
    
    print(f"\nCircuit Details:")
    print(f"- Qubits: {metrics['qubit_count']}")
    print(f"- Depth: {metrics['depth']}")
    print(f"- Total gates: {metrics['total_gate_count']}")
    print(f"- Two-qubit gate percentage: {metrics['two_qubit_percentage']:.1f}%")
    
    if "top_recommendation" in report:
        top = report["top_recommendation"]
        hw = top["hardware"]
        
        print(f"\nTop Recommended Hardware:")
        print(f"- Name: {hw['name']} ({hw['provider']})")
        print(f"- Compatibility Score: {top['compatibility_score']:.2f} (1.0 is perfect match)")
        print(f"- Qubits: {hw['qubit_count']}")
        print(f"- Connectivity: {hw['connectivity_type']}")
        print(f"- Avg Gate Fidelity: {hw['avg_gate_fidelity']:.4f}")
        
        print(f"\nStrengths:")
        for strength in top["strengths"]:
            print(f"- {strength}")
            
        print(f"\nLimitations:")
        if top["limitations"]:
            for limitation in top["limitations"]:
                print(f"- {limitation}")
        else:
            print("- None significant")
            
        print(f"\nAlternative Options:")
        alternatives = report["all_recommendations"][1:4]  # Show up to 3 alternatives
        if alternatives:
            for i, alt in enumerate(alternatives, 1):
                hw = alt["hardware"]
                score = alt["scores"]["overall"]
                print(f"{i}. {hw['name']} ({hw['provider']}) - Score: {score:.2f}, Qubits: {hw['qubit_count']}")
        else:
            print("- No viable alternatives found")
    else:
        print("\nNo compatible hardware found for this circuit")
        print("\nCircuit requirements:")
        requirements = report["requirements"]
        print(f"- Minimum qubits: {requirements['min_qubits']}")
        print(f"- Minimum depth: {requirements['min_depth']}")
        print(f"- Required gates: {', '.join(requirements['required_gates'])}")
        print(f"- Estimated required fidelity: {requirements['estimated_required_fidelity']:.4f}")
        print(f"- Needs fault tolerance: {'Yes' if requirements['needs_fault_tolerance'] else 'No'}")
        
    if report.get("all_recommendations"):
        print(f"\nTotal compatible hardware options: {len(report['all_recommendations'])}")
    else:
        print("\nConsider modifying your circuit to reduce resource requirements") 