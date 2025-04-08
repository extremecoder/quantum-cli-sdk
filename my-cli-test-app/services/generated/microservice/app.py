# Generated Quantum Microservice
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import json
import logging
import os
import uuid
from datetime import datetime
import asyncio
import time
import sys
from collections import Counter
import cirq
from cirq.contrib.qasm_import import circuit_from_qasm

# --- Service Configuration ---
DEFAULT_CIRCUIT_FILENAME = "default_circuit.qasm"
CIRCUITS_DIR = "circuits"
RESULTS_DIR = "results"
SERVICE_TITLE = "shors_factoring_15_compatible_mitigated_zne"
SERVICE_DESCRIPTION = "Quantum microservice for shors_factoring_15_compatible_mitigated_zne circuit"
SERVICE_VERSION = "0.1.0"

# --- Logging Setup ---
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler_stdout = logging.StreamHandler(sys.stdout)
log_handler_stdout.setFormatter(log_formatter)
# Optional file handler (consider volume mapping in Docker)
# log_handler_file = logging.FileHandler("microservice.log")
# log_handler_file.setFormatter(log_formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Default level
logger.addHandler(log_handler_stdout)
# logger.addHandler(log_handler_file)

import sys # Add import
logger.info(f"Initial sys.path: {sys.path}") # Log sys.path

# --- Backend Availability & SDK Import Handling ---
QISKIT_AVAILABLE = False
qiskit = None
QuantumCircuit = None
qasm2_loads = None
QASM2ParseError = None
AerSimulator = None
SDK_BACKENDS_AVAILABLE = True # Assume True initially, set False on critical import error

try:
    # Try importing Qiskit
    import qiskit
    from qiskit import QuantumCircuit
    from qiskit.qasm2 import loads as qasm2_loads, QASM2ParseError
    try:
        # Correct import for Qiskit 1.0+
        from qiskit_aer import AerSimulator
        QISKIT_AVAILABLE = True
    except ImportError:
        logger.warning("qiskit installed, but qiskit-aer not found or failed to import. Qiskit backend unavailable.")
except ImportError:
    logger.debug("Qiskit not available.")
    pass

CIRQ_AVAILABLE = False
cirq = None
# Rely on cirq.contrib.qasm_import instead
try:
    import cirq
    CIRQ_AVAILABLE = True
except ImportError:
    logger.debug("Cirq not available.")
    pass

BRAKET_AVAILABLE = False
braket = None
BraketCircuit = None
LocalSimulator = None
try:
    import braket
    from braket.circuits import Circuit as BraketCircuit # Alias to avoid name clash
    from braket.devices import LocalSimulator
    BRAKET_AVAILABLE = True
except ImportError:
    logger.debug("Braket not available.")
    pass

# --- FastAPI App Initialization ---
app = FastAPI(
    title=SERVICE_TITLE,
    description=SERVICE_DESCRIPTION,
    version=SERVICE_VERSION
)

# --- Pydantic Models ---
class CircuitRequest(BaseModel):
    circuit: Optional[str] = None
    shots: int = 1000
    parameters: Dict[str, float] = {}

class JobStatus(BaseModel):
    job_id: str
    status: str = Field(description="Job status: QUEUED, RUNNING, COMPLETED, FAILED")
    created_at: str
    simulator: str
    shots: int

class ResultsResponse(BaseModel):
    job_id: str
    status: str
    counts: Optional[Dict[str, int]] = Field(None, description="Measurement counts as {bitstring: count}")
    execution_time_sec: Optional[float] = Field(None, description="Approximate execution time in seconds.")
    error: Optional[str] = Field(None, description="Error message if the job failed.")

class CircuitResponse(BaseModel):
    results: Dict[str, int]
    job_id: str
    metadata: Dict[str, Any] = {}

# --- In-Memory Job Store ---
# NOTE: This is simple and volatile. For production, use a persistent store (DB, Redis, etc.)
jobs: Dict[str, dict] = {}

# --- Directory Setup ---
os.makedirs(CIRCUITS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# --- Default Circuit Path ---
default_circuit_path = os.path.join(CIRCUITS_DIR, DEFAULT_CIRCUIT_FILENAME)

# --- Helper Functions ---
def load_circuit_qasm(qasm_str: Optional[str] = None) -> cirq.Circuit:
    """
    Load a quantum circuit from QASM string or the default file
    
    Args:
        qasm_str: Optional QASM string. If None, loads from default file
        
    Returns:
        A Cirq circuit object
    """
    try:
        if qasm_str:
            logger.info("Loading circuit from provided QASM string")
            return circuit_from_qasm(qasm_str)
        else:
            logger.info(f"Loading default circuit from {default_circuit_path}")
            with open(default_circuit_path, 'r') as f:
                return circuit_from_qasm(f.read())
    except Exception as e:
        logger.error(f"Error loading circuit: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to load circuit: {str(e)}")

def run_simulation(circuit: cirq.Circuit, shots: int = 1000) -> Dict[str, int]:
    """
    Run a simulation on the provided circuit
    
    Args:
        circuit: The Cirq circuit to simulate
        shots: Number of simulation shots
        
    Returns:
        Dictionary of measurement results
    """
    try:
        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions=shots)
        
        # Convert results to a simple counts dictionary
        counts = {}
        for key in result.measurements.keys():
            # Convert numpy arrays to regular Python ints
            bits = result.measurements[key].flatten().tolist()
            bitstring = ''.join(str(int(b)) for b in bits)
            
            if bitstring in counts:
                counts[bitstring] += 1
            else:
                counts[bitstring] = 1
                
        return counts
    except Exception as e:
        logger.error(f"Simulation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

# --- API Endpoints ---
@app.post("/run", response_model=CircuitResponse)
def run_circuit(request: CircuitRequest):
    """
    Run a quantum circuit and return the results
    
    The circuit can be provided as QASM in the request,
    or the default circuit will be used if not provided.
    """
    try:
        # Load the circuit (either from request or default)
        circuit = load_circuit_qasm(request.circuit)
        
        # Run the simulation
        results = run_simulation(circuit, request.shots)
        
        # Create a unique job ID (this is just a placeholder)
        job_id = "job-" + os.urandom(8).hex()
        
        # Log the job completion
        logger.info(f"Completed job {job_id} with {len(results)} results")
        
        # Return the response
        return CircuitResponse(
            results=results,
            job_id=job_id,
            metadata={
                "shots": request.shots,
                "circuit_type": "user-provided" if request.circuit else "default",
                "parameters": request.parameters
            }
        )
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get the status of a specific job."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Return relevant fields for status
    return JobStatus(
        job_id=job["job_id"],
        status=job["status"],
        created_at=job["created_at"],
        simulator=job["simulator"],
        shots=job["shots"]
    )

@app.get("/results/{job_id}", response_model=ResultsResponse)
async def get_job_results(job_id: str):
    """Get the results of a specific job."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] == "QUEUED" or job["status"] == "RUNNING":
        raise HTTPException(status_code=400, detail=f"Job status is {job['status']}. Results not yet available.")

    # Construct response
    response_data = {
        "job_id": job["job_id"],
        "status": job["status"],
        "counts": None,
        "execution_time_sec": None,
        "error": job.get("error")
    }

    # Extract results if job completed successfully
    job_results = job.get("results")
    if job["status"] == "COMPLETED" and job_results and isinstance(job_results, dict):
        response_data["counts"] = job_results.get("counts")
        response_data["execution_time_sec"] = job_results.get("execution_time_sec")
        # Potentially add backend_metadata if desired in the response

    return ResultsResponse(**response_data)

# --- Main execution block (for running app.py directly) ---
if __name__ == "__main__":
    service_port = int(os.environ.get("PORT", 8000)) # Use direct value here
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level_str, logging.INFO))
    logger.info("Starting Quantum Microservice '%s' v%s directly on port %d", SERVICE_TITLE, SERVICE_VERSION, service_port)
    # Use uvicorn for running the FastAPI app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=service_port, log_level=log_level_str.lower())
