"""
Generate microservice wrapper for quantum circuits.
"""

import os
import sys
import logging
import json
import re
import shutil
from pathlib import Path
import requests
import subprocess
from string import Template

from ..config import get_config
from ..microservice_generator import MicroserviceGenerator
from ..output_formatter import format_output
from ..utils import load_config, run_docker_command

# Set up logger
logger = logging.getLogger(__name__)

# Template for Docker file
DOCKERFILE_TEMPLATE = """FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
"""

# Template for requirements.txt
REQUIREMENTS_TEMPLATE = """fastapi>=0.68.0
uvicorn>=0.15.0
pydantic>=1.8.2
qiskit>=0.34.2
cirq>=1.0.0
amazon-braket-sdk>=1.9.0
matplotlib>=3.4.3
numpy>=1.20.0
"""

# Template for main app.py file
APP_TEMPLATE = """from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import logging
import os
import uuid
from datetime import datetime
import asyncio

# Import quantum backends
try:
    import qiskit
    from qiskit import QuantumCircuit, Aer, execute
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False

try:
    import cirq
    import cirq_qasm
    CIRQ_AVAILABLE = True
except ImportError:
    CIRQ_AVAILABLE = False

try:
    import braket
    from braket.circuits import Circuit
    from braket.devices import LocalSimulator
    BRAKET_AVAILABLE = True
except ImportError:
    BRAKET_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("microservice.log")
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="${app_name}",
    description="${app_description}",
    version="${app_version}"
)

# Models
class CircuitRequest(BaseModel):
    circuit: str
    parameters: Optional[Dict[str, Any]] = None
    shots: int = 1024
    simulator: str = "qiskit"
    
class JobStatus(BaseModel):
    job_id: str
    status: str
    created_at: str
    simulator: str
    shots: int
    
class ResultsResponse(BaseModel):
    job_id: str
    status: str
    counts: Optional[Dict[str, int]] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None

# In-memory job store (in production, use a database)
jobs = {}

# Circuit store
os.makedirs("circuits", exist_ok=True)
os.makedirs("results", exist_ok=True)

# Circuit implementations
${circuit_implementations}

# Routes
@app.get("/")
async def root():
    return {
        "message": "Quantum Microservice API",
        "name": "${app_name}",
        "version": "${app_version}"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "simulators": {
            "qiskit": QISKIT_AVAILABLE,
            "cirq": CIRQ_AVAILABLE,
            "braket": BRAKET_AVAILABLE
        },
        "uptime": "unknown"  # In a real service, track uptime
    }

@app.post("/run", response_model=JobStatus)
async def run_circuit(request: CircuitRequest, background_tasks: BackgroundTasks):
    # Validate simulator
    if request.simulator not in ["qiskit", "cirq", "braket"]:
        raise HTTPException(status_code=400, detail="Invalid simulator. Must be one of: qiskit, cirq, braket")
    
    # Check if simulator is available
    if request.simulator == "qiskit" and not QISKIT_AVAILABLE:
        raise HTTPException(status_code=400, detail="Qiskit simulator not available")
    elif request.simulator == "cirq" and not CIRQ_AVAILABLE:
        raise HTTPException(status_code=400, detail="Cirq simulator not available")
    elif request.simulator == "braket" and not BRAKET_AVAILABLE:
        raise HTTPException(status_code=400, detail="Braket simulator not available")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Save circuit to file
    circuit_path = f"circuits/{job_id}.qasm"
    with open(circuit_path, "w") as f:
        f.write(request.circuit)
    
    # Create job record
    job = {
        "job_id": job_id,
        "status": "QUEUED",
        "created_at": datetime.now().isoformat(),
        "circuit_path": circuit_path,
        "parameters": request.parameters,
        "shots": request.shots,
        "simulator": request.simulator
    }
    jobs[job_id] = job
    
    # Run in background
    background_tasks.add_task(execute_circuit, job_id)
    
    return JobStatus(
        job_id=job_id,
        status="QUEUED",
        created_at=job["created_at"],
        simulator=request.simulator,
        shots=request.shots
    )

@app.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        created_at=job["created_at"],
        simulator=job["simulator"],
        shots=job["shots"]
    )

@app.get("/jobs/{job_id}/results", response_model=ResultsResponse)
async def get_job_results(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] == "QUEUED" or job["status"] == "RUNNING":
        return ResultsResponse(
            job_id=job_id,
            status=job["status"]
        )
    
    result_path = f"results/{job_id}.json"
    if not os.path.exists(result_path):
        return ResultsResponse(
            job_id=job_id,
            status=job["status"],
            error="Results file not found"
        )
    
    with open(result_path, "r") as f:
        result = json.load(f)
    
    return ResultsResponse(
        job_id=job_id,
        status=job["status"],
        counts=result.get("counts"),
        execution_time=result.get("execution_time"),
        error=result.get("error")
    )

@app.get("/jobs")
async def list_jobs():
    return {
        "jobs": [
            {
                "job_id": job_id,
                "status": job["status"],
                "created_at": job["created_at"],
                "simulator": job["simulator"]
            } for job_id, job in jobs.items()
        ]
    }

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete job files
    try:
        if os.path.exists(f"circuits/{job_id}.qasm"):
            os.remove(f"circuits/{job_id}.qasm")
        if os.path.exists(f"results/{job_id}.json"):
            os.remove(f"results/{job_id}.json")
    except Exception as e:
        logger.error(f"Error deleting job files: {e}")
    
    # Remove from job store
    del jobs[job_id]
    
    return {"message": f"Job {job_id} deleted"}

# Background task for circuit execution
async def execute_circuit(job_id: str):
    if job_id not in jobs:
        logger.error(f"Job {job_id} not found")
        return
    
    job = jobs[job_id]
    job["status"] = "RUNNING"
    
    try:
        # Get circuit and parameters
        circuit_path = job["circuit_path"]
        parameters = job["parameters"] or {}
        shots = job["shots"]
        simulator = job["simulator"]
        
        if simulator == "qiskit":
            result = await execute_with_qiskit(circuit_path, parameters, shots)
        elif simulator == "cirq":
            result = await execute_with_cirq(circuit_path, parameters, shots)
        elif simulator == "braket":
            result = await execute_with_braket(circuit_path, parameters, shots)
        else:
            raise ValueError(f"Unsupported simulator: {simulator}")
        
        # Save results
        result_path = f"results/{job_id}.json"
        with open(result_path, "w") as f:
            json.dump(result, f, indent=2)
        
        job["status"] = "COMPLETED"
        logger.info(f"Job {job_id} completed")
        
    except Exception as e:
        logger.error(f"Error executing job {job_id}: {e}")
        job["status"] = "FAILED"
        
        # Save error
        result_path = f"results/{job_id}.json"
        with open(result_path, "w") as f:
            json.dump({"error": str(e)}, f, indent=2)

# Qiskit execution
async def execute_with_qiskit(circuit_path, parameters, shots):
    import time
    start_time = time.time()
    
    # Load circuit from file
    with open(circuit_path, "r") as f:
        qasm = f.read()
    
    # Replace parameters in QASM
    for param_name, param_value in parameters.items():
        qasm = qasm.replace(f"parameter {param_name}", str(param_value))
    
    # Create circuit from QASM
    circuit = QuantumCircuit.from_qasm_str(qasm)
    
    # Add measurements if not present
    if not circuit.clbits:
        circuit.measure_all()
    
    # Run simulation
    simulator = Aer.get_backend('qasm_simulator')
    job = execute(circuit, simulator, shots=shots)
    result = job.result()
    
    # Process results
    counts = result.get_counts()
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    return {
        "counts": counts,
        "execution_time": execution_time,
        "success": True
    }

# Cirq execution
async def execute_with_cirq(circuit_path, parameters, shots):
    import time
    start_time = time.time()
    
    # Load circuit from file
    with open(circuit_path, "r") as f:
        qasm = f.read()
    
    # Replace parameters in QASM
    for param_name, param_value in parameters.items():
        qasm = qasm.replace(f"parameter {param_name}", str(param_value))
    
    # Create circuit from QASM
    parser = cirq_qasm.QasmParser()
    circuit = parser.parse(qasm)
    
    # Run simulation
    simulator = cirq.Simulator()
    result = simulator.run(circuit, repetitions=shots)
    
    # Process results
    measurements = result.measurements
    if not measurements:
        # For circuits without explicit measurements
        counts = {"0": shots}
    else:
        # Convert measurements to counts
        key = list(measurements.keys())[0]
        bitstrings = []
        for bits in measurements[key]:
            bitstring = ''.join(str(int(b)) for b in bits)
            bitstrings.append(bitstring)
        
        # Count unique bitstrings
        counts = {}
        for bitstring in bitstrings:
            if bitstring not in counts:
                counts[bitstring] = 0
            counts[bitstring] += 1
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    return {
        "counts": counts,
        "execution_time": execution_time,
        "success": True
    }

# Braket execution
async def execute_with_braket(circuit_path, parameters, shots):
    import time
    start_time = time.time()
    
    # Load circuit from file
    with open(circuit_path, "r") as f:
        qasm = f.read()
    
    # Replace parameters in QASM
    for param_name, param_value in parameters.items():
        qasm = qasm.replace(f"parameter {param_name}", str(param_value))
    
    # Create circuit from QASM
    # Note: In production, use a proper QASM to Braket converter
    circuit = Circuit.from_openqasm(qasm)
    
    # Run simulation
    device = LocalSimulator()
    task = device.run(circuit, shots=shots)
    result = task.result()
    
    # Process results
    counts = result.measurement_counts
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    return {
        "counts": counts,
        "execution_time": execution_time,
        "success": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

# Template for README.md
README_TEMPLATE = """# ${app_name}

This is a microservice for running and interacting with quantum circuits.

## Features

- Run quantum circuits through a REST API
- Support for multiple simulators (Qiskit, Cirq, Braket)
- Asynchronous job execution
- Job status tracking
- Results retrieval

## API Endpoints

- `GET /`: Service information
- `GET /health`: Health check
- `POST /run`: Submit a circuit for execution
- `GET /jobs/{job_id}`: Get job status
- `GET /jobs/{job_id}/results`: Get job results
- `GET /jobs`: List all jobs
- `DELETE /jobs/{job_id}`: Delete a job

## Usage

### Running the service

```bash
# Build the Docker image
docker build -t ${app_name} .

# Run the container
docker run -p 8000:8000 ${app_name}
```

### API Examples

#### Run a circuit

```bash
curl -X POST http://localhost:8000/run \\
  -H "Content-Type: application/json" \\
  -d '{
    "circuit": "OPENQASM 2.0;\\ninclude \\"qelib1.inc\\";\\nqreg q[2];\\ncreg c[2];\\nh q[0];\\ncx q[0],q[1];\\nmeasure q -> c;",
    "shots": 1024,
    "simulator": "qiskit"
  }'
```

#### Get job status

```bash
curl http://localhost:8000/jobs/JOB_ID
```

#### Get job results

```bash
curl http://localhost:8000/jobs/JOB_ID/results
```

## Circuit Details

${circuit_documentation}
"""

# Template for circuit implementation in app.py
CIRCUIT_IMPLEMENTATION_TEMPLATE = """
# Implementation of ${circuit_name}
async def ${circuit_function_name}(parameters):
    # Create circuit
    circuit = QuantumCircuit(${num_qubits}, ${num_cbits})
    
    # Circuit implementation
    ${circuit_implementation}
    
    # Return QASM
    return circuit.qasm()
"""

def extract_circuit_info(qasm_file):
    """
    Extract information about a quantum circuit from QASM file.
    
    Args:
        qasm_file (str): Path to the QASM file
        
    Returns:
        dict: Circuit information
    """
    try:
        with open(qasm_file, 'r') as f:
            content = f.read()
            
        # Extract basic info
        info = {
            "name": os.path.splitext(os.path.basename(qasm_file))[0],
            "qasm_version": None,
            "includes": [],
            "qreg_count": 0,
            "creg_count": 0,
            "parameters": [],
            "gate_types": set(),
            "has_measurements": False
        }
        
        # Parse version
        version_match = re.search(r'OPENQASM\s+(\d+\.\d+);', content)
        if version_match:
            info["qasm_version"] = version_match.group(1)
            
        # Parse includes
        include_matches = re.findall(r'include\s+"([^"]+)";', content)
        info["includes"] = include_matches
        
        # Parse qregs
        qreg_matches = re.findall(r'qreg\s+(\w+)\[(\d+)\];', content)
        info["qreg_count"] = sum(int(size) for _, size in qreg_matches)
        
        # Parse cregs
        creg_matches = re.findall(r'creg\s+(\w+)\[(\d+)\];', content)
        info["creg_count"] = sum(int(size) for _, size in creg_matches)
        
        # Parse parameters
        param_matches = re.findall(r'parameter\s+(\w+)\s*=\s*([^;]+);', content)
        info["parameters"] = [name for name, _ in param_matches]
        
        # Detect gate types
        common_gates = ["h", "x", "y", "z", "cx", "rx", "ry", "rz", "u", "s", "t", "measure"]
        for gate in common_gates:
            pattern = r'\b' + gate + r'\s+'
            if re.search(pattern, content):
                info["gate_types"].add(gate)
                
        # Check for measurements
        if "measure" in info["gate_types"]:
            info["has_measurements"] = True
            
        return info
        
    except Exception as e:
        logger.error(f"Error extracting circuit info: {e}")
        return None

def generate_circuit_implementation(circuit_info):
    """
    Generate a python implementation for the circuit.
    
    Args:
        circuit_info (dict): Circuit information
        
    Returns:
        str: Python implementation
    """
    name = circuit_info["name"]
    function_name = f"create_{name.lower().replace('-', '_')}_circuit"
    
    # For a real implementation, we'd analyze the QASM and translate to code
    # This is a simplified version that just returns a template
    
    implementation = f"""
# Implementation of {name}
def {function_name}(parameters=None):
    \"\"\"
    Create the {name} circuit.
    
    Args:
        parameters (dict, optional): Circuit parameters
        
    Returns:
        QuantumCircuit: The circuit
    \"\"\"
    if parameters is None:
        parameters = {{}}
        
    # Create circuit with {circuit_info['qreg_count']} qubits and {circuit_info['creg_count']} classical bits
    circuit = QuantumCircuit({circuit_info['qreg_count']}, {circuit_info['creg_count']})
    
    # Here we would implement the circuit based on the QASM
    # For this template, we'll create a simple circuit
    
    # Add Hadamard gate to first qubit
    circuit.h(0)
    
    # Add controlled-X gate if we have at least 2 qubits
    if {circuit_info['qreg_count']} >= 2:
        circuit.cx(0, 1)
    
    # Add measurements if needed
    if {circuit_info['creg_count']} > 0:
        circuit.measure_all()
    
    return circuit
"""
    return implementation

def generate_circuit_documentation(circuit_info):
    """
    Generate documentation for the circuit.
    
    Args:
        circuit_info (dict): Circuit information
        
    Returns:
        str: Markdown documentation
    """
    name = circuit_info["name"]
    
    doc = f"""### {name}

This microservice implements the {name} quantum circuit.

- Number of qubits: {circuit_info['qreg_count']}
- Number of classical bits: {circuit_info['creg_count']}
- Gate types: {', '.join(circuit_info['gate_types'])}
- Has measurements: {'Yes' if circuit_info['has_measurements'] else 'No'}
"""

    if circuit_info["parameters"]:
        doc += "\nParameters:\n"
        for param in circuit_info["parameters"]:
            doc += f"- `{param}`\n"
    
    return doc

def call_llm_for_implementation(circuit_path, llm_url):
    """
    Call LLM service to generate circuit implementation.
    
    Args:
        circuit_path (str): Path to the circuit file
        llm_url (str): URL to the LLM service
        
    Returns:
        dict: Generated implementation and documentation
    """
    try:
        # Read circuit file
        with open(circuit_path, 'r') as f:
            qasm_content = f.read()
            
        # Prepare request payload
        payload = {
            "circuit_qasm": qasm_content,
            "task": "generate_microservice_implementation",
            "format": "json"
        }
        
        # Call LLM API
        logger.info(f"Calling LLM service at {llm_url}")
        response = requests.post(llm_url, json=payload, timeout=60)
        response.raise_for_status()
        
        # Process response
        result = response.json()
        
        return {
            "implementation": result.get("implementation", ""),
            "documentation": result.get("documentation", "")
        }
        
    except requests.RequestException as e:
        logger.error(f"Error calling LLM service: {e}")
        return None
    except Exception as e:
        logger.error(f"Error generating implementation with LLM: {e}")
        return None

def generate_microservice(source_file, dest_dir=None, llm_url=None):
    """
    Generate a microservice wrapper for a quantum circuit.
    
    Args:
        source_file (str): Path to the source circuit file
        dest_dir (str, optional): Destination directory for the microservice
        llm_url (str, optional): URL of LLM service for enhanced generation
        
    Returns:
        bool: True if generation was successful
    """
    logger.info(f"Starting microservice generation for {source_file}")
    
    # Ensure source file exists
    if not os.path.exists(source_file):
        logger.error(f"Source file {source_file} does not exist")
        return False
    
    # Determine file type
    file_ext = os.path.splitext(source_file)[1].lower()
    
    if file_ext != '.qasm':
        logger.error(f"Unsupported file type for microservice generation: {file_ext}")
        return False
    
    # Extract circuit information
    circuit_info = extract_circuit_info(source_file)
    if not circuit_info:
        logger.error("Failed to extract circuit information")
        return False
    
    # Determine destination directory
    if not dest_dir:
        dest_dir = os.path.join("microservice")
    
    # Create destination directory
    os.makedirs(dest_dir, exist_ok=True)
    
    # Determine app name
    app_name = f"quantum-{circuit_info['name']}-service"
    app_description = f"Quantum microservice for the {circuit_info['name']} circuit"
    app_version = "0.1.0"
    
    # Generate circuit implementation
    circuit_implementation = ""
    circuit_documentation = ""
    
    if llm_url:
        # Use LLM to generate implementation
        llm_result = call_llm_for_implementation(source_file, llm_url)
        if llm_result:
            circuit_implementation = llm_result["implementation"]
            circuit_documentation = llm_result["documentation"]
    
    # If LLM call failed or wasn't requested, use template-based generation
    if not circuit_implementation:
        circuit_implementation = generate_circuit_implementation(circuit_info)
        circuit_documentation = generate_circuit_documentation(circuit_info)
    
    # Create app.py
    app_content = Template(APP_TEMPLATE).substitute(
        app_name=app_name,
        app_description=app_description,
        app_version=app_version,
        circuit_implementations=circuit_implementation
    )
    
    with open(os.path.join(dest_dir, "app.py"), 'w') as f:
        f.write(app_content)
    
    # Create Dockerfile
    with open(os.path.join(dest_dir, "Dockerfile"), 'w') as f:
        f.write(DOCKERFILE_TEMPLATE)
    
    # Create requirements.txt
    with open(os.path.join(dest_dir, "requirements.txt"), 'w') as f:
        f.write(REQUIREMENTS_TEMPLATE)
    
    # Create README.md
    readme_content = Template(README_TEMPLATE).substitute(
        app_name=app_name,
        app_description=app_description,
        app_version=app_version,
        circuit_documentation=circuit_documentation
    )
    
    with open(os.path.join(dest_dir, "README.md"), 'w') as f:
        f.write(readme_content)
    
    # Copy the circuit file
    circuits_dir = os.path.join(dest_dir, "circuits")
    os.makedirs(circuits_dir, exist_ok=True)
    shutil.copy(source_file, os.path.join(circuits_dir, f"{circuit_info['name']}.qasm"))
    
    # Create results directory
    results_dir = os.path.join(dest_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    logger.info(f"Microservice generated in {dest_dir}")
    return True

if __name__ == "__main__":
    # This allows the module to be run directly for testing
    if len(sys.argv) < 2:
        print("Usage: microservice.py <source_file> [<dest_dir>] [--llm <llm_url>]")
        sys.exit(1)
    
    source = sys.argv[1]
    dest = None
    llm = None
    
    # Parse remaining arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--llm" and i+1 < len(sys.argv):
            llm = sys.argv[i+1]
            i += 2
        else:
            dest = sys.argv[i]
            i += 1
    
    success = generate_microservice(source, dest, llm)
    sys.exit(0 if success else 1)
