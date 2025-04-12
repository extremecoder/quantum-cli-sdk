"""
Commands for calculating execution costs on quantum hardware.
"""

import json
import sys
from pathlib import Path
import math
import random

# Sample pricing data (as of 2023) - in a real implementation, this would be updated regularly
PRICING = {
    "ibm": {
        "default": 0.00022,  # Cost per shot in USD
        "falcon": 0.00032,
        "eagle": 0.00045,
        "heron": 0.00022,
    },
    "aws": {
        "default": 0.00035,  # Cost per task hour (approximate conversion)
        "sv1": 0.00030,
        "dm1": 0.00035,
        "tn1": 0.00025,
        "device": 0.00099,
    },
    "google": {
        "default": 0.00040,  # Estimated cost per processor-second
        "rainbow": 0.00050,
        "weber": 0.00040,
    },
    "ionq": {
        "default": 0.00100,  # Estimated cost per shot
        "aria": 0.00120,
        "forte": 0.00150,
    },
    "rigetti": {
        "default": 0.00033,  # Estimated cost per shot
        "ankaa": 0.00033,
        "aspen": 0.00038,
    }
}

def calculate_cost(source="openqasm", platform="all", shots=1000, dest="results/cost_estimation", resource_file: str | None = None, output_format: str = "text"):
    """Calculate estimated execution costs for running a quantum circuit on various hardware.
    
    Args:
        source (str): Source file path (OpenQASM file)
        platform (str): Quantum hardware platform(s) to estimate costs for
        shots (int): Number of shots to run
        dest (str): Destination file for cost estimation results (JSON)
        resource_file (str | None, optional): Path to a resource estimation file to use instead of analyzing source. Defaults to None.
        output_format (str, optional): Format for potential console output (currently only affects saving). Defaults to "text".
    
    Returns:
        Optional[Dict[str, Any]]: Dictionary with cost estimation metrics, or None on error.
    """
    try:
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        circuit_data = None
        circuit_name = "Unknown"
        source_path = Path(source) # Define source_path early
        
        # --- Try loading resource data --- 
        resource_load_attempted = False

        # 1. Try explicit resource_file argument
        if resource_file:
            resource_load_attempted = True
            resource_path = Path(resource_file)
            if resource_path.is_file():
                try:
                    with open(resource_path, 'r') as f:
                        resource_results = json.load(f)
                    # Extract data (assuming keys from estimate_resources output)
                    circuit_data = {
                        "qubits": resource_results.get('qubit_count', 5),
                        "depth": resource_results.get('circuit_depth', 10),
                        "gates": resource_results.get('gate_counts', {'total': 20})
                    }
                    circuit_name = resource_results.get('circuit_name', resource_path.stem.replace('_resources', ''))
                    print(f"Using resource data from specified file: {resource_file}")
                except Exception as e:
                    print(f"Warning: Could not read/parse specified resource file {resource_file}: {e}. Will check default location or analyze source.", file=sys.stderr)
            else:
                 print(f"Warning: Specified resource file not found: {resource_file}. Will check default location or analyze source.", file=sys.stderr)

        # 2. If explicit file wasn't loaded, try default resource file location
        if circuit_data is None and not resource_load_attempted: # Only check default if explicit wasn't tried or failed
            if source_path.is_file(): # Need a valid source path to guess default name
                default_resource_dir = Path("results/analysis/resources")
                default_resource_filename = f"{source_path.stem}_resources.json"
                default_resource_path = default_resource_dir / default_resource_filename
                
                if default_resource_path.is_file():
                    print(f"Found potential default resource file: {default_resource_path}")
                    resource_load_attempted = True # Mark that we tried loading a resource file
                    try:
                        with open(default_resource_path, 'r') as f:
                            resource_results = json.load(f)
                        # Extract data
                        circuit_data = {
                            "qubits": resource_results.get('qubit_count', 5),
                            "depth": resource_results.get('circuit_depth', 10),
                            "gates": resource_results.get('gate_counts', {'total': 20})
                        }
                        circuit_name = resource_results.get('circuit_name', source_path.stem)
                        print(f"Using resource data from default file: {default_resource_path}")
                    except Exception as e:
                        print(f"Warning: Could not read/parse default resource file {default_resource_path}: {e}. Will analyze source file.", file=sys.stderr)
                else:
                    print(f"Default resource file not found at {default_resource_path}. Will analyze source file.")
            else:
                 # Can't guess default if source is invalid
                 pass # Will proceed to analyze source if source is valid later

        # 3. Analyze source file as fallback
        if circuit_data is None:
            if not source_path.is_file(): # Check source validity again
                 print(f"Error: Source file not found: {source}", file=sys.stderr)
                 return None
            print(f"Loading and analyzing circuit from {source}")
            circuit_data = analyze_circuit(str(source_path)) 
            circuit_name = source_path.stem # Use source stem if analyzing directly
        
        if not circuit_data:
            print("Error: Could not obtain circuit characteristics.", file=sys.stderr)
            return None

        # Calculate costs for each platform
        costs = {}
        
        # Determine which platforms to calculate for
        platforms_to_run = list(PRICING.keys()) if platform.lower() == "all" else [platform.lower()]
        
        # Calculate costs for each platform
        for plat in platforms_to_run:
            if plat in PRICING:
                costs[plat] = calculate_platform_cost(plat, circuit_data, shots)
        
        # Generate comparison data
        comparison = {}
        if len(costs) > 1:
            cheapest_platform = min(costs.items(), key=lambda x: x[1]["total_cost"])
            most_expensive_platform = max(costs.items(), key=lambda x: x[1]["total_cost"])
            comparison = {
                "cheapest": {
                    "platform": cheapest_platform[0],
                    "total_cost": cheapest_platform[1]["total_cost"],
                    "savings_vs_expensive": most_expensive_platform[1]["total_cost"] - cheapest_platform[1]["total_cost"]
                },
                "most_expensive": {
                    "platform": most_expensive_platform[0],
                    "total_cost": most_expensive_platform[1]["total_cost"]
                },
                "cost_ratio": most_expensive_platform[1]["total_cost"] / cheapest_platform[1]["total_cost"] if cheapest_platform[1]["total_cost"] > 0 else 0
            }
        
        # Create the final results
        results = {
            "circuit": {
                "name": circuit_name,
                "qubits": circuit_data["qubits"],
                "depth": circuit_data["depth"],
                "gates": circuit_data["gates"]
            },
            "execution": {
                "shots": shots
            },
            "costs": costs,
            "comparison": comparison,
            "disclaimer": "These estimates are approximate and may vary based on actual hardware availability, queue times, and pricing changes."
        }
        
        # Save results to file
        try:
            with open(dest_path, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Cost estimation results saved to {dest_path}")
        except IOError as e:
             print(f"Error saving results to {dest_path}: {e}", file=sys.stderr)
             # Continue to print summary even if save fails
        
        # Print a summary
        print("\nCost Estimation Summary:")
        print("=" * 50)
        print(f"Circuit: {results['circuit']['name']} ({results['circuit']['qubits']} qubits, depth {results['circuit']['depth']})")
        print(f"Shots: {shots}")
        print("\nEstimated costs:")
        for plat, cost_data in costs.items():
            print(f"- {plat.upper()}: ${cost_data['total_cost']:.2f}")
        if comparison:
            print(f"\nCheapest option: {comparison['cheapest']['platform'].upper()} (${comparison['cheapest']['total_cost']:.2f})")
            print(f"Most expensive option: {comparison['most_expensive']['platform'].upper()} (${comparison['most_expensive']['total_cost']:.2f})")
            if 'savings_vs_expensive' in comparison['cheapest']:
                print(f"Potential savings: ${comparison['cheapest']['savings_vs_expensive']:.2f}")
        print("=" * 50)
        
        return results
    except Exception as e:
        print(f"Error calculating execution costs: {e}", file=sys.stderr)
        return None

def analyze_circuit(source):
    """Analyze circuit characteristics (simplified placeholder implementation).
    
    Args:
        source: Source file path
    
    Returns:
        Dictionary with circuit characteristics
    """
    # In a real implementation, this would parse the OpenQASM file and analyze it
    
    # For now, return some dummy values
    # We could make this slightly more realistic by reading the file and counting qreg declarations
    try:
        with open(source, 'r') as f:
            content = f.read()
            # Very naive "analysis" - just for demonstration
            num_qubits = 5  # Default
            if "qreg" in content:
                # Try to extract qubit count - this is a very simplified approach
                for line in content.split('\n'):
                    if "qreg" in line:
                        try:
                            # Try to extract number of qubits from qreg q[n];
                            start_idx = line.find('[') + 1
                            end_idx = line.find(']')
                            if start_idx > 0 and end_idx > start_idx:
                                num_qubits = int(line[start_idx:end_idx])
                                break
                        except:
                            pass
    except:
        # If file can't be read, use defaults
        num_qubits = 5
    
    # Generate some plausible circuit characteristics based on qubit count
    return {
        "qubits": num_qubits,
        "depth": max(10, int(num_qubits * random.uniform(1.5, 4.0))),
        "gates": {
            "total": max(20, int(num_qubits * random.uniform(5, 15))),
            "single_qubit": max(10, int(num_qubits * random.uniform(3, 8))),
            "two_qubit": max(5, int(num_qubits * random.uniform(2, 7)))
        }
    }

def calculate_platform_cost(platform, circuit_data, shots):
    """Calculate the cost for a specific platform.
    
    Args:
        platform: Platform name
        circuit_data: Circuit characteristics
        shots: Number of shots
    
    Returns:
        Dictionary with cost details
    """
    platform_pricing = PRICING.get(platform, {"default": 0.0001})
    
    # Base cost calculation
    base_rate = platform_pricing["default"]
    
    # Calculate cost based on platform-specific pricing models
    if platform == "ibm":
        # IBM prices per shot
        base_cost = base_rate * shots
        # Add premium for larger circuits
        depth_factor = 1.0 + (circuit_data["depth"] / 50.0) * 0.5
        qubit_factor = 1.0 + (circuit_data["qubits"] / 10.0) * 0.8
        
        total_cost = base_cost * depth_factor * qubit_factor
        
        # Select device based on circuit size
        if circuit_data["qubits"] > 127:
            device = "eagle"
            device_rate = platform_pricing.get("eagle", base_rate)
        elif circuit_data["qubits"] > 27:
            device = "falcon"
            device_rate = platform_pricing.get("falcon", base_rate)
        else:
            device = "heron"
            device_rate = platform_pricing.get("heron", base_rate)
            
        # Recalculate with device-specific rate
        device_cost = device_rate * shots * depth_factor * qubit_factor
        
        return {
            "base_rate": base_rate,
            "device": device,
            "device_rate": device_rate,
            "shots": shots,
            "depth_factor": depth_factor,
            "qubit_factor": qubit_factor,
            "base_cost": base_cost,
            "device_cost": device_cost,
            "total_cost": device_cost
        }
        
    elif platform == "aws":
        # AWS prices per task-hour, converted to per-circuit estimate
        # Estimate task hours based on circuit complexity
        circuit_time_sec = (circuit_data["depth"] * circuit_data["qubits"] * 0.0002)
        task_hours = max(0.001, (circuit_time_sec * shots) / 3600)
        
        # Base cost using default rate
        base_cost = base_rate * task_hours
        
        # Select appropriate service based on circuit characteristics
        if circuit_data["qubits"] > 35:
            service = "device"  # Hardware
            service_rate = platform_pricing.get("device", base_rate)
        elif circuit_data["qubits"] > 25:
            service = "dm1"  # Density Matrix Simulator
            service_rate = platform_pricing.get("dm1", base_rate)
        else:
            service = "sv1"  # State Vector Simulator
            service_rate = platform_pricing.get("sv1", base_rate)
            
        # Calculate with service-specific rate
        service_cost = service_rate * task_hours
        
        return {
            "base_rate": base_rate,
            "service": service,
            "service_rate": service_rate,
            "circuit_time_sec": circuit_time_sec,
            "task_hours": task_hours,
            "shots": shots,
            "base_cost": base_cost,
            "service_cost": service_cost,
            "total_cost": service_cost
        }
        
    elif platform == "google":
        # Google prices per processor-second
        # Estimate processor seconds based on circuit
        processor_seconds = circuit_data["depth"] * 0.001 * shots
        processor_hours = processor_seconds / 3600
        
        # Base cost
        base_cost = base_rate * processor_seconds
        
        # Device selection
        if circuit_data["qubits"] > 23:
            device = "weber"
            device_rate = platform_pricing.get("weber", base_rate)
        else:
            device = "rainbow"
            device_rate = platform_pricing.get("rainbow", base_rate)
            
        # Calculate with device-specific rate
        device_cost = device_rate * processor_seconds
        
        return {
            "base_rate": base_rate,
            "device": device,
            "device_rate": device_rate,
            "processor_seconds": processor_seconds,
            "processor_hours": processor_hours,
            "shots": shots,
            "base_cost": base_cost,
            "device_cost": device_cost,
            "total_cost": device_cost
        }
        
    else:
        # Generic calculation for other platforms
        base_cost = base_rate * shots
        complexity_factor = (circuit_data["depth"] / 20.0) * (circuit_data["qubits"] / 5.0)
        total_cost = base_cost * (1.0 + complexity_factor * 0.5)
        
        return {
            "base_rate": base_rate,
            "shots": shots,
            "complexity_factor": complexity_factor,
            "base_cost": base_cost,
            "total_cost": total_cost
        } 