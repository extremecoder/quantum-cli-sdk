"""
Tests for the microservice command.
"""

import os
import sys
import pytest
import tempfile
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from quantum_cli_sdk.commands import microservice

# Sample QASM code for testing
SAMPLE_QASM = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q -> c;
"""

class TestMicroserviceCommand:
    """Test cases for the microservice command."""
    
    def setup_method(self):
        """Set up the test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.qasm_file = os.path.join(self.temp_dir, "test_circuit.qasm")
        
        # Create a test QASM file
        with open(self.qasm_file, "w") as f:
            f.write(SAMPLE_QASM)
    
    def teardown_method(self):
        """Clean up the test environment."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_generate_microservice(self):
        """Test generating a microservice from a QASM file."""
        output_dir = os.path.join(self.temp_dir, "microservice")
        
        # Call the generate_microservice function
        result = microservice.generate_microservice(
            source_file=self.qasm_file,
            dest_dir=output_dir,
            port=9000
        )
        
        # Check that the function returned success
        assert result is True
        
        # Check that the output directory was created
        assert os.path.exists(output_dir)
        
        # Check that all required files were created
        assert os.path.exists(os.path.join(output_dir, "app.py"))
        assert os.path.exists(os.path.join(output_dir, "Dockerfile"))
        assert os.path.exists(os.path.join(output_dir, "requirements.txt"))
        assert os.path.exists(os.path.join(output_dir, "README.md"))
        
        # Check that the circuit directory was created
        assert os.path.exists(os.path.join(output_dir, "circuits"))
        
        # Check that the circuit file was copied
        assert os.path.exists(os.path.join(output_dir, "circuits", "test_circuit.qasm"))
        
        # Check that the Dockerfile contains the specified port
        with open(os.path.join(output_dir, "Dockerfile"), "r") as f:
            dockerfile_content = f.read()
            assert "EXPOSE 9000" in dockerfile_content
            assert "--port", "9000" in dockerfile_content
    
    def test_generate_microservice_file_not_found(self):
        """Test generating a microservice with a nonexistent file."""
        output_dir = os.path.join(self.temp_dir, "microservice")
        
        # Call the generate_microservice function with a nonexistent file
        result = microservice.generate_microservice(
            source_file=os.path.join(self.temp_dir, "nonexistent.qasm"),
            dest_dir=output_dir
        )
        
        # Check that the function returned failure
        assert result is False
        
    def test_extract_circuit_info(self):
        """Test extracting circuit information from a QASM file."""
        # Call the extract_circuit_info function
        circuit_info = microservice.extract_circuit_info(self.qasm_file)
        
        # Check that the function returned a dictionary
        assert isinstance(circuit_info, dict)
        
        # Check that the dictionary contains the expected keys
        assert "name" in circuit_info
        assert "qreg_count" in circuit_info
        assert "creg_count" in circuit_info
        assert "gate_types" in circuit_info
        assert "operations" in circuit_info or "has_measurements" in circuit_info
        
        # Check that the circuit information is correct
        assert circuit_info["name"] == "test_circuit"
        assert circuit_info["qreg_count"] == 2
        assert circuit_info["creg_count"] == 2
        assert "h" in circuit_info["gate_types"]
        assert "cx" in circuit_info["gate_types"]
        assert "measure" in circuit_info["gate_types"]
        assert circuit_info["has_measurements"] is True
    
    @patch("requests.post")
    def test_call_llm_for_implementation(self, mock_post):
        """Test calling an LLM for implementation."""
        # Mock the response from the LLM service
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "implementation": "# Implementation code",
            "documentation": "# Documentation"
        }
        mock_post.return_value = mock_response
        
        # Call the call_llm_for_implementation function
        result = microservice.call_llm_for_implementation(self.qasm_file, "http://example.com/llm")
        
        # Check that the function returned the expected result
        assert result["implementation"] == "# Implementation code"
        assert result["documentation"] == "# Documentation"
        
        # Check that the requests.post function was called with the expected arguments
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "http://example.com/llm"
        assert "json" in kwargs
        assert "circuit_qasm" in kwargs["json"] or "qasm_content" in kwargs["json"]
    
    @patch("requests.post")
    def test_call_llm_for_implementation_error(self, mock_post):
        """Test calling an LLM for implementation with an error."""
        # Mock the response from the LLM service
        mock_post.side_effect = Exception("Connection error")
        
        # Call the call_llm_for_implementation function
        result = microservice.call_llm_for_implementation(self.qasm_file, "http://example.com/llm")
        
        # Check that the function returned None
        assert result is None 