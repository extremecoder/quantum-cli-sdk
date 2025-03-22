#!/usr/bin/env python3
"""
Quantum Circuit Sharing module for collaborating on quantum circuits.

This module provides functionality to:
- Share quantum circuits with other users
- Set permissions for shared circuits
- Send and receive circuit updates
- Track circuit access and collaboration history
"""

import os
import json
import uuid
import datetime
import time
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union

from .versioning import CircuitVersionControl, get_circuit_version, CircuitVersion

logger = logging.getLogger(__name__)

class SharingPermission:
    """Defines permission levels for shared circuits."""
    READ_ONLY = "read_only"       # Can view but not modify the circuit
    READ_WRITE = "read_write"     # Can view and modify the circuit
    ADMIN = "admin"               # Can view, modify, and manage sharing
    OWNER = "owner"               # Full control (only the original creator)

class SharedCircuit:
    """Represents a shared quantum circuit."""
    
    def __init__(self, 
                 share_id: str,
                 circuit_name: str,
                 owner: str,
                 description: str,
                 creation_time: float,
                 last_modified: float,
                 collaborators: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a shared circuit.
        
        Args:
            share_id: Unique identifier for the shared circuit
            circuit_name: Name of the circuit
            owner: Owner/creator of the circuit
            description: Description of the circuit
            creation_time: Creation timestamp
            last_modified: Last modification timestamp
            collaborators: Dictionary mapping collaborator IDs to their permissions
            tags: List of tags for categorization
            metadata: Additional metadata
        """
        self.share_id = share_id
        self.circuit_name = circuit_name
        self.owner = owner
        self.description = description
        self.creation_time = creation_time
        self.last_modified = last_modified
        self.collaborators = collaborators or {}
        self.tags = tags or []
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "share_id": self.share_id,
            "circuit_name": self.circuit_name,
            "owner": self.owner,
            "description": self.description,
            "creation_time": self.creation_time,
            "last_modified": self.last_modified,
            "collaborators": self.collaborators,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SharedCircuit':
        """Create a SharedCircuit from a dictionary."""
        return cls(
            share_id=data["share_id"],
            circuit_name=data["circuit_name"],
            owner=data["owner"],
            description=data["description"],
            creation_time=data["creation_time"],
            last_modified=data["last_modified"],
            collaborators=data.get("collaborators", {}),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )
    
    def __str__(self) -> str:
        """String representation of the shared circuit."""
        return f"{self.circuit_name} (Shared by {self.owner}) - {self.description}"


class SharingActivity:
    """Represents an activity in the sharing system."""
    
    def __init__(self, 
                 activity_id: str,
                 share_id: str,
                 user: str,
                 action: str,
                 timestamp: float,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize a sharing activity.
        
        Args:
            activity_id: Unique identifier for the activity
            share_id: ID of the shared circuit
            user: User who performed the action
            action: Type of action performed
            timestamp: Activity timestamp
            details: Additional details about the activity
        """
        self.activity_id = activity_id
        self.share_id = share_id
        self.user = user
        self.action = action
        self.timestamp = timestamp
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "activity_id": self.activity_id,
            "share_id": self.share_id,
            "user": self.user,
            "action": self.action,
            "timestamp": self.timestamp,
            "details": self.details
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SharingActivity':
        """Create a SharingActivity from a dictionary."""
        return cls(
            activity_id=data["activity_id"],
            share_id=data["share_id"],
            user=data["user"],
            action=data["action"],
            timestamp=data["timestamp"],
            details=data.get("details", {})
        )
    
    def __str__(self) -> str:
        """String representation of the activity."""
        dt = datetime.datetime.fromtimestamp(self.timestamp)
        date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        return f"{date_str} - {self.user} {self.action}"


class SharingManager:
    """Manages sharing of quantum circuits."""
    
    def __init__(self, storage_path: str, user_id: Optional[str] = None):
        """
        Initialize the sharing manager.
        
        Args:
            storage_path: Path to store sharing data
            user_id: Current user ID
        """
        self.storage_path = Path(storage_path)
        self.user_id = user_id or os.environ.get("USER", "unknown")
        
        self.shares_dir = self.storage_path / "shares"
        self.activities_dir = self.storage_path / "activities"
        self.registry_file = self.storage_path / "registry.json"
        
        # Registry of all shared circuits
        self.registry = {}
        
        # Ensure directories exist
        self._init_storage()
        
        # Load registry
        self._load_registry()
    
    def _init_storage(self) -> None:
        """Initialize storage directories."""
        try:
            self.storage_path.mkdir(exist_ok=True)
            self.shares_dir.mkdir(exist_ok=True)
            self.activities_dir.mkdir(exist_ok=True)
            
            if not self.registry_file.exists():
                with open(self.registry_file, 'w') as f:
                    json.dump({}, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to initialize storage: {e}")
    
    def _load_registry(self) -> bool:
        """Load the registry of shared circuits."""
        try:
            if self.registry_file.exists():
                with open(self.registry_file, 'r') as f:
                    self.registry = json.load(f)
                    
            return True
            
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
            return False
    
    def _save_registry(self) -> bool:
        """Save the registry of shared circuits."""
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(self.registry, f, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
            return False
    
    def _get_share_path(self, share_id: str) -> Path:
        """Get path to a shared circuit file."""
        return self.shares_dir / f"{share_id}.json"
    
    def _get_activity_path(self, activity_id: str) -> Path:
        """Get path to an activity file."""
        return self.activities_dir / f"{activity_id}.json"
    
    def _record_activity(self, 
                         share_id: str,
                         action: str,
                         details: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Record a sharing activity.
        
        Args:
            share_id: ID of the shared circuit
            action: Type of action performed
            details: Additional details about the activity
            
        Returns:
            Activity ID if successful, None otherwise
        """
        try:
            activity_id = str(uuid.uuid4())
            timestamp = datetime.datetime.now().timestamp()
            
            activity = SharingActivity(
                activity_id=activity_id,
                share_id=share_id,
                user=self.user_id,
                action=action,
                timestamp=timestamp,
                details=details
            )
            
            # Save activity to file
            activity_path = self._get_activity_path(activity_id)
            with open(activity_path, 'w') as f:
                json.dump(activity.to_dict(), f, indent=2)
                
            # Update the last_modified time for the shared circuit
            self._update_last_modified(share_id)
                
            return activity_id
            
        except Exception as e:
            logger.error(f"Failed to record activity: {e}")
            return None
    
    def _update_last_modified(self, share_id: str) -> bool:
        """Update the last_modified timestamp for a shared circuit."""
        try:
            share_path = self._get_share_path(share_id)
            
            if not share_path.exists():
                logger.error(f"Shared circuit {share_id} not found")
                return False
                
            with open(share_path, 'r') as f:
                share_data = json.load(f)
                
            share_data["last_modified"] = datetime.datetime.now().timestamp()
            
            with open(share_path, 'w') as f:
                json.dump(share_data, f, indent=2)
                
            # Update registry as well
            if share_id in self.registry:
                self.registry[share_id]["last_modified"] = share_data["last_modified"]
                self._save_registry()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to update last_modified: {e}")
            return False
    
    def share_circuit(self, 
                     repo_path: str,
                     circuit_name: str,
                     description: str,
                     recipients: List[str] = None,
                     permission: str = SharingPermission.READ_ONLY,
                     tags: List[str] = None) -> Optional[str]:
        """
        Share a quantum circuit with others.
        
        Args:
            repo_path: Path to the version control repository
            circuit_name: Name of the circuit to share
            description: Description of the shared circuit
            recipients: List of recipient user IDs
            permission: Permission level for recipients
            tags: List of tags for categorization
            
        Returns:
            Share ID if successful, None otherwise
        """
        try:
            # Get the circuit from the repository
            circuit_content = get_circuit_version(repo_path, circuit_name)
            if circuit_content is None:
                logger.error(f"Circuit '{circuit_name}' not found in repository {repo_path}")
                return None
                
            # Create a shared circuit entry
            share_id = str(uuid.uuid4())
            timestamp = datetime.datetime.now().timestamp()
            
            # Set up collaborators with permissions
            collaborators = {}
            if recipients:
                for recipient in recipients:
                    collaborators[recipient] = permission
            
            shared_circuit = SharedCircuit(
                share_id=share_id,
                circuit_name=circuit_name,
                owner=self.user_id,
                description=description,
                creation_time=timestamp,
                last_modified=timestamp,
                collaborators=collaborators,
                tags=tags or []
            )
            
            # Save shared circuit to file
            share_path = self._get_share_path(share_id)
            with open(share_path, 'w') as f:
                json.dump(shared_circuit.to_dict(), f, indent=2)
                
            # Add to registry
            self.registry[share_id] = {
                "circuit_name": circuit_name,
                "owner": self.user_id,
                "creation_time": timestamp,
                "last_modified": timestamp,
                "description": description
            }
            self._save_registry()
            
            # Record activity
            self._record_activity(
                share_id=share_id,
                action="shared_circuit",
                details={
                    "recipients": recipients or [],
                    "permission": permission
                }
            )
            
            logger.info(f"Shared circuit '{circuit_name}' with ID {share_id}")
            return share_id
            
        except Exception as e:
            logger.error(f"Failed to share circuit: {e}")
            return None
    
    def get_shared_circuit(self, share_id: str) -> Optional[SharedCircuit]:
        """
        Get a shared circuit by ID.
        
        Args:
            share_id: ID of the shared circuit
            
        Returns:
            SharedCircuit if found, None otherwise
        """
        try:
            share_path = self._get_share_path(share_id)
            
            if not share_path.exists():
                logger.error(f"Shared circuit {share_id} not found")
                return None
                
            with open(share_path, 'r') as f:
                share_data = json.load(f)
                
            return SharedCircuit.from_dict(share_data)
            
        except Exception as e:
            logger.error(f"Failed to get shared circuit: {e}")
            return None
    
    def list_shared_circuits(self, owned_only: bool = False) -> List[SharedCircuit]:
        """
        List shared circuits.
        
        Args:
            owned_only: If True, only list circuits owned by the current user
            
        Returns:
            List of shared circuits
        """
        try:
            result = []
            
            for share_id, info in self.registry.items():
                if owned_only and info["owner"] != self.user_id:
                    continue
                    
                shared_circuit = self.get_shared_circuit(share_id)
                if shared_circuit:
                    result.append(shared_circuit)
                    
            return result
            
        except Exception as e:
            logger.error(f"Failed to list shared circuits: {e}")
            return []
    
    def list_shared_with_me(self) -> List[SharedCircuit]:
        """
        List circuits shared with the current user.
        
        Returns:
            List of shared circuits
        """
        try:
            result = []
            
            for share_id in self.registry:
                shared_circuit = self.get_shared_circuit(share_id)
                
                if shared_circuit and self.user_id in shared_circuit.collaborators:
                    result.append(shared_circuit)
                    
            return result
            
        except Exception as e:
            logger.error(f"Failed to list circuits shared with me: {e}")
            return []
    
    def update_permissions(self, 
                          share_id: str, 
                          collaborator: str, 
                          permission: str) -> bool:
        """
        Update permissions for a collaborator.
        
        Args:
            share_id: ID of the shared circuit
            collaborator: Collaborator user ID
            permission: New permission level
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the shared circuit
            shared_circuit = self.get_shared_circuit(share_id)
            
            if not shared_circuit:
                return False
                
            # Check if user has permission to update
            if shared_circuit.owner != self.user_id:
                logger.error(f"Only the owner can update permissions")
                return False
                
            # Update permission
            shared_circuit.collaborators[collaborator] = permission
            
            # Save changes
            share_path = self._get_share_path(share_id)
            with open(share_path, 'w') as f:
                json.dump(shared_circuit.to_dict(), f, indent=2)
                
            # Record activity
            self._record_activity(
                share_id=share_id,
                action="updated_permission",
                details={
                    "collaborator": collaborator,
                    "permission": permission
                }
            )
            
            logger.info(f"Updated permission for {collaborator} on circuit {share_id} to {permission}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update permissions: {e}")
            return False
    
    def remove_collaborator(self, share_id: str, collaborator: str) -> bool:
        """
        Remove a collaborator from a shared circuit.
        
        Args:
            share_id: ID of the shared circuit
            collaborator: Collaborator user ID to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the shared circuit
            shared_circuit = self.get_shared_circuit(share_id)
            
            if not shared_circuit:
                return False
                
            # Check if user has permission to update
            if shared_circuit.owner != self.user_id:
                logger.error(f"Only the owner can remove collaborators")
                return False
                
            # Remove collaborator
            if collaborator in shared_circuit.collaborators:
                del shared_circuit.collaborators[collaborator]
                
                # Save changes
                share_path = self._get_share_path(share_id)
                with open(share_path, 'w') as f:
                    json.dump(shared_circuit.to_dict(), f, indent=2)
                    
                # Record activity
                self._record_activity(
                    share_id=share_id,
                    action="removed_collaborator",
                    details={
                        "collaborator": collaborator
                    }
                )
                
                logger.info(f"Removed collaborator {collaborator} from circuit {share_id}")
                return True
            else:
                logger.error(f"Collaborator {collaborator} not found")
                return False
            
        except Exception as e:
            logger.error(f"Failed to remove collaborator: {e}")
            return False
    
    def get_activity_history(self, share_id: str) -> List[SharingActivity]:
        """
        Get activity history for a shared circuit.
        
        Args:
            share_id: ID of the shared circuit
            
        Returns:
            List of activities
        """
        try:
            # Get all activity files
            activities = []
            
            for activity_path in self.activities_dir.glob("*.json"):
                with open(activity_path, 'r') as f:
                    activity_data = json.load(f)
                    
                if activity_data["share_id"] == share_id:
                    activities.append(SharingActivity.from_dict(activity_data))
                    
            # Sort by timestamp (newest first)
            activities.sort(key=lambda x: x.timestamp, reverse=True)
            
            return activities
            
        except Exception as e:
            logger.error(f"Failed to get activity history: {e}")
            return []
    
    def get_access_level(self, share_id: str) -> Optional[str]:
        """
        Get the access level of the current user for a shared circuit.
        
        Args:
            share_id: ID of the shared circuit
            
        Returns:
            Access level if found, None otherwise
        """
        try:
            # Get the shared circuit
            shared_circuit = self.get_shared_circuit(share_id)
            
            if not shared_circuit:
                return None
                
            # Check if user is the owner
            if shared_circuit.owner == self.user_id:
                return SharingPermission.OWNER
                
            # Check if user is a collaborator
            if self.user_id in shared_circuit.collaborators:
                return shared_circuit.collaborators[self.user_id]
                
            # User has no access
            return None
            
        except Exception as e:
            logger.error(f"Failed to get access level: {e}")
            return None
    
    def has_write_access(self, share_id: str) -> bool:
        """
        Check if the current user has write access to a shared circuit.
        
        Args:
            share_id: ID of the shared circuit
            
        Returns:
            True if user has write access, False otherwise
        """
        access_level = self.get_access_level(share_id)
        
        return access_level in [
            SharingPermission.OWNER,
            SharingPermission.ADMIN,
            SharingPermission.READ_WRITE
        ]
    
    def unshare_circuit(self, share_id: str) -> bool:
        """
        Unshare a circuit.
        
        Args:
            share_id: ID of the shared circuit
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the shared circuit
            shared_circuit = self.get_shared_circuit(share_id)
            
            if not shared_circuit:
                return False
                
            # Check if user has permission to unshare
            if shared_circuit.owner != self.user_id:
                logger.error(f"Only the owner can unshare a circuit")
                return False
                
            # Remove from registry
            if share_id in self.registry:
                del self.registry[share_id]
                self._save_registry()
                
            # Delete the share file
            share_path = self._get_share_path(share_id)
            if share_path.exists():
                share_path.unlink()
                
            # Record activity (but keep the activity history)
            self._record_activity(
                share_id=share_id,
                action="unshared_circuit"
            )
            
            logger.info(f"Unshared circuit {share_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unshare circuit: {e}")
            return False
    
    def search_shared_circuits(self, query: str) -> List[SharedCircuit]:
        """
        Search for shared circuits.
        
        Args:
            query: Search query
            
        Returns:
            List of matching shared circuits
        """
        try:
            query = query.lower()
            results = []
            
            # Get all circuits
            all_circuits = []
            all_circuits.extend(self.list_shared_circuits())
            all_circuits.extend(self.list_shared_with_me())
            
            # Remove duplicates
            unique_circuits = {}
            for circuit in all_circuits:
                unique_circuits[circuit.share_id] = circuit
                
            # Search for matches
            for circuit in unique_circuits.values():
                if (query in circuit.circuit_name.lower() or
                    query in circuit.description.lower() or
                    query in circuit.owner.lower() or
                    any(query in tag.lower() for tag in circuit.tags)):
                    results.append(circuit)
                    
            return results
            
        except Exception as e:
            logger.error(f"Failed to search shared circuits: {e}")
            return []

# Convenience functions for command-line use

def share_circuit(repo_path: str,
                 circuit_name: str,
                 description: str,
                 storage_path: str,
                 recipients: List[str] = None,
                 permission: str = SharingPermission.READ_ONLY,
                 tags: List[str] = None,
                 user_id: Optional[str] = None) -> Optional[str]:
    """Share a quantum circuit with others."""
    manager = SharingManager(storage_path, user_id)
    return manager.share_circuit(
        repo_path=repo_path,
        circuit_name=circuit_name,
        description=description,
        recipients=recipients,
        permission=permission,
        tags=tags
    )

def list_my_shared_circuits(storage_path: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List circuits shared by the current user."""
    manager = SharingManager(storage_path, user_id)
    circuits = manager.list_shared_circuits(owned_only=True)
    return [circuit.to_dict() for circuit in circuits]

def list_shared_with_me(storage_path: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List circuits shared with the current user."""
    manager = SharingManager(storage_path, user_id)
    circuits = manager.list_shared_with_me()
    return [circuit.to_dict() for circuit in circuits]

def get_shared_circuit_details(share_id: str, storage_path: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get details of a shared circuit."""
    manager = SharingManager(storage_path, user_id)
    circuit = manager.get_shared_circuit(share_id)
    return circuit.to_dict() if circuit else None

def update_share_permissions(share_id: str, 
                            collaborator: str, 
                            permission: str, 
                            storage_path: str,
                            user_id: Optional[str] = None) -> bool:
    """Update permissions for a collaborator."""
    manager = SharingManager(storage_path, user_id)
    return manager.update_permissions(share_id, collaborator, permission)

def remove_collaborator(share_id: str, 
                       collaborator: str, 
                       storage_path: str,
                       user_id: Optional[str] = None) -> bool:
    """Remove a collaborator from a shared circuit."""
    manager = SharingManager(storage_path, user_id)
    return manager.remove_collaborator(share_id, collaborator)

def unshare_circuit(share_id: str, storage_path: str, user_id: Optional[str] = None) -> bool:
    """Unshare a circuit."""
    manager = SharingManager(storage_path, user_id)
    return manager.unshare_circuit(share_id)

def get_activity_history(share_id: str, storage_path: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get activity history for a shared circuit."""
    manager = SharingManager(storage_path, user_id)
    activities = manager.get_activity_history(share_id)
    return [activity.to_dict() for activity in activities]

def search_shared_circuits(query: str, storage_path: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search for shared circuits."""
    manager = SharingManager(storage_path, user_id)
    circuits = manager.search_shared_circuits(query)
    return [circuit.to_dict() for circuit in circuits] 