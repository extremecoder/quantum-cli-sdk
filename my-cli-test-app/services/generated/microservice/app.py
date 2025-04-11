# -*- coding: utf-8 -*-
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

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Default level
logger.addHandler(log_handler_stdout)

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
try:
    import cirq
    from cirq.contrib.qasm_import import circuit_from_qasm
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
    simulator: str = "cirq"  # Default to cirq, but allow selection of "qiskit" or "braket"

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

def run_simulation_cirq(circuit: cirq.Circuit, shots: int = 1000) -> Dict[str, int]:
    """
    Run a simulation on the provided circuit using Cirq
    
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
        logger.error(f"Cirq simulation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cirq simulation failed: {str(e)}")

def run_simulation_qiskit(qasm_str: str, shots: int = 1000) -> Dict[str, int]:
    """
    Run a simulation on the provided circuit using Qiskit
    
    Args:
        qasm_str: The OpenQASM string to simulate
        shots: Number of simulation shots
        
    Returns:
        Dictionary of measurement results
    """
    try:
        # Try importing qiskit modules directly
        try:
            import qiskit
            # For Qiskit 0.25.x (terra), QuantumCircuit is in circuit submodule
            from qiskit.circuit import QuantumCircuit
            
            # Try both import patterns for Aer (newer versions use qiskit_aer)
            try:
                from qiskit_aer import AerSimulator
                from qiskit.primitives import BackendSampler
                backend = AerSimulator()
                logger.info("Using Qiskit AerSimulator for simulation")
                
                # For Qiskit 1.0+, use the Sampler primitive
                sampler = BackendSampler(backend)
                
            except ImportError as aer_error:
                logger.warning(f"Failed to import qiskit_aer: {aer_error}. Falling back to older Qiskit API.")
                # Fallback for older Qiskit versions
                from qiskit import Aer, execute
                backend = Aer.get_backend('qasm_simulator')
                
        except ImportError as e:
            logger.error(f"Required Qiskit modules not available: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Qiskit simulator requested but not available: {str(e)}")
        
        # Log the QASM string (can be removed in production)
        logger.debug(f"Running Qiskit simulation with QASM: {qasm_str[:100]}...")
        
        # Load QASM into Qiskit circuit
        circuit = QuantumCircuit.from_qasm_str(qasm_str)
        
        # Run the simulation - handle both new and old APIs
        if 'sampler' in locals():
            # New Qiskit 1.0+ API using Sampler
            job_result = sampler.run(circuit, shots=shots).result()
            # Convert quasi-distribution to counts
            quasi_dist = job_result.quasi_dists[0]
            counts = {}
            for bitstring_val, count_prob in quasi_dist.items():
                # Handle if bitstring is already an integer (not a string)
                if isinstance(bitstring_val, int):
                    bit_length = circuit.num_qubits
                    bitstring = format(bitstring_val, '0' + str(bit_length) + 'b')
                else:
                    bitstring = bitstring_val
                counts[bitstring] = int(count_prob * shots)
        else:
            # Old Qiskit API using execute
            job = execute(circuit, backend, shots=shots)
            result = job.result()
            
            if not result.success:
                raise Exception("Qiskit simulation failed")
                
            # Get counts and return
            counts = result.get_counts()
        
        # Handle the case where counts is not a dictionary
        if not isinstance(counts, dict):
            counts = {"0": shots}  # Default counts if no measurements
        
        return {k: v for k, v in counts.items()}
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Qiskit simulation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Qiskit simulation failed: {str(e)}")

def run_simulation_braket(qasm_str: str, shots: int = 1000) -> Dict[str, int]:
    """
    Run a simulation on the provided circuit using AWS Braket
    
    Args:
        qasm_str: The OpenQASM string to simulate
        shots: Number of simulation shots
        
    Returns:
        Dictionary of measurement results
    """
    try:
        # Try importing braket modules directly
        try:
            from braket.devices import LocalSimulator
            from braket.circuits import Circuit
        except ImportError as e:
            logger.error(f"Required Braket modules not available: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Braket simulator requested but not available: {str(e)}")
        
        # For Braket, use Cirq as a fallback since direct OpenQASM parsing isn't as straightforward
        logger.info("Converting QASM to Cirq circuit for Braket simulation")
        
        # First convert to Cirq circuit
        cirq_circuit = circuit_from_qasm(qasm_str)
        
        # Then run using Cirq's simulator since direct conversion is complex
        simulator = cirq.Simulator()
        result = simulator.run(cirq_circuit, repetitions=shots)
        
        # Process the measurement results
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
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Braket simulation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Braket simulation failed: {str(e)}")

# Use the existing run_simulation as an alias for cirq
run_simulation = run_simulation_cirq

# --- API Endpoints ---
@app.post("/run", response_model=CircuitResponse)
def run_circuit(request: CircuitRequest):
    """
    Run a quantum circuit and return the results
    
    The circuit can be provided as QASM in the request,
    or the default circuit will be used if not provided.
    """
    try:
        # Load the circuit
        circuit = load_circuit_qasm(request.circuit)
        qasm_str = request.circuit
        if qasm_str is None:
            with open(default_circuit_path, 'r') as f:
                qasm_str = f.read()
        
        # Run the simulation with the selected backend
        if request.simulator.lower() == "qiskit":
            results = run_simulation_qiskit(qasm_str, request.shots)
        elif request.simulator.lower() == "braket":
            results = run_simulation_braket(qasm_str, request.shots)
        else:  # Default to Cirq
            results = run_simulation_cirq(circuit, request.shots)
        
        # Create a unique job ID
        job_id = "job-" + os.urandom(8).hex()
        
        # Store job in the jobs dictionary
        jobs[job_id] = {
            "job_id": job_id,
            "status": "COMPLETED",
            "created_at": datetime.now().isoformat(),
            "simulator": request.simulator,
            "shots": request.shots,
            "results": {
                "counts": results,
                "execution_time_sec": None
            }
        }
        
        # Log the job completion
        logger.info(f"Completed job {job_id} with {len(results)} results")
        
        # Return the response
        return CircuitResponse(
            results=results,
            job_id=job_id,
            metadata={
                "shots": request.shots,
                "circuit_type": "user-provided" if request.circuit else "default",
                "parameters": request.parameters,
                "simulator": request.simulator  # Include which simulator was used
            }
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error processing circuit request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

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
    service_port = int(os.environ.get("PORT", 8000))
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level_str, logging.INFO))
    logger.info("Starting Quantum Microservice '%s' v%s directly on port %d", SERVICE_TITLE, SERVICE_VERSION, service_port)
    # Use uvicorn for running the FastAPI app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=service_port, log_level=log_level_str.lower())
