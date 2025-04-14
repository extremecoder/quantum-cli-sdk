"""
Generate microservice wrapper for quantum circuits.
"""

import os
import sys
import logging
import shutil

# Set up logger
logger = logging.getLogger(__name__)

# Path to templates directory
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "microservice")

def generate_microservice(source_file=None, dest_dir=None, llm_url=None, port=8889, app_root=None):
    """
    Generate a microservice for the provided QASM circuit.
    
    Args:
        source_file: Input QASM file (default: search in ir/openqasm/mitigated/)
        dest_dir: Destination directory (default: microservice in project root)
        llm_url: URL to an LLM for enhanced generation (not used in simplified version)
        port: Port number for the service to listen on (not used in simplified version)
        app_root: Root of the application (used for resolving paths)
        
    Returns:
        bool: True if generation succeeded
    """
    # Override app_root to use current directory if not provided
    if not app_root:
        app_root = os.getcwd()
        logger.debug(f"app_root not provided, using current directory: {app_root}")

    # --- Determine Input Source File --- 
    actual_source_file = None
    if source_file is None:
        logger.info("Source file not provided, searching in default location ir/openqasm/mitigated/...")
        default_ir_dir = os.path.join(app_root, "ir", "openqasm", "mitigated")
        if os.path.isdir(default_ir_dir):
            qasm_files = [f for f in os.listdir(default_ir_dir) if f.lower().endswith('.qasm')]
            if len(qasm_files) == 1:
                actual_source_file = os.path.join(default_ir_dir, qasm_files[0])
                logger.info(f"Found default source file: {actual_source_file}")
            elif len(qasm_files) > 1:
                logger.error(f"Multiple .qasm files found in {default_ir_dir}: {qasm_files}. Specify input file.")
                return False
            else:
                logger.error(f"No .qasm files found in {default_ir_dir}. Provide source file.")
                return False
        else:
            logger.error(f"Default IR directory not found: {default_ir_dir}. Provide source file.")
            return False
    elif os.path.exists(source_file):
        # If source_file is provided, use it directly after validation
        # Check if it's absolute, make it absolute if not (relative to CWD)
        if not os.path.isabs(source_file):
            actual_source_file = os.path.abspath(source_file)
            logger.info(f"Resolved relative source file path to: {actual_source_file}")
        else:
            actual_source_file = source_file
    else:
        logger.error(f"Provided source file does not exist: {source_file}")
        return False

    # --- Validate Input Source File --- 
    if not actual_source_file or not os.path.exists(actual_source_file):
        logger.error(f"Input source file '{source_file or 'default'}' could not be found or resolved to '{actual_source_file}'.")
        return False
    
    logger.info(f"Using source file: {actual_source_file}")
    file_ext = os.path.splitext(actual_source_file)[1].lower()
    if file_ext != '.qasm':
        logger.error(f"Unsupported file type '{file_ext}'. Requires .qasm")
        return False

    # --- Determine Destination Directory --- 
    if not dest_dir:
        dest_dir = os.path.join(app_root, "microservice")
        logger.info(f"Output directory not specified, defaulting to: {dest_dir}")
    elif not os.path.isabs(dest_dir):
        dest_dir = os.path.join(app_root, dest_dir)
    
    dest_dir = os.path.abspath(dest_dir)
    
    try:
        os.makedirs(dest_dir, exist_ok=True)
        logger.info(f"Ensured microservice destination directory exists: {dest_dir}")
    except Exception as e:
        logger.error(f"Failed to create destination directory {dest_dir}: {e}")
        return False

    # --- Copy the Dockerfile template ---
    dockerfile_template_path = os.path.join(TEMPLATES_DIR, "Dockerfile")
    if not os.path.exists(dockerfile_template_path):
        logger.error(f"Dockerfile template not found at {dockerfile_template_path}")
        return False

    # Get the OpenQASM filename
    qasm_filename = os.path.basename(actual_source_file)
    
    # Read the template Dockerfile
    try:
        with open(dockerfile_template_path, 'r') as template_file:
            dockerfile_content = template_file.read()
        
        # Replace "test_circuit.qasm" with the actual filename
        dockerfile_content = dockerfile_content.replace("test_circuit.qasm", qasm_filename)
        
        # Add a CMD to override the base image's CMD and specify the port
        if not "CMD " in dockerfile_content:
            dockerfile_content += f"""
# Export the port as an environment variable (don't override CMD)
ENV PORT={port}
EXPOSE {port}
"""
        
        # Write the updated Dockerfile to the destination directory
        dockerfile_dest_path = os.path.join(dest_dir, "Dockerfile")
        with open(dockerfile_dest_path, 'w') as dest_file:
            dest_file.write(dockerfile_content)
        
        logger.info(f"Created Dockerfile at {dockerfile_dest_path}")
    except Exception as e:
        logger.error(f"Failed to process Dockerfile template: {e}")
        return False

    # --- Copy the OpenQASM file to the destination directory ---
    try:
        qasm_dest_path = os.path.join(dest_dir, qasm_filename)
        shutil.copy2(actual_source_file, qasm_dest_path)
        logger.info(f"Copied OpenQASM file to {qasm_dest_path}")
    except Exception as e:
        logger.error(f"Failed to copy OpenQASM file: {e}")
        return False

    # --- Create README.md file ---
    try:
        readme_content = f"""# Quantum Microservice

This is a quantum computation microservice generated from the {qasm_filename} OpenQASM file.

## Building the Docker Image

To build the Docker image, run:

```bash
docker build -t quantum-service .
```

## Running the Microservice

By default, the microservice runs on port 8889. To start the container:

```bash
docker run -p 8889:8889 quantum-service
```

### Changing the Port

To run the service on a different port (for example, 9000):

```bash
docker run -p 9000:9000 -e PORT=9000 quantum-service
```

## Endpoints

- POST /api/v1/circuits/execute - Execute a quantum circuit
- GET /api/v1/jobs/{job_id} - Check job status
- DELETE /api/v1/jobs/{job_id} - Cancel a job
"""
        readme_path = os.path.join(dest_dir, "README.md")
        with open(readme_path, 'w') as readme_file:
            readme_file.write(readme_content)
        
        logger.info(f"Created README.md at {readme_path}")
    except Exception as e:
        logger.error(f"Failed to create README.md: {e}")
        # Non-fatal error, continue with generation

    # --- Create test directory and test scripts ---
    try:
        # Create test directory
        test_dir = os.path.join(dest_dir, "tests")
        os.makedirs(test_dir, exist_ok=True)
        
        # Create API test script
        test_script_content = f"""#!/usr/bin/env python3
\"\"\"
API Test Script for Quantum Microservice.
\"\"\"
import argparse
import json
import requests
import time
import os
from pathlib import Path

class QuantumAPIClient:
    \"\"\"Client for interacting with the Quantum Microservice API.\"\"\"
    
    def __init__(self, host: str = "localhost", port: int = 8889, api_base: str = "/api/v1"):
        \"\"\"
        Initialize API client.
        
        Args:
            host: API host
            port: API port
            api_base: Base API path
        \"\"\"
        self.base_url = f"http://{{host}}:{{port}}{{api_base}}"
        print(f"API URL: {{self.base_url}}")
    
    def execute_circuit(self, circuit_path: str, shots: int = 1024, 
                       backend_type: str = "simulator", backend_provider: str = "qiskit",
                       backend_name: str = None, async_mode: bool = False,
                       parameters: dict = None) -> dict:
        \"\"\"
        Execute a quantum circuit.
        
        Args:
            circuit_path: Path to OpenQASM circuit file
            shots: Number of execution shots
            backend_type: "simulator" or "hardware"
            backend_provider: Provider name
            backend_name: Specific backend name (optional)
            async_mode: Whether to run in async mode
            parameters: Circuit parameters (optional)
            
        Returns:
            API response as dict
        \"\"\"
        # Read circuit file
        with open(circuit_path, 'r') as f:
            circuit_content = f.read()
        
        # Build request payload
        payload = {{
            "circuit": circuit_content,
            "shots": shots,
            "backend_type": backend_type,
            "backend_provider": backend_provider,
            "async_mode": async_mode
        }}
        
        # Add optional parameters
        if backend_name:
            payload["backend_name"] = backend_name
        if parameters:
            payload["parameters"] = parameters
        
        # Execute API call
        response = requests.post(
            f"{{self.base_url}}/circuits/execute",
            json=payload,
            headers={{"Content-Type": "application/json"}}
        )
        
        # Handle response
        if response.status_code in [200, 202]:
            return response.json()
        else:
            print(f"Error: {{response.status_code}} - {{response.text}}")
            return {{"status": "error", "error": response.text}}
    
    def get_job_status(self, job_id: str) -> dict:
        \"\"\"
        Get status of a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            API response as dict
        \"\"\"
        response = requests.get(f"{{self.base_url}}/jobs/{{job_id}}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {{response.status_code}} - {{response.text}}")
            return {{"status": "error", "error": response.text}}
    
    def cancel_job(self, job_id: str) -> dict:
        \"\"\"
        Cancel a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            API response as dict
        \"\"\"
        response = requests.delete(f"{{self.base_url}}/jobs/{{job_id}}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {{response.status_code}} - {{response.text}}")
            return {{"status": "error", "error": response.text}}

def main():
    \"\"\"Main entry point.\"\"\"
    parser = argparse.ArgumentParser(description="Test Quantum Microservice API")
    parser.add_argument("--host", default="localhost", help="API host")
    parser.add_argument("--port", type=int, default=8889, help="API port")
    parser.add_argument("--circuit", default="../{qasm_filename}", help="Path to QASM circuit file")
    parser.add_argument("--test", choices=["sync", "async", "all"], default="all", 
                        help="Test mode: sync, async, or all")
    
    args = parser.parse_args()
    
    # Initialize API client
    client = QuantumAPIClient(host=args.host, port=args.port)
    
    circuit_path = args.circuit
    if not os.path.isabs(circuit_path):
        circuit_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), circuit_path)
    
    if not os.path.exists(circuit_path):
        print(f"Error: Circuit file not found: {{circuit_path}}")
        return
    
    print(f"Testing with circuit: {{circuit_path}}")
    
    # Test synchronous execution
    if args.test in ["sync", "all"]:
        print("\\n=== Testing Synchronous Circuit Execution ===")
        sync_result = client.execute_circuit(
            circuit_path=circuit_path,
            shots=1024,
            backend_type="simulator",
            backend_provider="qiskit",
            async_mode=False
        )
        print("Synchronous execution result:")
        print(json.dumps(sync_result, indent=2))
    
    # Test asynchronous execution
    if args.test in ["async", "all"]:
        print("\\n=== Testing Asynchronous Circuit Execution ===")
        async_result = client.execute_circuit(
            circuit_path=circuit_path,
            shots=1024,
            backend_type="simulator",
            backend_provider="qiskit",
            async_mode=True
        )
        print("Asynchronous execution result:")
        print(json.dumps(async_result, indent=2))
        
        if async_result.get("status") == "success" and "job_id" in async_result.get("data", {{}}):
            job_id = async_result["data"]["job_id"]
            
            # Test job status
            print("\\n=== Testing Job Status ===")
            time.sleep(1)  # Wait a bit for job to process
            status_result = client.get_job_status(job_id)
            print("Job status result:")
            print(json.dumps(status_result, indent=2))
            
            # Wait and check again if not completed
            if status_result.get("data", {{}}).get("status") not in ["COMPLETED", "FAILED"]:
                print("Waiting for job to complete...")
                time.sleep(3)
                status_result = client.get_job_status(job_id)
                print("Updated job status:")
                print(json.dumps(status_result, indent=2))
            
            # Test job cancellation if still running
            if status_result.get("data", {{}}).get("status") in ["QUEUED", "RUNNING"]:
                print("\\n=== Testing Job Cancellation ===")
                cancel_result = client.cancel_job(job_id)
                print("Job cancellation result:")
                print(json.dumps(cancel_result, indent=2))
    
    print("\\n=== API Testing Complete ===")

if __name__ == "__main__":
    main()
"""
        test_api_path = os.path.join(test_dir, "test_api.py")
        with open(test_api_path, 'w') as test_file:
            test_file.write(test_script_content)
        
        # Make the test script executable
        os.chmod(test_api_path, 0o755)
        logger.info(f"Created API test script at {test_api_path}")
        
        # Create hardware test script
        hardware_test_content = f"""#!/usr/bin/env python3
\"\"\"
Test script for all supported quantum hardware providers.
\"\"\"
import requests
import json
import time
from typing import Dict, Any

API_URL = "http://localhost:{port}/api/v1/circuits/execute"

def test_hardware(provider: str) -> Dict[str, Any]:
    \"\"\"
    Test a specific quantum hardware.
    
    Args:
        provider: The hardware provider (ibm)
        
    Returns:
        API response
    \"\"\"
    print(f"\\n===== Testing {{provider}} hardware =====")
    
    # Read the QASM file
    #with open("../{qasm_filename}", "r") as f:
    #    circuit = f.read()
    
    # Create the payload
    payload = {{
        #"circuit": circuit,
        "shots": 1024,
        "backend_type": "hardware",
        "backend_provider": provider,
        "backend_name": "ibmq_qasm_simulator",
        "async_mode": False
    }}
    
    # Make the API call
    print(f"Sending request to {{provider}} hardware...")
    response = requests.post(
        API_URL,
        json=payload,
        headers={{"Content-Type": "application/json"}}
    )
    
    # Print response
    result = response.json()
    print(json.dumps(result, indent=2))
    
    print(f"===== {{provider}} test complete =====\\n")
    return result

def main():
    \"\"\"Test all supported hardware providers.\"\"\"
    # Test each supported provider
    providers = ["ibm"]
    
    for provider in providers:
        result = test_hardware(provider)
        # Add a small delay between requests
        time.sleep(1)
    
    print("All hardware tests completed!")
    print("Note: To use IBM hardware, you must set the IBM_QUANTUM_TOKEN environment variable.")
    print("docker run -p {port}:{port} -e IBM_QUANTUM_TOKEN=your_token_here your-image-name")

if __name__ == "__main__":
    main()
"""
        hardware_test_path = os.path.join(test_dir, "test_hardware.py")
        with open(hardware_test_path, 'w') as hardware_file:
            hardware_file.write(hardware_test_content)
        
        # Make the hardware test script executable
        os.chmod(hardware_test_path, 0o755)
        logger.info(f"Created hardware test script at {hardware_test_path}")
    except Exception as e:
        logger.error(f"Failed to create test scripts: {e}")
        # Non-fatal error, continue with generation
    
    logger.info(f"Microservice generated successfully in {dest_dir}")
    print(f"Microservice generated successfully in {dest_dir}")
    print(f"To test the API, run:")
    print(f"  1. Start the microservice: docker run -p {port}:{port} [your-image-name]")
    print(f"  2. Execute the API test script: python {os.path.join(dest_dir, 'test', 'test_api.py')}")
    print(f"  3. Execute the hardware test script: python {os.path.join(dest_dir, 'test', 'test_hardware.py')}")
    print(f"     (For hardware tests, you'll need to provide the IBM_QUANTUM_TOKEN)")
    return True

if __name__ == "__main__":
    # For direct testing
    import argparse
    print("--- Running microservice.py generation directly (for testing) ---")
    parser = argparse.ArgumentParser(description="Generate Microservice")
    parser.add_argument("source_file", nargs='?', default=None, help="Path to source QASM file.")
    parser.add_argument("--dest-dir", default=None, help="Destination directory.")
    parser.add_argument("--app-root", default=None, help="App root override. Defaults to CWD.")
    args = parser.parse_args()

    app_root_main = args.app_root or os.getcwd()
    print(f"Source: {args.source_file or '(auto-detect)'}, Dest: {args.dest_dir or '(default)'}, AppRoot: {app_root_main}")

    print("\nStarting microservice generation...")
    success = generate_microservice(
        source_file=args.source_file, 
        dest_dir=args.dest_dir, 
        app_root=app_root_main
    )
    
    print("--- Generation Test Complete ---")
    sys.exit(0 if success else 1)
