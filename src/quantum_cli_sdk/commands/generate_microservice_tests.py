"""
Generate tests for quantum microservices.
"""

import os
import sys
import logging
import json
import re
import requests
import tempfile
import time
from pathlib import Path
from http import HTTPStatus

from ..config import get_config
from ..microservice_generator import MicroserviceGenerator
from ..output_formatter import format_output
from ..test_framework import generate_microservice_tests

# Set up logger
logger = logging.getLogger(__name__)

# Default test templates for different endpoints
DEFAULT_API_TEST_TEMPLATES = {
    "health": {
        "name": "test_health_endpoint",
        "description": "Test the health endpoint",
        "method": "GET",
        "endpoint": "/health",
        "expected_status": HTTPStatus.OK,
        "response_check": "assert response.json().get('status') == 'healthy'"
    },
    "run_circuit": {
        "name": "test_run_circuit_endpoint",
        "description": "Test the run circuit endpoint",
        "method": "POST",
        "endpoint": "/circuits/run",
        "expected_status": HTTPStatus.ACCEPTED,
        "response_check": "assert 'job_id' in response.json()"
    },
    "get_job_status": {
        "name": "test_job_status_endpoint",
        "description": "Test the job status endpoint",
        "method": "GET",
        "endpoint": "/jobs/{job_id}/status",
        "expected_status": HTTPStatus.OK,
        "response_check": "assert response.json().get('status') in ['queued', 'running', 'completed', 'failed']"
    },
    "get_job_results": {
        "name": "test_job_results_endpoint",
        "description": "Test the job results endpoint",
        "method": "GET",
        "endpoint": "/jobs/{job_id}/results",
        "expected_status": HTTPStatus.OK,
        "response_check": "assert 'counts' in response.json() or 'results' in response.json()"
    },
    "list_jobs": {
        "name": "test_list_jobs_endpoint",
        "description": "Test the list jobs endpoint",
        "method": "GET",
        "endpoint": "/jobs",
        "expected_status": HTTPStatus.OK,
        "response_check": "assert isinstance(response.json(), list)"
    },
    "delete_job": {
        "name": "test_delete_job_endpoint",
        "description": "Test the delete job endpoint",
        "method": "DELETE",
        "endpoint": "/jobs/{job_id}",
        "expected_status": HTTPStatus.OK,
        "response_check": "assert response.json().get('status') == 'deleted'"
    }
}

def extract_endpoints_from_file(api_file):
    """
    Extract API endpoints from a FastAPI application file.
    
    Args:
        api_file (str): Path to the FastAPI application file
        
    Returns:
        dict: Dictionary of endpoints with their details
    """
    endpoints = {}
    
    try:
        with open(api_file, 'r') as f:
            content = f.read()
            
        # Extract route decorators
        route_pattern = r'@app\.(?:get|post|put|delete)\([\'"]([^\'"]+)[\'"]\)'
        routes = re.findall(route_pattern, content)
        
        # Extract function names associated with routes
        for route in routes:
            # Find the function definition after the route
            pattern = fr'@app\.(?:get|post|put|delete)\([\'"]({re.escape(route)})[\'"]\)[^\n]*\ndef ([^\(]+)\('
            matches = re.findall(pattern, content)
            
            if matches:
                for match in matches:
                    path, func_name = match
                    
                    # Determine HTTP method
                    method_pattern = fr'@app\.(get|post|put|delete)\([\'"]({re.escape(path)})[\'"]'
                    method_match = re.search(method_pattern, content)
                    method = method_match.group(1).upper() if method_match else "GET"
                    
                    # Generate a key for the endpoint
                    key = func_name.strip()
                    
                    # Extract docstring if available
                    docstring_pattern = fr'def {re.escape(func_name)}\([^\)]*\):\s*[\'"]{3}([^\'"]+)[\'"]{3}'
                    docstring_match = re.search(docstring_pattern, content)
                    description = docstring_match.group(1).strip() if docstring_match else f"Test the {func_name} endpoint"
                    
                    endpoints[key] = {
                        "name": f"test_{func_name}",
                        "description": description,
                        "method": method,
                        "endpoint": path,
                        "expected_status": HTTPStatus.OK,
                        "response_check": "assert response.status_code == 200"
                    }
        
        logger.info(f"Extracted {len(endpoints)} endpoints from {api_file}")
        return endpoints
        
    except Exception as e:
        logger.error(f"Error extracting endpoints from {api_file}: {e}")
        return {}

def generate_pytest_test(endpoint, base_url="http://localhost:8000"):
    """
    Generate a pytest test for an API endpoint.
    
    Args:
        endpoint (dict): Endpoint details
        base_url (str): Base URL for the API
        
    Returns:
        str: Generated test code
    """
    # Handle path parameters
    has_path_params = "{" in endpoint["endpoint"] and "}" in endpoint["endpoint"]
    
    if has_path_params:
        # Extract parameter names from the path
        path_params = re.findall(r'{([^}]+)}', endpoint["endpoint"])
        param_fixtures = "\n".join([f"    {param} = '123e4567-e89b-12d3-a456-426614174000'  # Example UUID" for param in path_params])
        
        # Replace path parameters in the endpoint URL
        url = f'f"{endpoint["endpoint"]}"'
    else:
        param_fixtures = ""
        url = f'"{endpoint["endpoint"]}"'
    
    if endpoint["method"] == "GET":
        if has_path_params:
            request_code = f'response = client.get(base_url + {url})'
        else:
            request_code = f'response = client.get(base_url + {url})'
    elif endpoint["method"] == "POST":
        if has_path_params:
            request_code = f'response = client.post(base_url + {url}, json=data)'
        else:
            request_code = f'response = client.post(base_url + {url}, json=data)'
    elif endpoint["method"] == "PUT":
        if has_path_params:
            request_code = f'response = client.put(base_url + {url}, json=data)'
        else:
            request_code = f'response = client.put(base_url + {url}, json=data)'
    elif endpoint["method"] == "DELETE":
        if has_path_params:
            request_code = f'response = client.delete(base_url + {url})'
        else:
            request_code = f'response = client.delete(base_url + {url})'
    else:
        request_code = f'response = client.get(base_url + {url})'
    
    # Add data for POST/PUT requests
    data_setup = ""
    if endpoint["method"] in ["POST", "PUT"]:
        if "circuit" in endpoint["endpoint"].lower() or "run" in endpoint["endpoint"].lower():
            data_setup = '''    # Example quantum circuit in QASM format
    data = {
        "circuit": "OPENQASM 2.0;\\ninclude \\"qelib1.inc\\";\\nqreg q[2];\\ncreg c[2];\\nh q[0];\\ncx q[0],q[1];\\nmeasure q -> c;",
        "shots": 1024,
        "backend": "qiskit"
    }'''
        else:
            data_setup = '''    # Example data payload
    data = {
        "key": "value"
    }'''
    
    test_code = f'''def {endpoint["name"]}(client, base_url):
    """{endpoint["description"]}"""
{param_fixtures}
{data_setup}
    
    # Send request
    {request_code}
    
    # Check response
    assert response.status_code == {endpoint["expected_status"].value}
    {endpoint["response_check"]}
'''
    return test_code

def generate_locust_test(endpoints, api_name="QuantumAPI"):
    """
    Generate Locust load test for API endpoints.
    
    Args:
        endpoints (dict): Dictionary of endpoints
        api_name (str): Name of the API
        
    Returns:
        str: Generated Locust test code
    """
    task_methods = []
    
    for key, endpoint in endpoints.items():
        method = endpoint["method"].lower()
        path = endpoint["endpoint"]
        
        if method == "get":
            if "{" in path:
                # Path has parameters
                path_params = re.findall(r'{([^}]+)}', path)
                param_values = ", ".join([f'"{param}": "123e4567-e89b-12d3-a456-426614174000"' for param in path_params])
                task_code = f'''    @task
    def {key.lower()}(self):
        path_params = {{{param_values}}}
        formatted_path = "{path}"
        for param_name, param_value in path_params.items():
            formatted_path = formatted_path.replace(f"{{{{{param_name}}}}}", param_value)
        self.client.get(formatted_path, name="{path}")'''
            else:
                task_code = f'''    @task
    def {key.lower()}(self):
        self.client.get("{path}")'''
        
        elif method == "post":
            if "circuit" in path.lower() or "run" in path.lower():
                payload = '''{"circuit": "OPENQASM 2.0;\\ninclude \\"qelib1.inc\\";\\nqreg q[2];\\ncreg c[2];\\nh q[0];\\ncx q[0],q[1];\\nmeasure q -> c;", "shots": 1024, "backend": "qiskit"}'''
            else:
                payload = '''{"key": "value"}'''
                
            task_code = f'''    @task
    def {key.lower()}(self):
        self.client.post("{path}", json={payload})'''
        
        elif method == "put":
            payload = '''{"key": "value"}'''
            
            if "{" in path:
                # Path has parameters
                path_params = re.findall(r'{([^}]+)}', path)
                param_values = ", ".join([f'"{param}": "123e4567-e89b-12d3-a456-426614174000"' for param in path_params])
                task_code = f'''    @task
    def {key.lower()}(self):
        path_params = {{{param_values}}}
        formatted_path = "{path}"
        for param_name, param_value in path_params.items():
            formatted_path = formatted_path.replace(f"{{{{{param_name}}}}}", param_value)
        self.client.put(formatted_path, json={payload}, name="{path}")'''
            else:
                task_code = f'''    @task
    def {key.lower()}(self):
        self.client.put("{path}", json={payload})'''
        
        elif method == "delete":
            if "{" in path:
                # Path has parameters
                path_params = re.findall(r'{([^}]+)}', path)
                param_values = ", ".join([f'"{param}": "123e4567-e89b-12d3-a456-426614174000"' for param in path_params])
                task_code = f'''    @task
    def {key.lower()}(self):
        path_params = {{{param_values}}}
        formatted_path = "{path}"
        for param_name, param_value in path_params.items():
            formatted_path = formatted_path.replace(f"{{{{{param_name}}}}}", param_value)
        self.client.delete(formatted_path, name="{path}")'''
            else:
                task_code = f'''    @task
    def {key.lower()}(self):
        self.client.delete("{path}")'''
        
        else:
            continue
            
        task_methods.append(task_code)
    
    tasks_str = "\n\n".join(task_methods)
    
    locust_code = f'''from locust import HttpUser, task, between

class {api_name}User(HttpUser):
    wait_time = between(1, 3)
    
{tasks_str}
'''
    return locust_code

def generate_pytest_fixture():
    """Generate pytest fixture code for API tests."""
    
    return '''import pytest
import requests
import os
import time

@pytest.fixture
def base_url():
    """Get the base URL for the API."""
    return os.environ.get("API_BASE_URL", "http://localhost:8000")

@pytest.fixture
def client():
    """Create a requests session for API testing."""
    with requests.Session() as session:
        yield session
'''

def generate_conftest():
    """Generate conftest.py content."""
    
    return '''import pytest
import os
import requests
import time
import subprocess
import signal

@pytest.fixture(scope="session")
def api_service():
    """Start the API service for testing, if needed."""
    if os.environ.get("NO_SERVICE_FIXTURE") == "1":
        # Skip starting service if environment variable is set
        yield
        return
        
    # Start API service (customize as needed)
    try:
        process = subprocess.Popen(
            ["python", "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        # Wait for service to start
        base_url = "http://localhost:8000"
        max_retries = 30
        retries = 0
        while retries < max_retries:
            try:
                response = requests.get(f"{base_url}/health")
                if response.status_code == 200:
                    break
            except requests.RequestException:
                pass
                
            time.sleep(1)
            retries += 1
            
        if retries >= max_retries:
            raise Exception("API service failed to start")
            
        # Service is running
        yield
    finally:
        # Stop the service
        process.send_signal(signal.SIGTERM)
        process.wait(timeout=5)

@pytest.fixture
def base_url():
    """Get the base URL for the API."""
    return os.environ.get("API_BASE_URL", "http://localhost:8000")

@pytest.fixture
def client():
    """Create a requests session for API testing."""
    with requests.Session() as session:
        yield session
'''

def generate_requirements():
    """Generate requirements.txt for tests."""
    
    return '''pytest==7.3.1
requests==2.31.0
locust==2.15.1
'''

def generate_microservice_tests(microservice_dir, output_dir=None):
    """
    Generate tests for a quantum microservice.
    
    Args:
        microservice_dir (str): Path to the microservice directory
        output_dir (str, optional): Output directory for tests
        
    Returns:
        bool: True if successful
    """
    # Set up logger
    setup_logger()
    
    logger.info(f"Generating tests for microservice in {microservice_dir}")
    
    # Check if directory exists
    if not os.path.exists(microservice_dir):
        logger.error(f"Microservice directory does not exist: {microservice_dir}")
        return False
    
    # Find the main API file
    api_file = None
    for filename in ["app.py", "main.py", "api.py"]:
        potential_file = os.path.join(microservice_dir, filename)
        if os.path.exists(potential_file):
            api_file = potential_file
            break
    
    if not api_file:
        logger.error(f"Could not find API file in {microservice_dir}")
        return False
    
    # Determine output directory
    if not output_dir:
        output_dir = os.path.join(microservice_dir, "tests")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract endpoints from API file
    endpoints = extract_endpoints_from_file(api_file)
    
    # If no endpoints were found, use defaults
    if not endpoints:
        logger.warning(f"No endpoints found in {api_file}, using default templates")
        endpoints = DEFAULT_API_TEST_TEMPLATES
    
    # Generate test files
    test_files = {}
    
    # Generate pytest tests
    pytest_tests = []
    
    # Add imports
    pytest_tests.append("import pytest\nimport requests\nimport json\n\n")
    
    # Generate test functions
    for key, endpoint in endpoints.items():
        pytest_tests.append(generate_pytest_test(endpoint))
    
    test_files["test_api.py"] = "\n".join(pytest_tests)
    
    # Generate pytest fixture
    test_files["conftest.py"] = generate_conftest()
    
    # Generate Locust load test
    test_files["locustfile.py"] = generate_locust_test(endpoints)
    
    # Generate requirements.txt
    test_files["requirements.txt"] = generate_requirements()
    
    # Generate README.md
    readme_content = f"""# Microservice API Tests

This directory contains tests for the quantum microservice API.

## Running the tests

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the tests:
   ```
   pytest
   ```

3. Run load tests:
   ```
   locust -f locustfile.py --host=http://localhost:8000
   ```

## Test files

- `test_api.py`: API endpoint tests
- `conftest.py`: Pytest fixtures
- `locustfile.py`: Locust load tests
"""
    test_files["README.md"] = readme_content
    
    # Write files
    for filename, content in test_files.items():
        file_path = os.path.join(output_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        logger.info(f"Generated {file_path}")
    
    logger.info(f"Successfully generated tests in {output_dir}")
    
    return True

if __name__ == "__main__":
    # This allows the module to be run directly for testing
    if len(sys.argv) < 2:
        print("Usage: generate_microservice_tests.py <microservice_dir> [--output <output_dir>]")
        sys.exit(1)
    
    # Parse arguments
    microservice_dir = sys.argv[1]
    output_dir = None
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--output" and i+1 < len(sys.argv):
            output_dir = sys.argv[i+1]
            i += 2
        else:
            i += 1
    
    # Generate tests
    success = generate_microservice_tests(microservice_dir, output_dir)
    sys.exit(0 if success else 1) 