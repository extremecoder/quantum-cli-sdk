"""
Publish quantum packages to repositories.
"""

import os
import sys
import logging
import json
import yaml
import subprocess
import tempfile
import shutil
import requests
import zipfile
import tarfile
from pathlib import Path
from urllib.parse import urlparse

from ..config import get_config
from ..output_formatter import format_output
from ..utils import find_files, run_command

# Set up logger
logger = logging.getLogger(__name__)

# Default registry URL
DEFAULT_REGISTRY_URL = "https://quantum-hub.example.com/api/packages"

def extract_package_info(package_path):
    """
    Extract information from a package.
    
    Args:
        package_path (str): Path to the package file
        
    Returns:
        dict: Package information
    """
    try:
        ext = os.path.splitext(package_path)[1].lower()
        
        # Handle different package formats
        if ext == '.zip':
            with zipfile.ZipFile(package_path, 'r') as zipf:
                if 'quantum_manifest.json' in zipf.namelist():
                    with zipf.open('quantum_manifest.json') as f:
                        manifest = json.load(f)
                    return manifest
                else:
                    logger.error("quantum_manifest.json not found in package")
                    return None
                    
        elif ext in ['.gz', '.tgz']:
            with tarfile.open(package_path, 'r:gz') as tar:
                manifest_member = None
                for member in tar.getmembers():
                    if member.name == 'quantum_manifest.json':
                        manifest_member = member
                        break
                
                if manifest_member:
                    f = tar.extractfile(manifest_member)
                    manifest = json.load(f)
                    return manifest
                else:
                    logger.error("quantum_manifest.json not found in package")
                    return None
                    
        elif ext == '.whl':
            # For wheels, we need to inspect without extraction
            # This is a simplified approach
            temp_dir = tempfile.mkdtemp()
            try:
                # Use pip to show wheel metadata
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "show", "-f", package_path],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                # Parse output
                output = result.stdout
                package_info = {}
                for line in output.splitlines():
                    if ':' in line:
                        key, value = line.split(':', 1)
                        package_info[key.strip()] = value.strip()
                
                return {
                    "name": package_info.get("Name", "unknown"),
                    "version": package_info.get("Version", "0.0.0"),
                    "description": package_info.get("Summary", ""),
                    "author": package_info.get("Author", ""),
                    "package_type": "wheel"
                }
                
            finally:
                shutil.rmtree(temp_dir)
        else:
            logger.error(f"Unsupported package format: {ext}")
            return None
            
    except Exception as e:
        logger.error(f"Error extracting package info: {e}")
        return None

def login_to_registry(registry_url, username=None, password=None, token=None):
    """
    Login to package registry.
    
    Args:
        registry_url (str): Registry URL
        username (str, optional): Username
        password (str, optional): Password
        token (str, optional): API token
        
    Returns:
        dict: Authentication details
    """
    # Check for existing credentials
    config = get_config()
    
    if 'registries' in config:
        for reg in config.get('registries', []):
            if reg.get('url') == registry_url:
                logger.info(f"Using existing credentials for {registry_url}")
                return {
                    'token': reg.get('token'),
                    'username': reg.get('username')
                }
    
    # If credentials are provided directly, use them
    if token:
        return {'token': token}
    
    if username and password:
        # Try to authenticate and get token
        try:
            parsed_url = urlparse(registry_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            auth_url = f"{base_url}/api/auth/login"
            
            response = requests.post(
                auth_url,
                json={'username': username, 'password': password},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data:
                    # Save to config
                    if 'registries' not in config:
                        config['registries'] = []
                        
                    # Add or update registry entry
                    registry_found = False
                    for reg in config.get('registries', []):
                        if reg.get('url') == registry_url:
                            reg['token'] = data['token']
                            reg['username'] = username
                            registry_found = True
                            break
                            
                    if not registry_found:
                        config['registries'].append({
                            'url': registry_url,
                            'username': username,
                            'token': data['token']
                        })
                    
                    # Save updated config
                    from ..config import save_config
                    save_config(config)
                    
                    logger.info(f"Successfully logged in to {registry_url}")
                    return {'token': data['token'], 'username': username}
                else:
                    logger.error("Token not found in authentication response")
            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
    
    # If we reach here, authentication failed or wasn't attempted
    return None

def upload_to_registry(package_path, registry_url, auth, package_info=None):
    """
    Upload package to registry.
    
    Args:
        package_path (str): Path to package file
        registry_url (str): Registry URL
        auth (dict): Authentication details
        package_info (dict, optional): Package information
        
    Returns:
        bool: True if upload was successful
    """
    try:
        logger.info(f"Uploading package to {registry_url}")
        
        # Prepare upload URL
        if not registry_url.endswith('/'):
            registry_url += '/'
            
        upload_url = f"{registry_url}upload"
        
        # Prepare headers
        headers = {}
        if auth and 'token' in auth:
            headers['Authorization'] = f"Bearer {auth['token']}"
        
        # Prepare metadata
        if not package_info:
            package_info = extract_package_info(package_path)
            
        if not package_info:
            logger.error("Failed to extract package information")
            return False
        
        # Prepare files for upload
        files = {
            'package': (os.path.basename(package_path), open(package_path, 'rb'), 'application/octet-stream')
        }
        
        # Prepare metadata
        data = {
            'name': package_info.get('name', 'unknown'),
            'version': package_info.get('version', '0.0.0'),
            'description': package_info.get('description', ''),
            'author': package_info.get('author', '')
        }
        
        # Add extra metadata if available
        if 'metadata' in package_info:
            for key, value in package_info.get('metadata', {}).items():
                if key not in data:
                    data[key] = value
        
        # Make request
        response = requests.post(
            upload_url,
            headers=headers,
            data=data,
            files=files,
            timeout=300  # Longer timeout for large uploads
        )
        
        # Close file
        files['package'][1].close()
        
        # Check response
        if response.status_code in [200, 201]:
            logger.info(f"Package uploaded successfully: {response.json().get('message', '')}")
            return True
        else:
            logger.error(f"Upload failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error uploading package: {e}")
        return False

def publish_to_pypi(package_path, repository_url=None, username=None, password=None):
    """
    Publish Python wheel package to PyPI or a custom repository.
    
    Args:
        package_path (str): Path to wheel package
        repository_url (str, optional): Repository URL
        username (str, optional): Username
        password (str, optional): Password
        
    Returns:
        bool: True if publish was successful
    """
    try:
        logger.info(f"Publishing wheel package to {'PyPI' if not repository_url else repository_url}")
        
        # Check if package is a wheel
        if not package_path.endswith('.whl'):
            logger.error("Only wheel packages can be published to PyPI")
            return False
        
        # Prepare twine command
        cmd = [sys.executable, "-m", "twine", "upload"]
        
        # Add repository URL if specified
        if repository_url:
            cmd.extend(["--repository-url", repository_url])
        
        # Add credentials if provided
        if username and password:
            cmd.extend(["--username", username, "--password", password])
        
        # Add package path
        cmd.append(package_path)
        
        # Run twine
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check result
        if result.returncode == 0:
            logger.info("Package published successfully to PyPI")
            return True
        else:
            logger.error(f"Failed to publish to PyPI: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error publishing to PyPI: {e}")
        return False

def publish(package_path, registry_url=None, username=None, password=None, token=None, pypi=False, repository_url=None):
    """
    Publish a quantum package to a registry.
    
    Args:
        package_path (str): Path to package file
        registry_url (str, optional): Registry URL
        username (str, optional): Username for registry
        password (str, optional): Password for registry
        token (str, optional): API token for registry
        pypi (bool, optional): Whether to publish to PyPI
        repository_url (str, optional): PyPI repository URL
        
    Returns:
        bool: True if publish was successful
    """
    # Set up logger
    setup_logger()
    
    logger.info(f"Publishing quantum package: {package_path}")
    
    # Ensure package file exists
    if not os.path.isfile(package_path):
        logger.error(f"Package file not found: {package_path}")
        return False
    
    # Extract package info
    package_info = extract_package_info(package_path)
    if not package_info:
        logger.error("Failed to extract package information")
        return False
    
    success = True
    
    # Publish to quantum package registry if specified
    if registry_url or not pypi:
        # Use default registry if not specified
        if not registry_url:
            registry_url = DEFAULT_REGISTRY_URL
            
        # Login to registry
        auth = login_to_registry(registry_url, username, password, token)
        if not auth:
            logger.error("Failed to authenticate with registry")
            return False
            
        # Upload package
        success = success and upload_to_registry(package_path, registry_url, auth, package_info)
    
    # Publish to PyPI if specified
    if pypi and package_path.endswith('.whl'):
        success = success and publish_to_pypi(package_path, repository_url, username, password)
    
    return success

if __name__ == "__main__":
    # This allows the module to be run directly for testing
    if len(sys.argv) < 2:
        print("Usage: publish.py <package_file> [--registry <url>] [--username <username>] [--password <password>] [--token <token>] [--pypi] [--repository <url>]")
        sys.exit(1)
    
    # Parse arguments
    package_file = sys.argv[1]
    registry = None
    username = None
    password = None
    token = None
    pypi = False
    repository = None
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--registry" and i+1 < len(sys.argv):
            registry = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == "--username" and i+1 < len(sys.argv):
            username = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == "--password" and i+1 < len(sys.argv):
            password = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == "--token" and i+1 < len(sys.argv):
            token = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == "--pypi":
            pypi = True
            i += 1
        elif sys.argv[i] == "--repository" and i+1 < len(sys.argv):
            repository = sys.argv[i+1]
            i += 2
        else:
            i += 1
    
    # Run publish
    success = publish(package_file, registry, username, password, token, pypi, repository)
    sys.exit(0 if success else 1)
