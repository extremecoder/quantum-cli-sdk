"""
Provision infrastructure for quantum applications.
"""

import os
import sys
import logging
import json
import yaml
import subprocess
import tempfile
import shutil
import time
from pathlib import Path

from ..config import get_config
from ..utils import load_config
from ..output_formatter import format_output
from ..resource_management import provision_resource, deprovision_resource

# Set up logger
logger = logging.getLogger(__name__)

# Infrastructure provider types
PROVIDER_TYPES = ["local", "aws", "azure", "gcp", "ibm"]

# Default provider configurations
DEFAULT_PROVIDERS = {
    "local": {
        "type": "local",
        "simulator": "qiskit",
        "max_qubits": 32,
        "shots": 1024
    },
    "aws": {
        "type": "aws",
        "region": "us-east-1",
        "instance_type": "m5.xlarge",
        "simulator": "braket",
        "qpu": "SV1"
    },
    "azure": {
        "type": "azure",
        "location": "eastus",
        "resource_group": "quantum-rg",
        "workspace": "quantum-workspace"
    },
    "gcp": {
        "type": "gcp",
        "project": "quantum-project",
        "region": "us-central1",
        "service_account": "quantum-sa"
    },
    "ibm": {
        "type": "ibm",
        "instance": "ibmq_qasm_simulator",
        "provider": "ibm-q"
    }
}

def load_infrastructure_config(config_file):
    """
    Load infrastructure configuration from file.
    
    Args:
        config_file (str): Path to config file
        
    Returns:
        dict: Configuration data
    """
    try:
        # Determine file type from extension
        ext = os.path.splitext(config_file)[1].lower()
        
        if ext in ['.yaml', '.yml']:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
        elif ext == '.json':
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            logger.error(f"Unsupported config file format: {ext}")
            return None
            
        return config
        
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None

def validate_provider_config(provider, config):
    """
    Validate provider configuration.
    
    Args:
        provider (str): Provider type
        config (dict): Provider configuration
        
    Returns:
        bool: True if configuration is valid
    """
    if provider not in PROVIDER_TYPES:
        logger.error(f"Unsupported provider type: {provider}")
        return False
        
    # Validate required fields
    required_fields = {
        "local": ["simulator"],
        "aws": ["region"],
        "azure": ["location", "resource_group"],
        "gcp": ["project", "region"],
        "ibm": ["instance"]
    }
    
    for field in required_fields.get(provider, []):
        if field not in config:
            logger.error(f"Missing required field for {provider}: {field}")
            return False
            
    return True

def create_local_infrastructure(config, output_dir):
    """
    Create local infrastructure using Docker.
    
    Args:
        config (dict): Provider configuration
        output_dir (str): Output directory
        
    Returns:
        bool: True if creation was successful
    """
    try:
        logger.info("Creating local infrastructure with Docker")
        
        # Create docker-compose.yml
        docker_compose = {
            "version": "3",
            "services": {
                "quantum-simulator": {
                    "image": "quantum/simulator:latest",
                    "ports": ["8000:8000"],
                    "volumes": [
                        "./circuits:/app/circuits",
                        "./results:/app/results"
                    ],
                    "environment": [
                        f"SIMULATOR_TYPE={config.get('simulator', 'qiskit')}",
                        f"MAX_QUBITS={config.get('max_qubits', 32)}",
                        f"DEFAULT_SHOTS={config.get('shots', 1024)}"
                    ]
                },
                "quantum-api": {
                    "image": "quantum/api:latest",
                    "ports": ["8080:8080"],
                    "depends_on": ["quantum-simulator"],
                    "environment": [
                        "SIMULATOR_URL=http://quantum-simulator:8000"
                    ]
                }
            }
        }
        
        compose_file = os.path.join(output_dir, "docker-compose.yml")
        with open(compose_file, 'w') as f:
            yaml.dump(docker_compose, f, default_flow_style=False)
            
        # Create directories
        os.makedirs(os.path.join(output_dir, "circuits"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "results"), exist_ok=True)
        
        # Create README.md
        readme_file = os.path.join(output_dir, "README.md")
        with open(readme_file, 'w') as f:
            f.write(f"""# Local Quantum Infrastructure

This directory contains the configuration for a local quantum simulator infrastructure.

## Configuration

- Simulator: {config.get("simulator", "qiskit")}
- Max Qubits: {config.get("max_qubits", 32)}
- Default Shots: {config.get("shots", 1024)}

## Usage

To start the infrastructure:

```bash
docker-compose up -d
```

To stop the infrastructure:

```bash
docker-compose down
```

## API Endpoints

- Simulator API: http://localhost:8000
- Quantum API: http://localhost:8080
""")
        
        logger.info(f"Local infrastructure configuration created in {output_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating local infrastructure: {e}")
        return False

def create_aws_infrastructure(config, output_dir):
    """
    Create AWS infrastructure using Terraform.
    
    Args:
        config (dict): Provider configuration
        output_dir (str): Output directory
        
    Returns:
        bool: True if creation was successful
    """
    try:
        logger.info(f"Creating AWS infrastructure in {config.get('region', 'us-east-1')}")
        
        # Create main.tf
        tf_content = f"""
provider "aws" {{
  region = "{config.get('region', 'us-east-1')}"
}}

resource "aws_iam_role" "quantum_role" {{
  name = "{config.get('name', 'quantum')}_role"

  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {{
          Service = "braket.amazonaws.com"
        }}
      }},
    ]
  }})
}}

resource "aws_iam_role_policy_attachment" "quantum_policy" {{
  role       = aws_iam_role.quantum_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonBraketFullAccess"
}}

resource "aws_s3_bucket" "quantum_bucket" {{
  bucket = "{config.get('name', 'quantum')}-{config.get('region', 'us-east-1')}-{int(time.time())}"
}}

output "role_arn" {{
  value = aws_iam_role.quantum_role.arn
}}

output "bucket_name" {{
  value = aws_s3_bucket.quantum_bucket.bucket
}}
"""
        
        tf_file = os.path.join(output_dir, "main.tf")
        with open(tf_file, 'w') as f:
            f.write(tf_content)
            
        # Create terraform.tfvars
        tfvars_file = os.path.join(output_dir, "terraform.tfvars")
        with open(tfvars_file, 'w') as f:
            for key, value in config.items():
                if key not in ["type"]:
                    f.write(f'{key} = "{value}"\n')
                    
        # Create README.md
        readme_file = os.path.join(output_dir, "README.md")
        with open(readme_file, 'w') as f:
            f.write(f"""# AWS Quantum Infrastructure

This directory contains the Terraform configuration for AWS Braket quantum infrastructure.

## Configuration

- Region: {config.get("region", "us-east-1")}
- QPU: {config.get("qpu", "SV1")}

## Usage

To initialize Terraform:

```bash
terraform init
```

To see what resources will be created:

```bash
terraform plan
```

To create the infrastructure:

```bash
terraform apply
```

To destroy the infrastructure:

```bash
terraform destroy
```
""")
        
        logger.info(f"AWS infrastructure configuration created in {output_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating AWS infrastructure: {e}")
        return False

def create_azure_infrastructure(config, output_dir):
    """
    Create Azure infrastructure using Terraform.
    
    Args:
        config (dict): Provider configuration
        output_dir (str): Output directory
        
    Returns:
        bool: True if creation was successful
    """
    try:
        logger.info(f"Creating Azure infrastructure in {config.get('location', 'eastus')}")
        
        # Create main.tf
        tf_content = f"""
provider "azurerm" {{
  features {{}}
}}

resource "azurerm_resource_group" "quantum_rg" {{
  name     = "{config.get('resource_group', 'quantum-rg')}"
  location = "{config.get('location', 'eastus')}"
}}

resource "azurerm_quantum_workspace" "quantum_workspace" {{
  name                = "{config.get('workspace', 'quantum-workspace')}"
  location            = azurerm_resource_group.quantum_rg.location
  resource_group_name = azurerm_resource_group.quantum_rg.name

  storage_account {{
    name     = "{config.get('name', 'quantum')}storage"
    location = azurerm_resource_group.quantum_rg.location
  }}

  provider_sku {{
    provider_id = "microsoft"
    sku_id      = "basic"
  }}
}}

output "workspace_id" {{
  value = azurerm_quantum_workspace.quantum_workspace.id
}}
"""
        
        tf_file = os.path.join(output_dir, "main.tf")
        with open(tf_file, 'w') as f:
            f.write(tf_content)
            
        # Create terraform.tfvars
        tfvars_file = os.path.join(output_dir, "terraform.tfvars")
        with open(tfvars_file, 'w') as f:
            for key, value in config.items():
                if key not in ["type"]:
                    f.write(f'{key} = "{value}"\n')
                    
        # Create README.md
        readme_file = os.path.join(output_dir, "README.md")
        with open(readme_file, 'w') as f:
            f.write(f"""# Azure Quantum Infrastructure

This directory contains the Terraform configuration for Azure Quantum infrastructure.

## Configuration

- Location: {config.get("location", "eastus")}
- Resource Group: {config.get("resource_group", "quantum-rg")}
- Workspace: {config.get("workspace", "quantum-workspace")}

## Usage

To initialize Terraform:

```bash
terraform init
```

To see what resources will be created:

```bash
terraform plan
```

To create the infrastructure:

```bash
terraform apply
```

To destroy the infrastructure:

```bash
terraform destroy
```
""")
        
        logger.info(f"Azure infrastructure configuration created in {output_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating Azure infrastructure: {e}")
        return False

def provision_infrastructure(provider_type, config=None, config_file=None, output_dir=None, apply=False):
    """
    Provision infrastructure for quantum applications.
    
    Args:
        provider_type (str): Type of infrastructure provider
        config (dict, optional): Provider configuration
        config_file (str, optional): Path to config file
        output_dir (str, optional): Output directory
        apply (bool, optional): Whether to apply the configuration
        
    Returns:
        bool: True if provisioning was successful
    """
    # Set up logger
    setup_logger()
    
    logger.info(f"Provisioning {provider_type} infrastructure")
    
    # Load config from file if specified
    if config_file:
        loaded_config = load_infrastructure_config(config_file)
        if loaded_config:
            config = loaded_config
    
    # Use default config if not provided
    if not config:
        config = DEFAULT_PROVIDERS.get(provider_type, {})
    
    # Ensure provider type is set in config
    config["type"] = provider_type
    
    # Validate config
    if not validate_provider_config(provider_type, config):
        return False
    
    # Determine output directory
    if not output_dir:
        output_dir = os.path.join(os.getcwd(), f"quantum-{provider_type}-infra")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create provider-specific infrastructure
    success = False
    
    if provider_type == "local":
        success = create_local_infrastructure(config, output_dir)
    elif provider_type == "aws":
        success = create_aws_infrastructure(config, output_dir)
    elif provider_type == "azure":
        success = create_azure_infrastructure(config, output_dir)
    elif provider_type in ["gcp", "ibm"]:
        logger.error(f"Provisioning for {provider_type} is not yet implemented")
        return False
    
    # Apply the configuration if requested
    if success and apply:
        if provider_type == "local":
            try:
                logger.info("Starting local infrastructure")
                subprocess.run(
                    ["docker-compose", "up", "-d"],
                    cwd=output_dir,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                logger.info("Local infrastructure started successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Error starting local infrastructure: {e.stderr.decode()}")
                return False
        elif provider_type in ["aws", "azure"]:
            try:
                logger.info("Initializing Terraform")
                subprocess.run(
                    ["terraform", "init"],
                    cwd=output_dir,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                logger.info("Applying Terraform configuration")
                subprocess.run(
                    ["terraform", "apply", "-auto-approve"],
                    cwd=output_dir,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                logger.info(f"{provider_type.upper()} infrastructure provisioned successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Error applying Terraform configuration: {e.stderr.decode()}")
                return False
    
    return success

if __name__ == "__main__":
    # This allows the module to be run directly for testing
    if len(sys.argv) < 2:
        print("Usage: provision.py <provider_type> [--config <config_file>] [--output <output_dir>] [--apply]")
        sys.exit(1)
    
    # Parse arguments
    provider = sys.argv[1]
    config_file = None
    output_dir = None
    apply = False
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--config" and i+1 < len(sys.argv):
            config_file = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == "--output" and i+1 < len(sys.argv):
            output_dir = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == "--apply":
            apply = True
            i += 1
        else:
            i += 1
    
    # Run provisioning
    success = provision_infrastructure(provider, config_file=config_file, output_dir=output_dir, apply=apply)
    sys.exit(0 if success else 1)
