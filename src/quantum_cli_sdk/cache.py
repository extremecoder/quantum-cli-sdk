"""
Caching system for the Quantum CLI SDK.

This module provides an intelligent caching layer for simulation results
to avoid redundant calculations during development.
"""

import os
import json
import hashlib
import logging
import pickle
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple

# Set up logging
logger = logging.getLogger(__name__)

class CacheKey:
    """Represents a unique key for caching simulation results."""
    
    def __init__(self, 
                 circuit_code: str, 
                 simulator: str, 
                 shots: int, 
                 parameters: Optional[Dict[str, Any]] = None):
        """Initialize a cache key.
        
        Args:
            circuit_code: The quantum circuit code (e.g., OpenQASM)
            simulator: The simulator used (e.g., qiskit, cirq)
            shots: Number of simulation shots
            parameters: Additional parameters that affect the simulation
        """
        self.circuit_code = circuit_code
        self.simulator = simulator
        self.shots = shots
        self.parameters = parameters or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the cache key to a dictionary.
        
        Returns:
            Dictionary representation of the cache key
        """
        return {
            "circuit_code": self.circuit_code,
            "simulator": self.simulator,
            "shots": self.shots,
            "parameters": self.parameters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheKey':
        """Create a cache key from a dictionary.
        
        Args:
            data: Dictionary representation of a cache key
            
        Returns:
            CacheKey instance
        """
        return cls(
            circuit_code=data.get("circuit_code", ""),
            simulator=data.get("simulator", ""),
            shots=data.get("shots", 0),
            parameters=data.get("parameters", {})
        )
    
    def get_hash(self) -> str:
        """Get a hash of the cache key.
        
        Returns:
            Hash string
        """
        # Convert the key to a JSON string
        key_str = json.dumps(self.to_dict(), sort_keys=True)
        
        # Compute hash
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def __eq__(self, other):
        """Compare cache keys for equality."""
        if not isinstance(other, CacheKey):
            return False
        
        return (
            self.circuit_code == other.circuit_code and
            self.simulator == other.simulator and
            self.shots == other.shots and
            self.parameters == other.parameters
        )
    
    def __hash__(self):
        """Hash function for the cache key."""
        return hash(self.get_hash())


class CacheEntry:
    """Represents a cached simulation result."""
    
    def __init__(self, 
                 key: CacheKey, 
                 result: Any, 
                 timestamp: Optional[float] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize a cache entry.
        
        Args:
            key: The cache key
            result: The simulation result
            timestamp: Time when the result was cached
            metadata: Additional metadata about the cached result
        """
        self.key = key
        self.result = result
        self.timestamp = timestamp or time.time()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the cache entry to a dictionary.
        
        Returns:
            Dictionary representation of the cache entry
        """
        return {
            "key": self.key.to_dict(),
            "timestamp": self.timestamp,
            "metadata": self.metadata
            # result is not included as it may not be JSON serializable
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], result: Any) -> 'CacheEntry':
        """Create a cache entry from a dictionary and result data.
        
        Args:
            data: Dictionary representation of a cache entry
            result: The simulation result
            
        Returns:
            CacheEntry instance
        """
        return cls(
            key=CacheKey.from_dict(data.get("key", {})),
            result=result,
            timestamp=data.get("timestamp", time.time()),
            metadata=data.get("metadata", {})
        )
    
    def age(self) -> float:
        """Get the age of the cache entry in seconds.
        
        Returns:
            Age in seconds
        """
        return time.time() - self.timestamp


class SimulationCache:
    """Manages caching of simulation results."""
    
    def __init__(self, cache_dir: Optional[str] = None, max_age: Optional[float] = None):
        """Initialize the simulation cache.
        
        Args:
            cache_dir: Directory to store cache files
            max_age: Maximum age of cache entries in seconds
        """
        if cache_dir is None:
            # Default to .quantum_cache in the current directory
            cache_dir = ".quantum_cache"
        
        self.cache_dir = cache_dir
        self.max_age = max_age  # None means no expiration
        
        # In-memory cache
        self.memory_cache: Dict[str, CacheEntry] = {}
        
        # Make sure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Try to load index
        self._load_index()
    
    def _get_cache_path(self, key_hash: str) -> str:
        """Get the path to a cache file.
        
        Args:
            key_hash: Hash of the cache key
            
        Returns:
            Path to the cache file
        """
        return os.path.join(self.cache_dir, f"{key_hash}.cache")
    
    def _get_index_path(self) -> str:
        """Get the path to the cache index file.
        
        Returns:
            Path to the index file
        """
        return os.path.join(self.cache_dir, "index.json")
    
    def _load_index(self) -> None:
        """Load the cache index from disk."""
        index_path = self._get_index_path()
        
        if not os.path.exists(index_path):
            return
        
        try:
            with open(index_path, 'r') as f:
                index_data = json.load(f)
            
            # Process each entry in the index
            for key_hash, entry_data in index_data.items():
                # Skip if the cache file doesn't exist
                cache_path = self._get_cache_path(key_hash)
                if not os.path.exists(cache_path):
                    continue
                
                # Check if the entry is expired
                if self.max_age is not None:
                    entry_age = time.time() - entry_data.get("timestamp", 0)
                    if entry_age > self.max_age:
                        # Entry is expired, delete the cache file
                        try:
                            os.remove(cache_path)
                        except Exception:
                            pass
                        continue
                
                # We don't load the actual result data here to save memory
                # It will be loaded on demand when get() is called
                key = CacheKey.from_dict(entry_data.get("key", {}))
                self.memory_cache[key_hash] = CacheEntry(
                    key=key,
                    result=None,  # Result is not loaded yet
                    timestamp=entry_data.get("timestamp", time.time()),
                    metadata=entry_data.get("metadata", {})
                )
            
            logger.debug(f"Loaded {len(self.memory_cache)} entries from cache index")
            
        except Exception as e:
            logger.error(f"Error loading cache index: {e}")
    
    def _save_index(self) -> None:
        """Save the cache index to disk."""
        index_path = self._get_index_path()
        
        try:
            # Create index data
            index_data = {}
            for key_hash, entry in self.memory_cache.items():
                index_data[key_hash] = entry.to_dict()
            
            # Save index
            with open(index_path, 'w') as f:
                json.dump(index_data, f, indent=2)
            
            logger.debug(f"Saved {len(self.memory_cache)} entries to cache index")
            
        except Exception as e:
            logger.error(f"Error saving cache index: {e}")
    
    def _load_result(self, key_hash: str) -> Any:
        """Load a result from a cache file.
        
        Args:
            key_hash: Hash of the cache key
            
        Returns:
            The cached result or None if not found
        """
        cache_path = self._get_cache_path(key_hash)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                result = pickle.load(f)
            
            return result
            
        except Exception as e:
            logger.error(f"Error loading cached result: {e}")
            return None
    
    def _save_result(self, key_hash: str, result: Any) -> bool:
        """Save a result to a cache file.
        
        Args:
            key_hash: Hash of the cache key
            result: The result to save
            
        Returns:
            True if successful, False otherwise
        """
        cache_path = self._get_cache_path(key_hash)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(result, f)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving cached result: {e}")
            return False
    
    def clear(self) -> None:
        """Clear the cache."""
        # Clear in-memory cache
        self.memory_cache.clear()
        
        # Remove cache files
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            
            logger.info("Cache cleared")
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def put(self, key: CacheKey, result: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store a result in the cache.
        
        Args:
            key: The cache key
            result: The result to cache
            metadata: Additional metadata about the result
        """
        # Get key hash
        key_hash = key.get_hash()
        
        # Create cache entry
        entry = CacheEntry(key=key, result=result, metadata=metadata)
        
        # Store in memory
        self.memory_cache[key_hash] = entry
        
        # Store result on disk
        self._save_result(key_hash, result)
        
        # Update index
        self._save_index()
        
        logger.debug(f"Cached result for {key.simulator} simulation with {key.shots} shots")
    
    def get(self, key: CacheKey) -> Optional[Any]:
        """Retrieve a result from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached result or None if not found or expired
        """
        # Get key hash
        key_hash = key.get_hash()
        
        # Check if the key exists in memory
        if key_hash not in self.memory_cache:
            return None
        
        # Get cache entry
        entry = self.memory_cache[key_hash]
        
        # Check if the entry is expired
        if self.max_age is not None and entry.age() > self.max_age:
            # Entry is expired, remove it
            del self.memory_cache[key_hash]
            try:
                os.remove(self._get_cache_path(key_hash))
            except Exception:
                pass
            self._save_index()
            return None
        
        # If the result is not loaded yet, load it
        if entry.result is None:
            entry.result = self._load_result(key_hash)
            if entry.result is None:
                # Result could not be loaded, remove the entry
                del self.memory_cache[key_hash]
                self._save_index()
                return None
        
        logger.debug(f"Retrieved cached result for {key.simulator} simulation with {key.shots} shots")
        return entry.result
    
    def has(self, key: CacheKey) -> bool:
        """Check if a key exists in the cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if the key exists and is not expired, False otherwise
        """
        # Get key hash
        key_hash = key.get_hash()
        
        # Check if the key exists in memory
        if key_hash not in self.memory_cache:
            return False
        
        # Get cache entry
        entry = self.memory_cache[key_hash]
        
        # Check if the entry is expired
        if self.max_age is not None and entry.age() > self.max_age:
            return False
        
        return True
    
    def invalidate(self, key: CacheKey) -> None:
        """Invalidate a cache entry.
        
        Args:
            key: The cache key
        """
        # Get key hash
        key_hash = key.get_hash()
        
        # Check if the key exists in memory
        if key_hash not in self.memory_cache:
            return
        
        # Remove from memory
        del self.memory_cache[key_hash]
        
        # Remove from disk
        try:
            os.remove(self._get_cache_path(key_hash))
        except Exception:
            pass
        
        # Update index
        self._save_index()
        
        logger.debug(f"Invalidated cache entry for {key.simulator} simulation with {key.shots} shots")
    
    def prune(self, max_age: Optional[float] = None) -> int:
        """Remove expired entries from the cache.
        
        Args:
            max_age: Maximum age of entries to keep (in seconds)
            
        Returns:
            Number of entries removed
        """
        if max_age is None:
            max_age = self.max_age
        
        if max_age is None:
            # No expiration
            return 0
        
        # List of keys to remove
        keys_to_remove = []
        
        # Check each entry
        for key_hash, entry in self.memory_cache.items():
            if entry.age() > max_age:
                keys_to_remove.append(key_hash)
        
        # Remove entries
        for key_hash in keys_to_remove:
            del self.memory_cache[key_hash]
            try:
                os.remove(self._get_cache_path(key_hash))
            except Exception:
                pass
        
        # Update index
        if keys_to_remove:
            self._save_index()
        
        logger.debug(f"Pruned {len(keys_to_remove)} expired cache entries")
        return len(keys_to_remove)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        # Count entries by simulator
        simulators = {}
        for entry in self.memory_cache.values():
            simulator = entry.key.simulator
            simulators[simulator] = simulators.get(simulator, 0) + 1
        
        # Calculate total size
        total_size = 0
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
        except Exception:
            pass
        
        return {
            "entries": len(self.memory_cache),
            "simulators": simulators,
            "size_bytes": total_size,
            "cache_dir": self.cache_dir
        }


# Global cache instance
_simulation_cache = None

def get_cache(cache_dir: Optional[str] = None, max_age: Optional[float] = None) -> SimulationCache:
    """Get the global simulation cache instance.
    
    Args:
        cache_dir: Directory to store cache files
        max_age: Maximum age of cache entries in seconds
        
    Returns:
        SimulationCache instance
    """
    global _simulation_cache
    
    if _simulation_cache is None:
        _simulation_cache = SimulationCache(cache_dir, max_age)
    
    return _simulation_cache

def initialize_cache(cache_dir: Optional[str] = None, max_age: Optional[float] = None) -> SimulationCache:
    """Initialize the cache system.
    
    Args:
        cache_dir: Directory to store cache files
        max_age: Maximum age of cache entries in seconds
        
    Returns:
        SimulationCache instance
    """
    global _simulation_cache
    
    _simulation_cache = SimulationCache(cache_dir, max_age)
    return _simulation_cache 