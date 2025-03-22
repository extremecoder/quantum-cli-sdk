#!/usr/bin/env python3
"""
Quantum Circuit Versioning System for tracking changes to quantum circuits.

This module provides functionality to:
- Initialize a version control repository for quantum circuits
- Track changes to quantum circuits
- Manage versions with commit messages
- Roll back to previous versions
- Compare different versions of circuits
"""

import os
import json
import uuid
import hashlib
import datetime
import shutil
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple, Any, Union

logger = logging.getLogger(__name__)

class CircuitVersion:
    """Represents a single version of a quantum circuit."""
    
    def __init__(self, 
                 version_id: str, 
                 parent_id: Optional[str], 
                 circuit_hash: str,
                 message: str, 
                 timestamp: float,
                 author: str,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a circuit version.
        
        Args:
            version_id: Unique identifier for this version
            parent_id: ID of the parent version (None for initial version)
            circuit_hash: Hash of the circuit content
            message: Commit message describing the change
            timestamp: Creation time as Unix timestamp
            author: Author of this version
            metadata: Additional information about this version
        """
        self.version_id = version_id
        self.parent_id = parent_id
        self.circuit_hash = circuit_hash
        self.message = message
        self.timestamp = timestamp
        self.author = author
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation for storage."""
        return {
            "version_id": self.version_id,
            "parent_id": self.parent_id,
            "circuit_hash": self.circuit_hash,
            "message": self.message,
            "timestamp": self.timestamp,
            "author": self.author,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CircuitVersion':
        """Create a CircuitVersion from a dictionary."""
        return cls(
            version_id=data["version_id"],
            parent_id=data["parent_id"],
            circuit_hash=data["circuit_hash"],
            message=data["message"],
            timestamp=data["timestamp"],
            author=data["author"],
            metadata=data.get("metadata", {})
        )
    
    def __str__(self) -> str:
        """String representation of the version."""
        dt = datetime.datetime.fromtimestamp(self.timestamp)
        date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        return f"Version {self.version_id[:8]} ({date_str}) by {self.author}: {self.message}"


class CircuitVersionControl:
    """Manages version control for quantum circuits."""
    
    def __init__(self, repo_path: str):
        """
        Initialize the version control system.
        
        Args:
            repo_path: Path to the repository directory
        """
        self.repo_path = Path(repo_path)
        self.versions_dir = self.repo_path / "versions"
        self.circuits_dir = self.repo_path / "circuits"
        self.index_file = self.repo_path / "index.json"
        self.head_file = self.repo_path / "HEAD"
        self.config_file = self.repo_path / "config.json"
        
        # Default configuration
        self.config = {
            "author": os.environ.get("USER", "unknown"),
            "remote_url": None,
            "auto_commit": False
        }
        
        # Index mapping circuit names to their current version IDs
        self.index = {}
        
        # HEAD points to the current version for each circuit
        self.head = {}
        
        # Dictionary of loaded versions
        self.loaded_versions = {}
        
    def init(self, author: Optional[str] = None) -> bool:
        """
        Initialize a new repository.
        
        Args:
            author: Author name for future commits
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create repository structure
            self.repo_path.mkdir(exist_ok=True)
            self.versions_dir.mkdir(exist_ok=True)
            self.circuits_dir.mkdir(exist_ok=True)
            
            # Set author if provided
            if author:
                self.config["author"] = author
                
            # Save initial config
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            # Initialize empty index
            with open(self.index_file, 'w') as f:
                json.dump({}, f, indent=2)
                
            # Initialize empty HEAD
            with open(self.head_file, 'w') as f:
                json.dump({}, f, indent=2)
                
            logger.info(f"Initialized version control repository at {self.repo_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize repository: {e}")
            return False
    
    def load(self) -> bool:
        """
        Load the repository information.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if repository exists
            if not self.repo_path.exists():
                logger.error(f"Repository at {self.repo_path} does not exist")
                return False
                
            # Load config
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                    
            # Load index
            if self.index_file.exists():
                with open(self.index_file, 'r') as f:
                    self.index = json.load(f)
                    
            # Load HEAD
            if self.head_file.exists():
                with open(self.head_file, 'r') as f:
                    self.head = json.load(f)
                    
            logger.info(f"Loaded version control repository from {self.repo_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load repository: {e}")
            return False
    
    def save_state(self) -> bool:
        """
        Save the current repository state.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Save index
            with open(self.index_file, 'w') as f:
                json.dump(self.index, f, indent=2)
                
            # Save HEAD
            with open(self.head_file, 'w') as f:
                json.dump(self.head, f, indent=2)
                
            # Save config
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to save repository state: {e}")
            return False
    
    def compute_hash(self, content: str) -> str:
        """
        Compute the hash of circuit content.
        
        Args:
            content: Circuit content (e.g., OpenQASM code)
            
        Returns:
            Hash of the content
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def get_circuit_path(self, circuit_hash: str) -> Path:
        """
        Get the path to a circuit file.
        
        Args:
            circuit_hash: Hash of the circuit
            
        Returns:
            Path to the circuit file
        """
        return self.circuits_dir / f"{circuit_hash}.qasm"
    
    def get_version_path(self, version_id: str) -> Path:
        """
        Get the path to a version file.
        
        Args:
            version_id: ID of the version
            
        Returns:
            Path to the version file
        """
        return self.versions_dir / f"{version_id}.json"
    
    def commit(self, 
               circuit_name: str, 
               content: str, 
               message: str, 
               author: Optional[str] = None,
               metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Commit a new version of a circuit.
        
        Args:
            circuit_name: Name of the circuit
            content: Circuit content (e.g., OpenQASM code)
            message: Commit message
            author: Author of this commit (defaults to configured author)
            metadata: Additional metadata for this version
            
        Returns:
            Version ID if successful, None otherwise
        """
        try:
            # Generate hash for the circuit content
            circuit_hash = self.compute_hash(content)
            
            # Check if this exact circuit already exists
            if circuit_name in self.index:
                current_version_id = self.index[circuit_name]
                current_version = self.get_version(current_version_id)
                
                if current_version and current_version.circuit_hash == circuit_hash:
                    logger.info(f"No changes detected for circuit '{circuit_name}'")
                    return current_version_id
            
            # Write circuit content to file
            circuit_path = self.get_circuit_path(circuit_hash)
            circuit_path.parent.mkdir(exist_ok=True)
            
            with open(circuit_path, 'w') as f:
                f.write(content)
            
            # Create version object
            version_id = str(uuid.uuid4())
            parent_id = self.index.get(circuit_name)
            timestamp = datetime.datetime.now().timestamp()
            author_name = author or self.config["author"]
            
            version = CircuitVersion(
                version_id=version_id,
                parent_id=parent_id,
                circuit_hash=circuit_hash,
                message=message,
                timestamp=timestamp,
                author=author_name,
                metadata=metadata
            )
            
            # Save version to file
            version_path = self.get_version_path(version_id)
            with open(version_path, 'w') as f:
                json.dump(version.to_dict(), f, indent=2)
            
            # Update index and HEAD
            self.index[circuit_name] = version_id
            self.head[circuit_name] = version_id
            self.save_state()
            
            logger.info(f"Committed version {version_id[:8]} for circuit '{circuit_name}': {message}")
            return version_id
            
        except Exception as e:
            logger.error(f"Failed to commit: {e}")
            return None
    
    def get_version(self, version_id: str) -> Optional[CircuitVersion]:
        """
        Get a specific version.
        
        Args:
            version_id: ID of the version
            
        Returns:
            CircuitVersion object if found, None otherwise
        """
        if version_id in self.loaded_versions:
            return self.loaded_versions[version_id]
            
        try:
            version_path = self.get_version_path(version_id)
            
            if not version_path.exists():
                logger.error(f"Version {version_id} not found")
                return None
                
            with open(version_path, 'r') as f:
                version_data = json.load(f)
                
            version = CircuitVersion.from_dict(version_data)
            self.loaded_versions[version_id] = version
            return version
            
        except Exception as e:
            logger.error(f"Failed to get version {version_id}: {e}")
            return None
    
    def get_circuit(self, circuit_name: str, version_id: Optional[str] = None) -> Optional[str]:
        """
        Get the content of a circuit.
        
        Args:
            circuit_name: Name of the circuit
            version_id: ID of the version to get (defaults to HEAD)
            
        Returns:
            Circuit content if found, None otherwise
        """
        try:
            # Use specified version or HEAD
            if version_id is None:
                if circuit_name not in self.head:
                    logger.error(f"Circuit '{circuit_name}' not found")
                    return None
                version_id = self.head[circuit_name]
            
            # Get version info
            version = self.get_version(version_id)
            if not version:
                return None
            
            # Get circuit content
            circuit_path = self.get_circuit_path(version.circuit_hash)
            
            if not circuit_path.exists():
                logger.error(f"Circuit file for version {version_id} not found")
                return None
                
            with open(circuit_path, 'r') as f:
                content = f.read()
                
            return content
            
        except Exception as e:
            logger.error(f"Failed to get circuit: {e}")
            return None
    
    def checkout(self, circuit_name: str, version_id: str) -> bool:
        """
        Checkout a specific version of a circuit.
        
        Args:
            circuit_name: Name of the circuit
            version_id: ID of the version to checkout
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Verify version exists
            version = self.get_version(version_id)
            if not version:
                return False
            
            # Update HEAD
            self.head[circuit_name] = version_id
            self.save_state()
            
            logger.info(f"Checked out version {version_id[:8]} for circuit '{circuit_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to checkout: {e}")
            return False
    
    def list_versions(self, circuit_name: str) -> List[CircuitVersion]:
        """
        List all versions of a circuit.
        
        Args:
            circuit_name: Name of the circuit
            
        Returns:
            List of CircuitVersion objects
        """
        versions = []
        try:
            if circuit_name not in self.index:
                logger.error(f"Circuit '{circuit_name}' not found")
                return []
            
            # Start from the latest version and go backward
            current_id = self.index[circuit_name]
            
            while current_id:
                version = self.get_version(current_id)
                if not version:
                    break
                    
                versions.append(version)
                current_id = version.parent_id
                
            return versions
            
        except Exception as e:
            logger.error(f"Failed to list versions: {e}")
            return []
    
    def compare_versions(self, 
                         circuit_name: str, 
                         version_id_1: str, 
                         version_id_2: str) -> Dict[str, Any]:
        """
        Compare two versions of a circuit.
        
        Args:
            circuit_name: Name of the circuit
            version_id_1: ID of the first version
            version_id_2: ID of the second version
            
        Returns:
            Dictionary with comparison results
        """
        try:
            # Get both versions
            circuit1 = self.get_circuit(circuit_name, version_id_1)
            circuit2 = self.get_circuit(circuit_name, version_id_2)
            
            if circuit1 is None or circuit2 is None:
                return {"error": "One or both versions not found"}
                
            version1 = self.get_version(version_id_1)
            version2 = self.get_version(version_id_2)
            
            # Simple comparison for now
            # In a real implementation, this would do a more sophisticated diff
            lines1 = circuit1.split("\n")
            lines2 = circuit2.split("\n")
            
            # Count differences
            added = len([l for l in lines2 if l and l not in lines1])
            removed = len([l for l in lines1 if l and l not in lines2])
            
            return {
                "version1": {
                    "id": version_id_1,
                    "timestamp": version1.timestamp,
                    "author": version1.author,
                    "message": version1.message
                },
                "version2": {
                    "id": version_id_2,
                    "timestamp": version2.timestamp,
                    "author": version2.author,
                    "message": version2.message
                },
                "lines_added": added,
                "lines_removed": removed,
                "is_identical": version1.circuit_hash == version2.circuit_hash
            }
            
        except Exception as e:
            logger.error(f"Failed to compare versions: {e}")
            return {"error": str(e)}
    
    def list_circuits(self) -> List[Dict[str, Any]]:
        """
        List all circuits in the repository.
        
        Returns:
            List of dictionaries with circuit information
        """
        result = []
        try:
            for circuit_name, version_id in self.index.items():
                version = self.get_version(version_id)
                if version:
                    result.append({
                        "name": circuit_name,
                        "current_version": version_id,
                        "last_modified": version.timestamp,
                        "author": version.author,
                        "message": version.message
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list circuits: {e}")
            return []

# Convenience functions for command-line use

def init_repo(repo_path: str, author: Optional[str] = None) -> bool:
    """Initialize a new version control repository."""
    vc = CircuitVersionControl(repo_path)
    return vc.init(author)

def commit_circuit(repo_path: str, 
                  circuit_name: str, 
                  circuit_file: str, 
                  message: str, 
                  author: Optional[str] = None) -> Optional[str]:
    """Commit a circuit file to the repository."""
    try:
        with open(circuit_file, 'r') as f:
            content = f.read()
            
        vc = CircuitVersionControl(repo_path)
        if not vc.load():
            return None
            
        return vc.commit(circuit_name, content, message, author)
        
    except Exception as e:
        logger.error(f"Failed to commit circuit: {e}")
        return None

def get_circuit_version(repo_path: str, 
                        circuit_name: str, 
                        version_id: Optional[str] = None, 
                        output_file: Optional[str] = None) -> Optional[str]:
    """Get a specific version of a circuit."""
    try:
        vc = CircuitVersionControl(repo_path)
        if not vc.load():
            return None
            
        content = vc.get_circuit(circuit_name, version_id)
        
        if content is None:
            return None
            
        if output_file:
            with open(output_file, 'w') as f:
                f.write(content)
                
        return content
        
    except Exception as e:
        logger.error(f"Failed to get circuit version: {e}")
        return None

def list_circuit_versions(repo_path: str, circuit_name: str) -> List[Dict[str, Any]]:
    """List all versions of a circuit."""
    try:
        vc = CircuitVersionControl(repo_path)
        if not vc.load():
            return []
            
        versions = vc.list_versions(circuit_name)
        return [v.to_dict() for v in versions]
        
    except Exception as e:
        logger.error(f"Failed to list circuit versions: {e}")
        return []

def checkout_version(repo_path: str, circuit_name: str, version_id: str) -> bool:
    """Checkout a specific version of a circuit."""
    try:
        vc = CircuitVersionControl(repo_path)
        if not vc.load():
            return False
            
        return vc.checkout(circuit_name, version_id)
        
    except Exception as e:
        logger.error(f"Failed to checkout version: {e}")
        return False 