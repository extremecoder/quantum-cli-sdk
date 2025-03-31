"""
Run quantum applications.
"""

import os
import sys
import logging
import json
import subprocess
import time
import importlib.util
import zipfile
import tempfile
import shutil
from pathlib import Path

from ..config import get_config
from ..app_runner import AppRunner
from ..output_formatter import format_output
from ..utils import load_config

# Set up logger
logger = logging.getLogger(__name__)

def is_package(app_path):
    """
    Check if the app path is a package.
    
    Args:
        app_path (str): Path to application
        
    Returns:
        bool: True if app_path is a package
    """
    return app_path.endswith('.zip') or app_path.endswith('.whl')

def extract_package(package_path, output_dir):
    """
    Extract a package to a directory.
    
    Args:
        package_path (str): Path to package
        output_dir (str): Output directory
        
    Returns:
        str: Path to extracted package, or None if extraction fails
    """
    try:
        logger.info(f"Extracting package {package_path} to {output_dir}")
        
        if package_path.endswith('.zip'):
            with zipfile.ZipFile(package_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
                
            # Try to find manifest
            manifest_path = os.path.join(output_dir, 'quantum_manifest.json')
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                    
                # Get entrypoint
                entrypoint = manifest.get('entrypoint')
                if entrypoint and os.path.exists(os.path.join(output_dir, entrypoint)):
                    return os.path.join(output_dir, entrypoint)
            
            # If no manifest or entrypoint, try to find a main.py or app.py
            for root, _, files in os.walk(output_dir):
                for file in files:
                    if file in ['main.py', 'app.py']:
                        return os.path.join(root, file)
                        
            # If we still haven't found an entrypoint, use the first .py file
            for root, _, files in os.walk(output_dir):
                for file in files:
                    if file.endswith('.py'):
                        return os.path.join(root, file)
                        
        elif package_path.endswith('.whl'):
            # For wheel packages, use pip to install
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--target", output_dir, package_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Try to find manifest in installed package
            for root, _, files in os.walk(output_dir):
                if 'quantum_manifest.json' in files:
                    manifest_path = os.path.join(root, 'quantum_manifest.json')
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                        
                    # Get entrypoint
                    entrypoint = manifest.get('entrypoint')
                    if entrypoint:
                        entrypoint_path = os.path.join(output_dir, entrypoint)
                        if os.path.exists(entrypoint_path):
                            return entrypoint_path
            
            # If no manifest or entrypoint, try to find a main.py or app.py
            for root, _, files in os.walk(output_dir):
                for file in files:
                    if file in ['main.py', 'app.py']:
                        return os.path.join(root, file)
                        
            # If we still haven't found an entrypoint, use the first .py file
            for root, _, files in os.walk(output_dir):
                for file in files:
                    if file.endswith('.py'):
                        return os.path.join(root, file)
        
        logger.error("Could not find entrypoint in package")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting package: {e}")
        return None

def install_dependencies(app_dir):
    """
    Install dependencies for the application.
    
    Args:
        app_dir (str): Application directory
        
    Returns:
        bool: True if installation was successful
    """
    try:
        # Check for requirements.txt
        requirements_path = os.path.join(app_dir, 'requirements.txt')
        if os.path.exists(requirements_path):
            logger.info("Installing dependencies from requirements.txt")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", requirements_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info("Dependencies installed successfully")
            return True
            
        logger.warning("No requirements.txt found. Skipping dependency installation.")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing dependencies: {e.stderr.decode()}")
        return False
    except Exception as e:
        logger.error(f"Error installing dependencies: {e}")
        return False

def run_python_app(app_path, args=None):
    """
    Run a Python application.
    
    Args:
        app_path (str): Path to Python script
        args (list, optional): Command line arguments
        
    Returns:
        bool: True if run was successful
    """
    try:
        logger.info(f"Running Python application: {app_path}")
        
        cmd = [sys.executable, app_path]
        if args:
            cmd.extend(args)
            
        process = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info("Application executed successfully")
        logger.info(f"Output: {process.stdout}")
        
        if process.stderr:
            logger.warning(f"Stderr: {process.stderr}")
            
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running application: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error running application: {e}")
        return False

def run_qasm_app(app_path, simulator="qiskit", shots=1024, args=None):
    """
    Run a QASM application using a simulator.
    
    Args:
        app_path (str): Path to QASM file
        simulator (str, optional): Simulator to use (qiskit, cirq, braket)
        shots (int, optional): Number of shots to run
        args (list, optional): Additional arguments
        
    Returns:
        bool: True if run was successful
    """
    try:
        logger.info(f"Running QASM application: {app_path} with {simulator} simulator")
        
        # Create a temporary Python file to run the circuit
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            temp_py = f.name
            
            f.write(f"""
import sys
import json
import time

# Load specified simulator
if "{simulator}" == "qiskit":
    try:
        from qiskit import QuantumCircuit, Aer, execute
    except ImportError:
        print("Error: Qiskit not installed. Run 'pip install qiskit'.")
        sys.exit(1)
elif "{simulator}" == "cirq":
    try:
        import cirq
        import cirq_qasm
    except ImportError:
        print("Error: Cirq not installed. Run 'pip install cirq cirq-qasm'.")
        sys.exit(1)
elif "{simulator}" == "braket":
    try:
        from braket.circuits import Circuit
        from braket.devices import LocalSimulator
    except ImportError:
        print("Error: Braket SDK not installed. Run 'pip install amazon-braket-sdk'.")
        sys.exit(1)
else:
    print(f"Error: Unsupported simulator '{simulator}'")
    sys.exit(1)

# Run the circuit
try:
    start_time = time.time()
    
    if "{simulator}" == "qiskit":
        # Load circuit from file
        with open("{app_path}", "r") as f:
            qasm = f.read()
        
        # Create circuit from QASM
        circuit = QuantumCircuit.from_qasm_str(qasm)
        
        # Add measurements if not present
        if not circuit.clbits:
            circuit.measure_all()
        
        # Run simulation
        simulator = Aer.get_backend('qasm_simulator')
        job = execute(circuit, simulator, shots={shots})
        result = job.result()
        
        # Process results
        counts = result.get_counts()
        
        # Print results
        print(json.dumps(counts, indent=2))
        
    elif "{simulator}" == "cirq":
        # Load circuit from file
        with open("{app_path}", "r") as f:
            qasm = f.read()
        
        # Create circuit from QASM
        parser = cirq_qasm.QasmParser()
        circuit = parser.parse(qasm)
        
        # Run simulation
        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions={shots})
        
        # Process results
        measurements = result.measurements
        if not measurements:
            # For circuits without explicit measurements
            counts = {{"0": {shots}}}
        else:
            # Convert measurements to counts
            key = list(measurements.keys())[0]
            bitstrings = []
            for bits in measurements[key]:
                bitstring = ''.join(str(int(b)) for b in bits)
                bitstrings.append(bitstring)
            
            # Count unique bitstrings
            counts = {{}}
            for bitstring in bitstrings:
                if bitstring not in counts:
                    counts[bitstring] = 0
                counts[bitstring] += 1
        
        # Print results
        print(json.dumps(counts, indent=2))
        
    elif "{simulator}" == "braket":
        # Load circuit from file
        with open("{app_path}", "r") as f:
            qasm = f.read()
        
        # Create circuit from QASM
        circuit = Circuit.from_openqasm(qasm)
        
        # Run simulation
        device = LocalSimulator()
        task = device.run(circuit, shots={shots})
        result = task.result()
        
        # Process results
        counts = result.measurement_counts
        
        # Print results
        print(json.dumps(counts, indent=2))
    
    end_time = time.time()
    print(f"Execution time: {{end_time - start_time:.2f}} seconds")
    
except Exception as e:
    print(f"Error executing circuit: {{e}}")
    sys.exit(1)
""".encode())
        
        # Run the temporary Python file
        cmd = [sys.executable, temp_py]
        if args:
            cmd.extend(args)
            
        process = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info("QASM application executed successfully")
        logger.info(f"Output: {process.stdout}")
        
        if process.stderr:
            logger.warning(f"Stderr: {process.stderr}")
            
        # Delete the temporary file
        try:
            os.unlink(temp_py)
        except:
            pass
            
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running QASM application: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error running QASM application: {e}")
        return False

def run_app(app_path, args=None, simulator=None, shots=1024):
    """
    Run a quantum application.
    
    Args:
        app_path (str): Path to application
        args (list, optional): Command line arguments
        simulator (str, optional): Simulator to use for QASM files
        shots (int, optional): Number of shots for QASM files
        
    Returns:
        bool: True if run was successful
    """
    # Set up logger
    setup_logger()
    
    logger.info(f"Running quantum application: {app_path}")
    
    # Check if app path exists
    if not os.path.exists(app_path):
        logger.error(f"Application path does not exist: {app_path}")
        return False
    
    # Check if app is a package
    if is_package(app_path):
        # Create temporary directory for extraction
        temp_dir = tempfile.mkdtemp()
        try:
            # Extract package
            app_file = extract_package(app_path, temp_dir)
            if not app_file:
                return False
                
            # Install dependencies
            if not install_dependencies(temp_dir):
                return False
                
            # Determine file type and run
            if app_file.endswith('.py'):
                return run_python_app(app_file, args)
            elif app_file.endswith('.qasm'):
                sim = simulator or "qiskit"
                return run_qasm_app(app_file, sim, shots, args)
            else:
                logger.error(f"Unsupported file type: {app_file}")
                return False
                
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
    else:
        # Regular file
        if app_path.endswith('.py'):
            # Install dependencies from app directory
            app_dir = os.path.dirname(app_path)
            if not install_dependencies(app_dir):
                return False
                
            return run_python_app(app_path, args)
        elif app_path.endswith('.qasm'):
            sim = simulator or "qiskit"
            return run_qasm_app(app_path, sim, shots, args)
        else:
            logger.error(f"Unsupported file type: {app_path}")
            return False

if __name__ == "__main__":
    # This allows the module to be run directly for testing
    if len(sys.argv) < 2:
        print("Usage: run_app.py <app_path> [--simulator <simulator>] [--shots <shots>] [-- <app_args>]")
        sys.exit(1)
    
    # Parse arguments
    app_path = sys.argv[1]
    simulator = None
    shots = 1024
    args = []
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--simulator" and i+1 < len(sys.argv):
            simulator = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == "--shots" and i+1 < len(sys.argv):
            shots = int(sys.argv[i+1])
            i += 2
        elif sys.argv[i] == "--":
            args = sys.argv[i+1:]
            break
        else:
            i += 1
    
    # Run app
    success = run_app(app_path, args, simulator, shots)
    sys.exit(0 if success else 1)
