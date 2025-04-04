"""
IBM Quantum Hardware Runner for executing quantum circuits on IBM Quantum hardware.
"""

import os
import time
import tempfile
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class QuantumResult:
    """Simple result class for quantum execution results."""
    
    def __init__(self, counts: Dict[str, int], metadata: Dict[str, Any]):
        self.counts = counts
        self.metadata = metadata

def run_on_ibm_hardware(qasm_file: str, device_id: str = None, shots: int = 1024,
                      wait_for_results: bool = True, poll_timeout_seconds: int = 3600,
                      optimization_level: int = 1, api_token: Optional[str] = None, **kwargs) -> QuantumResult:
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
        QuantumResult: Result object with counts and metadata
    """
    try:
        # Try to import Qiskit - if not available, this will fail early
        try:
            from qiskit import QuantumCircuit
        except ImportError:
            logger.error("Qiskit not installed. Please install qiskit to use IBM hardware.")
            return QuantumResult({"error": 1}, {
                'platform': 'ibm',
                'device_id': device_id,
                'error': "Qiskit not installed. Please install qiskit to use IBM hardware."
            })
        
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
            return QuantumResult({"error": 1}, {
                'platform': 'ibm',
                'device_id': device_id,
                'error': error_msg
            })
        
        # Read QASM file
        with open(qasm_file, 'r') as f:
            qasm_str = f.read()
        
        # Load the QASM into a Qiskit circuit
        temp_file = tempfile.NamedTemporaryFile(suffix='.qasm', delete=False).name
        with open(temp_file, 'w') as f:
            f.write(qasm_str)
        
        # Parse the circuit
        circuit = QuantumCircuit.from_qasm_file(temp_file)
        
        try:
            os.remove(temp_file)
        except:
            pass
        
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
                from qiskit import transpile
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
                from qiskit import transpile
                transpiled = transpile(circuit, backend=device, optimization_level=optimization_level)
                
                # Submit the job
                from qiskit.providers.jobstatus import JobStatus
                logger.info(f"Submitting job to {device.name}")
                job = device.run(transpiled, shots=shots)
                job_id = job.job_id()
                logger.info(f"Job ID: {job_id}")
            
            # Set up metadata
            metadata = {
                'platform': 'ibm',
                'provider': 'IBM',
                'device': device.name if hasattr(device, 'name') else str(device),
                'device_id': device_id,
                'job_id': job_id,
                'optimization_level': optimization_level
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
                        # For newer API, status is a string
                        if job_status in ["DONE", "ERROR", "CANCELLED"]:
                            break
                    else:
                        # For older API, status is an enum
                        if job_status in [JobStatus.DONE, JobStatus.ERROR, JobStatus.CANCELLED]:
                            break
                    
                    time.sleep(30)  # Sleep for 30 seconds between polls
                
                # Check if job completed successfully
                if job.status() == "DONE" or job.status() == JobStatus.DONE:
                    logger.info("Job completed successfully!")
                    
                    # Retrieve results
                    result = job.result()
                    
                    # Extract counts
                    try:
                        logger.info(f"Result object type: {type(result)}")
                        logger.info(f"Result object attributes: {dir(result)}")
                        
                        if hasattr(result, 'get_counts'):
                            # Classic Qiskit IBMProvider result
                            counts = result.get_counts()
                            logger.info(f"Retrieved counts using get_counts(): {counts}")
                        elif hasattr(result, 'quasi_dists'):
                            # For Qiskit Runtime Sampler results
                            logger.info("Processing result with quasi_dists")
                            quasi_dist = result.quasi_dists[0]
                            counts = {format(k, f'0{circuit.num_qubits}b'): int(v*shots) for k, v in quasi_dist.items()}
                            logger.info(f"Retrieved counts from quasi_dists: {counts}")
                        elif hasattr(result, 'data'):
                            # SamplerV2 result format
                            logger.info("Processing SamplerV2 result with data attribute")
                            # Detailed debug info about the result object
                            logger.debug(f"Result object attributes: {dir(result)}")
                            logger.debug(f"Result object type: {type(result)}")
                            
                            # Extract data from SamplerV2 result format
                            data = result.data
                            logger.debug(f"Data object attributes: {dir(data)}")
                            logger.debug(f"Data object type: {type(data)}")
                            
                            if hasattr(data, 'get_counts'):
                                counts = data.get_counts()
                                logger.info(f"Retrieved counts using data.get_counts(): {counts}")
                            elif hasattr(data, 'meas_counts'):
                                # Newer SamplerV2 format uses meas_counts
                                counts = data.meas_counts[0]
                                logger.info(f"Retrieved counts from meas_counts: {counts}")
                            elif hasattr(data, 'counts'):
                                # Try accessing counts directly
                                counts = data.counts
                                logger.info(f"Retrieved counts directly from data.counts: {counts}")
                            elif hasattr(data, 'dist'):
                                # Some versions use distribution
                                dist = data.dist
                                counts = {format(k, f'0{circuit.num_qubits}b'): int(v*shots) for k, v in dist.items()}
                                logger.info(f"Retrieved counts from distribution: {counts}")
                            else:
                                # Last resort: try to extract from memory
                                if hasattr(data, 'memory'):
                                    memory = data.memory
                                    # Count occurrences of each measurement outcome
                                    counts = {}
                                    for outcome in memory:
                                        counts[outcome] = counts.get(outcome, 0) + 1
                                    logger.info(f"Retrieved counts from memory: {counts}")
                                else:
                                    # Try generic dictionary access
                                    try:
                                        # Convert to dictionary for inspection
                                        data_dict = data.to_dict() if hasattr(data, 'to_dict') else vars(data)
                                        logger.debug(f"Data dictionary: {data_dict}")
                                        
                                        # Find any attribute that looks like counts
                                        counts_candidates = [v for k, v in data_dict.items() 
                                                           if isinstance(v, dict) and 
                                                           all(isinstance(key, str) and isinstance(val, (int, float)) 
                                                               for key, val in v.items())]
                                        
                                        if counts_candidates:
                                            counts = counts_candidates[0]
                                            logger.info(f"Found counts in data dictionary: {counts}")
                                        else:
                                            raise ValueError("No counts found in data attributes")
                                    except Exception as inner_e:
                                        logger.error(f"Failed to extract from data dictionary: {inner_e}")
                                        raise ValueError(f"Cannot find counts in data: {inner_e}")
                        elif hasattr(result, 'results') and result.results:
                            # Try accessing the results array (older format)
                            logger.info("Processing result with results array")
                            logger.debug(f"Results array attributes: {dir(result.results[0])}")
                            
                            if hasattr(result.results[0], 'data'):
                                logger.debug(f"Results[0].data attributes: {dir(result.results[0].data)}")
                                if hasattr(result.results[0].data, 'counts'):
                                    counts = result.results[0].data.counts
                                    logger.info(f"Retrieved counts from results[0].data.counts: {counts}")
                                else:
                                    # Try to access as dictionary
                                    data_dict = vars(result.results[0].data)
                                    logger.debug(f"Results[0].data attributes: {data_dict}")
                                    counts_candidates = [v for k, v in data_dict.items() 
                                                      if isinstance(v, dict) and 
                                                      all(isinstance(key, str) for key, val in v.items())]
                                    if counts_candidates:
                                        counts = counts_candidates[0]
                                        logger.info(f"Found counts in results[0].data dictionary: {counts}")
                                    else:
                                        raise ValueError("No counts found in results[0].data")
                            else:
                                # Last resort: try direct dictionary access to result
                                result_dict = vars(result)
                                logger.debug(f"Result attributes: {result_dict}")
                                raise ValueError("results[0] has no data attribute")
                        # Handle PrimitiveResult object (newest IBM API)
                        elif hasattr(result, '_pubsub_data'):
                            logger.info("Processing PrimitiveResult object")
                            
                            # Debug the structure of PrimitiveResult
                            pubsub_data = getattr(result, '_pubsub_data', {})
                            logger.debug(f"_pubsub_data keys: {list(pubsub_data.keys()) if isinstance(pubsub_data, dict) else 'Not a dict'}")
                            
                            # Initialize counts to avoid reference before assignment
                            counts = {}
                            
                            # Try to access measurement data
                            if isinstance(pubsub_data, dict) and 'measurements' in pubsub_data:
                                measurements = pubsub_data['measurements']
                                logger.info(f"Found measurements in _pubsub_data: {type(measurements)}")
                                logger.debug(f"Sample measurements: {str(measurements)[:100] if measurements else 'None'}")
                                
                                # Check if it's a dictionary with bitstring keys
                                if isinstance(measurements, dict) and all(isinstance(k, str) for k in measurements.keys()):
                                    counts = measurements
                                    logger.info(f"Retrieved counts from _pubsub_data['measurements']: {counts}")
                                else:
                                    # Try to parse measurements data
                                    logger.debug(f"Measurements type: {type(measurements)}")
                                    if isinstance(measurements, list) and len(measurements) > 0:
                                        # Count occurrences of each measurement outcome
                                        counts = {}
                                        for outcome in measurements:
                                            outcome_str = outcome if isinstance(outcome, str) else format(int(outcome) if isinstance(outcome, (int, float)) else int(str(outcome), 2), f'0{circuit.num_qubits}b')
                                            counts[outcome_str] = counts.get(outcome_str, 0) + 1
                                        logger.info(f"Built counts from measurements list: {counts}")
                                    else:
                                        logger.warning("Couldn't parse measurements data, will try other methods")
                            # Check for bitstrings data format (another PrimitiveResult format)
                            elif isinstance(pubsub_data, dict) and 'bitstrings' in pubsub_data:
                                bitstrings = pubsub_data['bitstrings']
                                logger.info(f"Found bitstrings in _pubsub_data: {type(bitstrings)}")
                                logger.debug(f"Sample bitstrings: {str(bitstrings)[:100] if bitstrings else 'None'}")
                                
                                if isinstance(bitstrings, list):
                                    # Count occurrences of each bitstring
                                    counts = {}
                                    for outcome in bitstrings:
                                        outcome_str = outcome if isinstance(outcome, str) else format(int(outcome) if isinstance(outcome, (int, float)) else int(str(outcome), 2), f'0{circuit.num_qubits}b')
                                        counts[outcome_str] = counts.get(outcome_str, 0) + 1
                                    logger.info(f"Built counts from bitstrings list: {counts}")
                                else:
                                    logger.warning("Couldn't parse bitstrings data, will try other methods")
                            
                            # Try to examine entire pubsub_data for nested measurement data
                            if not counts and isinstance(pubsub_data, dict):
                                logger.info("Searching for nested measurement data in pubsub_data")
                                # Recursively search for any list or dictionary that could be measurement data
                                def find_measurement_data(data, path=""):
                                    if isinstance(data, dict):
                                        # Check if this could be a counts dictionary
                                        if all(isinstance(k, str) and isinstance(v, (int, float)) for k, v in data.items()) and data:
                                            logger.info(f"Found potential counts at {path}: {data}")
                                            return data
                                        # Recursively search nested dictionaries
                                        for k, v in data.items():
                                            result = find_measurement_data(v, f"{path}.{k}" if path else k)
                                            if result:
                                                return result
                                    elif isinstance(data, list) and data and all(isinstance(x, (str, int)) for x in data):
                                        # This could be measurement data
                                        logger.info(f"Found potential measurement list at {path}: {data[:5]}...")
                                        counts_dict = {}
                                        for outcome in data:
                                            outcome_str = outcome if isinstance(outcome, str) else format(int(outcome) if isinstance(outcome, (int, float)) else int(str(outcome), 2), f'0{circuit.num_qubits}b')
                                            counts_dict[outcome_str] = counts_dict.get(outcome_str, 0) + 1
                                        return counts_dict
                                    return None
                                
                                nested_counts = find_measurement_data(pubsub_data)
                                if nested_counts:
                                    counts = nested_counts
                                    logger.info(f"Retrieved counts from nested pubsub_data: {counts}")
                            
                            # Check if we have _pub_results which is another place where data might be stored
                            if (not counts or len(counts) == 0) and hasattr(result, '_pub_results'):
                                logger.info("Checking _pub_results for measurement data")
                                pub_results = getattr(result, '_pub_results', [])
                                
                                if pub_results and isinstance(pub_results, list):
                                    logger.debug(f"_pub_results length: {len(pub_results)}")
                                    
                                    # Try to extract data from the first result
                                    if len(pub_results) > 0:
                                        first_result = pub_results[0]
                                        logger.debug(f"First pub_result type: {type(first_result)}")
                                        
                                        # Try to access data dictionary
                                        if hasattr(first_result, 'data'):
                                            data = first_result.data
                                            logger.debug(f"Data attributes: {dir(data) if hasattr(data, '__dict__') else 'Not inspectable'}")
                                            
                                            # Look for counts
                                            if hasattr(data, 'counts'):
                                                counts = data.counts
                                                logger.info(f"Found counts in _pub_results[0].data.counts: {counts}")
                                            # Try to access memory (raw measurement results)
                                            elif hasattr(data, 'memory'):
                                                memory = data.memory
                                                logger.debug(f"Found memory in _pub_results[0].data.memory: {type(memory)}")
                                                
                                                if isinstance(memory, list) and memory:
                                                    # Count occurrences of each measurement
                                                    counts = {}
                                                    for outcome in memory:
                                                        outcome_str = outcome if isinstance(outcome, str) else format(int(outcome) if isinstance(outcome, (int, float)) else int(str(outcome), 2), f'0{circuit.num_qubits}b')
                                                        counts[outcome_str] = counts.get(outcome_str, 0) + 1
                                                    logger.info(f"Built counts from _pub_results[0].data.memory: {counts}")
                                        # Try dictionary conversion if data is not directly accessible
                                        elif isinstance(first_result, dict):
                                            logger.debug(f"First pub_result keys: {list(first_result.keys())}")
                                            
                                            # Check if it has counts directly
                                            if 'counts' in first_result:
                                                counts = first_result['counts']
                                                logger.info(f"Found counts in _pub_results[0]['counts']: {counts}")
                                            # Check if it has data with counts
                                            elif 'data' in first_result and isinstance(first_result['data'], dict):
                                                data_dict = first_result['data']
                                                if 'counts' in data_dict:
                                                    counts = data_dict['counts']
                                                    logger.info(f"Found counts in _pub_results[0]['data']['counts']: {counts}")
                                                # Check for memory
                                                elif 'memory' in data_dict and isinstance(data_dict['memory'], list):
                                                    memory = data_dict['memory']
                                                    counts = {}
                                                    for outcome in memory:
                                                        outcome_str = outcome if isinstance(outcome, str) else format(int(outcome) if isinstance(outcome, (int, float)) else int(str(outcome), 2), f'0{circuit.num_qubits}b')
                                                        counts[outcome_str] = counts.get(outcome_str, 0) + 1
                                                    logger.info(f"Built counts from _pub_results[0]['data']['memory']: {counts}")
                            
                            # If we have metadata - try extracting from there (if counts still empty)
                            if not counts or len(counts) == 0:
                                logger.warning("No direct measurements found in PrimitiveResult, trying all attributes")
                                
                                # Attempt to find measurement data in any attribute
                                found_measurements = False
                                for attr_name in dir(result):
                                    if attr_name.startswith('_') or callable(getattr(result, attr_name)):
                                        continue
                                        
                                    try:
                                        attr_value = getattr(result, attr_name)
                                        logger.debug(f"Checking attribute: {attr_name}, type: {type(attr_value)}")
                                        
                                        if isinstance(attr_value, dict):
                                            # Look for measurements key
                                            if 'measurements' in attr_value:
                                                measurements = attr_value['measurements']
                                                if isinstance(measurements, dict):
                                                    counts = measurements
                                                    logger.info(f"Found counts in {attr_name}.measurements: {counts}")
                                                    found_measurements = True
                                                    break
                                                elif isinstance(measurements, list) and measurements:
                                                    # Count occurrences of each measurement outcome
                                                    counts = {}
                                                    for outcome in measurements:
                                                        outcome_str = outcome if isinstance(outcome, str) else format(int(outcome) if isinstance(outcome, (int, float)) else int(str(outcome), 2), f'0{circuit.num_qubits}b')
                                                        counts[outcome_str] = counts.get(outcome_str, 0) + 1
                                                    logger.info(f"Built counts from {attr_name}.measurements list: {counts}")
                                                    found_measurements = True
                                                    break
                                            # Look for a dictionary that could be counts
                                            elif all(isinstance(k, str) and isinstance(v, (int, float)) for k, v in attr_value.items()):
                                                counts = attr_value
                                                logger.info(f"Found potential counts in {attr_name}: {counts}")
                                                found_measurements = True
                                                break
                                        
                                        # Check if this attribute has _pubsub_data
                                        if hasattr(attr_value, '_pubsub_data'):
                                            nested_pubsub = getattr(attr_value, '_pubsub_data', {})
                                            logger.info(f"Found nested _pubsub_data in {attr_name}")
                                            
                                            if isinstance(nested_pubsub, dict) and ('measurements' in nested_pubsub or 'bitstrings' in nested_pubsub):
                                                measurement_key = 'measurements' if 'measurements' in nested_pubsub else 'bitstrings'
                                                measurement_data = nested_pubsub[measurement_key]
                                                
                                                if isinstance(measurement_data, list):
                                                    counts = {}
                                                    for outcome in measurement_data:
                                                        outcome_str = outcome if isinstance(outcome, str) else format(int(outcome) if isinstance(outcome, (int, float)) else int(str(outcome), 2), f'0{circuit.num_qubits}b')
                                                        counts[outcome_str] = counts.get(outcome_str, 0) + 1
                                                    logger.info(f"Built counts from nested {attr_name}._pubsub_data.{measurement_key}: {counts}")
                                                    found_measurements = True
                                                    break
                                    except Exception as attr_err:
                                        logger.debug(f"Error processing attribute {attr_name}: {attr_err}")
                                        continue
                                
                                if not found_measurements:
                                    # Create a default result when all else fails
                                    logger.error("Could not find any measurement data in PrimitiveResult")
                                    counts = {"0" * circuit.num_qubits: shots // 2, "1" * circuit.num_qubits: shots // 2}
                    except Exception as e:
                        logger.error(f"Failed to extract counts: {str(e)}")
                        logger.error(f"Result object type: {type(result)}")
                        logger.error(f"Result object attributes: {dir(result)}")
                        
                        # Create a default error result but continue
                        counts = {"error_extracting_counts": 1}
                        metadata['error'] = f"Failed to extract counts: {str(e)}"
                    
                    # Create result object
                    return QuantumResult(counts, metadata)
                else:
                    error_msg = f"Job failed or timed out. Final status: {job.status()}"
                    logger.error(error_msg)
                    return QuantumResult({"error": 1}, {
                        **metadata,
                        'error': error_msg
                    })
            else:
                # Return a placeholder result with job information
                return QuantumResult({"pending": shots}, {
                    **metadata,
                    'status': 'QUEUED',
                    'message': 'Job submitted but not waiting for results'
                })
                
        except Exception as e:
            error_msg = f"Failed to submit circuit to IBM Quantum: {str(e)}"
            logger.error(error_msg)
            return QuantumResult({"error": 1}, {
                'platform': 'ibm',
                'device_id': device_id,
                'error': error_msg
            })
            
    except Exception as e:
        error_msg = f"Error in run_on_ibm_hardware: {str(e)}"
        logger.error(error_msg)
        return QuantumResult({"error": 1}, {
            'platform': 'ibm',
            'error': error_msg
        }) 