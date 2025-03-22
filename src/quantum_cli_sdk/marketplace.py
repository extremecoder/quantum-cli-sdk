#!/usr/bin/env python3
"""
Quantum Algorithm Marketplace for sharing and discovering quantum algorithms.

This module provides functionality to:
- Browse available quantum algorithms
- Search for algorithms by keywords, tags, or other criteria
- Download algorithms from the marketplace
- Publish algorithms to the marketplace
- Rate and review algorithms
"""

import os
import json
import uuid
import datetime
import requests
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union

from .versioning import CircuitVersionControl, get_circuit_version

logger = logging.getLogger(__name__)

# Default marketplace URL - would be replaced with actual service in production
DEFAULT_MARKETPLACE_URL = "https://quantum-marketplace.example.com/api"
DEFAULT_MARKETPLACE_CONFIG = "~/.quantum-cli/marketplace_config.json"

class MarketplaceAlgorithm:
    """Represents a quantum algorithm in the marketplace."""
    
    def __init__(self, 
                 algorithm_id: str,
                 name: str,
                 description: str,
                 author: str,
                 version: str,
                 tags: List[str],
                 created_at: float,
                 updated_at: float,
                 rating: float = 0.0,
                 downloads: int = 0,
                 requirements: Optional[Dict[str, str]] = None,
                 example_usage: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize an algorithm record.
        
        Args:
            algorithm_id: Unique identifier for the algorithm
            name: Algorithm name
            description: Description of the algorithm
            author: Author name
            version: Version string
            tags: List of tags for categorization
            created_at: Creation timestamp
            updated_at: Last update timestamp
            rating: Average rating (0-5)
            downloads: Number of downloads
            requirements: Required dependencies
            example_usage: Example code showing how to use the algorithm
            metadata: Additional metadata
        """
        self.algorithm_id = algorithm_id
        self.name = name
        self.description = description
        self.author = author
        self.version = version
        self.tags = tags
        self.created_at = created_at
        self.updated_at = updated_at
        self.rating = rating
        self.downloads = downloads
        self.requirements = requirements or {}
        self.example_usage = example_usage
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "algorithm_id": self.algorithm_id,
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "version": self.version,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "rating": self.rating,
            "downloads": self.downloads,
            "requirements": self.requirements,
            "example_usage": self.example_usage,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketplaceAlgorithm':
        """Create a MarketplaceAlgorithm from a dictionary."""
        return cls(
            algorithm_id=data["algorithm_id"],
            name=data["name"],
            description=data["description"],
            author=data["author"],
            version=data["version"],
            tags=data["tags"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            rating=data.get("rating", 0.0),
            downloads=data.get("downloads", 0),
            requirements=data.get("requirements", {}),
            example_usage=data.get("example_usage"),
            metadata=data.get("metadata", {})
        )
    
    def __str__(self) -> str:
        """String representation of the algorithm."""
        return f"{self.name} v{self.version} by {self.author} - {self.description}"


class MarketplaceClient:
    """Client for interacting with the quantum algorithm marketplace."""
    
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the marketplace client.
        
        Args:
            api_url: URL of the marketplace API
            api_key: API key for authentication
        """
        self.api_url = api_url or os.environ.get("QUANTUM_MARKETPLACE_URL", DEFAULT_MARKETPLACE_URL)
        self.api_key = api_key or os.environ.get("QUANTUM_MARKETPLACE_API_KEY")
        
        # Load config if available
        self.config_path = os.path.expanduser(
            os.environ.get("QUANTUM_MARKETPLACE_CONFIG", DEFAULT_MARKETPLACE_CONFIG)
        )
        self.config = self._load_config()
        
        # Set API key from config if not provided
        if not self.api_key and "api_key" in self.config:
            self.api_key = self.config["api_key"]
    
    def _load_config(self) -> Dict[str, Any]:
        """Load marketplace configuration from file."""
        config = {}
        try:
            config_path = Path(self.config_path)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded marketplace configuration from {self.config_path}")
        except Exception as e:
            logger.warning(f"Failed to load marketplace configuration: {e}")
        
        return config
    
    def _save_config(self) -> bool:
        """Save marketplace configuration to file."""
        try:
            config_path = Path(self.config_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            logger.info(f"Saved marketplace configuration to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save marketplace configuration: {e}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Quantum-SDK-Client/1.0"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        return headers
    
    def _api_request(self, 
                     method: str, 
                     endpoint: str, 
                     data: Optional[Dict[str, Any]] = None,
                     params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make an API request to the marketplace.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request payload
            params: Query parameters
            
        Returns:
            API response as dictionary
            
        Raises:
            Exception: If the API request fails
        """
        # In a real implementation, this would make actual HTTP requests
        # For demo purposes, we'll simulate responses based on the endpoint
        
        # Simulated marketplace data
        simulated_algorithms = [
            {
                "algorithm_id": "alg-001",
                "name": "Shor's Algorithm",
                "description": "Implementation of Shor's algorithm for integer factorization",
                "author": "quantum_dev",
                "version": "1.2.0",
                "tags": ["factorization", "cryptography", "rsa"],
                "created_at": datetime.datetime(2023, 5, 15).timestamp(),
                "updated_at": datetime.datetime(2023, 6, 20).timestamp(),
                "rating": 4.8,
                "downloads": 1250,
                "requirements": {"qiskit": ">=0.34.0"},
                "example_usage": "# Example code for using Shor's algorithm\n...",
                "metadata": {"complexity": "O(log N)^3", "quantum_advantage": "exponential"}
            },
            {
                "algorithm_id": "alg-002",
                "name": "Grover's Search",
                "description": "Optimized implementation of Grover's search algorithm",
                "author": "qcomputing",
                "version": "2.0.1",
                "tags": ["search", "optimization", "amplitude amplification"],
                "created_at": datetime.datetime(2023, 1, 10).timestamp(),
                "updated_at": datetime.datetime(2023, 8, 5).timestamp(),
                "rating": 4.5,
                "downloads": 983,
                "requirements": {"cirq": ">=1.0.0"},
                "example_usage": "# Example code for using Grover's search\n...",
                "metadata": {"complexity": "O(√N)", "quantum_advantage": "quadratic"}
            },
            {
                "algorithm_id": "alg-003",
                "name": "VQE",
                "description": "Variational Quantum Eigensolver for chemistry simulations",
                "author": "quantum_chemistry",
                "version": "1.0.0",
                "tags": ["chemistry", "optimization", "variational"],
                "created_at": datetime.datetime(2023, 3, 25).timestamp(),
                "updated_at": datetime.datetime(2023, 3, 25).timestamp(),
                "rating": 4.2,
                "downloads": 756,
                "requirements": {"qiskit": ">=0.34.0", "numpy": ">=1.20.0"},
                "example_usage": "# Example code for using VQE\n...",
                "metadata": {"complexity": "varies", "applications": ["molecular energy", "ground states"]}
            }
        ]
        
        # Simulate API responses based on the endpoint
        if method == "GET" and endpoint == "/algorithms":
            # Filter by tag if provided
            tag_filter = params.get("tag") if params else None
            
            if tag_filter:
                filtered_algorithms = [
                    alg for alg in simulated_algorithms 
                    if tag_filter in alg["tags"]
                ]
                return {"algorithms": filtered_algorithms, "count": len(filtered_algorithms)}
            
            return {"algorithms": simulated_algorithms, "count": len(simulated_algorithms)}
        
        elif method == "GET" and endpoint.startswith("/algorithms/"):
            algorithm_id = endpoint.split("/")[-1]
            for alg in simulated_algorithms:
                if alg["algorithm_id"] == algorithm_id:
                    return {"algorithm": alg}
            
            return {"error": "Algorithm not found"}
        
        elif method == "POST" and endpoint == "/algorithms":
            # Simulate publishing an algorithm
            if not data:
                return {"error": "Missing algorithm data"}
            
            # In a real implementation, this would validate and store the algorithm
            algorithm_id = str(uuid.uuid4())
            return {
                "success": True,
                "algorithm_id": algorithm_id,
                "message": "Algorithm published successfully"
            }
        
        elif method == "POST" and endpoint.startswith("/algorithms/") and endpoint.endswith("/download"):
            # Simulate downloading an algorithm
            algorithm_id = endpoint.split("/")[-2]
            for alg in simulated_algorithms:
                if alg["algorithm_id"] == algorithm_id:
                    # Increment download count in a real implementation
                    return {
                        "success": True,
                        "download_url": f"https://quantum-marketplace.example.com/download/{algorithm_id}",
                        "algorithm": alg
                    }
            
            return {"error": "Algorithm not found"}
        
        elif method == "POST" and endpoint.startswith("/algorithms/") and endpoint.endswith("/reviews"):
            # Simulate adding a review
            algorithm_id = endpoint.split("/")[-2]
            for alg in simulated_algorithms:
                if alg["algorithm_id"] == algorithm_id:
                    return {
                        "success": True,
                        "message": "Review added successfully"
                    }
            
            return {"error": "Algorithm not found"}
        
        # Simulate API error for unhandled cases
        return {"error": "Unhandled API request"}
    
    def browse_algorithms(self, tag: Optional[str] = None) -> List[MarketplaceAlgorithm]:
        """
        Browse available algorithms, optionally filtered by tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of algorithms
        """
        params = {"tag": tag} if tag else None
        response = self._api_request("GET", "/algorithms", params=params)
        
        if "algorithms" in response:
            return [MarketplaceAlgorithm.from_dict(alg) for alg in response["algorithms"]]
        
        logger.error(f"Failed to browse algorithms: {response.get('error', 'Unknown error')}")
        return []
    
    def get_algorithm(self, algorithm_id: str) -> Optional[MarketplaceAlgorithm]:
        """
        Get details of a specific algorithm.
        
        Args:
            algorithm_id: ID of the algorithm
            
        Returns:
            Algorithm details if found, None otherwise
        """
        response = self._api_request("GET", f"/algorithms/{algorithm_id}")
        
        if "algorithm" in response:
            return MarketplaceAlgorithm.from_dict(response["algorithm"])
        
        logger.error(f"Failed to get algorithm {algorithm_id}: {response.get('error', 'Unknown error')}")
        return None
    
    def publish_algorithm(self, 
                          name: str,
                          description: str,
                          version: str,
                          tags: List[str],
                          circuit_path: str,
                          author: Optional[str] = None,
                          requirements: Optional[Dict[str, str]] = None,
                          example_usage: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Publish an algorithm to the marketplace.
        
        Args:
            name: Algorithm name
            description: Description of the algorithm
            version: Version string
            tags: List of tags for categorization
            circuit_path: Path to the circuit file
            author: Author name (defaults to user from config)
            requirements: Required dependencies
            example_usage: Example code showing how to use the algorithm
            metadata: Additional metadata
            
        Returns:
            Algorithm ID if successful, None otherwise
        """
        try:
            # Read circuit file
            with open(circuit_path, 'r') as f:
                circuit_content = f.read()
                
            # Set author from config if not provided
            if not author:
                author = self.config.get("author") or os.environ.get("USER", "unknown")
                
            # Prepare algorithm data
            algorithm_data = {
                "name": name,
                "description": description,
                "author": author,
                "version": version,
                "tags": tags,
                "circuit_content": circuit_content,
                "created_at": datetime.datetime.now().timestamp(),
                "updated_at": datetime.datetime.now().timestamp(),
                "requirements": requirements or {},
                "example_usage": example_usage,
                "metadata": metadata or {}
            }
            
            # Publish to marketplace
            response = self._api_request("POST", "/algorithms", data=algorithm_data)
            
            if response.get("success"):
                logger.info(f"Published algorithm {name} v{version} with ID {response['algorithm_id']}")
                return response["algorithm_id"]
            
            logger.error(f"Failed to publish algorithm: {response.get('error', 'Unknown error')}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to publish algorithm: {e}")
            return None
    
    def download_algorithm(self, 
                           algorithm_id: str, 
                           output_path: Optional[str] = None) -> Optional[str]:
        """
        Download an algorithm from the marketplace.
        
        Args:
            algorithm_id: ID of the algorithm
            output_path: Path to save the algorithm to
            
        Returns:
            Path to the downloaded algorithm if successful, None otherwise
        """
        try:
            # Request download
            response = self._api_request("POST", f"/algorithms/{algorithm_id}/download")
            
            if not response.get("success"):
                logger.error(f"Failed to download algorithm: {response.get('error', 'Unknown error')}")
                return None
                
            # In a real implementation, this would download from the URL
            # For demo purposes, we'll simulate by creating a file with dummy content
            
            algorithm = MarketplaceAlgorithm.from_dict(response["algorithm"])
            
            # Determine output path
            if output_path is None:
                output_path = f"{algorithm.name.lower().replace(' ', '_')}_v{algorithm.version}.qasm"
                
            # Write algorithm to file
            with open(output_path, 'w') as f:
                f.write(f"// {algorithm.name} v{algorithm.version}\n")
                f.write(f"// Author: {algorithm.author}\n")
                f.write(f"// Description: {algorithm.description}\n")
                f.write(f"// Downloaded from Quantum Marketplace\n\n")
                f.write("// Simulated circuit content for demo purposes\n")
                f.write("OPENQASM 2.0;\n")
                f.write('include "qelib1.inc";\n\n')
                f.write(f"// Tags: {', '.join(algorithm.tags)}\n")
                f.write("qreg q[5];\n")
                f.write("creg c[5];\n\n")
                f.write("// Algorithm implementation would be here\n")
                
                # Add example usage if available
                if algorithm.example_usage:
                    f.write("\n// Example Usage:\n")
                    f.write("/*\n")
                    f.write(algorithm.example_usage)
                    f.write("\n*/\n")
                    
            logger.info(f"Downloaded algorithm '{algorithm.name}' to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to download algorithm: {e}")
            return None
    
    def submit_review(self, 
                      algorithm_id: str, 
                      rating: float, 
                      comment: Optional[str] = None) -> bool:
        """
        Submit a review for an algorithm.
        
        Args:
            algorithm_id: ID of the algorithm
            rating: Rating value (0-5)
            comment: Review comment
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate rating
            if not 0 <= rating <= 5:
                logger.error(f"Invalid rating value: {rating}. Must be between 0 and 5.")
                return False
                
            # Prepare review data
            review_data = {
                "rating": rating,
                "comment": comment,
                "reviewer": self.config.get("author") or os.environ.get("USER", "anonymous"),
                "timestamp": datetime.datetime.now().timestamp()
            }
            
            # Submit review
            response = self._api_request("POST", f"/algorithms/{algorithm_id}/reviews", data=review_data)
            
            if response.get("success"):
                logger.info(f"Submitted review for algorithm {algorithm_id}")
                return True
                
            logger.error(f"Failed to submit review: {response.get('error', 'Unknown error')}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to submit review: {e}")
            return False
    
    def search_algorithms(self, query: str) -> List[MarketplaceAlgorithm]:
        """
        Search for algorithms based on a query string.
        
        Args:
            query: Search query
            
        Returns:
            List of matching algorithms
        """
        try:
            # In a real implementation, this would send a search request to the API
            # For demo purposes, we'll simulate by filtering the browse results
            
            all_algorithms = self.browse_algorithms()
            
            # Simple filtering for demo purposes
            query = query.lower()
            results = []
            
            for alg in all_algorithms:
                # Check if query appears in name, description, or tags
                if (query in alg.name.lower() or 
                    query in alg.description.lower() or 
                    any(query in tag.lower() for tag in alg.tags)):
                    results.append(alg)
                    
            return results
            
        except Exception as e:
            logger.error(f"Failed to search algorithms: {e}")
            return []
    
    def configure(self, api_key: str, author: str) -> bool:
        """
        Configure the marketplace client.
        
        Args:
            api_key: API key for authentication
            author: Author name for publishing
            
        Returns:
            True if configuration was saved successfully, False otherwise
        """
        try:
            self.api_key = api_key
            self.config["api_key"] = api_key
            self.config["author"] = author
            
            return self._save_config()
            
        except Exception as e:
            logger.error(f"Failed to configure marketplace client: {e}")
            return False

# Convenience functions for command-line use

def browse_marketplace(tag: Optional[str] = None) -> List[Dict[str, Any]]:
    """Browse available algorithms in the marketplace."""
    client = MarketplaceClient()
    algorithms = client.browse_algorithms(tag)
    return [alg.to_dict() for alg in algorithms]

def search_marketplace(query: str) -> List[Dict[str, Any]]:
    """Search for algorithms in the marketplace."""
    client = MarketplaceClient()
    algorithms = client.search_algorithms(query)
    return [alg.to_dict() for alg in algorithms]

def get_algorithm_details(algorithm_id: str) -> Optional[Dict[str, Any]]:
    """Get details of a specific algorithm."""
    client = MarketplaceClient()
    algorithm = client.get_algorithm(algorithm_id)
    return algorithm.to_dict() if algorithm else None

def download_algorithm(algorithm_id: str, output_path: Optional[str] = None) -> Optional[str]:
    """Download an algorithm from the marketplace."""
    client = MarketplaceClient()
    return client.download_algorithm(algorithm_id, output_path)

def publish_algorithm(name: str, 
                     description: str, 
                     version: str,
                     tags: List[str],
                     circuit_path: str,
                     author: Optional[str] = None,
                     requirements: Optional[Dict[str, str]] = None,
                     example_usage: Optional[str] = None) -> Optional[str]:
    """Publish an algorithm to the marketplace."""
    client = MarketplaceClient()
    return client.publish_algorithm(
        name=name,
        description=description,
        version=version,
        tags=tags,
        circuit_path=circuit_path,
        author=author,
        requirements=requirements,
        example_usage=example_usage
    )

def submit_review(algorithm_id: str, rating: float, comment: Optional[str] = None) -> bool:
    """Submit a review for an algorithm."""
    client = MarketplaceClient()
    return client.submit_review(algorithm_id, rating, comment)

def configure_marketplace(api_key: str, author: str) -> bool:
    """Configure the marketplace client."""
    client = MarketplaceClient()
    return client.configure(api_key, author) 