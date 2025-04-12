"""
IBM Quantum Hardware Runner for executing quantum circuits on IBM Quantum hardware.
"""

import os
import time
import tempfile
import json
import logging
from typing import Dict, Any, Optional
from qiskit import QuantumCircuit, transpile
from qiskit.providers.jobstatus import JobStatus

logger = logging.getLogger(__name__)

def run_on_ibm_hardware(qasm_file: str, device_id: str = None, shots: int = 1024,
                      wait_for_results: bool = True, poll_timeout_seconds: int = 3600,
                      optimization_level: int = 1, api_token: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Run a QASM file on IBM Quantum hardware.
    
    Args:
        qasm_file: Path to the QASM file
        device_id: IBM Quantum backend name
        shots: Number of shots to run
        wait_for_results: Whether to wait for results (True) or return immediately (False)
        poll_timeout_seconds: Maximum time to wait for results, in seconds
        optimization_level: Transpiler optimization level (0-3)
        api_token: IBM Quantum API token (optional)
        **kwargs: Additional arguments
        
    Returns:
        Dict[str, Any]: Dictionary containing counts and metadata
    """
    # Initialize counts and metadata early
    counts = {"error": 1} # Default error counts
    metadata = {
        'platform': 'ibm',
        'device_id': device_id or 'unknown',
        'error': 'Initialization error' # Default error message
    }
    circuit: Optional[QuantumCircuit] = None
    
    try:
        # Try to import Qiskit
        try: from qiskit import QuantumCircuit
        except ImportError:
            logger.error("Qiskit not installed. Please install qiskit to use IBM hardware.")
            metadata['error'] = "Qiskit not installed. Please install qiskit to use IBM hardware."
            return {"counts": counts, "metadata": metadata} # Return dict
        
        # Get IBM credentials - either from config or from args
        ibm_api_token = None
        
        # First check if token is provided as an argument
        if api_token:
            ibm_api_token = api_token
            logger.info("Using IBM Quantum API token provided in arguments.")
        
        # Check environment variables
        if not ibm_api_token:
            # Try multiple possible environment variable names
            for env_var in ['QISKIT_IBM_TOKEN', 'IBM_QUANTUM_TOKEN', 'IBM_API_TOKEN']:
                if env_var in os.environ and os.environ[env_var]:
                    ibm_api_token = os.environ[env_var]
                    logger.info(f"Using IBM Quantum API token from environment variable: {env_var}")
                    break
        
        # Try to get from Qiskit saved credentials
        if not ibm_api_token:
            try:
                from qiskit_ibm_provider import IBMProvider
                # This uses credentials saved via IBMProvider.save_account()
                provider = IBMProvider()
                logger.info("Using IBM Quantum credentials from Qiskit saved account.")
                ibm_api_token = "USING_SAVED_ACCOUNT"  # Placeholder to indicate we're using saved credentials
            except Exception as e:
                logger.warning(f"Error accessing saved IBM credentials: {e}")
        
        if not ibm_api_token:
            error_msg = "IBM Quantum API token not found. Please provide it using --api-token or set it as an environment variable (QISKIT_IBM_TOKEN, IBM_QUANTUM_TOKEN)."
            logger.error(error_msg)
            metadata['error'] = error_msg
            return {"counts": counts, "metadata": metadata} # Return dict
        
        # Read QASM file
        with open(qasm_file, 'r') as f:
            qasm_str = f.read()
        
        # Load the QASM into a Qiskit circuit
        temp_file = tempfile.NamedTemporaryFile(suffix='.qasm', delete=False).name
        with open(temp_file, 'w') as f:
            f.write(qasm_str)
        
        # Parse the circuit
        try:
            circuit = QuantumCircuit.from_qasm_file(temp_file)
        finally:
            try: os.remove(temp_file)
            except: pass
        
        if circuit is None:
            error_msg = "Failed to load circuit from QASM."
            logger.error(error_msg)
            metadata['error'] = error_msg
            return {"counts": counts, "metadata": metadata} # Return dict
        
        # Initialize IBM Quantum services based on API version
        try:
            try:
                # First try with Qiskit IBM Runtime (newer API)
                from qiskit_ibm_runtime import QiskitRuntimeService, Sampler
                
                # Initialize the QiskitRuntimeService
                if ibm_api_token == "USING_SAVED_ACCOUNT":
                    service = QiskitRuntimeService()
                else:
                    service = QiskitRuntimeService(channel="ibm_quantum", token=ibm_api_token)
                
                logger.info("Using QiskitRuntimeService API")
                
                if not service.active_account():
                    raise RuntimeError("IBM Quantum credentials invalid or expired")
                
                # Get available hardware backends
                backends = service.backends(operational=True, simulator=False)
                if not backends:
                    raise RuntimeError("No IBM Quantum devices available")
                
                # Select backend
                if device_id and any(b.name == device_id for b in backends):
                    device = next(b for b in backends if b.name == device_id)
                    logger.info(f"Using specified device: {device.name}")
                else:
                    if device_id:
                        logger.warning(f"Specified device {device_id} not found or not available")
                    
                    # Get least busy device
                    device = min(backends, key=lambda b: b.status().pending_jobs)
                    logger.info(f"Using least busy device: {device.name}")
                
                # Print device info
                logger.info(f"Device: {device.name}, Qubits: {device.num_qubits}")
                
                # Transpile circuit for the target device
                transpiled = transpile(circuit, backend=device, optimization_level=optimization_level)
                
                # Submit the job using Runtime API
                logger.info(f"Submitting job to {device.name} using Runtime API")
                
                # Try different Sampler initialization approaches
                try:
                    # First try SamplerV2 (newer API)
                    from qiskit_ibm_runtime import SamplerV2
                    logger.info("Attempting to initialize SamplerV2")
                    
                    # Set options for shots
                    options = {"default_shots": shots}
                    
                    # Initialize SamplerV2
                    sampler = SamplerV2(mode=device, options=options)
                    
                    # Submit job
                    job = sampler.run([transpiled])
                    logger.info("Successfully submitted job using SamplerV2")
                except (ImportError, Exception) as e:
                    logger.warning(f"Error with SamplerV2 initialization: {str(e)}")
                    
                    # Fall back to regular Sampler
                    logger.info("Falling back to regular Sampler")
                    sampler = Sampler(backend=device)
                    job = sampler.run([transpiled], shots=shots)
                    logger.info("Successfully submitted job using Sampler")
                
                # Get job ID
                job_id = job.job_id()
                logger.info(f"Job ID: {job_id}")
                logger.info(f"Monitor at: https://quantum.ibm.com/jobs/{job_id}")
            
            except (ImportError, Exception) as e:
                # Fall back to IBMProvider (older API)
                logger.warning(f"Runtime API failed: {str(e)}")
                logger.info("Falling back to IBMProvider API")
                
                from qiskit_ibm_provider import IBMProvider
                
                # Initialize provider
                if ibm_api_token == "USING_SAVED_ACCOUNT":
                    provider = IBMProvider()
                else:
                    provider = IBMProvider(token=ibm_api_token)
                
                # Get available backends
                backends = provider.backends(operational=True, simulator=False)
                
                # Select backend
                if device_id and any(b.name == device_id for b in backends):
                    device = provider.get_backend(device_id)
                    logger.info(f"Using specified device: {device.name}")
                else:
                    if device_id:
                        logger.warning(f"Specified device {device_id} not found or not available")
                    
                    # Get least busy backend
                    device = provider.backend.least_busy(backends)
                    logger.info(f"Using least busy device: {device.name}")
                
                # Print device info
                logger.info(f"Device: {device.name}, Qubits: {device.configuration().n_qubits}")
                
                # Transpile circuit for the target device
                transpiled = transpile(circuit, backend=device, optimization_level=optimization_level)
                
                # Submit the job
                logger.info(f"Submitting job to {device.name}")
                job = device.run(transpiled, shots=shots)
                job_id = job.job_id()
                logger.info(f"Job ID: {job_id}")
            
            # Set up metadata
            metadata = {
                'platform': 'ibm',
                'provider': 'IBM',
                'device': device.name if hasattr(device, 'name') else str(device),
                'device_id': device_id if device_id else (device.name if hasattr(device, 'name') else str(device)),
                'job_id': job_id,
                'optimization_level': optimization_level,
                'error': None # Clear initial error
            }
            
            # Wait for results if requested
            if wait_for_results:
                logger.info(f"Waiting for job to complete (timeout: {poll_timeout_seconds}s)...")
                start_time = time.time()
                
                # Poll until job completes or timeout
                while time.time() - start_time < poll_timeout_seconds:
                    job_status = job.status()
                    logger.info(f"Current status: {job_status}")
                    
                    # Check if job completed or failed
                    if isinstance(job_status, str):
                        if job_status.upper() in ["DONE", "ERROR", "CANCELLED"]:
                            break
                    elif job_status in [JobStatus.DONE, JobStatus.ERROR, JobStatus.CANCELLED]:
                        break
                    
                    time.sleep(30)  # Sleep for 30 seconds between polls
                
                # --- Result Processing Block (Returns dict or raises error) --- 
                job_final_status = job.status()
                status_str = job_final_status.name if hasattr(job_final_status, 'name') else str(job_final_status)
                logger.info(f"Final job status check. Value: {status_str}")
                
                if job and (job_final_status == JobStatus.DONE or status_str.upper() == "DONE"):
                    logger.info("Job completed successfully!")
                    metadata['status'] = status_str
                    metadata['execution_time'] = time.time() - start_time
                    
                    try:
                        result = job.result()
                        logger.info(f"Result object type: {type(result)}")
                        logger.debug(f"Result object attributes: {dir(result)}")
                        
                        result_counts = None # Initialize
                        
                        # Standard Qiskit result format
                        if hasattr(result, 'get_counts'):
                            try:
                                result_counts = result.get_counts(0) # Try index 0 first
                                logger.info(f"Successfully extracted counts from result.get_counts(0)")
                            except Exception as e:
                                logger.warning(f"Failed to extract counts using result.get_counts(): {str(e)}")
                        
                        # PrimitiveResult format (IBM Qiskit Runtime SamplerV2)
                        elif hasattr(result, '_pub_results') and result._pub_results:
                            logger.info("Processing PrimitiveResult format (SamplerV2)")
                            if len(result._pub_results) > 0:
                                pub_result = result._pub_results[0]
                                logger.info(f"pub_result type: {type(pub_result)}")
                                logger.debug(f"pub_result attributes: {dir(pub_result)}")

                                if hasattr(pub_result, 'data'):
                                    logger.debug(f"pub_result.data type: {type(pub_result.data)}")
                                    logger.debug(f"pub_result.data attributes: {dir(pub_result.data)}")

                                    # Function to attempt extraction (as provided by user)
                                    def attempt_extraction(reg_name):
                                        if reg_name and hasattr(pub_result.data, reg_name):
                                            creg_data = getattr(pub_result.data, reg_name)
                                            logger.info(f"Attempting extraction with register name: {reg_name}")
                                            if hasattr(creg_data, 'get_counts'):
                                                try:
                                                    counts = creg_data.get_counts()
                                                    logger.info(f"Counts extracted successfully using register '{reg_name}': {counts}")
                                                    return counts
                                                except Exception as e:
                                                    logger.warning(f"Error calling get_counts on register '{reg_name}': {e}")
                                            else: logger.warning(f"Register data for '{reg_name}' has no get_counts method.")
                                        else: logger.debug(f"pub_result.data has no attribute named '{reg_name}'")
                                        return None

                                    # Determine classical register name (best effort)
                                    creg_name = None
                                    if circuit and hasattr(circuit, 'cregs') and circuit.cregs: # Added check for circuit existence
                                        creg_name = circuit.cregs[0].name
                                        logger.info(f"Found classical register name from circuit: {creg_name}")
                                    else: 
                                        logger.warning("Could not find classical register name in circuit object. Will try common names.")
                                        creg_name = "c" # Default
                                    logger.info(f"Attempting counts extraction with register: {creg_name}")

                                    extracted_counts = attempt_extraction(creg_name)
                                    if extracted_counts is None: # Fallback attempts
                                        logger.info("Primary extraction failed. Trying common register names.")
                                        common_names = ['c', 'meas', 'measurement', 'creg']
                                        if creg_name in common_names: common_names.remove(creg_name)
                                        for name in common_names:
                                            extracted_counts = attempt_extraction(name)
                                            if extracted_counts is not None: break
                                    
                                    if extracted_counts is None: # Final fallback: inspect all data attributes
                                        logger.warning("Could not extract counts using common names. Inspecting all data attributes.")
                                        for attr in dir(pub_result.data):
                                            if not attr.startswith('_'):
                                                logger.debug(f"Inspecting attribute: {attr}")
                                                extracted_counts = attempt_extraction(attr)
                                                if extracted_counts is not None: break
                                            
                                    if extracted_counts is not None:
                                        result_counts = extracted_counts
                                    else: logger.error("Failed to extract counts from pub_result.data using all methods.")
                                else: logger.error("pub_result has no data attribute")
                            else: logger.error("result has no _pub_results or it's empty")
                        
                        # Try simple data.counts attribute
                        elif hasattr(result, 'data') and hasattr(result.data, 'counts'):
                             try: 
                                 result_counts = result.data.counts
                                 logger.info("Successfully extracted counts from result.data.counts")
                             except Exception as e: logger.warning(f"Failed to extract from result.data.counts: {str(e)}")

                        # Check if counts were found
                        if result_counts is not None:
                            counts = result_counts
                            logger.info(f"Using extracted counts: {counts}")
                        else:
                            logger.warning("No counts could be extracted, returning default error counts.")
                            counts = {"error_extracting_counts": 1}
                            metadata['error'] = "Failed to extract counts from result object."
                            
                        return {"counts": counts, "metadata": metadata} # Return dict
                        
                    except Exception as e:
                        error_msg = f"Failed to process result object: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        metadata['error'] = error_msg
                        counts = {"error_processing_result": 1}
                        return {"counts": counts, "metadata": metadata} # Return dict
                else:
                    error_msg = f"Job failed or timed out. Final status: {status_str}"
                    logger.error(error_msg)
                    metadata['error'] = error_msg
                    counts = {"error_job_failed_or_timed_out": 1}
                    return {"counts": counts, "metadata": metadata} # Return dict
            else:
                # Return a placeholder result with job information
                logger.info("Job submitted, not waiting for results.")
                metadata['status'] = 'SUBMITTED'
                counts = {} # No counts available yet
                return {"counts": counts, "metadata": metadata} # Return dict
                
        except Exception as e:
            error_msg = f"Failed to submit circuit to IBM Quantum: {str(e)}"
            logger.error(error_msg, exc_info=True)
            metadata['error'] = error_msg
            counts = {"error_submitting_job": 1}
            return {"counts": counts, "metadata": metadata} # Return dict
            
    except Exception as e:
        error_msg = f"Error in run_on_ibm_hardware: {str(e)}"
        logger.error(error_msg, exc_info=True)
        metadata['error'] = error_msg # Update metadata
        counts = {"error_outer_exception": 1} # Update counts
        return {"counts": counts, "metadata": metadata} # Return dict 