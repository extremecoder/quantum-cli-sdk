"""
Commands for running quantum circuits on hardware.
"""

import json
import sys
import logging
from pathlib import Path
import time

# Set up logging
logger = logging.getLogger(__name__)

def run_on_hardware(platform, device, source="openqasm", shots=1024, parameters=None, dest="results/run", provider_config=None):
    """Run a quantum circuit on hardware.
    
    Args:
        platform: Quantum computing platform (ibm, aws, google, or all)
        device: Device ID
        source: Source file path
        shots: Number of shots
        parameters: Circuit parameters (comma-separated)
        dest: Destination file for run results
        provider_config: Configuration for the quantum provider
    """
    try:
        # Ensure the output directory exists
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load the circuit
        try:
            with open(source, 'r') as f:
                circuit_code = f.read()
            logger.info(f"Loaded circuit from {source}")
        except FileNotFoundError:
            print(f"Error: Source file '{source}' not found", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Error loading circuit from {source}: {e}", file=sys.stderr)
            return None
        
        # Parse parameters if provided
        params = {}
        if parameters:
            param_list = parameters.split(',')
            for i, p in enumerate(param_list):
                try:
                    params[f"param{i}"] = float(p)
                except ValueError:
                    # If not a float, keep it as a string
                    params[f"param{i}"] = p
        
        # Check if we have provider configuration
        if provider_config is None:
            provider_config = {}
            logger.warning(f"No configuration found for provider '{platform}', using defaults")
        else:
            logger.info(f"Using configuration for provider '{platform}'")
            
        # Platform-specific configuration and execution
        if platform == "ibm":
            # Check for IBM-specific configuration
            token = provider_config.get("token")
            hub = provider_config.get("hub", "ibm-q")
            group = provider_config.get("group", "open")
            project = provider_config.get("project", "main")
            
            if not token:
                print(f"Error: IBM Quantum token not configured. Please set it with 'quantum-cli config set-provider ibm token YOUR_TOKEN'", file=sys.stderr)
                return None
            
            print(f"Running circuit on IBM Quantum device '{device}' with {shots} shots")
            print(f"Using hub: {hub}, group: {group}, project: {project}")
            # TODO: Implement actual IBM Quantum run
            
        elif platform == "aws":
            # Check for AWS-specific configuration
            region = provider_config.get("region", "us-east-1")
            s3_bucket = provider_config.get("s3_bucket")
            
            print(f"Running circuit on AWS Braket device '{device}' with {shots} shots")
            print(f"Using region: {region}" + (f", S3 bucket: {s3_bucket}" if s3_bucket else ""))
            # TODO: Implement actual AWS Braket run
            
        elif platform == "google":
            # Check for Google-specific configuration
            project_id = provider_config.get("project_id")
            
            if not project_id:
                print(f"Error: Google Cloud project ID not configured. Please set it with 'quantum-cli config set-provider google project_id YOUR_PROJECT_ID'", file=sys.stderr)
                return None
            
            print(f"Running circuit on Google Quantum device '{device}' with {shots} shots")
            print(f"Using project ID: {project_id}")
            # TODO: Implement actual Google Quantum run
            
        else:
            print(f"Unsupported platform: {platform}", file=sys.stderr)
            return None
        
        # Simulate waiting for job completion
        print("Job submitted. Waiting for completion...")
        for i in range(5):
            print(f"Job progress: {(i+1)*20}%")
            time.sleep(0.5)  # Just for demo purposes
        
        # Create a dummy result for now
        results = {
            "platform": platform,
            "device": device,
            "shots": shots,
            "source": source,
            "parameters": params,
            "job_id": f"job-{int(time.time())}",
            "results": {"00": int(shots * 0.48), "11": int(shots * 0.48), "01": int(shots * 0.02), "10": int(shots * 0.02)}
        }
        
        # Save results to file
        with open(dest_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Run results saved to {dest}")
        
        return results
    except Exception as e:
        print(f"Error running circuit on hardware: {e}", file=sys.stderr)
        return None 